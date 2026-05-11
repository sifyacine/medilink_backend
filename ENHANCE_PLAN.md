# Medilink Backend — Enhancement & Scalability Plan

> Audit date: 2026-05-11  
> Branch: main  
> Overall quality: solid foundations, targeted critical issues before scaling.

---

## Table of Contents

1. [What Is Already Done Well](#1-what-is-already-done-well)
2. [Critical — Fix Before Scale](#2-critical--fix-before-scale)
3. [High Priority — Next Sprint](#3-high-priority--next-sprint)
4. [Medium Priority — Refactoring Round](#4-medium-priority--refactoring-round)
5. [Low Priority — Tech Debt](#5-low-priority--tech-debt)
6. [What to Remove](#6-what-to-remove)
7. [What to Reduce](#7-what-to-reduce)
8. [What to Increase](#8-what-to-increase)
9. [Scalability Roadmap](#9-scalability-roadmap)

---

## 1. What Is Already Done Well

Keep these patterns exactly as they are.

### Custom Exception Hierarchy (`common/exceptions.py`)
Domain-specific exceptions (`AppointmentException`, `ProviderException`) with consistent error codes, and a unified exception handler. Every app follows this — do not break this pattern.

### Centralized Enums (`common/enums.py`)
All roles, statuses, and types in one file. This is the right approach and saves you from scattered hardcoded strings.

### Authentication Guards (`common/authentication.py`)
`TokenAuthenticationWithAccountStatus` and `ProviderTokenAuthentication` block suspended/deactivated users at the authentication layer before any view logic runs. This is the correct place to enforce account state.

### Services Layer Pattern
Each app has a `services.py` containing the business logic. Views are thin. This is the right architecture — the issue is that it is not applied *consistently* (serializers and signals are doing work that belongs in services).

### Transaction Awareness in Signals
Using `transaction.on_commit()` before dispatching notifications is correct — it ensures side effects fire only after the database write commits.

### Profile Completion Heuristic (`accounts/models/user.py`)
`recalculate_profile_completion()` is role-aware and computed correctly from model fields. Keep it; it is not bloat.

### Query Optimization Helpers (`common/utils.py`)
`get_appointment_select_related()` and similar helpers centralize prefetch logic. The problem is they are not consistently *used*. Do not remove them — expand usage.

### Settings Split (`core/settings/`)
`base.py` → `development.py` / `production.py` is the right structure. Keep it.

---

## 2. Critical — Fix Before Scale

### 2.1 N+1 Queries in Appointment Serializers

**File:** `appointments/serializers.py` — `_get_custom_service_price()`

**Problem:** This function is called once per `AppointmentService` instance during serialization. On a list of 50 appointments with 3 services each, this is 150 separate `DoctorService`/`NurseService` queries.

**Fix:** Prefetch the custom service lookups in the viewset queryset, then pass them into the serializer context instead of querying per item.

```python
# appointments/views.py — in get_queryset()
from django.db.models import Prefetch
from services.models import DoctorService, NurseService

queryset = Appointment.objects.select_related(
    'provider__user',
    'provider__doctor_profile',
    'provider__nurse_profile',
    'patient_user',
    'patient_record',
).prefetch_related(
    Prefetch(
        'provider__doctor_profile__doctorservice_set',
        queryset=DoctorService.objects.select_related('service'),
        to_attr='prefetched_doctor_services',
    ),
    Prefetch(
        'provider__nurse_profile__nurseservice_set',
        queryset=NurseService.objects.select_related('service'),
        to_attr='prefetched_nurse_services',
    ),
    'appointment_services__service',
)
```

```python
# appointments/serializers.py — remove the per-item DB query
def _get_custom_service_price(provider, service, context):
    doctor_services = getattr(
        getattr(provider, 'doctor_profile', None),
        'prefetched_doctor_services', []
    )
    for ds in doctor_services:
        if ds.service_id == service.pk:
            return ds.custom_price
    # same for nurse_services
    return service.price
```

**Rule going forward:** Serializers must not issue DB queries. All data they need must be prefetched in the viewset before serialization begins.

---

### 2.2 Thread-Unsafe State Tracking in Signals

**File:** `appointments/signals.py` lines 11–26

**Problem:** Module-level dicts (`_previous_status`, `_deleted_appointment_data`) keyed by instance PK are shared across all requests in the same process. Under concurrent load two requests can overwrite each other's entries.

```python
# CURRENT — NOT thread-safe
_previous_status = {}  # shared dict across all threads

@receiver(pre_save, sender=Appointment)
def capture_previous_status(sender, instance, **kwargs):
    _previous_status[instance.pk] = ...  # race condition here
```

**Fix option A (preferred) — store state on the instance:**
```python
@receiver(pre_save, sender=Appointment)
def capture_previous_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._previous_status = Appointment.objects.only('status').get(pk=instance.pk).status
        except Appointment.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None
```

**Fix option B — remove signal and call explicitly from the service:**
```python
# appointments/services.py
def update_appointment_status(appointment, new_status, actor):
    old_status = appointment.status
    appointment.status = new_status
    appointment.save(update_fields=['status', 'updated_at'])
    _dispatch_status_change_notifications(appointment, old_status, new_status)
```

Option B is cleaner — business logic is explicit and testable. Signals become notification-only side effects, not business logic orchestrators.

---

### 2.3 Missing Patient Exclusivity Constraint

**Affects:** `appointments`, `invoices`, `nurse_requests`, `prescriptions`, `medical_record`

**Problem:** Every one of these models stores both `patient_user` (FK to User) and `patient_record` (FK to PatientRecord) as nullable fields with no enforcement that exactly one must be set. Both can be NULL, or both can be filled.

**Fix — add a `CheckConstraint` in each model's `Meta`:**
```python
# appointments/models.py
from django.db import models

class Appointment(models.Model):
    ...
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(patient_user__isnull=False, patient_record__isnull=True) |
                    models.Q(patient_user__isnull=True, patient_record__isnull=False)
                ),
                name='appointment_patient_xor',
            )
        ]
    
    def clean(self):
        super().clean()
        if bool(self.patient_user_id) == bool(self.patient_record_id):
            raise ValidationError('Set exactly one of patient_user or patient_record.')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

Apply the same pattern to `Invoice`, `NurseRequest`, `Prescription`, `MedicalRecord`. Generate and run migrations after each.

---

### 2.4 Select-For-Update on Booking Conflict Checks

**File:** `appointments/services.py` — conflict checking

**Problem:** Without a database-level lock, two concurrent requests can both pass the conflict check and create overlapping appointments.

**Fix:**
```python
# appointments/services.py
from django.db import transaction

def create_appointment(provider, patient, scheduled_datetime, services, **kwargs):
    with transaction.atomic():
        # Lock all of this provider's appointments for the day
        Appointment.objects.filter(
            provider=provider,
            scheduled_date=scheduled_datetime.date(),
        ).select_for_update(nowait=True)
        
        _check_scheduling_conflict(provider, scheduled_datetime)
        appointment = Appointment.objects.create(...)
        return appointment
```

`select_for_update(nowait=True)` raises `OperationalError` immediately if another transaction holds the lock — return a 409 to the client instead of silently double-booking.

---

## 3. High Priority — Next Sprint

### 3.1 Move Pricing Logic Out of Serializers → Services

**File:** `appointments/serializers.py`, `nurse_requests/serializers.py`, `invoices/serializers.py`

Business logic (price calculation, tax, discount) belongs in `services.py` or model methods. Serializers should only transform already-computed data into the output shape.

**Target structure:**
```
services/pricing.py
├── get_service_price(provider, service) → Decimal
├── calculate_appointment_total(appointment) → Decimal
└── calculate_invoice_total(invoice) → dict  # subtotal, tax, discount, total
```

Call these from the service layer before creating/updating. The serializer then just reads `obj.calculated_total`.

---

### 3.2 Eliminate String-Based Role and Status Comparisons

**Search pattern:** `grep -r "== 'PROVIDER'\|== 'PATIENT'\|== 'ADMIN'\|== 'PENDING'\|== 'APPROVED'" --include="*.py"`

Every occurrence should become an enum comparison:

```python
# BAD
if user.role == 'PROVIDER':

# GOOD
from common.enums import UserRole
if user.role == UserRole.PROVIDER:
```

Run the grep, fix every hit. This is a typo-resistant, IDE-navigable pattern — it already exists in enums.py, just not consistently used in views.

---

### 3.3 Add Missing Database Indexes

Apply to all models that appear in filtered list endpoints. These are the most impactful missing ones:

```python
# appointments/models.py
class Meta:
    indexes = [
        models.Index(fields=['provider', 'status', '-scheduled_date']),
        models.Index(fields=['patient_user', '-scheduled_date']),
        models.Index(fields=['patient_record', '-scheduled_date']),
        models.Index(fields=['status', '-created_at']),
    ]

# nurse_requests/models.py
class Meta:
    indexes = [
        models.Index(fields=['patient_user', '-created_at']),
        models.Index(fields=['status', 'city']),
        models.Index(fields=['provider', '-created_at']),
    ]

# invoices/models.py
class Meta:
    indexes = [
        models.Index(fields=['provider', 'status']),
        models.Index(fields=['patient_user', '-created_at']),
    ]
```

---

### 3.4 Fix Nullable Unique Fields

**File:** `providers/models/doctor.py` — `license_number`

In PostgreSQL, `unique=True` on a nullable field allows multiple rows with `NULL`. This means many doctors can have no license number without any uniqueness enforcement.

```python
# providers/models/doctor.py
class Meta:
    constraints = [
        models.UniqueConstraint(
            fields=['license_number'],
            condition=models.Q(license_number__isnull=False),
            name='doctor_license_number_unique_notnull',
        )
    ]
# Remove unique=True from the field itself
license_number = models.CharField(max_length=100, blank=True, null=True)
```

Audit all other `unique=True, null=True` fields across the codebase and apply the same fix.

---

### 3.5 Enforce Pagination Explicitly on All ViewSets

**Problem:** Global `PAGE_SIZE=20` helps, but if a viewset overrides `list()` or uses a non-standard method, pagination may be skipped silently.

**Fix:** Add to `common/views.py` (create if it doesn't exist) a base viewset class:
```python
# common/views.py
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class BaseModelViewSet(viewsets.ModelViewSet):
    pagination_class = StandardPagination
```

All app viewsets inherit from `BaseModelViewSet` instead of `viewsets.ModelViewSet`. Pagination is then impossible to accidentally omit.

---

### 3.6 Consolidate Permission Logic into Permission Classes

**Problem:** Some views repeat `if hasattr(user, 'provider_profile'):` inline instead of relying on the permission classes in `common/permissions.py`. This means the same check exists in two places.

**Rule:** Views should only declare `permission_classes`. They must not have inline authorization checks. If you need a new check, add a new permission class in `common/permissions.py` and declare it on the viewset.

---

## 4. Medium Priority — Refactoring Round

### 4.1 Split Large Serializer Files

Files over ~300 lines that mix multiple concerns:

| File | Action |
|------|--------|
| `appointments/serializers.py` (~950 lines) | Split into `serializers/create.py`, `serializers/list.py`, `serializers/detail.py` |
| `nurse_requests/serializers.py` (~500+ lines) | Split into `serializers/request.py`, `serializers/offer.py` |
| `accounts/serializers/` | Already split — good, keep pattern |

**Pattern to follow:**
```
appointments/
  serializers/
    __init__.py   ← re-exports everything
    create.py     ← write serializers (validation-heavy)
    list.py       ← lightweight list/summary serializers
    detail.py     ← full detail serializers
```

---

### 4.2 Centralize Feature Flags in Settings

**Current:** Feature flags are scattered scalar booleans in `base.py`.

**Target:**
```python
# core/settings/base.py
MEDILINK = {
    'FEATURES': {
        'AUTO_INVOICE_APPOINTMENTS': False,
        'AUTO_INVOICE_NURSE_REQUESTS': False,
        'AUTO_SEND_INVOICE': False,
    },
    'BOOKING': {
        'MIN_NOTICE_HOURS': 24,
        'MAX_ADVANCE_DAYS': 90,
        'DEFAULT_DURATION_MINUTES': 30,
    },
    'LIMITS': {
        'MAX_ACTIVE_NURSE_REQUESTS': 5,
        'MAX_APPOINTMENT_SERVICES': 10,
    },
    'SECURITY': {
        'PASSWORD_RESET_EXPIRY_HOURS': 24,
        'MAX_FAILED_LOGIN_ATTEMPTS': 5,
        'ACCOUNT_LOCK_DURATION_MINUTES': 30,
    },
}
```

Access via `from django.conf import settings; settings.MEDILINK['BOOKING']['MIN_NOTICE_HOURS']`.

---

### 4.3 Add Lat/Lon Validators

**File:** `nurse_requests/models.py`

```python
# common/validators.py
from django.core.exceptions import ValidationError

def validate_latitude(value):
    if not -90 <= float(value) <= 90:
        raise ValidationError('Latitude must be between -90 and 90.')

def validate_longitude(value):
    if not -180 <= float(value) <= 180:
        raise ValidationError('Longitude must be between -180 and 180.')
```

Apply to every model field that stores geographic coordinates.

---

### 4.4 Standardize Serializer Field Declarations

**Problem:** Some serializers declare a field as `required=False` in the field definition but then raise a `ValidationError` in `validate()` if it's missing. This is contradictory — DRF documentation and API consumers expect `required=False` to mean optional.

**Rule:**
- If a field is required → `required=True` (or omit, as True is default)
- If a field is conditional (required for nurses but not doctors) → declare `required=False` and validate conditionally in `validate()` with a clear error message explaining the condition

---

### 4.5 Replace Manual `hasattr` Provider Checks with Properties

**Problem:** Code repeatedly does `hasattr(provider, 'doctor_profile')` or tries/catches `Provider.doctor_profile.RelatedObjectDoesNotExist`.

**Fix:** Add typed properties on the `Provider` model:

```python
# providers/models/provider.py
class Provider(models.Model):
    ...
    @property
    def is_doctor(self):
        return self.provider_type == ProviderType.DOCTOR
    
    @property
    def typed_profile(self):
        """Returns the type-specific profile or None."""
        profile_map = {
            ProviderType.DOCTOR: 'doctor_profile',
            ProviderType.NURSE: 'nurse_profile',
            ProviderType.CLINIC: 'clinic_profile',
        }
        attr = profile_map.get(self.provider_type)
        if attr:
            return getattr(self, attr, None)
        return None
```

---

## 5. Low Priority — Tech Debt

### 5.1 Remove Legacy / Deprecated Fields

**File:** `providers/models/provider.py`

Fields marked with comments like `# Legacy` or `# Deprecated` should be removed in a dedicated migration. Keeping dead database columns wastes storage and confuses readers.

Steps:
1. Search `grep -r "Legacy\|Deprecated\|TODO.*remove" --include="*.py"` across all models
2. Verify no code references the field
3. Create and run migration to drop the column

---

### 5.2 Audit for Unused Imports and Dead Code

```bash
# Quick dead import audit
pip install autoflake
autoflake --check --remove-unused-variables --remove-all-unused-imports -r .
```

Do not auto-apply — review output first. Common culprits: old serializer classes imported in `__init__.py` but never used, utility functions written but never called.

---

### 5.3 Standardize `update_fields` Usage

Every `model.save()` that only updates specific fields should use `update_fields` to avoid writing the full row:

```python
# BAD
appointment.status = AppointmentStatus.CONFIRMED
appointment.save()

# GOOD
appointment.status = AppointmentStatus.CONFIRMED
appointment.save(update_fields=['status', 'updated_at'])
```

This reduces lock contention on high-write tables like `appointments` and `nurse_requests`.

---

### 5.4 Add `__str__` Methods to All Models

Every model should have a meaningful `__str__`. Missing ones make Django admin and shell sessions confusing. Audit with:
```bash
grep -rL "__str__" --include="models.py" .
```

---

## 6. What to Remove

| Item | Location | Reason |
|------|----------|--------|
| Module-level `_previous_status` dict | `appointments/signals.py:11-26` | Thread-unsafe, replace with instance attribute |
| Module-level `_deleted_appointment_data` dict | `appointments/signals.py` | Same reason |
| Duplicate feature flag scalars | `core/settings/base.py` | Merge into `MEDILINK` dict |
| Fields with `# Legacy` / `# Deprecated` comments | `providers/models/` | Dead database columns |
| Redundant `CustomRegisterSerializer` if unused | `accounts/serializers/auth.py` | Verify and remove if dj-rest-auth does not reference it |
| Inline permission checks inside views | Various `views.py` files | Move to permission classes, remove from views |

---

## 7. What to Reduce

| Item | Current State | Target |
|------|--------------|--------|
| `appointments/serializers.py` | ~950 lines, 1 file | 3 focused files under 300 lines each |
| `nurse_requests/serializers.py` | 500+ lines | 2 files |
| Business logic per serializer | Pricing, validation, status decisions | Move to `services/pricing.py` |
| Signal responsibilities | Signals trigger business logic | Signals trigger only notification dispatch |
| Defensive `hasattr` / try-except chains | Scattered throughout views | Replace with typed model properties |
| Database queries per serialization | N queries on list endpoints | 0 (all data prefetched before serialization) |

---

## 8. What to Increase

| Item | Current State | Target |
|------|--------------|--------|
| Database indexes | Minimal on some models | Cover all heavily filtered fields |
| `select_related` / `prefetch_related` usage | Inconsistent | Applied on every list queryset |
| `update_fields` usage on `.save()` | Rarely used | All partial saves use it |
| `select_for_update()` on conflict-sensitive writes | None | Appointment creation, offer acceptance |
| Unit test coverage in `services.py` | Unknown | Every service function has at minimum a happy path + one failure test |
| Explicit `pagination_class` declarations | Relies on global default | Explicit on every ViewSet |
| Input validation for geographic fields | None | Validators on all lat/lon fields |
| `CheckConstraint` on patient exclusivity | Not enforced at DB level | All five affected models |

---

## 9. Scalability Roadmap

### Phase 1 — Correctness (Do Now)
Fix the critical issues in section 2. None of these require infrastructure changes:
- N+1 queries → prefetch in viewsets
- Signal state → instance attribute
- Patient XOR constraint → migration
- Booking lock → `select_for_update`

### Phase 2 — Performance (When Load Increases)
Once Postgres is showing slow queries, add:
- All missing indexes from section 3.3
- Query result caching for read-heavy endpoints (provider profile, services catalog) via Django's cache framework (already connected via Redis in production)
- Read-only database replica for list endpoints (Django's `DATABASE_ROUTERS`)

### Phase 3 — Background Tasks (When Notification Volume Grows)
The current synchronous signal-based notification dispatch works at low volume. When FCM calls or WebSocket pushes start adding latency to request/response cycles:
- Add **Celery** with Redis broker (Redis is already deployed in production)
- Move notification dispatch to async Celery tasks
- Move invoice auto-generation to scheduled Celery beat task
- This is a clean migration: signals call `task.delay()` instead of the service function directly

```python
# notifications/tasks.py (new file when Celery is added)
from celery import shared_task

@shared_task
def send_appointment_notification(appointment_id, notification_type):
    appointment = Appointment.objects.select_related(...).get(pk=appointment_id)
    NotificationService.dispatch(appointment, notification_type)
```

### Phase 4 — Multi-Tenancy / Sharding (Later)
The current schema is flat (all providers in one table). If the platform grows to thousands of providers across multiple cities/regions:
- Partition the `appointments` table by `scheduled_date` (Postgres table partitioning)
- Consider per-region read replicas
- Geographic query optimization using PostGIS (replace `DecimalField` lat/lon with `PointField`)

---

## Quick Reference — Files by Priority to Touch

```
CRITICAL NOW:
  appointments/signals.py          ← fix thread-unsafe state tracking
  appointments/serializers.py      ← fix N+1, split file
  appointments/services.py         ← add select_for_update
  appointments/models.py           ← add patient XOR constraint + indexes
  invoices/models.py               ← add patient XOR constraint + indexes
  nurse_requests/models.py         ← add patient XOR constraint + indexes + geo validators
  prescriptions/models.py          ← add patient XOR constraint
  medical_record/models.py         ← add patient XOR constraint

HIGH NEXT:
  common/views.py (create)         ← BaseModelViewSet with StandardPagination
  common/validators.py             ← add lat/lon validators
  core/settings/base.py            ← MEDILINK config dict
  providers/models/doctor.py       ← fix nullable unique constraint
  accounts/views/                  ← replace string role checks with enums

MEDIUM LATER:
  appointments/serializers/ (split into directory)
  nurse_requests/serializers/ (split into directory)
  services/pricing.py (create)     ← centralize pricing logic
  providers/models/provider.py     ← add typed_profile property, remove legacy fields
```
