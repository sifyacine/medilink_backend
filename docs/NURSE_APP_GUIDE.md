# Nurse App - Requests & Offers Guide

## Overview

The Nurse App enables nurses to manage their on-demand nursing services, receive patient requests in real-time, submit offers, and track their service history. It follows a professional marketplace model where nurses can control their availability, pricing, and service areas.

---

## Table of Contents

1. [Workflow Overview](#workflow-overview)
2. [Key Concepts](#key-concepts)
3. [Setup & Profile Management](#setup--profile-management)
4. [API Endpoints](#api-endpoints)
5. [Step-by-Step Workflows](#step-by-step-workflows)
6. [Offer Management Strategy](#offer-management-strategy)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## Workflow Overview

### Complete Nurse Request-to-Service Journey

```
1. Complete Nurse Profile (Required)
   ↓
2. Add Services to Profile
   (Configure which services you offer and at what price)
   ↓
3. Set Availability
   (Mark yourself as available/unavailable)
   ↓
4. View Available Requests
   (See requests matching your services and location)
   ↓
5. Review Request Details
   (Check patient location, price, service type)
   ↓
6. Submit Offer (Accept or Counter-Offer)
   (Set your price, ETA, additional info)
   ↓
7. Wait for Patient Response
   (Patient reviews all offers and chooses)
   ↓
8. Offer Accepted!
   (Your offer was selected, prepare to serve)
   ↓
9. Provide Service
   (Travel to location, perform service)
   ↓
10. Complete & Get Paid
    (Mark complete, receive payment)
    ↓
11. Build Reputation
    (Receive reviews, improve rating)
```

---

## Key Concepts

### Request Visibility Rules

**IMPORTANT**: Nurses ONLY see requests for services they have added to their profile!

- If you want to receive requests for "Wound Care", you MUST add it to your profile
- If you don't add a service, you won't see ANY requests for that service
- Your service availability must be set to `true` to receive new requests

### Offer Status Flow

| Offer Status | Description | Nurse Action Available |
|--------------|-------------|------------------------|
| **PENDING** | Patient reviewing your offer | Wait or submit another counter-offer |
| **ACCEPTED** | Patient accepted your offer! | Prepare to serve, travel to location |
| **REJECTED** | Patient declined your offer | None (can see other requests) |
| **COUNTER_OFFERED** | You made a counter-offer | Wait for patient response |
| **EXPIRED** | Offer expired without response | None (request may have been accepted by another nurse) |

### Request Status Flow (From Nurse Perspective)

| Request Status | What It Means | Nurse Action |
|----------------|---------------|--------------|
| **CREATED** | Just created, not yet visible to nurses | None (wait for broadcasting) |
| **SEARCHING** | Actively seeking nurse responses | Submit offer or counter-offer |
| **NURSE_RESPONDED** | At least one nurse responded | Patient reviewing offers |
| **PATIENT_DECISION** | Multiple offers, patient deciding | Wait for patient decision |
| **ACCEPTED** | A nurse's offer was accepted | Check if it's yours |
| **IN_PROGRESS** | Service in progress | If your offer: provide service |
| **COMPLETED** | Service finished | If your offer: rate patient if desired |
| **CANCELLED** | Request cancelled by patient | None (move to next request) |

---

## Setup & Profile Management

### Step 1: Complete Nurse Profile

Before you can receive any requests, you must complete your nurse profile with:

**Required Information:**
- First name, Last name
- Professional license number
- Certification information
- Years of experience
- Phone number
- Profile image/photo
- Biography

**Optional Information:**
- Service area radius (default 50 km)
- Work address/clinic location
- Specialties
- Languages spoken

### Step 2: Add Services to Profile

Once your profile is complete, you must add the nursing services you offer.

#### Get List of Available Services

```
GET /api/nurse-requests/nurse/my-services/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "my_services": [
    {
      "id": 1,
      "service_id": 1,
      "title": "Basic Wound Care",
      "description": "Professional wound cleaning and dressing",
      "base_price": "50.00",
      "custom_price": null,
      "effective_price": "50.00 DZD",
      "duration_minutes": 30,
      "is_available": true,
      "is_on_demand": true,
      "created_at": "2024-04-15T09:00:00Z"
    }
  ],
  "my_services_count": 1,
  "available_to_add": [
    {
      "id": 2,
      "name": "IV Administration",
      "description": "Intravenous therapy administration",
      "base_price": "75.00",
      "estimated_duration": "00:15:00",
      "is_active": true,
      "currency": "DZD",
      "is_home_service": true
    },
    {
      "id": 3,
      "name": "Injection Service",
      "description": "Professional injection administration",
      "base_price": "25.00",
      "estimated_duration": "00:05:00",
      "is_active": true,
      "currency": "DZD",
      "is_home_service": true
    }
  ],
  "available_to_add_count": 2,
  "message": "Add services to receive on-demand requests for those services"
}
```

#### Add a Service to Your Profile

```
POST /api/nurse-requests/nurse/my-services/add/
Authorization: Bearer <token>
Content-Type: application/json

{
  "service_id": 2,
  "custom_price": "80.00"
}
```

**Fields:**
- `service_id` (required): ID of the service from available services
- `custom_price` (optional): Your custom price override (if different from base)

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "service_id": 2,
    "title": "IV Administration",
    "description": "Intravenous therapy administration",
    "base_price": "75.00",
    "custom_price": "80.00",
    "effective_price": "80.00 DZD",
    "duration_minutes": 15,
    "is_available": true,
    "is_on_demand": true,
    "created_at": "2024-04-18T10:00:00Z"
  },
  "message": "Successfully added \"IV Administration\" to your profile. You will now receive requests for this service."
}
```

#### Update Service Availability & Pricing

```
PATCH /api/nurse-requests/nurse/my-services/{service_id}/availability/
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_available": true,
  "custom_price": "85.00"
}
```

**Fields:**
- `is_available` (optional): Set true to receive requests, false to pause temporarily
- `custom_price` (optional): Update your custom price

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "service_id": 2,
    "title": "IV Administration",
    "is_available": true,
    "custom_price": "85.00",
    "effective_price": "85.00 DZD",
    "created_at": "2024-04-18T10:00:00Z"
  },
  "message": "Service is now available"
}
```

#### Remove a Service from Profile

```
DELETE /api/nurse-requests/nurse/my-services/{service_id}/remove/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Removed \"IV Administration\" from your profile. You will no longer receive requests for this service."
}
```

---

## API Endpoints

### 1. View Available Requests

#### List Available Requests in Your Service Area

```
GET /api/nurse-requests/nurse/available-requests/
Authorization: Bearer <token>
```

**Query Parameters:**
- `city` (optional): Filter by city name

**Examples:**
```
GET /api/nurse-requests/nurse/available-requests/
GET /api/nurse-requests/nurse/available-requests/?city=Algiers
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 45,
      "service_id": 1,
      "service_name": "Basic Wound Care",
      "service_description": "Professional wound cleaning and dressing",
      "patient_name": "A. S.",
      "patient_offered_price": "75.00",
      "base_price": "50.00",
      "latitude": "36.7372",
      "longitude": "3.0588",
      "city": "Algiers",
      "address_line": "123 Main Street, Apartment 5",
      "status": "SEARCHING",
      "created_at": "2024-04-18T10:30:00Z",
      "my_offer": null
    },
    {
      "id": 44,
      "service_id": 1,
      "service_name": "Basic Wound Care",
      "service_description": "Professional wound cleaning and dressing",
      "patient_name": "F. B.",
      "patient_offered_price": "100.00",
      "base_price": "50.00",
      "latitude": "36.7450",
      "longitude": "3.0650",
      "city": "Algiers",
      "address_line": "456 Oak Street",
      "status": "SEARCHING",
      "created_at": "2024-04-18T10:15:00Z",
      "my_offer": {
        "id": 8,
        "offered_price": "100.00",
        "status": "PENDING",
        "estimated_arrival_time": "00:20:00",
        "distance_km": "4.5"
      }
    }
  ],
  "your_active_services_count": 2,
  "message": "Showing requests for your 2 active service(s)"
}
```

**Warning Response** (If no services in profile):
```json
{
  "success": true,
  "count": 0,
  "results": [],
  "warning": {
    "code": "NR3007",
    "message": "You have no active services in your profile. Add services to start receiving requests.",
    "action": "Go to /api/nurse-requests/nurse/my-services/ to add services"
  }
}
```

#### Get Request Details

```
GET /api/nurse-requests/nurse/available-requests/{request_id}/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "service_id": 1,
    "service_name": "Basic Wound Care",
    "service_description": "Professional wound cleaning and dressing",
    "patient_name": "A. S.",
    "patient_offered_price": "75.00",
    "base_price": "50.00",
    "latitude": "36.7372",
    "longitude": "3.0588",
    "city": "Algiers",
    "address_line": "123 Main Street, Apartment 5",
    "status": "SEARCHING",
    "created_at": "2024-04-18T10:30:00Z",
    "my_offer": null
  }
}
```

---

### 2. Submit Offer (Accept at Patient's Price)

#### Accept Request at Patient's Offered Price

```
POST /api/nurse-requests/nurse/available-requests/{request_id}/accept/
Authorization: Bearer <token>
Content-Type: application/json

{
  "estimated_arrival_time": "00:25:00",
  "notes": "I'll be there in about 25 minutes. Current traffic is heavy.",
  "distance_km": "3.5"
}
```

**Fields:**
- `estimated_arrival_time` (optional): Duration format HH:MM:SS (e.g., "00:25:00" for 25 minutes)
- `notes` (optional): Message to patient about your offer
- `distance_km` (optional): Actual distance from your location

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Request accepted successfully",
  "offer_id": 12,
  "offered_price": "75.00"
}
```

**Errors:**
```json
{
  "success": false,
  "error": {
    "code": "NR3007",
    "message": "You cannot respond to this request because you do not offer \"IV Administration\" service.",
    "details": {
      "service_id": 2,
      "service_name": "IV Administration",
      "action": "Add this service to your profile first"
    }
  }
}
```

---

### 3. Submit Counter-Offer (Different Price)

#### Counter-Offer at Higher Price

```
POST /api/nurse-requests/nurse/available-requests/{request_id}/counter-offer/
Authorization: Bearer <token>
Content-Type: application/json

{
  "offered_price": "85.00",
  "estimated_arrival_time": "00:30:00",
  "notes": "Heavy traffic, might take 30 minutes. Price reflects current market rate.",
  "distance_km": "5.2"
}
```

**Fields:**
- `offered_price` (required): Your counter offer price (must be ≥ patient's offered price AND base price)
- `estimated_arrival_time` (optional): Your estimated arrival time
- `notes` (optional): Explanation of counter-offer
- `distance_km` (optional): Distance from your location

**Validation Rules:**
- Counter offer must be ≥ patient's offered price
- Counter offer must be ≥ base price
- Example: If patient offers 75 DZD and base is 50 DZD, minimum counter is 75 DZD

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Counter offer submitted successfully",
  "offer_id": 13,
  "offered_price": "85.00"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "NR2002",
    "message": "Counter offer must be at least 75.00 DZD",
    "details": {
      "minimum_price": "75.00",
      "your_offer": "70.00"
    }
  }
}
```

---

### 4. Reject Request

#### Reject Without Submitting Offer

```
POST /api/nurse-requests/nurse/available-requests/{request_id}/reject/
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "Too far from my location. Patient location is outside my service area."
}
```

**Fields:**
- `reason` (optional): Why you're rejecting this request

**Response:**
```json
{
  "success": true,
  "message": "Request rejected"
}
```

---

### 5. View Your Submitted Offers

#### List All Offers You've Submitted

```
GET /api/nurse-requests/nurse/my-offers/
Authorization: Bearer <token>
```

**Query Parameters:**
- `status`: Filter by request status (SEARCHING, ACCEPTED, COMPLETED, CANCELLED)
- `offer_status`: Filter by your offer status (PENDING, ACCEPTED, REJECTED)
- `is_active`: Filter active requests (true/false)
- `is_history`: Filter historical requests (true/false)

**Examples:**
```
GET /api/nurse-requests/nurse/my-offers/?offer_status=ACCEPTED
GET /api/nurse-requests/nurse/my-offers/?status=COMPLETED
GET /api/nurse-requests/nurse/my-offers/?is_active=true
```

**Response:**
```json
{
  "success": true,
  "count": 8,
  "results": [
    {
      "id": 45,
      "patient_name": "Ahmed Sifi",
      "service": {
        "id": 1,
        "name": "Basic Wound Care"
      },
      "status": "ACCEPTED",
      "final_price": "75.00",
      "offers": [
        {
          "id": 12,
          "nurse_id": 10,
          "offered_price": "75.00",
          "status": "ACCEPTED",
          "estimated_arrival_time": "00:25:00",
          "notes": "I'll be there in about 25 minutes"
        }
      ],
      "created_at": "2024-04-18T10:30:00Z",
      "accepted_at": "2024-04-18T10:50:00Z"
    }
  ],
  "stats": {
    "total_offers": 8,
    "pending": 2,
    "accepted": 1
  }
}
```

#### Get Offer Details

```
GET /api/nurse-requests/nurse/my-offers/{request_id}/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "patient_name": "Ahmed Sifi",
    "service": {
      "id": 1,
      "name": "Basic Wound Care",
      "description": "Professional wound cleaning and dressing",
      "base_price": "50.00"
    },
    "status": "ACCEPTED",
    "final_price": "75.00",
    "offers": [
      {
        "id": 12,
        "nurse_id": 10,
        "offered_price": "75.00",
        "status": "ACCEPTED"
      }
    ],
    "accepted_at": "2024-04-18T10:50:00Z",
    "started_at": null,
    "completed_at": null,
    "city": "Algiers",
    "latitude": "36.7372",
    "longitude": "3.0588"
  }
}
```

---

### 6. Manage Service Lifecycle

#### Mark Service as Started

```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/start/
Authorization: Bearer <token>
```

**Status Change:** ACCEPTED → IN_PROGRESS

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "status": "IN_PROGRESS",
    "started_at": "2024-04-18T11:00:00Z"
  },
  "message": "Service started"
}
```

#### Mark Service as Completed

```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/complete/
Authorization: Bearer <token>
```

**Status Change:** IN_PROGRESS → COMPLETED

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "status": "COMPLETED",
    "completed_at": "2024-04-18T12:00:00Z",
    "final_price": "75.00"
  },
  "message": "Service completed successfully"
}
```

