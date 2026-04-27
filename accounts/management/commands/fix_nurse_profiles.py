"""
Management command to diagnose and fix nurse provider profile issues.
Usage: python manage.py fix_nurse_profiles [--fix]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from providers.models import Provider, Nurse

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnose and optionally fix nurse provider profile issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix issues found',
        )

    def handle(self, *args, **options):
        fix_issues = options.get('fix', False)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('NURSE PROVIDER DIAGNOSTIC & FIX'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # Get all provider users
        provider_users = User.objects.filter(role='PROVIDER').order_by('id')
        self.stdout.write(f'Total PROVIDER users: {provider_users.count()}\n')

        issues_found = []
        fixed = []

        for user in provider_users:
            self.stdout.write(f"\n{'─'*80}")
            self.stdout.write(self.style.HTTP_INFO(f'User: {user.email} (ID: {user.id})'))
            self.stdout.write(f'Role: {user.role}')
            self.stdout.write(f'Is Active: {user.is_active}')
            
            # Check if provider_profile exists
            if not hasattr(user, 'provider_profile'):
                self.stdout.write(self.style.ERROR('❌ ISSUE: No provider_profile relationship!'))
                issues_found.append({
                    'user': user.email,
                    'issue': 'Missing provider_profile',
                    'user_id': user.id
                })
                continue
            
            provider = user.provider_profile
            self.stdout.write(f'Provider Type: {provider.provider_type}')
            self.stdout.write(f'Provider Status: {provider.status}')
            
            # Check if nurse_profile exists for NURSE providers
            if provider.provider_type == 'NURSE':
                if not hasattr(provider, 'nurse_profile'):
                    self.stdout.write(self.style.ERROR('❌ ISSUE: NURSE provider has no nurse_profile!'))
                    issues_found.append({
                        'user': user.email,
                        'issue': 'Missing nurse_profile',
                        'user_id': user.id,
                        'provider_id': provider.id
                    })
                    
                    # Attempt to fix if --fix flag is set
                    if fix_issues:
                        try:
                            with transaction.atomic():
                                nurse = Nurse.objects.create(
                                    provider=provider,
                                    first_name=user.first_name,
                                    last_name=user.last_name,
                                    phone_number=user.phone_number or ''
                                )
                                self.stdout.write(self.style.SUCCESS(
                                    f'✓ FIXED: Created nurse_profile (ID: {nurse.id})'
                                ))
                                fixed.append({
                                    'user': user.email,
                                    'action': 'Created nurse_profile'
                                })
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'✗ FAILED TO FIX: {str(e)}'))
                else:
                    nurse = provider.nurse_profile
                    self.stdout.write(self.style.SUCCESS('✓ Nurse Profile exists'))
                    self.stdout.write(f'  - First Name: {nurse.first_name}')
                    self.stdout.write(f'  - Last Name: {nurse.last_name}')
                    self.stdout.write(f'  - License Number: {nurse.license_number}')
                    self.stdout.write(f'  - Phone: {nurse.phone_number}')

        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.HTTP_INFO(f'Issues found: {len(issues_found)}'))
        self.stdout.write(self.style.SUCCESS(f'Issues fixed: {len(fixed)}'))
        self.stdout.write('='*80 + '\n')

        if issues_found:
            self.stdout.write(self.style.WARNING('\nRemaining issues that need attention:'))
            for issue in issues_found:
                self.stdout.write(f"\n  User: {issue['user']}")
                self.stdout.write(f"  Issue: {issue['issue']}")
                if 'provider_id' in issue:
                    self.stdout.write(f"  Provider ID: {issue['provider_id']}")

        if fixed:
            self.stdout.write(self.style.SUCCESS('\nIssues automatically fixed:'))
            for item in fixed:
                self.stdout.write(f"\n  User: {item['user']}")
                self.stdout.write(f"  Action: {item['action']}")

        if not issues_found:
            self.stdout.write(self.style.SUCCESS('\n✓ All nurse providers are configured correctly!\n'))
        elif fix_issues and len(fixed) == len(issues_found):
            self.stdout.write(self.style.SUCCESS('\n✓ All issues have been automatically fixed!\n'))
        else:
            self.stdout.write(self.style.WARNING(
                '\nTo automatically fix these issues, run:\n'
                '  python manage.py fix_nurse_profiles --fix\n'
            ))
