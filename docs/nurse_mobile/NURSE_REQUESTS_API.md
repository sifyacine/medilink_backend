# On-Demand Nursing Service API - Nurse Mobile App

## Overview

This documentation covers the **on-demand nursing service** feature for the Nurse Mobile App. Nurses can view patient requests, make offers or counter-offers, accept jobs, and manage their service profiles.

**Base URL:** `https://dzmedilink.duckdns.org/api/`

---

## 👩‍⚕️ Complete Nurse Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NURSE APP - REQUEST HANDLING FLOW                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │                    ONE-TIME SETUP                         │              │
│  │  (Required before nurse can receive any requests)         │              │
│  ├──────────────────────────────────────────────────────────┤              │
│  │  1. View available nursing services                       │              │
│  │  2. Add services nurse wants to offer to their profile    │              │
│  │  3. Set custom prices if desired                          │              │
│  └──────────────────────────────────────────────────────────┘              │
│                              │                                              │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │                    ACTIVE MODE                            │              │
│  │  (Nurse is online and ready to receive requests)          │              │
│  ├──────────────────────────────────────────────────────────┤              │
│  │                                                           │              │
│  │  ┌─────────────────┐                                     │              │
│  │  │ Available       │◀── WebSocket/Polling                │              │
│  │  │ Requests List   │    New requests appear here         │              │
│  │  └────────┬────────┘                                     │              │
│  │           │                                               │              │
│  │           ▼                                               │              │
│  │  ┌─────────────────────────────────────────────────────┐ │              │
│  │  │               VIEW REQUEST DETAILS                  │ │              │
│  │  │  Patient: Ahmed B.                                  │ │              │
│  │  │  Service: Wound Dressing                            │ │              │
│  │  │  Location: 123 Main St (3.5 km away)               │ │              │
│  │  │  Offered Price: 1500 DA                              │ │              │
│  │  └─────────────────────────────────────────────────────┘ │              │
│  │           │                                               │              │
│  │           ▼                                               │              │
│  │  ┌───────────┬───────────┬───────────┐                  │              │
│  │  │  ACCEPT   │  COUNTER  │  REJECT   │                  │              │
│  │  │ 1500 DA   │  OFFER    │           │                  │              │
│  │  │           │  2000 DA+ │           │                  │              │
│  │  └─────┬─────┴─────┬─────┴─────┬─────┘                  │              │
│  │        │           │           │                         │              │
│  │        ▼           ▼           ▼                         │              │
│  │   ┌─────────┐ ┌─────────┐  ┌─────────┐                  │              │
│  │   │ Offer   │ │ Offer   │  │ Request │                  │              │
│  │   │ Sent!   │ │ Sent!   │  │ Removed │                  │              │
│  │   │ Wait... │ │ Wait... │  │from list│                  │              │
│  │   └────┬────┘ └────┬────┘  └─────────┘                  │              │
│  │        │           │                                     │              │
│  │        └─────┬─────┘                                     │              │
│  │              ▼                                            │              │
│  │   ┌──────────────────────────────────────┐               │              │
│  │   │        WAITING FOR PATIENT           │               │              │
│  │   │   Patient may accept your offer      │               │              │
│  │   │   or choose another nurse            │               │              │
│  │   └──────────────────────────────────────┘               │              │
│  │              │                                            │              │
│  │              ▼                                            │              │
│  │   ┌────────────────────┐  ┌────────────────────┐         │              │
│  │   │ 🎉 OFFER ACCEPTED! │  │ ❌ OFFER REJECTED  │         │              │
│  │   │ Go to patient      │  │ Patient chose      │         │              │
│  │   │ location           │  │ another nurse      │         │              │
│  │   └─────────┬──────────┘  └────────────────────┘         │              │
│  │             │                                             │              │
│  │             ▼                                             │              │
│  │   ┌──────────────────────────────────────┐               │              │
│  │   │        SERVICE IN PROGRESS           │               │              │
│  │   │   [Start Service] → [Complete]       │               │              │
│  │   └──────────────────────────────────────┘               │              │
│  │                                                           │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication

All endpoints require authentication with a Bearer token:

```http
Authorization: Token your_auth_token_here
```

