"""
Appointment models for the Medilink platform.

This module provides comprehensive appointment scheduling with:
- Provider availability management
- Double-booking prevention
- Status lifecycle enforcement
- Patient/Provider creation tracking
- Scheduling conflict detection

Key features:
- Appointments can be created by both patients and providers
- Supports clinic, home visit, and online appointment locations
- Full status lifecycle (pending, confirmed, cancelled, completed, no-show)
- Links to PatientRecord for patients without accounts
- Integrates with the services and address apps
"""
import uuid
from datetime import timedelta, datetime, time
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

from accounts.models import User
from providers.models.provider import Provider
from patients.models import PatientRecord


class DayOfWeek(models.IntegerChoices):
    """Days of the week for availability scheduling."""
    MONDAY = 0, 'Monday'
    TUESDAY = 1, 'Tuesday'
    WEDNESDAY = 2, 'Wednesday'
    THURSDAY = 3, 'Thursday'
    FRIDAY = 4, 'Friday'
    SATURDAY = 5, 'Saturday'
    SUNDAY = 6, 'Sunday'


class ProviderAvailability(models.Model):
    """
    Provider weekly availability schedule.
    
    Defines recurring time slots when a provider is available for appointments.
    Multiple slots per day are supported for lunch breaks, etc.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='availability_slots',
        help_text='Provider this availability belongs to'
    )
    day_of_week = models.IntegerField(
        choices=DayOfWeek.choices,
        help_text='Day of the week'
    )
    start_time = models.TimeField(
        help_text='Start time of availability window'
    )
    end_time = models.TimeField(
        help_text='End time of availability window'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this availability slot is active'
    )
    # Location type available during this slot
    location_type = models.CharField(
        max_length=20,
        choices=[
            ('CLINIC', 'At Clinic'),
            ('HOME', 'Home Visit'),
            ('ONLINE', 'Online/Telemedicine'),
            ('ALL', 'All Location Types'),
        ],
        default='ALL',
        help_text='Type of appointments available during this slot'
    )
    # Slot capacity (for clinics that can handle multiple patients at once)
    max_appointments = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Maximum concurrent appointments in this slot'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'provider_availability'
        verbose_name = 'Provider Availability'
        verbose_name_plural = 'Provider Availabilities'
        ordering = ['day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['provider', 'day_of_week']),
            models.Index(fields=['is_active']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(start_time__lt=models.F('end_time')),
                name='availability_start_before_end'
            ),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def clean(self):
        """Validate that start_time is before end_time."""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': 'End time must be after start time.'
                })


class ProviderTimeOff(models.Model):
    """
    Provider time off / unavailability periods.
    
    For vacations, holidays, sick days, or any blocked time.
    Takes precedence over ProviderAvailability.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='time_off_periods',
        help_text='Provider this time off belongs to'
    )
    start_datetime = models.DateTimeField(
        help_text='Start of unavailable period'
    )
    end_datetime = models.DateTimeField(
        help_text='End of unavailable period'
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text='Reason for time off'
    )
    is_recurring_annual = models.BooleanField(
        default=False,
        help_text='Whether this repeats annually (e.g., holidays)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'provider_time_off'
        verbose_name = 'Provider Time Off'
        verbose_name_plural = 'Provider Time Off Periods'
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['provider', 'start_datetime', 'end_datetime']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.start_datetime.date()} to {self.end_datetime.date()}"
    
    def clean(self):
        """Validate that start is before end."""
        if self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError({
                    'end_datetime': 'End datetime must be after start datetime.'
                })

class AppointmentStatus(models.TextChoices):
    """Appointment status choices."""
    PENDING = 'PENDING', 'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    COMPLETED = 'COMPLETED', 'Completed'
    NO_SHOW = 'NO_SHOW', 'No Show'
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'


class AppointmentLocationType(models.TextChoices):
    """Where the appointment takes place."""
    CLINIC = 'CLINIC', 'At Clinic'
    HOME = 'HOME', 'Home Visit'
    ONLINE = 'ONLINE', 'Online/Video Call'


class CancellationReason(models.TextChoices):
    """Predefined cancellation reasons."""
    PATIENT_REQUEST = 'PATIENT_REQUEST', 'Patient Request'
    PROVIDER_UNAVAILABLE = 'PROVIDER_UNAVAILABLE', 'Provider Unavailable'
    EMERGENCY = 'EMERGENCY', 'Emergency'
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'
    NO_RESPONSE = 'NO_RESPONSE', 'No Response'
    OTHER = 'OTHER', 'Other'


