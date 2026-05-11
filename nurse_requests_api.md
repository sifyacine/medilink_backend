# Nurse Requests API — v3
## Complete Mobile Integration Guide

**Base URL:** `https://api.medilink.dz/api/nurse-requests/`  
**Auth:** `Authorization: Token <token>` on every request  
**Currency:** All prices in **DZD** (Algerian Dinar)  
**Date format:** ISO 8601 — `2025-12-31T23:59:59Z`

---

## Status Flow (Uber-like)

```
Patient creates request
        ↓
    CREATED ──► SEARCHING ──► NURSE_RESPONDED ──► PATIENT_DECISION
                                                        ↓
                                                    ACCEPTED
                                                        ↓
                                                  IN_PROGRESS
                                                        ↓
                                                   COMPLETED
       (any stage before COMPLETED can become CANCELLED)
```

| Status | Who sees it | What's happening |
|--------|-------------|-----------------|
| `SEARCHING` | Patient waiting, nurses being notified | Patient's request is live, nearby nurses get FCM/WS push |
| `NURSE_RESPONDED` | Patient gets notified | At least one nurse sent an offer |
| `PATIENT_DECISION` | Patient chooses | Multiple offers available (alias used in some filters) |
| `ACCEPTED` | Both parties notified | Patient picked a nurse, others' offers expired |
| `IN_PROGRESS` | Both parties notified | Nurse tapped "Start Service" |
| `COMPLETED` | Patient notified, reviews unlocked | Nurse tapped "Complete Service" |
| `CANCELLED` | Relevant party notified | Patient or system cancelled |

---

## WebSocket Connection

**Endpoint:** `wss://api.medilink.dz/ws/nurse-requests/`  
**Auth:** Pass `?token=<auth_token>` in the query string — **not** in headers.  
**Close code 4001** = not authenticated; reconnect with a valid token.

### Channel Groups (server-managed)

| Group | Who joins | Purpose |
|-------|-----------|---------|
| `user_{user_id}_nurse_requests` | Patient & Nurse (personal) | Personal events (offers, status) |
| `request_{request_id}_updates` | Anyone watching a request | All status changes on one request |
| `city_{city_name}_requests` | Nurses in that city | New requests broadcast to city |

> City group names use lowercase with underscores: `city_algiers_requests`, `city_oran_requests`

### Sending a message to the server

```json
{ "type": "ping" }
```
Server replies `{ "type": "pong" }`.

---

## Error Response Format

Every error returns:

```json
{
  "success": false,
  "error": {
    "code": "NR3003",
    "message": "Human-readable message",
    "details": { }
  }
}
```

---

---

# SECTION A — PATIENT MOBILE APP

---

## A.1  Browse Nursing Services

**`GET /api/nurse-requests/services/`**

No required params. Returns all active on-demand nursing services.

**Response `200`:**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 3,
      "name": "Home Blood Draw",
      "description": "Nurse visits your home to collect blood samples.",
      "base_price": "800.00",
      "estimated_duration": "00:30:00",
      "is_active": true,
      "icon": "/media/services/icons/blood_draw.png",
      "currency": "DZD",
      "is_home_service": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "message": "Select a service to request a nurse"
}
```

---

**`GET /api/nurse-requests/services/{id}/`**

**Response `200`:**
```json
{
  "success": true,
  "data": { /* same service object */ },
  "available_nurses_count": 12,
  "message": "12 nurses available for this service"
}
```

---

## A.2  Get Saved Addresses

**`GET /api/nurse-requests/patient/nurse-requests/saved-addresses/`**

Returns the patient's saved addresses (linked via ContentType to their User).

**Response `200`:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": 7,
      "street": "12 Rue Didouche Mourad",
      "city": "Algiers",
      "state": "Alger",
      "zip_code": "16000",
      "country": "Algeria",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "is_primary": true,
      "address_type": "HOME",
      "full_address": "12 Rue Didouche Mourad, Algiers, Alger, Algeria",
      "has_coordinates": true
    }
  ],
  "message": "Select a saved address or choose location from map"
}
```

**Mobile tip:** Show addresses with `has_coordinates: true` first — those can be used directly. Addresses without coordinates require the patient to pin the map.

---

## A.3  Create a Request (Manual Location)

**`POST /api/nurse-requests/patient/nurse-requests/`**

**Request body:**
```json
{
  "service": 3,
  "patient_offered_price": "900.00",
  "latitude": "36.737232",
  "longitude": "3.086472",
  "city": "Algiers",
  "address_line": "12 Rue Didouche Mourad, Bab El Oued",
  "notes": "Please ring the bell on the second floor"
}
```