---

## API Endpoints Summary

### Profile Service Management
| Action | Endpoint | Method |
|--------|----------|--------|
| View my services & available services | `/api/nurse-requests/nurse/my-services/` | GET |
| Add service to profile | `/api/nurse-requests/nurse/my-services/add/` | POST |
| Remove service from profile | `/api/nurse-requests/nurse/my-services/{service_id}/remove/` | DELETE |
| Update service availability | `/api/nurse-requests/nurse/my-services/{service_id}/availability/` | PATCH |

### Request Handling
| Action | Endpoint | Method |
|--------|----------|--------|
| View available requests | `/api/nurse-requests/nurse/available-requests/` | GET |
| Get request details | `/api/nurse-requests/nurse/available-requests/{id}/` | GET |
| Accept at patient's price | `/api/nurse-requests/nurse/available-requests/{id}/accept/` | POST |
| Make counter offer | `/api/nurse-requests/nurse/available-requests/{id}/counter-offer/` | POST |
| Reject request | `/api/nurse-requests/nurse/available-requests/{id}/reject/` | POST |

### My Offers & Jobs
| Action | Endpoint | Method |
|--------|----------|--------|
| View my submitted offers | `/api/nurse-requests/nurse/my-offers/` | GET |
| Start service | `/api/nurse-requests/patient/nurse-requests/{id}/start/` | POST |
| Complete service | `/api/nurse-requests/patient/nurse-requests/{id}/complete/` | POST |

---

## ⚠️ CRITICAL: One-Time Setup Required

**Nurses will ONLY see requests for services they have added to their profile!**

Before a nurse can receive any on-demand requests, they must:
1. View available nursing services
2. Add the services they want to offer
3. Set custom prices if desired

---

## Profile Services Management

### View My Services & Available Services

```http
GET /api/nurse-requests/nurse/my-services/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "success": true,
    "my_services": [
        {
            "id": 1,
            "service_id": 1,
            "title": "Wound Dressing",
            "description": "Professional wound care and dressing change",
            "base_price": "50.00",
            "custom_price": null,
            "effective_price": "50.00",
            "duration_minutes": 30,
            "is_available": true,
            "is_on_demand": true,
            "created_at": "2026-01-15T10:00:00Z"
        }
    ],
    "my_services_count": 1,
    "available_to_add": [
        {
            "id": 2,
            "name": "IV Therapy",
            "description": "Intravenous fluid and medication administration",
            "base_price": "100.00",
            "duration_minutes": 60
        },
        {
            "id": 3,
            "name": "Injection",
            "description": "Intramuscular or subcutaneous injection",
            "base_price": "30.00",
            "duration_minutes": 15
        }
    ],
    "available_to_add_count": 2,
    "message": "Add services to receive on-demand requests for those services"
}
```

**UI: My Services Screen**
```
┌─────────────────────────────────────┐
│          My Services                │
├─────────────────────────────────────┤
│                                     │
│  SERVICES I OFFER (1)               │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────────┐│
│  │ ✅ Wound Dressing               ││
│  │ Base: 1000 DA | My Price: 1000 DA ││
│  │ [Available ▼]  [Remove]         ││
│  └─────────────────────────────────┘│
│                                     │
│  AVAILABLE TO ADD (2)               │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────────┐│
│  │ ➕ IV Therapy                   ││
│  │ Base Price: 2000 DA             ││
│  │ [Add to My Services]            ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │ ➕ Injection                    ││
│  │ Base Price: 600 DA              ││
│  │ [Add to My Services]            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### Add Service to Profile

```http
POST /api/nurse-requests/nurse/my-services/add/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "service_id": 2,
    "custom_price": "120.00"
}
```

> **Note:** `custom_price` is optional. If not provided, the service's base price is used.

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "id": 2,
        "service_id": 2,
        "title": "IV Therapy",
        "description": "Intravenous fluid and medication administration",
        "base_price": "100.00",
        "custom_price": "120.00",
        "effective_price": "120.00",
        "duration_minutes": 60,
        "is_available": true,
        "is_on_demand": true
    },
    "message": "Successfully added \"IV Therapy\" to your profile. You will now receive requests for this service."
}
```