---

### 7. View Service History

#### List Your Accepted & Completed Services

```
GET /api/nurse-requests/nurse/request-history/
Authorization: Bearer <token>
```

**Query Parameters:**
- `status`: Filter by request status (ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED)
- `date_from`: Filter from date (YYYY-MM-DD format)
- `date_to`: Filter until date (YYYY-MM-DD format)
- `patient_name`: Filter by partial patient name
- `ordering`: Sort by field (-completed_at, final_price, etc.)
- `page`: Pagination page number
- `page_size`: Results per page

**Examples:**
```
GET /api/nurse-requests/nurse/request-history/?status=COMPLETED
GET /api/nurse-requests/nurse/request-history/?date_from=2024-04-01&date_to=2024-04-30
GET /api/nurse-requests/nurse/request-history/?ordering=-completed_at
```

**Response:**
```json
{
  "success": true,
  "count": 12,
  "results": [
    {
      "id": 45,
      "service_name": "Basic Wound Care",
      "patient_name": "A. S.",
      "patient_initials": "AS",
      "status": "COMPLETED",
      "status_display": "Completed",
      "final_price": "75.00",
      "base_price": "50.00",
      "accepted_at": "2024-04-18T10:50:00Z",
      "started_at": "2024-04-18T11:00:00Z",
      "completed_at": "2024-04-18T12:00:00Z",
      "city": "Algiers",
      "can_leave_review": true,
      "nurse_review": null,
      "patient_review": {
        "id": "uuid-1",
        "rating": 5,
        "text": "Excellent service, very professional",
        "created_at": "2024-04-18T13:00:00Z"
      },
      "created_at": "2024-04-18T10:30:00Z"
    }
  ],
  "stats": {
    "total_accepted": 5,
    "total_in_progress": 1,
    "total_completed": 12,
    "total_cancelled": 2
  }
}
```

