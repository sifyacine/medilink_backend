"""
Dashboard statistics service for provider dashboards.

Computes real-time stats for:
- Appointments (counts by status, today's list)
- Invoices (revenue, outstanding, overdue)
- Patients (total count, gender breakdown)
- Reviews (average rating, total, recent)
- Activity feed (combined recent events)
"""
import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum, Q, Case, When, Value, IntegerField
from django.utils import timezone

logger = logging.getLogger(__name__)


class DashboardStatsService:
    """Compute dashboard statistics for a given provider."""

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------

    @staticmethod
    def get_appointment_stats(provider):
        from appointments.models import Appointment, AppointmentStatus

        qs = Appointment.objects.filter(provider=provider)
        today = timezone.now().date()

        status_counts = qs.values("status").annotate(count=Count("id"))
        status_map = {item["status"]: item["count"] for item in status_counts}

        return {
            "total": sum(status_map.values()),
            "pending": status_map.get(AppointmentStatus.PENDING, 0),
            "confirmed": status_map.get(AppointmentStatus.CONFIRMED, 0),
            "completed": status_map.get(AppointmentStatus.COMPLETED, 0),
            "cancelled": status_map.get(AppointmentStatus.CANCELLED, 0),
            "no_show": status_map.get(AppointmentStatus.NO_SHOW, 0),
            "rescheduled": status_map.get(AppointmentStatus.RESCHEDULED, 0),
            "rejected": status_map.get(AppointmentStatus.REJECTED, 0),
            "today_count": qs.filter(scheduled_date=today).count(),
            "upcoming_count": qs.filter(
                scheduled_date__gte=today,
                status__in=[
                    AppointmentStatus.PENDING,
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.RESCHEDULED,
                ],
            ).count(),
        }

    @staticmethod
    def get_today_appointments(provider):
        from appointments.models import Appointment
        from appointments.serializers import AppointmentListSerializer
        from common.utils import (
            get_appointment_select_related,
            get_appointment_prefetch_related,
        )

        today = timezone.now().date()
        qs = (
            Appointment.objects.filter(provider=provider, scheduled_date=today)
            .select_related(*get_appointment_select_related())
            .prefetch_related(*get_appointment_prefetch_related())
            .order_by("scheduled_time")
        )
        return AppointmentListSerializer(qs, many=True).data

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------

    @staticmethod
    def get_invoice_summary(provider):
        from invoices.models import Invoice, InvoiceStatus

        qs = Invoice.objects.filter(provider=provider)

        totals = qs.aggregate(
            total_amount=Sum("total"),
            total_paid=Sum("amount_paid"),
        )
        total_amount = totals["total_amount"] or Decimal("0.00")
        total_paid = totals["total_paid"] or Decimal("0.00")

        status_counts = qs.values("status").annotate(count=Count("id"))
        sm = {item["status"]: item["count"] for item in status_counts}

        return {
            "total_invoices": sum(sm.values()),
            "total_revenue": str(total_paid),
            "total_outstanding": str(total_amount - total_paid),
            "draft_count": sm.get(InvoiceStatus.DRAFT, 0),
            "sent_count": (
                sm.get(InvoiceStatus.SENT, 0)
                + sm.get(InvoiceStatus.VIEWED, 0)
            ),
            "paid_count": sm.get(InvoiceStatus.PAID, 0),
            "overdue_count": sm.get(InvoiceStatus.OVERDUE, 0),
            "partially_paid_count": sm.get(InvoiceStatus.PARTIALLY_PAID, 0),
            "cancelled_count": sm.get(InvoiceStatus.CANCELLED, 0),
        }

    # ------------------------------------------------------------------
    # Patients
    # ------------------------------------------------------------------

    @staticmethod
    def get_patient_stats(provider):
        from patients.models import ProviderPatientAccess, PatientRecord

        access_qs = ProviderPatientAccess.objects.filter(provider=provider)
        patient_ids = access_qs.values_list("patient_record_id", flat=True)

        records = PatientRecord.objects.filter(
            id__in=patient_ids, is_deleted=False
        )

        gender_counts = records.aggregate(
            male=Count(Case(When(gender="MALE", then=1), output_field=IntegerField())),
            female=Count(Case(When(gender="FEMALE", then=1), output_field=IntegerField())),
            other=Count(Case(When(gender="OTHER", then=1), output_field=IntegerField())),
            prefer_not_to_say=Count(
                Case(When(gender="PREFER_NOT_TO_SAY", then=1), output_field=IntegerField())
            ),
        )

        total = records.count()

        return {
            "total_patients": total,
            "gender_breakdown": {
                "male": gender_counts["male"],
                "female": gender_counts["female"],
                "other": gender_counts["other"],
                "prefer_not_to_say": gender_counts["prefer_not_to_say"],
            },
        }

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    @staticmethod
    def get_review_stats(provider):
        from django.contrib.contenttypes.models import ContentType
        from reviews.models import ReviewAggregate, Review, ReviewStatus

        ct = ContentType.objects.get_for_model(provider)
        object_id = str(provider.pk)

        # Use pre-computed aggregate if available
        try:
            agg = ReviewAggregate.objects.get(content_type=ct, object_id=object_id)
            avg_rating = float(agg.average_rating)
            total_reviews = agg.review_count
            distribution = {
                "1": agg.rating_1_count,
                "2": agg.rating_2_count,
                "3": agg.rating_3_count,
                "4": agg.rating_4_count,
                "5": agg.rating_5_count,
            }
        except ReviewAggregate.DoesNotExist:
            avg_rating = 0.0
            total_reviews = 0
            distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

        # Recent reviews (last 5)
        recent = (
            Review.objects.filter(
                reviewed_content_type=ct,
                reviewed_object_id=object_id,
                status=ReviewStatus.ACTIVE,
            )
            .select_related("reviewer")
            .order_by("-created_at")[:5]
        )
        recent_data = [
            {
                "id": str(r.pk),
                "reviewer_name": r.reviewer.get_full_name() or r.reviewer.email,
                "rating": r.rating,
                "title": r.title,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent
        ]

        return {
            "average_rating": round(avg_rating, 2),
            "total_reviews": total_reviews,
            "rating_distribution": distribution,
            "recent_reviews": recent_data,
        }

    # ------------------------------------------------------------------
    # Activity feed
    # ------------------------------------------------------------------

    @staticmethod
    def get_recent_activity(provider, limit=20):
        """Build a combined activity feed from appointments, invoices, and reviews."""
        items = []

        # Recent appointments (created or status-changed)
        from appointments.models import Appointment

        appts = (
            Appointment.objects.filter(provider=provider)
            .select_related("patient_user", "patient_record")
            .order_by("-updated_at")[:limit]
        )
        for a in appts:
            patient_name = _patient_display(a.patient_user, a.patient_record)
            items.append({
                "type": "appointment",
                "id": str(a.pk),
                "description": f"{a.get_status_display()} appointment with {patient_name}",
                "status": a.status,
                "timestamp": a.updated_at.isoformat() if a.updated_at else a.created_at.isoformat(),
            })

        # Recent invoices
        from invoices.models import Invoice

        invoices = (
            Invoice.objects.filter(provider=provider)
            .select_related("patient_user", "patient_record")
            .order_by("-updated_at")[:limit]
        )
        for inv in invoices:
            patient_name = _patient_display(inv.patient_user, inv.patient_record)
            items.append({
                "type": "invoice",
                "id": str(inv.pk),
                "description": f"Invoice {inv.invoice_number} — {inv.get_status_display()} ({patient_name})",
                "status": inv.status,
                "amount": str(inv.total),
                "timestamp": inv.updated_at.isoformat() if inv.updated_at else inv.created_at.isoformat(),
            })

        # Recent reviews
        from django.contrib.contenttypes.models import ContentType
        from reviews.models import Review, ReviewStatus

        ct = ContentType.objects.get_for_model(provider)
        reviews = (
            Review.objects.filter(
                reviewed_content_type=ct,
                reviewed_object_id=str(provider.pk),
                status=ReviewStatus.ACTIVE,
            )
            .select_related("reviewer")
            .order_by("-created_at")[:limit]
        )
        for r in reviews:
            reviewer_name = r.reviewer.get_full_name() or r.reviewer.email
            items.append({
                "type": "review",
                "id": str(r.pk),
                "description": f"{reviewer_name} left a {r.rating}★ review",
                "rating": r.rating,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
            })

        # Sort combined list by timestamp descending, take top `limit`
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return items[:limit]

    # ------------------------------------------------------------------
    # Full dashboard snapshot
    # ------------------------------------------------------------------

    @staticmethod
    def get_full_dashboard(provider):
        return {
            "appointments": DashboardStatsService.get_appointment_stats(provider),
            "today_appointments": DashboardStatsService.get_today_appointments(provider),
            "invoices": DashboardStatsService.get_invoice_summary(provider),
            "patients": DashboardStatsService.get_patient_stats(provider),
            "reviews": DashboardStatsService.get_review_stats(provider),
            "recent_activity": DashboardStatsService.get_recent_activity(provider),
        }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _patient_display(patient_user, patient_record):
    """Return a display name for the patient."""
    if patient_user:
        name = patient_user.get_full_name()
        if name and name.strip():
            return name.strip()
        return patient_user.email
    if patient_record:
        return patient_record.full_name or str(patient_record.patient_unique_id)
    return "Unknown patient"
