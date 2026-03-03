"""
Invoice serializers for the Medilink platform.

Provides serializers for:
- Invoice CRUD operations
- Invoice items management
- Payment recording
- Activity logging
- Localization support
"""
from decimal import Decimal
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction

from .models import (
    Invoice, InvoiceItem, Payment, InvoiceActivity,
    InvoiceStatus, InvoiceType, PaymentMethod, ItemType
)
from services.models import Service, ProviderCustomService
from common.utils import get_patient_display_name


class InvoiceItemSerializer(serializers.ModelSerializer):
    """
    Serializer for invoice line items.
    """
    # Read-only computed fields
    total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    
    # Source object details (read-only)
    service_details = serializers.SerializerMethodField()
    custom_service_details = serializers.SerializerMethodField()
    
    # Localized description (read-only)
    localized_description = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'item_type', 'order',
            'service', 'custom_service', 'prescription_item',
            'description', 'description_en', 'description_ar', 'description_fr',
            'localized_description',
            'quantity', 'unit', 'unit_price', 'discount_percentage', 'total',
            'notes',
            'service_details', 'custom_service_details',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']
    
    def get_service_details(self, obj):
        """Get details of linked service."""
        if obj.service:
            return {
                'id': str(obj.service.id),
                'title': obj.service.title,
                'price': str(obj.service.price),
                'currency': obj.service.currency,
            }
        return None
    
    def get_custom_service_details(self, obj):
        """Get details of linked custom service."""
        if obj.custom_service:
            return {
                'id': str(obj.custom_service.id),
                'title': obj.custom_service.title,
                'price': str(obj.custom_service.price),
            }
        return None
    
    def get_localized_description(self, obj):
        """Get description in requested language."""
        request = self.context.get('request')
        language = 'en'
        if request:
            language = request.headers.get('Accept-Language', 'en')[:2]
        return obj.get_description(language)


