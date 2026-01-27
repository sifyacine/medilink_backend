from django.contrib import admin
from medical_records.models import (
    MedicalRecord,
    Prescription,
    Allergy,
    MedicalRecordAttachment,
    MedicalRecordNote,
    ProviderAccess,
)


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient', 'provider', 'record_type', 'record_date', 'is_active', 'created_at']
    list_filter = ['record_type', 'is_active', 'is_confidential', 'record_date']
    search_fields = ['title', 'diagnosis', 'patient__email']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['medication_name', 'medical_record', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['medication_name', 'medical_record__title']


@admin.register(Allergy)
class AllergyAdmin(admin.ModelAdmin):
    list_display = ['patient', 'allergen', 'severity', 'is_active', 'diagnosed_date']
    list_filter = ['severity', 'is_active', 'diagnosed_date']
    search_fields = ['patient__email', 'allergen']


@admin.register(MedicalRecordAttachment)
class MedicalRecordAttachmentAdmin(admin.ModelAdmin):
    list_display = ['medical_record', 'file_type', 'description', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['medical_record__title', 'description']


@admin.register(MedicalRecordNote)
class MedicalRecordNoteAdmin(admin.ModelAdmin):
    list_display = ['medical_record', 'author', 'note_type', 'is_visible_to_patient', 'created_at']
    list_filter = ['note_type', 'is_visible_to_patient', 'created_at']
    search_fields = ['medical_record__title', 'content']


@admin.register(ProviderAccess)
class ProviderAccessAdmin(admin.ModelAdmin):
    list_display = ['patient', 'provider', 'access_type', 'is_active', 'granted_at', 'expires_at']
    list_filter = ['access_type', 'is_active', 'granted_at']
    search_fields = ['patient__email', 'provider__user__email']
