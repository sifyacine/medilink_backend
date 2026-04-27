"""
Management command to check user and provider accounts.
Usage: python manage.py check_accounts
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from providers.models import Provider, Nurse

User = get_user_model()


class Command(BaseCommand):
    help = 'Check user and provider accounts'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*80)
        self.stdout.write('USER & PROVIDER ACCOUNT CHECK')
        self.stdout.write('='*80 + '\n')

        # All users
        all_users = User.objects.all().order_by('id')
        self.stdout.write(f'Total Users: {all_users.count()}\n')
        
        self.stdout.write('All Users:')
        for user in all_users:
            status = '✓ ACTIVE' if user.is_active else '✗ INACTIVE'
            self.stdout.write(f'  ID: {user.id}, Email: {user.email}, Role: {user.role} [{status}]')

        # All providers
        all_providers = Provider.objects.all().order_by('id')
        self.stdout.write(f'\nTotal Providers: {all_providers.count()}\n')
        
        self.stdout.write('All Providers:')
        for provider in all_providers:
            user = provider.user
            self.stdout.write(f'  ID: {provider.id}, User: {user.email}, Type: {provider.provider_type}, Status: {provider.status}')
            
            # Check for subtype profiles
            if provider.provider_type == 'NURSE':
                if hasattr(provider, 'nurse_profile'):
                    self.stdout.write(f'    ✓ Nurse Profile exists')
                else:
                    self.stdout.write(f'    ✗ Nurse Profile MISSING')
            elif provider.provider_type == 'DOCTOR':
                if hasattr(provider, 'doctor_profile'):
                    self.stdout.write(f'    ✓ Doctor Profile exists')
                else:
                    self.stdout.write(f'    ✗ Doctor Profile MISSING')

        # Check for orphaned nurses
        orphan_nurses = Nurse.objects.filter(provider__isnull=True)
        if orphan_nurses.exists():
            self.stdout.write(f'\n⚠ Found {orphan_nurses.count()} orphaned Nurse profiles')