| Field | Required | Constraint |
|-------|----------|------------|
| `service` | ✅ | Must be `service_type=NURSE`, `is_on_demand=True`, `is_active=True` |
| `patient_offered_price` | ✅ | Must be ≥ `service.base_price` |
| `latitude` | ✅ | −90 to +90 |
| `longitude` | ✅ | −180 to +180 |
| `city` | ✅ | City name for nurse broadcast channel |
| `address_line` | ❌ | Human-readable address label |
| `notes` | ❌ | Additional instructions for nurse |

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "patient_user": 15,
    "patient_record": null,
    "patient_name": "Yacine B.",
    "service": {
      "id": 3,
      "name": "Home Blood Draw",
      "base_price": "800.00",
      "estimated_duration": "00:30:00"
    },
    "accepted_nurse": null,
    "accepted_nurse_name": null,
    "accepted_nurse_profile": null,
    "base_price": "800.00",
    "patient_offered_price": "900.00",
    "final_price": null,
    "address": null,
    "address_details": null,
    "latitude": "36.737232",
    "longitude": "3.086472",
    "city": "Algiers",
    "state": "",
    "address_line": "12 Rue Didouche Mourad",
    "country": "Algeria",
    "status": "SEARCHING",
    "notes": "Please ring the bell on the second floor",
    "offers": [],
    "created_at": "2025-05-11T10:00:00Z",
    "updated_at": "2025-05-11T10:00:00Z",
    "accepted_at": null,
    "started_at": null,
    "completed_at": null,
    "cancelled_at": null,
    "cancellation_reason": "",
    "can_leave_review": false
  },
  "message": "Request created successfully. Searching for available nurses..."
}
```

**What happens immediately after creation:**
1. Status set to `SEARCHING`
2. `request_created` signal fires → `transaction.on_commit`
3. City-wide WebSocket event: `nurse_request_new` → `city_algiers_requests`
4. FCM push to every approved nurse within 30 km who has the service in their profile

---

## A.4  Create a Request (Using Saved Address)

**`POST /api/nurse-requests/patient/nurse-requests/use-saved-address/`**

**Request body:**
```json
{
  "service": 3,
  "patient_offered_price": "900.00",
  "address_id": 7,
  "notes": "Ring doorbell twice"
}
```

The server copies `latitude`, `longitude`, `city`, and `address_line` from the saved address automatically.

**Response:** Same `201` structure as A.3.

**Error — address has no coordinates:**
```json
{
  "success": false,
  "error": {
    "code": "NR5002",
    "message": "This address does not have valid coordinates. Please select location from map."
  }
}
```

---

## A.5  List My Requests

**`GET /api/nurse-requests/patient/nurse-requests/`**

| Query param | Values | Effect |
|------------|--------|--------|
| `status` | `SEARCHING`, `ACCEPTED`, `COMPLETED`, etc. | Filter by exact status |
| `is_active=true` | boolean | SEARCHING, NURSE_RESPONDED, PATIENT_DECISION, ACCEPTED, IN_PROGRESS |
| `is_history=true` | boolean | COMPLETED and CANCELLED only |

**Response `200`:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "service_name": "Home Blood Draw",
      "patient_name": "Yacine B.",
      "status": "NURSE_RESPONDED",
      "patient_offered_price": "900.00",
      "final_price": null,
      "city": "Algiers",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "offers_count": 3,
      "created_at": "2025-05-11T10:00:00Z",
      "updated_at": "2025-05-11T10:05:00Z"
    }
  ]
}
```

---

## A.6  Get Request Detail

**`GET /api/nurse-requests/patient/nurse-requests/{id}/`**

Returns full detail with all offers, accepted nurse profile, and review eligibility.

**`offers` array (when nurses have responded):**
```json
{
  "offers": [
    {
      "id": 88,
      "nurse_id": 9,
      "nurse_name": "Fatima Zahra Benali",
      "nurse_rating": 4.7,
      "nurse_review_count": 23,
      "nurse_profile_image": "https://api.medilink.dz/media/nurses/profiles/fz.jpg",
      "nurse_years_experience": 7,
      "nurse_completed_services": 45,
      "nurse_biography": "Specialised in home care and wound management...",
      "nurse_is_verified": true,
      "offered_price": "900.00",
      "status": "PENDING",
      "estimated_arrival_time": "00:20:00",
      "distance_km": "4.50",
      "notes": "I'm nearby, can arrive quickly",
      "created_at": "2025-05-11T10:03:00Z",
      "responded_at": "2025-05-11T10:03:00Z"
    }
  ]
}
```

**`accepted_nurse_profile` (when accepted):**
```json
{
  "accepted_nurse_profile": {
    "first_name": "Fatima Zahra",
    "last_name": "Benali",
    "phone_number": "+213XXXXXXXXX",
    "profile_image": "https://api.medilink.dz/media/nurses/profiles/fz.jpg",
    "average_rating": 4.7,
    "review_count": 23,
    "rating_distribution": { "1": 0, "2": 1, "3": 2, "4": 5, "5": 15 },
    "recent_reviews": [
      {
        "id": "uuid-here",
        "rating": 5,
        "text": "Very professional and gentle...",
        "created_at": "2025-04-10T00:00:00Z",
        "has_response": false
      }
    ]
  }
}
```

---

## A.7  View Nurse Profile (Before Accepting)

**`GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-profile/{nurse_id}/`**