#### Get History Detail

```
GET /api/nurse-requests/nurse/request-history/{request_id}/
Authorization: Bearer <token>
```

---

### 8. Leave Reviews for Patients

After completing a service, you can review the patient:

```
POST /api/reviews/
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 5,
  "text": "Excellent patient! Very cooperative and easy to work with.",
  "reviewed_content_type": "user",
  "reviewed_object_id": "5",
  "context_content_type": "nurseservicerequest",
  "context_object_id": "45"
}
```

**Fields:**
- `rating` (1-5): Your rating of the patient
- `text`: Your review comment
- `reviewed_content_type`: "user" (patient is a user)
- `reviewed_object_id`: Patient's user ID
- `context_content_type`: "nurseservicerequest"
- `context_object_id`: Request ID

---

## Step-by-Step Workflows

### Complete Nurse Journey - From Profile Setup to Service Completion

#### Phase 1: Initial Setup (One-Time)

**Step 1: Complete Profile**
- Fill in personal information
- Add professional credentials
- Upload profile photo
- Set service area (default 50 km)
- Status: Profile complete

**Step 2: Add Initial Services**
```
GET /api/nurse-requests/nurse/my-services/
Review available services list

POST /api/nurse-requests/nurse/my-services/add/
Add 2-3 services you commonly provide
Set custom prices if different from base
```

