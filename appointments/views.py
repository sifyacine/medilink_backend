"""
Views for the appointments app.

Provides comprehensive REST API for:
- Appointment CRUD operations
- Status lifecycle management (confirm, cancel, complete, no-show)
- Provider availability management
- Scheduling conflict detection
- Appointment history and search
- Available time slot generation
"""
from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    Appointment,
    AppointmentReminder,
    AppointmentStatus,
    ProviderAvailability,
    ProviderTimeOff,
    AppointmentLocationType,
)
from .serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentConfirmSerializer,
    AppointmentCancelSerializer,
    AppointmentCompleteSerializer,
    AppointmentReminderSerializer,
    AppointmentStatusChoicesSerializer,
    AppointmentLocationTypeChoicesSerializer,
    AppointmentRescheduleSerializer,
    AppointmentHistorySerializer,
    ProviderAvailabilitySerializer,
    ProviderTimeOffSerializer,
    AvailableSlotsRequestSerializer,
    AvailableSlotSerializer,
    ProviderScheduleSerializer,
)
from .services import SchedulingService, AppointmentService
from .permissions import (
    IsAppointmentParticipant,
    CanCreateAppointment,
    CanConfirmAppointment,
    CanCancelAppointment,
    CanCompleteAppointment,
)
from providers.models import Provider


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments.
    
    Provides CRUD operations and status transition actions.
    
    Endpoints:
    - GET /appointments/ - List appointments
    - POST /appointments/ - Create appointment
    - GET /appointments/{id}/ - Get appointment details
    - PUT/PATCH /appointments/{id}/ - Update appointment
    - DELETE /appointments/{id}/ - Delete appointment
    - POST /appointments/{id}/confirm/ - Confirm appointment
    - POST /appointments/{id}/cancel/ - Cancel appointment
    - POST /appointments/{id}/complete/ - Complete appointment
    - POST /appointments/{id}/no_show/ - Mark as no-show
    - GET /appointments/upcoming/ - Get upcoming appointments
    - GET /appointments/past/ - Get past appointments
    """
    permission_classes = [permissions.IsAuthenticated, IsAppointmentParticipant]
    
    def get_queryset(self):
        """
        Return appointments based on user role.
        
        - Patients see their own appointments
        - Providers see appointments where they are the provider
        - Admins see all appointments
        
        Uses optimized query with select_related and prefetch_related
        to prevent N+1 queries.
        """
        from common.utils import get_appointment_select_related, get_appointment_prefetch_related
        
        user = self.request.user
        queryset = Appointment.objects.all()
        
        # Admin sees all
        if user.is_staff or user.is_superuser:
            pass
        # Provider sees their appointments
        elif hasattr(user, 'provider_profile'):
            queryset = queryset.filter(provider=user.provider_profile)
        # Patient sees their appointments
        else:
            queryset = queryset.filter(
                Q(patient_user=user) | 
                Q(patient_record__linked_user=user) |
                Q(created_by=user)
            )
        
        # Apply filters
        queryset = self._apply_filters(queryset)
        
        # Optimize with select_related and prefetch_related using centralized helpers
        return queryset.select_related(
            *get_appointment_select_related()
        ).prefetch_related(
            *get_appointment_prefetch_related()
        ).order_by('-scheduled_date', '-scheduled_time')
    
    def _apply_filters(self, queryset):
        """Apply query parameter filters."""
        params = self.request.query_params
        
        # Filter by status
        status_filter = params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = params.get('date_from')
        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)
        
        date_to = params.get('date_to')
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)
        
        # Filter by provider
        provider_id = params.get('provider')
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        
        # Filter by patient
        patient_id = params.get('patient')
        if patient_id:
            queryset = queryset.filter(
                Q(patient_user_id=patient_id) | Q(patient_record_id=patient_id)
            )
        
        # Filter by location type
        location_type = params.get('location_type')
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        # Search in reason/notes
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(reason__icontains=search) | Q(notes__icontains=search)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return AppointmentListSerializer
        if self.action == 'create':
            return AppointmentCreateSerializer
        if self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        if self.action == 'confirm':
            return AppointmentConfirmSerializer
        if self.action == 'cancel':
            return AppointmentCancelSerializer
        if self.action == 'complete':
            return AppointmentCompleteSerializer
        if self.action == 'reschedule':
            return AppointmentRescheduleSerializer
        if self.action == 'history':
            return AppointmentHistorySerializer
        return AppointmentDetailSerializer
    
    def get_permissions(self):
        """Return appropriate permissions."""
        if self.action == 'create':
            return [permissions.IsAuthenticated(), CanCreateAppointment()]
        if self.action == 'confirm':
            return [permissions.IsAuthenticated(), CanConfirmAppointment()]
        if self.action == 'cancel':
            return [permissions.IsAuthenticated(), CanCancelAppointment()]
        if self.action == 'complete':
            return [permissions.IsAuthenticated(), CanCompleteAppointment()]
        if self.action == 'no_show':
            return [permissions.IsAuthenticated(), CanCompleteAppointment()]
        if self.action == 'reschedule':
            return [permissions.IsAuthenticated(), IsAppointmentParticipant()]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm an appointment.
        
        Only the provider can confirm.
        For online appointments, a meeting_link must be provided.
        """
        appointment = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'appointment': appointment}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            if serializer.validated_data.get('notes'):
                appointment.provider_notes = serializer.validated_data['notes']
            
            # Set meeting_link if provided (required for online appointments)
            if serializer.validated_data.get('meeting_link'):
                appointment.meeting_link = serializer.validated_data['meeting_link']
                appointment.save(update_fields=['meeting_link'])
            
            appointment.confirm()
            
            return Response({
                'status': 'confirmed',
                'message': 'Appointment confirmed successfully',
                'data': AppointmentDetailSerializer(appointment).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject an appointment (provider rejects patient's request).
        
        Only providers can reject appointments.
        Requires rejection_reason.
        """
        appointment = self.get_object()
        
        # Check if user is the provider
        if not hasattr(request.user, 'provider_profile'):
            return Response(
                {'error': 'Only providers can reject appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.provider_profile != appointment.provider:
            return Response(
                {'error': 'You can only reject your own appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('rejection_reason', '')
        if not reason:
            return Response(
                {'error': 'Rejection reason is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            appointment.reject(reason=reason)
            
            return Response({
                'status': 'rejected',
                'message': 'Appointment rejected successfully',
                'data': AppointmentDetailSerializer(appointment).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post', 'get'], url_path='services')
    def manage_services(self, request, pk=None):
        """
        Attach or view services for an appointment.
        
        GET - List current services
        POST - Attach services (body: {"service_ids": [uuid, ...]})
        
        Only providers can attach services.
        """
        appointment = self.get_object()
        
        if request.method == 'GET':
            from appointments.models import AppointmentService
            from services.serializers import ServiceSerializer
            
            appointment_services = appointment.appointment_services.select_related('service')
            services_data = []
            for aps in appointment_services:
                services_data.append({
                    'id': str(aps.id),
                    'service': ServiceSerializer(aps.service).data if hasattr(aps, 'service') else None,
                    'notes': aps.notes,
                    'created_at': aps.created_at.isoformat()
                })
            
            return Response({
                'appointment_id': str(appointment.id),
                'services': services_data
            })
        
        # POST - Attach services
        if not hasattr(request.user, 'provider_profile'):
            return Response(
                {'error': 'Only providers can attach services.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.provider_profile != appointment.provider:
            return Response(
                {'error': 'You can only modify your own appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        service_ids = request.data.get('service_ids', [])
        if not service_ids:
            return Response(
                {'error': 'service_ids is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from services.models import Service
        from appointments.models import AppointmentService
        
        # Validate services exist
        services = Service.objects.filter(id__in=service_ids)
        if services.count() != len(service_ids):
            return Response(
                {'error': 'One or more services not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Add services (avoid duplicates)
        added = []
        for service in services:
            aps, created = AppointmentService.objects.get_or_create(
                appointment=appointment,
                service=service
            )
            if created:
                added.append(str(service.id))
        
        return Response({
            'message': f'{len(added)} services attached successfully',
            'added_service_ids': added,
            'data': AppointmentDetailSerializer(appointment).data
        })
    
    @action(detail=True, methods=['delete'], url_path='services/(?P<service_id>[^/.]+)')
    def remove_service(self, request, pk=None, service_id=None):
        """
        Remove a service from an appointment.
        
        DELETE /api/appointments/{id}/services/{service_id}/
        """
        appointment = self.get_object()
        
        if not hasattr(request.user, 'provider_profile'):
            return Response(
                {'error': 'Only providers can remove services.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.provider_profile != appointment.provider:
            return Response(
                {'error': 'You can only modify your own appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from appointments.models import AppointmentService
        
        try:
            aps = AppointmentService.objects.get(
                appointment=appointment,
                service_id=service_id
            )
            aps.delete()
            return Response({
                'message': 'Service removed successfully'
            })
        except AppointmentService.DoesNotExist:
            return Response(
                {'error': 'Service not attached to this appointment.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def prescription(self, request, pk=None):
        """
        Get the prescription for an appointment (if exists).
        
        GET /api/appointments/{id}/prescription/
        """
        appointment = self.get_object()
        
        if not hasattr(appointment, 'prescription') or not appointment.prescription:
            return Response(
                {'error': 'No prescription for this appointment.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from prescriptions.serializers import PrescriptionDetailSerializer
        return Response(
            PrescriptionDetailSerializer(
                appointment.prescription,
                context={'request': request}
            ).data
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an appointment.
        
        Both patient and provider can cancel.
        """
        appointment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            appointment.cancel(
                cancelled_by=request.user,
                reason=serializer.validated_data.get('reason', 'OTHER'),
                notes=serializer.validated_data.get('notes', '')
            )
            
            return Response({
                'status': 'cancelled',
                'message': 'Appointment cancelled successfully',
                'data': AppointmentDetailSerializer(appointment).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark an appointment as completed.
        
        Only the provider can complete.
        For online appointments, meeting_link must have been set during confirmation.
        """
        appointment = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'appointment': appointment}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            if serializer.validated_data.get('provider_notes'):
                appointment.provider_notes = serializer.validated_data['provider_notes']
                appointment.save(update_fields=['provider_notes'])
            
            appointment.complete()
            
            return Response({
                'status': 'completed',
                'message': 'Appointment marked as completed',
                'data': AppointmentDetailSerializer(appointment).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def no_show(self, request, pk=None):
        """
        Mark an appointment as no-show.
        
        Only the provider can mark as no-show.
        """
        appointment = self.get_object()
        
        try:
            appointment.mark_no_show()
            
            return Response({
                'status': 'no_show',
                'message': 'Appointment marked as no-show',
                'data': AppointmentDetailSerializer(appointment).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming appointments.
        """
        now = timezone.now()
        queryset = self.get_queryset().filter(
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED],
            scheduled_date__gte=now.date()
        ).order_by('scheduled_date', 'scheduled_time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """
        Get past appointments.
        """
        now = timezone.now()
        queryset = self.get_queryset().filter(
            Q(status__in=[AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]) |
            Q(scheduled_date__lt=now.date())
        ).order_by('-scheduled_date', '-scheduled_time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get today's appointments.
        """
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            scheduled_date=today
        ).order_by('scheduled_time')
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get appointment statistics.
        """
        queryset = self.get_queryset()
        
        today = timezone.now().date()
        
        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status=AppointmentStatus.PENDING).count(),
            'confirmed': queryset.filter(status=AppointmentStatus.CONFIRMED).count(),
            'completed': queryset.filter(status=AppointmentStatus.COMPLETED).count(),
            'cancelled': queryset.filter(status=AppointmentStatus.CANCELLED).count(),
            'no_show': queryset.filter(status=AppointmentStatus.NO_SHOW).count(),
            'today': queryset.filter(scheduled_date=today).count(),
            'upcoming': queryset.filter(
                scheduled_date__gte=today,
                status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
            ).count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """
        Reschedule an existing appointment.
        
        Validates the new time against provider availability
        and checks for double-booking conflicts.
        
        Request body:
        - scheduled_date: New date (YYYY-MM-DD)
        - scheduled_time: New time (HH:MM)
        - notes: Optional note about rescheduling
        """
        appointment = self.get_object()
        
        serializer = AppointmentRescheduleSerializer(
            data=request.data,
            context={'request': request, 'instance': appointment}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            rescheduled = AppointmentService.reschedule_appointment(
                appointment=appointment,
                new_date=serializer.validated_data['scheduled_date'],
                new_time=serializer.validated_data['scheduled_time'],
                rescheduled_by_user=request.user
            )
            
            return Response({
                'status': 'rescheduled',
                'message': 'Appointment rescheduled successfully',
                'data': AppointmentDetailSerializer(rescheduled).data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get appointment history for the current user.
        
        Returns past/completed/cancelled appointments.
        
        Query params:
        - include_upcoming: Include upcoming appointments (default: false)
        - date_from: Start date filter
        - date_to: End date filter
        """
        user = request.user
        include_upcoming = request.query_params.get('include_upcoming', 'false').lower() == 'true'
        
        # For patients
        if not hasattr(user, 'provider_profile'):
            queryset = AppointmentService.get_patient_history(
                patient_user=user,
                include_upcoming=include_upcoming
            )
        # For providers
        else:
            queryset = Appointment.objects.filter(
                provider=user.provider_profile
            ).order_by('-scheduled_date', '-scheduled_time')
            
            if not include_upcoming:
                queryset = queryset.filter(
                    Q(status__in=[
                        AppointmentStatus.COMPLETED,
                        AppointmentStatus.CANCELLED,
                        AppointmentStatus.NO_SHOW
                    ]) |
                    Q(scheduled_date__lt=timezone.now().date())
                )
        
        # Apply date filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AppointmentHistorySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search for appointments.
        
        Query params:
        - q: Search query (searches patient name, email, reason, notes)
        - status: Filter by status
        - date_from: Start date
        - date_to: End date
        - location_type: Filter by location type
        - provider: Filter by provider ID
        - created_by_role: Filter by who created (PATIENT, PROVIDER, ADMIN)
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Search query
        q = request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(patient_user__first_name__icontains=q) |
                Q(patient_user__last_name__icontains=q) |
                Q(patient_user__email__icontains=q) |
                Q(patient_record__first_name__icontains=q) |
                Q(patient_record__last_name__icontains=q) |
                Q(patient_record__email__icontains=q) |
                Q(reason__icontains=q) |
                Q(notes__icontains=q) |
                Q(service__title__icontains=q)
            )
        
        # Additional filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)
        
        location_type = request.query_params.get('location_type')
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        created_by_role = request.query_params.get('created_by_role')
        if created_by_role:
            queryset = queryset.filter(created_by_role=created_by_role)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AppointmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def week(self, request):
        """
        Get appointments for the current week (Monday-Sunday).
        
        Query params:
        - week_offset: Number of weeks from current (0=this week, 1=next week, -1=last week)
        """
        week_offset = int(request.query_params.get('week_offset', 0))
        
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=6)
        
        queryset = self.get_queryset().filter(
            scheduled_date__gte=start_of_week,
            scheduled_date__lte=end_of_week
        ).order_by('scheduled_date', 'scheduled_time')
        
        serializer = AppointmentListSerializer(queryset, many=True)
        return Response({
            'week_start': start_of_week.isoformat(),
            'week_end': end_of_week.isoformat(),
            'appointments': serializer.data
        })


class AppointmentReminderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointment reminders.
    """
    serializer_class = AppointmentReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return AppointmentReminder.objects.filter(
            Q(appointment__patient_user=user) |
            Q(appointment__provider__user=user)
        ).select_related('appointment')


class AppointmentChoicesView(APIView):
    """
    View to get available appointment choices.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        return Response({
            'statuses': AppointmentStatusChoicesSerializer.get_choices(),
            'location_types': AppointmentLocationTypeChoicesSerializer.get_choices(),
        })


class ProviderAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing provider availability.
    
    Providers can define their weekly availability schedule.
    Supports multiple slots per day for breaks.
    """
    serializer_class = ProviderAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Providers see their own availability
        if hasattr(user, 'provider_profile'):
            return ProviderAvailability.objects.filter(
                provider=user.provider_profile
            ).order_by('day_of_week', 'start_time')
        
        # Admin sees all
        if user.is_staff or user.is_superuser:
            return ProviderAvailability.objects.all().order_by(
                'provider', 'day_of_week', 'start_time'
            )
        
        # Others see nothing
        return ProviderAvailability.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Auto-set provider if not specified
        if hasattr(user, 'provider_profile') and 'provider' not in serializer.validated_data:
            serializer.save(provider=user.provider_profile)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_schedule(self, request):
        """Get the current provider's weekly schedule."""
        user = request.user
        
        if not hasattr(user, 'provider_profile'):
            return Response(
                {'error': 'Only providers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        availability = ProviderAvailability.objects.filter(
            provider=user.provider_profile,
            is_active=True
        ).order_by('day_of_week', 'start_time')
        
        serializer = ProviderAvailabilitySerializer(availability, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        Bulk update provider availability.
        
        Replaces all existing availability with new schedule.
        
        Request body: List of availability slots
        """
        user = request.user
        
        if not hasattr(user, 'provider_profile'):
            return Response(
                {'error': 'Only providers can update availability'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        provider = user.provider_profile
        
        # Validate the new schedule
        serializer = ProviderAvailabilitySerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        # Delete existing and create new
        ProviderAvailability.objects.filter(provider=provider).delete()
        
        for slot_data in serializer.validated_data:
            slot_data['provider'] = provider
            ProviderAvailability.objects.create(**slot_data)
        
        # Return updated schedule
        new_availability = ProviderAvailability.objects.filter(
            provider=provider
        ).order_by('day_of_week', 'start_time')
        
        return Response(ProviderAvailabilitySerializer(new_availability, many=True).data)


class ProviderTimeOffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing provider time off periods.
    
    Providers can block out dates/times for vacations, holidays, etc.
    """
    serializer_class = ProviderTimeOffSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'provider_profile'):
            return ProviderTimeOff.objects.filter(
                provider=user.provider_profile
            ).order_by('start_datetime')
        
        if user.is_staff or user.is_superuser:
            return ProviderTimeOff.objects.all().order_by('provider', 'start_datetime')
        
        return ProviderTimeOff.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        
        if hasattr(user, 'provider_profile') and 'provider' not in serializer.validated_data:
            serializer.save(provider=user.provider_profile)
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming time off periods."""
        user = request.user
        
        if not hasattr(user, 'provider_profile'):
            return Response(
                {'error': 'Only providers can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        time_off = ProviderTimeOff.objects.filter(
            provider=user.provider_profile,
            end_datetime__gte=timezone.now()
        ).order_by('start_datetime')
        
        serializer = ProviderTimeOffSerializer(time_off, many=True)
        return Response(serializer.data)


class AvailableSlotsView(APIView):
    """
    View to get available appointment slots for a provider.
    
    Returns time slots that are:
    - Within the provider's availability schedule
    - Not blocked by time off
    - Not conflicting with existing appointments
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get available slots.
        
        Query params:
        - provider: Provider ID (required)
        - date: Date to check (YYYY-MM-DD, required)
        - duration_minutes: Appointment duration (default: 30)
        - location_type: Type of appointment (default: CLINIC)
        """
        provider_id = request.query_params.get('provider')
        date_str = request.query_params.get('date')
        duration_minutes = int(request.query_params.get('duration_minutes', 30))
        location_type = request.query_params.get('location_type', 'CLINIC')
        
        if not provider_id or not date_str:
            return Response(
                {'error': 'provider and date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            provider = Provider.objects.get(pk=provider_id)
        except Provider.DoesNotExist:
            return Response(
                {'error': 'Provider not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get available slots
        slots = SchedulingService.get_available_slots(
            provider=provider,
            target_date=target_date,
            duration_minutes=duration_minutes,
            location_type=location_type
        )
        
        return Response({
            'provider': str(provider.id),
            'date': date_str,
            'duration_minutes': duration_minutes,
            'location_type': location_type,
            'available_slots': slots
        })


class ProviderScheduleView(APIView):
    """
    View to get a provider's complete schedule.
    
    Returns availability, time off, and appointments for a date range.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get provider schedule.
        
        Query params:
        - provider: Provider ID (optional if user is provider)
        - start_date: Start of date range (YYYY-MM-DD)
        - end_date: End of date range (YYYY-MM-DD)
        """
        user = request.user
        provider_id = request.query_params.get('provider')
        
        # Determine provider
        if provider_id:
            try:
                provider = Provider.objects.get(pk=provider_id)
            except Provider.DoesNotExist:
                return Response(
                    {'error': 'Provider not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif hasattr(user, 'provider_profile'):
            provider = user.provider_profile
        else:
            return Response(
                {'error': 'provider parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse dates
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            # Default to current week
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        else:
            try:
                from datetime import datetime
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get schedule
        schedule = SchedulingService.get_provider_schedule(
            provider=provider,
            start_date=start_date,
            end_date=end_date
        )
        
        return Response({
            'provider': str(provider.id),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            **schedule
        })
