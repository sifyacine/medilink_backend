from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class RequestStatus(models.TextChoices):
    """Status choices for nurse service requests"""
    CREATED = 'CREATED', _('Created')
    SEARCHING = 'SEARCHING', _('Searching for Nurses')
    NURSE_RESPONDED = 'NURSE_RESPONDED', _('Nurses Responded')
    PATIENT_DECISION = 'PATIENT_DECISION', _('Awaiting Patient Decision')
    ACCEPTED = 'ACCEPTED', _('Accepted')
    IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
    COMPLETED = 'COMPLETED', _('Completed')
    CANCELLED = 'CANCELLED', _('Cancelled')


class OfferStatus(models.TextChoices):
    """Status choices for nurse offers"""
    PENDING = 'PENDING', _('Pending')
    ACCEPTED = 'ACCEPTED', _('Accepted by Patient')
    REJECTED = 'REJECTED', _('Rejected')
    COUNTER_OFFERED = 'COUNTER_OFFERED', _('Counter Offered')
    EXPIRED = 'EXPIRED', _('Expired')


# NursingService model removed - now using services.Service with service_type='NURSE' and is_on_demand=True


class NurseServiceRequest(models.Model):
    """
    Patient's request for on-demand nursing service.
    Follows an Uber-like flow with location and pricing.
    
    Patient identification (one of these must be set):
    - patient_user: For patients with Medilink accounts
    - patient_record: For patients without accounts
    """
    # Patient identification (one of these must be set)
    patient_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='nurse_service_requests',
        help_text=_("Patient with a user account")
    )
    patient_record = models.ForeignKey(
        'patients.PatientRecord',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='nurse_service_requests',
        help_text=_("Patient record (for patients without accounts)")
    )
    
    # Service - uses the main Service model from services app
    # Only services with service_type='NURSE' and is_on_demand=True are valid
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.PROTECT,
        related_name='nurse_requests',
        help_text=_("Nursing service from the services catalog")
    )
    accepted_nurse = models.ForeignKey(
        'providers.Provider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_nurse_requests',
        limit_choices_to={'provider_type': 'NURSE'}
    )

    # Pricing
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Service base price at time of request")
    )
    patient_offered_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("Price offered by patient (>= base_price)")
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Final agreed price after acceptance")
    )

    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    city = models.CharField(max_length=100)
    address_line = models.CharField(max_length=500, blank=True)

    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.CREATED
    )
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Nurse Service Request')
        verbose_name_plural = _('Nurse Service Requests')
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['city', 'status']),
        ]

    def __str__(self):
        patient_name = self.get_patient_display_name()
        return f"Request #{self.id} - {self.service.title} by {patient_name}"
    
    def get_patient_display_name(self):
        """Get the display name for the patient."""
        if self.patient_user:
            return f"{self.patient_user.first_name} {self.patient_user.last_name}".strip() or self.patient_user.email
        elif self.patient_record:
            return f"{self.patient_record.first_name} {self.patient_record.last_name}".strip()
        return "Unknown Patient"
    
    def get_patient_user(self):
        """Get the user associated with the patient (if any)."""
        if self.patient_user:
            return self.patient_user
        elif self.patient_record and self.patient_record.linked_user:
            return self.patient_record.linked_user
        return None

    def save(self, *args, **kwargs):
        # Ensure patient_offered_price is >= base_price
        if self.patient_offered_price < self.base_price:
            raise ValueError(
                f"Patient offered price (${self.patient_offered_price}) cannot be "
                f"lower than base price (${self.base_price})"
            )
        super().save(*args, **kwargs)


class NurseOffer(models.Model):
    """
    Nurse's response to a service request.
    Can be acceptance, counter-offer, or rejection.
    """
    request = models.ForeignKey(
        NurseServiceRequest,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    nurse = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='nurse_offers',
        limit_choices_to={'provider_type': 'NURSE'}
    )
    
    # Offer details
    offered_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_("Price offered by nurse (>= patient_offered_price)")
    )
    status = models.CharField(
        max_length=20,
        choices=OfferStatus.choices,
        default=OfferStatus.PENDING
    )
    
    # Additional info
    estimated_arrival_time = models.DurationField(
        null=True,
        blank=True,
        help_text=_("Estimated time to reach patient location")
    )
    notes = models.TextField(blank=True)
    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Distance from nurse to patient in kilometers")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['offered_price', '-created_at']
        verbose_name = _('Nurse Offer')
        verbose_name_plural = _('Nurse Offers')
        unique_together = ['request', 'nurse']
        indexes = [
            models.Index(fields=['request', 'status']),
            models.Index(fields=['nurse', '-created_at']),
        ]

    def __str__(self):
        return f"Offer by {self.nurse} for Request #{self.request.id} - ${self.offered_price}"

    def save(self, *args, **kwargs):
        # Validate offered price is >= patient's offered price and base price
        if self.offered_price < self.request.patient_offered_price:
            raise ValueError(
                f"Nurse offered price (${self.offered_price}) cannot be lower than "
                f"patient's offered price (${self.request.patient_offered_price})"
            )
        if self.offered_price < self.request.base_price:
            raise ValueError(
                f"Nurse offered price (${self.offered_price}) cannot be lower than "
                f"base price (${self.request.base_price})"
            )
        super().save(*args, **kwargs)


class RequestHistory(models.Model):
    """
    Audit trail for all state changes and actions on a request.
    Useful for debugging, analytics, and transparency.
    """
    request = models.ForeignKey(
        NurseServiceRequest,
        on_delete=models.CASCADE,
        related_name='history'
    )
    actor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    action = models.CharField(max_length=100)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Request History')
        verbose_name_plural = _('Request Histories')

    def __str__(self):
        return f"{self.action} on Request #{self.request.id} at {self.timestamp}"