**Step 3: Verify Address**
- Set work location (for distance calculation)
- Ensure coordinates are accurate
- Status: Ready to receive requests

---

#### Phase 2: Receiving & Responding to Requests (Daily)

**Step 1: Check Available Requests**
```
GET /api/nurse-requests/nurse/available-requests/
Displays requests matching your services
Shows: Patient price, distance, location, service type
Refresh: Every 5-10 seconds for new requests
```

**Step 2: Review Request Details**
```
GET /api/nurse-requests/nurse/available-requests/{request_id}/
Check patient address line, special notes
Estimate travel time and distance
Decision: Accept at patient's price or counter-offer?
```

**Step 3: Submit Offer - Option A (Accept at Patient's Price)**
```
POST /api/nurse-requests/nurse/available-requests/{request_id}/accept/
Body: estimated_arrival_time, distance_km, notes
Status: PENDING (waiting for patient decision)
Display: "Offer submitted! Waiting for patient response..."
```

**Step 3: Submit Offer - Option B (Counter-Offer)**
```
POST /api/nurse-requests/nurse/available-requests/{request_id}/counter-offer/
Body: offered_price (must be > patient's offer), ETA, notes
Status: PENDING (waiting for patient decision)
Display: "Counter-offer submitted at {price} DZD"
```

**Step 4: Wait for Patient Response**
```
Poll: GET /api/nurse-requests/nurse/my-offers/?offer_status=PENDING
Every 10-15 seconds

Possible Outcomes:
- Offer ACCEPTED: Status → ACCEPTED
- Offer REJECTED: Status → REJECTED (patient chose another nurse)
- Expired: Timeout (usually 15-30 minutes)
```

---

#### Phase 3: Service Delivery

**Step 1: Offer Accepted**
```
Status: ACCEPTED
GET /api/nurse-requests/nurse/my-offers/{request_id}/
Shows accepted nurse profile, address, final price
Display: Patient details, location, service requirements
Action: Prepare equipment, travel to location
```

**Step 2: Arrive at Patient Location**
```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/start/
Status: IN_PROGRESS
Timestamp: started_at recorded
Display: Service timer, location on map
```

**Step 3: Provide Service**
```
Execute nursing service per patient's requirements
Follow any special instructions from patient
Maintain professional standards
Ensure patient comfort and safety
```

**Step 4: Complete Service**
```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/complete/
Status: COMPLETED
Timestamp: completed_at recorded
Final Price: final_price recorded
Display: Service receipt, rating option
```

---

#### Phase 4: Post-Service

**Step 1: Option to Review Patient**
```
GET /api/nurse-requests/nurse/request-history/{request_id}/
If can_leave_review = true:
  POST /api/reviews/
  Submit 1-5 star rating and comments
```

**Step 2: Track Earnings**
```
GET /api/nurse-requests/nurse/request-history/?status=COMPLETED
View: All completed services
Aggregate: Total earnings, average rating, service count
```

**Step 3: Check Your Reputation**
```
Monitor: Your profile rating (aggregate of all patient reviews)
Track: Completed service count
View: Recent reviews from patients
Strategy: Maintain high rating for better offers
```

---

## Offer Management Strategy

### Decision Tree for Responding to Requests

```
Is this request for a service I offer?
├─ NO → Cannot respond (add service to profile first)
└─ YES
   ├─ Can I reach patient in time?
   │  ├─ NO → REJECT (too far, can't service efficiently)
   │  └─ YES
   │     ├─ Is patient's offered price acceptable?
   │     │  ├─ YES (≥ my minimum acceptable price)
   │     │  │  └─ ACCEPT at patient's price
   │     │  │     (Quick response increases acceptance chance)
   │     │  └─ NO (< my minimum acceptable price)
   │     │     ├─ Is counter-offer viable?
   │     │     │  ├─ YES (patient might accept higher)
   │     │     │  │  └─ COUNTER-OFFER
   │     │     │  │     (Higher price, risk patient rejection)
   │     │     │  └─ NO (too low even for counter)
   │     │     │     └─ REJECT (not profitable)
```

### Pricing Strategy Tips

1. **Accept at Patient's Price**: Faster acceptance, builds rating
2. **Counter-Offer**: Higher earnings if patient agrees
3. **Balance Act**: 
   - Counter too often → Lower acceptance rate
   - Accept too often → Lower earnings
   - Find your optimal rate (typically 60-70% acceptance rate)

### Visibility Strategy

```
Services Added to Profile = Requests Visibility
More Services = More Requests = More Opportunities
But: Only add services you're confident providing
     Quality > Quantity (maintain high ratings)
```

---

## Error Handling

### Common Error Codes

| Code | Message | Solution |
|------|---------|----------|
| NR3001 | Request not found | Request may have been accepted by another nurse |
| NR3003 | Invalid request status | Request status changed (no longer SEARCHING) |
| NR3007 | Service not in profile | Must add service to profile first |
| NR4003 | Offer already submitted | You already offered on this request |
| NR6003 | Not a nurse | Your account is not a nurse profile |
| NR6004 | Nurse profile not found | Complete your nurse profile first |
| NR6005 | Nurse not verified | Your nurse credentials need verification |
| NR2002 | Price below minimum | Counter-offer below patient's offer + base price |

### Example Error Response

```json
{
  "success": false,
  "error": {
    "code": "NR3007",
    "message": "You cannot respond to this request because you do not offer \"IV Administration\" service.",
    "details": {
      "service_id": 2,
      "service_name": "IV Administration",
      "action": "Add this service to your profile first"
    }
  }
}
```

---

## Best Practices

### For Nurse App Developers

1. **Real-time Request Flow**
   - Poll `/api/nurse-requests/nurse/available-requests/` every 5-10 seconds
   - Show notifications for NEW requests (sound + visual)
   - Update "my_offer" status in real-time
   - Show accepted offer immediately

2. **Smart Offer Decisions**
   - Display profit margin (offered_price - base_price)
   - Show distance and estimated travel time
   - Sort requests by distance, price, or urgency
   - Allow quick one-tap accept

3. **Service Management**
   - Display current status of each service (available/unavailable)
   - Show custom price vs base price clearly
   - Allow bulk toggle for multiple services
   - Warn if removing popular service

4. **Performance Optimization**
   - Cache service list locally
   - Implement smart polling (exponential backoff if no new requests)
   - Use WebSocket for real-time offer status updates
   - Paginate large history lists

5. **User Experience**
   - Clear status indicators (PENDING, ACCEPTED, REJECTED, EXPIRED)
   - Show expected earnings per request
   - Display patient reviews before responding
   - Allow quick counter-offer with pre-filled values

6. **Navigation Flow**
   ```
   Available Requests (Home)
   ├─ Request List (with filters)
   ├─ Request Details (map, patient info, notes)
   ├─ My Offers (pending, accepted, rejected)
   ├─ My Services (add, remove, toggle availability)
   ├─ Request History (completed services, ratings)
   └─ Profile Settings
   ```

7. **Offer Decision UI**
   ```
   Show:
   - Patient offered price: 75.00 DZD
   - Base price: 50.00 DZD
   - Your profit: 25.00 DZD
   - Distance: 3.5 km
   - Estimated time: 25 minutes
   
   Options:
   [Accept at 75.00 DZD] [Counter-Offer] [Decline]
   ```

### Key UX Considerations

1. **Quick Response is Better**
   - First nurse to offer often gets accepted
   - Optimize UI for fast offer submission

2. **Accept vs Counter Trade-off**
   - Acceptance Rate decreases with counter-offers
   - Show acceptance probability based on price difference

3. **Service Area Management**
   - Show distance clearly
   - Warn if request is outside service area
   - Allow manual override for nearby requests

4. **Earnings Tracking**
   - Show total earnings for period
   - Average earnings per service
   - Most profitable service type
   - Motivate with earnings goals

5. **Rating Protection**
   - Show patient's name anonymized
   - Show service history with ratings
   - Remind about importance of good reviews

### Recommended App Tabs

```
1. Available Requests (Primary Tab)
   - List of available requests
   - Filters: Service type, distance, price
   - Quick actions: Accept, Counter-Offer, Decline

2. My Offers (Secondary Tab)
   - Pending offers (awaiting patient decision)
   - Accepted offers (ready to serve)
   - Completed offers (for review/reference)

3. My Services (Settings Tab)
   - Add/remove services
   - Toggle availability
   - Set custom prices

4. Earnings (Analytics Tab)
   - Total earnings this month
   - Service breakdown
   - Rating and reviews

5. Profile (Account Tab)
   - Edit profile info
   - Update credentials
   - Change availability status
```

---

## Contact & Support

For API issues or feature requests, contact the backend team.
For more details, refer to the main API documentation.
