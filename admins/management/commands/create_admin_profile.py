"""
Management command: create_admin_profile

Usage:
    python manage.py create_admin_profile <email> --sub-role SUPER_ADMIN
    python manage.py create_admin_profile <email> --sub-role MODERATOR
    python manage.py create_admin_profile <email> --sub-role SUPPORT
    python manage.py create_admin_profile <email> --sub-role CONTENT_EDITOR
    python manage.py create_admin_profile <email> --sub-role SUPER_ADMIN --notes "Initial super admin"

The target user must already exist and have role=ADMIN.
If the user's role is not ADMIN, the command will upgrade it automatically
unless --no-upgrade is passed.
"""
from django.core.management.base import BaseCommand, CommandError

from common.enums import UserRole, AdminSubRole
from admins.models.admin_profile import AdminProfile


class Command(BaseCommand):
    help = 'Create or update an AdminProfile for an existing admin user.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the existing user')
        parser.add_argument(
            '--sub-role',
            type=str,
            choices=[r.value for r in AdminSubRole],
            default=AdminSubRole.SUPPORT,
            dest='sub_role',
            help='Admin sub-role to assign (default: SUPPORT)',
        )
        parser.add_argument(
            '--notes',
            type=str,
            default='',
            dest='notes',
            help='Optional internal notes for this admin profile',
        )
        parser.add_argument(
            '--no-upgrade',
            action='store_true',
            dest='no_upgrade',
            help="Don't automatically upgrade user role to ADMIN if it isn't already",
        )

    def handle(self, *args, **options):
        from accounts.models import User  # lazy import to avoid circular refs

        email = options['email']
        sub_role = options['sub_role']
        notes = options['notes']
        no_upgrade = options['no_upgrade']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"No user found with email: {email}")

        # Ensure the user has the ADMIN role
        if user.role != UserRole.ADMIN:
            if no_upgrade:
                raise CommandError(
                    f"User {email} has role '{user.role}', not ADMIN. "
                    "Pass without --no-upgrade to auto-upgrade."
                )
            self.stdout.write(
                self.style.WARNING(
                    f"User {email} has role '{user.role}'. Upgrading to ADMIN..."
                )
            )
            user.role = UserRole.ADMIN
            user.save(update_fields=['role'])

        # Create or update the AdminProfile
        profile, created = AdminProfile.objects.update_or_create(
            user=user,
            defaults={'sub_role': sub_role, 'notes': notes},
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} AdminProfile for {email} — sub_role={sub_role}"
            )
        )