Returns full nurse profile + their offer details. Use this for the "Nurse Details" screen before the patient taps Accept.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "id": 9,
    "first_name": "Fatima Zahra",
    "last_name": "Benali",
    "full_name": "Fatima Zahra Benali",
    "profile_image": "https://...",
    "biography": "8 years of home care experience...",
    "license_number": "ALG-NRS-2017-0099",
    "certification": "RN",
    "years_of_experience": 7,
    "is_verified": true,
    "is_available": true,
    "is_home_service_available": true,
    "average_rating": 4.7,
    "review_count": 23,
    "rating_distribution": { "1": 0, "2": 1, "3": 2, "4": 5, "5": 15 },
    "recent_reviews": [ /* last 5 reviews */ ],
    "completed_services_count": 45,
    "services_offered": [
      {
        "id": 3,
        "title": "Home Blood Draw",
        "price": "900.00 DZD",
        "duration_minutes": 30
      }
    ]
  },
  "offer": {
    "id": 88,
    "offered_price": "900.00",
    "status": "PENDING",
    "estimated_arrival_time": "00:20:00",
    "notes": "I'm nearby, can arrive quickly"
  }
}
```

---

## A.8  View Nurse Service History (Before Accepting)

**`GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-history/{nurse_id}/`**

Returns last 10 completed services for that nurse (anonymised patient names).

**Response `200`:**
```json
{
  "success": true,
  "count": 10,
  "results": [
    {
      "id": 35,
      "service_title": "Home Blood Draw",
      "patient_name": "Y***e",
      "completed_at": "2025-04-30T15:00:00Z",
      "final_price": "900.00",
      "review": { "rating": 5, "text": "Very professional..." }
    }
  ]
}
```

---

## A.9  Accept a Nurse Offer

**`POST /api/nurse-requests/patient/nurse-requests/{id}/accept/`**

**Request body:**
```json
{
  "offer_id": 88
}
```

> **Important:** `offer_id` must reference an offer with status `PENDING` or `COUNTER_OFFERED`. Rejected or expired offers cannot be accepted.

**Response `200`:**
```json
{
  "success": true,
  "data": { /* full NurseServiceRequestDetailSerializer */ },
  "message": "Offer accepted! The nurse will be on their way."
}
```

**What happens:**
1. Chosen offer → `ACCEPTED`
2. All other `PENDING`/`COUNTER_OFFERED` offers → `REJECTED`
3. `accepted_nurse` and `final_price` set on request
4. Status → `ACCEPTED`
5. `request_status_changed` signal fires → notifies nurse (FCM + WS) and patient (WS)
6. Medical record access granted to nurse

**Possible errors:**

| Code | Meaning |
|------|---------|
| `NR3003` | Request status is not NURSE_RESPONDED or PATIENT_DECISION |
| `NR3004` | Request is already cancelled |
| `NR3005` | Request already has an accepted offer |
| `NR4001` | offer_id not found or doesn't belong to this request |
| `NR4002` | Offer status is no longer PENDING/COUNTER_OFFERED |

---

## A.10  Decline a Specific Offer

**`POST /api/nurse-requests/patient/nurse-requests/{id}/decline_offer/`**

Declines one offer while keeping the request open for others.

**Request body:**
```json
{
  "offer_id": 88,
  "reason": "Looking for a closer nurse"
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": { /* updated request with offer status now REJECTED */ },
  "message": "Offer declined. You can continue reviewing other offers."
}
```

The declined nurse receives:
- FCM: "Your offer for Home Blood Draw was declined"
- WS event: `nurse_offer_declined`

---

## A.11  Cancel a Request

**`POST /api/nurse-requests/patient/nurse-requests/{id}/cancel/`**

**Request body:**
```json
{
  "cancellation_reason": "I found another option"
}
```

**Response `200`:** Full request detail with `status: "CANCELLED"`.

**Rules:**
- Cannot cancel a `COMPLETED` request
- Cannot cancel an already `CANCELLED` request
- All `PENDING`/`COUNTER_OFFERED` offers → `EXPIRED`
- If nurse was already accepted: nurse gets FCM + WS cancellation notification

---

## A.12  Leave a Review for the Nurse

Uses the **generic Reviews API** (not nurse-requests specific). Call after `status = COMPLETED` and `can_leave_review = true`.

**`POST /api/reviews/`**

**Request body:**
```json
{
  "reviewed_content_type": "provider",
  "reviewed_object_id": "9",
  "context_content_type": "nurseservicerequest",
  "context_object_id": "42",
  "rating": 5,
  "text": "Fatima was professional, gentle and on time.",
  "title": "Excellent service"
}
```

| Field | Note |
|-------|------|
| `reviewed_content_type` | Always `"provider"` for a nurse |
| `reviewed_object_id` | `accepted_nurse` field from the request (Provider ID as string) |
| `context_content_type` | Always `"nurseservicerequest"` |
| `context_object_id` | The `NurseServiceRequest.id` as string — prevents duplicate reviews per service |
| `rating` | Integer 1–5 |

**Response `201`:** Review object with ID.

**After review:**
- Nurse gets FCM: "⭐ New Review — Yacine gave you 5★"
- Nurse gets WS event: `nurse_review_received`
- Nurse's aggregate rating updated → WS event `nurse_rating_updated`

**Check `can_leave_review` first** — `true` means review not yet submitted and request is completed.

---

## A.13  Report a Nurse

Uses the **generic Reports API**.

**`POST /api/reports/`**

**Request body:**
```json
{
  "reported_content_type": "provider",
  "reported_object_id": "9",
  "reason": "UNPROFESSIONAL",
  "description": "The nurse was rude and refused to follow instructions.",
  "priority": "HIGH"
}
```

| `reason` options | |
|------|--|
| `INAPPROPRIATE_BEHAVIOR` | `HARASSMENT` | `UNPROFESSIONAL` |
| `FAKE_PROFILE` | `SCAM` | `SAFETY_CONCERN` |
| `INCORRECT_INFO` | `OTHER` | |

---

## A.14  Patient WebSocket Events

Subscribe to `user_{user_id}_nurse_requests` for personal events and `request_{id}_updates` for a specific request.

### Events received by patient

| Event type | When fired | Key payload fields |
|-----------|-----------|-------------------|
| `nurse_request_new` | Own request created (confirmation) | `request` |
| `nurse_request_offer` | A nurse submitted an offer | `request`, `offer` |
| `nurse_request_accepted` | Patient accepted (own action confirmation) | `request` |
| `nurse_request_in_progress` | Nurse tapped Start | `request`, `message` |
| `nurse_request_completed` | Nurse tapped Complete | `request`, `message` |
| `nurse_request_cancelled` | Request cancelled | `request`, `cancelled_by`, `reason` |

### Sample WS payload — nurse offer received

```json
{
  "type": "nurse_request_offer",
  "data": {
    "request": { /* full request object */ },
    "offer": {
      "id": 88,
      "nurse_id": 9,
      "nurse_name": "Fatima Zahra Benali",
      "nurse_rating": 4.7,
      "offered_price": "900.00",
      "status": "PENDING",
      "estimated_arrival_time": "00:20:00",
      "distance_km": "4.50"
    },
    "message": "Fatima Zahra Benali accepted your request at 900.00 DZD"
  }
}
```

### Sample WS payload — service in progress

```json
{
  "type": "nurse_request_in_progress",
  "data": {
    "request": { /* full request */ },
    "message": "Fatima Zahra Benali has started the service"
  }
}
```

---

---

# SECTION B — NURSE MOBILE APP

---

## B.1  Setup — Manage Profile Services

Nurses must add services to their profile to receive on-demand requests. A nurse with zero services sees zero available requests.

**`GET /api/nurse-requests/nurse/my-services/`**

**Response `200`:**
```json
{
  "success": true,
  "my_services": [
    {
      "id": 3,
      "service_id": 3,
      "title": "Home Blood Draw",
      "description": "...",
      "base_price": "800.00",
      "custom_price": "900.00",
      "effective_price": "900.00 DZD",
      "duration_minutes": 30,
      "is_available": true,
      "is_on_demand": true,
      "created_at": "2025-05-01T00:00:00Z"
    }
  ],
  "my_services_count": 1,
  "available_to_add": [ /* services not yet in profile */ ],
  "available_to_add_count": 4,
  "message": "Add services to receive on-demand requests for those services"
}
```

---

**`POST /api/nurse-requests/nurse/my-services/add/`**

**Request body:**
```json
{
  "service_id": 3,
  "custom_price": "950.00"
}
```

`custom_price` is optional — omit to use the service's base price. If set, it overrides the base price shown to patients.

---

**`PATCH /api/nurse-requests/nurse/my-services/{service_id}/availability/`**

Toggle availability without removing the service.

```json
{
  "is_available": false
}
```

When `is_available: false`, the nurse will **not** receive new requests for that service until re-enabled.

---

**`DELETE /api/nurse-requests/nurse/my-services/{service_id}/remove/`**

Removes service from profile permanently (but doesn't affect in-progress requests for that service).

---

## B.2  Update Location (REQUIRED for receiving nearby requests)

> **⚠️ Gap identified:** There is no dedicated REST endpoint to update `NurseLocation`. The `NurseLocation` model exists in the database but the app must call the generic provider profile update or a direct admin endpoint. **Mobile app should periodically PATCH the nurse location** — see implementation note below.

**Temporary workaround — direct PATCH on the nurse profile:**

**`PATCH /api/providers/nurse/location/`** *(endpoint needs to be added — see Gaps section)*

Until that endpoint exists, location is consumed from `NurseLocation` which is populated by admin or background sync. The `get_nurses_within_radius()` function reads from `nurse.current_location` (the `NurseLocation` table).

**What the endpoint should accept:**
```json
{
  "latitude": "36.737232",
  "longitude": "3.086472",
  "accuracy_meters": 10,
  "is_active": true
}
```

**Why this matters:**
- FCM push to nearby nurses uses Haversine distance from `NurseLocation.latitude/longitude`
- Nurses without `is_active = true` location are excluded from `get_nurses_within_radius()`
- Nurses also use `Address` (WORK/CLINIC type, `is_primary=True`) for the available-requests distance filter in `NurseAvailableRequestsViewSet`

---

## B.3  Available Requests Feed

**`GET /api/nurse-requests/nurse/available-requests/`**

Returns requests in `SEARCHING` or `NURSE_RESPONDED` status that:
- Match services in the nurse's profile (`is_available=True`)
- The nurse has NOT already responded to
- Are within the nurse's `service_area_km` (default 50km) of their primary WORK/CLINIC address

| Query param | Effect |
|------------|--------|
| `city=Algiers` | Filter to one city |

**Response `200`:**
```json
{
  "success": true,
  "count": 4,
  "results": [
    {
      "id": 42,
      "service_id": 3,
      "service_name": "Home Blood Draw",
      "service_description": "Nurse visits your home to collect blood samples.",
      "patient_name": "Yacine B.",
      "patient_offered_price": "900.00",
      "base_price": "800.00",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "city": "Algiers",
      "address_line": "12 Rue Didouche Mourad, Bab El Oued",
      "status": "SEARCHING",
      "created_at": "2025-05-11T10:00:00Z",
      "my_offer": null,
      "patient_rating": 4.8,
      "patient_review_count": 3,
      "patient_clinical_summary": {
        "blood_type": "A+",
        "known_allergies": "Penicillin",
        "chronic_conditions": "Hypertension"
      }
    }
  ],
  "your_active_services_count": 2
}
```

**`patient_clinical_summary`** — basic clinical info (blood type, allergies, chronic conditions) exposed to nurses before they accept, so they can decide if they can handle the case. **No confidential records** are included here.

---

## B.4  View a Single Available Request

**`GET /api/nurse-requests/nurse/available-requests/{id}/`**

Returns full request detail. Validates that the nurse offers the required service.

**Error — nurse doesn't offer this service:**
```json
{
  "success": false,
  "error": {
    "code": "NR3007",
    "message": "You do not offer \"Home Blood Draw\" service. Add it to your profile first.",
    "details": {
      "service_id": 3,
      "service_name": "Home Blood Draw",
      "action": "POST /api/nurse-requests/nurse/my-services/add/ with service_id=3"
    }
  }
}
```

---

## B.5  Accept at Patient's Price

**`POST /api/nurse-requests/nurse/available-requests/{id}/accept/`**

**Request body:**
```json
{
  "estimated_arrival_time": "00:20:00",
  "notes": "I'm 5 km away, on my way",
  "distance_km": "4.80"
}
```

All fields are optional. `distance_km` is auto-calculated from `NurseLocation` if not provided.

**Response `201`:**
```json
{
  "success": true,
  "message": "Request accepted successfully",
  "offer_id": 88,
  "offered_price": "900.00"
}
```

**What happens:**
1. `NurseOffer` created with `status=PENDING`, `offered_price = patient_offered_price`
2. Request status updated to `NURSE_RESPONDED` (if was `SEARCHING`)
3. `nurse_offer_submitted` signal fires → patient gets FCM + WS `nurse_request_offer`
4. Request disappears from this nurse's available list on next fetch

---

## B.6  Make a Counter-Offer

**`POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/`**

Use when your price is higher than what the patient offered.

**Request body:**
```json
{
  "offered_price": "1100.00",
  "estimated_arrival_time": "00:30:00",
  "notes": "Rush hour traffic, higher price to cover extra time",
  "distance_km": "6.20"
}
```

**Constraint:** `offered_price` must be ≥ `patient_offered_price` AND ≥ `base_price`.

**Response `201`:**
```json
{
  "success": true,
  "message": "Counter offer submitted successfully",
  "offer_id": 89,
  "offered_price": "1100.00"
}
```

Patient receives:
- FCM: "💰 Counter Offer — Fatima Zahra offered 1100.00 DZD for Home Blood Draw"
- WS event: `nurse_request_offer`

---

## B.7  Reject / Dismiss a Request

**`POST /api/nurse-requests/nurse/available-requests/{id}/reject/`**

Removes the request from this nurse's feed. Does not affect other nurses.

**Request body (optional):**
```json
{
  "reason": "Too far from my location"
}
```

**Response `200`:**
```json
{
  "success": true,
  "message": "Request dismissed"
}
```

> Internally, a `NurseOffer` with `status=REJECTED` is created as a marker so the request is excluded from subsequent queries for this nurse.

---

## B.8  View My Submitted Offers

**`GET /api/nurse-requests/nurse/my-offers/`**

Shows all requests where the nurse submitted any offer (including rejected, expired, and accepted).

| Query param | Values |
|------------|--------|
| `status` | `SEARCHING`, `ACCEPTED`, `COMPLETED`, etc. |
| `offer_status` | `PENDING`, `ACCEPTED`, `REJECTED`, `COUNTER_OFFERED`, `EXPIRED` |
| `is_active=true` | Active requests only |
| `is_history=true` | Completed/cancelled only |

**Response `200`:**
```json
{
  "success": true,
  "count": 15,
  "results": [ /* NurseServiceRequestDetailSerializer objects */ ],
  "stats": {
    "total_offers": 15,
    "pending": 2,
    "accepted": 8
  }
}
```

---

## B.9  Active Request — Mark as Started

After a patient accepts the offer, the nurse travels to the patient. When the nurse arrives and begins the service:

**`POST /api/nurse-requests/nurse/request-history/{id}/start/`**

No body required.

**Requirement:** Request must be in `ACCEPTED` status and the calling nurse must be `accepted_nurse`.

**Response `200`:**
```json
{
  "success": true,
  "data": { /* full request with status=IN_PROGRESS, started_at set */ },
  "message": "Service started"
}
```

**What happens:**
- Status → `IN_PROGRESS`, `started_at` = now
- Patient gets FCM: "🏥 Service Started — Fatima Zahra Benali has started providing Home Blood Draw"
- Both parties get WS: `nurse_request_in_progress`

---

## B.10  Active Request — Mark as Completed

**`POST /api/nurse-requests/nurse/request-history/{id}/complete/`**

**Requirement:** Request must be in `IN_PROGRESS` status.

**Response `200`:**
```json
{
  "success": true,
  "data": { /* full request with status=COMPLETED, completed_at set */ },
  "message": "Service completed successfully"
}
```

**What happens:**
- Status → `COMPLETED`, `completed_at` = now
- Patient gets FCM: "✔️ Service Completed — You can now leave a review"
- Patient gets WS: `nurse_request_completed`
- `can_leave_review` becomes `true` on both sides
- Review window unlocked for patient → nurse and nurse → patient

---

## B.11  Request History (Nurse Side)

**`GET /api/nurse-requests/nurse/request-history/`**

Shows all requests where this nurse was the `accepted_nurse`.

| Query param | Effect |
|------------|--------|
| `status` | `ACCEPTED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| `date_from` | ISO date, e.g. `2025-01-01` |
| `date_to` | ISO date, e.g. `2025-12-31` |
| `patient_name` | Partial name match |
| `ordering` | Default `-completed_at`. Also: `final_price`, `-final_price`, etc. |
| `page` | Pagination page |
| `page_size` | Default 20 |

