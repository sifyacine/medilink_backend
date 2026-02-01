"""
Invoice models for the Medilink platform.

This module provides comprehensive invoice management with:
- Provider-issued invoices to patients
- Support for services, custom services, products, and custom line items
- Payment tracking with multiple payment methods
- Invoice status workflow (DRAFT → SENT → PAID/OVERDUE/CANCELLED)
- Tax and discount support
- Appointment integration
- Prescription integration
- Multi-currency support (DZD, USD, EUR)

Invoice Types:
- SERVICE: For healthcare services provided
- PRODUCT: For products sold (pharmacy, medical supplies)
- MIXED: Combination of services and products
- CUSTOM: Manual invoice with custom items

Integration Points:
- Appointments: Auto-generate invoice when appointment is completed
- Prescriptions: Invoice for dispensed medications
- Nurse Requests: Invoice for on-demand nursing services
- Direct Sales: Invoice for products sold by sellers
"""
import uuid
import secrets
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import User
from providers.models.provider import Provider
from services.models import Currency


def generate_invoice_number():
    """
    Generate a unique invoice number.
    Format: INV-YYYYMMDD-XXXXXXXX (e.g., INV-20240115-A1B2C3D4)
    """
    date_part = timezone.now().strftime('%Y%m%d')
    random_part = secrets.token_hex(4).upper()
    return f"INV-{date_part}-{random_part}"


class InvoiceStatus(models.TextChoices):
    """Invoice status choices."""
    DRAFT = 'DRAFT', 'Draft'  # Invoice created but not sent
    SENT = 'SENT', 'Sent'  # Invoice sent to patient
    VIEWED = 'VIEWED', 'Viewed'  # Patient has viewed the invoice
    PARTIALLY_PAID = 'PARTIALLY_PAID', 'Partially Paid'  # Partial payment received
    PAID = 'PAID', 'Paid'  # Fully paid
    OVERDUE = 'OVERDUE', 'Overdue'  # Past due date
    CANCELLED = 'CANCELLED', 'Cancelled'  # Invoice cancelled
    REFUNDED = 'REFUNDED', 'Refunded'  # Full refund issued
    PARTIALLY_REFUNDED = 'PARTIALLY_REFUNDED', 'Partially Refunded'  # Partial refund


class InvoiceType(models.TextChoices):
    """Invoice type choices."""
    SERVICE = 'SERVICE', 'Service Invoice'  # Healthcare services
    PRODUCT = 'PRODUCT', 'Product Invoice'  # Products/medications
    MIXED = 'MIXED', 'Mixed Invoice'  # Services + Products
    CUSTOM = 'CUSTOM', 'Custom Invoice'  # Manual/custom items


class PaymentMethod(models.TextChoices):
    """Payment method choices."""
    CASH = 'CASH', 'Cash'
    CARD = 'CARD', 'Credit/Debit Card'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
    MOBILE_PAYMENT = 'MOBILE_PAYMENT', 'Mobile Payment'  # CCP, BaridiMob, etc.
    INSURANCE = 'INSURANCE', 'Insurance'
    CHEQUE = 'CHEQUE', 'Cheque'
    OTHER = 'OTHER', 'Other'


class ItemType(models.TextChoices):
    """Invoice item type choices."""
    SERVICE = 'SERVICE', 'Service'  # From services.Service
    CUSTOM_SERVICE = 'CUSTOM_SERVICE', 'Custom Service'  # From ProviderCustomService
    PRODUCT = 'PRODUCT', 'Product'  # Future products
    MEDICATION = 'MEDICATION', 'Medication'  # From prescriptions
    CUSTOM = 'CUSTOM', 'Custom Item'  # Manual entry


