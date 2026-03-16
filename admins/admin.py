from django.contrib import admin

from admins.models.admin_profile import AdminProfile
from admins.models.activity_log import AdminActivityLog


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'sub_role', 'created_at']
    list_filter = ['sub_role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdminActivityLog)
class AdminActivityLogAdmin(admin.ModelAdmin):
    list_display = ['admin', 'action', 'object_repr', 'ip_address', 'created_at']
    list_filter = ['action']
    search_fields = ['admin__email', 'object_repr']
    readonly_fields = ['admin', 'action', 'content_type', 'object_id', 'object_repr',
                       'ip_address', 'extra_data', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
