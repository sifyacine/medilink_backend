"""
Serializers for the appointments app.

Provides comprehensive serialization for:
- Appointment listing, detail, creation, and updates
- Scheduling validation with double-booking prevention
- Status management and transitions
- Availability slot presentation
"""
from rest_framework import serializers
from django.utils import timezone

from .models import (
    Appointment,
    AppointmentReminder,
    AppointmentStatus,
    AppointmentLocationType,
    CancellationReason,
    CreatedByRole,
    ProviderAvailability,
    ProviderTimeOff,
    DayOfWeek,
    AppointmentService,
)
from .services import SchedulingService
from providers.models.provider import Provider
from patients.models import PatientRecord
from accounts.models import User
from common.utils import get_patient_display_name, get_provider_display_name
from common.enums import UserRole


def _get_custom_service_price(provider, service):
    """
    Return the provider's custom price for a service, or the service's base price.

    Uses prefetched custom service data (loaded via get_appointment_prefetch_related)
    so no additional DB queries are issued during serialization.
    Falls back to a live DB query only if prefetch data is not available.
    """
    from decimal import Decimal

    base_price = service.price or Decimal('0.00')

    for profile_attr in ('doctor_profile', 'nurse_profile'):
        profile = getattr(provider, profile_attr, None)
        if profile is None:
            continue
        prefetched = getattr(profile, 'prefetched_custom_services', None)
        if prefetched is not None:
            for entry in prefetched:
                if entry.service_id == service.pk:
                    return entry.custom_price if entry.custom_price else base_price
            return base_price
        # Fallback when queryset was not prefetched (e.g. direct serializer use)
        try:
            if profile_attr == 'doctor_profile':
                from services.models import DoctorService
                ds = DoctorService.objects.get(doctor=profile, service=service)
                return ds.custom_price if ds.custom_price else base_price
            else:
                from services.models import NurseService
                ns = NurseService.objects.get(nurse=profile, service=service)
                return ns.custom_price if ns.custom_price else base_price
        except Exception:
            return base_price

    return base_price


class AppointmentServiceDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for services included in an appointment.
    Shows service details with custom pricing if set by the doctor.
    """
    service_id = serializers.UUIDField(source='service.id', read_only=True)
    service_name = serializers.CharField(source='service.title', read_only=True)
    service_description = serializers.CharField(source='service.description', read_only=True)
    
    # Show the custom price if doctor has set one, otherwise base price
    price = serializers.SerializerMethodField()
    currency = serializers.CharField(source='service.currency', read_only=True)
    
    class Meta:
        model = AppointmentService
        fields = [
            'id',
            'service_id',
            'service_name',
            'service_description',
            'price',
            'currency',
            'notes',
        ]
    
    def get_price(self, obj):
        price = _get_custom_service_price(obj.appointment.provider, obj.service)
        return f"{float(price):.2f} DZD"


class AppointmentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing appointments.
    Uses centralized utilities for consistent patient/provider name display.
    """
    provider_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.title', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    can_leave_review = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'provider',
            'provider_name',
            'patient_user',
            'patient_name',
            'service_name',
            'scheduled_date',
            'scheduled_time',
            'duration_minutes',
            'location_type',
            'location_type_display',
            'status',
            'status_display',
            'reason',
            'is_upcoming',
            'allowed_actions',
            'can_leave_review',
            'created_at',
        ]
    
    def get_can_leave_review(self, obj):
        if obj.status != AppointmentStatus.COMPLETED:
            return False
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from reviews.models import Review
        from django.contrib.contenttypes.models import ContentType
        from .models import Appointment as ApptModel
        appointment_ct = ContentType.objects.get_for_model(ApptModel)
        has_review = Review.objects.filter(
            reviewer=request.user,
            context_content_type=appointment_ct,
            context_object_id=str(obj.id)
        ).exists()

        return not has_review

    def get_provider_name(self, obj):
        """Use centralized provider name helper."""
        return get_provider_display_name(obj.provider)

    def get_patient_name(self, obj):
        """Use centralized patient name helper."""
        return get_patient_display_name(obj.patient_user, obj.patient_record)

    def get_allowed_actions(self, obj):
        """Get allowed actions for this appointment based on current user."""
        request = self.context.get('request')
        user = request.user if request else None
        return obj.get_allowed_actions(user)


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for viewing full appointment information.
    Uses centralized utilities for consistent data presentation.
    
    **Multi-Service Support:**
    - Shows all selected services with their prices
    - Displays custom pricing if doctor has set it
    - Calculates total price for the appointment
    """
    provider_name = serializers.SerializerMethodField()
    provider_email = serializers.EmailField(source='provider.user.email', read_only=True)
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)
    
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    patient_phone = serializers.SerializerMethodField()
    
    service_name = serializers.CharField(source='service.title', read_only=True, allow_null=True)
    service_description = serializers.CharField(source='service.description', read_only=True, allow_null=True)
    
    # Selected services with prices
    selected_services = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    
    created_by_name = serializers.SerializerMethodField()
    cancelled_by_name = serializers.SerializerMethodField()
    
    is_upcoming = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    can_leave_review = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            # Provider info
            'provider',
            'provider_name',
            'provider_email',
            'provider_type',
            # Patient info
            'patient_user',
            'patient_record',
            'patient_name',
            'patient_email',
            'patient_phone',
            # Service
            'service',
            'service_name',
            'service_description',
            # Multi-service selection
            'selected_services',
            'total_price',
            # Scheduling
            'scheduled_date',
            'scheduled_time',
            'duration_minutes',
            # Location
            'location_type',
            'location_type_display',
            'clinic_address',
            'home_address',
            'meeting_link',
            # Status and notes
            'status',
            'status_display',
            'reason',
            'notes',
            # Cancellation
            'cancellation_reason',
            'cancellation_notes',
            'cancelled_by',
            'cancelled_by_name',
            'cancelled_at',
            # Metadata
            'created_by',
            'created_by_name',
            'confirmed_at',
            'completed_at',
            'is_upcoming',
            'is_past',
            'allowed_actions',
            'can_leave_review',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'confirmed_at',
            'completed_at',
            'cancelled_by',
            'cancelled_at',
            'created_by',
            'created_at',
            'updated_at',
        ]
    
    def get_can_leave_review(self, obj):
        if obj.status != AppointmentStatus.COMPLETED:
            return False
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        from reviews.models import Review
        from django.contrib.contenttypes.models import ContentType
        from .models import Appointment as ApptModel
        appointment_ct = ContentType.objects.get_for_model(ApptModel)
        has_review = Review.objects.filter(
            reviewer=request.user,
            context_content_type=appointment_ct,
            context_object_id=str(obj.id)
        ).exists()

        return not has_review

    def get_provider_name(self, obj):
        """Use centralized provider name helper."""
        return get_provider_display_name(obj.provider)
    
    def get_patient_name(self, obj):
        """Use centralized patient name helper."""
        return get_patient_display_name(obj.patient_user, obj.patient_record)
    
    def get_patient_email(self, obj):
        """Use centralized patient email helper."""
        from common.utils import get_patient_email
        return get_patient_email(obj.patient_user, obj.patient_record)
    
    def get_patient_phone(self, obj):
        """Use centralized patient phone helper."""
        from common.utils import get_patient_phone
        return get_patient_phone(obj.patient_user, obj.patient_record)
    
    def get_selected_services(self, obj):
        """Get all services selected for this appointment with their prices."""
        appointment_services = obj.appointment_services.all()
        if not appointment_services.exists():
            if obj.service:
                price = str(_get_custom_service_price(obj.provider, obj.service))
                return [{
                    'service_id': str(obj.service.id),
                    'service_name': obj.service.title,
                    'service_description': obj.service.description,
                    'price': price,
                    'currency': obj.service.currency,
                }]
            return []

        return AppointmentServiceDetailSerializer(appointment_services, many=True).data
    
    def get_total_price(self, obj):
        """Calculate total price of all selected services."""
        from decimal import Decimal

        total = Decimal('0.00')
        appointment_services = obj.appointment_services.all()

        if not appointment_services.exists():
            if obj.service:
                total = _get_custom_service_price(obj.provider, obj.service)
        else:
            for app_service in appointment_services:
                total += _get_custom_service_price(obj.provider, app_service.service)

        return str(total)
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None
    
    def get_cancelled_by_name(self, obj):
        if obj.cancelled_by:
            return obj.cancelled_by.get_full_name() or obj.cancelled_by.email
        return None
    
    def get_allowed_actions(self, obj):
        """Get allowed actions for this appointment based on current user."""
        request = self.context.get('request')
        user = request.user if request else None
        return obj.get_allowed_actions(user)


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating appointments.
    
    Can be used by:
    - Patients: Must specify provider, can optionally specify service(s)
    - Providers: Must specify patient_user OR patient_record
    
    **Multi-Service Selection:**
    - Patient can select multiple services when booking
    - Each service can have custom pricing set by the doctor
    - Total price is calculated and shown to patient before booking
    
    Notes:
    - scheduled_time is optional (providers manage their own schedules)
    - duration_minutes is optional (defaults to 30 if not provided)
    - For online appointments, meeting_link can be added later by provider
    """
    # Make these explicitly optional
    provider = serializers.PrimaryKeyRelatedField(
        queryset=Provider.objects.all(),
        required=False,
        allow_null=True,
        help_text='Provider UUID. Auto-filled when the requesting user is a provider.'
    )
    scheduled_time = serializers.TimeField(required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=5)

    # Multiple services selection (IDs)
    service_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        write_only=True,
        help_text='List of service IDs to include in this appointment'
    )
    
    class Meta:
        model = Appointment
        fields = [
            'provider',
            'patient_user',
            'patient_record',
            'service',
            'service_ids',  # Added for multi-service selection
            'scheduled_date',
            'scheduled_time',
            'duration_minutes',
            'location_type',
            'clinic_address',
            'home_address',
            'meeting_link',
            'reason',
            'notes',
        ]
    
    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request else None

        patient_user = attrs.get('patient_user')
        patient_record = attrs.get('patient_record')
        provider = attrs.get('provider')
        service_ids = attrs.get('service_ids', [])

        # Providers always get their own profile — ignore whatever provider ID
        # they sent so a doctor with User.id=8 can never accidentally book under
        # Provider #8 (which might belong to a completely different doctor).
        if user and hasattr(user, 'provider_profile'):
            attrs['provider'] = user.provider_profile
            provider = attrs['provider']

        if not provider:
            raise serializers.ValidationError({
                'provider': 'Provider is required.'
            })

        # If user is a patient, automatically set patient_user
        if user and hasattr(user, 'role') and user.role == UserRole.PATIENT:
            if not patient_user and not patient_record:
                attrs['patient_user'] = user

        # Validate patient identification
        if not attrs.get('patient_user') and not attrs.get('patient_record'):
            raise serializers.ValidationError({
                'patient_user': 'Either patient_user or patient_record must be provided.'
            })
        
        if attrs.get('patient_user') and attrs.get('patient_record'):
            raise serializers.ValidationError({
                'patient_user': 'Cannot specify both patient_user and patient_record.'
            })
        
        # Validate services exist
        if service_ids:
            from services.models import Service
            services = Service.objects.filter(id__in=service_ids)

            if services.count() != len(service_ids):
                raise serializers.ValidationError({
                    'service_ids': 'One or more service IDs are invalid.'
                })

            # Store services for later
            attrs['_services'] = list(services)
        
        # Validate scheduling
        scheduled_date = attrs.get('scheduled_date')
        scheduled_time = attrs.get('scheduled_time')
        
        # Validate date is not in the past
        if scheduled_date:
            if scheduled_date < timezone.now().date():
                raise serializers.ValidationError({
                    'scheduled_date': 'Appointment cannot be scheduled in the past.'
                })
            
            # If time is provided, validate full datetime
            if scheduled_time:
                appointment_datetime = timezone.datetime.combine(scheduled_date, scheduled_time)
                if timezone.is_naive(appointment_datetime):
                    appointment_datetime = timezone.make_aware(appointment_datetime)
                
                if appointment_datetime < timezone.now():
                    raise serializers.ValidationError({
                        'scheduled_date': 'Appointment cannot be scheduled in the past.'
                    })
        
        # Validate location-specific requirements
        location_type = attrs.get('location_type', AppointmentLocationType.CLINIC)
        
        if location_type == AppointmentLocationType.HOME and not attrs.get('home_address'):
            raise serializers.ValidationError({
                'home_address': 'Home address is required for home visit appointments.'
            })
        
        # Check provider's daily appointment limit
        if provider and scheduled_date:
            daily_limit = provider.daily_appointment_limit
            if daily_limit > 0:
                # Count existing appointments for that day (excluding cancelled/rejected)
                existing_count = Appointment.objects.filter(
                    provider=provider,
                    scheduled_date=scheduled_date,
                    status__in=[
                        AppointmentStatus.PENDING,
                        AppointmentStatus.CONFIRMED,
                        AppointmentStatus.COMPLETED,
                    ]
                ).count()
                
                if existing_count >= daily_limit:
                    raise serializers.ValidationError({
                        'scheduled_date': f'This provider has reached their daily appointment limit ({daily_limit}) for this date. Please choose another date.'
                    })
        
        # For providers creating appointments, skip slot availability check —
        # they manage their own schedule and can enter any time.
        # For patients, validate against the provider's availability.
        user_is_provider = user and hasattr(user, 'provider_profile')
        if scheduled_time and not user_is_provider:
            duration_minutes = attrs.get('duration_minutes') or 30
            is_available, availability_message = SchedulingService.check_provider_available(
                provider=provider,
                scheduled_date=scheduled_date,
                scheduled_time=scheduled_time,
                duration_minutes=duration_minutes,
                location_type=location_type
            )

            if not is_available:
                raise serializers.ValidationError({
                    'scheduled_time': availability_message
                })
        
        return attrs
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        
        # Extract services before creating appointment
        services = validated_data.pop('_services', [])
        validated_data.pop('service_ids', None)  # Remove service_ids from validated_data
        
        if user:
            validated_data['created_by'] = user
            
            # Set created_by_role based on who's creating
            if user.is_staff or user.is_superuser:
                validated_data['created_by_role'] = CreatedByRole.ADMIN
            elif hasattr(user, 'provider_profile'):
                validated_data['created_by_role'] = CreatedByRole.PROVIDER
            else:
                validated_data['created_by_role'] = CreatedByRole.PATIENT
        
        # Create appointment
        appointment = super().create(validated_data)
        
        # Add selected services to appointment
        if services:
            from appointments.models import AppointmentService
            appointment_services = [
                AppointmentService(appointment=appointment, service=service)
                for service in services
            ]
            AppointmentService.objects.bulk_create(appointment_services)
            
            # Also set the primary service to the first selected service if not already set
            if not appointment.service and services:
                appointment.service = services[0]
                appointment.save(update_fields=['service'])
        
        return appointment


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating appointments.
    Only certain fields can be updated after creation.
    
    Restrictions:
    - Cannot update terminal (completed/cancelled) appointments
    - Cannot change provider, service, or time after confirmation (unless rescheduling)
    - Validates scheduling conflicts on time changes
    
    Uses centralized status helpers for consistent validation.
    """
    class Meta:
        model = Appointment
        fields = [
            'scheduled_date',
            'scheduled_time',
            'duration_minutes',
            'location_type',
            'clinic_address',
            'home_address',
            'meeting_link',
            'reason',
            'notes',
            'provider_notes',
        ]
    
    def validate(self, attrs):
        from common.domain_helpers import AppointmentStatusTransition
        
        instance = self.instance
        request = self.context.get('request')
        user = request.user if request else None
        
        # Cannot update terminal appointments
        if instance and AppointmentStatusTransition.is_terminal(instance.status):
            raise serializers.ValidationError(
                f'Cannot update appointment with status {instance.status}'
            )
        
        # For CONFIRMED appointments, only notes can be updated (not time/provider)
        if instance and instance.status == AppointmentStatus.CONFIRMED:
            restricted_fields = ['scheduled_date', 'scheduled_time', 'duration_minutes']
            for field in restricted_fields:
                if field in attrs and attrs[field] != getattr(instance, field):
                    # Only provider or admin can reschedule confirmed appointments
                    is_provider = hasattr(user, 'provider_profile') and user.provider_profile == instance.provider
                    is_admin = user.is_staff or user.is_superuser if user else False
                    
                    if not (is_provider or is_admin):
                        raise serializers.ValidationError({
                            field: f'Cannot change {field} on a confirmed appointment. Contact the provider to reschedule.'
                        })
        
        # Validate scheduling if date/time is being updated
        scheduled_date = attrs.get('scheduled_date', instance.scheduled_date if instance else None)
        scheduled_time = attrs.get('scheduled_time', instance.scheduled_time if instance else None)
        
        if scheduled_date and scheduled_time:
            appointment_datetime = timezone.datetime.combine(scheduled_date, scheduled_time)
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            
            if appointment_datetime < timezone.now():
                raise serializers.ValidationError({
                    'scheduled_date': 'Appointment cannot be scheduled in the past.'
                })
            
            # Check for scheduling conflicts (only if date/time changed)
            date_changed = 'scheduled_date' in attrs and attrs['scheduled_date'] != instance.scheduled_date
            time_changed = 'scheduled_time' in attrs and attrs['scheduled_time'] != instance.scheduled_time
            
            if date_changed or time_changed:
                duration_minutes = attrs.get('duration_minutes', instance.duration_minutes)
                location_type = attrs.get('location_type', instance.location_type)
                
                is_available, message = SchedulingService.check_provider_available(
                    provider=instance.provider,
                    scheduled_date=scheduled_date,
                    scheduled_time=scheduled_time,
                    duration_minutes=duration_minutes,
                    location_type=location_type,
                    exclude_appointment_id=str(instance.id)
                )
                
                if not is_available:
                    raise serializers.ValidationError({
                        'scheduled_time': message
                    })
        
        return attrs


class AppointmentConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming an appointment.
    
    For online appointments, the provider must provide a meeting link.
    """
    notes = serializers.CharField(required=False, allow_blank=True)
    meeting_link = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    
    def validate(self, attrs):
        """Validate that meeting_link is provided for online appointments."""
        appointment = self.context.get('appointment')
        
        if appointment and appointment.location_type == AppointmentLocationType.ONLINE:
            meeting_link = attrs.get('meeting_link') or appointment.meeting_link
            if not meeting_link:
                raise serializers.ValidationError({
                    'meeting_link': 'Meeting link is required for online appointments.'
                })
        
        return attrs


class AppointmentCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an appointment."""
    reason = serializers.ChoiceField(
        choices=CancellationReason.choices,
        default=CancellationReason.OTHER
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class AppointmentCompleteSerializer(serializers.Serializer):
    """
    Serializer for completing an appointment.
    
    For online appointments, meeting_link must have been set before completion.
    """
    provider_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate that meeting_link exists for online appointments."""
        appointment = self.context.get('appointment')
        
        if appointment and appointment.location_type == AppointmentLocationType.ONLINE:
            if not appointment.meeting_link:
                raise serializers.ValidationError({
                    'meeting_link': 'Meeting link must be set before completing an online appointment.'
                })
        
        return attrs


class AppointmentReminderSerializer(serializers.ModelSerializer):
    """Serializer for appointment reminders."""
    class Meta:
        model = AppointmentReminder
        fields = [
            'id',
            'appointment',
            'remind_at',
            'sent',
            'sent_at',
        ]
        read_only_fields = ['id', 'sent', 'sent_at']


class AppointmentStatusChoicesSerializer(serializers.Serializer):
    """Serializer for appointment status choices."""
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_choices(cls):
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in AppointmentStatus.choices
        ]


class AppointmentLocationTypeChoicesSerializer(serializers.Serializer):
    """Serializer for location type choices."""
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_choices(cls):
        return [
            {'value': choice[0], 'label': choice[1]}
            for choice in AppointmentLocationType.choices
        ]