**Response `200`:**
```json
{
  "success": true,
  "count": 45,
  "results": [
    {
      "id": 42,
      "service_name": "Home Blood Draw",
      "patient_name": "Y. B.",
      "patient_initials": "YB",
      "status": "COMPLETED",
      "status_display": "Completed",
      "final_price": "900.00",
      "base_price": "800.00",
      "accepted_at": "2025-05-11T10:10:00Z",
      "started_at": "2025-05-11T10:30:00Z",
      "completed_at": "2025-05-11T11:00:00Z",
      "cancelled_at": null,
      "cancellation_reason": "",
      "city": "Algiers",
      "can_leave_review": true,
      "nurse_review": null,
      "patient_review": {
        "id": "uuid-here",
        "rating": 5,
        "text": "Very professional and gentle...",
        "created_at": "2025-05-11T11:30:00Z"
      },
      "patient_overall_rating": 4.8,
      "patient_total_reviews": 3,
      "created_at": "2025-05-11T10:00:00Z",
      "updated_at": "2025-05-11T11:00:00Z"
    }
  ],
  "stats": {
    "total_accepted": 50,
    "total_in_progress": 1,
    "total_completed": 45,
    "total_cancelled": 4
  }
}
```

---

## B.12  Patient Medical Folder (After Acceptance)

