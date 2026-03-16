from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from admins.models.admin_profile import AdminProfile
from admins.models.activity_log import AdminActivityLog


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for AdminProfile.

    From here you can:
      - View all admin users and their sub-roles.
      - Change a user's sub-role and internal notes.
      - Use the "Create Admin User" action from the Users section.

    To create a brand-new admin user use the management command::

        python manage.py create_admin_user \\
            --email admin@medilink.dz \\
            --password S3cur3P@ss! \\
            --sub-role SUPER_ADMIN \\
            --is-superuser
    """

    list_display = ['user_email', 'user_full_name', 'sub_role', 'is_staff_badge', 'created_at']
    list_filter = ['sub_role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at', 'management_command_hint']
    ordering = ['sub_role', 'user__email']

    fieldsets = (
        ('Admin User', {
            'fields': ('user', 'sub_role', 'notes'),
        }),
        ('Sub-role Permissions Guide', {
            'classes': ('collapse',),
            'fields': (),
            'description': (
                '<b>SUPER_ADMIN</b> — Full platform access; can manage other admins.<br>'
                '<b>MODERATOR</b> — Approve/refuse providers, suspend/restore users.<br>'
                '<b>SUPPORT</b> — View users &amp; logs; can reset passwords (mostly read-only).<br>'
                '<b>CONTENT_EDITOR</b> — Manage platform content only (landing page, FAQs, blog).'
            ),
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
        ('Create New Admin User (CLI)', {
            'classes': ('collapse',),
            'fields': ('management_command_hint',),
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def user_full_name(self, obj):
        name = obj.user.get_full_name()
        return name if name.strip() else '—'
    user_full_name.short_description = 'Full Name'

    def is_staff_badge(self, obj):
        if obj.user.is_superuser:
            return format_html('<span style="color:green;font-weight:bold;">✓ Superuser</span>')
        if obj.user.is_staff:
            return format_html('<span style="color:#0066cc;">✓ Staff</span>')
        return format_html('<span style="color:#999;">—</span>')
    is_staff_badge.short_description = 'Django Access'

    def management_command_hint(self, obj=None):
        return format_html(
            '<pre style="background:#f5f5f5;padding:10px;border-radius:4px;">'
            '# Create a new admin user from the command line:\n'
            'python manage.py create_admin_user \\\n'
            '    --email admin@medilink.dz \\\n'
            '    --password S3cur3P@ss! \\\n'
            '    --sub-role SUPER_ADMIN \\\n'
            '    --first-name John --last-name Doe \\\n'
            '    --is-superuser\n\n'
            '# Promote an existing user to admin:\n'
            'python manage.py create_admin_profile user@medilink.dz \\\n'
            '    --sub-role SUPER_ADMIN'
            '</pre>'
        )
    management_command_hint.short_description = 'Management Command'

    def save_model(self, request, obj, form, change):
        """Ensure the linked user has role=ADMIN when saving."""
        from common.enums import UserRole
        if obj.user.role != UserRole.ADMIN:
            obj.user.role = UserRole.ADMIN
            obj.user.is_staff = True
            obj.user.save(update_fields=['role', 'is_staff'])
            messages.warning(
                request,
                f"User '{obj.user.email}' role was automatically upgraded to ADMIN "
                "and is_staff was set to True."
            )
        super().save_model(request, obj, form, change)


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
