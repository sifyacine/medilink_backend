# On-Demand Nursing Service API

## Overview

This feature implements an **Uber-like on-demand nursing service** where patients can request nursing services, set a location and price, and nearby nurses can accept, counter-offer, or reject the request.

---

## 📱 PATIENT MOBILE APP IMPLEMENTATION GUIDE

This section provides a step-by-step guide for implementing the on-demand nursing service in the **Patient Mobile App**.

### Complete User Flow (Patient Side)

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

### Step-by-Step Implementation

#### Step 1: Browse Available Nursing Services

**Screen: Service Selection Screen**

When the patient opens the nurse request feature, show a list of available nursing services.

```http
GET /api/nurse-requests/services/
```

**Implementation:**
```dart
// Example Flutter/Dart code
class ServiceListScreen extends StatefulWidget {
  @override
  Widget build(BuildContext context) {
    return FutureBuilder(
      future: api.getNursingServices(),
      builder: (context, snapshot) {
        if (snapshot.hasData) {
          return ListView.builder(
            itemCount: snapshot.data.results.length,
            itemBuilder: (context, index) {
              final service = snapshot.data.results[index];
              return ServiceCard(
                name: service.name,
                description: service.description,
                basePrice: service.base_price,
                duration: service.estimated_duration,
                onTap: () => navigateToLocationSelection(service),
              );
            },
          );
        }
        return LoadingSpinner();
      },
    );
  }
}
```

**UI Elements to Show:**
- Service name (e.g., "Wound Dressing", "IV Therapy")
- Description
- Base price (minimum price patient must offer)
- Estimated duration
- Service icon

---

#### Step 2: Select Location

**Screen: Location Selection Screen**

After selecting a service, the patient chooses where they need the nurse.

**Option A: Show Saved Addresses First**
```http
GET /api/nurse-requests/patient/nurse-requests/saved-addresses/
```

**Option B: Let Patient Select from Map**

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
│  │ 🏢 Office                       ││
│  │ 456 Business Ave, Algiers       ││
│  └─────────────────────────────────┘│
│                                     │
│  ─────── OR ───────                 │
│                                     │
│  [📍 Select Location on Map]        │
│                                     │
└─────────────────────────────────────┘
```

**Implementation Notes:**
- If patient selects a saved address, you'll use the `use-saved-address` endpoint
- If patient uses the map, you'll collect: `latitude`, `longitude`, `city`, `address_line`

---

#### Step 3: Set Price and Details

**Screen: Request Details Screen**

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
│  │ $  [  75.00  ]                  ││
│  └─────────────────────────────────┘│
│  ℹ️ Minimum: $50.00 (base price)    │
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

#### Step 4: Create Request

**Action: Submit Request**

**If using saved address:**
```http
POST /api/nurse-requests/patient/nurse-requests/use-saved-address/
Content-Type: application/json

{
    "service": 1,
    "patient_offered_price": "75.00",
    "address_id": 5,
    "notes": "Please ring doorbell twice"
}
```

**If using map coordinates:**
```http
POST /api/nurse-requests/patient/nurse-requests/
Content-Type: application/json

{
    "service": 1,
    "patient_offered_price": "75.00",
    "latitude": "36.7525",
    "longitude": "3.0420",
    "city": "Algiers",
    "address_line": "123 Main Street, Algiers Center",
    "notes": "Please ring doorbell twice"
}
```

**On Success - Show Waiting Screen:**

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
│   Your Offer: $75.00                │
│   Location: 123 Main Street         │
│                                     │
│                                     │
│   [Cancel Request]                  │
│                                     │
└─────────────────────────────────────┘
```

**Important: Start WebSocket Connection or Polling**

Once the request is created, immediately connect to WebSocket or start polling to receive nurse offers.

---

#### Step 5: Receiving Nurse Offers (Real-Time)

