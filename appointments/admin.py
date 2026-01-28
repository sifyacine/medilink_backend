"""
Admin configuration for the appointments app.

Provides comprehensive admin interface for:
- Appointments with status actions
- Provider availability management
- Provider time off management
- Appointment reminders
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Appointment,
    AppointmentReminder,
    ProviderAvailability,
    ProviderTimeOff,
    AppointmentStatus,
)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_patient_name',
        'provider',
        'scheduled_date',
        'scheduled_time',
        'status_badge',
        'location_type',
        'created_by_role',
        'created_at',
    ]
    list_filter = [
        'status',
        'location_type',
        'created_by_role',
        'scheduled_date',
        'created_at',
    ]
    search_fields = [
        'patient_user__email',
        'patient_user__first_name',
        'patient_user__last_name',
        'patient_record__first_name',
        'patient_record__last_name',
        'provider__user__email',
        'reason',
        'notes',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'confirmed_at',
        'completed_at',
        'cancelled_at',
        'created_by_role',
    ]
    ordering = ['-scheduled_date', '-scheduled_time']
    date_hierarchy = 'scheduled_date'
    actions = ['confirm_appointments', 'cancel_appointments', 'mark_completed']
    
    fieldsets = (
        ('Appointment Info', {
            'fields': ('id', 'provider', 'service')
        }),
        ('Patient', {
            'fields': ('patient_user', 'patient_record')
        }),
        ('Scheduling', {
            'fields': (
                'scheduled_date', 'scheduled_time', 'duration_minutes'
            )
        }),
        ('Location', {
            'fields': (
                'location_type', 'clinic_address', 'home_address', 'meeting_link'
            )
        }),
        ('Details', {
            'fields': ('status', 'reason', 'notes', 'provider_notes')
        }),
        ('Cancellation', {
            'fields': (
                'cancellation_reason', 'cancellation_notes',
                'cancelled_by', 'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_by', 'created_by_role', 'created_at', 'updated_at',
                'confirmed_at', 'completed_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_patient_name(self, obj):
        return obj.get_patient_display_name()
    get_patient_name.short_description = 'Patient'
    
    def status_badge(self, obj):
        colors = {
            AppointmentStatus.PENDING: '#FFA500',
            AppointmentStatus.CONFIRMED: '#28a745',
            AppointmentStatus.CANCELLED: '#dc3545',
            AppointmentStatus.COMPLETED: '#007bff',
            AppointmentStatus.NO_SHOW: '#6c757d',
            AppointmentStatus.RESCHEDULED: '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    @admin.action(description='Confirm selected appointments')
    def confirm_appointments(self, request, queryset):
        count = 0
        for appointment in queryset.filter(status=AppointmentStatus.PENDING):
            try:
                appointment.confirm()
                count += 1
            except Exception:
                pass
        self.message_user(request, f'{count} appointment(s) confirmed.')
    
    @admin.action(description='Cancel selected appointments')
    def cancel_appointments(self, request, queryset):
        count = 0
        for appointment in queryset.exclude(
            status__in=[AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]
        ):
            try:
                appointment.cancel(
                    cancelled_by=request.user,
                    reason='OTHER',
                    notes='Cancelled by admin'
                )
                count += 1
            except Exception:
                pass
        self.message_user(request, f'{count} appointment(s) cancelled.')
    
    @admin.action(description='Mark selected as completed')
    def mark_completed(self, request, queryset):
        count = 0
        for appointment in queryset.filter(status=AppointmentStatus.CONFIRMED):
            try:
                appointment.complete()
                count += 1
            except Exception:
                pass
        self.message_user(request, f'{count} appointment(s) marked as completed.')


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'appointment',
        'remind_at',
        'sent',
        'sent_at',
    ]
    list_filter = [
        'sent',
        'remind_at',
    ]
    search_fields = [
        'appointment__patient_user__email',
        'appointment__provider__user__email',
    ]
    readonly_fields = ['sent_at']


@admin.register(ProviderAvailability)
class ProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'provider',
        'day_of_week',
        'start_time',
        'end_time',
        'location_type',
        'max_appointments',
        'is_active',
    ]
    list_filter = [
        'day_of_week',
        'location_type',
        'is_active',
        'provider',
    ]
    search_fields = [
        'provider__user__email',
        'provider__user__first_name',
        'provider__user__last_name',
    ]
    ordering = ['provider', 'day_of_week', 'start_time']


@admin.register(ProviderTimeOff)
class ProviderTimeOffAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'provider',
        'start_datetime',
        'end_datetime',
        'reason',
        'is_recurring_annual',
    ]
    list_filter = [
        'is_recurring_annual',
        'start_datetime',
        'provider',
    ]
    search_fields = [
        'provider__user__email',
        'provider__user__first_name',
        'provider__user__last_name',
        'reason',
    ]
    ordering = ['provider', 'start_datetime']
    date_hierarchy = 'start_datetime'