---

### Remove Service from Profile

```http
DELETE /api/nurse-requests/nurse/my-services/{service_id}/remove/
Authorization: Token your_auth_token
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Removed \"IV Therapy\" from your profile. You will no longer receive requests for this service."
}
```

---

### Update Service Availability

Toggle availability or update custom pricing:

```http
PATCH /api/nurse-requests/nurse/my-services/{service_id}/availability/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "is_available": false,
    "custom_price": "130.00"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "id": 2,
        "service_id": 2,
        "title": "IV Therapy",
        "base_price": "100.00",
        "custom_price": "130.00",
        "effective_price": "130.00",
        "is_available": false
    },
    "message": "Service is now unavailable"
}
```

---

## Viewing Available Requests

### List Available Requests

Shows requests only for services the nurse has added to their profile.

```http
GET /api/nurse-requests/nurse/available-requests/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "success": true,
    "count": 3,
    "results": [
        {
            "id": 42,
            "service_name": "Wound Dressing",
            "service_description": "Professional wound care and dressing change",
            "patient_name": "Ahmed B.",
            "patient_offered_price": "75.00",
            "base_price": "50.00",
            "latitude": "36.752500",
            "longitude": "3.042000",
            "city": "Algiers",
            "address_line": "123 Main Street, Algiers Center",
            "notes": "Please ring doorbell twice",
            "created_at": "2026-01-31T14:30:00Z",
            "my_offer": null
        },
        {
            "id": 43,
            "service_name": "IV Therapy",
            "service_description": "Intravenous fluid and medication administration",
            "patient_name": "Fatima H.",
            "patient_offered_price": "110.00",
            "base_price": "100.00",
            "latitude": "36.755000",
            "longitude": "3.050000",
            "city": "Algiers",
            "address_line": "456 Center Avenue",
            "notes": "",
            "created_at": "2026-01-31T14:35:00Z",
            "my_offer": null
        }
    ],
    "your_active_services_count": 2,
    "message": "Showing requests for your 2 active service(s)"
}
```

**UI: Available Requests**
```
┌─────────────────────────────────────┐
│       Available Requests (3)        │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 🔵 NEW                          ││
│  │ Wound Dressing                  ││
│  │ 👤 Ahmed B.                     ││
│  │ 📍 123 Main St (3.5 km)         ││
│  │ 💰 Offering: 1500 DA             ││
│  │ ⏰ 5 min ago                    ││
│  │                                 ││
│  │ [View Details]                  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 🔵 NEW                          ││
│  │ IV Therapy                      ││
│  │ 👤 Fatima H.                    ││
│  │ 📍 456 Center Ave (8.2 km)      ││
│  │ 💰 Offering: 2500 DA            ││
│  │ ⏰ 12 min ago                   ││
│  │                                 ││
│  │ [View Details]                  ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### Real-Time Request Updates

#### WebSocket Connection

```javascript
// Connect to WebSocket for real-time new requests
const ws = new WebSocket('wss://dzmedilink.duckdns.org/ws/nurse-requests/available/');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'new_request':
            // Add new request to the list
            addRequestToList(data.request);
            // Show push notification
            showNotification("New nursing request nearby!");
            break;
        case 'request_cancelled':
            // Remove request from list
            removeRequestFromList(data.request_id);
            break;
        case 'offer_accepted':
            // Your offer was accepted!
            showAcceptedNotification(data.request);
            break;
        case 'offer_rejected':
            // Patient chose another nurse
            markOfferRejected(data.request_id);
            break;
    }
};