**WebSocket Connection (Preferred):**
```javascript
// Connect to WebSocket
const ws = new WebSocket(`wss://your-domain/ws/nurse-requests/${requestId}/`);

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
    }
};
```

**Polling Alternative (if WebSocket not available):**
```http
GET /api/nurse-requests/patient/nurse-requests/{id}/
```

Poll every 5-10 seconds to check for new offers.

**UI: Offers Appearing One by One:**

```
┌─────────────────────────────────────┐
│        Nurses Available             │
├─────────────────────────────────────┤
│                                     │
│  3 nurses have responded            │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👩‍⚕️ Nurse Fatima               ││
│  │ ⭐ 4.8 Rating                   ││
│  │ 📍 3.5 km away                  ││
│  │ ⏱️ ~25 min arrival              ││
│  │ 💰 $75.00 (Your price)          ││
│  │ [Accept This Nurse]             ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👨‍⚕️ Nurse Ahmed                ││
│  │ ⭐ 4.5 Rating                   ││
│  │ 📍 8.2 km away                  ││
│  │ ⏱️ ~45 min arrival              ││
│  │ 💰 $100.00 (Counter-offer)      ││
│  │ "Traffic is heavy today"        ││
│  │ [Accept This Nurse]             ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │ 👩‍⚕️ Nurse Leila                ││
│  │ ⭐ 4.9 Rating                   ││
│  │ 📍 2.1 km away                  ││
│  │ ⏱️ ~15 min arrival              ││
│  │ 💰 $75.00 (Your price)          ││
│  │ [Accept This Nurse]             ││
│  └─────────────────────────────────┘│
│                                     │
│  [Cancel Request]                   │
│                                     │
└─────────────────────────────────────┘
```

**Key Information to Display for Each Offer:**
- Nurse name
- Nurse profile picture
- Nurse rating
- Distance from patient
- Estimated arrival time
- Offered price (highlight if same as patient's offer or counter-offer)
- Nurse notes (if any)

---

#### Step 6a: Accept a Nurse Offer

**Action: Patient Taps "Accept This Nurse"**

```http
POST /api/nurse-requests/patient/nurse-requests/{request_id}/accept/
Content-Type: application/json

