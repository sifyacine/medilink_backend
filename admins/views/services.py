"""
Admin REST API views for the Services catalog.

Endpoints:
  GET    /api/admin/services/                         List all services (all filters)
  POST   /api/admin/services/                         Create a new service
  GET    /api/admin/services/{id}/                    Service detail (with provider assignments)
  PATCH  /api/admin/services/{id}/                    Update service
  DELETE /api/admin/services/{id}/                    Hard-delete service
  POST   /api/admin/services/{id}/toggle-active/      Flip is_active
  POST   /api/admin/services/{id}/toggle-on-demand/   Flip is_on_demand
  GET    /api/admin/services/stats/                   Catalog-wide statistics

  GET    /api/admin/nurse-services/                   All nurse↔service assignments
  PATCH  /api/admin/nurse-services/{id}/              Edit assignment (custom price, availability)
  DELETE /api/admin/nurse-services/{id}/              Remove assignment

  GET    /api/admin/doctor-services/                  All doctor↔service assignments
  PATCH  /api/admin/doctor-services/{id}/             Edit assignment
  DELETE /api/admin/doctor-services/{id}/             Remove assignment

  GET    /api/admin/custom-services/                  All provider custom services
  PATCH  /api/admin/custom-services/{id}/             Edit custom service
  POST   /api/admin/custom-services/{id}/toggle-active/  Flip is_active
"""
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admins.permissions import IsAdmin
from admins.serializers.services import (
    AdminDoctorServiceSerializer,
    AdminNurseServiceSerializer,
    AdminProviderCustomServiceSerializer,
    AdminServiceDetailSerializer,
    AdminServiceListSerializer,
)
from services.models import DoctorService, NurseService, ProviderCustomService, Service


class AdminServiceViewSet(viewsets.ModelViewSet):
    """
    Full catalog management for Medilink admins.

    Filters
    -------
    ?service_type=NURSE|DOCTOR|VTC|GENERAL
    ?is_active=true|false
    ?is_on_demand=true|false
    ?is_home_service=true|false
    ?specialty=<id>
    ?search=<text>          — searches title, all translation fields
    ?ordering=title|price|created_at|-title|-price|-created_at
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['service_type', 'is_active', 'is_on_demand', 'is_home_service', 'specialty', 'currency']
    search_fields = ['title', 'title_en', 'title_ar', 'title_fr', 'description', 'slug']
    ordering_fields = ['title', 'price', 'duration_minutes', 'created_at', 'updated_at']
    ordering = ['service_type', 'title']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Service.objects.select_related('specialty').annotate(
            _nurse_count=Count('nurses', distinct=True),
            _doctor_count=Count('doctors', distinct=True),
        ).order_by('service_type', 'title')

    def get_serializer_class(self):
        if self.action == 'list':
            return AdminServiceListSerializer
        return AdminServiceDetailSerializer

    # ------------------------------------------------------------------
    # Standard create / update
    # ------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        serializer = AdminServiceDetailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        return Response(
            {'success': True, 'data': AdminServiceDetailSerializer(service, context={'request': request}).data},
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AdminServiceDetailSerializer(
            instance, data=request.data, partial=True, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        return Response({'success': True, 'data': AdminServiceDetailSerializer(service, context={'request': request}).data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        title = instance.title
        instance.delete()
        return Response({'success': True, 'message': f'Service "{title}" deleted.'}, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Toggle actions
    # ------------------------------------------------------------------

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Flip is_active on a single service."""
        service = self.get_object()
        service.is_active = not service.is_active
        service.save(update_fields=['is_active'])
        state = 'activated' if service.is_active else 'deactivated'
        return Response({
            'success': True,
            'is_active': service.is_active,
            'message': f'Service "{service.title}" {state}.',
        })

    @action(detail=True, methods=['post'], url_path='toggle-on-demand')
    def toggle_on_demand(self, request, pk=None):
        """Flip is_on_demand on a single service."""
        service = self.get_object()
        service.is_on_demand = not service.is_on_demand
        service.save(update_fields=['is_on_demand'])
        state = 'enabled' if service.is_on_demand else 'disabled'
        return Response({
            'success': True,
            'is_on_demand': service.is_on_demand,
            'message': f'On-demand {state} for "{service.title}".',
        })

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Catalog-wide statistics for the admin dashboard."""
        qs = Service.objects.all()

        by_type = {}
        for row in qs.values('service_type').annotate(
            total=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            on_demand=Count('id', filter=Q(is_on_demand=True)),
        ):
            by_type[row['service_type']] = {
                'total': row['total'],
                'active': row['active'],
                'on_demand': row['on_demand'],
            }

        total = qs.count()
        active = qs.filter(is_active=True).count()
        on_demand = qs.filter(is_on_demand=True, service_type='NURSE').count()
        nurse_assignments = NurseService.objects.count()
        doctor_assignments = DoctorService.objects.count()
        custom_services = ProviderCustomService.objects.count()

        return Response({
            'success': True,
            'data': {
                'total_services': total,
                'active_services': active,
                'inactive_services': total - active,
                'on_demand_nurse_services': on_demand,
                'nurse_provider_assignments': nurse_assignments,
                'doctor_provider_assignments': doctor_assignments,
                'provider_custom_services': custom_services,
                'by_type': by_type,
            },
        })


class AdminNurseServiceViewSet(viewsets.ModelViewSet):
    """
    Admin management of nurse↔service assignments (NurseService).
    Admins can view, update pricing/availability, or remove an assignment.
    Nurses add/remove their own assignments via /api/nurse-requests/nurse/my-services/.

    Filters: ?nurse=<id>, ?service=<id>, ?is_available=true|false
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminNurseServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_available', 'service', 'service__service_type']
    search_fields = ['nurse__first_name', 'nurse__last_name', 'service__title']
    ordering_fields = ['created_at', 'is_available']
    ordering = ['-created_at']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return NurseService.objects.select_related(
            'nurse__provider', 'service'
        ).order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        label = f'{instance.nurse.full_name} / {instance.service.title}'
        instance.delete()
        return Response({'success': True, 'message': f'Assignment "{label}" removed.'}, status=status.HTTP_200_OK)


