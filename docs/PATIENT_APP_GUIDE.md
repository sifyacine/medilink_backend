# Patient App - Nurse Requests Guide

## Overview

The Patient App enables patients to request on-demand nursing services through a simple, Uber-like flow. Patients can browse available nursing services, create requests, receive offers from nearby nurses, and manage their service history.

---

## Table of Contents

1. [Workflow Overview](#workflow-overview)
2. [Key Concepts](#key-concepts)
3. [Request Status Flow](#request-status-flow)
4. [API Endpoints](#api-endpoints)
5. [Step-by-Step Workflows](#step-by-step-workflows)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## Workflow Overview

### Complete Nurse Request Journey

```
1. Browse Services
   ↓
2. Create Request (with location & price offer)
   ↓
3. Wait for Nurses to Respond (Nurses see your request and submit offers)
   ↓
4. Review Offers (Compare nurses' profiles, ratings, prices)
   ↓
5. Accept Best Offer (Choose your preferred nurse)
   ↓
6. Service In Progress (Nurse travels to location and provides service)
   ↓
7. Complete Service (Mark complete, pay the agreed price)
   ↓
8. Leave Review (Rate the nurse and provide feedback)
```

---

## Key Concepts

### Request Status Flow

| Status | Description | Patient Action Available |
|--------|-------------|--------------------------|
| **CREATED** | Request just created, not yet broadcasted | Cancel |
| **SEARCHING** | Actively searching for nurses, awaiting responses | Cancel, View offers (if any) |
| **NURSE_RESPONDED** | One or more nurses have submitted offers | Accept offer, Decline offers, Cancel |
| **PATIENT_DECISION** | Patient reviewing offers before acceptance | Accept offer, Decline offers, Cancel |
| **ACCEPTED** | Nurse offer accepted, waiting for service | Cancel before service starts |
| **IN_PROGRESS** | Service has started by nurse | None (wait for completion) |
| **COMPLETED** | Service finished successfully | Leave review |
| **CANCELLED** | Request cancelled by patient or system | None (view in history) |

### Offer Status Flow

| Offer Status | Description | Patient Action |
|--------------|-------------|-----------------|
| **PENDING** | Nurse submitted offer, waiting for patient response | Accept or Decline |
| **ACCEPTED** | Patient accepted this offer | None |
| **REJECTED** | Patient declined this offer | None |
| **COUNTER_OFFERED** | Nurse made a higher counter-offer | Accept or Decline |
| **EXPIRED** | Offer expired without response | None |

---

## API Endpoints

### 1. Browse Nursing Services

#### Get All Available Services
```
GET /api/nurse-requests/services/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "Basic Wound Care",
      "description": "Professional wound cleaning and dressing",
      "base_price": "50.00",
      "estimated_duration": "00:30:00",
      "is_active": true,
      "icon": "https://...",
      "currency": "DZD",
      "is_home_service": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "message": "Select a service to request a nurse"
}
```

#### Get Service Details with Nurse Count
```
GET /api/nurse-requests/services/{service_id}/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Basic Wound Care",
    "description": "Professional wound cleaning and dressing",
    "base_price": "50.00",
    "estimated_duration": "00:30:00",
    "is_active": true,
    "icon": "https://...",
    "currency": "DZD",
    "is_home_service": true,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  },
  "available_nurses_count": 12,
  "message": "12 nurses available for this service"
}
```

---

### 2. Get Patient's Saved Addresses

```
GET /api/nurse-requests/patient/nurse-requests/saved-addresses/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "count": 3,
  "results": [
    {
      "id": 1,
      "street": "123 Main St",
      "city": "Algiers",
      "state": "Algiers",
      "zip_code": "16000",
      "country": "Algeria",
      "latitude": "36.7372",
      "longitude": "3.0588",
      "is_primary": true,
      "address_type": "HOME",
      "full_address": "123 Main St, Algiers, Algiers, Algeria",
      "has_coordinates": true
    }
  ],
  "message": "Select a saved address or choose location from map"
}
```

---

### 3. Create Nurse Service Request

#### Method 1: Create with Map Location

```
POST /api/nurse-requests/patient/nurse-requests/
Authorization: Bearer <token>
Content-Type: application/json

{
  "service": 1,
  "patient_offered_price": "75.00",
  "latitude": "36.7372",
  "longitude": "3.0588",
  "city": "Algiers",
  "address_line": "123 Main Street, Apartment 5",
  "notes": "Please ring doorbell twice"
}
```

**Required Fields:**
- `service` (integer): Service ID
- `patient_offered_price` (decimal): Your price offer (must be ≥ base_price)
- `latitude` (decimal): Location latitude (-90 to 90)
- `longitude` (decimal): Location longitude (-180 to 180)
- `city` (string): City name

**Optional Fields:**
- `address_line`: Detailed address information
- `notes`: Special instructions for the nurse

**Success Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "patient_user": 5,
    "patient_name": "Ahmed Sifi",
    "service": {
      "id": 1,
      "name": "Basic Wound Care",
      "description": "Professional wound cleaning",
      "base_price": "50.00",
      "estimated_duration": "00:30:00",
      "is_active": true,
      "currency": "DZD",
      "is_home_service": true
    },
    "base_price": "50.00",
    "patient_offered_price": "75.00",
    "final_price": null,
    "latitude": "36.7372",
    "longitude": "3.0588",
    "city": "Algiers",
    "address_line": "123 Main Street, Apartment 5",
    "status": "CREATED",
    "notes": "Please ring doorbell twice",
    "offers": [],
    "created_at": "2024-04-18T10:30:00Z",
    "updated_at": "2024-04-18T10:30:00Z"
  },
  "message": "Request created successfully. Searching for available nurses..."
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "NR2001",
    "message": "Your offered price must be at least the base price",
    "details": {
      "field": "patient_offered_price",
      "messages": ["Ensure this value is greater than or equal to 50.00."]
    }
  }
}
```

#### Method 2: Create with Saved Address

```
POST /api/nurse-requests/patient/nurse-requests/use-saved-address/
Authorization: Bearer <token>
Content-Type: application/json

{
  "service": 1,
  "patient_offered_price": "75.00",
  "address_id": 1,
  "notes": "Please ring doorbell twice"
}
```

**Response:** Same as Method 1

---

### 4. View My Requests

#### List All My Requests

```
GET /api/nurse-requests/patient/nurse-requests/
Authorization: Bearer <token>
```

**Query Parameters:**
- `status`: Filter by status (CREATED, SEARCHING, ACCEPTED, COMPLETED, CANCELLED)
- `is_active`: Filter active requests (true/false)
- `is_history`: Filter completed/cancelled requests (true/false)

**Examples:**
```
GET /api/nurse-requests/patient/nurse-requests/?is_active=true
GET /api/nurse-requests/patient/nurse-requests/?is_history=true
GET /api/nurse-requests/patient/nurse-requests/?status=COMPLETED
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": 45,
      "service_name": "Basic Wound Care",
      "patient_name": "Ahmed Sifi",
      "status": "NURSE_RESPONDED",
      "patient_offered_price": "75.00",
      "final_price": null,
      "city": "Algiers",
      "latitude": "36.7372",
      "longitude": "3.0588",
      "offers_count": 3,
      "created_at": "2024-04-18T10:30:00Z",
      "updated_at": "2024-04-18T10:45:00Z"
    }
  ]
}
```

#### Get Request Details

```
GET /api/nurse-requests/patient/nurse-requests/{request_id}/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "patient_user": 5,
    "patient_name": "Ahmed Sifi",
    "service": {
      "id": 1,
      "name": "Basic Wound Care",
      "description": "Professional wound cleaning",
      "base_price": "50.00"
    },
    "accepted_nurse": null,
    "accepted_nurse_name": null,
    "accepted_nurse_profile": null,
    "base_price": "50.00",
    "patient_offered_price": "75.00",
    "final_price": null,
    "address_details": null,
    "latitude": "36.7372",
    "longitude": "3.0588",
    "city": "Algiers",
    "status": "NURSE_RESPONDED",
    "notes": "Please ring doorbell twice",
    "offers": [
      {
        "id": 1,
        "nurse_id": 10,
        "nurse_name": "Fatima Hadjri",
        "nurse_rating": 4.8,
        "nurse_review_count": 45,
        "nurse_profile_image": "https://...",
        "nurse_years_experience": 8,
        "nurse_completed_services": 120,
        "nurse_biography": "Experienced nurse with over 8 years...",
        "nurse_is_verified": true,
        "offered_price": "75.00",
        "status": "PENDING",
        "estimated_arrival_time": "00:25:00",
        "distance_km": "3.5",
        "notes": "I can be there in 25 minutes",
        "created_at": "2024-04-18T10:35:00Z",
        "responded_at": "2024-04-18T10:35:00Z"
      },
      {
        "id": 2,
        "nurse_id": 12,
        "nurse_name": "Zaineb Nouri",
        "nurse_rating": 4.6,
        "nurse_review_count": 38,
        "nurse_profile_image": "https://...",
        "nurse_years_experience": 6,
        "nurse_completed_services": 95,
        "nurse_biography": "Professional nurse specializing...",
        "nurse_is_verified": true,
        "offered_price": "80.00",
        "status": "PENDING",
        "estimated_arrival_time": "00:35:00",
        "distance_km": "5.2",
        "notes": "Traffic is heavy, might take 35 minutes",
        "created_at": "2024-04-18T10:40:00Z",
        "responded_at": "2024-04-18T10:40:00Z"
      }
    ],
    "can_leave_review": false,
    "created_at": "2024-04-18T10:30:00Z",
    "updated_at": "2024-04-18T10:45:00Z",
    "accepted_at": null,
    "started_at": null,
    "completed_at": null,
    "cancelled_at": null
  }
}
```

---

### 5. Accept a Nurse Offer

```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/accept/
Authorization: Bearer <token>
Content-Type: application/json