**`GET /api/nurse-requests/nurse/request-history/{id}/patient-folder/`**

Only accessible for `ACCEPTED`, `IN_PROGRESS`, or `COMPLETED` requests. Only the accepted nurse can access this. **Confidential records are excluded.** All accesses are logged.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "request_id": 42,
    "access_note": "Confidential records are excluded. Access is logged.",
    "patient_clinical_info": {
      "blood_type": "A+",
      "known_allergies": "Penicillin",
      "chronic_conditions": "Hypertension",
      "current_medications": "Amlodipine 5mg",
      "emergency_contact_name": "Karim B.",
      "emergency_contact_phone": "+213XXXXXXXXX"
    },
    "summary": {
      "total_records": 12,
      "active_allergies": 2,
      "critical_or_high": 1,
      "recent_30_days": 3,
      "record_types": {
        "PRESCRIPTION": 5,
        "ALLERGY": 2,
        "LAB_RESULT": 3,
        "VISIT_NOTE": 2
      }
    },
    "medical_records": {
      "timeline": [ /* all records, most recent first */ ],
      "by_type": { "PRESCRIPTION": [...], "ALLERGY": [...] },
      "active_allergies": [ /* allergy records */ ],
      "critical_or_high": [ /* severity CRITICAL or HIGH */ ],
      "recent_30_days": [ /* records in last 30 days */ ]
    }
  }
}
```

---

## B.13  Leave a Review for the Patient

Uses the generic Reviews API. Call after `status = COMPLETED` and `can_leave_review = true` on the history item.

**`POST /api/reviews/`**

```json
{
  "reviewed_content_type": "user",
  "reviewed_object_id": "<patient_user_id>",
  "context_content_type": "nurseservicerequest",
  "context_object_id": "<request_id>",
  "rating": 5,
  "text": "Patient was punctual, cooperative, and provided clear medical history.",
  "title": "Great patient"
}
```

| Field | Note |
|-------|------|
| `reviewed_content_type` | `"user"` for the patient |
| `reviewed_object_id` | `patient_user` field from the request object (User ID as string) |
| `context_content_type` | `"nurseservicerequest"` |
| `context_object_id` | `NurseServiceRequest.id` as string |

The unique constraint `(reviewer, reviewed_object, context_object)` prevents submitting twice for the same request.

---

## B.14  Report a Patient

**`POST /api/reports/`**

```json
{
  "reported_content_type": "user",
  "reported_object_id": "<patient_user_id>",
  "reason": "INAPPROPRIATE_BEHAVIOR",
  "description": "Patient was verbally abusive during the home visit.",
  "priority": "HIGH"
}
```

---

## B.15  Nurse WebSocket Events

Subscribe to `user_{user_id}_nurse_requests` for personal events and `city_{city}_requests` for new requests in the nurse's city.

### Events received by nurse

| Event type | When fired | Key payload fields |
|-----------|-----------|-------------------|
| `nurse_request_new` | New patient request in city | `request` (full object), `message` |
| `nurse_request_accepted` | Patient accepted nurse's offer | `request`, `message` |
| `nurse_request_in_progress` | (sent back to confirm start) | `request` |
| `nurse_request_completed` | (sent to request group) | `request` |
| `nurse_request_cancelled` | Patient cancelled the request | `request`, `cancelled_by`, `reason` |
| `nurse_offer_declined` | Patient declined nurse's specific offer | `request`, `reason`, `message` |
| `nurse_review_received` | Patient left a review | `review_id`, `rating`, `text`, `message` |
| `nurse_rating_updated` | Aggregate rating changed | `average_rating`, `review_count`, `message` |

### Sample WS payload — new request in city

```json
{
  "type": "nurse_request_new",
  "data": {
    "request": {
      "id": 42,
      "service_name": "Home Blood Draw",
      "patient_offered_price": "900.00",
      "city": "Algiers",
      "latitude": "36.737232",
      "longitude": "3.086472",
      "status": "SEARCHING",
      "created_at": "2025-05-11T10:00:00Z"
    },
    "message": "New nursing request: Home Blood Draw"
  }
}
```

### Sample WS payload — offer accepted

```json
{
  "type": "nurse_request_accepted",
  "data": {
    "request": { /* full request with status=ACCEPTED and accepted_nurse set */ },
    "message": "Yacine B. accepted your offer"
  }
}
```

### Sample WS payload — review received

```json
{
  "type": "nurse_review_received",
  "data": {
    "review_id": "uuid-here",
    "rating": 5,
    "text": "Very professional and gentle, highly recommend",
    "message": "Yacine B. left you a review"
  }
}
```

---

---

# Error Code Reference

| Code | Category | Meaning |
|------|----------|---------|
| `NR1001` | Service | Service not found |
| `NR1002` | Service | Service is inactive |
| `NR1003` | Service | Not a nursing service |
| `NR1004` | Service | Service not available for on-demand |
| `NR1005` | Service | Nurse already added this service to profile |
| `NR1006` | Service | Service not in nurse's profile |
| `NR2001` | Price | Offered price below base price |
| `NR2002` | Price | Counter-offer below patient's offered price |
| `NR2003` | Price | Invalid price value |
| `NR3001` | Request | Request not found |
| `NR3002` | Request | Not the request owner |
| `NR3003` | Request | Invalid status for this action |
| `NR3004` | Request | Already cancelled |
| `NR3005` | Request | Already accepted |
| `NR3006` | Request | Already completed |
| `NR3007` | Request | Nurse doesn't offer the required service |
| `NR4001` | Offer | Offer not found |
| `NR4002` | Offer | Offer no longer available |
| `NR4003` | Offer | Nurse already submitted an offer |
| `NR4004` | Offer | Offer has expired |
| `NR5001` | Location | Location coordinates required |
| `NR5002` | Location | Invalid coordinates |
| `NR5003` | Location | City is required |
| `NR5004` | Location | Address not found |
| `NR6001` | Auth | Not authenticated |
| `NR6002` | Auth | User is not a patient |
| `NR6003` | Auth | User is not a nurse |
| `NR6004` | Auth | Nurse profile not found |
| `NR6005` | Auth | Nurse is not verified/approved |

---

# Notification Types Reference

| FCM / In-app type | Who receives | When |
|-------------------|-------------|------|
| `NURSE_REQUEST_NEW` | Nearby nurses | Patient creates request |
| `NURSE_REQUEST_OFFER` | Patient | Nurse accepts at patient price |
| `NURSE_REQUEST_COUNTER_OFFER` | Patient | Nurse submits counter-offer |
| `NURSE_REQUEST_ACCEPTED` | Nurse | Patient accepts nurse's offer |
| `NURSE_REQUEST_IN_PROGRESS` | Patient | Nurse marks service started |
| `NURSE_REQUEST_COMPLETED` | Patient | Nurse marks service completed |
| `NURSE_REQUEST_CANCELLED` | Nurse or Patient | Either party cancels |

---

# Location & Geospatial System

## How nurses receive new request notifications

1. Patient creates request → `notify_new_request()` is called on `transaction.on_commit`
2. `get_nurses_within_radius(lat, lon, 30km)` queries **`NurseLocation`** table  
   - Only nurses with `NurseLocation.is_active = True` are considered
   - Distance calculated with Haversine formula
   - Respects `nurse.service_area_km` (each nurse's personal max radius)
3. Each qualifying nurse receives FCM push with distance info

## How the available-requests feed is filtered for nurses

`NurseAvailableRequestsViewSet.get_queryset()`:
1. Gets nurse's **primary WORK or CLINIC address** from `Address` table (ContentType-linked to User)
2. Calculates Haversine distance for each open request
3. Filters to requests within `nurse.service_area_km` (default 50 km)

> **Both mechanisms need the nurse to have location data.** If a nurse has no `NurseLocation` row and no WORK address, they receive city-wide FCM (distance=unknown) and see all open requests in the city (no radius filter). This is the fallback — not ideal.

## Location update flow (required implementation)

```
Nurse opens app → App requests GPS → PATCH /api/nurse-requests/nurse/location/ 
                                              (see Gaps section)
