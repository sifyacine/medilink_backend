# Medilink Patient App - Nurse Requests API Documentation

Complete API reference for patient-facing nurse service request endpoints. Patients can browse nursing services, create requests, manage offers, and leave reviews.

**Base URL:** `https://api.medilink.com/api/nurse-requests`  
**Authentication:** Bearer Token (JWT)  
**Default Pagination:** 20 items per page

---

## 📋 Table of Contents

1. [Service Browsing](#service-browsing)
2. [Request Management](#request-management)
3. [Offer Management](#offer-management)
4. [Service Completion & Reviews](#service-completion--reviews)
5. [Error Codes](#error-codes)

---

## 🏥 Service Browsing

### List All Available Nursing Services

Browse the complete catalog of on-demand nursing services.

**Endpoint:**
```
GET /services/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

**Response (200 OK):**
```json
{
  "success": true,
  "count": 8,
  "results": [
    {
      "id": 1,
      "name": "Home Care Nursing",
      "description": "Professional nursing care at your home",
      "base_price": "150.00",
      "estimated_duration": "01:00:00",
      "is_active": true,
      "icon": "https://cdn.medilink.com/icons/nursing.png",
      "currency": "DZD",
      "is_home_service": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-03-20T14:30:00Z"
    },
    {
      "id": 2,
      "name": "Wound Care",
      "description": "Professional wound treatment and dressing",
      "base_price": "200.00",
      "estimated_duration": "00:45:00",
      "is_active": true,
      "icon": "https://cdn.medilink.com/icons/wound-care.png",
      "currency": "DZD",
      "is_home_service": true,
      "created_at": "2024-01-20T09:00:00Z",
      "updated_at": "2024-03-22T11:15:00Z"
    }
  ],
  "message": "Select a service to request a nurse"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token

---

### Get Service Details

Get detailed information about a specific nursing service.

**Endpoint:**
```
GET /services/{id}/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Service ID |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Home Care Nursing",
    "description": "Professional nursing care at your home",
    "base_price": "150.00",
    "estimated_duration": "01:00:00",
    "is_active": true,
    "icon": "https://cdn.medilink.com/icons/nursing.png",
    "currency": "DZD",
    "is_home_service": true,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-03-20T14:30:00Z"
  },
  "available_nurses_count": 12,
  "message": "12 nurses available for this service"
}
```

**Error Responses:**
- `404 Not Found` - Service not found (error code: `NR1001`)

---

## 📝 Request Management

### Create a New Nurse Service Request

Create a new on-demand nursing service request.

**Endpoint:**
```
POST /patient/nurse-requests/
```

**Request Body:**
```json
{
  "service": 1,
  "patient_offered_price": "175.00",
  "latitude": 36.7538,
  "longitude": 3.0588,
  "city": "Algiers",
  "state": "Algiers",
  "address_line": "123 Main Street, Apartment 4B",
  "notes": "Please arrive between 2-3 PM, call before coming"
}
```

**Request Fields:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| service | integer | Yes | Valid service ID | Nursing service to request |
| patient_offered_price | decimal | Yes | >= base_price | Price patient offers to pay |
| latitude | decimal | Yes | -90 to 90 | Decimal degrees latitude |
| longitude | decimal | Yes | -180 to 180 | Decimal degrees longitude |
| city | string | Yes | Max 100 chars | City for the service |
| state | string | No | Max 100 chars | State/province (optional) |
| address_line | string | No | Max 500 chars | Detailed address (optional) |
| notes | string | No | Unlimited | Special instructions for nurse |

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "patient_user": 123,
    "patient_record": null,
    "patient_name": "Ahmed Ben Ali",
    "service": {
      "id": 1,
      "name": "Home Care Nursing",
      "description": "Professional nursing care at your home",
      "base_price": "150.00",
      "estimated_duration": "01:00:00",
      "is_active": true,
      "currency": "DZD",
      "is_home_service": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-03-20T14:30:00Z"
    },
    "accepted_nurse": null,
    "accepted_nurse_name": null,
    "accepted_nurse_profile": null,
    "base_price": "150.00",
    "patient_offered_price": "175.00",
    "final_price": null,
    "address": null,
    "address_details": null,
    "latitude": "36.7538",
    "longitude": "3.0588",
    "city": "Algiers",
    "state": "Algiers",
    "address_line": "123 Main Street, Apartment 4B",
    "country": "Algeria",
    "status": "SEARCHING",
    "notes": "Please arrive between 2-3 PM, call before coming",
    "offers": [],
    "created_at": "2024-04-15T14:30:00Z",
    "updated_at": "2024-04-15T14:30:00Z",
    "accepted_at": null,
    "started_at": null,
    "completed_at": null,
    "cancelled_at": null,
    "cancellation_reason": "",
    "can_leave_review": false
  },
  "message": "Request created successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Validation error (see error codes)
  - `NR1002` - Service is inactive
  - `NR1003` - Service is not a nursing service
  - `NR1004` - Service is not available for on-demand requests
  - `NR2001` - Patient offered price is below base price
- `404 Not Found` - Service not found (`NR1001`)

---

### List My Requests

Get all your nurse service requests with filtering options.

**Endpoint:**
```
GET /patient/nurse-requests/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by status (CREATED, SEARCHING, NURSE_RESPONDED, etc.) |
| is_active | boolean | - | Show active requests only (SEARCHING, ACCEPTED, IN_PROGRESS) |
| is_history | boolean | - | Show historical requests only (COMPLETED, CANCELLED) |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

**Example:**
```
GET /patient/nurse-requests/?status=COMPLETED&page=1
```

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 45,
      "service_name": "Home Care Nursing",
      "patient_name": "Ahmed Ben Ali",
      "status": "COMPLETED",
      "patient_offered_price": "175.00",
      "final_price": "175.00",
      "city": "Algiers",
      "latitude": "36.7538",
      "longitude": "3.0588",
      "offers_count": 3,
      "created_at": "2024-04-15T14:30:00Z",
      "updated_at": "2024-04-15T16:30:00Z"
    }
  ]
}
```

---

### Get Request Details

Get detailed information about a specific request.

**Endpoint:**
```
GET /patient/nurse-requests/{id}/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Request ID |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 45,
    "patient_user": 123,
    "patient_record": null,
    "patient_name": "Ahmed Ben Ali",
    "service": { ... },
    "accepted_nurse": 67,
    "accepted_nurse_name": "Fatima Ahmed",
    "accepted_nurse_profile": {
      "first_name": "Fatima",
      "last_name": "Ahmed",
      "phone_number": "+213-555-1234",
      "profile_image": "https://cdn.medilink.com/profiles/nurse-67.jpg",
      "average_rating": 4.8,
      "review_count": 24
    },
    "base_price": "150.00",
    "patient_offered_price": "175.00",
    "final_price": "175.00",
    "latitude": "36.7538",
    "longitude": "3.0588",
    "city": "Algiers",
    "state": "Algiers",
    "address_line": "123 Main Street, Apartment 4B",
    "country": "Algeria",
    "status": "IN_PROGRESS",
    "notes": "Please arrive between 2-3 PM",
    "offers": [
      {
        "id": 123,
        "nurse_id": 67,
        "nurse_name": "F. Ahmed",
        "nurse_rating": 4.8,
        "nurse_review_count": 24,
        "nurse_profile_image": "https://cdn.medilink.com/profiles/nurse-67.jpg",
        "nurse_years_experience": 5,
        "nurse_completed_services": 156,
        "nurse_biography": "Experienced nurse with 5 years in home care...",
        "nurse_is_verified": true,
        "offered_price": "175.00",
        "status": "ACCEPTED",
        "estimated_arrival_time": "00:30:00",
        "distance_km": "2.50",
        "notes": "I'm on my way",
        "created_at": "2024-04-15T14:45:00Z",
        "responded_at": "2024-04-15T14:45:00Z"
      }
    ],
    "created_at": "2024-04-15T14:30:00Z",
    "updated_at": "2024-04-15T15:00:00Z",
    "accepted_at": "2024-04-15T14:50:00Z",
    "started_at": "2024-04-15T15:10:00Z",
    "completed_at": null,
    "cancelled_at": null,
    "cancellation_reason": "",
    "can_leave_review": false
  }
}
```

---

## 💰 Offer Management

### Accept a Nurse Offer

Accept an offer from a specific nurse and lock in the service.

**Endpoint:**
```
POST /patient/nurse-requests/{id}/accept/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Request ID |

**Request Body:**
```json
{
  "offer_id": 123
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": { ... },
  "message": "Offer accepted! The nurse will be on their way."
}
```

**Error Responses:**
- `403 Forbidden` - Not the request owner (`NR3002`)
- `400 Bad Request` - Invalid state
  - `NR3005` - Request already has accepted offer
  - `NR3004` - Request is cancelled
  - `NR3006` - Request is completed
  - `NR3003` - Cannot accept at this stage
  - `NR4002` - Offer not available (`NR4002`)

---

### Decline a Nurse Offer

Decline a specific offer and continue reviewing other options.

**Endpoint:**
```
POST /patient/nurse-requests/{id}/decline-offer/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Request ID |

**Request Body:**
```json
{
  "offer_id": 123,
  "reason": "Looking for another option"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| offer_id | integer | Yes | ID of offer to decline |
| reason | string | No | Reason for declining (optional) |

**Response (200 OK):**
```json
{
  "success": true,
  "data": { ... },
  "message": "Offer declined. You can continue reviewing other offers."
}
```

**Error Responses:**
- `403 Forbidden` - Not the request owner (`NR3002`)
- `400 Bad Request` - Invalid state
  - `NR3005` - Request already accepted
  - `NR3004` - Request is cancelled
  - `NR3006` - Request is completed
  - `NR4002` - Offer not available

---

### Cancel Request

Cancel your entire service request.

**Endpoint:**
```
POST /patient/nurse-requests/{id}/cancel/
```

**Request Body:**
```json
{
  "cancellation_reason": "Changed my mind"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": { ... },
  "message": "Request cancelled successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid state
  - `NR3004` - Already cancelled
  - `NR3006` - Already completed

---

## ✅ Service Completion & Reviews

### Mark Service as Completed

Mark the service as completed (call this when nurse finishes).

**Endpoint:**
```
POST /patient/nurse-requests/{id}/complete/
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": { ... },
  "message": "Service completed successfully"
}
```

---

### Submit a Review

Leave a rating and review for the nurse.

**Endpoint:**
```
POST /api/reviews/
```

**Request Body:**
```json
{
  "target_type": "provider",
  "target_id": "67",
  "context_type": "nurseservicerequest",
  "context_id": "45",
  "rating": 5,
  "title": "Excellent professional service",
  "text": "Fatima was very professional and caring. She explained everything she was doing and made sure I was comfortable."
}
```

**Request Fields:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| target_type | string | Yes | "provider" | Type of entity being reviewed (nurse provider) |
| target_id | string | Yes | Valid provider ID | ID of the nurse to review |
| context_type | string | Yes | "nurseservicerequest" | Type of service context |
| context_id | string | Yes | Valid request ID | ID of the completed request |
| rating | integer | Yes | 1-5 | Star rating (1-5) |
| title | string | No | Max 255 chars | Review title (optional) |
| text | string | No | Unlimited | Detailed review text (optional) |

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "reviewer_name": "Ahmed Ben Ali",
    "rating": 5,
    "title": "Excellent professional service",
    "text": "Fatima was very professional and caring...",
    "status": "ACTIVE",
    "helpful_count": 0,
    "created_at": "2024-04-16T10:00:00Z",
    "updated_at": "2024-04-16T10:00:00Z"
  },
  "message": "Review submitted successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Validation error
  - Duplicate review for same nurse/request combination
  - Rating outside 1-5 range
  - Invalid target or context IDs

---

### View Nurse Reviews

View all reviews for a specific nurse.

**Endpoint:**
```
GET /api/reviews/?target_type=provider&target_id={nurse_id}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target_type | string | Yes | "provider" |
| target_id | string | Yes | Nurse provider ID |
| min_rating | integer | No | Minimum rating (1-5) |
| max_rating | integer | No | Maximum rating (1-5) |
| page | integer | No | Pagination page |
| page_size | integer | No | Results per page |

**Response (200 OK):**
```json
{
  "success": true,
  "count": 24,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "reviewer_name": "A. B.",
      "rating": 5,
      "title": "Excellent professional",
      "text": "Very professional and caring nurse...",
      "status": "ACTIVE",
      "helpful_count": 12,
      "created_at": "2024-04-16T10:00:00Z"
    }
  ],
  "average_rating": 4.8,
  "review_count": 24,
  "rating_distribution": {
    "1": 0,
    "2": 1,
    "3": 2,
    "4": 5,
    "5": 16
  }
}
```

---

## 📲 Notifications

### Get My Notifications

**Endpoint:**
```
GET /api/notifications/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| is_read | boolean | - | Filter by read status |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

---

### Mark All Notifications as Read

**Endpoint:**
```
POST /api/notifications/mark-all-read/
```

---

### Mark Single Notification as Read

**Endpoint:**
```
PATCH /api/notifications/{id}/read/
```

---

## 🔴 Error Codes

| Code | HTTP | Meaning | Action |
|------|------|---------|--------|
| NR1001 | 404 | Service not found | Check service ID |
| NR1002 | 400 | Service inactive | Choose an active service |
| NR1003 | 400 | Not a nursing service | Select a nursing service |
| NR1004 | 400 | Not on-demand | Service doesn't support on-demand requests |
| NR2001 | 400 | Price too low | Offered price must be ≥ base price |
| NR3001 | 404 | Request not found | Check request ID |
| NR3002 | 403 | Not request owner | Only request creator can modify |
| NR3003 | 400 | Invalid status | Request is in wrong state |
| NR3004 | 400 | Already cancelled | Request was already cancelled |
| NR3005 | 400 | Already accepted | Request already has accepted offer |
| NR3006 | 400 | Already completed | Request already completed |
| NR4001 | 404 | Offer not found | Check offer ID |
| NR4002 | 400 | Offer unavailable | Offer is no longer available |
| NR5001 | 400 | Location required | Latitude and longitude required |
| NR6001 | 401 | Not authenticated | Provide valid JWT token |
| NR6002 | 403 | Not a patient | User role must be patient |

---

## 📊 Status Values

Requests can have one of these statuses:

- `CREATED` - Just created, not yet searching
- `SEARCHING` - Actively searching for nurses
- `NURSE_RESPONDED` - At least one nurse has responded
- `PATIENT_DECISION` - Awaiting patient to decide
- `ACCEPTED` - Nurse offer accepted, waiting to start
- `IN_PROGRESS` - Service is currently happening
- `COMPLETED` - Service finished
- `CANCELLED` - Request cancelled

Offers can have one of these statuses:

- `PENDING` - Initial state, waiting for response
- `ACCEPTED` - Patient accepted this offer
- `REJECTED` - Patient chose different nurse or declined
- `COUNTER_OFFERED` - Nurse proposed higher price
- `EXPIRED` - Request was cancelled
