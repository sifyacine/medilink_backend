# Nurse Requests API — v2 Changelog & Production Reference

> **Supersedes:** `nurse_requests_api.md`
> **Date:** 2026-05-05
> **Status:** Production-ready

This document describes every change made during the v2 production hardening pass, the rationale for each change, and the definitive endpoint + WebSocket reference for both the patient app and nurse app.

---

## Summary of Changes

| # | File | Type | Description |
|---|------|------|-------------|
| 1 | `services.py` | Bug fix | `patient_accept_offer` captured `old_status` AFTER mutating the object — always logged `ACCEPTED → ACCEPTED` |
| 2 | `services.py` | Bug fix | `nurse_reject_request` did not create a `NurseOffer` record, so rejected requests reappeared in the nurse's feed on every refresh |
| 3 | `views.py` | Bug fix | Missing `import logging` and `RequestHistory` import caused `NameError` at runtime in `decline_offer` |
| 4 | `views.py` | Bug fix | `accept` action sent signal with hardcoded `old_status=NURSE_RESPONDED` — wrong when status was `PATIENT_DECISION` |
| 5 | `views.py` | Bug fix | `cancel` action captured `old_status` from the already-mutated object (same Python reference returned by `cancel_request`) |
| 6 | `views.py` | Bug fix | `decline_offer` used `__import__('logging')` inline hack — replaced with module-level `logger` |
| 7 | `views.py` | Feature | `start` and `complete` removed from `PatientNurseRequestViewSet` (had `IsPatient` permission — nurses could not call them) |
| 8 | `views.py` | Feature | `start` and `complete` added to `NurseRequestHistoryViewSet` with full nurse ownership check + signal dispatch |
| 9 | `views.py` | Hardening | `reject` action now validates request status is `SEARCHING`/`NURSE_RESPONDED` and blocks double-response |
| 10 | `consumers.py` | Bug fix | `get_nurse_city` used `ContentType` for `provider` object — views use `user` object; misaligned means nurses never joined the city channel |
| 11 | `consumers.py` | Feature | Added missing WS handlers: `nurse_offer_declined`, `nurse_review_received`, `nurse_rating_updated` |
| 12 | `consumers.py` | Hardening | Unauthenticated connections now close with code `4001` instead of silently dropping |
| 13 | `consumers.py` | Hardening | City lookup has two fallbacks (any primary address, then any address) so nurses without a `WORK`/`CLINIC` address still join a city group |

---

## Bug Details

### Bug 1 — `patient_accept_offer` old_status always `ACCEPTED`

**Before:**
```python
request_obj.status = RequestStatus.ACCEPTED
request_obj.save()
# ...
RequestHistory.objects.create(
    old_status=request_obj.status,   # ← already ACCEPTED at this point
    new_status=RequestStatus.ACCEPTED,
)
```

**After:**
```python
old_status = request_obj.status      # ← captured before any mutation
request_obj.status = RequestStatus.ACCEPTED
request_obj.save()
# ...
RequestHistory.objects.create(
    old_status=old_status,
    new_status=RequestStatus.ACCEPTED,
)
```

---

### Bug 2 — Rejected requests reappear in nurse feed

`NurseAvailableRequestsViewSet.get_queryset` excludes requests the nurse already responded to:
```python
.exclude(offers__nurse=nurse.provider)
```
But `nurse_reject_request` only wrote a `RequestHistory` row — no `NurseOffer` was created — so the exclude had nothing to match on.

**Fix:** `nurse_reject_request` now creates a `NurseOffer` with `status=REJECTED` as the first operation, then logs to `RequestHistory`. The `unique_together = ['request', 'nurse']` constraint prevents duplicate records.

---

### Bug 3 — NameError at runtime in `decline_offer`

`views.py` had no `import logging` or `from .models import RequestHistory`. Both were used inside `decline_offer`.

**Fix:** Added at the top of `views.py`:
```python
import logging
from .models import (
    NurseServiceRequest, NurseOffer, RequestHistory, RequestStatus, OfferStatus
)
logger = logging.getLogger(__name__)
```

