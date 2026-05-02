# On-Demand Nurse Requests — API Documentation

> **For:** Flutter Mobile Developer  
> **Applies to:** Both nurse and patient apps  
> **Auth:** All endpoints require `Authorization: Token <token>` header  
> **Base prefix:** `/api/nurse-requests/`

---

## Table of Contents

1. [Overview & Request Lifecycle](#1-overview--request-lifecycle)
2. [Standard Response Format](#2-standard-response-format)
3. [Error Code Reference](#3-error-code-reference)
4. [Push Notification Events (FCM)](#4-push-notification-events-fcm)
5. [Services Catalog (Shared)](#5-services-catalog-shared)
6. [Patient Endpoints](#6-patient-endpoints)
   - [List my requests](#61-list-my-requests)
   - [Create a request](#62-create-a-request)
   - [Create using saved address](#63-create-using-saved-address)
   - [Get saved addresses](#64-get-saved-addresses)
   - [Get request detail](#65-get-request-detail)
   - [Accept a nurse offer](#66-accept-a-nurse-offer)
   - [Decline a nurse offer](#67-decline-a-nurse-offer)
   - [Cancel a request](#68-cancel-a-request)
   - [View nurse profile before accepting](#69-view-nurse-profile-before-accepting)
7. [Nurse Endpoints](#7-nurse-endpoints)
   - [Manage my services](#71-manage-my-services)
   - [List available requests](#72-list-available-requests)
   - [Get request detail](#73-get-request-detail-nurse-view)
   - [Accept at patient price](#74-accept-at-patient-price)
   - [Counter-offer](#75-counter-offer)
   - [Reject a request](#76-reject-a-request)
   - [My offers (history)](#77-my-offers-history)
   - [Request history](#78-request-history)
8. [Status Flow Diagram](#8-status-flow-diagram)
9. [Flutter Implementation Checklist](#9-flutter-implementation-checklist)

---

## 1. Overview & Request Lifecycle

This feature works like a ride-hailing app but for nursing services.

**Flow:**
1. Patient browses the services catalog and picks a service
2. Patient creates a request with location + offered price → status becomes `SEARCHING`
3. Nearby **approved** nurses receive an **FCM push notification**
4. Nurses who offer that service can **accept** (at patient price) or **counter-offer**
5. Patient reviews nurse offers and **accepts one**
6. Nurse starts the service → `IN_PROGRESS`
7. Nurse completes the service → `COMPLETED`
8. Patient can leave a review

> **Pre-condition for nurses:** A nurse must add services to their profile via `POST /api/nurse-requests/nurse/my-services/add/` **before** they appear in request discovery and receive FCM notifications.

---

## 2. Standard Response Format

All responses follow one of two shapes:

### Success
```json
{
  "success": true,
  "data": { ... },
  "message": "Human-readable message"
}
```

For lists:
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

---

## 3. Error Code Reference

| Code | Area | Meaning |
|---|---|---|
| `NR1001` | Service | Service not found |
| `NR1002` | Service | Service is not active |
| `NR1003` | Service | Not a nursing service |
| `NR1004` | Service | Not available for on-demand requests |
| `NR1005` | Service | Already added to nurse profile |
| `NR1006` | Service | Service not in nurse profile |
| `NR2001` | Price | Offered price is below base price |
| `NR2002` | Price | Counter-offer below patient's offered price |
| `NR2003` | Price | Invalid price value |
| `NR3001` | Request | Request not found |
| `NR3002` | Request | Not the request owner |
| `NR3003` | Request | Invalid status for this action |
| `NR3004` | Request | Already cancelled |
| `NR3005` | Request | Already accepted |
| `NR3006` | Request | Already completed |
| `NR3007` | Request | Nurse does not offer this service |
| `NR4001` | Offer | Offer not found |
| `NR4002` | Offer | Offer no longer available |
| `NR4003` | Offer | Nurse already submitted an offer |
| `NR4004` | Offer | Offer expired |
| `NR5001` | Location | Location is required |
| `NR5002` | Location | Invalid coordinates |
| `NR5003` | Location | City is required |
| `NR5004` | Location | Address not found |
| `NR6001` | Auth | Not authenticated |
| `NR6002` | Auth | Caller is not a patient |
| `NR6003` | Auth | Caller is not a nurse |
| `NR6004` | Auth | Nurse profile not found |
| `NR6005` | Auth | Nurse not verified |

---

## 4. Push Notification Events (FCM)

All FCM payloads are delivered as a **data-only message** (no `notification` block). The app must build the local notification from the data payload.

### 4.1 New Request Nearby (→ Nurse)

Sent when a patient creates a request within the nurse's service area.

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

**Trigger:** Patient POSTs to `/api/nurse-requests/patient/nurse-requests/`  
**Recipients:** All approved, available nurses within the lesser of their `service_area_km` and 30 km  
**Pre-condition:** Nurse must have an active `NurseLocation` record (location sharing enabled)

---

### 4.2 Nurse Offer Received (→ Patient)

```json
{
  "notification_type": "NURSE_REQUEST_OFFER",
  "request_id": "42",
  "offer_id": "17"
}
```

Also sent for counter-offers with `"notification_type": "NURSE_REQUEST_COUNTER_OFFER"`.

---

### 4.3 Offer Accepted (→ Nurse)

```json
{
  "notification_type": "NURSE_REQUEST_ACCEPTED",
  "request_id": "42"
}
```

---

### 4.4 Service Started (→ Patient)

```json
{
  "notification_type": "NURSE_REQUEST_IN_PROGRESS",
  "request_id": "42"
}
```

---

### 4.5 Service Completed (→ Patient)

```json
{
  "notification_type": "NURSE_REQUEST_COMPLETED",
  "request_id": "42"
}
```

---

### 4.6 Request Cancelled (→ relevant party)

```json
{
  "notification_type": "NURSE_REQUEST_CANCELLED",
  "request_id": "42"
}
```

---

### FCM Handling Notes

- Register the device token via the notifications API before showing any nurse request screens
- On receiving `nurse_request_new`: navigate the nurse to the available requests list
- On receiving any other `notification_type`: re-fetch the request detail by `request_id` to refresh the UI
- All numeric values in FCM payloads are **strings** — parse them explicitly (`double.parse(...)`)

---

## 5. Services Catalog (Shared)

> Both patient and nurse apps use this to browse available nursing services.

### List all nursing services

```
GET /api/nurse-requests/services/
```

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
  "data": { ... },
  "available_nurses_count": 4,
  "message": "4 nurses available for this service"
}
```

**Error — `404 Not Found`**
```json
{
  "success": false,
  "error": { "code": "NR1001", "message": "Nursing service not found" }
}
```

---

## 6. Patient Endpoints

> Require the user to have role `PATIENT`.

---

### 6.1 List my requests

```
GET /api/nurse-requests/patient/nurse-requests/
```

**Query parameters:**

| Parameter | Values | Description |
|---|---|---|
| `status` | `SEARCHING`, `NURSE_RESPONDED`, `ACCEPTED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` | Filter by exact status |
| `is_active` | `true` | Only active requests (not completed/cancelled) |
| `is_history` | `true` | Only completed or cancelled requests |

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

---

### 6.2 Create a request

```
POST /api/nurse-requests/patient/nurse-requests/
Content-Type: application/json
```

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `service` | integer | **yes** | Service ID from the catalog |
| `patient_offered_price` | decimal string | **yes** | Must be ≥ service base price |
| `latitude` | decimal string | **yes** | Patient's current location |
| `longitude` | decimal string | **yes** | Patient's current location |
| `city` | string | **yes** | City name |
| `address_line` | string | no | Apartment / street detail |
| `notes` | string | no | Additional notes for the nurse |

```json
{
  "service": 1,
  "patient_offered_price": "750.00",
  "latitude": "36.737232",
  "longitude": "3.086472",
  "city": "Algiers",
  "address_line": "Apt 3B, Rue Didouche Mourad",
  "notes": "Please bring gloves"
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
      "base_price": "650.00",
      "estimated_duration": "00:45:00"
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
    "notes": "Please bring gloves",
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
|---|---|---|
| `NR1001` | 400 | Service not found |
| `NR1003` | 400 | Not a nursing service |
| `NR1004` | 400 | Service not available for on-demand |
| `NR2001` | 400 | Offered price below base price |
| `NR5002` | 400 | Invalid coordinates |
| `NR5003` | 400 | City missing |

---

### 6.3 Create using saved address

```
POST /api/nurse-requests/patient/nurse-requests/use-saved-address/
Content-Type: application/json
```

**Request body:**

| Field | Type | Required |
|---|---|---|
| `service` | integer | **yes** |
| `patient_offered_price` | decimal string | **yes** |
| `address_id` | integer | **yes** |
| `notes` | string | no |

```json
{
  "service": 1,
  "patient_offered_price": "750.00",
  "address_id": 5,
  "notes": "Ring bell twice"
}
```

**Success — `201 Created`** — same shape as [6.2](#62-create-a-request)

**Errors:**

| Code | HTTP | Trigger |
|---|---|---|
| `NR5004` | 400 | `address_id` missing |
| `NR5004` | 404 | Address not found or not owned by patient |
| `NR5002` | 400 | Saved address has no coordinates |

---

### 6.4 Get saved addresses

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

> Only use addresses where `has_coordinates: true` for nurse requests.

---

### 6.5 Get request detail

```
GET /api/nurse-requests/patient/nurse-requests/{id}/
```

**Response — `200 OK`** — full request object (same as create response `data`)

The `offers` array contains all nurse responses:

```json
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
    "status": "PENDING",
    "estimated_arrival_time": "00:20:00",
    "distance_km": "2.30",
    "notes": "I can be there in 20 minutes",
    "created_at": "2026-05-02T10:05:00Z",
    "responded_at": null
  }
]
```

**Offer status values:** `PENDING`, `ACCEPTED`, `REJECTED`, `COUNTER_OFFERED`, `EXPIRED`

---

### 6.6 Accept a nurse offer

```
POST /api/nurse-requests/patient/nurse-requests/{id}/accept/
Content-Type: application/json
```

**Request body:**
```json
{
  "offer_id": 17
}
```

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Offer accepted! The nurse will be on their way."
}
```

**Errors:**

| Code | HTTP | Trigger |
|---|---|---|
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Not the request owner |
| `NR3004` | 400 | Request already cancelled |
| `NR3005` | 400 | Request already accepted |
| `NR3006` | 400 | Request already completed |
| `NR3003` | 400 | No nurses have responded yet |
| `NR4001` | 400 | Invalid offer ID |
| `NR4002` | 400 | Offer is no longer available |

---

### 6.7 Decline a nurse offer

Declines one offer without cancelling the request. The patient can still accept other offers.

```
POST /api/nurse-requests/patient/nurse-requests/{id}/decline_offer/
Content-Type: application/json
```

**Request body:**
```json
{
  "offer_id": 17,
  "reason": "Too expensive"
}
```

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Offer declined. You can continue reviewing other offers."
}
```

**Errors:** `NR3001`, `NR3002`, `NR3004`, `NR3005`, `NR3006`, `NR4001`, `NR4002`

---

### 6.8 Cancel a request

```
POST /api/nurse-requests/patient/nurse-requests/{id}/cancel/
Content-Type: application/json
```

**Request body:**
```json
{
  "cancellation_reason": "Changed my mind"
}
```

`cancellation_reason` is optional.

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Request cancelled successfully"
}
```

**Errors:**

| Code | HTTP | Trigger |
|---|---|---|
| `NR3001` | 404 | Request not found |
| `NR3002` | 403 | Not the request owner |
| `NR3004` | 400 | Already cancelled |
| `NR3006` | 400 | Already completed (cannot cancel) |

---

### 6.9 View nurse profile before accepting

```
GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-profile/{nurse_id}/
```

`nurse_id` is the `nurse_id` field from the offer object.

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
    "biography": "Specialized in wound care...",
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

---

## 7. Nurse Endpoints

> Require the user to have role `PROVIDER` with `provider_type: NURSE`.

---

### 7.1 Manage my services

Nurses must add services to their profile to receive requests for those services.

#### List my services

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
      "description": "...",
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
  "available_to_add": [ ... ],
  "available_to_add_count": 5,
  "message": "Add services to receive on-demand requests for those services"
}
```

#### Add a service

```
POST /api/nurse-requests/nurse/my-services/add/
Content-Type: application/json
```

```json
{
  "service_id": 2,
  "custom_price": "900.00"
}
```

`custom_price` is optional. If omitted, the service's base price is used.

**Success — `201 Created`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Successfully added \"IV Therapy\" to your profile. You will now receive requests for this service."
}
```

**Errors:**

| Code | HTTP | Trigger |
|---|---|---|
| `NR6004` | 404 | Nurse profile not found |
| `NR1001` | 404 | Service not found |
| `NR1003` | 400 | Not a nursing service |
| `NR1004` | 400 | Not available for on-demand |
| `NR1002` | 400 | Service inactive |
| `NR1005` | 400 | Already in profile |

#### Remove a service

```
DELETE /api/nurse-requests/nurse/my-services/{service_id}/remove/
```

**Success — `200 OK`**
```json
{
  "success": true,
  "message": "Removed \"IV Therapy\" from your profile."
}
```

#### Update availability / price for a service

```
PATCH /api/nurse-requests/nurse/my-services/{service_id}/availability/
Content-Type: application/json
```

```json
{
  "is_available": false,
  "custom_price": "800.00"
}
```

Both fields are optional — send only what needs to change.

**Success — `200 OK`**
```json
{
  "success": true,
  "data": { ... },
  "message": "Service is now unavailable"
}
```

---

### 7.2 List available requests

Shows requests that:
- Are in `SEARCHING` or `NURSE_RESPONDED` status
- Match a service the nurse has in their profile (and is available for)
- The nurse has not already responded to
- Are within the nurse's configured service area

```
GET /api/nurse-requests/nurse/available-requests/
```

**Query parameter:**

| Parameter | Description |
|---|---|
| `city` | Filter by city name (case-insensitive partial match) |

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
      "service_description": "Professional wound dressing",
      "patient_name": "Amina B.",
      "patient_offered_price": "750.00",
      "base_price": "650.00",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "city": "Algiers",
      "address_line": "Apt 3B, Rue Didouche Mourad",
      "status": "SEARCHING",
      "created_at": "2026-05-02T10:00:00Z",
      "my_offer": null
    }
  ],
  "your_active_services_count": 2,
  "message": "Showing requests for your 2 active service(s)"
}
```

> `my_offer` is `null` if the nurse hasn't responded yet, or contains the offer object if they have.

**Warning response when nurse has no services — `200 OK`**
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

---

### 7.3 Get request detail (nurse view)

```
GET /api/nurse-requests/nurse/available-requests/{id}/
```

Returns the same detail shape as `NurseAvailableRequestSerializer` with `my_offer` populated if the nurse has already responded.

**Errors:**

| Code | HTTP | Trigger |
|---|---|---|
| `NR6004` | 404 | Nurse profile not found |
| `NR3001` | 404 | Request not found or nurse does not offer the service |
| `NR3007` | 403 | Nurse does not offer this service |

---

### 7.4 Accept at patient price

The nurse accepts the request at the price the patient offered.

```
POST /api/nurse-requests/nurse/available-requests/{id}/accept/
Content-Type: application/json
```

**Request body (all optional):**

| Field | Type | Description |
|---|---|---|
| `estimated_arrival_time` | string `HH:MM:SS` | Estimated time to arrive |
| `notes` | string | Message to the patient |
| `distance_km` | decimal | Distance from nurse to patient (auto-calculated if not provided) |

```json
{
  "estimated_arrival_time": "00:20:00",
  "notes": "I'll be there soon, please have the supplies ready.",
  "distance_km": 2.3
}
```

**Success — `201 Created`**
```json
{
  "success": true,
  "message": "Request accepted successfully",
  "offer_id": 17,
  "offered_price": "750.00"
}
```

**Errors:**

| Code | HTTP | Trigger |
|---|---|---|
| `NR3001` | 404 | Request not found |
| `NR6004` | 404 | Nurse profile not found |
| `NR3007` | 403 | Nurse does not offer this service |
| `NR4003` | 400 | Already submitted an offer |
| `NR3003` | 400 | Request no longer available (wrong status) |
| `NR4002` | 400 | Service error |

---

### 7.5 Counter-offer

Nurse proposes a higher price than the patient offered.

```
POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/
Content-Type: application/json
```

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `offered_price` | decimal | **yes** | Must be ≥ patient's offered price |
| `estimated_arrival_time` | string `HH:MM:SS` | no | |
| `notes` | string | no | Reason for higher price |
| `distance_km` | decimal | no | |

```json
{
  "offered_price": "900.00",
  "estimated_arrival_time": "00:30:00",
  "notes": "Traffic is heavy in this area",
  "distance_km": 8.5
}
```

**Success — `201 Created`**
```json
{
  "success": true,
  "message": "Counter offer submitted successfully",
  "offer_id": 18,
  "offered_price": "900.00"
}
```

**Errors:**

| Code | HTTP | Trigger |
|---|---|---|
| `NR2002` | 400 | Offered price below patient's offer |
| `NR4003` | 400 | Already submitted an offer |
| `NR3007` | 403 | Nurse does not offer this service |

---

### 7.6 Reject a request

Nurse dismisses the request without making an offer.

```
POST /api/nurse-requests/nurse/available-requests/{id}/reject/
Content-Type: application/json
```

**Request body (optional):**
```json
{
  "reason": "Too far from my current location"
}
```

**Success — `200 OK`**
```json
{
  "success": true,
  "message": "Request rejected"
}
```

---

### 7.7 My offers (history)

All requests where the nurse submitted any offer (pending, accepted, rejected, etc.).

```
GET /api/nurse-requests/nurse/my-offers/
```

**Query parameters:**

| Parameter | Values | Description |
|---|---|---|
| `status` | `SEARCHING`, `ACCEPTED`, `COMPLETED`, `CANCELLED`, etc. | Filter by request status |
| `offer_status` | `PENDING`, `ACCEPTED`, `REJECTED`, `COUNTER_OFFERED`, `EXPIRED` | Filter by nurse's offer status |
| `is_active` | `true` | Only active requests |
| `is_history` | `true` | Only completed or cancelled |

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

---

### 7.8 Request history

Only requests where the nurse was the **accepted nurse**.

```
GET /api/nurse-requests/nurse/request-history/
```

**Query parameters:**

| Parameter | Format | Description |
|---|---|---|
| `status` | `ACCEPTED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` | Filter by request status |
| `date_from` | `YYYY-MM-DD` | Filter completed_at from date |
| `date_to` | `YYYY-MM-DD` | Filter completed_at to date |
| `patient_name` | string | Partial name search |
| `ordering` | `-completed_at`, `final_price`, `-final_price` | Sort field |

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

---

## 8. Status Flow Diagram

```
Patient creates request
        │
        ▼
    SEARCHING ──────────────────────────► CANCELLED (patient cancels)
        │
        │ (nurse submits offer)
        ▼
 NURSE_RESPONDED ────────────────────────► CANCELLED (patient cancels)
        │
        │ (patient accepts offer)
        ▼
    ACCEPTED ───────────────────────────► CANCELLED (patient cancels)
        │
        │ (nurse starts service)
        ▼
  IN_PROGRESS
        │
        │ (nurse completes)
        ▼
   COMPLETED ──► patient can leave review
```

**What each status means for the UI:**

| Status | Patient UI | Nurse UI |
|---|---|---|
| `SEARCHING` | "Looking for nurses…" spinner | Request appears in available list |
| `NURSE_RESPONDED` | Show offers list, prompt to accept | Offer submitted, waiting |
| `ACCEPTED` | Nurse is confirmed, show ETA | Go to patient, navigate |
| `IN_PROGRESS` | Service underway | Tap "Complete" when done |
| `COMPLETED` | Rate and review screen | History entry |
| `CANCELLED` | Show cancellation reason | Offer removed |

---

## 9. Flutter Implementation Checklist

### Patient App

- [ ] Fetch services catalog on the service selection screen (`GET /services/`)
- [ ] Use device GPS or map picker to get `latitude`, `longitude`, `city`
- [ ] Show `base_price` as minimum — the patient cannot offer less
- [ ] Poll or use WebSocket group `request_{id}_updates` to refresh offer list in real time
- [ ] On FCM `nurse_request_new` received: ignore (this goes to nurses, not patients)
- [ ] On FCM `NURSE_REQUEST_OFFER` or `NURSE_REQUEST_COUNTER_OFFER`: re-fetch request detail to show new offer
- [ ] In the offer card show: nurse name, photo, rating, experience, distance, arrival time, offered price
- [ ] Tapping a nurse card → call the nurse-profile endpoint before showing accept button
- [ ] Distinguish `PENDING` offers (can accept/decline) from `COUNTER_OFFERED` ones (higher price)
- [ ] After accepting an offer, navigate to an "On the way" screen (status `ACCEPTED`)
- [ ] After `IN_PROGRESS` notification: show "Service in progress" screen
- [ ] After `COMPLETED` notification: show review screen (`can_leave_review: true`)

### Nurse App

- [ ] On first launch after login: prompt nurse to add services (`GET /nurse/my-services/`)
- [ ] Register FCM token so the server can send `nurse_request_new` notifications
- [ ] Enable location sharing (update `NurseLocation` via the provider location endpoint) so the radius filter works
- [ ] On FCM `nurse_request_new`: navigate to available requests list or show a banner
- [ ] Refresh available requests list when app foregrounds
- [ ] Show `patient_offered_price` and the option to accept at that price or counter-offer
- [ ] When submitting counter-offer, validate locally that `offered_price >= patient_offered_price`
- [ ] On FCM `NURSE_REQUEST_ACCEPTED`: navigate to the accepted request detail
- [ ] Show "Start service" button (calls `POST /patient/nurse-requests/{id}/start/`) when status is `ACCEPTED`
- [ ] Show "Complete service" button (calls `POST /patient/nurse-requests/{id}/complete/`) when status is `IN_PROGRESS`
- [ ] Request history (`/nurse/request-history/`) shows anonymized patient names — this is intentional
- [ ] `can_leave_review: true` in history detail means the nurse can review the patient
- [ ] Available request cards now show `patient_rating`, `patient_review_count`, and `patient_clinical_summary` — use these to display patient reliability and key medical info
- [ ] History detail includes `patient_overall_rating` and `patient_total_reviews` — show alongside this-request review
- [ ] Use `GET /nurse/request-history/{id}/patient-folder/` to show the patient's non-confidential medical records during/after service (status must be ACCEPTED, IN_PROGRESS, or COMPLETED)

---

## 10. New Fields Reference (2025 Update)

### 10.1 Available Request — Patient Info Fields

Returned in each item of `GET /api/nurse-requests/nurse/available-requests/`.

| Field | Type | Description |
|---|---|---|
| `patient_rating` | `float \| null` | Aggregate star rating this patient has received from past nurses. `null` if no reviews yet. |
| `patient_review_count` | `int` | Total number of reviews the patient has received. |
| `patient_clinical_summary` | `object \| null` | Basic clinical info required for safe care. `null` if no PatientRecord is linked. |
| `patient_clinical_summary.blood_type` | `string` | e.g. `"A+"`, `"UNKNOWN"` |
| `patient_clinical_summary.known_allergies` | `string` | Free-text allergy notes |
| `patient_clinical_summary.chronic_conditions` | `string` | Free-text chronic conditions |

**Sample:**
```json
{
  "id": 42,
  "service_name": "Wound Care",
  "patient_name": "Amina B.",
  "patient_offered_price": "750.00",
  "patient_rating": 4.7,
  "patient_review_count": 12,
  "patient_clinical_summary": {
    "blood_type": "O+",
    "known_allergies": "Penicillin",
    "chronic_conditions": "Type 2 Diabetes"
  }
}
```

---

### 10.2 Request History — Patient Rating Fields

Returned in each item of `GET /api/nurse-requests/nurse/request-history/`.

| Field | Type | Description |
|---|---|---|
| `patient_overall_rating` | `float \| null` | Patient's overall aggregate rating. `null` if no reviews. |
| `patient_total_reviews` | `int` | Total reviews the patient has ever received. |
| `nurse_review` | `object \| null` | The review the nurse left for the patient **on this specific request**. |
| `patient_review` | `object \| null` | The review the patient left for the nurse on this specific request. |

---

### 10.3 Accepted Nurse Profile — Full Rating Detail

Returned in `accepted_nurse_profile` inside `GET /api/nurse-requests/patient/nurse-requests/{id}/`.

| Field | Type | Description |
|---|---|---|
| `average_rating` | `float` | Nurse's average star rating |
| `review_count` | `int` | Total reviews |
| `rating_distribution` | `object` | Breakdown by star: `{1: N, 2: N, 3: N, 4: N, 5: N}` |
| `recent_reviews` | `array` | Up to 3 most recent reviews with `id`, `rating`, `text`, `created_at`, `has_response` |

---

## 11. Patient Medical Folder (Nurse Access)

### 11.1 View Patient Medical Folder

```
GET /api/nurse-requests/nurse/request-history/{id}/patient-folder/
```

**Auth:** Nurse only. The authenticated nurse must be the `accepted_nurse` on the request.  
**Status requirement:** Request must be in `ACCEPTED`, `IN_PROGRESS`, or `COMPLETED` status.  
**Privacy:** Confidential records (`is_confidential=true`) are **never** returned. All access is logged in `MedicalRecordAccessLog`.

**Response:**
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
      "by_type": { ... },
      "active_allergies": [ ... ],
      "critical_or_high": [ ... ],
      "recent_30_days": [ ... ]
    }
  }
}
```

**Error cases:**

| Code | Meaning |
|---|---|
| `NR3001` | Request not found |
| `NR3002` | Nurse is not the accepted nurse on this request |
| `NR3003` | Request is not in an allowed status (ACCEPTED/IN_PROGRESS/COMPLETED) |
| `NR6004` | Nurse profile not found |
