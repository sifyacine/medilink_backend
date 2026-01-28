"""
Admin configuration for the Notifications app.
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Notification, DeviceToken, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification model."""
    
    list_display = [
        'id',
        'recipient_email',
        'title',
        'notification_type',
        'category',
        'priority_badge',
        'is_read',
        'push_sent',
        'created_at',
    ]
    list_filter = [
        'notification_type',
        'category',
        'priority',
        'is_read',
        'push_sent',
        'created_at',
    ]
    search_fields = [
        'recipient__email',
        'title',
        'message',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'read_at',
        'push_sent_at',
    ]
    raw_id_fields = ['recipient']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'recipient', 'title', 'message', 'image_url')
        }),
        ('Classification', {
            'fields': ('notification_type', 'category', 'priority')
        }),
        ('Related Object', {
            'fields': ('related_content_type', 'related_object_id'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'push_sent', 'push_sent_at')
        }),
        ('Additional', {
            'fields': ('action_url', 'data', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def recipient_email(self, obj):
        return obj.recipient.email
    recipient_email.short_description = 'Recipient'
    recipient_email.admin_order_field = 'recipient__email'
    
    def priority_badge(self, obj):
        colors = {
            'LOW': '#6c757d',
            'NORMAL': '#17a2b8',
            'HIGH': '#ffc107',
            'URGENT': '#dc3545',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.priority
        )
    priority_badge.short_description = 'Priority'
    
    actions = ['mark_as_read', 'mark_as_unread', 'resend_push']
    
    @admin.action(description='Mark selected notifications as read')
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, f'{count} notifications marked as read.')
    
    @admin.action(description='Mark selected notifications as unread')
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).update(is_read=False, read_at=None)
        self.message_user(request, f'{count} notifications marked as unread.')
    
    @admin.action(description='Resend push notification')
    def resend_push(self, request, queryset):
        from .services import NotificationService
        count = 0
        for notification in queryset:
            NotificationService._send_push_for_notification(notification)
            count += 1
        self.message_user(request, f'Push sent for {count} notifications.')


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    """Admin for DeviceToken model."""
    
    list_display = [
        'id',
        'user_email',
        'device_type',
        'device_name',
        'is_active_badge',
        'failure_count',
        'created_at',
        'last_used_at',
    ]
    list_filter = [
        'device_type',
        'is_active',
        'created_at',
    ]
    search_fields = [
        'user__email',
        'device_name',
        'device_id',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_used_at',
    ]
    raw_id_fields = ['user']
    ordering = ['-created_at']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inactive</span>'
        )
    is_active_badge.short_description = 'Status'
    
    actions = ['activate_tokens', 'deactivate_tokens', 'reset_failures']
    
    @admin.action(description='Activate selected tokens')
    def activate_tokens(self, request, queryset):
        count = queryset.update(is_active=True, failure_count=0)
        self.message_user(request, f'{count} tokens activated.')
    
    @admin.action(description='Deactivate selected tokens')
    def deactivate_tokens(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} tokens deactivated.')
    
    @admin.action(description='Reset failure counts')
    def reset_failures(self, request, queryset):
        count = queryset.update(failure_count=0)
        self.message_user(request, f'Failure count reset for {count} tokens.')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin for NotificationPreference model."""
    
    list_display = [
        'user_email',
        'push_enabled',
        'email_enabled',
        'quiet_hours_enabled',
        'updated_at',
    ]
    list_filter = [
        'push_enabled',
        'email_enabled',
        'quiet_hours_enabled',
    ]
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Push Notifications', {
            'fields': (
                'push_enabled',
                'push_appointments',
                'push_messages',
                'push_reminders',
                'push_promotions',
                'push_system',
            )
        }),
        ('Email Notifications', {
            'fields': (
                'email_enabled',
                'email_appointments',
                'email_reminders',
            )
        }),
        ('Quiet Hours', {
            'fields': (
                'quiet_hours_enabled',
                'quiet_hours_start',
                'quiet_hours_end',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