class CreatedByRole(models.TextChoices):
    """Who created the appointment."""
    PATIENT = 'PATIENT', 'Created by Patient'
    PROVIDER = 'PROVIDER', 'Created by Provider'
    ADMIN = 'ADMIN', 'Created by Admin'
    SYSTEM = 'SYSTEM', 'System Generated'


class Appointment(models.Model):
    """
    Appointment model for scheduling between patients and providers.
    
    Appointments can be created by:
    - Patients (with accounts) booking with providers
    - Providers creating appointments for patients (with or without accounts)
    
    The patient can be identified either by:
    - patient_user: A registered User account
    - patient_record: A PatientRecord (for patients without accounts)
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Provider (required)
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='appointments',
        help_text='Healthcare provider for this appointment'
    )
    
    # Patient identification (one of these must be set)
    patient_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='patient_appointments',
        help_text='Patient with a user account'
    )
    patient_record = models.ForeignKey(
        PatientRecord,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='appointments',
        help_text='Patient record (for patients without accounts)'
    )
    
    # Service being provided (optional)
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments',
        help_text='Service being provided'
    )
    
    # Scheduling
    scheduled_date = models.DateField(
        db_index=True,
        help_text='Date of the appointment'
    )
    scheduled_time = models.TimeField(
        help_text='Start time of the appointment'
    )
    duration_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(5)],
        help_text='Duration of appointment in minutes'
    )
    
    # Location
    location_type = models.CharField(
        max_length=20,
        choices=AppointmentLocationType.choices,
        default=AppointmentLocationType.CLINIC,
        help_text='Type of appointment location'
    )
    
    # For clinic appointments - link to provider's clinic address
    clinic_address = models.ForeignKey(
        'address.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clinic_appointments',
        help_text='Clinic address for the appointment'
    )
    
    # For home visits - patient's address
    home_address = models.ForeignKey(
        'address.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='home_appointments',
        help_text='Home address for home visit appointments'
    )
    
    # For online appointments
    meeting_link = models.URLField(
        blank=True,
        help_text='Video call link for online appointments'
    )
    
    # Status and notes
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
        db_index=True,
        help_text='Current status of the appointment'
    )
    reason = models.TextField(
        blank=True,
        help_text='Reason for the appointment / Chief complaint'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes for the appointment'
    )
    
    # Provider notes (visible only to provider)
    provider_notes = models.TextField(
        blank=True,
        help_text='Private notes for the provider'
    )
    
    # Cancellation info
    cancellation_reason = models.CharField(
        max_length=30,
        choices=CancellationReason.choices,
        blank=True,
        help_text='Reason for cancellation'
    )
    cancellation_notes = models.TextField(
        blank=True,
        help_text='Additional cancellation details'
    )
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_appointments',
        help_text='User who cancelled the appointment'
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the appointment was cancelled'
    )
    
    # Who created the appointment
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_appointments',
        help_text='User who created this appointment'
    )
    
    # Source of creation (tracks who initiated)
    created_by_role = models.CharField(
        max_length=20,
        choices=CreatedByRole.choices,
        default=CreatedByRole.PATIENT,
        help_text='Role of the user who created this appointment'
    )
    
    # Confirmation
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the appointment was confirmed'
    )
    
    # Completion
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the appointment was completed'
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the appointment was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'appointments'
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
        ordering = ['scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['provider', 'scheduled_date']),
            models.Index(fields=['patient_user', 'scheduled_date']),
            models.Index(fields=['patient_record', 'scheduled_date']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date', 'status']),
        ]
        constraints = [
            # Ensure at least one patient identifier is provided
            models.CheckConstraint(
                condition=(
                    models.Q(patient_user__isnull=False) |
                    models.Q(patient_record__isnull=False)
                ),
                name='appointment_has_patient'
            ),
            # Ensure not both patient types are set
            models.CheckConstraint(
                condition=~(
                    models.Q(patient_user__isnull=False) &
                    models.Q(patient_record__isnull=False)
                ),
                name='appointment_single_patient_type'
            ),
        ]
    
    def __str__(self):
        patient_name = self.get_patient_display_name()
        return f'{patient_name} with {self.provider} on {self.scheduled_date}'
    
    def clean(self):
        """Validate the appointment."""
        super().clean()
        
        # Validate patient identification
        if not self.patient_user and not self.patient_record:
            raise ValidationError(
                'Either patient_user or patient_record must be provided.'
            )
        
        if self.patient_user and self.patient_record:
            raise ValidationError(
                'Cannot have both patient_user and patient_record.'
            )
        
        # Validate location-specific fields
        if self.location_type == AppointmentLocationType.ONLINE and not self.meeting_link:
            # Meeting link can be added later
            pass
        
        # Validate scheduling (appointment should be in the future for new appointments)
        if not self.pk:  # New appointment
            appointment_datetime = timezone.datetime.combine(
                self.scheduled_date,
                self.scheduled_time
            )
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            
            if appointment_datetime < timezone.now():
                raise ValidationError(
                    'Appointment cannot be scheduled in the past.'
                )
    
    def get_patient_display_name(self):
        """Get display name for the patient."""
        if self.patient_user:
            return self.patient_user.get_full_name() or self.patient_user.email
        if self.patient_record:
            return f'{self.patient_record.first_name} {self.patient_record.last_name}'
        return 'Unknown Patient'
    
    def get_scheduled_datetime(self):
        """Get the full datetime of the appointment."""
        dt = timezone.datetime.combine(self.scheduled_date, self.scheduled_time)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt
    
    def get_end_datetime(self):
        """Get the end datetime of the appointment."""
        from datetime import timedelta
        return self.get_scheduled_datetime() + timedelta(minutes=self.duration_minutes)
    
    def confirm(self, save=True):
        """Confirm the appointment."""
        if self.status != AppointmentStatus.PENDING:
            raise ValidationError(f'Cannot confirm appointment with status {self.status}')
        
        self.status = AppointmentStatus.CONFIRMED
        self.confirmed_at = timezone.now()
        
        if save:
            self.save(update_fields=['status', 'confirmed_at', 'updated_at'])
    
    def cancel(self, cancelled_by, reason=CancellationReason.OTHER, notes='', save=True):
        """Cancel the appointment."""
        if self.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise ValidationError(f'Cannot cancel appointment with status {self.status}')
        
        self.status = AppointmentStatus.CANCELLED
        self.cancelled_by = cancelled_by
        self.cancelled_at = timezone.now()
        self.cancellation_reason = reason
        self.cancellation_notes = notes
        
        if save:
            self.save(update_fields=[
                'status', 'cancelled_by', 'cancelled_at',
                'cancellation_reason', 'cancellation_notes', 'updated_at'
            ])
    
    def complete(self, save=True):
        """Mark the appointment as completed."""
        if self.status != AppointmentStatus.CONFIRMED:
            raise ValidationError(f'Cannot complete appointment with status {self.status}')
        
        self.status = AppointmentStatus.COMPLETED
        self.completed_at = timezone.now()
        
        if save:
            self.save(update_fields=['status', 'completed_at', 'updated_at'])
    
    def mark_no_show(self, save=True):
        """Mark the appointment as no-show."""
        if self.status != AppointmentStatus.CONFIRMED:
            raise ValidationError(f'Cannot mark as no-show with status {self.status}')
        
        self.status = AppointmentStatus.NO_SHOW
        
        if save:
            self.save(update_fields=['status', 'updated_at'])
    
    @property
    def is_upcoming(self):
        """Check if the appointment is upcoming."""
        return (
            self.status in [AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED] and
            self.get_scheduled_datetime() > timezone.now()
        )
    
    @property
    def is_past(self):
        """Check if the appointment is in the past."""
        return self.get_scheduled_datetime() < timezone.now()


class AppointmentReminder(models.Model):
    """
    Reminders for appointments.
    """
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    remind_at = models.DateTimeField(
        db_index=True,
        help_text='When to send the reminder'
    )
    sent = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether the reminder has been sent'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the reminder was sent'
    )
    
    class Meta:
        db_table = 'appointment_reminders'
        verbose_name = 'Appointment Reminder'
        verbose_name_plural = 'Appointment Reminders'
        ordering = ['remind_at']
    
    def __str__(self):
        return f'Reminder for {self.appointment} at {self.remind_at}'
