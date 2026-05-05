# On-Demand Nurse Requests — API Documentation

> **For:** Flutter Mobile Developer
> **Applies to:** Patient App & Nurse App
> **Auth:** All endpoints require `Authorization: Token <token>` header
> **Base prefix:** `/api/nurse-requests/`

---

## Table of Contents

**Shared**
1. [Overview & Request Lifecycle](#1-overview--request-lifecycle)
2. [Standard Response Format](#2-standard-response-format)
3. [Error Code Reference](#3-error-code-reference)
4. [Push Notification Events (FCM)](#4-push-notification-events-fcm)
5. [WebSocket Real-time Updates](#5-websocket-real-time-updates)
6. [Services Catalog](#6-services-catalog-shared)

**Patient App**
7. [List my requests](#71-list-my-requests)
8. [Create a request (manual location)](#72-create-a-request-manual-location)
9. [Create using a saved address](#73-create-using-a-saved-address)
10. [Get saved addresses](#74-get-saved-addresses)
11. [Get request detail](#75-get-request-detail)
12. [Accept a nurse offer](#76-accept-a-nurse-offer)
13. [Decline a nurse offer](#77-decline-a-nurse-offer)
14. [Cancel a request](#78-cancel-a-request)
15. [View nurse profile before accepting](#79-view-nurse-profile-before-accepting)
16. [View nurse service history](#710-view-nurse-service-history)
17. [Start service](#711-start-service)
18. [Complete service](#712-complete-service)

**Nurse App**
19. [List my services](#81-list-my-services)
20. [Add a service](#82-add-a-service)
21. [Remove a service](#83-remove-a-service)
22. [Update availability / price](#84-update-availability--price)
23. [List available requests](#85-list-available-requests)
24. [Get request detail (nurse view)](#86-get-request-detail-nurse-view)
25. [Accept at patient price](#87-accept-at-patient-price)
26. [Counter-offer](#88-counter-offer)
27. [Reject a request](#89-reject-a-request)
28. [My offers (history)](#810-my-offers-history)
29. [Request history](#811-request-history)
30. [View patient medical folder](#812-view-patient-medical-folder)

**Reference**
31. [Status Flow Diagram](#9-status-flow-diagram)
32. [Flutter Implementation Checklist](#10-flutter-implementation-checklist)

---

## 1. Overview & Request Lifecycle

This feature works like a ride-hailing app but for nursing services.

**Flow:**
1. Patient browses the services catalog and picks a service
2. Patient creates a request with location + offered price → status becomes `SEARCHING`
3. Nearby **approved** nurses with that service in their profile receive an **FCM push notification**
4. Each nurse can **accept** (at patient's price) or **counter-offer** (higher price)
5. Patient reviews incoming offers and **accepts one**
6. Request moves to `ACCEPTED` → nurse heads to patient location
7. Nurse taps "Start" → `IN_PROGRESS`
8. Nurse taps "Complete" → `COMPLETED`
9. Patient can leave a review for the nurse; nurse can leave a review for the patient

> **Pre-condition for nurses:** A nurse must add at least one service to their profile via `POST /api/nurse-requests/nurse/my-services/add/` **before** they appear in request discovery and receive FCM notifications.

> **Pre-condition for location filtering:** Nurses must have a primary `WORK` or `CLINIC` address with valid coordinates so the Haversine distance filter can match them to nearby requests. Without a location, all in-service requests are shown regardless of distance.

---

## 2. Standard Response Format

### Success — single object
```json
{
  "success": true,
  "data": { ... },
  "message": "Human-readable message"
}
```

### Success — list
```json
{
  "success": true,
  "count": 5,
  "results": [ ... ],
  "message": "..."
}
```

### Error
```json
{
  "success": false,
  "error": {
    "code": "NR3001",
    "message": "Human-readable error message",
    "details": { }
  }
}
```

> Always check `success` first. If `false`, read `error.code` to determine the exact problem.

### Warning (inside a success response)
Some list endpoints return a `warning` key alongside `success: true` when the result is empty for a fixable reason:
```json
{
  "success": true,
  "count": 0,
  "results": [],
  "warning": {
    "code": "NR1006",
    "message": "You have no active services...",
    "action": "Go to /api/nurse-requests/nurse/my-services/ to add services"
  }
}
```

---

## 3. Error Code Reference

| Code | HTTP Status | Area | Meaning |
|------|------------|------|---------|
| `NR1001` | 400 / 404 | Service | Service not found |
| `NR1002` | 400 | Service | Service is not active |
| `NR1003` | 400 | Service | Not a nursing service |
| `NR1004` | 400 | Service | Not available for on-demand requests |
| `NR1005` | 400 | Service | Already added to nurse profile |
| `NR1006` | 400 | Service | Service not in nurse profile |
| `NR2001` | 400 | Price | Offered price is below base price |
| `NR2002` | 400 | Price | Counter-offer is below patient's offered price |
| `NR2003` | 400 | Price | Invalid price value |
| `NR3001` | 404 | Request | Request not found |
| `NR3002` | 403 | Request | Caller is not the request owner |
| `NR3003` | 400 | Request | Invalid status for this action |
| `NR3004` | 400 | Request | Request already cancelled |
| `NR3005` | 400 | Request | Request already accepted |
| `NR3006` | 400 | Request | Request already completed |
| `NR3007` | 403 | Request | Nurse does not offer this service |
| `NR4001` | 400 / 404 | Offer | Offer not found |
| `NR4002` | 400 | Offer | Offer no longer available |
| `NR4003` | 400 | Offer | Nurse already submitted an offer |
| `NR4004` | 400 | Offer | Offer expired |
| `NR5001` | 400 | Location | Location is required |
| `NR5002` | 400 | Location | Invalid coordinates |
| `NR5003` | 400 | Location | City is required |
| `NR5004` | 400 / 404 | Location | Address not found or not owned by patient |
| `NR6001` | 401 | Auth | Not authenticated |
| `NR6002` | 403 | Auth | Caller is not a patient |
| `NR6003` | 403 | Auth | Caller is not a nurse |
| `NR6004` | 404 | Auth | Nurse profile not found |
| `NR6005` | 403 | Auth | Nurse account not verified |

---

## 4. Push Notification Events (FCM)

All FCM messages are delivered as **data-only** (no `notification` block). Build the local notification from the data payload inside the app.

> All numeric values in FCM payloads are **strings** — always parse explicitly (`double.parse(...)`, `int.parse(...)`).

### 4.1 New Request Nearby → Nurse

Sent when a patient creates a request that is within the nurse's service area and matches a service in the nurse's profile.

```json
{
  "notification_type": "nurse_request_new",
  "request_id": "42",
  "service_title": "Wound Care",
  "patient_name": "Amina B.",
  "patient_offered_price": "750.00",
  "distance_km": "3.45",
  "city": "Algiers"
}
```

**Recipients:** All approved + available nurses within the lesser of `nurse.service_area_km` and **30 km**.

---

### 4.2 Nurse Offer Received → Patient

Sent each time a nurse submits an offer or counter-offer.

```json
{
  "notification_type": "NURSE_REQUEST_OFFER",
  "request_id": "42",
  "offer_id": "17"
}
```

For counter-offers: `"notification_type": "NURSE_REQUEST_COUNTER_OFFER"`.

---

### 4.3 Offer Accepted → Nurse

```json
{
  "notification_type": "NURSE_REQUEST_ACCEPTED",
  "request_id": "42"
}
```

---

### 4.4 Offer Declined → Nurse

```json
{
  "notification_type": "NURSE_REQUEST_OFFER_DECLINED",
  "request_id": "42",
  "offer_id": "17"
}
```

---

### 4.5 Service Started → Patient

```json
{
  "notification_type": "NURSE_REQUEST_IN_PROGRESS",
  "request_id": "42"
}
```

---

### 4.6 Service Completed → Patient

```json
{
  "notification_type": "NURSE_REQUEST_COMPLETED",
  "request_id": "42"
}
```

---

### 4.7 Request Cancelled → Relevant Party

```json
{
  "notification_type": "NURSE_REQUEST_CANCELLED",
  "request_id": "42"
}
```

---

### FCM Handling Summary

| `notification_type` | App | Action |
|---------------------|-----|--------|
| `nurse_request_new` | Nurse | Navigate to available requests list |
| `NURSE_REQUEST_OFFER` / `NURSE_REQUEST_COUNTER_OFFER` | Patient | Re-fetch request detail to refresh offer list |
| `NURSE_REQUEST_ACCEPTED` | Nurse | Navigate to accepted request detail |
| `NURSE_REQUEST_OFFER_DECLINED` | Nurse | Update UI to show offer was declined |
| `NURSE_REQUEST_IN_PROGRESS` | Patient | Show "Service in progress" screen |
| `NURSE_REQUEST_COMPLETED` | Patient | Show review screen |
| `NURSE_REQUEST_CANCELLED` | Both | Show cancellation info |

---

## 5. WebSocket Real-time Updates

Subscribe to WebSocket channels for live status updates without polling.

### Patient — subscribe to request updates
```
ws://<host>/ws/nurse-requests/<request_id>/
Headers: Authorization: Token <token>
```

Channel group: `request_<request_id>_updates`

### Nurse — subscribe to available requests
```
ws://<host>/ws/nurse-requests/available/
Headers: Authorization: Token <token>
```

Channel groups: `user_<id>_nurse_requests`, `city_<city>_requests`

### Incoming WebSocket Event Types

| `type` | Sent to | Meaning |
|--------|---------|---------|
| `nurse_request_new` | Nurses | New request available |
| `nurse_request_offer` | Patient | Nurse submitted an offer |
| `nurse_request_accepted` | Nurse | Patient accepted this nurse's offer |
| `nurse_request_in_progress` | Patient | Service started |
| `nurse_request_completed` | Patient | Service completed |
| `nurse_request_cancelled` | Both | Request cancelled |

> On any status-change WebSocket event, re-fetch the relevant endpoint to get the updated data object.

---

## 6. Services Catalog (Shared)

Both apps use this to browse available nursing services before creating a request or managing profile services.

### List all nursing services

```
GET /api/nurse-requests/services/
```

**Auth required:** Yes (any authenticated user)

**Response — `200 OK`**
```json
{
  "success": true,
  "count": 3,
  "results": [
    {
      "id": 1,
      "name": "Wound Care",
      "description": "Professional wound dressing and care",
      "base_price": "650.00",
      "estimated_duration": "00:45:00",
      "is_active": true,
      "icon": null,
      "currency": "DZD",
      "is_home_service": true,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ],
  "message": "Select a service to request a nurse"
}
```

---

### Get service detail

```
GET /api/nurse-requests/services/{id}/
```

**Response — `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Wound Care",
    "description": "Professional wound dressing and care",
    "base_price": "650.00",
    "estimated_duration": "00:45:00",
    "is_active": true,
    "icon": null,
    "currency": "DZD",
    "is_home_service": true,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  },
  "available_nurses_count": 4,
  "message": "4 nurses available for this service"
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR1001` | 404 | Service not found or not a nursing service |

---

---

# PATIENT APP ENDPOINTS

> All patient endpoints require a user with role `PATIENT`.
> HTTP `403 Forbidden` is returned (code `NR6002`) if the authenticated user is not a patient.

---

## 7.1 List My Requests

```
GET /api/nurse-requests/patient/nurse-requests/
```

**Query Parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `status` | `CREATED`, `SEARCHING`, `NURSE_RESPONDED`, `PATIENT_DECISION`, `ACCEPTED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` | Filter by exact status (uppercase) |
| `is_active` | `true` | Only requests that are not yet completed or cancelled |
| `is_history` | `true` | Only `COMPLETED` and `CANCELLED` requests |

Active statuses: `CREATED`, `SEARCHING`, `NURSE_RESPONDED`, `PATIENT_DECISION`, `ACCEPTED`, `IN_PROGRESS`
History statuses: `COMPLETED`, `CANCELLED`

> `is_active` and `is_history` are mutually exclusive. If both are sent, `is_active` takes precedence.

**Response — `200 OK`**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": 42,
      "service_name": "Wound Care",
      "patient_name": "Amina Benali",
      "status": "SEARCHING",
      "patient_offered_price": "750.00",
      "final_price": null,
      "city": "Algiers",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "offers_count": 2,
      "created_at": "2026-05-02T10:00:00Z",
      "updated_at": "2026-05-02T10:01:00Z"
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Request ID |
| `service_name` | string | Name of the nursing service |
| `patient_name` | string | Patient's display name |
| `status` | string | Current request status |
| `patient_offered_price` | decimal string | Price the patient offered |
| `final_price` | decimal string \| null | Agreed final price — set only after offer is accepted |
| `city` | string | Service location city |
| `latitude` / `longitude` | decimal string | Service location coordinates |
| `offers_count` | int | Number of nurse offers received |
| `created_at` / `updated_at` | ISO 8601 | Timestamps |

---

## 7.2 Create a Request (Manual Location)

```
POST /api/nurse-requests/patient/nurse-requests/
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| `service` | integer | **yes** | Must be an active nursing service (`service_type=NURSE`, `is_on_demand=true`) |
| `patient_offered_price` | decimal string | **yes** | Must be ≥ service base price |
| `latitude` | decimal string | **yes** | Valid latitude coordinate |
| `longitude` | decimal string | **yes** | Valid longitude coordinate |
| `city` | string | **yes** | City name (used for nurse filtering and grouping) |
| `address_line` | string | no | Apartment / floor / street detail |
| `notes` | string | no | Additional notes for the nurse |

```json
{
  "service": 1,
  "patient_offered_price": "750.00",
  "latitude": "36.737232",
  "longitude": "3.086472",
  "city": "Algiers",
  "address_line": "Apt 3B, Rue Didouche Mourad",
  "notes": "Please bring sterile gloves"
}
```

**Success — `201 Created`**
```json
{
  "success": true,
  "message": "Request created successfully. Searching for available nurses...",
  "data": {
    "id": 42,
    "patient_user": 10,
    "patient_record": null,
    "patient_name": "Amina Benali",
    "service": {
      "id": 1,
      "name": "Wound Care",
      "description": "Professional wound dressing and care",
      "base_price": "650.00",
      "estimated_duration": "00:45:00",
      "is_active": true,
      "icon": null,
      "currency": "DZD",
      "is_home_service": true
    },
    "accepted_nurse": null,
    "accepted_nurse_name": null,
    "accepted_nurse_profile": null,
    "base_price": "650.00",
    "patient_offered_price": "750.00",
    "final_price": null,
    "address": null,
    "address_details": null,
    "latitude": "36.737232",
    "longitude": "3.086472",
    "city": "Algiers",
    "state": "",
    "address_line": "Apt 3B, Rue Didouche Mourad",
    "country": "Algeria",
    "status": "SEARCHING",
    "notes": "Please bring sterile gloves",
    "offers": [],
    "created_at": "2026-05-02T10:00:00Z",
    "updated_at": "2026-05-02T10:00:00Z",
    "accepted_at": null,
    "started_at": null,
    "completed_at": null,
    "cancelled_at": null,
    "cancellation_reason": "",
    "can_leave_review": false
  }
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR1001` | 400 | `service` ID does not exist |
| `NR1003` | 400 | Service exists but is not a nursing service |
| `NR1004` | 400 | Service is not available for on-demand requests |
| `NR2001` | 400 | `patient_offered_price` is below the service base price |
| `NR5002` | 400 | `latitude` or `longitude` is invalid |
| `NR5003` | 400 | `city` is missing |

> After creation, FCM notifications are automatically sent to all nearby eligible nurses.

---

## 7.3 Create Using a Saved Address

Creates a request using coordinates from a previously saved address.

```
POST /api/nurse-requests/patient/nurse-requests/use-saved-address/
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `service` | integer | **yes** | Same validation as manual create |
| `patient_offered_price` | decimal string | **yes** | Must be ≥ service base price |
| `address_id` | integer | **yes** | ID from the saved addresses list |
| `notes` | string | no | Additional notes for the nurse |

```json
{
  "service": 1,
  "patient_offered_price": "750.00",
  "address_id": 5,
  "notes": "Ring bell twice"
}
```

**Success — `201 Created`** — same shape as [7.2 Create response](#72-create-a-request-manual-location)

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR5004` | 400 | `address_id` field is missing |
| `NR5004` | 404 | Address not found or does not belong to this patient |
| `NR5002` | 400 | The saved address has no coordinates (use only addresses where `has_coordinates: true`) |

---

## 7.4 Get Saved Addresses

Returns the patient's saved addresses for quick selection.

```
GET /api/nurse-requests/patient/nurse-requests/saved-addresses/
```

**Response — `200 OK`**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": 5,
      "street": "Rue Didouche Mourad",
      "city": "Algiers",
      "state": "Algiers",
      "zip_code": "16000",
      "country": "Algeria",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "is_primary": true,
      "address_type": "HOME",
      "full_address": "Rue Didouche Mourad, Algiers, Algiers, Algeria",
      "has_coordinates": true
    }
  ],
  "message": "Select a saved address or choose location from map"
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Address ID — used in `address_id` when creating a request |
| `full_address` | string | Formatted display string |
| `has_coordinates` | boolean | `true` if the address has valid `latitude` and `longitude` |
| `is_primary` | boolean | Primary address is listed first |
| `address_type` | string | `HOME`, `WORK`, `CLINIC`, etc. |

> Only use addresses where `has_coordinates: true`. Addresses without coordinates cannot be used for nurse requests.

---

## 7.5 Get Request Detail

```
GET /api/nurse-requests/patient/nurse-requests/{id}/
```

**Response — `200 OK`** — full request object

```json
{
  "id": 42,
  "patient_user": 10,
  "patient_record": null,
  "patient_name": "Amina Benali",
  "service": { ... },
  "accepted_nurse": 3,
  "accepted_nurse_name": "Karim Zerrouk",
  "accepted_nurse_profile": {
    "first_name": "Karim",
    "last_name": "Zerrouk",
    "phone_number": "+213 555 000111",
    "profile_image": "https://example.com/media/...",
    "average_rating": 4.7,
    "review_count": 23,
    "rating_distribution": { "1": 0, "2": 1, "3": 2, "4": 8, "5": 12 },
    "recent_reviews": [
      {
        "id": "abc123",
        "rating": 5,
        "text": "Excellent care",
        "created_at": "2026-04-20T14:00:00Z",
        "has_response": false
      }
    ]
  },
  "base_price": "650.00",
  "patient_offered_price": "750.00",
  "final_price": "750.00",
  "address": null,
  "address_details": null,
  "latitude": "36.737232",
  "longitude": "3.086472",
  "city": "Algiers",
  "state": "",
  "address_line": "Apt 3B",
  "country": "Algeria",
  "status": "ACCEPTED",
  "notes": "Please bring gloves",
  "offers": [
    {
      "id": 17,
      "nurse_id": 3,
      "nurse_name": "Karim Zerrouk",
      "nurse_rating": 4.7,
      "nurse_review_count": 23,
      "nurse_profile_image": "https://example.com/media/nurses/profiles/photo.jpg",
      "nurse_years_experience": 5,
      "nurse_completed_services": 48,
      "nurse_biography": "Specialized in wound care and post-op follow-up...",
      "nurse_is_verified": true,
      "offered_price": "750.00",
      "status": "ACCEPTED",
      "estimated_arrival_time": "00:20:00",
      "distance_km": "2.30",
      "notes": "I can be there in 20 minutes",
      "created_at": "2026-05-02T10:05:00Z",
      "responded_at": "2026-05-02T10:05:00Z"
    }
  ],
  "created_at": "2026-05-02T10:00:00Z",
  "updated_at": "2026-05-02T10:06:00Z",
  "accepted_at": "2026-05-02T10:06:00Z",
  "started_at": null,
  "completed_at": null,
  "cancelled_at": null,
  "cancellation_reason": "",
  "can_leave_review": false
}
```

**Key fields:**

| Field | Description |
|-------|-------------|
| `offers` | All nurse responses. Each includes nurse info, rating, offer price, estimated arrival |
| `can_leave_review` | `true` when status is `COMPLETED` and the patient has not reviewed the nurse yet |
| `accepted_nurse_profile` | Populated once an offer is accepted — includes rating, recent reviews |
| `final_price` | Set once offer is accepted |

**Offer status values:** `PENDING`, `ACCEPTED`, `REJECTED`, `COUNTER_OFFERED`, `EXPIRED`

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found or does not belong to this patient |

---

## 7.6 Accept a Nurse Offer

```
POST /api/nurse-requests/patient/nurse-requests/{id}/accept/
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required |
|-------|------|----------|
| `offer_id` | integer | **yes** |

```json
{
  "offer_id": 17
}
```

**Verifications performed (in order):**
1. Request exists and belongs to this patient
2. Request is not `CANCELLED`, `ACCEPTED`, or `COMPLETED`
3. Request status is `NURSE_RESPONDED` or `PATIENT_DECISION` (nurses must have responded first)
4. `offer_id` exists for this request and its status is `PENDING`

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Offer accepted! The nurse will be on their way."
}
```

The response `data` is the full updated request object. Status becomes `ACCEPTED`. All other offers for this request are automatically rejected. The accepted nurse receives an FCM notification.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Not the request owner |
| `NR3004` | 400 | Request already cancelled |
| `NR3005` | 400 | Request already accepted |
| `NR3006` | 400 | Request already completed |
| `NR3003` | 400 | No nurses have responded yet (status must be `NURSE_RESPONDED` or `PATIENT_DECISION`) |
| `NR4001` | 400 | Invalid `offer_id` |
| `NR4002` | 400 | Offer is no longer available (already rejected/expired) |

---

## 7.7 Decline a Nurse Offer

Declines a single offer **without cancelling the request**. The patient can still accept other pending offers.

```
POST /api/nurse-requests/patient/nurse-requests/{id}/decline_offer/
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `offer_id` | integer | **yes** | |
| `reason` | string | no | Optional reason for the nurse |

```json
{
  "offer_id": 17,
  "reason": "Too expensive"
}
```

**Verifications performed:**
1. Request exists and belongs to this patient
2. Request is not `ACCEPTED`, `CANCELLED`, or `COMPLETED`
3. `offer_id` exists for this request
4. Offer status is `PENDING` or `COUNTER_OFFERED`

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Offer declined. You can continue reviewing other offers."
}
```

The declined offer's status becomes `REJECTED`. The nurse receives a decline notification.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Not the request owner |
| `NR3005` | 400 | Request already has an accepted offer |
| `NR3004` | 400 | Request already cancelled |
| `NR3006` | 400 | Request already completed |
| `NR4001` | 400 | `offer_id` missing |
| `NR4001` | 404 | Offer not found for this request |
| `NR4002` | 400 | Offer is no longer in `PENDING` or `COUNTER_OFFERED` state |

---

## 7.8 Cancel a Request

```
POST /api/nurse-requests/patient/nurse-requests/{id}/cancel/
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required |
|-------|------|----------|
| `cancellation_reason` | string | no |

```json
{
  "cancellation_reason": "Changed my mind"
}
```

**Verifications performed:**
1. Request exists and belongs to this patient
2. Request is not already `CANCELLED`
3. Request is not `COMPLETED`

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Request cancelled successfully"
}
```

Status becomes `CANCELLED`. If a nurse had been accepted, they receive a cancellation FCM notification.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Not the request owner |
| `NR3004` | 400 | Request already cancelled |
| `NR3006` | 400 | Cannot cancel a completed request |

---

## 7.9 View Nurse Profile Before Accepting

Shows the full profile of a nurse who made an offer on this request. Use this before showing the "Accept" button.

```
GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-profile/{nurse_id}/
```

`nurse_id` is the `nurse_id` field from the offer object in the request detail response.

**Verifications performed:**
1. Request exists and belongs to this patient
2. The nurse (`nurse_id`) has made an offer on this specific request
3. Nurse profile exists

**Response — `200 OK`**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "first_name": "Karim",
    "last_name": "Zerrouk",
    "full_name": "Karim Zerrouk",
    "profile_image": "https://example.com/media/nurses/profiles/photo.jpg",
    "biography": "Specialized in wound care and post-op follow-up...",
    "license_number": "ALG-2019-1234",
    "certification": "Registered Nurse",
    "years_of_experience": 5,
    "is_verified": true,
    "is_available": true,
    "is_home_service_available": true,
    "average_rating": 4.7,
    "review_count": 23,
    "rating_distribution": { "1": 0, "2": 1, "3": 2, "4": 8, "5": 12 },
    "recent_reviews": [
      {
        "id": "abc123",
        "rating": 5,
        "text": "Excellent care, very professional",
        "created_at": "2026-04-20T14:00:00Z",
        "has_response": false
      }
    ],
    "completed_services_count": 48,
    "services_offered": [
      {
        "id": 1,
        "title": "Wound Care",
        "price": "750.00 DZD",
        "duration_minutes": 45
      }
    ]
  },
  "offer": {
    "id": 17,
    "offered_price": "750.00",
    "status": "PENDING",
    "estimated_arrival_time": "00:20:00",
    "notes": "I can be there in 20 minutes"
  },
  "message": "Nurse profile retrieved successfully"
}
```

**Profile fields:**

| Field | Description |
|-------|-------------|
| `is_verified` | Whether the nurse's credentials were verified by Medilink |
| `is_home_service_available` | Whether the nurse offers home visits |
| `completed_services_count` | Total completed nurse requests via this platform |
| `average_rating` | Aggregate star rating (0.0–5.0) |
| `rating_distribution` | Breakdown by star count |
| `recent_reviews` | Up to 5 most recent reviews |
| `services_offered` | Services currently in the nurse's profile with effective prices |

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR4001` | 404 | This nurse has not made an offer on this request |
| `NR6004` | 404 | Nurse profile not found |

---

## 7.10 View Nurse Service History

Shows the nurse's last 10 completed services (anonymized). Use this alongside the profile to assess reliability.

```
GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-history/{nurse_id}/
```

**Verifications performed:**
1. Request exists and belongs to this patient
2. The nurse (`nurse_id`) has made an offer on this request

**Response — `200 OK`**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 38,
      "service_title": "Wound Care",
      "patient_name": "A***i",
      "completed_at": "2026-04-28T15:30:00Z",
      "final_price": "750.00",
      "review": {
        "rating": 5,
        "text": "Very professional"
      }
    }
  ],
  "message": "Nurse service history retrieved"
}
```

> Patient names are anonymized for privacy. `review` is `null` if no review was left for that service.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR4001` | 404 | This nurse has not made an offer on this request |

---

## 7.11 Start Service

Marks a request as `IN_PROGRESS`. Typically called by the nurse app (see [8.7](#87-accept-at-patient-price)), but this endpoint is also accessible to the patient/admin if needed.

```
POST /api/nurse-requests/patient/nurse-requests/{id}/start/
```

No request body required.

**Verifications performed:**
1. Request exists
2. Request is in `ACCEPTED` status

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Service started"
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR3003` | 400 | Request is not in `ACCEPTED` status |

---

## 7.12 Complete Service

Marks a request as `COMPLETED`. Typically called by the nurse app, but accessible to the patient/admin as well.

```
POST /api/nurse-requests/patient/nurse-requests/{id}/complete/
```

No request body required.

**Verifications performed:**
1. Request exists
2. Request is in `IN_PROGRESS` status

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Service completed successfully"
}
```

After completion, `can_leave_review` becomes `true` in the request detail.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR3003` | 400 | Request is not in `IN_PROGRESS` status |

---

---

# NURSE APP ENDPOINTS

> All nurse endpoints require a user with role `PROVIDER` and `provider_type: NURSE`.
> HTTP `403 Forbidden` is returned (code `NR6003`) if the authenticated user is not a nurse.
> An additional check for an existing `Nurse` profile record is applied to most endpoints (code `NR6004`).

---

## 8.1 List My Services

Returns services in the nurse's profile and all services available to add.

```
GET /api/nurse-requests/nurse/my-services/
```

**Response — `200 OK`**
```json
{
  "success": true,
  "my_services": [
    {
      "id": 1,
      "service_id": 1,
      "title": "Wound Care",
      "description": "Professional wound dressing and care",
      "base_price": "650.00",
      "custom_price": "750.00",
      "effective_price": "750.00 DZD",
      "duration_minutes": 45,
      "is_available": true,
      "is_on_demand": true,
      "created_at": "2026-05-01T09:00:00Z"
    }
  ],
  "my_services_count": 1,
  "available_to_add": [
    {
      "id": 2,
      "name": "IV Therapy",
      "description": "...",
      "base_price": "800.00",
      "estimated_duration": "01:00:00",
      "is_active": true,
      "currency": "DZD",
      "is_home_service": true
    }
  ],
  "available_to_add_count": 5,
  "message": "Add services to receive on-demand requests for those services"
}
```

**Fields in `my_services`:**

| Field | Description |
|-------|-------------|
| `custom_price` | Nurse-specific price override. `null` if not set |
| `effective_price` | `custom_price` if set, otherwise `base_price` — formatted with currency |
| `is_available` | Whether the nurse is currently accepting requests for this service |

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |

---

## 8.2 Add a Service

Adds a nursing service to the nurse's profile so they start receiving requests for it.

```
POST /api/nurse-requests/nurse/my-services/add/
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `service_id` | integer | **yes** | Must be an active nursing on-demand service |
| `custom_price` | decimal string | no | If omitted, base price is used |

```json
{
  "service_id": 2,
  "custom_price": "900.00"
}
```

**Verifications performed:**
1. Nurse profile exists
2. `service_id` is provided
3. Service exists
4. Service `service_type == NURSE`
5. Service `is_on_demand == true`
6. Service `is_active == true`
7. Service is not already in the nurse's profile

**Success — `201 Created`**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "service_id": 2,
    "title": "IV Therapy",
    "base_price": "800.00",
    "custom_price": "900.00",
    "effective_price": "900.00 DZD",
    "duration_minutes": 60,
    "is_available": true,
    "is_on_demand": true,
    "created_at": "2026-05-03T08:00:00Z"
  },
  "message": "Successfully added \"IV Therapy\" to your profile. You will now receive requests for this service."
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR1001` | 400 | `service_id` missing |
| `NR1001` | 404 | Service not found |
| `NR1003` | 400 | Not a nursing service |
| `NR1004` | 400 | Not available for on-demand |
| `NR1002` | 400 | Service inactive |
| `NR1005` | 400 | Already in nurse's profile |

---

## 8.3 Remove a Service

Removes a service from the nurse's profile. The nurse will no longer receive requests for this service.

```
DELETE /api/nurse-requests/nurse/my-services/{service_id}/remove/
```

`service_id` is the **service's ID** (not the profile service record ID).

**Verifications performed:**
1. Nurse profile exists
2. Service is currently in the nurse's profile

**Success — `200 OK`**
```json
{
  "success": true,
  "message": "Removed \"IV Therapy\" from your profile. You will no longer receive requests for this service."
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR1006` | 404 | Service is not in the nurse's profile |

---

## 8.4 Update Availability / Price

Toggle availability or change the custom price for a service already in the profile.

```
PATCH /api/nurse-requests/nurse/my-services/{service_id}/availability/
Content-Type: application/json
```

`service_id` is the **service's ID**.

**Request Body:** (both fields are optional — send only what changes)

| Field | Type | Description |
|-------|------|-------------|
| `is_available` | boolean | `true` = accepting requests; `false` = paused |
| `custom_price` | decimal string | Override price for this service |

```json
{
  "is_available": false
}
```

**Verifications performed:**
1. Nurse profile exists
2. Service is in the nurse's profile

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Service is now unavailable"
}
```

> Setting `is_available: false` prevents new requests from appearing in the nurse's feed for that service but does not affect in-progress requests.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR1006` | 404 | Service is not in the nurse's profile |

---

## 8.5 List Available Requests

Shows requests that match the nurse's profile and location.

**A request is visible to a nurse if ALL of the following are true:**
- Status is `SEARCHING` or `NURSE_RESPONDED`
- Request's service is in the nurse's profile and `is_available: true`
- Nurse has NOT already submitted an offer for it
- Request location is within the nurse's `service_area_km` radius (if the nurse has a `WORK`/`CLINIC` address with coordinates)

```
GET /api/nurse-requests/nurse/available-requests/
```

**Query Parameter:**

| Parameter | Description |
|-----------|-------------|
| `city` | Case-insensitive partial match on request city |

**Response — `200 OK`**
```json
{
  "success": true,
  "count": 3,
  "results": [
    {
      "id": 42,
      "service_id": 1,
      "service_name": "Wound Care",
      "service_description": "Professional wound dressing and care",
      "patient_name": "Amina B.",
      "patient_offered_price": "750.00",
      "base_price": "650.00",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "city": "Algiers",
      "address_line": "Apt 3B, Rue Didouche Mourad",
      "status": "SEARCHING",
      "created_at": "2026-05-02T10:00:00Z",
      "my_offer": null,
      "patient_rating": 4.7,
      "patient_review_count": 12,
      "patient_clinical_summary": {
        "blood_type": "O+",
        "known_allergies": "Penicillin",
        "chronic_conditions": "Type 2 Diabetes"
      }
    }
  ],
  "your_active_services_count": 2,
  "message": "Showing requests for your 2 active service(s)"
}
```

**Key fields:**

| Field | Description |
|-------|-------------|
| `my_offer` | `null` if no offer submitted. Contains the offer object if the nurse already responded (only visible after page reload — newly submitted offers need a re-fetch) |
| `patient_name` | Partially masked for privacy (e.g., `"Amina B."`) |
| `patient_rating` | Aggregate rating from past nurse reviews. `null` if no reviews |
| `patient_review_count` | Total reviews the patient has received |
| `patient_clinical_summary` | Blood type, allergies, chronic conditions. `null` if patient has no record |

**Warning when no services in profile — `200 OK`**
```json
{
  "success": true,
  "count": 0,
  "results": [],
  "warning": {
    "code": "NR1006",
    "message": "You have no active services in your profile. Add services to start receiving requests.",
    "action": "Go to /api/nurse-requests/nurse/my-services/ to add services"
  }
}
```

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |

---

## 8.6 Get Request Detail (Nurse View)

```
GET /api/nurse-requests/nurse/available-requests/{id}/
```

Returns the same shape as a single result from [8.5](#85-list-available-requests), with `my_offer` populated if the nurse has already responded.

**Verifications performed:**
1. Nurse profile exists
2. Request exists
3. Nurse offers the requested service and is available for it

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR3001` | 404 | Request not found or nurse does not offer this service |
| `NR3007` | 403 | Nurse does not offer this service (service not in profile or `is_available: false`) |

---

## 8.7 Accept at Patient Price

Nurse agrees to provide the service at the price the patient offered.

```
POST /api/nurse-requests/nurse/available-requests/{id}/accept/
Content-Type: application/json
```

**Request Body:** (all fields optional)

| Field | Type | Description |
|-------|------|-------------|
| `estimated_arrival_time` | string `HH:MM:SS` | Estimated travel time |
| `notes` | string | Message visible to the patient |
| `distance_km` | decimal | Distance from nurse to patient in km |

```json
{
  "estimated_arrival_time": "00:20:00",
  "notes": "I'll be there soon, please have the supplies ready.",
  "distance_km": 2.3
}
```

**Verifications performed:**
1. Nurse profile exists
2. Request exists
3. Nurse offers this service and is available
4. Nurse has NOT already submitted an offer (`NR4003`)
5. Request is in `SEARCHING` or `NURSE_RESPONDED` status (`NR3003`)

**Success — `201 Created`**
```json
{
  "success": true,
  "message": "Request accepted successfully",
  "offer_id": 17,
  "offered_price": "750.00"
}
```

The offer is created with `status: PENDING` and `offered_price = patient_offered_price`. The patient receives an FCM notification.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR6004` | 404 | Nurse profile not found |
| `NR3007` | 403 | Nurse does not offer this service |
| `NR4003` | 400 | Nurse already submitted an offer for this request |
| `NR3003` | 400 | Request no longer available (status changed) |
| `NR4002` | 400 | Service error during offer creation |

---

## 8.8 Counter-Offer

Nurse proposes a price higher than what the patient offered.

```
POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/
Content-Type: application/json
```

**Request Body:**

| Field | Type | Required | Validation |
|-------|------|----------|-----------|
| `offered_price` | decimal | **yes** | Must be ≥ `patient_offered_price` AND ≥ `base_price` |
| `estimated_arrival_time` | string `HH:MM:SS` | no | |
| `notes` | string | no | Reason for the higher price |
| `distance_km` | decimal | no | |

```json
{
  "offered_price": "900.00",
  "estimated_arrival_time": "00:30:00",
  "notes": "Traffic is heavy in this area",
  "distance_km": 8.5
}
```

**Verifications performed:**
1. Same as [8.7 Accept](#87-accept-at-patient-price) (nurse profile, service in profile, not already offered, request status)
2. `offered_price` ≥ `patient_offered_price`
3. `offered_price` ≥ `base_price`

**Success — `201 Created`**
```json
{
  "success": true,
  "message": "Counter offer submitted successfully",
  "offer_id": 18,
  "offered_price": "900.00"
}
```

The offer is created with `status: COUNTER_OFFERED`. The patient receives an FCM counter-offer notification.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR6004` | 404 | Nurse profile not found |
| `NR3007` | 403 | Nurse does not offer this service |
| `NR4003` | 400 | Nurse already submitted an offer |
| `NR3003` | 400 | Request no longer available |
| `NR2002` | 400 | `offered_price` is below `patient_offered_price` |

---

## 8.9 Reject a Request

Nurse dismisses a request without making an offer. The request is not cancelled — other nurses can still respond.

```
POST /api/nurse-requests/nurse/available-requests/{id}/reject/
Content-Type: application/json
```

**Request Body:** (optional)

| Field | Type |
|-------|------|
| `reason` | string |

```json
{
  "reason": "Too far from my current location"
}
```

**Verifications performed:**
1. Nurse profile exists
2. Request exists

**Success — `200 OK`**
```json
{
  "success": true,
  "message": "Request rejected"
}
```

Rejection is logged in `RequestHistory`. The request will no longer appear in the nurse's available list.

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |
| `NR3001` | 404 | Request not found |

---

## 8.10 My Offers (History)

All requests where this nurse submitted any offer (regardless of outcome).

```
GET /api/nurse-requests/nurse/my-offers/
```

**Query Parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `status` | `SEARCHING`, `ACCEPTED`, `COMPLETED`, `CANCELLED`, etc. | Filter by request status |
| `offer_status` | `PENDING`, `ACCEPTED`, `REJECTED`, `COUNTER_OFFERED`, `EXPIRED` | Filter by this nurse's offer status on each request |
| `is_active` | `true` | Only requests that are not yet completed or cancelled |
| `is_history` | `true` | Only `COMPLETED` and `CANCELLED` requests |

**Response — `200 OK`**
```json
{
  "success": true,
  "count": 5,
  "results": [ ... ],
  "stats": {
    "total_offers": 5,
    "pending": 1,
    "accepted": 3
  }
}
```

Each result is a full request object (same shape as [7.5 Get request detail](#75-get-request-detail)).

**Stats fields:**

| Field | Description |
|-------|-------------|
| `total_offers` | Total requests where nurse submitted an offer |
| `pending` | Requests with this nurse's offer still in `PENDING` state |
| `accepted` | Requests where this nurse was chosen as the accepted nurse |

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |

---

## 8.11 Request History

Only requests where this nurse was the **accepted nurse**.

```
GET /api/nurse-requests/nurse/request-history/
```

**Query Parameters:**

| Parameter | Format | Description |
|-----------|--------|-------------|
| `status` | `ACCEPTED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` | Filter by request status |
| `date_from` | `YYYY-MM-DD` | Filter by `completed_at` ≥ date |
| `date_to` | `YYYY-MM-DD` | Filter by `completed_at` ≤ date |
| `patient_name` | string | Partial name search (matches first or last name) |
| `ordering` | `-completed_at` (default), `final_price`, `-final_price` | Sort order |
| `page` | integer | Pagination page number |
| `page_size` | integer | Results per page (default 20) |

> `date_from` / `date_to` filter on `completed_at`. Non-completed requests won't appear in date-filtered results.

**Response — `200 OK`**
```json
{
  "success": true,
  "count": 12,
  "results": [
    {
      "id": 40,
      "service_name": "Wound Care",
      "patient_name": "A. B.",
      "patient_initials": "AB",
      "status": "COMPLETED",
      "status_display": "Completed",
      "final_price": "750.00",
      "base_price": "650.00",
      "accepted_at": "2026-05-01T11:00:00Z",
      "started_at": "2026-05-01T11:25:00Z",
      "completed_at": "2026-05-01T12:10:00Z",
      "cancelled_at": null,
      "cancellation_reason": "",
      "city": "Algiers",
      "can_leave_review": true,
      "nurse_review": null,
      "patient_review": {
        "id": "xyz",
        "rating": 5,
        "text": "Great nurse, very professional",
        "created_at": "2026-05-01T12:30:00Z"
      },
      "patient_overall_rating": 4.2,
      "patient_total_reviews": 8,
      "created_at": "2026-05-01T10:00:00Z",
      "updated_at": "2026-05-01T12:10:00Z"
    }
  ],
  "stats": {
    "total_accepted": 2,
    "total_in_progress": 1,
    "total_completed": 12,
    "total_cancelled": 1
  }
}
```

**Key fields:**

| Field | Description |
|-------|-------------|
| `patient_name` | Anonymized (e.g., `"A. B."`) for privacy |
| `patient_initials` | Two-letter initials for avatar display |
| `can_leave_review` | `true` when completed and nurse has not reviewed the patient yet |
| `nurse_review` | Review this nurse submitted for the patient on this request |
| `patient_review` | Review the patient submitted for this nurse on this request |
| `patient_overall_rating` | Patient's aggregate rating from all nurse reviews (not just this request) |
| `patient_total_reviews` | Total number of reviews the patient has ever received |

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR6004` | 404 | Nurse profile not found |

---

### Get History Detail

```
GET /api/nurse-requests/nurse/request-history/{id}/
```

**Verifications performed:**
1. Request exists
2. Nurse was the `accepted_nurse` on this request

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Nurse was not the accepted nurse on this request |

---

## 8.12 View Patient Medical Folder

View the patient's non-confidential medical records for an accepted/active/completed service.

```
GET /api/nurse-requests/nurse/request-history/{id}/patient-folder/
```

**Auth:** Nurse only. Must be the `accepted_nurse` on the request.

**Status requirement:** Request must be `ACCEPTED`, `IN_PROGRESS`, or `COMPLETED`.

**Privacy:**
- Confidential records (`is_confidential=true`) are **never** returned
- Every access is logged in `MedicalRecordAccessLog` with the nurse's user, IP address, and timestamp

**Verifications performed:**
1. Request exists
2. Nurse is the `accepted_nurse` on this request
3. Request status is `ACCEPTED`, `IN_PROGRESS`, or `COMPLETED`

**Response — `200 OK`**
```json
{
  "success": true,
  "data": {
    "request_id": 42,
    "access_note": "Confidential records are excluded. Access is logged.",
    "patient_clinical_info": {
      "blood_type": "O+",
      "known_allergies": "Penicillin",
      "chronic_conditions": "Type 2 Diabetes",
      "current_medications": "Metformin 500mg",
      "emergency_contact_name": "Karim Benali",
      "emergency_contact_phone": "+213 555 123456"
    },
    "summary": {
      "total_records": 8,
      "active_allergies": 1,
      "critical_or_high": 2,
      "recent_30_days": 3,
      "record_types": {
        "DIAGNOSIS": 3,
        "PRESCRIPTION": 2,
        "ALLERGY": 1,
        "LAB_RESULT": 2
      }
    },
    "medical_records": {
      "timeline": [ ... ],
      "by_type": {
        "DIAGNOSIS": [ ... ],
        "PRESCRIPTION": [ ... ],
        "ALLERGY": [ ... ],
        "LAB_RESULT": [ ... ]
      },
      "active_allergies": [ ... ],
      "critical_or_high": [ ... ],
      "recent_30_days": [ ... ]
    }
  }
}
```

**Response structure:**

| Section | Description |
|---------|-------------|
| `patient_clinical_info` | Quick-access clinical demographics from the patient's record |
| `summary` | Counts by type and severity for fast triage |
| `medical_records.timeline` | All non-confidential records ordered by `record_date` desc |
| `medical_records.by_type` | Same records grouped by `record_type` |
| `medical_records.active_allergies` | Only records with `record_type=ALLERGY` |
| `medical_records.critical_or_high` | Records with `severity_level` in `CRITICAL`, `HIGH` |
| `medical_records.recent_30_days` | Records from the last 30 days |

**Errors:**

| Code | HTTP | Trigger |
|------|------|---------|
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Nurse is not the accepted nurse on this request |
| `NR3003` | 400 | Request status is not `ACCEPTED`, `IN_PROGRESS`, or `COMPLETED` |
| `NR6004` | 404 | Nurse profile not found |

---

---

## 9. Status Flow Diagram

```
Patient creates request
        │
        ▼
    SEARCHING ──────────────────────────────────────► CANCELLED (patient cancels)
        │
        │ (first nurse submits offer)
        ▼
 NURSE_RESPONDED ────────────────────────────────────► CANCELLED (patient cancels)
        │
        │ (patient accepts one offer)
        ▼
    ACCEPTED ───────────────────────────────────────► CANCELLED (patient cancels)
        │
        │ (nurse marks service started)
        ▼
  IN_PROGRESS
        │
        │ (nurse marks service completed)
        ▼
   COMPLETED ──► patient can leave review for nurse
              ──► nurse can leave review for patient
```

**Status reference:**

| Status | Patient UI | Nurse UI |
|--------|------------|---------|
| `SEARCHING` | "Looking for nurses…" spinner | Request appears in available list |
| `NURSE_RESPONDED` | Offer list, prompt to accept/decline | Offer submitted — awaiting patient |
| `PATIENT_DECISION` | Multiple offers visible | Awaiting patient decision |
| `ACCEPTED` | Nurse confirmed — show name, ETA, contact | Navigate to patient — tap "Start" |
| `IN_PROGRESS` | Service underway | Show "Complete" button |
| `COMPLETED` | Rate and review screen | History entry — `can_leave_review: true` |
| `CANCELLED` | Show cancellation reason | Offer removed from view |

**State transition rules:**

| From | To | Who triggers | Endpoint |
|------|----|-------------|----------|
| `CREATED` | `SEARCHING` | System | Automatic on creation |
| `SEARCHING` | `NURSE_RESPONDED` | System | Automatic when first offer arrives |
| `NURSE_RESPONDED` | `ACCEPTED` | Patient | `POST .../accept/` |
| `ACCEPTED` | `IN_PROGRESS` | Nurse/Patient | `POST .../start/` |
| `IN_PROGRESS` | `COMPLETED` | Nurse/Patient | `POST .../complete/` |
| Any active | `CANCELLED` | Patient | `POST .../cancel/` |

---

## 10. Flutter Implementation Checklist

### Patient App

- [ ] Fetch services catalog on the service selection screen (`GET /services/`)
- [ ] Display `base_price` as minimum — patient cannot offer less
- [ ] Use device GPS or map picker to fill `latitude`, `longitude`, `city`
- [ ] Offer a "Use saved address" flow: call `GET .../saved-addresses/`, filter for `has_coordinates: true`
- [ ] Register FCM token before showing any nurse request screens
- [ ] Subscribe to WebSocket `request_<id>_updates` after creating a request for live updates
- [ ] On FCM `NURSE_REQUEST_OFFER` / `NURSE_REQUEST_COUNTER_OFFER`: re-fetch request detail to refresh offer list
- [ ] In each offer card show: nurse name, photo, rating, years experience, distance, arrival time, price
- [ ] Distinguish `PENDING` offers (accept at this price) from `COUNTER_OFFERED` ones (higher price)
- [ ] Tapping a nurse card → call `GET .../nurse-profile/{nurse_id}/` and show full profile + history (`GET .../nurse-history/{nurse_id}/`) before showing accept button
- [ ] Call `POST .../accept/` with the selected `offer_id`
- [ ] After accepting, navigate to an "On the way" screen (status `ACCEPTED`) — show accepted nurse name, photo, ETA
- [ ] On FCM `NURSE_REQUEST_IN_PROGRESS`: show "Service in progress" screen
- [ ] On FCM `NURSE_REQUEST_COMPLETED`: show review screen (`can_leave_review: true`)
- [ ] Handle decline flow: `POST .../decline_offer/` — stays on offer list, other offers still visible
- [ ] Allow cancel at any active status: `POST .../cancel/`

### Nurse App

- [ ] On first launch after login: check `GET /nurse/my-services/` — if `my_services_count == 0`, prompt to add services
- [ ] Register FCM token so the server can send `nurse_request_new` notifications
- [ ] Ensure a primary `WORK` or `CLINIC` address with valid coordinates is saved — needed for distance-based filtering
- [ ] On FCM `nurse_request_new`: navigate to available requests list or show a banner
- [ ] Refresh available requests list when app foregrounds or on pull-to-refresh
- [ ] Handle the `warning` key in the available requests response (no services case)
- [ ] In each available request card, show: service name, offered price, distance, city, patient rating, clinical summary (blood type, allergies)
- [ ] Show "Accept at patient price" and "Counter-offer" buttons
- [ ] When submitting counter-offer, validate locally that `offered_price >= patient_offered_price`
- [ ] On FCM `NURSE_REQUEST_ACCEPTED`: navigate to the accepted request detail — show patient address
- [ ] Show "Start service" button when status is `ACCEPTED` → `POST .../start/`
- [ ] Show "Complete service" button when status is `IN_PROGRESS` → `POST .../complete/`
- [ ] During `ACCEPTED` or `IN_PROGRESS`, offer access to patient medical folder: `GET /nurse/request-history/{id}/patient-folder/`
- [ ] Request history (`/nurse/request-history/`) shows anonymized patient names — this is intentional
- [ ] `can_leave_review: true` in history means nurse can review the patient via the reviews API
- [ ] `patient_overall_rating` and `patient_total_reviews` are visible per history entry
- [ ] Toggle service availability from the services management screen (`PATCH .../availability/`)

---

## 11. Field-Level Validation Summary

### Patient offering price
- `patient_offered_price` ≥ `service.base_price`
- Error: `NR2001` — "Offered price ({amount} DZD) cannot be lower than base price ({base} DZD)"

### Nurse counter-offer price
- `offered_price` ≥ `request.patient_offered_price`
- `offered_price` ≥ `request.base_price`
- Error: `NR2002` — "Counter offer must be at least {patient_offered_price}"

### Location
- `latitude` and `longitude` must be valid decimal coordinates
- `city` is required
- Error: `NR5002` for invalid coordinates, `NR5003` for missing city

### Estimated arrival time format
- Must be in `HH:MM:SS` duration format
- Example: `"00:20:00"` for 20 minutes, `"01:30:00"` for 90 minutes

### One offer per nurse per request
- A nurse can only submit one offer per request (accept or counter-offer, not both)
- Error: `NR4003` — "You have already submitted an offer for this request"
