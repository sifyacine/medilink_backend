"""
Invoice admin configuration for the Medilink platform.

Provides Django admin interface for:
- Invoice management
- Invoice item management
- Payment management
- Activity log viewing
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from .models import Invoice, InvoiceItem, Payment, InvoiceActivity, InvoiceStatus


class InvoiceItemInline(admin.TabularInline):
    """Inline admin for invoice items."""
    model = InvoiceItem
    extra = 0
    readonly_fields = ['total', 'created_at']
    fields = [
        'order', 'item_type', 'description',
        'quantity', 'unit', 'unit_price', 'discount_percentage', 'total',
    ]


class PaymentInline(admin.TabularInline):
    """Inline admin for payments."""
    model = Payment
    extra = 0
    readonly_fields = ['created_at', 'recorded_by']
    fields = [
        'amount', 'payment_method', 'payment_date',
        'reference_number', 'is_verified', 'is_refund',
        'recorded_by',
    ]


class InvoiceActivityInline(admin.TabularInline):
    """Inline admin for invoice activities."""
    model = InvoiceActivity
    extra = 0
    readonly_fields = ['activity_type', 'description', 'performed_by', 'created_at']
    fields = ['activity_type', 'description', 'performed_by', 'created_at']
    can_delete = False
    max_num = 0  # Don't allow adding new activities via admin
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin for Invoice model."""
    list_display = [
        'invoice_number', 'provider_name', 'patient_name',
        'status_badge', 'invoice_type', 'total_display',
        'amount_due_display', 'issue_date', 'due_date',
    ]
    list_filter = ['status', 'invoice_type', 'currency', 'issue_date', 'due_date']
    search_fields = [
        'invoice_number',
        'provider__user__email', 'provider__user__first_name', 'provider__user__last_name',
        'patient_user__email', 'patient_user__first_name', 'patient_user__last_name',
        'patient_record__first_name', 'patient_record__last_name',
    ]
    readonly_fields = [
        'invoice_number', 'subtotal', 'tax_amount', 'discount_amount',
        'total', 'amount_paid', 'amount_due',
        'created_at', 'updated_at', 'created_by',
        'sent_at', 'viewed_at', 'paid_at',
        'cancelled_at', 'cancelled_by',
    ]
    
    fieldsets = [
        ('Invoice Info', {
            'fields': ['invoice_number', 'invoice_type', 'status']
        }),
        ('Parties', {
            'fields': ['provider', 'patient_user', 'patient_record']
        }),
        ('Related Objects', {
            'fields': ['appointment', 'prescription', 'nurse_request'],
            'classes': ['collapse'],
        }),
        ('Dates', {
            'fields': ['issue_date', 'due_date', 'sent_at', 'viewed_at', 'paid_at']
        }),
        ('Amounts', {
            'fields': [
                'currency',
                ('subtotal', 'tax_rate', 'tax_amount'),
                ('discount_type', 'discount_value', 'discount_amount', 'discount_reason'),
                ('total', 'amount_paid'),
            ]
        }),
        ('Notes', {
            'fields': ['notes', 'notes_en', 'notes_ar', 'notes_fr', 'terms', 'internal_notes'],
            'classes': ['collapse'],
        }),
        ('Cancellation', {
            'fields': ['cancelled_at', 'cancelled_by', 'cancellation_reason'],
            'classes': ['collapse'],
        }),
        ('Audit', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
    
    inlines = [InvoiceItemInline, PaymentInline, InvoiceActivityInline]
    
    def provider_name(self, obj):
        user = obj.provider.user
        return user.get_full_name() or user.email
    provider_name.short_description = 'Provider'
    
    def patient_name(self, obj):
        return obj.get_patient_display_name()
    patient_name.short_description = 'Patient'
    
    def status_badge(self, obj):
        colors = {
            InvoiceStatus.DRAFT: '#6c757d',
            InvoiceStatus.SENT: '#17a2b8',
            InvoiceStatus.VIEWED: '#6610f2',
            InvoiceStatus.PARTIALLY_PAID: '#fd7e14',
            InvoiceStatus.PAID: '#28a745',
            InvoiceStatus.OVERDUE: '#dc3545',
            InvoiceStatus.CANCELLED: '#343a40',
            InvoiceStatus.REFUNDED: '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_display(self, obj):
        return f'{obj.total} {obj.currency}'
    total_display.short_description = 'Total'
    
    def amount_due_display(self, obj):
        if obj.amount_due > 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{} {}</span>',
                obj.amount_due, obj.currency
            )
        return format_html(
            '<span style="color: #28a745;">Paid</span>'
        )
    amount_due_display.short_description = 'Amount Due'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_sent', 'mark_as_paid', 'recalculate_totals']
    
    @admin.action(description='Mark selected invoices as sent')
    def mark_as_sent(self, request, queryset):
        count = 0
        for invoice in queryset.filter(status=InvoiceStatus.DRAFT):
            invoice.mark_as_sent()
            count += 1
        self.message_user(request, f'{count} invoice(s) marked as sent.')
    
    @admin.action(description='Mark selected invoices as paid')
    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        count = 0
        for invoice in queryset.exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.CANCELLED]):
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = timezone.now()
            invoice.amount_paid = invoice.total
            invoice.save()
            count += 1
        self.message_user(request, f'{count} invoice(s) marked as paid.')
    
    @admin.action(description='Recalculate invoice totals')
    def recalculate_totals(self, request, queryset):
        for invoice in queryset:
            invoice.calculate_totals()
            invoice.save()
        self.message_user(request, f'{queryset.count()} invoice(s) recalculated.')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Admin for InvoiceItem model."""
    list_display = [
        'invoice_link', 'description', 'item_type',
        'quantity', 'unit_price', 'discount_percentage', 'total',
    ]
    list_filter = ['item_type', 'invoice__status']
    search_fields = ['description', 'invoice__invoice_number']
    readonly_fields = ['total', 'created_at', 'updated_at']
    
    def invoice_link(self, obj):
        url = reverse('admin:invoices_invoice_change', args=[obj.invoice.id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
    invoice_link.short_description = 'Invoice'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for Payment model."""
    list_display = [
        'invoice_link', 'amount', 'payment_method',
        'payment_date', 'is_verified', 'is_refund',
    ]
    list_filter = ['payment_method', 'is_verified', 'is_refund', 'payment_date']
    search_fields = ['invoice__invoice_number', 'reference_number']
    readonly_fields = ['created_at', 'updated_at', 'recorded_by']
    
    def invoice_link(self, obj):
        url = reverse('admin:invoices_invoice_change', args=[obj.invoice.id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
    invoice_link.short_description = 'Invoice'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InvoiceActivity)
class InvoiceActivityAdmin(admin.ModelAdmin):
    """Admin for InvoiceActivity model (read-only)."""
    list_display = [
        'invoice_link', 'activity_type', 'description',
        'performed_by', 'created_at',
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = ['invoice__invoice_number', 'description']
    readonly_fields = [
        'invoice', 'activity_type', 'description',
        'old_value', 'new_value',
        'performed_by', 'ip_address', 'user_agent', 'created_at',
    ]
    
    def invoice_link(self, obj):
        url = reverse('admin:invoices_invoice_change', args=[obj.invoice.id])
        return format_html('<a href="{}">{}</a>', url, obj.invoice.invoice_number)
    invoice_link.short_description = 'Invoice'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