// Keep-alive ping
setInterval(() => {
    ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
}, 30000);
```

#### Polling Alternative

If WebSocket unavailable, poll every 10-15 seconds:

```http
GET /api/nurse-requests/nurse/available-requests/
Authorization: Token your_auth_token
```

---

## Responding to Requests

### View Request Details

```http
GET /api/nurse-requests/nurse/available-requests/{id}/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "id": 42,
    "service": {
        "id": 1,
        "name": "Wound Dressing",
        "description": "Professional wound care and dressing change",
        "base_price": "50.00"
    },
    "patient_name": "Ahmed B.",
    "patient_offered_price": "75.00",
    "base_price": "50.00",
    "latitude": "36.752500",
    "longitude": "3.042000",
    "city": "Algiers",
    "address_line": "123 Main Street, Algiers Center",
    "notes": "Please ring doorbell twice",
    "status": "SEARCHING",
    "created_at": "2026-01-31T14:30:00Z",
    "my_offer": null
}
```

**UI: Request Details Screen**
```
┌─────────────────────────────────────┐
│       Request Details               │
├─────────────────────────────────────┤
│                                     │
│  SERVICE                            │
│  Wound Dressing                     │
│  Professional wound care service    │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  PATIENT                            │
│  👤 Ahmed B.                        │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  LOCATION                           │
│  📍 123 Main Street, Algiers        │
│  📏 Distance: 3.5 km                │
│  🚗 ~25 min to arrive               │
│  [Open in Maps]                     │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  PRICING                            │
│  Base Price: 1000 DA                 │
│  Patient Offers: 1500 DA             │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  NOTES                              │
│  "Please ring doorbell twice"       │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  [Accept at 1500 DA] [Counter Offer]│
│  [Reject]                           │
│                                     │
└─────────────────────────────────────┘
```

---

### Option A: Accept at Patient's Price

Accept the request at the patient's offered price:

```http
POST /api/nurse-requests/nurse/available-requests/{id}/accept/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "estimated_arrival_time": "00:25:00",
    "notes": "On my way!",
    "distance_km": 3.5
}
```

**Request Body Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `estimated_arrival_time` | string (HH:MM:SS) | No | Estimated time to reach patient |
| `notes` | string | No | Message for the patient |
| `distance_km` | decimal | No | Distance from nurse to patient |

**Response (201 Created):**
```json
{
    "success": true,
    "message": "Request accepted successfully",
    "offer_id": 123,
    "offered_price": "75.00"
}
```

---

### Option B: Make Counter Offer

If you want to charge more than the patient's offered price:

```http
POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "offered_price": "100.00",
    "estimated_arrival_time": "00:45:00",
    "notes": "Traffic is heavy today",
    "distance_km": 8.2
}
```

**Request Body Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `offered_price` | decimal | **Yes** | Your counter-offer price |
| `estimated_arrival_time` | string (HH:MM:SS) | No | Estimated time to reach patient |
| `notes` | string | No | Reason for counter-offer |
| `distance_km` | decimal | No | Distance from nurse to patient |

**Validation Rules:**
- `offered_price` must be ≥ patient's `patient_offered_price`
- `offered_price` must be ≥ service's `base_price`

**Response (201 Created):**
```json
{
    "success": true,
    "message": "Counter offer submitted successfully",
    "offer_id": 124,
    "offered_price": "100.00"
}
```

**UI: Counter Offer Dialog**
```
┌─────────────────────────────────────┐
│       Make Counter Offer            │
├─────────────────────────────────────┤
│                                     │
│  Patient offered: 1500 DA           │
│                                     │
│  Your price:                        │
│  ┌─────────────────────────────────┐│
│  │ DA [  2000  ]                   ││
│  └─────────────────────────────────┘│
│  ℹ️ Must be ≥ 1500 DA                │
│                                     │
│  Reason (optional):                 │
│  ┌─────────────────────────────────┐│
│  │ Traffic is heavy today          ││
│  └─────────────────────────────────┘│
│                                     │
│  [Submit Counter Offer]  [Cancel]   │
│                                     │
└─────────────────────────────────────┘
```

---

### Option C: Reject Request

If you don't want to take this job:

```http
POST /api/nurse-requests/nurse/available-requests/{id}/reject/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "reason": "Too far from my location"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "message": "Request rejected"
}
```

---

## Managing My Offers & History

### View Submitted Offers (Full History)

See all requests where you've submitted an offer, including full history:

```http
GET /api/nurse-requests/nurse/my-offers/
Authorization: Token your_auth_token
```

**Query Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `status` | Filter by request status | `?status=COMPLETED` |
| `offer_status` | Filter by your offer status | `?offer_status=REJECTED` |
| `is_active` | Show only active requests | `?is_active=true` |
| `is_history` | Show only historical requests | `?is_history=true` |

**Filter Examples:**
- All my offers: `/api/nurse-requests/nurse/my-offers/`
- Active only: `/api/nurse-requests/nurse/my-offers/?is_active=true`
- History only: `/api/nurse-requests/nurse/my-offers/?is_history=true`
- Rejected offers: `/api/nurse-requests/nurse/my-offers/?offer_status=REJECTED`
- Completed jobs: `/api/nurse-requests/nurse/my-offers/?status=COMPLETED`
- Cancelled by patient: `/api/nurse-requests/nurse/my-offers/?status=CANCELLED`

**Response:**
```json
{
    "success": true,
    "count": 5,
    "results": [
        {
            "id": 42,
            "service_name": "Wound Dressing",
            "patient_name": "Ahmed B.",
            "patient_offered_price": "1500.00",
            "my_offer": {
                "id": 123,
                "offered_price": "1500.00",
                "status": "PENDING",
                "estimated_arrival_time": "00:25:00",
                "created_at": "2026-01-31T14:35:00Z"
            },
            "request_status": "NURSE_RESPONDED",
            "city": "Algiers"
        },
        {
            "id": 38,
            "service_name": "IV Therapy",
            "patient_name": "Fatima H.",
            "patient_offered_price": "2500.00",
            "my_offer": {
                "id": 120,
                "offered_price": "2500.00",
                "status": "ACCEPTED"
            },
            "request_status": "COMPLETED",
            "final_price": "2500.00",
            "city": "Algiers"
        },
        {
            "id": 35,
            "service_name": "Injection",
            "patient_name": "Karim S.",
            "patient_offered_price": "800.00",
            "my_offer": {
                "id": 115,
                "offered_price": "1000.00",
                "status": "REJECTED"
            },
            "request_status": "ACCEPTED",
            "final_price": "800.00",
            "city": "Oran",
            "note": "Patient chose another nurse"
        },
        {
            "id": 32,
            "service_name": "Wound Dressing",
            "patient_name": "Sara M.",
            "patient_offered_price": "1500.00",
            "my_offer": {
                "id": 110,
                "offered_price": "1500.00",
                "status": "PENDING"
            },
            "request_status": "CANCELLED",
            "city": "Algiers",
            "note": "Patient cancelled request"
        }
    ],
    "stats": {
        "total_offers": 5,
        "pending": 1,
        "accepted": 2
    }
}
```

---

## 📜 Offer History

Your offer history includes **all requests** you've ever responded to:

### What's Included in History

| Scenario | Offer Status | Request Status | Description |
|----------|--------------|----------------|-------------|
| ✅ **Job Completed** | `ACCEPTED` | `COMPLETED` | You completed the service |
| ❌ **Patient Chose Another** | `REJECTED` | `ACCEPTED` | Patient accepted another nurse |
| 🔄 **Counter-offer Rejected** | `REJECTED` | `ACCEPTED` | Your higher price was rejected |
| 🚫 **Patient Cancelled** | `PENDING` | `CANCELLED` | Patient cancelled before accepting |
| ⏳ **Waiting for Decision** | `PENDING` | Active | Patient hasn't decided yet |

### History UI Suggestion

```
┌─────────────────────────────────────┐
│         My Offer History            │
├─────────────────────────────────────┤
│                                     │
│  [All] [Active] [Completed] [Reject]│
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ ✅ IV Therapy                   ││
│  │ 31 Jan 2026 • 2,500 DA          ││
│  │ Patient: Fatima H.              ││
│  │ Status: COMPLETED               ││
│  │ Your offer: ACCEPTED ✓          ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ ❌ Injection                    ││
│  │ 28 Jan 2026 • 1,000 DA (yours)  ││
│  │ Patient: Karim S.               ││
│  │ Status: ACCEPTED (another nurse)││
│  │ Your offer: REJECTED            ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 🚫 Wound Dressing               ││
│  │ 25 Jan 2026 • 1,500 DA          ││
│  │ Patient: Sara M.                ││
│  │ Status: CANCELLED by patient    ││
│  │ Your offer was pending          ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### Note on Deletion