---

### Bug 4 — Signal sent with wrong `old_status` in `accept`

**Before:**
```python
request_status_changed.send(
    old_status=RequestStatus.NURSE_RESPONDED,  # hardcoded — wrong for PATIENT_DECISION
    ...
)
```

**After:**
```python
old_status = request_obj.status   # captured before calling service
updated_request = NurseRequestService.patient_accept_offer(...)
request_status_changed.send(old_status=old_status, ...)
```

---

### Bug 5 — Signal sent with wrong `old_status` in `cancel`

`cancel_request` mutates and returns `request_obj` (same Python object). Reading `request_obj.status` after the call returns the new `CANCELLED` value.

**Fix:** Same pattern — capture `old_status = request_obj.status` before calling the service.

---

### Bug 6 — `decline_offer` inline logger hack

**Before:** `logger_instance = __import__('logging').getLogger(__name__)`
**After:** Uses module-level `logger = logging.getLogger(__name__)`

---

### Bug 7 & 8 — `start` / `complete` inaccessible to nurses

These actions lived in `PatientNurseRequestViewSet` with `permission_classes = [IsAuthenticated, IsPatient]`. A nurse calling them received `403 Forbidden`.

**Fix:**
- **Removed** `start` and `complete` from `PatientNurseRequestViewSet`
- **Added** to `NurseRequestHistoryViewSet` (which has `[IsAuthenticated, IsNurse]`)
- Each action verifies `request_obj.accepted_nurse == nurse.provider` before proceeding
- Both actions dispatch `request_status_changed` signal for real-time notifications

New endpoints:
```
POST /api/nurse-requests/nurse/request-history/{id}/start/
POST /api/nurse-requests/nurse/request-history/{id}/complete/
```

---

### Bug 9 — `reject` had no guards

`reject` accepted any request regardless of status and allowed a nurse who had already accepted to call reject again (would silently succeed but create a duplicate history entry, and with the new REJECTED offer fix would hit the `unique_together` DB constraint and crash).

**Fix:**
1. Validates `request_obj.status in [SEARCHING, NURSE_RESPONDED]`
2. Checks `NurseOffer.objects.filter(...).exclude(status=REJECTED).first()` — if the nurse has a non-rejected offer (i.e., they already accepted/counter-offered) returns `NR4003`

---

### Bug 10 — Nurse never joins city channel

**Before (broken):**
```python
ct = ContentType.objects.get_for_model(provider)   # ContentType for Provider model
addr = Address.objects.filter(content_type=ct, object_id=provider.pk).first()
```

**After (aligned with views):**
```python
user_ct = ContentType.objects.get_for_model(self.user)   # ContentType for User model
addr = Address.objects.filter(
    content_type=user_ct, object_id=self.user.pk,
    address_type__in=['WORK', 'CLINIC'], is_primary=True,
).first()
```

The views look up addresses by `user`, not by `provider`. The consumer now matches this, plus has two fallback levels so nurses with no WORK/CLINIC address still connect to a city group.

---

### Bug 11 — Missing WS event handlers

The notifier broadcast `nurse_offer_declined`, `nurse_review_received`, and `nurse_rating_updated` via `WebSocketBroadcaster`, but the consumer had no handler for these types — they were silently dropped.

**Added:**
```python
async def nurse_offer_declined(self, event): ...
async def nurse_review_received(self, event): ...
async def nurse_rating_updated(self, event): ...
```

---

## Endpoint Reference (v2)

> Only endpoints that changed are listed in full. Unchanged endpoints from `nurse_requests_api.md` remain valid.

### Base URL
```
/api/nurse-requests/
```

### Auth
```
Authorization: Token <token>
```

---

### NURSE APP — Status Management

#### Start Service
```
POST /api/nurse-requests/nurse/request-history/{id}/start/
```

**Permission:** Authenticated nurse + must be the `accepted_nurse` on the request.

