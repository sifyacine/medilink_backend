# Medilink Nurse App - Service Requests API Documentation

Complete API reference for nurse-facing service request endpoints. Nurses can browse available requests, submit offers, manage acceptances, and view their service history.

**Base URL:** `https://api.medilink.com/api/nurse-requests`  
**Authentication:** Bearer Token (JWT)  
**Default Pagination:** 20 items per page

---

## 📋 Table of Contents

1. [Available Requests](#available-requests)
2. [Offer Management](#offer-management)
3. [Request History](#request-history)
4. [Reviews & Ratings](#reviews--ratings)
5. [My Services](#my-services)
6. [Error Codes](#error-codes)

---

## 🔍 Available Requests

### Browse Available Requests

Get a list of nursing service requests in your area that you can respond to.

**Endpoint:**
```
GET /nurse/available-requests/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| city | string | - | Filter by city |
| status | string | - | Filter by request status (SEARCHING, NURSE_RESPONDED) |
| service_id | integer | - | Filter by service type |
| date_from | string | - | Filter requests from date (ISO 8601) |
| date_to | string | - | Filter requests until date (ISO 8601) |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

**Example:**
```
GET /nurse/available-requests/?city=Algiers&status=SEARCHING
```

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 45,
      "service_id": 1,
      "service_name": "Home Care Nursing",
      "service_description": "Professional nursing care at your home",
      "patient_name": "A. B.",
      "patient_offered_price": "175.00",
      "base_price": "150.00",
      "latitude": "36.7538",
      "longitude": "3.0588",
      "city": "Algiers",
      "address_line": "123 Main Street, Apartment 4B",
      "status": "SEARCHING",
      "created_at": "2024-04-15T14:30:00Z",
      "my_offer": null
    }
  ]
}
```

---

### Get Request Details

Get detailed information about a specific request before submitting an offer.

**Endpoint:**
```
GET /nurse/available-requests/{id}/
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
    "service_id": 1,
    "service_name": "Home Care Nursing",
    "service_description": "Professional nursing care at your home...",
    "patient_name": "A. B.",
    "patient_offered_price": "175.00",
    "base_price": "150.00",
    "latitude": "36.7538",
    "longitude": "3.0588",
    "city": "Algiers",
    "address_line": "123 Main Street, Apartment 4B",
    "status": "SEARCHING",
    "created_at": "2024-04-15T14:30:00Z",
    "my_offer": {
      "id": 123,
      "status": "PENDING",
      "offered_price": "175.00",
      "estimated_arrival_time": "00:30:00",
      "distance_km": "2.50",
      "notes": "Ready to go",
      "created_at": "2024-04-15T14:45:00Z"
    }
  }
}
```

---

## 💼 Offer Management

### Accept Request (At Patient's Price)

Accept a service request at the patient's offered price.

**Endpoint:**
```
POST /nurse/available-requests/{id}/accept/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Request ID |

**Request Body:**
```json
{
  "estimated_arrival_time": "00:30:00",
  "distance_km": "2.50",
  "notes": "I'm on my way, see you soon"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| estimated_arrival_time | duration | No | ETA (format: HH:MM:SS) |
| distance_km | decimal | No | Distance to patient location |
| notes | string | No | Additional message for patient |

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "request_id": 45,
    "nurse_id": 67,
    "offered_price": "175.00",
    "status": "PENDING",
    "estimated_arrival_time": "00:30:00",
    "distance_km": "2.50",
    "notes": "I'm on my way, see you soon",
    "created_at": "2024-04-15T14:45:00Z"
  },
  "message": "Offer submitted successfully"
}
```

**Error Responses:**
- `400 Bad Request`
  - `NR4003` - You already responded to this request
  - `NR3007` - Service not in your nurse profile
- `403 Forbidden`
  - `NR6005` - Your nurse profile is not verified

---

### Counter Offer (Higher Price)

Make a counter-offer with a higher price than the patient's offer.

**Endpoint:**
```
POST /nurse/available-requests/{id}/counter-offer/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Request ID |

**Request Body:**
```json
{
  "offered_price": "200.00",
  "estimated_arrival_time": "00:30:00",
  "distance_km": "2.50",
  "notes": "Need to charge travel time to remote location"
}
```

**Request Fields:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| offered_price | decimal | Yes | >= patient's offered price | Your proposed price |
| estimated_arrival_time | duration | No | Format HH:MM:SS | ETA to reach patient |
| distance_km | decimal | No | - | Distance to location |
| notes | string | No | - | Message to patient explaining price |

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 124,
    "request_id": 45,
    "nurse_id": 67,
    "offered_price": "200.00",
    "status": "COUNTER_OFFERED",
    "estimated_arrival_time": "00:30:00",
    "distance_km": "2.50",
    "notes": "Need to charge travel time to remote location",
    "created_at": "2024-04-15T14:50:00Z"
  },
  "message": "Counter offer submitted successfully"
}
```

**Error Responses:**
- `400 Bad Request`
  - `NR2002` - Price below patient's offered price
  - `NR2001` - Price below base price
  - `NR4003` - Already responded to this request
- `403 Forbidden`
  - `NR6005` - Nurse profile not verified

---

### Reject Request

Decline a service request.

**Endpoint:**
```
POST /nurse/available-requests/{id}/reject/
```

**Request Body:**
```json
{
  "reason": "Too far from my location"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reason | string | No | Reason for declining |

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Request rejected"
}
```

---

## 📋 Request History

### List Your Request History

View all requests where you were accepted (history of services).

**Endpoint:**
```
GET /nurse/request-history/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by status (ACCEPTED, IN_PROGRESS, COMPLETED, CANCELLED) |
| date_from | string | - | Filter from date (ISO 8601: YYYY-MM-DD) |
| date_to | string | - | Filter until date (ISO 8601: YYYY-MM-DD) |
| patient_name | string | - | Filter by partial patient name |
| ordering | string | -completed_at | Sort field (e.g., -completed_at, final_price) |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

**Example:**
```
GET /nurse/request-history/?status=COMPLETED&date_from=2024-01-01&ordering=-completed_at
```

**Response (200 OK):**
```json
{
  "success": true,
  "count": 12,
  "results": [
    {
      "id": 45,
      "service_name": "Home Care Nursing",
      "patient_name": "A. B.",
      "patient_initials": "AB",
      "status": "COMPLETED",
      "status_display": "Completed",
      "final_price": "175.00",
      "base_price": "150.00",
      "accepted_at": "2024-04-15T14:50:00Z",
      "started_at": "2024-04-15T15:10:00Z",
      "completed_at": "2024-04-15T16:10:00Z",
      "cancelled_at": null,
      "cancellation_reason": "",
      "city": "Algiers",
      "can_leave_review": true,
      "nurse_review": null,
      "patient_review": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "rating": 5,
        "text": "Professional and caring",
        "created_at": "2024-04-16T10:00:00Z"
      },
      "created_at": "2024-04-15T14:30:00Z",
      "updated_at": "2024-04-15T16:10:00Z"
    }
  ],
  "stats": {
    "total_accepted": 45,
    "total_in_progress": 2,
    "total_completed": 40,
    "total_cancelled": 3
  }
}
```

---

### Get History Detail

View detailed information about a past service.

**Endpoint:**
```
GET /nurse/request-history/{id}/
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
    "service_name": "Home Care Nursing",
    "patient_name": "A. B.",
    "patient_initials": "AB",
    "status": "COMPLETED",
    "status_display": "Completed",
    "final_price": "175.00",
    "base_price": "150.00",
    "accepted_at": "2024-04-15T14:50:00Z",
    "started_at": "2024-04-15T15:10:00Z",
    "completed_at": "2024-04-15T16:10:00Z",
    "city": "Algiers",
    "can_leave_review": true,
    "patient_review": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "rating": 5,
      "text": "Professional and caring service",
      "created_at": "2024-04-16T10:00:00Z"
    },
    "nurse_review": null
  }
}
```

**Error Responses:**
- `403 Forbidden` - You were not accepted for this request (`NR3002`)
- `404 Not Found` - Request not found (`NR3001`)

---

## ⭐ Reviews & Ratings

### Submit a Review for Patient

Leave a rating and review for the patient after completing service.

**Endpoint:**
```
POST /api/reviews/
```

**Request Body:**
```json
{
  "target_type": "user",
  "target_id": "123",
  "context_type": "nurseservicerequest",
  "context_id": "45",
  "rating": 5,
  "title": "Cooperative and respectful",
  "text": "Patient was very cooperative during the service and followed all instructions."
}
```

**Request Fields:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| target_type | string | Yes | "user" | Type of entity being reviewed (patient user) |
| target_id | string | Yes | Valid user ID | ID of the patient |
| context_type | string | Yes | "nurseservicerequest" | Service context type |
| context_id | string | Yes | Valid request ID | Request ID |
| rating | integer | Yes | 1-5 | Star rating |
| title | string | No | Max 255 chars | Review title |
| text | string | No | Unlimited | Detailed review |

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": "660f8400-e29b-41d4-a716-446655440001",
    "reviewer_name": "Fatima Ahmed",
    "rating": 5,
    "title": "Cooperative and respectful",
    "text": "Patient was very cooperative...",
    "status": "ACTIVE",
    "created_at": "2024-04-16T16:30:00Z"
  },
  "message": "Review submitted successfully"
}
```

---

### View Your Received Reviews

See all reviews patients have left for you.

**Endpoint:**
```
GET /api/reviews/received/?target_type=provider&target_id={my_provider_id}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| target_type | string | Yes | "provider" |
| target_id | string | Yes | Your provider ID |
| min_rating | integer | No | Minimum rating (1-5) |
| max_rating | integer | No | Maximum rating (1-5) |
| page | integer | No | Pagination page |
| page_size | integer | No | Results per page |

**Response (200 OK):**
```json
{
  "success": true,
  "count": 40,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "reviewer_name": "A. B.",
      "rating": 5,
      "title": "Excellent professional",
      "text": "Very professional and caring...",
      "status": "ACTIVE",
      "helpful_count": 8,
      "created_at": "2024-04-16T10:00:00Z"
    }
  ],
  "average_rating": 4.8,
  "review_count": 40,
  "rating_distribution": {
    "1": 0,
    "2": 1,
    "3": 1,
    "4": 6,
    "5": 32
  }
}
```

---

### Respond to a Review

Reply to a review a patient left for you.

**Endpoint:**
```
POST /api/reviews/{review_id}/respond/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| review_id | string | Yes | Review ID |

**Request Body:**
```json
{
  "response": "Thank you so much for the kind words! I appreciate your cooperation during the service."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "response": "Thank you so much for the kind words!",
    "response_at": "2024-04-16T17:00:00Z",
    "response_by": "Your Name"
  },
  "message": "Response posted successfully"
}
```

---

## 🔧 My Services

### List My Services

View all nursing services you offer.

**Endpoint:**
```
GET /nurse/my-services/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| is_available | boolean | - | Filter by availability |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