> ⚠️ **History records cannot be deleted.** They serve as audit records and are important for:
> - Service verification and proof of work
> - Dispute resolution
> - Performance tracking
> - Payment and earning history

---

**UI: My Offers Screen**
```
┌─────────────────────────────────────┐
│           My Offers                 │
├─────────────────────────────────────┤
│                                     │
│  PENDING (2)                        │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────────┐│
│  │ ⏳ Wound Dressing               ││
│  │ 👤 Ahmed B.                     ││
│  │ 💰 My offer: 1,500 DA           ││
│  │ Waiting for patient decision... ││
│  └─────────────────────────────────┘│
│                                     │
│  ACCEPTED (1)                       │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────────┐│
│  │ ✅ IV Therapy                   ││
│  │ 👤 Fatima H.                    ││
│  │ 💰 Final: 2,500 DA              ││
│  │ [Navigate] [Start Service]      ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## When Patient Accepts Your Offer

You'll receive a WebSocket notification:

```json
{
    "type": "offer_accepted",
    "request": {
        "id": 42,
        "status": "ACCEPTED",
        "patient_name": "Ahmed B.",
        "location": {
            "address_line": "123 Main Street, Algiers",
            "latitude": "36.752500",
            "longitude": "3.042000"
        },
        "final_price": "75.00",
        "patient_phone": "+213..."
    }
}
```

**Show Acceptance Screen:**
```
┌─────────────────────────────────────┐
│      🎉 Offer Accepted!             │
├─────────────────────────────────────┤
│                                     │
│  Patient Ahmed B. accepted          │
│  your offer!                        │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  Service: Wound Dressing            │
│  Final Price: 1500 DA                │
│                                     │
│  Location:                          │
│  📍 123 Main Street, Algiers        │
│                                     │
│  [📍 Navigate to Patient]           │
│                                     │
│  [📞 Call Patient]                  │
│                                     │
└─────────────────────────────────────┘
```

---

## Service Execution

### Start Service

When you arrive at the patient's location:

```http
POST /api/nurse-requests/patient/nurse-requests/{request_id}/start/
Authorization: Token your_auth_token
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "id": 42,
        "status": "IN_PROGRESS",
        "started_at": "2026-01-31T15:00:00Z"
    },
    "message": "Service started"
}
```

---

### Complete Service

When service is finished:

```http
POST /api/nurse-requests/patient/nurse-requests/{request_id}/complete/
Authorization: Token your_auth_token
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "id": 42,
        "status": "COMPLETED",
        "completed_at": "2026-01-31T15:30:00Z",
        "final_price": "75.00"
    },
    "message": "Service completed successfully"
}
```

---

## Request Status Reference

```
CREATED → SEARCHING → NURSE_RESPONDED → PATIENT_DECISION → ACCEPTED → IN_PROGRESS → COMPLETED
                                                         ↘ CANCELLED ↙
