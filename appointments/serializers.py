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
)
from .services import SchedulingService
from providers.models.provider import Provider
from patients.models import PatientRecord
from accounts.models import User
from common.utils import get_patient_display_name, get_provider_display_name


class AppointmentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing appointments.
    Uses centralized utilities for consistent patient/provider name display.
    """
    provider_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    service_name = serializers.CharField(source='service.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    
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
            'is_upcoming',
            'allowed_actions',
            'created_at',
        ]
    
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
    """
    provider_name = serializers.SerializerMethodField()
    provider_email = serializers.EmailField(source='provider.user.email', read_only=True)
    provider_type = serializers.CharField(source='provider.provider_type', read_only=True)
    
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    patient_phone = serializers.SerializerMethodField()
    
    service_name = serializers.CharField(source='service.name', read_only=True, allow_null=True)
    service_description = serializers.CharField(source='service.description', read_only=True, allow_null=True)
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    
    created_by_name = serializers.SerializerMethodField()
    cancelled_by_name = serializers.SerializerMethodField()
    
    is_upcoming = serializers.BooleanField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    allowed_actions = serializers.SerializerMethodField()
    
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
    - Patients: Must specify provider, can optionally specify service
    - Providers: Must specify patient_user OR patient_record
    """
    class Meta:
        model = Appointment
        fields = [
            'provider',
            'patient_user',
            'patient_record',
            'service',
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
        
        # If user is a patient, automatically set patient_user
        if user and hasattr(user, 'role') and user.role == 'PATIENT':
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
        
        # Validate scheduling
        scheduled_date = attrs.get('scheduled_date')
        scheduled_time = attrs.get('scheduled_time')
        
        if scheduled_date and scheduled_time:
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
        
        # Validate provider availability and check for double-booking
        duration_minutes = attrs.get('duration_minutes', 30)
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
        
        if user:
            validated_data['created_by'] = user
            
            # Set created_by_role based on who's creating
            if user.is_staff or user.is_superuser:
                validated_data['created_by_role'] = CreatedByRole.ADMIN
            elif hasattr(user, 'provider_profile'):
                validated_data['created_by_role'] = CreatedByRole.PROVIDER
            else:
                validated_data['created_by_role'] = CreatedByRole.PATIENT
        
        return super().create(validated_data)


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
    """Serializer for confirming an appointment."""
    notes = serializers.CharField(required=False, allow_blank=True)


class AppointmentCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an appointment."""
    reason = serializers.ChoiceField(
        choices=CancellationReason.choices,
        default=CancellationReason.OTHER
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class AppointmentCompleteSerializer(serializers.Serializer):
    """Serializer for completing an appointment."""
    provider_notes = serializers.CharField(required=False, allow_blank=True)


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
