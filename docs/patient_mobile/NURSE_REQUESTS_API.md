# On-Demand Nursing Service API - Patient Mobile App

## Overview

This documentation covers the **on-demand nursing service** feature for the Patient Mobile App. Patients can request nursing services at their location, set their preferred price, and choose from nurses who respond to their request.

**Base URL:** `https://dzmedilink.duckdns.org/api/`

---

## 📱 Complete Patient Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PATIENT APP - NURSE REQUEST FLOW                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Step 1     │───▶│   Step 2     │───▶│   Step 3     │                  │
│  │   Browse     │    │   Select     │    │   Set Price  │                  │
│  │   Services   │    │   Location   │    │   & Details  │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │ Show list of │    │ Pick from    │    │ Enter price  │                  │
│  │ nursing      │    │ saved addr   │    │ (≥ base),    │                  │
│  │ services     │    │ OR use map   │    │ add notes    │                  │
│  └──────────────┘    └──────────────┘    └──────────────┘                  │
│                                                │                           │
│                                                ▼                           │
│                              ┌─────────────────────────────┐               │
│                              │         Step 4              │               │
│                              │   CREATE REQUEST & WAIT     │               │
│                              │   Status: SEARCHING         │               │
│                              │   Show "Finding nurses..."  │               │
│                              └─────────────────────────────┘               │
│                                                │                           │
│                                                ▼                           │
│                              ┌─────────────────────────────┐               │
│                              │         Step 5              │               │
│                              │   NURSES START RESPONDING   │               │
│                              │   Offers appear one by one  │               │
│                              │   via WebSocket/polling     │               │
│                              └─────────────────────────────┘               │
│                                                │                           │
│                                                ▼                           │
│                    ┌───────────────────────────┴───────────────────┐      │
│                    │                                               │      │
│                    ▼                                               ▼      │
│         ┌──────────────────┐                          ┌──────────────────┐│
│         │     Step 6a      │                          │     Step 6b      ││
│         │  ACCEPT OFFER    │                          │  CANCEL REQUEST  ││
│         │  Choose a nurse  │                          │  Changed mind    ││
│         └──────────────────┘                          └──────────────────┘│
│                    │                                                      │
│                    ▼                                                      │
│         ┌──────────────────┐    ┌──────────────────┐    ┌────────────────┐│
│         │     Step 7       │───▶│     Step 8       │───▶│    Step 9      ││
│         │ NURSE CONNECTED  │    │  SERVICE STARTS  │    │  COMPLETED     ││
│         │ Status: ACCEPTED │    │  IN_PROGRESS     │    │  Rate nurse    ││
│         └──────────────────┘    └──────────────────┘    └────────────────┘│
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication

All endpoints require authentication with a Bearer token:

```http
Authorization: Token your_auth_token_here
```

---

## API Endpoints Summary

| Action | Endpoint | Method |
|--------|----------|--------|
| Browse services | `/api/nurse-requests/services/` | GET |
| Get service details | `/api/nurse-requests/services/{id}/` | GET |
| Get saved addresses | `/api/nurse-requests/patient/nurse-requests/saved-addresses/` | GET |
| Create request (saved address) | `/api/nurse-requests/patient/nurse-requests/use-saved-address/` | POST |
| Create request (map location) | `/api/nurse-requests/patient/nurse-requests/` | POST |
| List my requests | `/api/nurse-requests/patient/nurse-requests/` | GET |
| Get request details | `/api/nurse-requests/patient/nurse-requests/{id}/` | GET |
| View nurse profile | `/api/nurse-requests/patient/nurse-requests/{id}/nurse-profile/{nurse_id}/` | GET |
| View nurse history | `/api/nurse-requests/patient/nurse-requests/{id}/nurse-history/{nurse_id}/` | GET |
| Accept nurse offer | `/api/nurse-requests/patient/nurse-requests/{id}/accept/` | POST |
| Cancel request | `/api/nurse-requests/patient/nurse-requests/{id}/cancel/` | POST |

---

## Step-by-Step Implementation