App sends location every 5 min while active → Backend updates NurseLocation
Nurse goes offline → PATCH is_active=false
```

---

# Complete Request Lifecycle (State Machine Summary)

```
Patient                                     Server                         Nurse
  |                                           |                              |
  |--POST /patient/nurse-requests/----------->|                              |
  |                                           |--WS city broadcast---------->|
  |                                           |--FCM to nearby nurses------->|
  |<--WS: nurse_request_new (confirmation)----|                              |
  |                                    status=SEARCHING                      |
  |                                           |                              |
  |                                           |<-POST /nurse/available-requests/{id}/accept/
  |<--FCM+WS: nurse_request_offer-------------|                              |
  |                                    status=NURSE_RESPONDED                |
  |                                           |                              |
  |--POST /patient/nurse-requests/{id}/accept/|                              |
  |                                           |--FCM+WS: request_accepted--->|
  |<--WS: nurse_request_accepted (confirm)----|                              |
  |                                    status=ACCEPTED                       |
  |                                           |                              |
  |                                           |<-POST /nurse/request-history/{id}/start/
  |<--FCM+WS: nurse_request_in_progress-------|                              |
  |                                    status=IN_PROGRESS                    |
  |                                           |                              |
  |                                           |<-POST /nurse/request-history/{id}/complete/
  |<--FCM+WS: nurse_request_completed---------|                              |
  |                                    status=COMPLETED                      |
  |                                           |                              |
  |--POST /api/reviews/ (rate nurse)--------->|                              |
  |                                           |--FCM: nurse_review_received->|
  |                                           |--WS:  nurse_review_received->|
  |                                           |--WS:  nurse_rating_updated-->|
