"""
Management command: create_admin_user

Creates a brand-new Medilink admin user (role=ADMIN) together with an
AdminProfile in a single step.  Useful for bootstrapping the platform
or adding additional admins without going through the Django admin UI.

Usage examples
--------------
# Create a SUPER_ADMIN (full access):
    python manage.py create_admin_user \\
        --email superadmin@medilink.dz \\
        --password S3cur3P@ss! \\
        --sub-role SUPER_ADMIN \\
        --first-name Admin \\
        --last-name Medilink

# Create a MODERATOR (approve providers, suspend users):
    python manage.py create_admin_user \\
        --email moderator@medilink.dz \\
        --password S3cur3P@ss! \\
        --sub-role MODERATOR

# Create a SUPPORT agent (read-only + password reset):
    python manage.py create_admin_user \\
        --email support@medilink.dz \\
        --password S3cur3P@ss! \\
        --sub-role SUPPORT

# Create a CONTENT_EDITOR (manage landing page / FAQs / blog):
    python manage.py create_admin_user \\
        --email content@medilink.dz \\
        --password S3cur3P@ss! \\
        --sub-role CONTENT_EDITOR

Sub-role permissions summary
-----------------------------
  SUPER_ADMIN    — Full platform access; can manage other admins.
  MODERATOR      — Approve/refuse providers, suspend/restore users.
  SUPPORT        — View users & logs; can reset passwords (mostly read-only).
  CONTENT_EDITOR — Manage platform content only (landing page, FAQs, blog, etc.).
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from common.enums import UserRole, AdminSubRole


class Command(BaseCommand):
    help = 'Create a new Medilink admin user with an AdminProfile in one step.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, type=str, help='Admin email address')
        parser.add_argument('--password', required=True, type=str, help='Admin password')
        parser.add_argument(
            '--sub-role',
            required=True,
            type=str,
            choices=[r.value for r in AdminSubRole],
            dest='sub_role',
            help=(
                'Admin sub-role: SUPER_ADMIN | MODERATOR | SUPPORT | CONTENT_EDITOR'
            ),
        )
        parser.add_argument('--first-name', default='', dest='first_name', help='First name')
        parser.add_argument('--last-name', default='', dest='last_name', help='Last name')
        parser.add_argument(
            '--notes',
            default='',
            dest='notes',
            help='Internal notes about this admin (visible only to SUPER_ADMINs)',
        )
        parser.add_argument(
            '--is-superuser',
            action='store_true',
            dest='is_superuser',
            default=False,
            help='Grant Django superuser privileges (required to access /django-admin/ panel)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from accounts.models import User
        from admins.models.admin_profile import AdminProfile

        email = options['email'].lower().strip()
        password = options['password']
        sub_role = options['sub_role']
        first_name = options['first_name']
        last_name = options['last_name']
        notes = options['notes']
        is_superuser = options['is_superuser']

        # Validate: email must not already be taken
        if User.objects.filter(email=email).exists():
            raise CommandError(
                f"A user with email '{email}' already exists. "
                "If you want to promote an existing user, use:\n"
                f"  python manage.py create_admin_profile {email} --sub-role {sub_role}"
            )

        # Create the user
        user = User.objects.create_user(
            email=email,
            password=password,
            role=UserRole.ADMIN,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,           # must be True to access Django admin panel
            is_superuser=is_superuser,
            is_active=True,
            email_verified=True,     # admin accounts are pre-verified
        )

        # Create the AdminProfile
        AdminProfile.objects.create(
            user=user,
            sub_role=sub_role,
            notes=notes,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Admin user created successfully!\n"
                f"  Email     : {email}\n"
                f"  Sub-role  : {sub_role}\n"
                f"  is_staff  : True\n"
                f"  is_superuser: {is_superuser}\n\n"
                f"The user can now log in at the Medilink frontend with these credentials.\n"
                f"Django admin panel access: {'✓ Yes' if is_superuser else '✗ No (add --is-superuser flag)'}\n"
            )
        )