### Step 1: Browse Available Nursing Services

Display a list of available nursing services the patient can request.

```http
GET /api/nurse-requests/services/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "success": true,
    "count": 5,
    "results": [
        {
            "id": 1,
            "name": "Wound Dressing",
            "description": "Professional wound care and dressing change",
            "base_price": "1000.00",
            "duration_minutes": 30,
            "is_active": true,
            "icon": "wound-care"
        },
        {
            "id": 2,
            "name": "IV Therapy",
            "description": "Intravenous fluid and medication administration",
            "base_price": "2000.00",
            "duration_minutes": 60,
            "is_active": true,
            "icon": "iv-drip"
        },
        {
            "id": 3,
            "name": "Injection",
            "description": "Intramuscular or subcutaneous injection",
            "base_price": "30.00",
            "duration_minutes": 15,
            "is_active": true,
            "icon": "syringe"
        }
    ],
    "message": "Select a service to request a nurse"
}
```

**UI Elements to Display:**
- Service name
- Description
- Base price (minimum price patient must offer)
- Estimated duration
- Service icon

#### Get Service Details (Optional)

```http
GET /api/nurse-requests/services/{id}/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Wound Dressing",
        "description": "Professional wound care and dressing change",
        "base_price": "1000.00",
        "duration_minutes": 30,
        "is_active": true,
        "icon": "wound-care"
    },
    "available_nurses_count": 12,
    "message": "12 nurses available for this service"
}
```

---

### Step 2: Select Location

After selecting a service, the patient chooses where they need the nurse to come.

#### Option A: Use Saved Address

First, get the patient's saved addresses:

```http
GET /api/nurse-requests/patient/nurse-requests/saved-addresses/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "success": true,
    "count": 2,
    "results": [
        {
            "id": 5,
            "street": "123 Main Street",
            "city": "Algiers",
            "state": "Algiers Province",
            "country": "Algeria",
            "latitude": "36.752500",
            "longitude": "3.042000",
            "is_primary": true,
            "address_type": "HOME",
            "full_address": "123 Main Street, Algiers, Algiers Province, Algeria",
            "has_coordinates": true
        },
        {
            "id": 8,
            "street": "456 Business Avenue",
            "city": "Algiers",
            "state": "Algiers Province",
            "country": "Algeria",
            "latitude": "36.755000",
            "longitude": "3.050000",
            "is_primary": false,
            "address_type": "WORK",
            "full_address": "456 Business Avenue, Algiers, Algiers Province, Algeria",
            "has_coordinates": true
        }
    ],
    "message": "Select a saved address or choose location from map"
}
```

**UI Flow:**
```
┌─────────────────────────────────────┐
│      Where do you need service?     │
├─────────────────────────────────────┤
│                                     │
│  📍 Saved Addresses:                │
│  ┌─────────────────────────────────┐│
│  │ 🏠 Home (Primary)               ││
│  │ 123 Main Street, Algiers        ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │ 🏢 Work                         ││
│  │ 456 Business Avenue, Algiers    ││
│  └─────────────────────────────────┘│
│                                     │
│  ─────── OR ───────                 │
│                                     │
│  [📍 Select Location on Map]        │
│                                     │
└─────────────────────────────────────┘
```

#### Option B: Select from Map

If patient selects from map, collect:
- `latitude` - GPS latitude
- `longitude` - GPS longitude  
- `city` - City name
- `address_line` - Human-readable address

---

### Step 3: Set Price and Details

**UI Screen:**
```
┌─────────────────────────────────────┐
│       Request Details               │
├─────────────────────────────────────┤
│                                     │
│  Service: Wound Dressing            │
│  Location: 123 Main Street          │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  Your Offer:                        │
│  ┌─────────────────────────────────┐│
│  │ DA [  1500  ]                   ││
│  └─────────────────────────────────┘│
│  ℹ️ Minimum: 1000 DA (base price)    │
│                                     │
│  💡 Tip: Offering more may attract  │
│     nurses faster!                  │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  Notes (optional):                  │
│  ┌─────────────────────────────────┐│
│  │ Please ring doorbell twice...   ││
│  └─────────────────────────────────┘│
│                                     │
│  [       Create Request       ]     │
│                                     │
└─────────────────────────────────────┘
```