{
  "offer_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "status": "ACCEPTED",
    "accepted_nurse": 10,
    "accepted_nurse_name": "Fatima Hadjri",
    "accepted_nurse_profile": {
      "first_name": "Fatima",
      "last_name": "Hadjri",
      "phone_number": "+213612345678",
      "profile_image": "https://...",
      "average_rating": 4.8,
      "review_count": 45
    },
    "final_price": "75.00",
    "accepted_at": "2024-04-18T10:50:00Z",
    "notes": "I can be there in 25 minutes"
  },
  "message": "Offer accepted! The nurse will be on their way."
}
```

**Errors:**
```json
{
  "success": false,
  "error": {
    "code": "NR4002",
    "message": "This offer is no longer available",
    "details": {
      "field": "offer_id",
      "messages": ["Validation failed"]
    }
  }
}
```

---

### 6. Decline an Offer (Optional - Keep Reviewing Others)

```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/decline_offer/
Authorization: Bearer <token>
Content-Type: application/json

{
  "offer_id": 2,
  "reason": "Looking for closer nurse"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "status": "PATIENT_DECISION",
    "offers": [
      {
        "id": 1,
        "nurse_id": 10,
        "nurse_name": "Fatima Hadjri",
        "offered_price": "75.00",
        "status": "PENDING"
      }
    ]
  },
  "message": "Offer declined. You can continue reviewing other offers."
}
```

---

### 7. View Nurse Profile Before Accepting

```
GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-profile/{nurse_id}/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 10,
    "first_name": "Fatima",
    "last_name": "Hadjri",
    "full_name": "Fatima Hadjri",
    "profile_image": "https://...",
    "biography": "Experienced nurse with over 8 years in home nursing care...",
    "license_number": "NL-12345678",
    "certification": "RN - Bachelor of Science in Nursing",
    "years_of_experience": 8,
    "is_verified": true,
    "is_available": true,
    "is_home_service_available": true,
    "average_rating": 4.8,
    "review_count": 45,
    "rating_distribution": {
      "1": 0,
      "2": 1,
      "3": 2,
      "4": 8,
      "5": 34
    },
    "recent_reviews": [
      {
        "id": "uuid-1",
        "rating": 5,
        "text": "Excellent service, very professional and caring",
        "created_at": "2024-04-15T14:30:00Z",
        "has_response": true
      }
    ],
    "completed_services_count": 120,
    "services_offered": [
      {
        "id": 1,
        "title": "Basic Wound Care",
        "price": "75.00 DZD",
        "duration_minutes": 30
      }
    ]
  },
  "offer": {
    "id": 1,
    "offered_price": "75.00",
    "status": "PENDING",
    "estimated_arrival_time": "00:25:00",
    "notes": "I can be there in 25 minutes"
  },
  "message": "Nurse profile retrieved successfully"
}
```

---

### 8. View Nurse's Service History

```
GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-history/{nurse_id}/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 40,
      "service_title": "Basic Wound Care",
      "patient_name": "A. S.",
      "completed_at": "2024-04-10T15:00:00Z",
      "final_price": "75.00",
      "review": {
        "rating": 5,
        "text": "Very professional and caring service"
      }
    }
  ],
  "message": "Nurse service history retrieved"
}
```

---

### 9. Cancel a Request

```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/cancel/
Authorization: Bearer <token>
Content-Type: application/json