**Preconditions:**
- Request status is `ACCEPTED`
- Authenticated nurse is `request.accepted_nurse`

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { "id": 42, "status": "IN_PROGRESS", "started_at": "2026-05-05T10:30:00Z", "..." },
  "message": "Service started"
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Nurse is not the accepted nurse on this request |
| `NR3003` | 400 | Request is not in `ACCEPTED` status |

**Side effects:**
- `request.status` → `IN_PROGRESS`
- `request.started_at` → now
- `RequestHistory` row created
- `request_status_changed` signal fires → `notify_service_started` → FCM + WS to patient

---

#### Complete Service
```
POST /api/nurse-requests/nurse/request-history/{id}/complete/
```

**Permission:** Authenticated nurse + must be the `accepted_nurse` on the request.

**Preconditions:**
- Request status is `IN_PROGRESS`
- Authenticated nurse is `request.accepted_nurse`

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { "id": 42, "status": "COMPLETED", "completed_at": "2026-05-05T11:45:00Z", "..." },
  "message": "Service completed successfully"
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Nurse is not the accepted nurse on this request |
| `NR3003` | 400 | Request is not in `IN_PROGRESS` status |

**Side effects:**
- `request.status` → `COMPLETED`
- `request.completed_at` → now
- `RequestHistory` row created
- `request_status_changed` signal fires → `notify_service_completed` → FCM + WS to patient
- `can_leave_review` becomes `true` for the patient

---

#### Reject a Request (hardened)
```
POST /api/nurse-requests/nurse/available-requests/{id}/reject/
Content-Type: application/json
```

**Body (optional):**
```json
{ "reason": "Too far from my location" }
```

**Validations (in order):**
1. Nurse profile exists (`NR6004`)
2. Request exists (`NR3001`)
3. Request status is `SEARCHING` or `NURSE_RESPONDED` (`NR3003`)
4. Nurse has not already submitted a non-rejected offer (`NR4003`)

**Success — `200 OK`**
```json
{ "success": true, "message": "Request dismissed" }
```