**Validation:**
- `patient_offered_price` must be ≥ `base_price`
- Show error if patient enters lower price

---

### Step 4: Create Request

#### Using Saved Address

```http
POST /api/nurse-requests/patient/nurse-requests/use-saved-address/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "service": 1,
    "patient_offered_price": "1500 DA",
    "address_id": 5,
    "notes": "Please ring doorbell twice"
}
```

#### Using Map Coordinates

```http
POST /api/nurse-requests/patient/nurse-requests/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "service": 1,
    "patient_offered_price": "1500 DA",
    "latitude": "36.7525",
    "longitude": "3.0420",
    "city": "Algiers",
    "address_line": "123 Main Street, Algiers Center",
    "notes": "Please ring doorbell twice"
}
```

**Response (201 Created):**
```json
{
    "success": true,
    "data": {
        "id": 42,
        "patient": 1,
        "patient_name": "Ahmed Ben Ali",
        "service": {
            "id": 1,
            "name": "Wound Dressing",
            "base_price": "1000.00"
        },
        "base_price": "1000.00",
        "patient_offered_price": "1500 DA",
        "final_price": null,
        "latitude": "36.752500",
        "longitude": "3.042000",
        "city": "Algiers",
        "address_line": "123 Main Street, Algiers Center",
        "status": "SEARCHING",
        "notes": "Please ring doorbell twice",
        "offers": [],
        "created_at": "2026-01-31T14:30:00Z"
    },
    "message": "Request created successfully. Searching for available nurses..."
}
```

**Show Waiting Screen:**
```
┌─────────────────────────────────────┐
│        Finding Nurses...            │
├─────────────────────────────────────┤
│                                     │
│           🔍                        │
│      (animated spinner)             │
│                                     │
│   Searching for available nurses    │
│   near your location...             │
│                                     │
│   Service: Wound Dressing           │
│   Your Offer: 1500 DA                │
│   Location: 123 Main Street         │
│                                     │
│                                     │
│   [Cancel Request]                  │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 5: Receiving Nurse Offers

Once the request is created, start listening for nurse offers.

#### WebSocket Connection (Recommended)

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket(`wss://dzmedilink.duckdns.org/ws/nurse-requests/${requestId}/`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'new_offer':
            // Add nurse offer to the list
            addOfferToList(data.offer);
            break;
        case 'request_updated':
            // Update request status
            updateRequestStatus(data.request);
            break;
        case 'request_cancelled':
            // Handle cancellation
            showCancellationMessage(data.reason);
            break;
    }
};

