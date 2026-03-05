"""
Appointment scheduling services.

Provides business logic for:
- Provider availability checking
- Double-booking prevention
- Scheduling conflict detection
- Available time slot calculation
"""
from datetime import datetime, date, time, timedelta
from typing import List, Tuple, Optional
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    Appointment,
    ProviderAvailability,
    ProviderTimeOff,
    AppointmentStatus,
    AppointmentLocationType,
)
from providers.models import Provider
from common.domain_helpers import BookingWindowValidator, AppointmentStatusTransition


class SchedulingService:
    """
    Service class for appointment scheduling operations.
    
    Handles:
    - Availability checking
    - Conflict detection
    - Time slot generation
    """
    
    # Use centralized booking window configuration
    MIN_BOOKING_NOTICE_HOURS = BookingWindowValidator.MIN_BOOKING_NOTICE_HOURS
    MAX_ADVANCE_BOOKING_DAYS = BookingWindowValidator.MAX_ADVANCE_BOOKING_DAYS
    
    @classmethod
    def check_provider_available(
        cls,
        provider: Provider,
        scheduled_date: date,
        scheduled_time: time,
        duration_minutes: int,
        location_type: str = AppointmentLocationType.CLINIC,
        exclude_appointment_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if a provider is available for an appointment.
        
        Args:
            provider: The provider to check
            scheduled_date: Date of appointment
            scheduled_time: Start time of appointment
            duration_minutes: Duration in minutes
            location_type: Type of appointment location
            exclude_appointment_id: Appointment ID to exclude (for rescheduling)
            
        Returns:
            Tuple of (is_available, message)
        """
        # 1. Check if date is too far in the future
        max_date = timezone.now().date() + timedelta(days=cls.MAX_ADVANCE_BOOKING_DAYS)
        if scheduled_date > max_date:
            return False, f"Cannot book more than {cls.MAX_ADVANCE_BOOKING_DAYS} days in advance."
        
        # 2. Check minimum booking notice
        appointment_datetime = timezone.make_aware(
            datetime.combine(scheduled_date, scheduled_time)
        )
        min_booking_time = timezone.now() + timedelta(hours=cls.MIN_BOOKING_NOTICE_HOURS)
        if appointment_datetime < min_booking_time:
            return False, f"Appointments require at least {cls.MIN_BOOKING_NOTICE_HOURS} hour(s) notice."
        
        # 3. Check for provider time off
        if cls._is_provider_on_time_off(provider, scheduled_date, scheduled_time, duration_minutes):
            return False, "Provider is not available on this date (time off)."
        
        # 4. Check provider availability schedule
        if not cls._is_within_availability(provider, scheduled_date, scheduled_time, duration_minutes, location_type):
            return False, "This time slot is outside the provider's available hours."
        
        # 5. Check for scheduling conflicts (double-booking)
        has_conflict, conflict_msg = cls._check_scheduling_conflict(
            provider, scheduled_date, scheduled_time, duration_minutes, exclude_appointment_id
        )
        if has_conflict:
            return False, conflict_msg
        
        return True, "Time slot is available."
    
    @classmethod
    def _is_provider_on_time_off(
        cls,
        provider: Provider,
        scheduled_date: date,
        scheduled_time: time,
        duration_minutes: int
    ) -> bool:
        """Check if the provider has time off during this slot."""
        appointment_start = timezone.make_aware(
            datetime.combine(scheduled_date, scheduled_time)
        )
        appointment_end = appointment_start + timedelta(minutes=duration_minutes)
        
        # Check for overlapping time off periods
        time_off = ProviderTimeOff.objects.filter(
            provider=provider,
            start_datetime__lt=appointment_end,
            end_datetime__gt=appointment_start
        ).exists()
        
        return time_off
    
    @classmethod
    def _is_within_availability(
        cls,
        provider: Provider,
        scheduled_date: date,
        scheduled_time: time,
        duration_minutes: int,
        location_type: str
    ) -> bool:
        """Check if the appointment falls within provider's availability."""
        day_of_week = scheduled_date.weekday()
        end_time = (
            datetime.combine(date.min, scheduled_time) + 
            timedelta(minutes=duration_minutes)
        ).time()
        
        # Query for matching availability slots
        availability_query = ProviderAvailability.objects.filter(
            provider=provider,
            day_of_week=day_of_week,
            is_active=True,
            start_time__lte=scheduled_time,
            end_time__gte=end_time
        )
        
        # Filter by location type if not 'ALL'
        if location_type != 'ALL':
            availability_query = availability_query.filter(
                Q(location_type=location_type) | Q(location_type='ALL')
            )
        
        # If no availability is configured, allow booking (provider hasn't set up schedule)
        if not ProviderAvailability.objects.filter(provider=provider, is_active=True).exists():
            return True
        
        return availability_query.exists()
    
    @classmethod
    def _check_scheduling_conflict(
        cls,
        provider: Provider,
        scheduled_date: date,
        scheduled_time: time,
        duration_minutes: int,
        exclude_appointment_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check for double-booking conflicts.
        
        Uses centralized status definitions to determine which appointments
        should be considered for conflict checking.
        
        Returns:
            Tuple of (has_conflict, message)
        """
        appointment_start = timezone.make_aware(
            datetime.combine(scheduled_date, scheduled_time)
        )
        appointment_end = appointment_start + timedelta(minutes=duration_minutes)
        
        # Get the day's availability to check max_appointments
        day_of_week = scheduled_date.weekday()
        availability = ProviderAvailability.objects.filter(
            provider=provider,
            day_of_week=day_of_week,
            is_active=True,
            start_time__lte=scheduled_time
        ).first()
        
        max_concurrent = availability.max_appointments if availability else 1
        
        # Find overlapping appointments using centralized active statuses
        # These are statuses that should block the time slot
        active_statuses = list(AppointmentStatusTransition.ACTIVE_STATUSES)
        overlapping_query = Appointment.objects.filter(
            provider=provider,
            scheduled_date=scheduled_date,
            status__in=active_statuses
        )
        
        # Exclude the current appointment if rescheduling
        if exclude_appointment_id:
            overlapping_query = overlapping_query.exclude(pk=exclude_appointment_id)
        
        # Check for time overlaps
        conflicting_appointments = []
        for apt in overlapping_query:
            apt_start = apt.get_scheduled_datetime()
            apt_end = apt.get_end_datetime()
            
            # Check if times overlap
            if apt_start < appointment_end and apt_end > appointment_start:
                conflicting_appointments.append(apt)
        
        if len(conflicting_appointments) >= max_concurrent:
            if max_concurrent == 1:
                return True, "This time slot is already booked."
            else:
                return True, f"Maximum appointments ({max_concurrent}) reached for this time slot."
        
        return False, ""
    
    @classmethod
    def get_available_slots(
        cls,
        provider: Provider,
        target_date: date,
        duration_minutes: int = 30,
        location_type: str = AppointmentLocationType.CLINIC,
        slot_interval_minutes: int = 15
    ) -> List[dict]:
        """
        Get available time slots for a provider on a given date.
        
        Args:
            provider: The provider to check
            target_date: The date to check
            duration_minutes: Required appointment duration
            location_type: Type of appointment
            slot_interval_minutes: Interval between slot start times
            
        Returns:
            List of available slot dictionaries with start_time and end_time
        """
        available_slots = []
        day_of_week = target_date.weekday()
        
        # Get provider's availability for this day
        availability_slots = ProviderAvailability.objects.filter(
            provider=provider,
            day_of_week=day_of_week,
            is_active=True
        )
        
        # Filter by location type
        if location_type != 'ALL':
            availability_slots = availability_slots.filter(
                Q(location_type=location_type) | Q(location_type='ALL')
            )
        
        # If no availability set, generate default slots (9 AM - 5 PM)
        if not availability_slots.exists():
            availability_slots = [{
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'max_appointments': 1
            }]
        else:
            availability_slots = list(availability_slots.values(
                'start_time', 'end_time', 'max_appointments'
            ))
        
        for slot in availability_slots:
            current_time = datetime.combine(target_date, slot['start_time'])
            end_time = datetime.combine(target_date, slot['end_time'])
            
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=duration_minutes)).time()
                
                # Check if this slot is available
                is_available, _ = cls.check_provider_available(
                    provider=provider,
                    scheduled_date=target_date,
                    scheduled_time=slot_start,
                    duration_minutes=duration_minutes,
                    location_type=location_type
                )
                
                if is_available:
                    available_slots.append({
                        'start_time': slot_start.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M'),
                        'duration_minutes': duration_minutes
                    })
                
                current_time += timedelta(minutes=slot_interval_minutes)
        
        return available_slots
    
    @classmethod
    def get_provider_schedule(
        cls,
        provider: Provider,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Get provider's schedule with appointments for a date range.
        
        Returns a dictionary with:
        - availability: Provider's availability slots
        - time_off: Time off periods
        - appointments: Existing appointments
        """
        # Get availability
        availability = ProviderAvailability.objects.filter(
            provider=provider,
            is_active=True
        ).values(
            'day_of_week', 'start_time', 'end_time', 'location_type', 'max_appointments'
        )
        
        # Get time off
        time_off = ProviderTimeOff.objects.filter(
            provider=provider,
            start_datetime__date__lte=end_date,
            end_datetime__date__gte=start_date
        ).values('start_datetime', 'end_datetime', 'reason')
        
        # Get appointments
        appointments = Appointment.objects.filter(
            provider=provider,
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date,
            status__in=[
                AppointmentStatus.PENDING,
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.RESCHEDULED
            ]
        ).values(
            'id', 'scheduled_date', 'scheduled_time', 'duration_minutes',
            'status', 'location_type'
        )
        
        return {
            'availability': list(availability),
            'time_off': list(time_off),
            'appointments': list(appointments)
        }


class AppointmentService:
    """
    Service class for appointment operations.
    """
    
    @classmethod
    def create_appointment(
        cls,
        provider: Provider,
        created_by_user,
        scheduled_date: date,
        scheduled_time: time,
        duration_minutes: int = 30,
        patient_user=None,
        patient_record=None,
        service=None,
        location_type: str = AppointmentLocationType.CLINIC,
        reason: str = '',
        notes: str = '',
        clinic_address=None,
        home_address=None,
        meeting_link: str = ''
    ) -> Appointment:
        """
        Create an appointment with full validation.
        
        Validates:
        - Provider availability
        - No double-booking
        - Required fields based on location type
        """
        from .models import CreatedByRole
        
        # Validate patient identification
        if not patient_user and not patient_record:
            raise ValidationError("Either patient_user or patient_record must be provided.")
        if patient_user and patient_record:
            raise ValidationError("Cannot have both patient_user and patient_record.")
        
        # Check provider availability
        is_available, message = SchedulingService.check_provider_available(
            provider=provider,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
            location_type=location_type
        )
        
        if not is_available:
            raise ValidationError(message)
        
        # Determine created_by_role
        if created_by_user.is_staff or created_by_user.is_superuser:
            created_by_role = CreatedByRole.ADMIN
        elif hasattr(created_by_user, 'provider_profile'):
            created_by_role = CreatedByRole.PROVIDER
        else:
            created_by_role = CreatedByRole.PATIENT
        
        # Create the appointment
        appointment = Appointment.objects.create(
            provider=provider,
            patient_user=patient_user,
            patient_record=patient_record,
            service=service,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            duration_minutes=duration_minutes,
            location_type=location_type,
            reason=reason,
            notes=notes,
            clinic_address=clinic_address,
            home_address=home_address,
            meeting_link=meeting_link,
            created_by=created_by_user,
            created_by_role=created_by_role
        )
        
        return appointment
    
    @classmethod
    def reschedule_appointment(
        cls,
        appointment: Appointment,
        new_date: date,
        new_time: time,
        rescheduled_by_user
    ) -> Appointment:
        """
        Reschedule an existing appointment.
        
        Uses centralized status transition validation to ensure only
        valid statuses can be rescheduled.
        """
        from .models import AppointmentStatus
        
        # Use centralized validation
        AppointmentStatusTransition.validate_transition(
            appointment.status, 
            AppointmentStatus.RESCHEDULED
        )
        
        # Check availability for new slot (excluding current appointment)
        is_available, message = SchedulingService.check_provider_available(
            provider=appointment.provider,
            scheduled_date=new_date,
            scheduled_time=new_time,
            duration_minutes=appointment.duration_minutes,
            location_type=appointment.location_type,
            exclude_appointment_id=str(appointment.id)
        )
        
        if not is_available:
            raise ValidationError(message)
        
        # Store old values for notification/audit
        old_date = appointment.scheduled_date
        old_time = appointment.scheduled_time
        
        # Update appointment
        appointment.scheduled_date = new_date
        appointment.scheduled_time = new_time
        appointment.status = AppointmentStatus.RESCHEDULED
        appointment.save(update_fields=[
            'scheduled_date', 'scheduled_time', 'status', 'updated_at'
        ])
        
        return appointment
    
    @classmethod
    def get_patient_history(
        cls,
        patient_user=None,
        patient_record=None,
        include_upcoming: bool = False
    ):
        """
        Get appointment history for a patient.
        
        By default, returns only past/completed/cancelled appointments.
        """
        if not patient_user and not patient_record:
            raise ValidationError("Patient identification required.")
        
        queryset = Appointment.objects.select_related(
            'provider', 'provider__user', 'service'
        )
        
        if patient_user:
            queryset = queryset.filter(patient_user=patient_user)
        else:
            queryset = queryset.filter(patient_record=patient_record)
        
        if not include_upcoming:
            queryset = queryset.filter(
                Q(status__in=[
                    AppointmentStatus.COMPLETED,
                    AppointmentStatus.CANCELLED,
                    AppointmentStatus.NO_SHOW
                ]) |
                Q(scheduled_date__lt=timezone.now().date())
            )
        
        return queryset.order_by('-scheduled_date', '-scheduled_time')
    
    @classmethod
    def get_provider_appointments(
        cls,
        provider: Provider,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        search: Optional[str] = None,
        location_type: Optional[str] = None
    ):
        """
        Get appointments for a provider with advanced filtering.
        """
        queryset = Appointment.objects.filter(
            provider=provider
        ).select_related(
            'patient_user', 'patient_record', 'service', 'clinic_address', 'home_address'
        )
        
        # Apply filters
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(scheduled_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(scheduled_date__lte=date_to)
        
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        if search:
            queryset = queryset.filter(
                Q(patient_user__first_name__icontains=search) |
                Q(patient_user__last_name__icontains=search) |
                Q(patient_user__email__icontains=search) |
                Q(patient_record__first_name__icontains=search) |
                Q(patient_record__last_name__icontains=search) |
                Q(reason__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('-scheduled_date', '-scheduled_time')

    @classmethod
    def auto_cancel_past_appointments(cls, grace_minutes: int = 15) -> int:
        """
        Auto-cancel appointments whose scheduled start time has passed.

        - Targets only active statuses (PENDING/CONFIRMED/RESCHEDULED)
        - Applies a small grace period (default 15 minutes)
        - Marks them as CANCELLED with reason NO_RESPONSE
        - Lets post_save signals broadcast notifications
        """
        from .models import CancellationReason

        now = timezone.now()
        cutoff = now - timedelta(minutes=grace_minutes)

        # Build cutoff conditions: past date, or today with time already passed
        # For appointments with no scheduled_time, cancel once the entire day has passed
        past_q = (
            Q(scheduled_date__lt=cutoff.date()) |
            (
                Q(scheduled_date=cutoff.date()) &
                Q(scheduled_time__isnull=False) &
                Q(scheduled_time__lt=cutoff.time())
            )
        )

        queryset = Appointment.objects.filter(
            status__in=list(AppointmentStatusTransition.ACTIVE_STATUSES)
        ).filter(past_q)

        count = 0
        for appt in queryset.select_related('provider', 'patient_user'):
            try:
                # Cancellation notes kept succinct for audit and notifications
                appt.cancel(
                    cancelled_by=None,
                    reason=CancellationReason.NO_RESPONSE,
                    notes='Auto-cancelled: scheduled time passed without completion.',
                    save=True,
                )
                count += 1
            except Exception:
                # Fail soft per appointment to allow others to continue
                continue

        return count