```

---

# Known Gaps & Missing Endpoints

These are items identified during audit that need to be implemented before the feature is fully production-ready.

## Gap 1 — Nurse Location Update Endpoint (CRITICAL)

**Status:** `NurseLocation` model exists but no REST endpoint to update it.

**Add to providers or nurse_requests app:**

```
PATCH /api/nurse-requests/nurse/location/
Body: { "latitude": "36.74", "longitude": "3.09", "accuracy_meters": 8, "is_active": true }
```

Mobile should call this:
- Every 5 minutes while nurse is marked "Available"
- Immediately when nurse opens the app
- With `is_active=false` when nurse marks themselves offline

---

## Gap 2 — AcceptOfferSerializer Rejects Counter-Offers

**File:** [nurse_requests/serializers.py](nurse_requests/serializers.py#L343)

The `validate_offer_id` method raises `ValidationError` if `offer.status != OfferStatus.PENDING`. This means a patient **cannot accept a counter-offer** — only PENDING (accept-at-patient-price) offers can be accepted.

**Fix required:**
```python
# Change:
if offer.status != OfferStatus.PENDING:
# To:
if offer.status not in (OfferStatus.PENDING, OfferStatus.COUNTER_OFFERED):
```

---

## Gap 3 — Nurse Location Update via NurseLocation (services.py)

**File:** [nurse_requests/services.py](nurse_requests/services.py#L141)

`get_nurses_within_radius()` accesses `nurse.current_location` which is the `NurseLocation` OneToOne relation. Without Gap 1 being fixed, nurses that don't have a `NurseLocation` row (or have `is_active=False`) will not receive FCM notifications for new requests, even if they are nearby.

---

## Gap 4 — Offer Expiry: No Timeout Mechanism

There is no automatic expiry of `PENDING`/`COUNTER_OFFERED` offers after a time limit. Offers remain open indefinitely until the patient acts or cancels.

**Recommendation:** Add a Celery beat task (or a scheduled management command via cron) that expires offers older than N minutes and moves the request back to `SEARCHING` if all offers expire. Since there is no Celery, this could be a lightweight management command run every 5 minutes via cron.

---

## Gap 5 — No Patient Review Trigger for Nurse → Patient Review

When the nurse's `can_leave_review = true` in the history endpoint, the nurse can call `POST /api/reviews/` with `reviewed_content_type = "user"` and `reviewed_object_id = patient_user_id`. However, there is no FCM notification sent to the patient when a nurse reviews them.

**Add to notifications.py:** `notify_patient_review_received()` — fires when `reviewed_content_type = user`.

---

## Gap 6 — City-Channel Broadcast Uses Exact Lowercase City Name

**File:** [nurse_requests/notifications.py](nurse_requests/notifications.py#L103)

City group name: `city_{city.lower().replace(' ', '_')}_requests`

If a nurse joins `city_algiers_requests` but the patient submits city as `"Alger"`, the nurse will not receive the broadcast. Mobile apps must normalize city names before submission.

**Recommendation:** Maintain a city whitelist/enum, or use wilaya codes instead of city names for channel routing.

---

## Gap 7 — Python-Level Distance Filtering (O(N) queries)

**File:** [nurse_requests/views.py](nurse_requests/views.py#L1144)

`NurseAvailableRequestsViewSet.get_queryset()` pulls all requests into Python and calculates distances in a loop. For high-volume deployments this is a bottleneck.

**Recommendation:** Use PostGIS `ST_Distance` or store a `geography` field; alternatively use a bounding-box pre-filter (lat/lon range) before the Haversine loop.

---

## Gap 8 — `_ws_to_provider` Calls `send_to_patient`

**File:** [nurse_requests/notifications.py](nurse_requests/notifications.py#L535)

The `_ws_to_provider` method calls `WebSocketBroadcaster.send_to_patient()` instead of `send_to_provider()`. This works only because both methods broadcast to `user_{id}_nurse_requests`, but it's semantically incorrect and should be fixed.

---

## Gap 9 — No Pagination on Patient Request List

`PatientNurseRequestViewSet.list()` returns all requests without pagination. A patient with many historical requests will receive them all in one response.

**Fix:** Add `pagination_class = StandardPagination` to the viewset.

---

## Gap 10 — Review for Counter-Offer Not Reflected in `can_leave_review`

`can_leave_review` in `NurseServiceRequestDetailSerializer` checks for any `ACTIVE` review regardless of counter-offer status. This is correct. But the nurse's `can_leave_review` in `NurseRequestHistorySerializer` also uses the right logic. No bug — noted for verification.

---

# Quick Reference — URL Map

## Patient App

| Method | URL | Action |
|--------|-----|--------|
| GET | `/api/nurse-requests/services/` | Browse nursing services |
| GET | `/api/nurse-requests/services/{id}/` | Service detail + nurse count |
| GET | `/api/nurse-requests/patient/nurse-requests/` | My requests |
| POST | `/api/nurse-requests/patient/nurse-requests/` | Create request |
| GET | `/api/nurse-requests/patient/nurse-requests/{id}/` | Request detail |
| POST | `/api/nurse-requests/patient/nurse-requests/{id}/accept/` | Accept offer |
| POST | `/api/nurse-requests/patient/nurse-requests/{id}/decline_offer/` | Decline one offer |
| POST | `/api/nurse-requests/patient/nurse-requests/{id}/cancel/` | Cancel request |
| GET | `/api/nurse-requests/patient/nurse-requests/{id}/nurse-profile/{nurse_id}/` | View nurse profile |
| GET | `/api/nurse-requests/patient/nurse-requests/{id}/nurse-history/{nurse_id}/` | View nurse history |
| GET | `/api/nurse-requests/patient/nurse-requests/saved-addresses/` | My saved addresses |
| POST | `/api/nurse-requests/patient/nurse-requests/use-saved-address/` | Create from saved address |
| POST | `/api/reviews/` | Leave review for nurse |
| POST | `/api/reports/` | Report nurse |

## Nurse App

| Method | URL | Action |
|--------|-----|--------|
| GET | `/api/nurse-requests/nurse/my-services/` | My profile services |
| POST | `/api/nurse-requests/nurse/my-services/add/` | Add service to profile |
| PATCH | `/api/nurse-requests/nurse/my-services/{id}/availability/` | Toggle availability |
| DELETE | `/api/nurse-requests/nurse/my-services/{id}/remove/` | Remove service |
| GET | `/api/nurse-requests/nurse/available-requests/` | Available requests in area |
| GET | `/api/nurse-requests/nurse/available-requests/{id}/` | Single request detail |
| POST | `/api/nurse-requests/nurse/available-requests/{id}/accept/` | Accept at patient price |
| POST | `/api/nurse-requests/nurse/available-requests/{id}/counter-offer/` | Counter-offer |
| POST | `/api/nurse-requests/nurse/available-requests/{id}/reject/` | Dismiss request |
| GET | `/api/nurse-requests/nurse/my-offers/` | My submitted offers |
| GET | `/api/nurse-requests/nurse/request-history/` | My accepted/completed history |
| GET | `/api/nurse-requests/nurse/request-history/{id}/` | History detail |
| POST | `/api/nurse-requests/nurse/request-history/{id}/start/` | Mark service started |
| POST | `/api/nurse-requests/nurse/request-history/{id}/complete/` | Mark service completed |
| GET | `/api/nurse-requests/nurse/request-history/{id}/patient-folder/` | Patient medical folder |
| POST | `/api/reviews/` | Leave review for patient |
| POST | `/api/reports/` | Report patient |