// Keep-alive ping
setInterval(() => {
    ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
}, 30000);
```

#### Polling Alternative (Fallback)

If WebSocket is not available, poll every 5-10 seconds:

```http
GET /api/nurse-requests/patient/nurse-requests/{id}/
Authorization: Token your_auth_token
```

**Response with Offers:**
```json
{
    "id": 42,
    "status": "NURSE_RESPONDED",
    "offers": [
        {
            "id": 123,
            "nurse_id": 5,
            "nurse_name": "Fatima H.",
            "nurse_rating": 4.8,
            "nurse_photo": "https://...",
            "offered_price": "1500 DA",
            "distance_km": "3.5",
            "estimated_arrival_time": "00:25:00",
            "notes": "",
            "status": "PENDING",
            "created_at": "2026-01-31T14:35:00Z"
        },
        {
            "id": 124,
            "nurse_id": 8,
            "nurse_name": "Ahmed K.",
            "nurse_rating": 4.5,
            "nurse_photo": "https://...",
            "offered_price": "2000.00",
            "distance_km": "8.2",
            "estimated_arrival_time": "00:45:00",
            "notes": "Traffic is heavy today",
            "status": "PENDING",
            "created_at": "2026-01-31T14:37:00Z"
        }
    ]
}
```

**UI: Display Offers:**
```
┌─────────────────────────────────────┐
│        Nurses Available             │
├─────────────────────────────────────┤
│                                     │
│  2 nurses have responded            │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👩‍⚕️ Fatima H.                   ││
│  │ ⭐ 4.8 Rating                   ││
│  │ 📍 3.5 km away                  ││
│  │ ⏱️ ~25 min arrival              ││
│  │ 💰 1500 DA (Your price) ✅       ││
│  │ [View Profile] [Accept]         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👨‍⚕️ Ahmed K.                    ││
│  │ ⭐ 4.5 Rating                   ││
│  │ 📍 8.2 km away                  ││
│  │ ⏱️ ~45 min arrival              ││
│  │ 💰 2000 DA (Counter-offer) ⬆️   ││
│  │ "Traffic is heavy today"        ││
│  │ [View Profile] [Accept]         ││
│  └─────────────────────────────────┘│
│                                     │
│  [Cancel Request]                   │
│                                     │
└─────────────────────────────────────┘
```

**Key Information to Display:**
- Nurse name and photo
- Rating (stars)
- Distance from patient
- Estimated arrival time
- Offered price (highlight if same as patient's offer or counter-offer)
- Nurse notes (if any)
- "View Profile" to see more details before deciding

---

### Step 5b: View Nurse Profile (Before Accepting)

Before accepting an offer, patients can view detailed nurse information.

#### Get Nurse Profile

```http
GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-profile/{nurse_id}/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 5,
        "full_name": "Fatima Hamdi",
        "photo": "https://...",
        "rating": 4.8,
        "reviews_count": 127,
        "years_experience": 8,
        "specializations": ["Wound Care", "IV Therapy"],
        "bio": "Experienced nurse specializing in home care services...",
        "completed_requests": 245,
        "verification_status": "VERIFIED"
    },
    "offer": {
        "id": 123,
        "offered_price": "1500 DA",
        "status": "PENDING",
        "estimated_arrival_time": "00:25:00",
        "notes": ""
    },
    "message": "Nurse profile retrieved successfully"
}
```

#### Get Nurse Service History

```http
GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-history/{nurse_id}/
Authorization: Token your_auth_token
```

**Response:**
```json
{
    "success": true,
    "count": 10,
    "results": [
        {
            "service_name": "Wound Dressing",
            "completed_at": "2026-01-28T16:00:00Z",
            "patient_rating": 5,
            "review_text": "Excellent service, very professional"
        },
        {
            "service_name": "IV Therapy",
            "completed_at": "2026-01-25T10:00:00Z",
            "patient_rating": 5,
            "review_text": "Very gentle and caring"
        }
    ],
    "message": "Nurse service history retrieved"
}
```

---

### Step 6a: Accept a Nurse Offer

When the patient chooses a nurse:

```http
POST /api/nurse-requests/patient/nurse-requests/{request_id}/accept/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "offer_id": 123
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "id": 42,
        "status": "ACCEPTED",
        "accepted_nurse": 5,
        "accepted_nurse_name": "Fatima H.",
        "accepted_nurse_phone": "+213...",
        "final_price": "1500 DA",
        "accepted_at": "2026-01-31T14:45:00Z"
    },
    "message": "Offer accepted! The nurse will be on their way."
}
```

**Show Confirmation Screen:**
```
┌─────────────────────────────────────┐
│          ✅ Nurse Assigned!         │
├─────────────────────────────────────┤
│                                     │
│         👩‍⚕️                         │
│      Fatima H.                      │
│      is on her way                  │
│                                     │
│  ────────────────────────────────   │
│                                     │
│  📍 Arriving in ~25 minutes         │
│  💰 Final Price: 1500 DA             │
│                                     │
│  📞 Contact Nurse                   │
│  💬 Send Message                    │
│                                     │
│  ────────────────────────────────   │
│                                     │
│  Service: Wound Dressing            │
│  Location: 123 Main Street          │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 6b: Cancel Request

If patient changes their mind:

