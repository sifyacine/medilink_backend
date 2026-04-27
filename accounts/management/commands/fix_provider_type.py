"""
Management command to fix provider type issues.
Usage: python manage.py fix_provider_type <email> <new_type>
Example: python manage.py fix_provider_type "sifyacine2003@gmail.com" NURSE
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from providers.models import Provider, Nurse, Doctor, Clinic
from providers.models.laboratory import Laboratory
from providers.models.vtc import VTC

User = get_user_model()


class Command(BaseCommand):
    help = 'Change a provider type from one to another'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email of the provider user')
        parser.add_argument('new_type', type=str, help='New provider type (DOCTOR, NURSE, CLINIC, LABORATORY, VTC, SELLER)')

    def handle(self, *args, **options):
        email = options['email'].lower()
        new_type = options['new_type'].upper()

        valid_types = ['DOCTOR', 'NURSE', 'CLINIC', 'LABORATORY', 'VTC', 'SELLER']
        if new_type not in valid_types:
            self.stdout.write(self.style.ERROR(f'Invalid provider type. Must be one of: {", ".join(valid_types)}'))
            return

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with email {email} not found'))
            return

        if user.role != 'PROVIDER':
            self.stdout.write(self.style.ERROR(f'User is not a provider (role: {user.role})'))
            return

        try:
            provider = user.provider_profile
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'User has no provider profile: {str(e)}'))
            return

        old_type = provider.provider_type
        self.stdout.write(f'\nChanging provider type:')
        self.stdout.write(f'  User: {user.email}')
        self.stdout.write(f'  Current Type: {old_type}')
        self.stdout.write(f'  New Type: {new_type}')

        if old_type == new_type:
            self.stdout.write(self.style.WARNING('Provider type is already the same!'))
            return

        with transaction.atomic():
            # Delete old subtype profile
            if old_type == 'DOCTOR' and hasattr(provider, 'doctor_profile'):
                provider.doctor_profile.delete()
                self.stdout.write(f'  ✓ Deleted old Doctor profile')
            elif old_type == 'NURSE' and hasattr(provider, 'nurse_profile'):
                provider.nurse_profile.delete()
                self.stdout.write(f'  ✓ Deleted old Nurse profile')
            elif old_type == 'CLINIC' and hasattr(provider, 'clinic_profile'):
                provider.clinic_profile.delete()
                self.stdout.write(f'  ✓ Deleted old Clinic profile')
            elif old_type == 'LABORATORY' and hasattr(provider, 'laboratory_profile'):
                provider.laboratory_profile.delete()
                self.stdout.write(f'  ✓ Deleted old Laboratory profile')
            elif old_type == 'VTC' and hasattr(provider, 'vtc_profile'):
                provider.vtc_profile.delete()
                self.stdout.write(f'  ✓ Deleted old VTC profile')

            # Update provider type
            provider.provider_type = new_type
            provider.save()
            self.stdout.write(f'  ✓ Updated provider type')

            # Create new subtype profile
            if new_type == 'DOCTOR':
                Doctor.objects.create(
                    provider=provider,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone_number=user.phone_number or ''
                )
                self.stdout.write(f'  ✓ Created Doctor profile')
            elif new_type == 'NURSE':
                Nurse.objects.create(
                    provider=provider,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone_number=user.phone_number or ''
                )
                self.stdout.write(f'  ✓ Created Nurse profile')
            elif new_type == 'CLINIC':
                Clinic.objects.create(
                    provider=provider,
                    clinic_name=user.first_name or 'Clinic'
                )
                self.stdout.write(f'  ✓ Created Clinic profile')
            elif new_type == 'LABORATORY':
                Laboratory.objects.create(
                    provider=provider,
                    lab_name=user.first_name or 'Laboratory'
                )
                self.stdout.write(f'  ✓ Created Laboratory profile')
            elif new_type == 'VTC':
                VTC.objects.create(
                    provider=provider,
                    company_name=user.first_name or 'VTC Company'
                )
                self.stdout.write(f'  ✓ Created VTC profile')

        self.stdout.write(self.style.SUCCESS(f'\n✓ Provider type changed successfully from {old_type} to {new_type}\n'))
