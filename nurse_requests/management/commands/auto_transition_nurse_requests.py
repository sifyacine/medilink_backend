"""
Management command: auto_transition_nurse_requests

Applies time-based status transitions to open nurse requests.
Run every minute via cron or systemd timer:

    * * * * * /path/to/venv/bin/python /path/to/manage.py auto_transition_nurse_requests \
              --settings=core.settings.production >> /var/log/medilink/auto_transition.log 2>&1

Production systemd timer alternative (medilink-auto-transition.timer):

    [Unit]
    Description=MediLink nurse request auto-transitions

    [Timer]
    OnCalendar=*:*:00
    Persistent=true

    [Install]
    WantedBy=timers.target
"""
import logging

from django.core.management.base import BaseCommand

from nurse_requests.services import NurseRequestService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Auto-transition stale nurse requests (run every minute via cron)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be transitioned without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self._dry_run()
            return

        try:
            counts = NurseRequestService.run_auto_transitions()
        except Exception as exc:
            logger.error('auto_transition_nurse_requests failed: %s', exc)
            self.stderr.write(self.style.ERROR(f'Error: {exc}'))
            return

        total = sum(counts.values())
        if total == 0:
            return  # nothing to report — keep cron output clean

        self.stdout.write(
            self.style.SUCCESS(
                f'[auto_transition] '
                f'searching_cancelled={counts["searching_cancelled"]} '
                f'offers_expired={counts["offers_expired"]} '
                f'decision_cancelled={counts["decision_cancelled"]} '
                f'start_cancelled={counts["start_cancelled"]} '
                f'auto_completed={counts["in_progress_completed"]}'
            )
        )

    def _dry_run(self):
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta
        from nurse_requests.models import NurseServiceRequest, NurseOffer, RequestStatus, OfferStatus

        cfg = settings.MEDILINK.get('NURSE_REQUEST_TIMEOUTS', {})
        now = timezone.now()

        searching = NurseServiceRequest.objects.filter(
            status=RequestStatus.SEARCHING,
            updated_at__lte=now - timedelta(minutes=cfg.get('SEARCHING_TIMEOUT_MINUTES', 30)),
        ).count()

        offers = NurseOffer.objects.filter(
            status__in=[OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED],
            created_at__lte=now - timedelta(minutes=cfg.get('OFFER_EXPIRY_MINUTES', 20)),
        ).count()

        unstarted = NurseServiceRequest.objects.filter(
            status=RequestStatus.ACCEPTED,
            accepted_at__lte=now - timedelta(hours=cfg.get('START_TIMEOUT_HOURS', 2)),
        ).count()

        self.stdout.write(
            f'[DRY RUN] Would cancel {searching} SEARCHING requests, '
            f'expire {offers} offers, '
            f'cancel {unstarted} ACCEPTED requests with no start.'
        )