class AdminDoctorServiceViewSet(viewsets.ModelViewSet):
    """
    Admin management of doctor↔service assignments (DoctorService).

    Filters: ?doctor=<id>, ?service=<id>, ?is_available=true|false
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminDoctorServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_available', 'service', 'service__service_type']
    search_fields = ['doctor__first_name', 'doctor__last_name', 'service__title']
    ordering_fields = ['created_at', 'is_available']
    ordering = ['-created_at']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return DoctorService.objects.select_related(
            'doctor__provider', 'service'
        ).order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        label = f'{instance.doctor.full_name} / {instance.service.title}'
        instance.delete()
        return Response({'success': True, 'message': f'Assignment "{label}" removed.'}, status=status.HTTP_200_OK)


class AdminProviderCustomServiceViewSet(viewsets.ModelViewSet):
    """
    Admin management of provider-created custom services.
    Admins can deactivate a custom service that violates platform rules.

    Filters: ?is_active=true|false, ?provider=<id>, ?specialty=<id>
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminProviderCustomServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_home_service', 'is_online_available', 'specialty']
    search_fields = ['title', 'title_en', 'title_ar', 'title_fr', 'provider__user__email']
    ordering_fields = ['created_at', 'price']
    ordering = ['-created_at']
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return ProviderCustomService.objects.select_related(
            'provider__user', 'specialty'
        ).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Flip is_active on a provider custom service."""
        svc = self.get_object()
        svc.is_active = not svc.is_active
        svc.save(update_fields=['is_active'])
        state = 'activated' if svc.is_active else 'deactivated'
        return Response({
            'success': True,
            'is_active': svc.is_active,
            'message': f'Custom service "{svc.title}" {state}.',
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        title = instance.title
        instance.delete()
        return Response({'success': True, 'message': f'Custom service "{title}" deleted.'}, status=status.HTTP_200_OK)