```http
POST /api/nurse-requests/patient/nurse-requests/{request_id}/cancel/
Authorization: Token your_auth_token
Content-Type: application/json

{
    "cancellation_reason": "Changed my mind"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "data": {
        "id": 42,
        "status": "CANCELLED",
        "cancellation_reason": "Changed my mind",
        "cancelled_at": "2026-01-31T14:40:00Z"
    },
    "message": "Request cancelled successfully"
}
```

---

### Step 7-9: Track Service Progress

Monitor status changes through polling or WebSocket:

| Status | Description | UI Action |
|--------|-------------|-----------|
| `ACCEPTED` | Nurse accepted, on the way | Show nurse info, ETA, contact options |
| `IN_PROGRESS` | Nurse arrived, service started | Show "Service in progress" |
| `COMPLETED` | Service finished | Show completion, ask for rating |

---

### List My Requests (Active & History)

Get all patient's nurse service requests including full history:

```http
GET /api/nurse-requests/patient/nurse-requests/
Authorization: Token your_auth_token
```

**Query Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `status` | Filter by specific status | `?status=COMPLETED` |
| `is_active` | Show only active requests | `?is_active=true` |
| `is_history` | Show only historical requests | `?is_history=true` |

**Filter Examples:**
- All requests: `/api/nurse-requests/patient/nurse-requests/`
- Active only: `/api/nurse-requests/patient/nurse-requests/?is_active=true`
- History only: `/api/nurse-requests/patient/nurse-requests/?is_history=true`
- Cancelled only: `/api/nurse-requests/patient/nurse-requests/?status=CANCELLED`
- Completed only: `/api/nurse-requests/patient/nurse-requests/?status=COMPLETED`

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "id": 42,
            "service_name": "Wound Dressing",
            "status": "SEARCHING",
            "patient_offered_price": "1500.00",
            "final_price": null,
            "city": "Algiers",
            "offers_count": 2,
            "created_at": "2026-01-31T14:30:00Z"
        },
        {
            "id": 38,
            "service_name": "IV Therapy",
            "status": "COMPLETED",
            "patient_offered_price": "2500.00",
            "final_price": "2500.00",
            "city": "Algiers",
            "offers_count": 3,
            "created_at": "2026-01-28T10:00:00Z"
        },
        {
            "id": 35,
            "service_name": "Injection",
            "status": "CANCELLED",
            "patient_offered_price": "800.00",
            "final_price": null,
            "city": "Oran",
            "offers_count": 1,
            "cancellation_reason": "Changed my mind",
            "created_at": "2026-01-25T09:00:00Z"
        }
    ]
}
```

---

## 📜 Request History

The patient's request history includes **all requests** regardless of outcome:

### What's Included in History

| Scenario | Status | Description |
|----------|--------|-------------|
| ✅ **Completed** | `COMPLETED` | Successfully completed services |
| ❌ **You Cancelled** | `CANCELLED` | Requests you cancelled manually |
| ⏰ **Auto-Cancelled** | `CANCELLED` | Requests cancelled due to no nurse response |
| 🔄 **In Progress** | Active statuses | Currently active requests |

### History UI Suggestion

```
┌─────────────────────────────────────┐
│         My Request History          │
├─────────────────────────────────────┤
│                                     │
│  [All] [Active] [Completed] [Cancel]│
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ ✅ Wound Dressing               ││
│  │ 31 Jan 2026 • 1,500 DA          ││
│  │ Nurse: Fatima H. ⭐ 4.8         ││
│  │ Status: COMPLETED               ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ ❌ IV Therapy                   ││
│  │ 25 Jan 2026 • 2,500 DA          ││
│  │ Status: CANCELLED               ││
│  │ Reason: Changed my mind         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ ⏰ Injection                    ││
│  │ 20 Jan 2026 • 800 DA            ││
│  │ Status: CANCELLED               ││
│  │ Reason: No nurse available      ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

### Note on Deletion

> ⚠️ **History records cannot be deleted.** They serve as audit records for completed transactions and are important for:
> - Service verification
> - Dispute resolution
> - Medical records tracking
> - Payment history

---

## Request Status Reference