{
  "cancellation_reason": "Found another service provider"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "status": "CANCELLED",
    "cancellation_reason": "Found another service provider",
    "cancelled_at": "2024-04-18T11:00:00Z"
  },
  "message": "Request cancelled successfully"
}
```

**Allowed Statuses for Cancellation:**
- CREATED
- SEARCHING
- NURSE_RESPONDED
- PATIENT_DECISION
- ACCEPTED

**Cannot Cancel:**
- IN_PROGRESS (service already started)
- COMPLETED (service already finished)
- CANCELLED (already cancelled)

---

### 10. Mark Service as Complete

```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/complete/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "status": "COMPLETED",
    "completed_at": "2024-04-18T12:00:00Z",
    "final_price": "75.00",
    "can_leave_review": true
  },
  "message": "Service completed successfully"
}
```

---

### 11. Leave a Review for Completed Service

This endpoint is handled by the Reviews API. See Reviews Documentation for details.

```
POST /api/reviews/
Authorization: Bearer <token>
Content-Type: application/json

{
  "rating": 5,
  "text": "Excellent service! Very professional and caring.",
  "reviewed_content_type": "provider",
  "reviewed_object_id": "10",
  "context_content_type": "nurseservicerequest",
  "context_object_id": "45"
}
```

---

## Step-by-Step Workflows

### Complete Patient Journey - From Request to Review

#### Step 1: Browse Services (App Loads)
```
GET /api/nurse-requests/services/
Display: List of available nursing services with prices and duration
Action: User selects a service
```

#### Step 2: Prepare Location
```
Option A - Use Saved Address:
  GET /api/nurse-requests/patient/nurse-requests/saved-addresses/
  Display: List of saved addresses
  Action: User selects an address