```

| Status | Description | Nurse Actions |
|--------|-------------|---------------|
| `SEARCHING` | Patient waiting for responses | Can Accept/Counter-offer/Reject |
| `NURSE_RESPONDED` | At least one nurse responded | Can still Accept/Counter-offer |
| `PATIENT_DECISION` | Multiple offers, patient choosing | Wait for decision |
| `ACCEPTED` | Your offer was accepted! | Navigate to patient, Start Service |
| `IN_PROGRESS` | Service being provided | Complete when done |
| `COMPLETED` | Service finished | No action needed |
| `CANCELLED` | Request cancelled | Removed from list |

---

## Offer Status Reference

| Status | Description |
|--------|-------------|
| `PENDING` | Waiting for patient to decide |
| `ACCEPTED` | Patient accepted your offer! |
| `REJECTED` | Patient chose another nurse |
| `COUNTER_OFFERED` | Your counter-offer is pending |
| `EXPIRED` | Offer expired (patient didn't respond) |

---

## WebSocket Events Reference

### Events Received by Nurse

#### New Request
```json
{
    "type": "new_request",
    "request": {
        "id": 42,
        "service_name": "Wound Dressing",
        "patient_name": "Ahmed B.",
        "patient_offered_price": "75.00",
        "city": "Algiers",
        "latitude": "36.752500",
        "longitude": "3.042000"
    }
}
```

#### Offer Accepted
```json
{
    "type": "offer_accepted",
    "request": {
        "id": 42,
        "status": "ACCEPTED",
        "patient_name": "Ahmed B.",
        "final_price": "75.00",
        "patient_phone": "+213..."
    }
}
```

#### Offer Rejected
```json
{
    "type": "offer_rejected",
    "request_id": 42,
    "message": "Patient chose another nurse"
}
```

#### Request Cancelled
```json
{
    "type": "request_cancelled",
    "request_id": 42,
    "reason": "Patient cancelled"
}
```

### Keep-Alive
```json
// Send
{"type": "ping", "timestamp": 1706709600}

