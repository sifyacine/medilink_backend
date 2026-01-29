"""
Admin configuration for prescriptions app.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Prescription, PrescriptionItem, PrescriptionStatus


class PrescriptionItemInline(admin.TabularInline):
    """Inline for prescription items."""
    model = PrescriptionItem
    extra = 0
    fields = [
        'medication_name', 'medication_type', 'strength',
        'dosage', 'frequency', 'duration_days', 'instructions', 'order'
    ]
    ordering = ['order']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Admin for prescriptions."""
    
    list_display = [
        'reference_number', 'get_patient_name', 'doctor',
        'clinic', 'status_badge', 'items_count', 'issued_at', 'created_at'
    ]
    list_filter = ['status', 'clinic', 'created_at', 'issued_at']
    search_fields = [
        'reference_number', 'patient__email', 'patient__first_name',
        'patient__last_name', 'patient_record__first_name',
        'patient_record__last_name', 'doctor__user__email'
    ]
    readonly_fields = ['id', 'reference_number', 'created_at', 'updated_at', 'issued_at']
    date_hierarchy = 'created_at'
    inlines = [PrescriptionItemInline]
    
    fieldsets = (
        ('Reference', {
            'fields': ('id', 'reference_number')
        }),
        ('Participants', {
            'fields': ('doctor', 'patient', 'patient_record', 'clinic', 'appointment')
        }),
        ('Medical Content', {
            'fields': ('diagnosis', 'notes', 'instructions')
        }),
        ('Status & Validity', {
            'fields': ('status', 'valid_until', 'pdf_file')
        }),
        ('Timestamps', {
            'fields': ('issued_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_patient_name(self, obj):
        return obj.get_patient_display_name()
    get_patient_name.short_description = 'Patient'
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'
    
    def status_badge(self, obj):
        colors = {
            PrescriptionStatus.DRAFT: '#6c757d',
            PrescriptionStatus.ISSUED: '#28a745',
            PrescriptionStatus.DISPENSED: '#17a2b8',
            PrescriptionStatus.EXPIRED: '#ffc107',
            PrescriptionStatus.CANCELLED: '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    """Admin for prescription items."""
    
    list_display = [
        'medication_name', 'prescription', 'medication_type',
        'dosage', 'frequency', 'duration_days'
    ]
    list_filter = ['medication_type', 'frequency']
    search_fields = ['medication_name', 'generic_name', 'prescription__reference_number']
    ordering = ['prescription', 'order']
