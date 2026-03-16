"""
Django admin configuration for accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import User
from admins.models.admin_profile import AdminProfile


class AdminProfileInline(admin.StackedInline):
    """
    Inline editor for AdminProfile shown on the User change/add page.
    Allows setting sub_role (SUPER_ADMIN / MODERATOR / SUPPORT / CONTENT_EDITOR)
    and internal notes directly from the User admin page.
    """
    model = AdminProfile
    verbose_name = 'Admin Profile (sub-role & permissions)'
    verbose_name_plural = 'Admin Profile'
    fields = ('sub_role', 'notes')
    extra = 0
    min_num = 0
    max_num = 1
    can_delete = False

    def get_extra(self, request, obj=None, **kwargs):
        # Show the inline creation form only when editing an ADMIN user that has no profile yet
        from common.enums import UserRole
        if obj and obj.role == UserRole.ADMIN:
            if not AdminProfile.objects.filter(user=obj).exists():
                return 1  # show empty form to create one
        return 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    list_display = ['email', 'role', 'admin_sub_role', 'is_active', 'is_staff', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    inlines = [AdminProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Role & Status', {
            'fields': ('role', 'account_status'),
            'description': (
                'To create a Medilink admin: set Role = ADMIN, then use the '
                '"Admin Profile" section below to assign a sub-role '
                '(SUPER_ADMIN / MODERATOR / SUPPORT / CONTENT_EDITOR). '
                'CLI shortcut: python manage.py create_admin_user --email EMAIL --sub-role SUPER_ADMIN'
            ),
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
        ('Quick Admin Setup', {
            'classes': ('wide', 'collapse'),
            'description': (
                'After saving with role=ADMIN, set the Admin sub-role in the '
                '"Admin Profile" inline below. Or run: '
                'python manage.py create_admin_user --email EMAIL --sub-role SUPER_ADMIN'
            ),
            'fields': ('is_staff',),
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def admin_sub_role(self, obj):
        """Show the admin sub-role in the list display."""
        try:
            return obj.admin_profile.get_sub_role_display()
        except Exception:
            return '-'
    admin_sub_role.short_description = 'Admin Sub-Role'
    admin_sub_role.admin_order_field = 'admin_profile__sub_role'