**Response (200 OK):**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 1,
      "service_id": 1,
      "title": "Home Care Nursing",
      "description": "Professional nursing care at your home",
      "base_price": "150.00",
      "custom_price": "175.00",
      "effective_price": "175.00",
      "duration_minutes": 60,
      "is_available": true,
      "is_on_demand": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

### Update Service Availability

Change service availability or custom pricing.

**Endpoint:**
```
PATCH /nurse/my-services/{id}/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Service ID |

**Request Body:**
```json
{
  "is_available": true,
  "custom_price": "200.00"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| is_available | boolean | No | Toggle availability |
| custom_price | decimal | No | Your custom price (or null to use base) |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "service_id": 1,
    "title": "Home Care Nursing",
    "base_price": "150.00",
    "custom_price": "200.00",
    "effective_price": "200.00",
    "is_available": true
  },
  "message": "Service updated successfully"
}
```

---

## 📊 Your Offers

### List My Offers

View all offers you've submitted.

**Endpoint:**
```
GET /nurse/my-offers/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by offer status (PENDING, ACCEPTED, REJECTED) |
| is_active | boolean | - | Show active offers only |
| is_history | boolean | - | Show historical offers only |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

---

## 🔴 Error Codes

| Code | HTTP | Meaning | Action |
|------|------|---------|--------|
| NR1003 | 400 | Not nursing service | Request is not for nursing |
| NR1004 | 400 | Not on-demand | Service doesn't support on-demand |
| NR2001 | 400 | Price too low | Counter-offer below base price |
| NR2002 | 400 | Price too low | Counter-offer below patient price |
| NR3001 | 404 | Request not found | Invalid request ID |
| NR3002 | 403 | Not request owner | Unauthorized for this request |
| NR3007 | 400 | Service not in profile | Add service to your profile first |
| NR4003 | 400 | Already responded | You already made an offer |
| NR6001 | 401 | Not authenticated | Provide valid JWT token |
| NR6003 | 403 | Not a nurse | User role must be nurse |
| NR6004 | 404 | Nurse profile missing | Create/complete nurse profile |
| NR6005 | 403 | Not verified | Nurse profile must be verified |

---

## 📊 Status Values

Requests you accepted can have:

- `ACCEPTED` - You accepted, waiting to start
- `IN_PROGRESS` - Service is happening
- `COMPLETED` - Service finished
- `CANCELLED` - Request was cancelled

Offers you submitted can have:

- `PENDING` - Awaiting patient response
- `ACCEPTED` - Patient accepted your offer
- `REJECTED` - Patient chose different nurse
- `COUNTER_OFFERED` - You made counter-offer (see in request)
- `EXPIRED` - Request was cancelled
