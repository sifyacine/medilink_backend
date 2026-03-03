from django.core.management.base import BaseCommand
from django.utils import timezone

from appointments.services import AppointmentService


class Command(BaseCommand):
    help = (
        "Auto-cancel appointments whose scheduled time has passed "
        "(PENDING/CONFIRMED/RESCHEDULED)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--grace-minutes",
            type=int,
            default=15,
            help="Minutes to wait after scheduled start before auto-cancelling",
        )

    def handle(self, *args, **options):
        grace = options["grace_minutes"]
        started_at = timezone.now()
        cancelled_count = AppointmentService.auto_cancel_past_appointments(
            grace_minutes=grace
        )
        finished_at = timezone.now()

        self.stdout.write(
            self.style.SUCCESS(
                f"Auto-cancelled {cancelled_count} appointment(s) "
                f"(grace={grace}m) in {(finished_at - started_at).total_seconds():.2f}s."
            )
        )