class AppointmentRescheduleSerializer(serializers.Serializer):
    """
    Serializer for rescheduling an appointment.
    
    Validates the new date/time against provider availability
    and checks for double-booking conflicts.
    """
    scheduled_date = serializers.DateField()
    scheduled_time = serializers.TimeField()
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        instance = self.context.get('instance')
        
        if not instance:
            raise serializers.ValidationError("Appointment instance required.")
        
        # Use centralized status transition validation
        from common.domain_helpers import AppointmentStatusTransition
        if not AppointmentStatusTransition.can_transition(instance.status, AppointmentStatus.RESCHEDULED):
            allowed = AppointmentStatusTransition.get_allowed_transitions(instance.status)
            if allowed:
                raise serializers.ValidationError({
                    'status': f'Cannot reschedule appointment with status {instance.status}. '
                              f'Allowed transitions: {", ".join(sorted(allowed))}'
                })
            else:
                raise serializers.ValidationError({
                    'status': f'Cannot reschedule appointment with status {instance.status}.'
                })
        
        # Validate against past dates
        scheduled_date = attrs.get('scheduled_date')
        scheduled_time = attrs.get('scheduled_time')
        
        appointment_datetime = timezone.datetime.combine(scheduled_date, scheduled_time)
        if timezone.is_naive(appointment_datetime):
            appointment_datetime = timezone.make_aware(appointment_datetime)
        
        if appointment_datetime < timezone.now():
            raise serializers.ValidationError({
                'scheduled_date': 'Cannot reschedule to a past date/time.'
            })
        
        # Check provider availability
        is_available, message = SchedulingService.check_provider_available(
            provider=instance.provider,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            duration_minutes=instance.duration_minutes,
            location_type=instance.location_type,
            exclude_appointment_id=str(instance.id)
        )
        
        if not is_available:
            raise serializers.ValidationError({
                'scheduled_time': message
            })
        
        return attrs


class ProviderAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for provider availability slots."""
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = ProviderAvailability
        fields = [
            'id',
            'provider',
            'day_of_week',
            'day_of_week_display',
            'start_time',
            'end_time',
            'is_active',
            'location_type',
            'max_appointments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time.'
            })
        
        return attrs


class ProviderTimeOffSerializer(serializers.ModelSerializer):
    """Serializer for provider time off periods."""
    
    class Meta:
        model = ProviderTimeOff
        fields = [
            'id',
            'provider',
            'start_datetime',
            'end_datetime',
            'reason',
            'is_recurring_annual',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        start = attrs.get('start_datetime')
        end = attrs.get('end_datetime')
        
        if start and end and start >= end:
            raise serializers.ValidationError({
                'end_datetime': 'End datetime must be after start datetime.'
            })
        
        return attrs


class AvailableSlotsRequestSerializer(serializers.Serializer):
    """Request serializer for getting available time slots."""
    provider = serializers.PrimaryKeyRelatedField(queryset=Provider.objects.all())
    date = serializers.DateField()
    duration_minutes = serializers.IntegerField(default=30, min_value=5, max_value=480)
    location_type = serializers.ChoiceField(
        choices=AppointmentLocationType.choices,
        default=AppointmentLocationType.CLINIC
    )


class AvailableSlotSerializer(serializers.Serializer):
    """Response serializer for an available time slot."""
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    duration_minutes = serializers.IntegerField()


class AppointmentHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for appointment history listing.
    Optimized for showing past appointments with centralized helpers.
    """
    provider_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.title', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    created_by_role_display = serializers.CharField(source='get_created_by_role_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id',
            'provider',
            'provider_name',
            'patient_name',
            'service_name',
            'scheduled_date',
            'scheduled_time',
            'duration_minutes',
            'location_type',
            'location_type_display',
            'status',
            'status_display',
            'reason',
            'created_by_role',
            'created_by_role_display',
            'cancellation_reason',
            'cancellation_notes',
            'completed_at',
            'cancelled_at',
            'created_at',
        ]
    
    def get_provider_name(self, obj):
        """Use centralized provider name helper."""
        return get_provider_display_name(obj.provider)
    
    def get_patient_name(self, obj):
        """Use centralized patient name helper."""
        return get_patient_display_name(obj.patient_user, obj.patient_record)


class ProviderScheduleSerializer(serializers.Serializer):
    """Response serializer for provider schedule."""
    availability = serializers.ListField()
    time_off = serializers.ListField()
    appointments = serializers.ListField()