```
CREATED → SEARCHING → NURSE_RESPONDED → PATIENT_DECISION → ACCEPTED → IN_PROGRESS → COMPLETED
                                                         ↘ CANCELLED ↙
```

| Status | Description |
|--------|-------------|
| `CREATED` | Request just created |
| `SEARCHING` | Broadcasting to nurses (show "Finding nurses...") |
| `NURSE_RESPONDED` | At least one nurse has responded |
| `PATIENT_DECISION` | Awaiting patient's final choice |
| `ACCEPTED` | Patient accepted a nurse offer |
| `IN_PROGRESS` | Nurse arrived, service being provided |
| `COMPLETED` | Service completed successfully |
| `CANCELLED` | Request was cancelled |

---

## WebSocket Events Reference

### Events Received by Patient

#### New Offer
```json
{
    "type": "new_offer",
    "offer": {
        "id": 123,
        "nurse_id": 5,
        "nurse_name": "Fatima H.",
        "offered_price": "1500 DA",
        "distance_km": 3.5,
        "estimated_arrival_time": "00:25:00"
    }
}
```

#### Request Updated
```json
{
    "type": "request_updated",
    "request": {
        "id": 42,
        "status": "ACCEPTED",
        "final_price": "1500 DA"
    }
}
```

#### Request Cancelled (by nurse/system)
```json
{
    "type": "request_cancelled",
    "request_id": 42,
    "reason": "No nurses available"
}
```

### Keep-Alive (Ping/Pong)
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

### Common Errors for Patients

| Code | Name | Description |
|------|------|-------------|
| `NR1001` | SERVICE_NOT_FOUND | Nursing service does not exist |
| `NR1002` | SERVICE_INACTIVE | Service is currently not active |
| `NR2001` | PRICE_BELOW_BASE | Offered price is below base price |
| `NR3001` | REQUEST_NOT_FOUND | Request not found |
| `NR3002` | REQUEST_NOT_OWNER | Not the owner of this request |
| `NR3003` | REQUEST_INVALID_STATUS | Cannot perform action in current status |
| `NR3004` | REQUEST_ALREADY_CANCELLED | Request already cancelled |
| `NR3005` | REQUEST_ALREADY_ACCEPTED | Already has an accepted offer |
| `NR4001` | OFFER_NOT_FOUND | Offer not found |
| `NR4002` | OFFER_NOT_AVAILABLE | Offer is no longer available |
| `NR5001` | LOCATION_REQUIRED | Location is required |
| `NR5002` | LOCATION_INVALID_COORDS | Invalid coordinates |
| `NR5004` | ADDRESS_NOT_FOUND | Saved address not found |

### Error Response Examples

**Price Below Base:**
```json
{
    "success": false,
    "error": {
        "code": "NR2001",
        "message": "Your offered price must be at least the base price",
        "details": {
            "field": "patient_offered_price",
            "base_price": "1000.00",
            "offered_price": "40.00"
        }
    }
}
```

**Invalid Status:**
```json
{
    "success": false,
    "error": {
        "code": "NR3003",
        "message": "Cannot accept offers at this stage. Wait for nurses to respond.",
        "details": {
            "current_status": "SEARCHING"
        }
    }
}
```

---

## Pricing Rules

1. **Patient** can only offer price **≥ base price**
2. **Nurses** may:
   - Accept at patient's price
   - Counter-offer at price **≥ patient's price**
3. **Patient** makes final decision (chooses which offer to accept)
4. Once accepted, `final_price` is locked and cannot be changed

---

## Quick Implementation Checklist

- [ ] Browse services screen with service list
- [ ] Location selection (saved addresses + map picker)
- [ ] Price input with base price validation
- [ ] Request creation with loading state
- [ ] WebSocket connection for real-time offers
- [ ] Polling fallback if WebSocket unavailable
- [ ] Offers list with nurse details
- [ ] Nurse profile view before accepting
- [ ] Accept offer confirmation
- [ ] Cancel request option
- [ ] Request history/tracking screen
- [ ] Status updates handling
