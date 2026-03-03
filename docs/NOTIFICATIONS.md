# Medilink — Notifications System (Full Documentation)

> **Last updated:** 2026-03-03

This document covers **every** notification channel in Medilink: REST API for
in-app history, Firebase Cloud Messaging (FCM) for push, and Django Channels
WebSockets for real-time UI updates.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Delivery Channels](#2-delivery-channels)
3. [REST API — Notification Management](#3-rest-api--notification-management)
4. [FCM Push Notifications](#4-fcm-push-notifications)
5. [WebSocket Real-Time Events](#5-websocket-real-time-events)
6. [Appointment Notifications](#6-appointment-notifications)
7. [Nurse Request Notifications](#7-nurse-request-notifications)
8. [Invoice Notifications](#8-invoice-notifications)
9. [Prescription Notifications](#9-prescription-notifications)
10. [Notification Types Reference](#10-notification-types-reference)
11. [WebSocket Event Reference](#11-websocket-event-reference)
12. [Frontend Integration Guide](#12-frontend-integration-guide)

---

## 1. Architecture Overview

```
┌──────────┐   REST API   ┌──────────────────────────┐
│ Frontend │◄────────────►│  Django REST Framework    │
│ (Web /   │              │  notifications/views.py   │
│  Mobile) │              └──────────────────────────┘
│          │
│          │   WebSocket   ┌──────────────────────────┐
│          │◄─────────────►│  Django Channels          │
│          │               │  consumers.py (3 apps)    │
│          │               └──────────────────────────┘
│          │
│          │   FCM Push    ┌──────────────────────────┐
│          │◄──────────────│  Firebase Cloud Messaging │
└──────────┘               │  via NotificationService  │
                           └──────────────────────────┘
```

**Flow for every event** (e.g. appointment confirmed):

1. View / signal handler calls `NotificationService.create_for_object()` →
   saves `Notification` row + sends FCM push to all user devices.
2. Same handler calls `WebSocketBroadcaster.send_to_patient()` / `.send_to_provider()` →
   pushes JSON via the Channel Layer to connected WebSocket clients.
3. Frontend receives WS event, updates its UI state **without refreshing**.

---

## 2. Delivery Channels

| Channel | Purpose | Persistence | Offline? |
|---------|---------|-------------|----------|
| **In-app (DB)** | Notification bell / history list | ✅ `Notification` model | ✅ Read later |
| **FCM Push** | Mobile/web push when app is background | ❌ Transient | ✅ Delivered by OS |
| **WebSocket** | Instant UI update while connected | ❌ Transient | ❌ Missed if offline |

All three fire together for important events (appointments, nurse requests).
Invoice & prescription notifications currently use **In-app + FCM only** (no WS).

---

## 3. REST API — Notification Management

Base path: `/api/notifications/`

### 3.1 Device Token Registration

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/api/notifications/register/` | `{ "token": "<fcm_token>", "device_type": "android"\|"ios"\|"web" }` | Register device for push |
| `POST` | `/api/notifications/unregister/` | `{ "token": "<fcm_token>" }` | Remove one device |
| `DELETE` | `/api/notifications/unregister-all/` | — | Remove all devices (logout) |
| `GET` | `/api/notifications/devices/` | — | List active devices |

### 3.2 Notification History

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/notifications/` | List all notifications (newest first) |
| `PATCH` | `/api/notifications/<uuid>/read/` | Mark one as read |
| `POST` | `/api/notifications/mark-all-read/` | Mark all as read |
| `DELETE` | `/api/notifications/<uuid>/` | Delete one |
| `DELETE` | `/api/notifications/clear-all/` | Delete all |

#### GET `/api/notifications/` — Response Example

```json
{
  "notifications": [
    {
      "id": "a1b2c3d4-...",
      "title": "✅ Appointment Confirmed",
      "body": "Your appointment with Dr. Smith on March 10, 2026 at 02:30 PM has been confirmed.",
      "notification_type": "APPOINTMENT_CONFIRMED",
      "data": {
        "type": "APPOINTMENT_CONFIRMED",
        "priority": "HIGH",
        "action_url": "/appointments/abc-123",
        "object_type": "Appointment",
        "object_id": "abc-123"
      },
      "is_read": false,
      "timestamp": "2026-03-03T10:30:00Z"
    }
  ],
  "count": 1,
  "unread_count": 1
}
```

### 3.3 Firebase Config & Testing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/notifications/config/` | Get Firebase client config (public) |
| `POST` | `/api/notifications/test/` | Send test push to yourself |
| `POST` | `/api/notifications/test-user/` | Send test push to another user |

---

## 4. FCM Push Notifications

### How It Works

1. Frontend obtains an FCM token from Firebase SDK.
2. Frontend registers it via `POST /api/notifications/register/`.
3. Backend stores it in `DeviceToken`.
4. When an event fires, `NotificationService.send_to_user()` fetches all
   active tokens and sends via `firebase_admin.messaging`.
5. Invalid tokens are automatically deactivated.

### Push Payload Format

```json
{
  "notification": {
    "title": "✅ Appointment Confirmed",
    "body": "Your appointment with Dr. Smith has been confirmed."
  },
  "data": {
    "type": "APPOINTMENT_CONFIRMED",
    "object_type": "Appointment",
    "object_id": "abc-123",
    "action_url": "/appointments/abc-123"
  }
}
```

The `data` field can be used client-side to deep-link into the correct screen.

---

## 5. WebSocket Real-Time Events

### 5.1 Connection

All WebSocket endpoints require authentication via query parameter:

```
ws://<host>/ws/<path>/?token=<auth-token>
```

The `WebSocketAuthMiddlewareStack` extracts the token and resolves the user.

### 5.2 Available WebSocket Endpoints

| Endpoint | Consumer | Groups Joined | Purpose |
|----------|----------|---------------|---------|
| `ws/notifications/` | `NotificationConsumer` | `user_<id>_notifications` | All notification types for this user |
| `ws/appointments/` | `AppointmentConsumer` | `user_<id>_appointments` | All appointment events for this user |
| `ws/appointments/<uuid>/` | `AppointmentConsumer` | `user_<id>_appointments` + `appointment_<uuid>` | Single appointment real-time tracking |
| `ws/nurse-requests/available/` | `NurseRequestConsumer` | `user_<id>_nurse_requests` + `city_<city>_requests` | Nurse: new requests in their city |
| `ws/nurse-requests/<id>/` | `NurseRequestConsumer` | `user_<id>_nurse_requests` + `request_<id>_updates` | Patient: track specific request |

### 5.3 Channel Groups

| Group Pattern | Who's In It | Events Received |
|---------------|-------------|-----------------|
| `user_<id>_notifications` | Every user on `/ws/notifications/` | All notifications + appointment events + nurse request events |
| `user_<id>_appointments` | Every user on `/ws/appointments/` | `new_appointment`, `appointment_confirmed`, etc. |
| `user_<id>_nurse_requests` | Every user on `/ws/nurse-requests/*` | `nurse_request_new`, `nurse_request_offer`, etc. |
| `appointment_<uuid>` | Users watching a specific appointment | Events for that appointment only |
| `request_<id>_updates` | Users watching a specific nurse request | Events for that request only |
| `city_<city>_requests` | Nurses listening for requests in a city | `nurse_request_new`, `nurse_request_cancelled` |

### 5.4 Client → Server Messages

All WebSocket endpoints support:

```json
{ "type": "ping" }          →  { "type": "pong" }
```

The `NotificationConsumer` also accepts:

```json
{ "type": "mark_read", "id": "<notification-uuid>" }
{ "type": "mark_all_read" }
```

---

## 6. Appointment Notifications

Source: `appointments/notifications.py` → `AppointmentNotifier`

Every event sends:
- **In-app + FCM push** via `NotificationService.create_for_object()`
- **WebSocket** via `WebSocketBroadcaster` to user groups + appointment group

The WS payload under `data.appointment` contains the **full `AppointmentDetailSerializer`
output** — same fields as `GET /api/appointments/<id>/` — so the frontend can replace
its local state directly.

### 6.1 Events

| Event Trigger | WS `type` | FCM Type | Who Receives |
|---------------|-----------|----------|--------------|
| Patient creates appointment | `new_appointment` | `APPOINTMENT_CREATED` | Provider (always) + Patient (if provider created it) |
| Provider confirms | `appointment_confirmed` | `APPOINTMENT_CONFIRMED` | Patient + Provider |
| Provider rejects | `appointment_rejected` | `APPOINTMENT_CANCELLED` | Patient + Provider |
| Either side cancels | `appointment_cancelled` | `APPOINTMENT_CANCELLED` | The other party (+ system cancel → both) |
| Either side reschedules | `appointment_rescheduled` | `APPOINTMENT_UPDATED` | Both |
| Provider completes | `appointment_completed` | `APPOINTMENT_COMPLETED` | Patient + Provider |
| Provider marks no-show | `appointment_no_show` | `APPOINTMENT_CANCELLED` | Patient + Provider |
| Reminder (scheduled) | `appointment_reminder` | `APPOINTMENT_REMINDER` | Patient |
| Non-status fields updated | `appointment_updated` | _(WS only)_ | Both |

### 6.2 WS Payload Example — `appointment_confirmed`

```json
{
  "type": "appointment_confirmed",
  "data": {
    "appointment": {
      "id": "abc-123",
      "provider": 5,
      "provider_name": "Dr. Ahmed Benali",
      "provider_email": "ahmed@clinic.dz",
      "provider_type": "DOCTOR",
      "patient_user": 12,
      "patient_record": null,
      "patient_name": "Yacine Kaci",
      "patient_email": "yacine@email.com",
      "patient_phone": "+213555123456",
      "service": 3,
      "service_name": "General Consultation",
      "service_description": "...",
      "selected_services": [
        {
          "id": 1,
          "service_id": "svc-uuid",
          "service_name": "General Consultation",
          "service_description": "...",
          "price": "3000.00",
          "currency": "DZD",
          "notes": ""
        }
      ],
      "total_price": "3000.00",
      "scheduled_date": "2026-03-10",
      "scheduled_time": "14:30:00",
      "duration_minutes": 30,
      "location_type": "IN_CLINIC",
      "location_type_display": "In Clinic",
      "clinic_address": null,
      "home_address": null,
      "meeting_link": null,
      "status": "CONFIRMED",
      "status_display": "Confirmed",
      "reason": "Regular checkup",
      "notes": "",
      "cancellation_reason": null,
      "cancellation_notes": null,
      "cancelled_by": null,
      "cancelled_by_name": null,
      "cancelled_at": null,
      "created_by": 12,
      "created_by_name": "Yacine Kaci",
      "confirmed_at": "2026-03-03T10:30:00Z",
      "completed_at": null,
      "is_upcoming": true,
      "is_past": false,
      "allowed_actions": {
        "can_confirm": false,
        "can_reject": false,
        "can_cancel": true,
        "can_complete": true,
        "can_mark_no_show": true,
        "can_reschedule": true,
        "is_terminal": false
      },
      "created_at": "2026-03-02T09:00:00Z",
      "updated_at": "2026-03-03T10:30:00Z"
    },
    "message": "Your appointment with Dr. Ahmed Benali has been confirmed!"
  }
}
```

### 6.3 Signal Flow

```
View saves Appointment → pre_save captures old status → post_save fires
→ transaction.on_commit:
    1. Re-fetches fresh appointment (with select_related/prefetch_related)
    2. Calls AppointmentNotifier.notify_xxx(appointment)
    3. Notifier serializes with AppointmentDetailSerializer
    4. Creates in-app + FCM via NotificationService
    5. Broadcasts via WebSocketBroadcaster to user groups + appointment group
```

---

## 7. Nurse Request Notifications

Source: `nurse_requests/notifications.py` → `NurseRequestNotifier`

Every WS payload under `data.request` contains the **full
`NurseServiceRequestDetailSerializer` output** — same fields as
`GET /api/nurse-requests/patient/nurse-requests/<id>/` — so the frontend
can replace its local state directly.

### 7.1 Events

| Event Trigger | WS `type` | FCM Type | Who Receives |
|---------------|-----------|----------|--------------|
| Patient creates request | `nurse_request_new` | _(WS only)_ | City nurses (WS) + Patient (WS confirmation) |
| Nurse submits offer (at patient price) | `nurse_request_offer` | `NURSE_REQUEST_OFFER` | Patient (FCM + WS) |
| Nurse submits counter-offer | `nurse_request_offer` | `NURSE_REQUEST_COUNTER_OFFER` | Patient (FCM + WS) |
| Patient accepts an offer | `nurse_request_accepted` | `NURSE_REQUEST_ACCEPTED` | Nurse (FCM + WS) + Patient (FCM + WS) |
| Nurse starts the service | `nurse_request_in_progress` | `NURSE_REQUEST_IN_PROGRESS` | Patient (FCM + WS) + Nurse (WS) |
| Service completed | `nurse_request_completed` | `NURSE_REQUEST_COMPLETED` | Patient (FCM + WS) + Nurse (FCM + WS) |
| Request cancelled | `nurse_request_cancelled` | `NURSE_REQUEST_CANCELLED` | Other party (FCM + WS) + City nurses (WS) |

### 7.2 WS Payload Example — `nurse_request_offer`

```json
{
  "type": "nurse_request_offer",
  "data": {
    "request": {
      "id": 42,
      "patient_user": 12,
      "patient_record": null,
      "patient_name": "Yacine Kaci",
      "service": {
        "id": 8,
        "name": "IV Drip Administration",
        "description": "Professional IV drip setup and monitoring",
        "base_price": "5000.00",
        "estimated_duration": "01:00:00",
        "is_active": true,
        "icon": null,
        "currency": "DZD",
        "is_home_service": true,
        "created_at": "2026-01-15T...",
        "updated_at": "2026-02-20T..."
      },
      "accepted_nurse": null,
      "accepted_nurse_name": null,
      "accepted_nurse_profile": null,
      "base_price": "5000.00",
      "patient_offered_price": "5500.00",
      "final_price": null,
      "address": null,
      "address_details": null,
      "latitude": "36.752887",
      "longitude": "3.042048",
      "city": "Algiers",
      "state": "Algiers",
      "address_line": "123 Rue Didouche Mourad",
      "country": "Algeria",
      "status": "NURSE_RESPONDED",
      "notes": "",
      "offers": [
        {
          "id": 1,
          "nurse_id": 7,
          "nurse_name": "Fatima Boudiaf",
          "nurse_rating": 4.8,
          "nurse_review_count": 23,
          "nurse_profile_image": "https://...",
          "nurse_years_experience": 5,
          "nurse_completed_services": 47,
          "nurse_biography": "Experienced nurse specializing in...",
          "nurse_is_verified": true,
          "offered_price": "5500.00",
          "status": "PENDING",
          "estimated_arrival_time": "00:25:00",
          "distance_km": "3.50",
          "notes": "I can be there in 25 minutes",
          "created_at": "2026-03-03T10:45:00Z",
          "responded_at": "2026-03-03T10:45:00Z"
        }
      ],
      "created_at": "2026-03-03T10:30:00Z",
      "updated_at": "2026-03-03T10:45:00Z",
      "accepted_at": null,
      "started_at": null,
      "completed_at": null,
      "cancelled_at": null,
      "cancellation_reason": "",
      "can_leave_review": false
    },
    "offer": {
      "id": 1,
      "nurse_id": 7,
      "nurse_name": "Fatima Boudiaf",
      "nurse_rating": 4.8,
      "nurse_review_count": 23,
      "nurse_profile_image": "https://...",
      "nurse_years_experience": 5,
      "nurse_completed_services": 47,
      "nurse_biography": "Experienced nurse specializing in...",
      "nurse_is_verified": true,
      "offered_price": "5500.00",
      "status": "PENDING",
      "estimated_arrival_time": "00:25:00",
      "distance_km": "3.50",
      "notes": "I can be there in 25 minutes",
      "created_at": "2026-03-03T10:45:00Z",
      "responded_at": "2026-03-03T10:45:00Z"
    },
    "message": "Fatima Boudiaf accepted your request for IV Drip Administration at $5500.00."
  }
}
```

### 7.3 Signal Flow

```
View action (create / accept / cancel / start / complete)
→ Service method does DB work inside transaction.atomic()
→ View sends Django signal (request_created / request_status_changed / nurse_offer_submitted)
→ Signal receiver wraps in transaction.on_commit:
    1. Re-fetches fresh request with select_related / prefetch_related
    2. Calls NurseRequestNotifier.notify_xxx(request, [offer])
    3. Notifier serializes with NurseServiceRequestDetailSerializer
    4. Creates in-app + FCM via NotificationService.create_for_object()
    5. Broadcasts via WebSocketBroadcaster to user groups + request group + city group
```

### 7.4 Signals

| Signal | Sent From | kwargs | Receiver Action |
|--------|-----------|--------|-----------------|
| `request_created` | `perform_create`, `use_saved_address` | `request` | `notify_new_request()` — city-wide WS broadcast |
| `nurse_offer_submitted` | nurse `accept`, `counter_offer` views | `request`, `offer` | `notify_nurse_offer()` — FCM + WS to patient |
| `request_status_changed` | patient `accept`, `cancel`; nurse `start`, `complete` | `request`, `old_status`, `new_status` | Routes to `notify_offer_accepted`, `notify_service_started`, `notify_service_completed`, `notify_request_cancelled` |

---

## 8. Invoice Notifications

Source: `invoices/services.py`

Uses **In-app + FCM only** (no WebSocket broadcast).

| Event | Method | FCM Type | Priority |
|-------|--------|----------|----------|
| Invoice sent to patient | `notify_invoice_sent()` | `INVOICE_CREATED` | NORMAL |
| Payment received | `notify_payment_received()` | `PAYMENT_RECEIVED` | NORMAL |
| Invoice overdue | `notify_overdue()` | `INVOICE_OVERDUE` | HIGH |
| Payment reminder | `send_payment_reminder()` | `INVOICE_OVERDUE` | HIGH |

---

## 9. Prescription Notifications

Source: `prescriptions/signals.py`

Uses **In-app + FCM only** (no WebSocket broadcast).

| Event | FCM Type | Priority |
|-------|----------|----------|
| New prescription issued | `PRESCRIPTION_ISSUED` | HIGH |

---

## 10. Notification Types Reference

All values of `NotificationType` (stored in `notification_type` field):

| Type | Category | Used By |
|------|----------|---------|
| `APPOINTMENT_CREATED` | APPOINTMENTS | AppointmentNotifier |
| `APPOINTMENT_CONFIRMED` | APPOINTMENTS | AppointmentNotifier |
| `APPOINTMENT_CANCELLED` | APPOINTMENTS | AppointmentNotifier (cancel / reject / no-show) |
| `APPOINTMENT_UPDATED` | APPOINTMENTS | AppointmentNotifier (reschedule) |
| `APPOINTMENT_REMINDER` | APPOINTMENTS | AppointmentNotifier |
| `APPOINTMENT_COMPLETED` | APPOINTMENTS | AppointmentNotifier |
| `NURSE_REQUEST_NEW` | NURSE_REQUESTS | NurseRequestNotifier |
| `NURSE_REQUEST_OFFER` | NURSE_REQUESTS | NurseRequestNotifier (nurse accepts at patient price) |
| `NURSE_REQUEST_COUNTER_OFFER` | NURSE_REQUESTS | NurseRequestNotifier (nurse counter-offers) |
| `NURSE_REQUEST_ACCEPTED` | NURSE_REQUESTS | NurseRequestNotifier (patient accepts offer) |
| `NURSE_REQUEST_IN_PROGRESS` | NURSE_REQUESTS | NurseRequestNotifier |
| `NURSE_REQUEST_COMPLETED` | NURSE_REQUESTS | NurseRequestNotifier |
| `NURSE_REQUEST_CANCELLED` | NURSE_REQUESTS | NurseRequestNotifier |
| `PRESCRIPTION_ISSUED` | PRESCRIPTIONS | prescriptions signals |
| `PRESCRIPTION_RENEWED` | PRESCRIPTIONS | _(not yet used)_ |
| `INVOICE_CREATED` | INVOICES | InvoiceService |
| `INVOICE_PAID` | INVOICES | _(not yet used)_ |
| `INVOICE_OVERDUE` | INVOICES | InvoiceService |
| `PAYMENT_RECEIVED` | INVOICES | InvoiceService |
| `MEDICAL_RECORD_SHARED` | MEDICAL_RECORDS | _(not yet used)_ |
| `LAB_RESULTS_READY` | MEDICAL_RECORDS | _(not yet used)_ |
| `SYSTEM` | SYSTEM | System-level |
| `MESSAGE` | MESSAGES | _(not yet used)_ |
| `GENERAL` | GENERAL | Default fallback |

---

## 11. WebSocket Event Reference

### 11.1 Appointment Events

All carry `data.appointment` with full `AppointmentDetailSerializer` output.

| WS `type` | Extra fields in `data` | Trigger |
|------------|----------------------|---------|
| `new_appointment` | `message` | Created |
| `appointment_confirmed` | `message` | Provider confirms |
| `appointment_rejected` | `reason`, `message` | Provider rejects |
| `appointment_cancelled` | `appointment_id`, `cancelled_by` (`patient`/`provider`/`system`), `reason`, `message` | Either cancels |
| `appointment_rescheduled` | `old_status`, `new_status`, `message` | Rescheduled |
| `appointment_completed` | `message` | Provider completes |
| `appointment_no_show` | `message` | Provider marks no-show |
| `appointment_reminder` | `minutes_until`, `message` | Scheduled reminder |
| `appointment_updated` | `message` | Non-status field change |

### 11.2 Nurse Request Events

All carry `data.request` with full `NurseServiceRequestDetailSerializer` output.

| WS `type` | Extra fields in `data` | Trigger |
|------------|----------------------|---------|
| `nurse_request_new` | `message` | Patient creates request |
| `nurse_request_offer` | `offer` (full serialized), `message` | Nurse submits offer |
| `nurse_request_accepted` | `message` | Patient accepts offer |
| `nurse_request_in_progress` | `message` | Nurse starts service |
| `nurse_request_completed` | `message` | Service done |
| `nurse_request_cancelled` | `cancelled_by` (`patient`/`nurse`/`system`), `reason`, `message` | Request cancelled |

### 11.3 General Notification Events

| WS `type` | Fields | When |
|------------|--------|------|
| `notification` | `data` (full notification object) | Any new in-app notification |
| `unread_count` | `count` | After connect, after mark_read |

---

## 12. Frontend Integration Guide

### 12.1 Connecting to WebSocket

```javascript
// Auth token from login
const token = localStorage.getItem('authToken');

// General notifications (all events)
const notifWs = new WebSocket(`ws://${host}/ws/notifications/?token=${token}`);

// Appointments stream (appointment events only)
const apptWs = new WebSocket(`ws://${host}/ws/appointments/?token=${token}`);

// Single appointment tracking
const apptDetailWs = new WebSocket(`ws://${host}/ws/appointments/${appointmentId}/?token=${token}`);

// Nurse requests — patient watching their request
const nurseReqWs = new WebSocket(`ws://${host}/ws/nurse-requests/${requestId}/?token=${token}`);

// Nurse requests — nurse browsing available
const nurseAvailWs = new WebSocket(`ws://${host}/ws/nurse-requests/available/?token=${token}`);
```

### 12.2 Handling Events

```javascript
notifWs.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  switch (msg.type) {
    // ── Appointment events ──────────────────────────
    case 'new_appointment':
    case 'appointment_confirmed':
    case 'appointment_rejected':
    case 'appointment_cancelled':
    case 'appointment_rescheduled':
    case 'appointment_completed':
    case 'appointment_no_show':
    case 'appointment_updated':
      // msg.data.appointment = full appointment object
      // Replace local state directly:
      updateAppointmentInStore(msg.data.appointment);
      showToast(msg.data.message);
      break;

    case 'appointment_reminder':
      showReminderDialog(msg.data.appointment, msg.data.minutes_until);
      break;

    // ── Nurse request events ────────────────────────
    case 'nurse_request_new':
      // For nurses: new request appeared
      addRequestToList(msg.data.request);
      break;

    case 'nurse_request_offer':
      // For patients: a nurse responded
      updateRequestInStore(msg.data.request);
      showOfferNotification(msg.data.offer);
      break;

    case 'nurse_request_accepted':
    case 'nurse_request_in_progress':
    case 'nurse_request_completed':
    case 'nurse_request_cancelled':
      updateRequestInStore(msg.data.request);
      showToast(msg.data.message);
      break;

    // ── General ─────────────────────────────────────
    case 'notification':
      addToNotificationBell(msg.data);
      break;

    case 'unread_count':
      updateBadge(msg.count);
      break;
  }
};
```

### 12.3 Keep-Alive

Send a ping every 30 seconds to prevent proxy timeouts:

```javascript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

### 12.4 Mark Read via WebSocket

```javascript
// Mark a single notification read
notifWs.send(JSON.stringify({ type: 'mark_read', id: notificationId }));

// Mark all read
notifWs.send(JSON.stringify({ type: 'mark_all_read' }));
// Server responds with: { "type": "unread_count", "count": 0 }
```

### 12.5 Registering for FCM Push

```javascript
// After Firebase init in the browser / mobile app
const fcmToken = await messaging.getToken();

await fetch('/api/notifications/register/', {
  method: 'POST',
  headers: { 'Authorization': `Token ${authToken}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({ token: fcmToken, device_type: 'web' })
});
```

### 12.6 Which WebSocket Should I Connect To?

| User Role | Recommended Connections |
|-----------|----------------------|
| **Patient (general)** | `ws/notifications/` — everything in one stream |
| **Patient (viewing appointments list)** | `ws/notifications/` + `ws/appointments/` |
| **Patient (viewing single appointment)** | `ws/appointments/<uuid>/` |
| **Patient (nurse request active)** | `ws/notifications/` + `ws/nurse-requests/<id>/` |
| **Provider (dashboard)** | `ws/notifications/` + `ws/appointments/` |
| **Nurse (browsing requests)** | `ws/notifications/` + `ws/nurse-requests/available/` |
| **Nurse (active service)** | `ws/notifications/` + `ws/nurse-requests/<id>/` |

> **Tip:** `ws/notifications/` receives ALL event types (appointments +
> nurse requests + general notifications). If your app only needs one
> connection, this is sufficient. The dedicated streams (`ws/appointments/`,
> `ws/nurse-requests/`) are for pages that only care about those specific events.

---

## Backend File Reference

| File | Purpose |
|------|---------|
| `notifications/models.py` | `Notification`, `DeviceToken`, enums |
| `notifications/services.py` | `NotificationService` (FCM), `WebSocketBroadcaster` (WS) |
| `notifications/consumers.py` | `NotificationConsumer` — general WS consumer |
| `notifications/views.py` | REST API endpoints |
| `notifications/middleware.py` | `WebSocketAuthMiddlewareStack` (token auth) |
| `notifications/routing.py` | WS URL patterns |
| `appointments/notifications.py` | `AppointmentNotifier` |
| `appointments/signals.py` | Signal receivers → `AppointmentNotifier` |
| `appointments/consumers.py` | `AppointmentConsumer` — appointment WS |
| `nurse_requests/notifications.py` | `NurseRequestNotifier` |
| `nurse_requests/signals.py` | Signal receivers → `NurseRequestNotifier` |
| `nurse_requests/consumers.py` | `NurseRequestConsumer` — nurse request WS |
| `invoices/services.py` | Invoice notification methods |
| `prescriptions/signals.py` | Prescription notification signal |
| `core/asgi.py` | ASGI entry point combining all WS routes |