{
    "offer_id": 123
}
```

**On Success:**
```json
{
    "success": true,
    "data": {
        "id": 42,
        "status": "ACCEPTED",
        "accepted_nurse": 5,
        "accepted_nurse_name": "Nurse Fatima",
        "final_price": "75.00",
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
│      Nurse Fatima                   │
│      is on her way                  │
│                                     │
│  ────────────────────────────────   │
│                                     │
│  📍 Arriving in ~25 minutes         │
│  💰 Final Price: $75.00             │
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

#### Step 6b: Cancel Request (Alternative)

**If patient changes their mind:**

```http
POST /api/nurse-requests/patient/nurse-requests/{request_id}/cancel/
Content-Type: application/json

{
    "cancellation_reason": "Changed my mind"
}
```

---

#### Step 7-9: Service Completion

**Tracking the Service:**

Poll or use WebSocket to track status changes:
- `ACCEPTED` → Nurse accepted, on the way
- `IN_PROGRESS` → Nurse arrived, service started
- `COMPLETED` → Service finished

**Show appropriate screens for each status.**

---

### Patient App API Summary Table

| Step | Action | Endpoint | Method |
|------|--------|----------|--------|
| 1 | Browse services | `/api/nurse-requests/services/` | GET |
| 2a | Get saved addresses | `/api/nurse-requests/patient/nurse-requests/saved-addresses/` | GET |
| 3a | Create request (saved addr) | `/api/nurse-requests/patient/nurse-requests/use-saved-address/` | POST |
| 3b | Create request (map) | `/api/nurse-requests/patient/nurse-requests/` | POST |
| 4 | Get request details | `/api/nurse-requests/patient/nurse-requests/{id}/` | GET |
| 5 | List my requests | `/api/nurse-requests/patient/nurse-requests/` | GET |
| 6a | Accept nurse offer | `/api/nurse-requests/patient/nurse-requests/{id}/accept/` | POST |
| 6b | Cancel request | `/api/nurse-requests/patient/nurse-requests/{id}/cancel/` | POST |

---

## 👩‍⚕️ NURSE MOBILE APP IMPLEMENTATION GUIDE

This section provides a step-by-step guide for implementing the on-demand nursing service in the **Nurse Mobile App**.

### Complete User Flow (Nurse Side)

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
│  │  │  Offered Price: $75.00                              │ │              │
│  │  └─────────────────────────────────────────────────────┘ │              │
│  │           │                                               │              │
│  │           ▼                                               │              │
│  │  ┌───────────┬───────────┬───────────┐                  │              │
│  │  │  ACCEPT   │  COUNTER  │  REJECT   │                  │              │
│  │  │  at $75   │  OFFER    │           │                  │              │
│  │  │           │  $100+    │           │                  │              │
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

### One-Time Setup: Managing Profile Services

**⚠️ IMPORTANT:** Nurses will ONLY see requests for services they have added to their profile!

#### View Available Services & Add to Profile

**Screen: My Services Screen**

```http
GET /api/nurse-requests/nurse/my-services/
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
            "base_price": "50.00",
            "custom_price": null,
            "effective_price": "50.00",
            "is_available": true
        }
    ],
    "my_services_count": 1,
    "available_to_add": [
        {
            "id": 2,
            "name": "IV Therapy",
            "base_price": "100.00"
        },
        {
            "id": 3,
            "name": "Injection",
            "base_price": "30.00"
        }
    ],
    "available_to_add_count": 2
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
│  │ Base: $50.00 | My Price: $50.00 ││
│  │ [Available ▼]  [Remove]         ││
│  └─────────────────────────────────┘│
│                                     │
│  AVAILABLE TO ADD (2)               │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────────┐│
│  │ ➕ IV Therapy                   ││
│  │ Base Price: $100.00             ││
│  │ [Add to My Services]            ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │ ➕ Injection                    ││
│  │ Base Price: $30.00              ││
│  │ [Add to My Services]            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

#### Add a Service to Profile

```http
POST /api/nurse-requests/nurse/my-services/add/
Content-Type: application/json

{
    "service_id": 2,
    "custom_price": "120.00"  // Optional - your custom price
}
```

#### Toggle Service Availability

```http
PATCH /api/nurse-requests/nurse/my-services/{service_id}/availability/
Content-Type: application/json

{
    "is_available": false  // or true
}
```

#### Remove a Service

```http
DELETE /api/nurse-requests/nurse/my-services/{service_id}/remove/
```

---

### Step 1: View Available Requests

**Screen: Available Requests Screen (Main Screen)**

```http
GET /api/nurse-requests/nurse/available-requests/
```

**This returns ONLY requests for services the nurse has added to their profile.**

**Response:**
```json
{
    "success": true,
    "count": 3,
    "results": [
        {
            "id": 42,
            "service_name": "Wound Dressing",
            "patient_name": "Ahmed B.",
            "patient_offered_price": "75.00",
            "latitude": "36.752500",
            "longitude": "3.042000",
            "city": "Algiers",
            "address_line": "123 Main Street",
            "created_at": "2026-01-31T14:30:00Z",
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
│  │ 💰 Offering: $75.00             ││
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
│  │ 💰 Offering: $110.00            ││
│  │ ⏰ 12 min ago                   ││
│  │                                 ││
│  │ [View Details]                  ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

**Real-Time Updates:**

Connect to WebSocket to receive new requests in real-time:
```javascript
const ws = new WebSocket('wss://your-domain/ws/nurse-requests/available/');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'new_request') {
        // Add new request to the list
        addRequestToList(data.request);
        // Show notification
        showNotification("New nursing request nearby!");
    }
};
```

---

### Step 2: View Request Details

**Screen: Request Details Screen**

Tap on a request to see full details.

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
│  Base Price: $50.00                 │
│  Patient Offers: $75.00             │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  NOTES                              │
│  "Please ring doorbell twice"       │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  [Accept at $75] [Counter Offer]    │
│  [Reject]                           │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3: Respond to Request

#### Option A: Accept at Patient's Price

**Action: Tap "Accept at $75"**

```http
POST /api/nurse-requests/nurse/available-requests/{id}/accept/
Content-Type: application/json

{
    "estimated_arrival_time": "00:25:00",
    "notes": "On my way!",
    "distance_km": 3.5
}
```

**Response:**
```json
{
    "success": true,
    "message": "Request accepted successfully",
    "offer_id": 123,
    "offered_price": "75.00"
}
```

#### Option B: Make Counter Offer

**Show Price Input Dialog:**

```
┌─────────────────────────────────────┐
│       Make Counter Offer            │
├─────────────────────────────────────┤
│                                     │
│  Patient offered: $75.00            │
│                                     │
│  Your price:                        │
│  ┌─────────────────────────────────┐│
│  │ $  [  100.00  ]                 ││
│  └─────────────────────────────────┘│
│  ℹ️ Must be ≥ $75.00                │
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

```http
POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/
Content-Type: application/json

{
    "offered_price": "100.00",
    "estimated_arrival_time": "00:45:00",
    "notes": "Traffic is heavy today",
    "distance_km": 3.5
}
```

#### Option C: Reject Request

```http
POST /api/nurse-requests/nurse/available-requests/{id}/reject/
Content-Type: application/json

{
    "reason": "Too far from my location"
}
```

---

### Step 4: Track My Offers

**Screen: My Offers Screen**

```http
GET /api/nurse-requests/nurse/my-offers/
```

Shows all requests where the nurse has submitted an offer.

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
│  │ 💰 My offer: $75.00             ││
│  │ Waiting for patient decision... ││
│  └─────────────────────────────────┘│
│                                     │
│  ACCEPTED (1)                       │
│  ─────────────────────────────────  │
│  ┌─────────────────────────────────┐│
│  │ ✅ IV Therapy                   ││
│  │ 👤 Fatima H.                    ││
│  │ 💰 Final: $110.00               ││
│  │ [Navigate] [Start Service]      ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### Step 5: When Patient Accepts Your Offer

**WebSocket Notification:**
```json
{
    "type": "offer_accepted",
    "request": {
        "id": 42,
        "status": "ACCEPTED",
        "patient_name": "Ahmed B.",
        "location": "123 Main Street",
        "final_price": "75.00"
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
│  Final Price: $75.00                │
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

### Step 6: Complete the Service

**When arrived at patient location:**
```http
POST /api/nurse-requests/patient/nurse-requests/{id}/start/
```

**When service is completed:**
```http
POST /api/nurse-requests/patient/nurse-requests/{id}/complete/
```

---

### Nurse App API Summary Table

| Step | Action | Endpoint | Method |
|------|--------|----------|--------|
| Setup | View my services | `/api/nurse-requests/nurse/my-services/` | GET |
| Setup | Add service to profile | `/api/nurse-requests/nurse/my-services/add/` | POST |
| Setup | Remove service | `/api/nurse-requests/nurse/my-services/{id}/remove/` | DELETE |
| Setup | Toggle availability | `/api/nurse-requests/nurse/my-services/{id}/availability/` | PATCH |
| 1 | View available requests | `/api/nurse-requests/nurse/available-requests/` | GET |
| 2 | Accept request | `/api/nurse-requests/nurse/available-requests/{id}/accept/` | POST |
| 2 | Counter offer | `/api/nurse-requests/nurse/available-requests/{id}/counter-offer/` | POST |
| 2 | Reject request | `/api/nurse-requests/nurse/available-requests/{id}/reject/` | POST |
| 3 | View my offers | `/api/nurse-requests/nurse/my-offers/` | GET |

---

## Integration with Services App

**Important:** Nursing services are managed through the **services** app, not separately. This ensures centralized service management by admins.

- **Service Type**: Services with `service_type=NURSE` and `is_on_demand=True` are available for on-demand requests
- **Admin Management**: Only super admins and admin users can create/edit nursing services via Django Admin or Admin API
- **Unified Catalog**: All services (doctor, nurse, VTC, general) are in one place
- **Nurse Profile Services**: Nurses must add services to their profile to receive requests for those services

### Admin Setup

To create a nursing service for on-demand requests:
1. Go to Django Admin → Services → Add Service
2. Set `Service Type` to **NURSE**
3. Check **Is on demand** checkbox
4. Check **Is home service** checkbox (recommended)
5. Set base price, title, description, etc.

### Nurse Profile Setup

Nurses must add services to their profile to receive on-demand requests:
1. Call `GET /api/nurse-requests/nurse/my-services/` to see available services
2. Call `POST /api/nurse-requests/nurse/my-services/add/` with `{"service_id": X}` to add
3. Once added, the nurse will see requests for that service

## Core Concepts

- **Nursing Service**: Services from `services.Service` with `service_type=NURSE` and `is_on_demand=True`
- **Nurse Profile Services**: Link between nurses and services they offer (from `services.NurseService`)
- **Service Request**: Patient's job offer with location and pricing
- **Nurse Offer**: Nurse's response (accept, counter-offer, or reject)
- **Real-time Updates**: WebSocket communication for live updates
- **Saved Addresses**: Patients can use saved addresses or select from map

---

## Request Lifecycle (States)

```
CREATED → SEARCHING → NURSE_RESPONDED → PATIENT_DECISION → ACCEPTED → IN_PROGRESS → COMPLETED
                                                         ↘ CANCELLED ↙
```

| Status | Description |
|--------|-------------|
| `CREATED` | Request just created |
| `SEARCHING` | Broadcasting to nearby nurses (patient sees "Finding nurses...") |
| `NURSE_RESPONDED` | At least one nurse has responded (offers start appearing) |
| `PATIENT_DECISION` | Awaiting patient's final choice |
| `ACCEPTED` | Patient accepted a nurse offer (nurse and patient connected) |
| `IN_PROGRESS` | Nurse arrived, service is being provided |
| `COMPLETED` | Service completed successfully |
| `CANCELLED` | Request was cancelled |

---

## Quick Start Guide

### For Patients

1. **Browse Services** → `GET /api/nurse-requests/services/`
2. **View Saved Addresses** → `GET /api/nurse-requests/patient/nurse-requests/saved-addresses/`
3. **Create Request** → Either:
   - Use saved address: `POST /api/nurse-requests/patient/nurse-requests/use-saved-address/`
   - Use map coordinates: `POST /api/nurse-requests/patient/nurse-requests/`
4. **Wait for Offers** → Connect to WebSocket or poll for updates
5. **Accept Offer** → `POST /api/nurse-requests/patient/nurse-requests/{id}/accept/`

### For Nurses

1. **Setup Profile Services** → `GET /api/nurse-requests/nurse/my-services/`
2. **Add Services** → `POST /api/nurse-requests/nurse/my-services/add/`
3. **View Available Requests** → `GET /api/nurse-requests/nurse/available-requests/`
4. **Respond to Request** → Either:
   - Accept: `POST /api/nurse-requests/nurse/available-requests/{id}/accept/`
   - Counter-offer: `POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/`
   - Reject: `POST /api/nurse-requests/nurse/available-requests/{id}/reject/`
5. **View My Offers** → `GET /api/nurse-requests/nurse/my-offers/`

---

## API Endpoints

### Base URL: `/api/nurse-requests/`

---

## Nursing Services Catalog

> **Note:** Services shown here are filtered from `services.Service` where `service_type='NURSE'` and `is_on_demand=True`.

### List All Available Services

```http
GET /api/nurse-requests/services/
```

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "name": "Wound Dressing",
            "description": "Professional wound care and dressing change",
            "base_price": "50.00",
            "duration_minutes": 30,
            "is_active": true,
            "icon": "wound-care",
            "created_at": "2026-01-15T10:00:00Z",
            "updated_at": "2026-01-15T10:00:00Z"
        }
    ]
}
```

### Get Service Details

```http
GET /api/nurse-requests/services/{id}/
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Wound Dressing",
        "description": "Professional wound care",
        "base_price": "50.00",
        ...
    },
    "available_nurses_count": 12,
    "message": "12 nurses available for this service"
}
```

---

## Patient Endpoints

### Get Saved Addresses

Before creating a request, patients can view their saved addresses or choose to select from map.

```http
GET /api/nurse-requests/patient/nurse-requests/saved-addresses/
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
        }
    ],
    "message": "Select a saved address or choose location from map"
}
```

---

### Create Request Using Saved Address

```http
POST /api/nurse-requests/patient/nurse-requests/use-saved-address/
```

**Request Body:**
```json
{
    "service": 1,
    "patient_offered_price": "75.00",
    "address_id": 5,
    "notes": "Please ring doorbell twice"
}
```

**Response:** `201 Created`
```json
{
    "success": true,
    "data": {
        "id": 42,
        "status": "SEARCHING",
        ...
    },
    "message": "Request created successfully using your saved address"
}
```

---

### Create New Service Request (Manual Location)

```http
POST /api/nurse-requests/patient/nurse-requests/
```

**Request Body:**
```json
{
    "service": 1,
    "patient_offered_price": "75.00",
    "latitude": "36.7525",
    "longitude": "3.0420",
    "city": "Algiers",
    "address_line": "123 Main Street, Algiers Center",
    "notes": "Please ring doorbell twice"
}
```

**Validation Rules:**
- `patient_offered_price` must be ≥ service's `base_price`
- Service must be active
- All location fields are required

**Response:** `201 Created`
```json
{
    "id": 42,
    "patient": 1,
    "patient_name": "Ahmed Ben Ali",
    "service": {
        "id": 1,
        "name": "Wound Dressing",
        "base_price": "50.00",
        ...
    },
    "base_price": "50.00",
    "patient_offered_price": "75.00",
    "final_price": null,
    "latitude": "36.752500",
    "longitude": "3.042000",
    "city": "Algiers",
    "address_line": "123 Main Street, Algiers Center",
    "status": "SEARCHING",
    "notes": "Please ring doorbell twice",
    "offers": [],
    "created_at": "2026-01-31T14:30:00Z",
    ...
}
```

---

### List My Requests

```http
GET /api/nurse-requests/patient/nurse-requests/
```

**Query Parameters:**
- `status`: Filter by status (e.g., `?status=SEARCHING`)

**Response:**
```json
{
    "count": 3,
    "results": [
        {
            "id": 42,
            "service_name": "Wound Dressing",
            "patient_name": "Ahmed Ben Ali",
            "status": "SEARCHING",
            "patient_offered_price": "75.00",
            "final_price": null,
            "city": "Algiers",
            "offers_count": 2,
            "created_at": "2026-01-31T14:30:00Z"
        }
    ]
}
```

---

### Get Request Details

```http
GET /api/nurse-requests/patient/nurse-requests/{id}/
```

**Response:** Full request details including all nurse offers.

---

### Accept a Nurse Offer

```http
POST /api/nurse-requests/patient/nurse-requests/{id}/accept/
```

**Request Body:**
```json
{
    "offer_id": 123
}
```

**Response:** `200 OK`
```json
{
    "id": 42,
    "status": "ACCEPTED",
    "accepted_nurse": 5,
    "accepted_nurse_name": "Nurse Fatima",
    "final_price": "75.00",
    "accepted_at": "2026-01-31T14:45:00Z",
    ...
}
```

---

### Cancel Request

```http
POST /api/nurse-requests/patient/nurse-requests/{id}/cancel/
```

**Request Body:**
```json
{
    "cancellation_reason": "Changed my mind"
}
```

**Response:** `200 OK` with updated request details.

---

## Nurse Endpoints

### List Available Requests

```http
GET /api/nurse-requests/nurse/available-requests/
```

Returns requests in `SEARCHING` or `NURSE_RESPONDED` status that the nurse hasn't responded to.

**Response:**
```json
{
    "count": 5,
    "results": [
        {
            "id": 42,
            "service_name": "Wound Dressing",
            "service_description": "Professional wound care...",
            "patient_name": "Ahmed B.",
            "patient_offered_price": "75.00",
            "latitude": "36.752500",
            "longitude": "3.042000",
            "city": "Algiers",
            "address_line": "123 Main Street, Algiers Center",
            "created_at": "2026-01-31T14:30:00Z",
            "my_offer": null
        }
    ]
}
```

---

### Accept Request at Patient's Price

```http
POST /api/nurse-requests/nurse/available-requests/{id}/accept/
```

**Request Body (optional):**
```json
{
    "estimated_arrival_time": "00:25:00",
    "notes": "On my way",
    "distance_km": 3.5
}
```

**Response:** `201 Created`
```json
{
    "message": "Request accepted successfully",
    "offer_id": 123
}
```

---

### Make Counter Offer

```http
POST /api/nurse-requests/nurse/available-requests/{id}/counter-offer/
```

**Request Body:**
```json
{
    "offered_price": "100.00",
    "estimated_arrival_time": "00:45:00",
    "notes": "Traffic is heavy, requesting higher compensation",
    "distance_km": 8.2
}
```

**Validation Rules:**
- `offered_price` must be ≥ patient's `patient_offered_price`
- `offered_price` must be ≥ service's `base_price`

**Response:** `201 Created`
```json
{
    "message": "Counter offer submitted successfully",
    "offer_id": 124
}
```

---

### Reject Request

```http
POST /api/nurse-requests/nurse/available-requests/{id}/reject/
```

**Request Body (optional):**
```json
{
    "reason": "Too far from my location"
}
```

**Response:** `200 OK`
```json
{
    "message": "Request rejected"
}
```

---

### View My Submitted Offers

```http
GET /api/nurse-requests/nurse/my-offers/
```

Returns all requests where the nurse has submitted an offer.

---

## Nurse Profile Services Management

**Important:** Nurses must add services to their profile to receive on-demand requests. If a nurse hasn't added a service, they won't see requests for that service.

### List My Services & Available Services to Add

```http
GET /api/nurse-requests/nurse/my-services/
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
            "description": "Professional wound care",
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
            "description": "IV drip administration",
            "base_price": "100.00",
            ...
        }
    ],
    "available_to_add_count": 3,
    "message": "Add services to receive on-demand requests for those services"
}
```

### Add Service to Profile

```http
POST /api/nurse-requests/nurse/my-services/add/
```

**Request Body:**
```json
{
    "service_id": 2,
    "custom_price": "120.00"
}
```

> **Note:** `custom_price` is optional. If not set, the base price is used.

**Response:** `201 Created`
```json
{
    "success": true,
    "data": {
        "id": 2,
        "service_id": 2,
        "title": "IV Therapy",
        "base_price": "100.00",
        "custom_price": "120.00",
        "effective_price": "120.00",
        "is_available": true,
        ...
    },
    "message": "Successfully added \"IV Therapy\" to your profile. You will now receive requests for this service."
}
```

### Remove Service from Profile

```http
DELETE /api/nurse-requests/nurse/my-services/{service_id}/remove/
```

**Response:**
```json
{
    "success": true,
    "message": "Removed \"IV Therapy\" from your profile. You will no longer receive requests for this service."
}
```

### Update Service Availability

```http
PATCH /api/nurse-requests/nurse/my-services/{service_id}/availability/
```

**Request Body:**
```json
{
    "is_available": false,
    "custom_price": "130.00"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 2,
        "is_available": false,
        "custom_price": "130.00",
        ...
    },
    "message": "Service is now unavailable"
}
```

---

## WebSocket Real-Time Communication

### Connection URLs

**Patient - Subscribe to Request Updates:**
```
ws://your-domain/ws/nurse-requests/{request_id}/
```

**Nurse - Subscribe to Available Requests:**
```
ws://your-domain/ws/nurse-requests/available/
```

### Message Types

#### New Request (sent to nurses)
```json
{
    "type": "new_request",
    "request": {
        "id": 42,
        "service_name": "Wound Dressing",
        "patient_offered_price": "75.00",
        ...
    }
}
```

#### New Offer (sent to patient)
```json
{
    "type": "new_offer",
    "offer": {
        "id": 123,
        "nurse_name": "Nurse Fatima",
        "offered_price": "75.00",
        "distance_km": 3.5,
        ...
    }
}
```

#### Request Updated
```json
{
    "type": "request_updated",
    "request": { ... }
}
```

#### Offer Accepted (sent to nurse)
```json
{
    "type": "offer_accepted",
    "request": { ... }
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

### Keep-Alive (Ping/Pong)
```json
// Send
{"type": "ping", "timestamp": 1706709600}

// Receive
{"type": "pong", "timestamp": 1706709600}
```

---

## Error Codes Reference

All error responses follow a consistent format:

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

### Service Errors (1xxx)

| Code | Name | Description |
|------|------|-------------|
| `NR1001` | SERVICE_NOT_FOUND | The requested nursing service does not exist |
| `NR1002` | SERVICE_INACTIVE | The service is currently not active |
| `NR1003` | SERVICE_NOT_NURSING | The selected service is not a nursing service |
| `NR1004` | SERVICE_NOT_ON_DEMAND | This service is not available for on-demand requests |
| `NR1005` | SERVICE_ALREADY_ADDED | Nurse has already added this service to their profile |
| `NR1006` | SERVICE_NOT_IN_PROFILE | This service is not in the nurse's profile |

### Price Errors (2xxx)

| Code | Name | Description |
|------|------|-------------|
| `NR2001` | PRICE_BELOW_BASE | Offered price is below the service's base price |
| `NR2002` | PRICE_BELOW_PATIENT_OFFER | Counter offer is below patient's offered price |
| `NR2003` | PRICE_INVALID | Invalid price format |

### Request Errors (3xxx)

| Code | Name | Description |
|------|------|-------------|
| `NR3001` | REQUEST_NOT_FOUND | Request not found |
| `NR3002` | REQUEST_NOT_OWNER | User is not the owner of this request |
| `NR3003` | REQUEST_INVALID_STATUS | Operation not allowed for current request status |
| `NR3004` | REQUEST_ALREADY_CANCELLED | Request has already been cancelled |
| `NR3005` | REQUEST_ALREADY_ACCEPTED | Request already has an accepted offer |
| `NR3006` | REQUEST_ALREADY_COMPLETED | Request has already been completed |
| `NR3007` | REQUEST_SERVICE_NOT_IN_NURSE_PROFILE | Nurse cannot respond because service is not in their profile |

### Offer Errors (4xxx)

| Code | Name | Description |
|------|------|-------------|
| `NR4001` | OFFER_NOT_FOUND | Offer not found |
| `NR4002` | OFFER_NOT_AVAILABLE | Offer is no longer available |
| `NR4003` | OFFER_ALREADY_SUBMITTED | Nurse has already submitted an offer |
| `NR4004` | OFFER_EXPIRED | Offer has expired |

### Location Errors (5xxx)

| Code | Name | Description |
|------|------|-------------|
| `NR5001` | LOCATION_REQUIRED | Location is required |
| `NR5002` | LOCATION_INVALID_COORDS | Invalid coordinates provided |
| `NR5003` | CITY_REQUIRED | City field is required |
| `NR5004` | ADDRESS_NOT_FOUND | Saved address not found |

### Auth/Permission Errors (6xxx)

| Code | Name | Description |
|------|------|-------------|
| `NR6001` | NOT_AUTHENTICATED | User is not authenticated |
| `NR6002` | NOT_PATIENT | User is not a patient |
| `NR6003` | NOT_NURSE | User is not a nurse |
| `NR6004` | NURSE_PROFILE_NOT_FOUND | Nurse profile not found or incomplete |
| `NR6005` | NURSE_NOT_VERIFIED | Nurse is not verified |

---

## Common Error Examples

### Validation Error (400)
```json
{
    "success": false,
    "error": {
        "code": "NR2001",
        "message": "Your offered price must be at least the base price",
        "details": {
            "field": "patient_offered_price",
            "messages": ["Offered price ($40.00) cannot be lower than base price ($50.00)"]
        }
    }
}
```

### Not Authorized (403)
```json
{
    "success": false,
    "error": {
        "code": "NR3002",
        "message": "You do not have permission to accept offers on this request"
    }
}
```

### Service Not in Nurse Profile (403)
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

### Invalid State (400)
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

### Nurse Has No Services (Warning)
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
```

---

## Data Models

### NursingService
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `name` | string | Service name |
| `description` | text | Detailed description |
| `base_price` | decimal | Minimum price (cannot be lowered) |
| `estimated_duration` | duration | Expected service duration |
| `is_active` | boolean | Whether service is available |
| `icon` | string | Icon identifier |

### NurseServiceRequest
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `patient` | FK | Link to patient |
| `service` | FK | Link to nursing service |
| `accepted_nurse` | FK | Accepted nurse provider |
| `base_price` | decimal | Service base price at time of request |
| `patient_offered_price` | decimal | Patient's offered price |
| `final_price` | decimal | Final agreed price |
| `latitude` | decimal | GPS latitude |
| `longitude` | decimal | GPS longitude |
| `city` | string | City name (used for matching) |
| `address_line` | string | Human-readable address |
| `status` | enum | Current request status |
| `notes` | text | Patient notes |

### NurseOffer
| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `request` | FK | Link to request |
| `nurse` | FK | Link to nurse provider |
| `offered_price` | decimal | Nurse's offered price |
| `status` | enum | Offer status (PENDING, ACCEPTED, REJECTED, etc.) |
| `estimated_arrival_time` | duration | ETA to patient |
| `distance_km` | decimal | Distance from nurse to patient |
| `notes` | text | Nurse notes |

---

## Pricing Rules Summary

1. **Patient** can only offer price **≥ base price**
2. **Nurse** can:
   - Accept at patient's price
   - Counter-offer at price **≥ patient's price**
3. **Patient** makes final decision (cannot counter-offer)
4. Once accepted, `final_price` is locked

---

## Future Enhancements

- [ ] Geospatial filtering with PostGIS
- [ ] Push notifications for mobile apps
- [ ] Rating/review system after completion
- [ ] Availability scheduling for nurses
- [ ] Payment integration
- [ ] Extend to Health VTC providers