**Side effects:**
- Creates `NurseOffer` with `status=REJECTED` (so the request is excluded from the nurse's feed)
- `RequestHistory` row created with `action=NURSE_REJECTED`
- Request does NOT move status — other nurses are unaffected

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR3001` | 404 | Request not found |
| `NR3003` | 400 | Request is no longer open (`ACCEPTED`, `COMPLETED`, `CANCELLED`) |
| `NR4003` | 400 | Nurse already submitted an offer (accept or counter-offer) |

---

## WebSocket Reference (v2)

### Connection URLs

```
ws://<host>/ws/nurse-requests/<request_id>/    # Patient — track one request
ws://<host>/ws/nurse-requests/available/        # Nurse  — city + personal feed
```

**Auth:** Standard token middleware (pass `Authorization: Token <token>` header).
Unauthenticated connections are closed with code **4001**.

### Groups Joined on Connect

| Group name | Who joins | Purpose |
|------------|-----------|---------|
| `user_<id>_nurse_requests` | Everyone | Personal stream |
| `request_<id>_updates` | Patient (and nurse once accepted) | One-request live feed |
| `city_<city>_requests` | Nurses | City-wide new-request broadcast |

> **City group fallback:** If a nurse has no `WORK`/`CLINIC` primary address, the consumer falls back to any primary address, then any address at all, before giving up. Nurses without any saved address receive FCM pushes but no city-channel WS events.

### All Event Types (Client ← Server)

| `type` | Sent to | Trigger |
|--------|---------|---------|
| `nurse_request_new` | Nurse | Patient created a new request in nurse's city |
| `nurse_request_offer` | Patient | Nurse submitted offer or accepted at patient price |
| `nurse_request_accepted` | Nurse | Patient accepted this nurse's offer |
| `nurse_request_in_progress` | Both | Nurse started the service |
| `nurse_request_completed` | Patient | Nurse completed the service |
| `nurse_request_cancelled` | Both | Request cancelled by patient |
| `nurse_offer_declined` | Nurse | Patient declined this nurse's specific offer |
| `nurse_review_received` | Nurse | Patient left a review for the nurse |
| `nurse_rating_updated` | Nurse | Aggregate rating recalculated after new review |
| `nurse_request_updated` | Both | Generic fallback for any other status change |

### Envelope Shape (all events)
```json
{
  "type": "<event_type>",
  "data": { ... }
}
```

`data` always contains the full serialised `NurseServiceRequestDetailSerializer` output plus any extra keys specific to the event (e.g., `offer`, `reason`, `message`).

### Client → Server
```json
{ "type": "ping" }
```
Server responds: `{ "type": "pong" }`

---

## Status Flow (Complete)

```
Patient creates request
        │
        ▼
    SEARCHING ──────────────────────────────────────► CANCELLED (patient)
        │
        │  first nurse responds (accept or counter-offer)
        ▼
 NURSE_RESPONDED ────────────────────────────────────► CANCELLED (patient)
        │
        │  patient accepts one offer
        ▼
    ACCEPTED ───────────────────────────────────────► CANCELLED (patient)
        │
        │  nurse calls  POST .../nurse/request-history/{id}/start/
        ▼
  IN_PROGRESS
        │
        │  nurse calls  POST .../nurse/request-history/{id}/complete/
        ▼
   COMPLETED ──► patient: can_leave_review = true
              ──► nurse:  can_leave_review = true
```

### Who Calls What

| Transition | Endpoint | Caller |
|-----------|---------|--------|
| `CREATED → SEARCHING` | Automatic on request creation | System |
| `SEARCHING → NURSE_RESPONDED` | Automatic when first offer arrives | System |
| `NURSE_RESPONDED → ACCEPTED` | `POST .../patient/nurse-requests/{id}/accept/` | Patient |
| `ACCEPTED → IN_PROGRESS` | `POST .../nurse/request-history/{id}/start/` | **Nurse** |
| `IN_PROGRESS → COMPLETED` | `POST .../nurse/request-history/{id}/complete/` | **Nurse** |
| Any active → `CANCELLED` | `POST .../patient/nurse-requests/{id}/cancel/` | Patient |

---

## Notification Triggers (complete map)

| Event | FCM recipient | WS groups notified |
|-------|-------------|-------------------|
| Request created | All nearby nurses (within 30km) | `city_<city>_requests`, `request_<id>_updates`, patient personal |
| Nurse submits offer | Patient | `request_<id>_updates`, patient personal |
| Patient accepts offer | Accepted nurse | `request_<id>_updates`, accepted nurse personal |
| Patient declines offer | Declined nurse | Nurse personal |
| Service started | Patient | `request_<id>_updates`, patient personal, nurse personal |
| Service completed | Patient | `request_<id>_updates`, patient personal |
| Request cancelled | Accepted nurse (if any) | `request_<id>_updates`, nurse personal, `city_<city>_requests` |
| Review received | Nurse | Nurse personal |
| Rating updated | Nurse | Nurse personal |

---

## Flutter Implementation Notes (v2 delta)

### Patient App — no endpoint changes
The patient-facing endpoint paths are **unchanged**. Only internal bugs were fixed; no URLs moved.

### Nurse App — changed endpoints

| Before (v1) | After (v2) | Notes |
|-------------|------------|-------|
| `POST /patient/nurse-requests/{id}/start/` | `POST /nurse/request-history/{id}/start/` | Moved to nurse namespace + nurse ownership check |
| `POST /patient/nurse-requests/{id}/complete/` | `POST /nurse/request-history/{id}/complete/` | Same |
| Reject: no guard | Reject: validates status + no double-respond | Same URL, stricter |

### WebSocket — new events to handle

Add handlers for:
- `nurse_offer_declined` — update the offer card UI for the nurse
- `nurse_review_received` — show toast/badge on nurse profile
- `nurse_rating_updated` — refresh rating display in nurse dashboard

All new events follow the same envelope: `{ "type": "...", "data": { ... } }`.
