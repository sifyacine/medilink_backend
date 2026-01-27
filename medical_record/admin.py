"""
Admin configuration for Medical Records app.
"""
from django.contrib import admin
from django.utils.html import format_html

from medical_record.models import (
    MedicalRecord,
    Prescription,
    Allergy,
    MedicalRecordAttachment,
    MedicalRecordNote,
    MedicalRecordAccessLog,
)


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    """Admin interface for MedicalRecord model."""
    list_display = [
        'id',
        'title',
        'patient',
        'record_type',
        'record_date',
        'created_by',
        'is_active',
        'requires_followup',
        'created_at',
    ]
    list_filter = [
        'record_type',
        'is_active',
        'requires_followup',
        'is_confidential',
        'record_date',
        'created_at',
    ]
    search_fields = [
        'title',
        'description',
        'symptoms',
        'diagnosis_code',
        'patient__email',
        'created_by__email',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'title', 'record_type', 'record_date')
        }),
        ('Clinical Information', {
            'fields': ('diagnosis_code', 'description', 'symptoms')
        }),
        ('Status', {
            'fields': ('is_active', 'is_confidential', 'requires_followup', 'followup_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by/updated_by on save."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Admin interface for Prescription model."""
    list_display = [
        'id',
        'medical_record',
        'medication_name',
        'dosage',
        'frequency',
        'quantity',
        'refills',
    ]
    list_filter = ['medication_name']
    search_fields = [
        'medication_name',
        'medical_record__title',
        'medical_record__patient__email',
    ]


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    """Admin interface for Allergy model."""
    list_display = [
        'id',
        'medical_record',
        'allergen',
        'severity',
        'first_observed',
    ]
    list_filter = ['severity', 'first_observed']
    search_fields = [
        'allergen',
        'reaction',
        'medical_record__title',
        'medical_record__patient__email',
    ]


@admin.register(MedicalRecordAttachment)
class MedicalRecordAttachmentAdmin(admin.ModelAdmin):
    """Admin interface for MedicalRecordAttachment model."""
    list_display = [
        'id',
        'medical_record',
        'file_name',
        'file_type',
        'file_size',
        'uploaded_by',
        'uploaded_at',
    ]
    list_filter = ['file_type', 'uploaded_at']
    search_fields = [
        'file_name',
        'description',
        'medical_record__title',
    ]
    readonly_fields = ['uploaded_at']


@admin.register(MedicalRecordNote)
class MedicalRecordNoteAdmin(admin.ModelAdmin):
    """Admin interface for MedicalRecordNote model."""
    list_display = [
        'id',
        'medical_record',
        'note_type',
        'content_preview',
        'created_by',
        'is_locked',
        'created_at',
    ]
    list_filter = ['note_type', 'is_locked', 'created_at']
    search_fields = [
        'content',
        'medical_record__title',
        'created_by__email',
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    def content_preview(self, obj):
        """Show truncated content preview."""
        if len(obj.content) > 50:
            return format_html(
                '<span title="{}">{}</span>',
                obj.content,
                obj.content[:50] + '...'
            )
        return obj.content
    content_preview.short_description = 'Content'


@admin.register(MedicalRecordAccessLog)
class MedicalRecordAccessLogAdmin(admin.ModelAdmin):
    """Admin interface for MedicalRecordAccessLog model."""
    list_display = [
        'id',
        'medical_record',
        'accessed_by',
        'access_type',
        'ip_address',
        'accessed_at',
    ]
    list_filter = ['access_type', 'accessed_at']
    search_fields = [
        'medical_record__title',
        'accessed_by__email',
        'ip_address',
    ]
    readonly_fields = ['accessed_at']
    date_hierarchy = 'accessed_at'
    
    def has_add_permission(self, request):
        """Disable manual creation of access logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of access logs."""
        return False
