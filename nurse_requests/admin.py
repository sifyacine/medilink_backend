from django.contrib import admin
from .models import (
    NurseServiceRequest,
    NurseOffer,
    RequestHistory
)

# NursingService admin removed - now managed through services app admin
# Services with service_type='NURSE' and is_on_demand=True are nursing services


class NurseOfferInline(admin.TabularInline):
    model = NurseOffer
    extra = 0
    readonly_fields = ['created_at', 'responded_at']
    fields = ['nurse', 'offered_price', 'status', 'distance_km', 'estimated_arrival_time']


class RequestHistoryInline(admin.TabularInline):
    model = RequestHistory
    extra = 0
    readonly_fields = ['timestamp', 'actor', 'action', 'old_status', 'new_status', 'details']
    can_delete = False


@admin.register(NurseServiceRequest)
class NurseServiceRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_patient_display', 'service', 'status', 'patient_offered_price',
        'final_price', 'city', 'created_at'
    ]
    list_filter = ['status', 'city', 'created_at']
    search_fields = ['patient_user__email', 'patient_user__first_name', 'patient_user__last_name', 'city']
    readonly_fields = [
        'created_at', 'updated_at', 'accepted_at', 'started_at',
        'completed_at', 'cancelled_at'
    ]
    inlines = [NurseOfferInline, RequestHistoryInline]
    fieldsets = (
        ('Request Information', {
            'fields': ('patient_user', 'patient_record', 'service', 'status', 'accepted_nurse')
        }),
        ('Pricing', {
            'fields': ('base_price', 'patient_offered_price', 'final_price')
        }),
        ('Location', {
            'fields': ('latitude', 'longitude', 'city', 'address_line')
        }),
        ('Notes & Cancellation', {
            'fields': ('notes', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'updated_at', 'accepted_at', 'started_at',
                'completed_at', 'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Patient')
    def get_patient_display(self, obj):
        return obj.get_patient_display_name()


@admin.register(NurseOffer)
class NurseOfferAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'request', 'nurse', 'offered_price', 'status',
        'distance_km', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'nurse__user__email',
        'nurse__user__first_name',
        'nurse__user__last_name',
        'request__id'
    ]
    readonly_fields = ['created_at', 'updated_at', 'responded_at']


@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'action', 'actor', 'old_status', 'new_status', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['request__id', 'action']
    readonly_fields = ['timestamp']