class InvoiceItemCreateSerializer(serializers.Serializer):
    """
    Serializer for creating invoice items.
    Supports different item types.
    """
    item_type = serializers.ChoiceField(
        choices=ItemType.choices,
        default=ItemType.CUSTOM
    )
    
    # For SERVICE type
    service_id = serializers.UUIDField(required=False, allow_null=True)
    
    # For CUSTOM_SERVICE type
    custom_service_id = serializers.UUIDField(required=False, allow_null=True)
    
    # For CUSTOM type or overrides
    description = serializers.CharField(max_length=500, required=False)
    description_en = serializers.CharField(max_length=500, required=False, allow_blank=True)
    description_ar = serializers.CharField(max_length=500, required=False, allow_blank=True)
    description_fr = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    quantity = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1.00')
    )
    unit = serializers.CharField(max_length=50, default='unit')
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False
    )
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    order = serializers.IntegerField(default=0)
    
    def validate(self, data):
        """Validate item data based on type."""
        item_type = data.get('item_type')
        
        if item_type == ItemType.SERVICE:
            if not data.get('service_id'):
                raise serializers.ValidationError({
                    'service_id': 'Required for SERVICE type items.'
                })
            try:
                service = Service.objects.get(id=data['service_id'])
                data['service'] = service
                data.setdefault('description', service.title)
                data.setdefault('description_en', service.title_en or service.title)
                data.setdefault('description_ar', service.title_ar or '')
                data.setdefault('description_fr', service.title_fr or '')
                data.setdefault('unit_price', service.price)
                data.setdefault('unit', 'session')
            except Service.DoesNotExist:
                raise serializers.ValidationError({
                    'service_id': 'Service not found.'
                })
        
        elif item_type == ItemType.CUSTOM_SERVICE:
            if not data.get('custom_service_id'):
                raise serializers.ValidationError({
                    'custom_service_id': 'Required for CUSTOM_SERVICE type items.'
                })
            try:
                custom_service = ProviderCustomService.objects.get(id=data['custom_service_id'])
                data['custom_service'] = custom_service
                data.setdefault('description', custom_service.title)
                data.setdefault('description_en', custom_service.title_en or custom_service.title)
                data.setdefault('description_ar', custom_service.title_ar or '')
                data.setdefault('description_fr', custom_service.title_fr or '')
                data.setdefault('unit_price', custom_service.price)
                data.setdefault('unit', 'session')
            except ProviderCustomService.DoesNotExist:
                raise serializers.ValidationError({
                    'custom_service_id': 'Custom service not found.'
                })
        
        elif item_type == ItemType.CUSTOM:
            if not data.get('description'):
                raise serializers.ValidationError({
                    'description': 'Required for CUSTOM type items.'
                })
            if not data.get('unit_price'):
                raise serializers.ValidationError({
                    'unit_price': 'Required for CUSTOM type items.'
                })
        
        return data
    
    def create(self, validated_data):
        """Create invoice item."""
        invoice = validated_data.pop('invoice')
        validated_data.pop('service_id', None)
        validated_data.pop('custom_service_id', None)
        
        return InvoiceItem.objects.create(
            invoice=invoice,
            **{k: v for k, v in validated_data.items() if k not in ['service', 'custom_service'] or validated_data.get(k)}
        )


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for payments.
    """
    invoice_number = serializers.CharField(
        source='invoice.invoice_number', read_only=True
    )
    currency = serializers.CharField(
        source='invoice.currency', read_only=True
    )
    recorded_by_name = serializers.CharField(
        source='recorded_by.get_full_name', read_only=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'invoice', 'invoice_number',
            'amount', 'currency', 'payment_method', 'payment_date',
            'reference_number', 'insurance_claim_number', 'insurance_provider',
            'is_verified', 'verified_at', 'verified_by',
            'is_refund', 'refund_reason', 'original_payment',
            'notes',
            'recorded_by', 'recorded_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'is_verified', 'verified_at', 'verified_by',
            'recorded_by', 'created_at', 'updated_at',
        ]
    
    def validate_amount(self, value):
        """Validate payment amount."""
        if value <= Decimal('0.00'):
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value
    
    def validate(self, data):
        """Validate payment data."""
        invoice = data.get('invoice')
        is_refund = data.get('is_refund', False)
        
        if not is_refund:
            # Check if payment doesn't exceed amount due
            amount = data.get('amount', Decimal('0.00'))
            if invoice and amount > invoice.amount_due:
                raise serializers.ValidationError({
                    'amount': f'Payment amount exceeds amount due ({invoice.amount_due}).'
                })
        else:
            # Refund validation
            if not data.get('refund_reason'):
                raise serializers.ValidationError({
                    'refund_reason': 'Refund reason is required.'
                })
        
        return data
    
    def create(self, validated_data):
        """Create payment and update invoice."""
        validated_data['recorded_by'] = self.context['request'].user
        return super().create(validated_data)


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying a payment."""
    is_verified = serializers.BooleanField(default=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class InvoiceActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for invoice activity log.
    """
    performed_by_name = serializers.CharField(
        source='performed_by.get_full_name', read_only=True
    )
    
    class Meta:
        model = InvoiceActivity
        fields = [
            'id', 'invoice', 'activity_type', 'description',
            'old_value', 'new_value',
            'performed_by', 'performed_by_name',
            'ip_address', 'created_at',
        ]
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    """
    Full invoice serializer with all details.
    """
    # Read-only computed fields
    amount_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    
    # Patient display name
    patient_display_name = serializers.SerializerMethodField()
    
    # Provider details
    provider_name = serializers.SerializerMethodField()
    provider_type = serializers.CharField(
        source='provider.provider_type', read_only=True
    )
    
    # Nested serializers (read-only by default)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    
    # Localized notes
    localized_notes = serializers.SerializerMethodField()
    
    # Status display
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    invoice_type_display = serializers.CharField(
        source='get_invoice_type_display', read_only=True
    )
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number',
            'provider', 'provider_name', 'provider_type',
            'patient_user', 'patient_record', 'patient_display_name',
            'invoice_type', 'invoice_type_display',
            'status', 'status_display',
            'appointment', 'prescription', 'nurse_request',
            'issue_date', 'due_date', 'sent_at', 'viewed_at', 'paid_at',
            'currency',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_type', 'discount_value', 'discount_amount', 'discount_reason',
            'total', 'amount_paid', 'amount_due',
            'notes', 'notes_en', 'notes_ar', 'notes_fr', 'localized_notes',
            'terms', 'internal_notes',
            'cancelled_at', 'cancelled_by', 'cancellation_reason',
            'created_by', 'created_at', 'updated_at',
            'items', 'payments',
        ]
        read_only_fields = [
            'id', 'invoice_number',
            'subtotal', 'tax_amount', 'discount_amount', 'total',
            'amount_paid', 'amount_due',
            'sent_at', 'viewed_at', 'paid_at',
            'cancelled_at', 'cancelled_by',
            'created_by', 'created_at', 'updated_at',
        ]
    
    def get_patient_display_name(self, obj):
        """Get patient display name."""
        return obj.get_patient_display_name()
    
    def get_provider_name(self, obj):
        """Get provider display name."""
        user = obj.provider.user
        return user.get_full_name() or user.email
    
    def get_localized_notes(self, obj):
        """Get notes in requested language."""
        request = self.context.get('request')
        language = 'en'
        if request:
            language = request.headers.get('Accept-Language', 'en')[:2]
        return obj.get_notes(language)
    
    def validate(self, data):
        """Validate invoice data."""
        patient_user = data.get('patient_user')
        patient_record = data.get('patient_record')
        
        # For updates, check existing values
        if self.instance:
            patient_user = patient_user if 'patient_user' in data else self.instance.patient_user
            patient_record = patient_record if 'patient_record' in data else self.instance.patient_record
        
        if not patient_user and not patient_record:
            raise serializers.ValidationError(
                'Either patient_user or patient_record must be provided.'
            )
        
        if patient_user and patient_record:
            raise serializers.ValidationError(
                'Cannot have both patient_user and patient_record.'
            )
        
        return data
    
    def create(self, validated_data):
        """Create invoice with audit tracking."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating invoices with items.
    """
    items = InvoiceItemCreateSerializer(many=True, required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'provider', 'patient_user', 'patient_record',
            'invoice_type', 'appointment', 'prescription', 'nurse_request',
            'issue_date', 'due_date', 'currency',
            'tax_rate', 'discount_type', 'discount_value', 'discount_reason',
            'notes', 'notes_en', 'notes_ar', 'notes_fr',
            'terms', 'internal_notes',
            'items',
        ]
        extra_kwargs = {
            'provider': {'required': False},
        }
    
    def validate(self, data):
        """Validate invoice creation data."""
        request = self.context['request']

        # Auto-set provider from authenticated user when not explicitly given
        if not data.get('provider'):
            if hasattr(request.user, 'provider_profile'):
                data['provider'] = request.user.provider_profile
            else:
                raise serializers.ValidationError({
                    'provider': 'This field is required for non-provider users.'
                })

        patient_user = data.get('patient_user')
        patient_record = data.get('patient_record')
        
        if not patient_user and not patient_record:
            raise serializers.ValidationError(
                'Either patient_user or patient_record must be provided.'
            )
        
        if patient_user and patient_record:
            raise serializers.ValidationError(
                'Cannot have both patient_user and patient_record.'
            )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Create invoice with items."""
        items_data = validated_data.pop('items', [])
        validated_data['created_by'] = self.context['request'].user
        
        invoice = Invoice.objects.create(**validated_data)
        
        # Create items
        for i, item_data in enumerate(items_data):
            item_data['order'] = item_data.get('order', i)
            
            # Resolve service/custom_service from IDs
            if item_data.get('service_id'):
                item_data['service'] = Service.objects.get(id=item_data.pop('service_id'))
            if item_data.get('custom_service_id'):
                item_data['custom_service'] = ProviderCustomService.objects.get(
                    id=item_data.pop('custom_service_id')
                )
            
            InvoiceItem.objects.create(invoice=invoice, **item_data)
        
        # Calculate totals
        invoice.calculate_totals()
        invoice.save()
        
        # Log creation
        InvoiceActivity.objects.create(
            invoice=invoice,
            activity_type='CREATED',
            description=f'Invoice {invoice.invoice_number} created',
            performed_by=self.context['request'].user,
        )
        
        return invoice


class InvoiceListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for invoice listings.
    """
    patient_display_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    amount_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number',
            'provider_name', 'patient_display_name',
            'invoice_type', 'status', 'status_display',
            'issue_date', 'due_date',
            'currency', 'total', 'amount_paid', 'amount_due',
            'items_count',
            'created_at',
        ]
    
    def get_patient_display_name(self, obj):
        return obj.get_patient_display_name()
    
    def get_provider_name(self, obj):
        user = obj.provider.user
        return user.get_full_name() or user.email
    
    def get_items_count(self, obj):
        return obj.items.count()


class InvoiceSendSerializer(serializers.Serializer):
    """Serializer for sending an invoice."""
    send_notification = serializers.BooleanField(default=True)
    message = serializers.CharField(required=False, allow_blank=True)


class InvoiceCancelSerializer(serializers.Serializer):
    """Serializer for cancelling an invoice."""
    reason = serializers.CharField(required=True)


class InvoiceFromAppointmentSerializer(serializers.Serializer):
    """
    Serializer for creating an invoice from an appointment.
    """
    appointment_id = serializers.UUIDField()
    include_services = serializers.BooleanField(default=True)
    tax_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00')
    )
    due_days = serializers.IntegerField(default=30, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_appointment_id(self, value):
        """Validate appointment exists and is completed."""
        from appointments.models import Appointment, AppointmentStatus
        
        try:
            appointment = Appointment.objects.get(id=value)
        except Appointment.DoesNotExist:
            raise serializers.ValidationError('Appointment not found.')
        
        if appointment.status != AppointmentStatus.COMPLETED:
            raise serializers.ValidationError(
                'Can only create invoice for completed appointments.'
            )
        
        return value


class InvoiceStatisticsSerializer(serializers.Serializer):
    """
    Serializer for invoice statistics.
    """
    total_invoices = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # By status
    draft_count = serializers.IntegerField()
    sent_count = serializers.IntegerField()
    paid_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    cancelled_count = serializers.IntegerField()
    
    # By type
    service_invoices = serializers.IntegerField()
    product_invoices = serializers.IntegerField()
    mixed_invoices = serializers.IntegerField()
    custom_invoices = serializers.IntegerField()