class Invoice(models.Model):
    """
    Invoice model for billing patients.
    
    Invoices can be created:
    - Automatically when an appointment is completed
    - Automatically when a prescription is dispensed
    - Manually by providers for products/services
    
    Key Features:
    - Unique invoice number for reference
    - Links to provider (issuer) and patient (recipient)
    - Optional links to appointment, prescription
    - Line items for detailed billing
    - Tax and discount support
    - Payment tracking
    - Due date and overdue handling
    - Multilingual notes support
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Invoice identification
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_invoice_number,
        db_index=True,
        help_text='Unique invoice number (e.g., INV-20240115-A1B2C3D4)'
    )
    
    # Provider who issued the invoice
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text='Provider who issued this invoice'
    )
    
    # Patient identification (one of these must be set)
    patient_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Patient with a user account'
    )
    patient_record = models.ForeignKey(
        'patients.PatientRecord',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Patient record (for patients without accounts)'
    )
    
    # Invoice type and status
    invoice_type = models.CharField(
        max_length=20,
        choices=InvoiceType.choices,
        default=InvoiceType.SERVICE,
        db_index=True,
        help_text='Type of invoice'
    )
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True,
        help_text='Current status of the invoice'
    )
    
    # Related objects (optional)
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Related appointment (if applicable)'
    )
    prescription = models.ForeignKey(
        'prescriptions.Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Related prescription (if applicable)'
    )
    nurse_request = models.ForeignKey(
        'nurse_requests.NurseServiceRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text='Related nurse request (if applicable)'
    )
    
    # Dates
    issue_date = models.DateField(
        default=timezone.now,
        help_text='Date the invoice was issued'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text='Payment due date'
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the invoice was sent to patient'
    )
    viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the patient first viewed the invoice'
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the invoice was fully paid'
    )
    
    # Currency
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.DZD,
        help_text='Invoice currency'
    )
    
    # Amounts (calculated from items)
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Sum of all items before tax and discount'
    )
    
    # Tax
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Tax rate percentage (e.g., 19.00 for 19%)'
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Calculated tax amount'
    )
    
    # Discount
    discount_type = models.CharField(
        max_length=20,
        choices=[
            ('PERCENTAGE', 'Percentage'),
            ('FIXED', 'Fixed Amount'),
        ],
        default='FIXED',
        help_text='Type of discount'
    )
    discount_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Discount value (percentage or fixed amount)'
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Calculated discount amount'
    )
    discount_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text='Reason for discount (if any)'
    )
    
    # Total
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Final total after tax and discount'
    )
    
    # Payment tracking
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total amount paid so far'
    )
    
    @property
    def amount_due(self):
        """Calculate remaining amount due."""
        return max(self.total - self.amount_paid, Decimal('0.00'))
    
    # Notes (multilingual support)
    notes = models.TextField(
        blank=True,
        help_text='General notes on the invoice'
    )
    notes_en = models.TextField(
        blank=True,
        help_text='Notes in English'
    )
    notes_ar = models.TextField(
        blank=True,
        help_text='Notes in Arabic'
    )
    notes_fr = models.TextField(
        blank=True,
        help_text='Notes in French'
    )
    
    # Terms and conditions
    terms = models.TextField(
        blank=True,
        help_text='Payment terms and conditions'
    )
    
    # Internal notes (not shown to patient)
    internal_notes = models.TextField(
        blank=True,
        help_text='Internal notes (not visible to patient)'
    )
    
    # Cancellation
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the invoice was cancelled'
    )
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_invoices',
        help_text='User who cancelled the invoice'
    )
    cancellation_reason = models.TextField(
        blank=True,
        help_text='Reason for cancellation'
    )
    
    # Audit trail
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
        help_text='User who created this invoice'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When the invoice was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    
    class Meta:
        db_table = 'invoices'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['patient_user', 'status']),
            models.Index(fields=['patient_record', 'status']),
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['appointment']),
        ]
    
    def __str__(self):
        patient_name = self.get_patient_display_name()
        return f'{self.invoice_number} - {patient_name} ({self.status})'
    
    def clean(self):
        """Validate the invoice."""
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
        
        # Validate due date
        if self.due_date and self.issue_date and self.due_date < self.issue_date:
            raise ValidationError({
                'due_date': 'Due date cannot be before issue date.'
            })
    
    def get_patient_display_name(self):
        """Get display name for the patient."""
        from common.utils import get_patient_display_name
        return get_patient_display_name(self.patient_user, self.patient_record)
    
    def get_notes(self, language: str = 'en') -> str:
        """Get localized notes."""
        lang_map = {
            'en': self.notes_en,
            'ar': self.notes_ar,
            'fr': self.notes_fr,
        }
        localized = lang_map.get(language, '')
        return localized if localized else self.notes
    
    def calculate_totals(self):
        """
        Calculate subtotal, tax, discount, and total from items.
        Call this after modifying invoice items.
        """
        # Calculate subtotal from items
        self.subtotal = sum(
            item.total for item in self.items.all()
        ) or Decimal('0.00')
        
        # Calculate discount
        if self.discount_type == 'PERCENTAGE':
            self.discount_amount = (self.subtotal * self.discount_value / 100).quantize(Decimal('0.01'))
        else:
            self.discount_amount = min(self.discount_value, self.subtotal)
        
        # Amount after discount
        after_discount = self.subtotal - self.discount_amount
        
        # Calculate tax
        self.tax_amount = (after_discount * self.tax_rate / 100).quantize(Decimal('0.01'))
        
        # Calculate total
        self.total = after_discount + self.tax_amount
    
    def mark_as_sent(self):
        """Mark invoice as sent."""
        if self.status == InvoiceStatus.DRAFT:
            self.status = InvoiceStatus.SENT
            self.sent_at = timezone.now()
            self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_as_viewed(self):
        """Mark invoice as viewed by patient."""
        if self.status == InvoiceStatus.SENT:
            self.status = InvoiceStatus.VIEWED
            self.viewed_at = timezone.now()
            self.save(update_fields=['status', 'viewed_at', 'updated_at'])
    
    def check_overdue(self):
        """Check if invoice is overdue and update status."""
        if (self.status in [InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.PARTIALLY_PAID]
            and self.due_date
            and self.due_date < timezone.now().date()):
            self.status = InvoiceStatus.OVERDUE
            self.save(update_fields=['status', 'updated_at'])
    
    def update_payment_status(self):
        """Update status based on payment amounts."""
        if self.amount_paid >= self.total:
            self.status = InvoiceStatus.PAID
            self.paid_at = timezone.now()
        elif self.amount_paid > Decimal('0.00'):
            self.status = InvoiceStatus.PARTIALLY_PAID
            self.paid_at = None
        self.save(update_fields=['status', 'paid_at', 'updated_at'])


class InvoiceItem(models.Model):
    """
    Individual line item on an invoice.
    
    Can represent:
    - Services from the services catalog
    - Custom services created by providers
    - Products (future)
    - Medications from prescriptions
    - Custom/manual items
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent invoice'
    )
    
    # Item type
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.SERVICE,
        help_text='Type of item'
    )
    
    # References to source objects (optional based on item_type)
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items',
        help_text='Service from catalog (for SERVICE type)'
    )
    custom_service = models.ForeignKey(
        'services.ProviderCustomService',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items',
        help_text='Custom service (for CUSTOM_SERVICE type)'
    )
    prescription_item = models.ForeignKey(
        'prescriptions.PrescriptionItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_items',
        help_text='Prescription item (for MEDICATION type)'
    )
    
    # Item order
    order = models.PositiveIntegerField(
        default=0,
        help_text='Display order on invoice'
    )
    
    # Description (multilingual support)
    description = models.CharField(
        max_length=500,
        help_text='Item description'
    )
    description_en = models.CharField(
        max_length=500,
        blank=True,
        help_text='Description in English'
    )
    description_ar = models.CharField(
        max_length=500,
        blank=True,
        help_text='Description in Arabic'
    )
    description_fr = models.CharField(
        max_length=500,
        blank=True,
        help_text='Description in French'
    )
    
    # Quantity and pricing
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Quantity'
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        default='unit',
        help_text='Unit of measure (e.g., "session", "box", "unit")'
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price per unit'
    )
    
    # Item-level discount (optional)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text='Item-specific discount percentage'
    )
    
    # Calculated total
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Line item total (quantity × unit_price - discount)'
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Additional notes for this item'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoice_items'
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['item_type']),
        ]
    
    def __str__(self):
        return f'{self.invoice.invoice_number} - {self.description}'
    
    def save(self, *args, **kwargs):
        """Calculate total before saving."""
        self.calculate_total()
        # Auto-populate English description
        if not self.description_en and self.description:
            self.description_en = self.description
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate line item total."""
        subtotal = self.quantity * self.unit_price
        discount = (subtotal * self.discount_percentage / 100).quantize(Decimal('0.01'))
        self.total = subtotal - discount
    
    def get_description(self, language: str = 'en') -> str:
        """Get localized description."""
        lang_map = {
            'en': self.description_en,
            'ar': self.description_ar,
            'fr': self.description_fr,
        }
        localized = lang_map.get(language, '')
        return localized if localized else self.description
    
    @classmethod
    def from_service(cls, invoice, service, quantity=1, custom_price=None):
        """
        Create an invoice item from a Service.
        
        Args:
            invoice: Parent Invoice
            service: Service instance
            quantity: Quantity (default 1)
            custom_price: Override price (optional)
        
        Returns:
            InvoiceItem instance (not saved)
        """
        return cls(
            invoice=invoice,
            item_type=ItemType.SERVICE,
            service=service,
            description=service.title,
            description_en=service.title_en or service.title,
            description_ar=service.title_ar or '',
            description_fr=service.title_fr or '',
            quantity=Decimal(str(quantity)),
            unit='session',
            unit_price=custom_price if custom_price else service.price,
        )
    
    @classmethod
    def from_custom_service(cls, invoice, custom_service, quantity=1):
        """
        Create an invoice item from a ProviderCustomService.
        
        Args:
            invoice: Parent Invoice
            custom_service: ProviderCustomService instance
            quantity: Quantity (default 1)
        
        Returns:
            InvoiceItem instance (not saved)
        """
        return cls(
            invoice=invoice,
            item_type=ItemType.CUSTOM_SERVICE,
            custom_service=custom_service,
            description=custom_service.title,
            description_en=custom_service.title_en or custom_service.title,
            description_ar=custom_service.title_ar or '',
            description_fr=custom_service.title_fr or '',
            quantity=Decimal(str(quantity)),
            unit='session',
            unit_price=custom_service.price,
        )


class Payment(models.Model):
    """
    Payment record for an invoice.
    
    Supports:
    - Multiple payments per invoice (for partial payments)
    - Various payment methods
    - Refunds (negative amounts or separate refund records)
    - Payment verification tracking
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text='Invoice being paid'
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Payment amount'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        help_text='Method of payment'
    )
    payment_date = models.DateTimeField(
        default=timezone.now,
        help_text='When the payment was made'
    )
    
    # Reference numbers
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='External reference (transaction ID, cheque number, etc.)'
    )
    
    # For insurance payments
    insurance_claim_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Insurance claim number (for insurance payments)'
    )
    insurance_provider = models.CharField(
        max_length=200,
        blank=True,
        help_text='Insurance provider name'
    )
    
    # Verification
    is_verified = models.BooleanField(
        default=False,
        help_text='Whether payment has been verified'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the payment was verified'
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments',
        help_text='User who verified the payment'
    )
    
    # Refund tracking
    is_refund = models.BooleanField(
        default=False,
        help_text='Whether this is a refund'
    )
    refund_reason = models.TextField(
        blank=True,
        help_text='Reason for refund (if applicable)'
    )
    original_payment = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refunds',
        help_text='Original payment being refunded'
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Payment notes'
    )
    
    # Audit
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_payments',
        help_text='User who recorded this payment'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoice_payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['invoice']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f'{self.invoice.invoice_number} - {self.amount} {self.invoice.currency}'
    
    def save(self, *args, **kwargs):
        """Update invoice payment tracking after save."""
        super().save(*args, **kwargs)
        self.update_invoice_payment_total()
    
    def delete(self, *args, **kwargs):
        """Update invoice payment tracking after delete."""
        invoice = self.invoice
        super().delete(*args, **kwargs)
        self.update_invoice_payment_total(invoice)
    
    def update_invoice_payment_total(self, invoice=None):
        """Update the invoice's amount_paid field."""
        invoice = invoice or self.invoice
        total_paid = invoice.payments.filter(
            is_refund=False
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        total_refunded = invoice.payments.filter(
            is_refund=True
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        
        invoice.amount_paid = total_paid - total_refunded
        invoice.update_payment_status()


class InvoiceActivity(models.Model):
    """
    Activity log for invoice changes.
    Tracks all significant events for audit trail.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='activities',
        help_text='Invoice this activity relates to'
    )
    
    # Activity type
    activity_type = models.CharField(
        max_length=50,
        choices=[
            ('CREATED', 'Invoice Created'),
            ('UPDATED', 'Invoice Updated'),
            ('SENT', 'Invoice Sent'),
            ('VIEWED', 'Invoice Viewed'),
            ('ITEM_ADDED', 'Item Added'),
            ('ITEM_REMOVED', 'Item Removed'),
            ('ITEM_UPDATED', 'Item Updated'),
            ('PAYMENT_RECEIVED', 'Payment Received'),
            ('PAYMENT_REFUNDED', 'Payment Refunded'),
            ('STATUS_CHANGED', 'Status Changed'),
            ('CANCELLED', 'Invoice Cancelled'),
            ('REMINDER_SENT', 'Reminder Sent'),
            ('NOTE_ADDED', 'Note Added'),
        ],
        help_text='Type of activity'
    )
    
    # Description
    description = models.TextField(
        help_text='Description of the activity'
    )
    
    # Old and new values for changes
    old_value = models.JSONField(
        null=True,
        blank=True,
        help_text='Previous value (for changes)'
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        help_text='New value (for changes)'
    )
    
    # Who performed the action
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_activities',
        help_text='User who performed this action'
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the user'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text='User agent string'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'invoice_activities'
        verbose_name = 'Invoice Activity'
        verbose_name_plural = 'Invoice Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice', '-created_at']),
            models.Index(fields=['activity_type']),
        ]
    
    def __str__(self):
        return f'{self.invoice.invoice_number} - {self.activity_type}'