Option B - Choose on Map:
  Display: Map interface for location selection
  Get: Latitude, longitude, city from map
```

#### Step 3: Create Request
```
POST /api/nurse-requests/patient/nurse-requests/
Body: service, patient_offered_price, location info, notes
Status: CREATED
Action: System broadcasts to nearby nurses
```

#### Step 4: Wait for Offers
```
Status: SEARCHING → NURSE_RESPONDED
GET /api/nurse-requests/patient/nurse-requests/{request_id}/
Polling: Every 3-5 seconds to check for new offers
Display: Offers list with nurse info
```

#### Step 5: Review Offers (Optional Enhanced View)
```
For each offer in the list:
  GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-profile/{nurse_id}/
  Display: Full nurse profile with ratings, reviews, services
  
  Optional:
  GET /api/nurse-requests/patient/nurse-requests/{request_id}/nurse-history/{nurse_id}/
  Display: Nurse's service history
```

#### Step 6: Accept Best Offer
```
POST /api/nurse-requests/patient/nurse-requests/{request_id}/accept/
Body: offer_id of chosen nurse
Status: NURSE_RESPONDED → ACCEPTED
Display: Accepted nurse details, ETA
```

#### Step 7: Wait for Nurse (In Progress)
```
Status: ACCEPTED → IN_PROGRESS
Polling: Get request details to track status changes
Display: Nurse location (if available), status updates
```

#### Step 8: Service Completion
```
Status: IN_PROGRESS → COMPLETED
POST /api/nurse-requests/patient/nurse-requests/{request_id}/complete/
Or: Nurse marks complete and system auto-updates
```

#### Step 9: Leave Review
```
POST /api/reviews/
Body: Rating (1-5), review text, reviewed nurse, context request
Display: Confirmation of review submission
```

#### Step 10: View History
```
GET /api/nurse-requests/patient/nurse-requests/?is_history=true
Display: All completed and cancelled requests
Action: View details, reviews of past nurses
```

---

## Error Handling

### Common Error Codes

| Code | Message | Solution |
|------|---------|----------|
| NR1001 | Service not found | Refresh services list and try again |
| NR2001 | Price below base | Increase offered price to at least base price |
| NR3001 | Request not found | Request may have expired or been deleted |
| NR3002 | Not request owner | You don't have permission to access this request |
| NR3003 | Invalid request status | Current request status doesn't allow this action |
| NR3004 | Request already cancelled | Request has been cancelled, cannot modify |
| NR3005 | Request already accepted | Cannot accept multiple offers |
| NR3006 | Request already completed | Cannot modify completed requests |
| NR4001 | Offer not found | Offer has been withdrawn or expired |
| NR4002 | Offer not available | Offer status has changed, try refreshing |
| NR4003 | Offer already submitted | Nurse has already responded to this request |
| NR5001 | Location required | Must provide location coordinates |
| NR5002 | Invalid coordinates | Latitude (-90 to 90), Longitude (-180 to 180) |
| NR5003 | City required | Must specify city name |
| NR5004 | Address not found | Saved address doesn't exist or isn't yours |

### Example Error Response

```json
{
  "success": false,
  "error": {
    "code": "NR2001",
    "message": "Your offered price must be at least the base price",
    "details": {
      "field": "patient_offered_price",
      "messages": ["Your price must be >= 50.00 DZD"]
    }
  }
}
```

---

## Best Practices

### For Patient App Developers

1. **Real-time Updates**
   - Poll `/api/nurse-requests/patient/nurse-requests/{request_id}/` every 3-5 seconds while SEARCHING
   - Display offers in real-time as they arrive
   - Show nurse profiles with ratings before acceptance

2. **Location Handling**
   - Save user's home/work addresses for quick access
   - Allow map-based location selection for one-time requests
   - Always validate coordinates before submission

3. **Price Strategy**
   - Show base price clearly
   - Explain that higher offered price attracts more nurses
   - Allow price adjustment before request creation

4. **User Feedback**
   - Collect reviews after service completion
   - Show nurse ratings prominently during offer selection
   - Display estimated arrival time and distance

5. **Error Handling**
   - Show user-friendly error messages
   - Suggest corrective actions (e.g., "Increase price to 50.00 DZD")
   - Log errors for debugging

6. **Request Lifecycle**
   - Display status updates clearly (SEARCHING → NURSE_RESPONDED → ACCEPTED → IN_PROGRESS → COMPLETED)
   - Allow cancellation at appropriate stages
   - Show cost breakdown (base price, offered price, final price)

7. **Performance**
   - Use pagination when displaying request history
   - Cache service list locally (refresh on app launch)
   - Implement efficient polling (exponential backoff after no changes)

### Recommended UI States

```
Creating Request
  ↓
Searching (Loading spinner, "Searching for nurses...")
  ↓
Offers Received (Display list, sort by price/rating)
  ↓
Offer Selected (Show confirm dialog)
  ↓
Accepted (Show nurse details, ETA, map)
  ↓
In Progress (Show current location, estimated completion)
  ↓
Completed (Show "Rate Nurse" option)
  ↓
Reviewed (Show confirmation)
```

---

## Contact & Support

For API issues or feature requests, contact the backend team.
For more details, refer to the main API documentation.
