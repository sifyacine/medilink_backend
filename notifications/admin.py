from django.contrib import admin
from .models import Notification, DeviceToken


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'category', 'is_read', 'push_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'push_sent', 'priority', 'category', 'created_at')
    search_fields = ('title', 'body', 'recipient__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'push_sent_at', 'read_at')
    ordering = ('-created_at',)


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__email', 'token')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-updated_at',)
