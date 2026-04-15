# Medilink Nurse App - Complete API Documentation

Complete API reference for nurse-facing endpoints including request management, profile, invoices, reviews, and services.

**Base URL:** `https://api.medilink.com/api`  
**Authentication:** Bearer Token (JWT)  
**Default Pagination:** 20 items per page

---

## 📋 Table of Contents

1. [Profile Management](#profile-management) ⭐ NEW
2. [Available Requests](#available-requests)
3. [Offer Management](#offer-management)
4. [Request History](#request-history)
5. [Invoices Management](#invoices-management) ⭐ NEW
6. [Reviews & Ratings](#reviews--ratings)
7. [My Services](#my-services)
8. [Error Codes](#error-codes)

---

## 👤 Profile Management

### Get My Nurse Profile

Retrieve your complete nurse profile with all professional information.

**Endpoint:**
```
GET /provider/profile/
```

**Response (200 OK):**
```json
{
  "id": 42,
  "email": "fatima.ahmed@medilink.com",
  "first_name": "Fatima",
  "last_name": "Ahmed",
  "full_name": "Fatima Ahmed",
  "gender": "F",
  "gender_display": "Female",
  "date_of_birth": "1995-05-15",
  "profile_image": "https://cdn.medilink.com/profiles/nurse-42.jpg",
  "phone_number": "+213-555-1234",
  "license_number": "NU-DZA-2020-12345",
  "certification": "Registered Nurse (RN)",
  "years_of_experience": 5,
  "biography": "Experienced nurse specializing in home care...",
  "degree_document": "https://cdn.medilink.com/docs/degree-42.pdf",
  "entrepreneur_card_front": "https://cdn.medilink.com/docs/card-front-42.jpg",
  "entrepreneur_card_back": "https://cdn.medilink.com/docs/card-back-42.jpg",
  "entrepreneur_card_pdf": "https://cdn.medilink.com/docs/card-42.pdf",
  "is_verified": true,
  "is_available": true,
  "is_home_service_available": true,
  "service_area_km": 50,
  "services": [
    {
      "id": 1,
      "title": "Home Care Nursing",
      "slug": "home-care-nursing",
      "description": "Professional nursing care at your home",
      "price": "150.00",
      "custom_price": "175.00",
      "final_price": "175.00",
      "duration_minutes": 60,
      "is_home_service": true,
      "is_available": true
    }
  ],
  "provider_status": {
    "status": "APPROVED",
    "provider_type": "NURSE",
    "is_active": true,
    "verification_documents": {
      "degree": { "status": "VERIFIED" },
      "entrepreneur_card": { "status": "VERIFIED" }
    }
  },
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2024-04-15T14:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing authentication token
- `403 Forbidden` - User is not a provider (`NR6003`)
- `404 Not Found` - Nurse profile not found (`NR6004`)

---

### Update My Nurse Profile

Update your nurse profile information. Can update most fields except verified status.

**Endpoint:**
```
PUT /provider/profile/
```

**Request Body (Full Update):**
```json
{
  "first_name": "Fatima",
  "last_name": "Ahmed",
  "gender": "F",
  "date_of_birth": "1995-05-15",
  "phone_number": "+213-555-1234",
  "license_number": "NU-DZA-2020-12345",
  "certification": "Registered Nurse (RN)",
  "years_of_experience": 6,
  "biography": "Experienced nurse with 6 years in home care and hospital settings",
  "is_available": true,
  "is_home_service_available": true,
  "service_area_km": 60
}
```

**Request Fields:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| first_name | string | No | Max 100 chars | First name |
| last_name | string | No | Max 100 chars | Last name |
| gender | string | No | F/M/OTHER | Gender |
| date_of_birth | date | No | ISO 8601 | Date of birth |
| phone_number | string | No | Max 20 chars | Phone number |
| license_number | string | No | Unique | Nursing license number |
| certification | string | No | Max 200 chars | Certification type |
| years_of_experience | integer | No | 0-100 | Years of experience |
| biography | string | No | Unlimited | Professional biography |
| is_available | boolean | No | - | Availability status |
| is_home_service_available | boolean | No | - | Home service availability |
| service_area_km | integer | No | >= 1 | Max service distance |

**Response (200 OK):**
```json
{
  "id": 42,
  "first_name": "Fatima",
  "last_name": "Ahmed",
  "years_of_experience": 6,
  "service_area_km": 60,
  "is_available": true,
  ...
}
```

**Error Responses:**
- `400 Bad Request` - Validation error (e.g., invalid license format)
- `403 Forbidden` - Not authorized to update
- `404 Not Found` - Profile not found

---

### Partial Update My Nurse Profile

Update specific fields of your profile (PATCH).

**Endpoint:**
```
PATCH /provider/profile/
```

**Request Body (Partial Update - Only Changed Fields):**
```json
{
  "biography": "Updated biography with more experience",
  "is_available": false,
  "service_area_km": 75
}
```

**Response (200 OK):**
```json
{
  "id": 42,
  "biography": "Updated biography with more experience",
  "is_available": false,
  "service_area_km": 75,
  ...
}
```

---

### Upload/Update Profile Image

Update your profile picture.

**Endpoint:**
```
PATCH /provider/profile/
```

**Request Body (Multipart Form Data):**
```
profile_image: <image file>
```

**Supported Formats:** JPG, PNG, WEBP (max 5MB)

---

### Upload/Update Certification Documents

Upload degree, entrepreneur card, and other certification documents.

**Endpoint:**
```
PATCH /provider/profile/
```

**Request Body (Multipart Form Data):**
```
degree_document: <PDF or image file>
entrepreneur_card_front: <image or PDF>
entrepreneur_card_back: <image or PDF>
entrepreneur_card_pdf: <PDF file>
```

**Supported Formats:** PDF, JPG, PNG, WEBP (max 10MB each)

**Note:** Uploading new documents may require re-verification by admin.

---

## 🔍 Available Requests

### Browse Available Requests

Get a list of nursing service requests in your area that you can respond to.

**Endpoint:**
```
GET /nurse-requests/nurse/available-requests/
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
GET /nurse-requests/nurse/available-requests/?city=Algiers&status=SEARCHING
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
GET /nurse-requests/nurse/available-requests/{id}/
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
POST /nurse-requests/nurse/available-requests/{id}/accept/
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
POST /nurse-requests/nurse/available-requests/{id}/counter-offer/
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
POST /nurse-requests/nurse/available-requests/{id}/reject/
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
GET /nurse-requests/nurse/request-history/
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
GET /nurse-requests/nurse/request-history/?status=COMPLETED&date_from=2024-01-01&ordering=-completed_at
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

**Filtering Examples:**
```
# Completed services only
GET /nurse-requests/nurse/request-history/?status=COMPLETED

# Last 30 days
GET /nurse-requests/nurse/request-history/?date_from=2024-03-16&date_to=2024-04-15

# Search by patient
GET /nurse-requests/nurse/request-history/?patient_name=Ahmed

# Sorted by highest price
GET /nurse-requests/nurse/request-history/?ordering=-final_price
```

---

### Get History Detail

View detailed information about a past service.

**Endpoint:**
```
GET /nurse-requests/nurse/request-history/{id}/
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

## 💰 Invoices Management

### List My Invoices

Get all invoices you've created for patients.

**Endpoint:**
```
GET /invoices/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by status (DRAFT, SENT, PAID, OVERDUE, etc.) |
| invoice_type | string | - | Filter by type (SERVICE, PRODUCT, MIXED, CUSTOM) |
| date_from | string | - | Filter from date (ISO 8601) |
| date_to | string | - | Filter until date (ISO 8601) |
| search | string | - | Search by invoice number or patient name |
| ordering | string | -created_at | Sort by field |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

**Example:**
```
GET /invoices/?status=PAID&date_from=2024-03-01&ordering=-created_at
```

**Response (200 OK):**
```json
{
  "success": true,
  "count": 8,
  "results": [
    {
      "id": 123,
      "invoice_number": "INV-20240415-A1B2C3D4",
      "patient_name": "Ahmed Ben Ali",
      "patient_email": "ahmed@example.com",
      "status": "PAID",
      "invoice_type": "SERVICE",
      "total": "175.00",
      "amount_paid": "175.00",
      "currency": "DZD",
      "issue_date": "2024-04-15",
      "due_date": "2024-05-15",
      "created_at": "2024-04-15T10:00:00Z",
      "updated_at": "2024-04-17T14:30:00Z"
    }
  ],
  "pagination": {
    "count": 8,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

---

### Get Invoice Details

Get full details of a specific invoice.

**Endpoint:**
```
GET /invoices/{id}/
```

**URL Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | integer | Yes | Invoice ID |

**Response (200 OK):**
```json
{
  "id": 123,
  "invoice_number": "INV-20240415-A1B2C3D4",
  "status": "PAID",
  "invoice_type": "SERVICE",
  "patient_name": "Ahmed Ben Ali",
  "patient_email": "ahmed@example.com",
  "patient_phone": "+213-555-9876",
  "issue_date": "2024-04-15",
  "due_date": "2024-05-15",
  "currency": "DZD",
  "subtotal": "150.00",
  "tax": "0.00",
  "discount": "0.00",
  "total": "175.00",
  "amount_paid": "175.00",
  "balance_due": "0.00",
  "notes": "Payment received. Thank you for your service.",
  "items": [
    {
      "id": 456,
      "item_type": "SERVICE",
      "description": "Home Care Nursing - 1 hour",
      "quantity": 1,
      "unit_price": "175.00",
      "line_total": "175.00"
    }
  ],
  "payments": [
    {
      "id": 789,
      "amount": "175.00",
      "payment_method": "CARD",
      "payment_date": "2024-04-17",
      "status": "VERIFIED"
    }
  ],
  "created_at": "2024-04-15T10:00:00Z",
  "updated_at": "2024-04-17T14:30:00Z"
}
```

---

### Create New Invoice

Create an invoice for a patient.

**Endpoint:**
```
POST /invoices/
```

**Request Body:**
```json
{
  "patient_user": 123,
  "invoice_type": "SERVICE",
  "issue_date": "2024-04-15",
  "due_date": "2024-05-15",
  "currency": "DZD",
  "notes": "Invoice for nursing service",
  "items": [
    {
      "item_type": "SERVICE",
      "description": "Home Care Nursing - 1 hour",
      "quantity": 1,
      "unit_price": "175.00"
    }
  ]
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| patient_user | integer | Yes | Patient user ID |
| invoice_type | string | Yes | Type: SERVICE, PRODUCT, MIXED, CUSTOM |
| issue_date | date | Yes | Issue date (ISO 8601) |
| due_date | date | Yes | Due date (ISO 8601) |
| currency | string | Yes | Currency: DZD, USD, EUR |
| notes | string | No | Invoice notes |
| items | array | Yes | Invoice line items |

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 124,
    "invoice_number": "INV-20240415-B2C3D4E5",
    "status": "DRAFT",
    "patient_user": 123,
    "invoice_type": "SERVICE",
    "total": "175.00",
    "created_at": "2024-04-15T11:00:00Z"
  },
  "message": "Invoice created successfully"
}
```

---

### Update Invoice (Draft Only)

Update an invoice that's still in DRAFT status.

**Endpoint:**
```
PUT /invoices/{id}/
```

**Request Body:**
```json
{
  "due_date": "2024-05-20",
  "notes": "Updated notes"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": { ... },
  "message": "Invoice updated successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invoice not in DRAFT status

---

### Send Invoice to Patient

Send the invoice to the patient.

**Endpoint:**
```
POST /invoices/{id}/send/
```

**Request Body:**
```json
{
  "send_email": true,
  "message": "Please find your invoice attached. Payment due by the date shown."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "SENT",
    "email_sent": true,
    "sent_at": "2024-04-15T11:15:00Z"
  },
  "message": "Invoice sent to patient"
}
```

---

### Cancel Invoice

Cancel an invoice.

**Endpoint:**
```
POST /invoices/{id}/cancel/
```

**Request Body:**
```json
{
  "reason": "Patient declined service"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "CANCELLED",
    "cancelled_at": "2024-04-15T11:20:00Z"
  },
  "message": "Invoice cancelled successfully"
}
```

---

### Record Payment

Record a payment for an invoice.

**Endpoint:**
```
POST /invoices/{id}/record_payment/
```

**Request Body:**
```json
{
  "amount": "175.00",
  "payment_method": "CARD",
  "payment_date": "2024-04-17",
  "reference_number": "TXN-12345678"
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | decimal | Yes | Payment amount |
| payment_method | string | Yes | Method: CASH, CARD, BANK_TRANSFER, etc. |
| payment_date | date | Yes | Payment date |
| reference_number | string | No | Transaction reference |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "payment_id": 789,
    "amount": "175.00",
    "status": "PENDING_VERIFICATION",
    "invoice_status": "PARTIALLY_PAID"
  },
  "message": "Payment recorded successfully"
}
```

---

### Delete Invoice (Draft Only)

Delete a draft invoice.

**Endpoint:**
```
DELETE /invoices/{id}/
```

**Response (204 No Content):**
```
(Empty response on success)
```

**Error Responses:**
- `400 Bad Request` - Invoice not in DRAFT status
- `404 Not Found` - Invoice not found

---

### Get Invoice Statistics

Get statistics about your invoices.

**Endpoint:**
```
GET /invoices/statistics/
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "total_invoices": 45,
    "draft_invoices": 2,
    "sent_invoices": 5,
    "paid_invoices": 35,
    "overdue_invoices": 3,
    "total_amount": "7875.00",
    "total_paid": "7450.00",
    "total_pending": "425.00",
    "currency": "DZD",
    "this_month": {
      "total_invoices": 8,
      "total_amount": "1400.00",
      "total_paid": "1200.00"
    },
    "average_payment_days": 5
  }
}
```

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

### View My Reviews (Written)

See all reviews you've written for patients.

**Endpoint:**
```
GET /api/reviews/my-reviews/
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
  "count": 12,
  "results": [
    {
      "id": "770g9500-f30c-52e5-b827-557766551111",
      "reviewed_name": "Ahmed Ben Ali",
      "rating": 5,
      "title": "Cooperative patient",
      "text": "Very cooperative...",
      "status": "ACTIVE",
      "created_at": "2024-04-16T16:30:00Z"
    }
  ]
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
    "response_by": "Fatima Ahmed"
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
GET /nurse-requests/nurse/my-services/
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
PATCH /nurse-requests/nurse/my-services/{id}/
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

## 🔄 My Offers

### List My Offers

View all offers you've submitted on requests.

**Endpoint:**
```
GET /nurse-requests/nurse/my-offers/
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by offer status (PENDING, ACCEPTED, REJECTED) |
| is_active | boolean | - | Show active offers only |
| is_history | boolean | - | Show historical offers only |
| page | integer | 1 | Pagination page |
| page_size | integer | 20 | Results per page |

**Response (200 OK):**
```json
{
  "success": true,
  "count": 15,
  "results": [
    {
      "id": 123,
      "request_id": 45,
      "service_name": "Home Care Nursing",
      "patient_name": "A. B.",
      "offered_price": "175.00",
      "status": "ACCEPTED",
      "estimated_arrival_time": "00:30:00",
      "distance_km": "2.50",
      "created_at": "2024-04-15T14:45:00Z"
    }
  ]
}
```

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

Invoices can have:

- `DRAFT` - Created but not sent
- `SENT` - Sent to patient
- `VIEWED` - Patient has viewed
- `PAID` - Fully paid
- `PARTIALLY_PAID` - Partial payment received
- `OVERDUE` - Past due date
- `CANCELLED` - Cancelled
- `REFUNDED` - Full refund issued

---

## 🔐 Profile Data Management

### Fields You Can Edit:
- First name, last name
- Gender, date of birth
- Phone number
- Professional certifications
- Years of experience
- Biography
- Profile image
- Degree documents
- Entrepreneur card documents
- Service area (max distance)
- Availability status
- Home service availability

### Fields You Cannot Edit (Admin-Only):
- License number (can request change)
- Verified status (requires admin verification)
- Account email (change through account settings)

### To Delete Profile Data:
- Remove profile image: PATCH with empty image field
- Clear biography: PATCH with empty text
- Update certifications: Contact admin
- To delete entire profile: Contact support

---

## 💡 Notes

- **Real-time Notifications:** All state changes trigger instant WebSocket updates
- **Pagination:** Default 20 items per page, adjustable with `page_size`
- **Filtering:** Combine multiple filters (e.g., `?status=COMPLETED&date_from=2024-01-01`)
- **Sorting:** Use `-` prefix for descending order (e.g., `?ordering=-created_at`)
- **Date Format:** All dates use ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
- **Verification:** Your profile must be verified to accept requests
- **Invoice History:** Keep invoices for tax and audit purposes

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
