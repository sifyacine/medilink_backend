"""
Management command to delete notifications older than 30 days.

Usage:
    # Dry run (see what would be deleted):
    python manage.py cleanup_notifications --dry-run

    # Actually delete:
    python manage.py cleanup_notifications

    # Custom age (e.g. 60 days):
    python manage.py cleanup_notifications --days 60

Set up as a daily cron job on the droplet:
    crontab -e
    0 3 * * * cd /home/django/backend/medilink_backend && /home/django/backend/medilink_backend/venv/bin/python manage.py cleanup_notifications >> /var/log/medilink_cleanup.log 2>&1
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Delete notifications older than 30 days (configurable via --days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete notifications older than this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        from notifications.models import Notification

        days = options['days']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(days=days)

        old_notifications = Notification.objects.filter(created_at__lt=cutoff)
        count = old_notifications.count()

        if dry_run:
            self.stdout.write(f"[DRY RUN] Would delete {count} notifications older than {days} days (before {cutoff})")
            return

        if count == 0:
            self.stdout.write("No notifications older than %d days." % days)
            return

        deleted, _ = old_notifications.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} notifications older than {days} days."))