// Receive
{"type": "pong", "timestamp": 1706709600}
```

---

## Error Codes Reference

All errors follow this format:

```json
{
    "success": false,
    "error": {
        "code": "NR1001",
        "message": "Human-readable error message",
        "details": { ... }
    }
}
```

### Common Errors for Nurses

| Code | Name | Description |
|------|------|-------------|
| `NR1001` | SERVICE_NOT_FOUND | Nursing service does not exist |
| `NR1002` | SERVICE_INACTIVE | Service is currently not active |
| `NR1003` | SERVICE_NOT_NURSING | Not a nursing service |
| `NR1004` | SERVICE_NOT_ON_DEMAND | Not available for on-demand |
| `NR1005` | SERVICE_ALREADY_ADDED | Already in your profile |
| `NR1006` | SERVICE_NOT_IN_PROFILE | Not in your profile |
| `NR2002` | PRICE_BELOW_PATIENT_OFFER | Counter offer below patient's price |
| `NR3001` | REQUEST_NOT_FOUND | Request not found |
| `NR3003` | REQUEST_INVALID_STATUS | Cannot perform action in current status |
| `NR3007` | REQUEST_SERVICE_NOT_IN_NURSE_PROFILE | Service not in your profile |
| `NR4003` | OFFER_ALREADY_SUBMITTED | Already submitted an offer |
| `NR6003` | NOT_NURSE | User is not a nurse |
| `NR6004` | NURSE_PROFILE_NOT_FOUND | Nurse profile incomplete |
| `NR6005` | NURSE_NOT_VERIFIED | Nurse not verified |

### Error Response Examples

**Service Not in Profile:**
```json
{
    "success": false,
    "error": {
        "code": "NR3007",
        "message": "You cannot respond to this request because you do not offer \"Wound Dressing\" service.",
        "details": {
            "service_id": 1,
            "service_name": "Wound Dressing",
            "action": "Add this service to your profile first"
        }
    }
}
```

**Counter Offer Too Low:**
```json
{
    "success": false,
    "error": {
        "code": "NR2002",
        "message": "Your counter offer must be at least the patient's offered price",
        "details": {
            "patient_offered_price": "75.00",
            "your_offer": "60.00"
        }
    }
}
```

**No Services in Profile (Warning):**
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

## Pricing Rules

1. **Patient** offers a price ≥ base price
2. **Nurse** can:
   - **Accept** at patient's price (instant offer)
   - **Counter-offer** at price ≥ patient's price
   - **Reject** (no price requirement)
3. **Patient** makes final decision
4. Once accepted, `final_price` is locked

---

## Quick Implementation Checklist

### One-Time Setup
- [ ] My Services screen showing added services
- [ ] Available services list with "Add" button
- [ ] Add service with optional custom price
- [ ] Toggle service availability
- [ ] Remove service from profile

### Request Handling
- [ ] Available requests list (filtered by profile services)
- [ ] Request details screen with patient info
- [ ] Accept at patient's price action
- [ ] Counter offer dialog with price input
- [ ] Reject request action
- [ ] Calculate distance/ETA from nurse location

### My Offers & Status
- [ ] My offers list grouped by status
- [ ] WebSocket for real-time updates
- [ ] Push notification for offer accepted
- [ ] Navigation integration to patient location
- [ ] Start service action
- [ ] Complete service action

### Real-Time
- [ ] WebSocket connection for new requests
- [ ] Polling fallback if WebSocket unavailable
- [ ] Push notifications for key events
