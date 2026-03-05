from django.core.management.base import BaseCommand
from django.utils import timezone

from prescriptions.models import Prescription


class Command(BaseCommand):
    help = (
        "Auto-expire ISSUED prescriptions whose valid_until date has passed.\n\n"
        "Recommended cron schedule (daily at midnight):\n"
        "  0 0 * * * cd /path/to/project && python manage.py auto_expire_prescriptions\n"
    )

    def handle(self, *args, **options):
        started_at = timezone.now()
        expired_count = Prescription.expire_past_valid_until()
        finished_at = timezone.now()

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {expired_count} prescription(s) "
                f"in {(finished_at - started_at).total_seconds():.2f}s."
            )
        )
