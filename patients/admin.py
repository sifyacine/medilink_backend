"""
Admin configuration for Patient Records app.
"""
from django.contrib import admin

from patients.models import PatientRecord, ProviderPatientAccess


@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):
    """Admin configuration for PatientRecord model."""
    
    list_display = [
        'id',
        'first_name',
        'last_name',
        'date_of_birth',
        'gender',
        'phone_number',
        'is_linked',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'gender',
        'blood_type',
        'is_active',
        'token_used',
        'country',
        'created_at',
    ]
    search_fields = [
        'first_name',
        'last_name',
        'phone_number',
        'email',
        'national_id',
    ]
    readonly_fields = [
        'linking_token',
        'token_used',
        'token_used_at',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'date_of_birth',
                'gender',
            )
        }),
        ('Contact Information', {
            'fields': (
                'phone_number',
                'email',
                'emergency_contact_name',
                'emergency_contact_phone',
            )
        }),
        ('Medical Information', {
            'fields': (
                'blood_type',
                'known_allergies',
                'chronic_conditions',
                'current_medications',
            )
        }),
        ('Address', {
            'fields': (
                'address',
                'city',
                'state',
                'country',
            )
        }),
        ('Identification', {
            'fields': (
                'national_id',
            )
        }),
        ('Account Linking', {
            'fields': (
                'linked_user',
                'linking_token',
                'token_used',
                'token_used_at',
            )
        }),
        ('Metadata', {
            'fields': (
                'notes',
                'is_active',
                'created_by_provider',
                'created_at',
                'updated_at',
            )
        }),
    )


@admin.register(ProviderPatientAccess)
class ProviderPatientAccessAdmin(admin.ModelAdmin):
    """Admin configuration for ProviderPatientAccess model."""
    
    list_display = [
        'id',
        'provider',
        'patient_record',
        'access_level',
        'granted_by',
        'created_at',
    ]
    list_filter = [
        'access_level',
        'created_at',
    ]
    search_fields = [
        'provider__user__email',
        'patient_record__first_name',
        'patient_record__last_name',
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
