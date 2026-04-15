# Medilink Nurse App - API Summary & Implementation Notes

Complete reference guide for all nurse app endpoints with implementation status and important notes.

---

## 📋 Overview

The Medilink Nurse App provides comprehensive management of:
- ✅ Service Requests (browse, offer, accept, decline)
- ✅ Service History (track completed/cancelled services)
- ✅ Profile Management (view, update all personal/professional info)
- ✅ Invoice Management (create, send, track payments)
- ✅ Reviews & Ratings (submit and view reviews)
- ✅ Services Management (list and update services offered)
- ✅ Offers Management (list submitted offers)

---

## 👤 Profile Management Endpoints

All profile endpoints use base URL: `https://api.medilink.com/api`

### Profile Retrieval & Management

| Method | Endpoint | Purpose | Authentication | Status |
|--------|----------|---------|-----------------|--------|
| GET | `/provider/profile/` | Get complete nurse profile | Required | ✅ Active |
| PUT | `/provider/profile/` | Full update of profile | Required | ✅ Active |
| PATCH | `/provider/profile/` | Partial update of profile | Required | ✅ Active |

### Editable Profile Fields

**Personal Information:**
- first_name (string, max 100 chars)
- last_name (string, max 100 chars)
- gender (F/M/OTHER)
- date_of_birth (ISO 8601 date)
- phone_number (string, max 20 chars)
- profile_image (JPG, PNG, WEBP, max 5MB)

**Professional Information:**
- license_number (string, unique - admin may verify)
- certification (string, max 200 chars)
- years_of_experience (integer, 0-100)
- biography (unlimited text)
- service_area_km (integer, default 50km)

**Availability & Status:**
- is_available (boolean)
- is_home_service_available (boolean)

**Documents (Requires Re-verification on Update):**
- degree_document (PDF/image, max 10MB)
- entrepreneur_card_front (PDF/image, max 10MB)
- entrepreneur_card_back (PDF/image, max 10MB)
- entrepreneur_card_pdf (PDF, max 10MB)

### Read-Only Profile Fields

These fields are managed by admin or system:
- id
- email (change via account settings)
- is_verified (admin-only, requires document verification)
- provider_status (managed by admin)
- created_at / updated_at (timestamps)

---

## 💰 Invoice Management Endpoints

All invoice endpoints use base URL: `https://api.medilink.com/api`

### Invoice CRUD Operations

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/invoices/` | List all your invoices | ✅ Active |
| GET | `/invoices/{id}/` | Get invoice details | ✅ Active |
| POST | `/invoices/` | Create new invoice | ✅ Active |
| PUT | `/invoices/{id}/` | Update invoice (draft only) | ✅ Active |
| PATCH | `/invoices/{id}/` | Partial update (draft only) | ✅ Active |
| DELETE | `/invoices/{id}/` | Delete invoice (draft only) | ✅ Active |

### Invoice Actions

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/invoices/{id}/send/` | Send invoice to patient | ✅ Active |
| POST | `/invoices/{id}/cancel/` | Cancel invoice | ✅ Active |
| POST | `/invoices/{id}/record_payment/` | Record payment received | ✅ Active |
| POST | `/invoices/{id}/mark_viewed/` | Mark invoice as viewed | ✅ Active |
| GET | `/invoices/{id}/activities/` | Get invoice activity log | ✅ Active |
| GET | `/invoices/statistics/` | Get invoice statistics | ✅ Active |

### Invoice Status Workflow

```
DRAFT → SENT → VIEWED → PAID
                    ↓
                PARTIALLY_PAID
                    ↓
                OVERDUE
                
Can be CANCELLED at any stage
Can be REFUNDED or PARTIALLY_REFUNDED from PAID
```

### Invoice Types

- **SERVICE** - Healthcare services provided
- **PRODUCT** - Medications or medical supplies
- **MIXED** - Combination of services and products
- **CUSTOM** - Manual/custom items

### Payment Methods

- CASH
- CARD (Credit/Debit Card)
- BANK_TRANSFER
- MOBILE_PAYMENT (CCP, BaridiMob, etc.)
- INSURANCE
- CHEQUE
- OTHER

### Supported Currencies

- DZD (Algerian Dinar - Default)
- USD (US Dollar)
- EUR (Euro)

### Invoice Query Filters

```
GET /invoices/?status=PAID&date_from=2024-03-01&ordering=-created_at

Supported Filters:
- status: DRAFT, SENT, VIEWED, PAID, PARTIALLY_PAID, OVERDUE, CANCELLED, REFUNDED
- invoice_type: SERVICE, PRODUCT, MIXED, CUSTOM
- date_from: ISO 8601 date (YYYY-MM-DD)
- date_to: ISO 8601 date (YYYY-MM-DD)
- search: invoice number or patient name (partial match)
- ordering: any field with optional - prefix for descending
```

---

## ⭐ Reviews Management Endpoints

All reviews endpoints use base URL: `https://api.medilink.com/api`

### Review Operations

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/reviews/received/` | List reviews patients left for you | ✅ Active |
| GET | `/reviews/my-reviews/` | List reviews you've written | ✅ Active |
| POST | `/reviews/` | Submit review for patient | ✅ Active |
| POST | `/reviews/{id}/respond/` | Respond to a review you received | ✅ Active |
| GET | `/reviews/{id}/` | Get review details | ✅ Active |
| PUT | `/reviews/{id}/` | Edit your review | ✅ Active |
| DELETE | `/reviews/{id}/` | Delete your review (soft delete) | ✅ Active |
| POST | `/reviews/{id}/helpful/` | Mark review as helpful | ✅ Active |
| DELETE | `/reviews/{id}/helpful/` | Remove helpful mark | ✅ Active |
| POST | `/reviews/{id}/flag/` | Flag review for moderation | ✅ Active |

### Review Context & One-Per-User Rule

**Context-Based Reviews:** Reviews are linked to specific services to prevent duplicates.

```
Context Types:
- nurseservicerequest: Linked to specific nurse request
- appointment: Linked to specific appointment
- prescription: Linked to specific prescription

One-Per-User Rule:
- Only one review per reviewer per reviewed entity per context
- Example: Can review Patient A after Service 1, and again after Service 2
- But cannot review Patient A twice for the same Service 1
```

### Review Rating Distribution

```json
{
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

### Review Status Values

- **ACTIVE** - Published, visible to all
- **HIDDEN** - Hidden by admin (moderation)
- **DELETED** - Soft-deleted by reviewer
- **FLAGGED** - Flagged for moderation review

---

## 🔍 Service Request Endpoints

All nurse request endpoints use base URL: `https://api.medilink.com/api/nurse-requests`

### Available Requests Browsing

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/nurse/available-requests/` | List requests in your area | ✅ Active |
| GET | `/nurse/available-requests/{id}/` | Get request details | ✅ Active |

### Offer Submission

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/nurse/available-requests/{id}/accept/` | Accept at patient price | ✅ Active |
| POST | `/nurse/available-requests/{id}/counter-offer/` | Counter-offer higher price | ✅ Active |
| POST | `/nurse/available-requests/{id}/reject/` | Decline request | ✅ Active |

### Request History

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/nurse/request-history/` | List completed/accepted requests | ✅ Active |
| GET | `/nurse/request-history/{id}/` | Get service history detail | ✅ Active |

### Service Management

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/nurse/my-services/` | List your offered services | ✅ Active |
| PATCH | `/nurse/my-services/{id}/` | Update service availability/price | ✅ Active |

### Offers Management

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/nurse/my-offers/` | List all your submitted offers | ✅ Active |

### Request Status Workflow

```
SEARCHING → NURSE_RESPONDED → PATIENT_DECISION → ACCEPTED → IN_PROGRESS → COMPLETED
                                      ↑
                                 [NEW] DECLINE
                                (single offers)
                                      
Can be CANCELLED at any point
```

---

## 🔐 Authentication & Authorization

### Required Authentication
- All endpoints require valid JWT Bearer token
- Token obtained from `/api/auth/login/` endpoint
- Include in header: `Authorization: Bearer <token>`

### Role Requirements
- **Nurse App:** User must have role = PROVIDER with provider_type = NURSE
- **Profile Endpoints:** Only your own profile accessible
- **Invoice Endpoints:** Can only access invoices you created or are related to
- **Review Endpoints:** Can submit/view reviews as allowed by context

### Verification Requirements
- Profile must be `is_verified = true` to:
  - Accept service requests
  - Submit offers
  - Create invoices
  - Be visible to patients

---

## 📊 Query Parameters & Filtering

### Common Filter Parameters

```
# Status Filtering
?status=COMPLETED
?status=PAID,PARTIALLY_PAID

# Date Range Filtering
?date_from=2024-01-01&date_to=2024-12-31

# Pagination
?page=1&page_size=50

# Sorting/Ordering
?ordering=created_at          # ascending
?ordering=-created_at         # descending
?ordering=-final_price,created_at  # multiple fields

# Search
?search=patient_name
?search=invoice_number

# Boolean Filters
?is_available=true
?is_active=true
?is_history=true
```

---

## 🔔 Real-Time Updates (WebSocket)

All state changes trigger real-time notifications via:

1. **WebSocket:** Instant in-app updates
   - Message types: request_accepted, offer_declined, review_received, etc.
   
2. **FCM Push:** Mobile background notifications
   - High priority for urgent events (offer received, accepted)
   - Normal priority for completion/review events
   
3. **In-App Database:** Persistent notification history
   - Stored in notifications table
   - Retrievable via `/api/notifications/`

---

## 📝 Response Format

### Successful Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "code": "SUCCESS"
}
```

### Paginated Response
```json
{
  "success": true,
  "count": 42,
  "next": "https://api.medilink.com/api/invoices/?page=2",
  "previous": null,
  "results": [ ... ],
  "pagination": {
    "count": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "NR6005",
    "message": "Your nurse profile is not verified",
    "details": { }
  }
}
```

---

## 🎯 Common Workflows

### Complete Service & Get Paid

1. **Browse Available Requests**
   ```
   GET /nurse-requests/nurse/available-requests/
   ```

2. **Submit Offer**
   ```
   POST /nurse-requests/nurse/available-requests/{id}/accept/
   ```

3. **Wait for Patient Acceptance**
   - Real-time WebSocket notification

4. **Complete Service**
   - Request moves to COMPLETED status

5. **Create Invoice**
   ```
   POST /invoices/ (with final_price from request)
   ```

6. **Send Invoice**
   ```
   POST /invoices/{id}/send/
   ```

7. **Record Payment**
   ```
   POST /invoices/{id}/record_payment/
   ```

8. **Get Paid Notification**
   - WebSocket notification when payment verified

---

### Receive & Respond to Review

1. **Patient Submits Review**
   - Real-time WebSocket notification
   - Notification in database

2. **You See Review**
   ```
   GET /api/reviews/received/
   ```

3. **Respond to Review**
   ```
   POST /api/reviews/{id}/respond/
   ```

4. **Response Visible to Public**
   - Shown under your reviews on your profile

---

### Update Profile & Services

1. **View Current Profile**
   ```
   GET /provider/profile/
   ```

2. **Update Profile**
   ```
   PUT /provider/profile/
   ```

3. **Upload New Documents** (if needed)
   ```
   PATCH /provider/profile/ (with multipart files)
   ```

4. **Update Service Availability**
   ```
   PATCH /nurse-requests/nurse/my-services/{id}/
   ```

5. **Track Service Offering**
   ```
   GET /nurse-requests/nurse/my-services/
   ```

---

## 📋 Data Validation Rules

### Profile Data
- **License Number:** Must be unique, format: NU-XXX-XXXX-XXXXX
- **Years of Experience:** 0-100
- **Service Area:** Minimum 1 km, reasonable maximum 500 km
- **Phone:** Must be valid format for Algeria or international
- **Profile Image:** JPEG, PNG, WebP only, max 5MB
- **Documents:** PDF or images, max 10MB each

### Invoice Data
- **Invoice Number:** Auto-generated, unique format INV-YYYYMMDD-XXXXXXXX
- **Amounts:** Must be decimal with 2 places max (e.g., 175.00)
- **Currency:** Must be DZD, USD, or EUR
- **Dates:** Issue date must be ≤ Due date
- **Items:** At least one item required
- **Status:** Follows strict workflow (see status values)

### Review Data
- **Rating:** Must be 1-5 integer
- **Title:** Max 255 characters
- **Text:** Unlimited but should be concise
- **One Per User Per Context:** Enforced by database constraints

---

## 🚀 Performance Optimization

### Recommended Query Practices

1. **Use Pagination**
   ```
   # Good
   GET /invoices/?page=1&page_size=50
   
   # Avoid (slow for large datasets)
   GET /invoices/?page_size=10000
   ```

2. **Filter Early**
   ```
   # Good - filters in database
   GET /invoices/?status=PAID&date_from=2024-01-01
   
   # Avoid - fetches all then filters
   GET /invoices/
   ```

3. **Use Appropriate Ordering**
   ```
   # Good - indexed field
   GET /invoices/?ordering=-created_at
   
   # Avoid if possible - non-indexed field
   GET /invoices/?ordering=provider_notes
   ```

---

## ✅ Implementation Checklist for Nurse App

- [x] Profile management (get, update, upload documents)
- [x] Invoice creation and management (CRUD)
- [x] Invoice payment tracking
- [x] Invoice statistics
- [x] Service request browsing
- [x] Offer submission (accept and counter-offer)
- [x] Request history with filtering
- [x] Review submission
- [x] Review viewing (received and written)
- [x] Review responses
- [x] Service management
- [x] Real-time notifications
- [x] Payment tracking
- [x] Document verification
- [x] Status tracking for all entities

---

## 🔗 Related Documentation

- **Patient App API:** See PATIENT_API.md
- **Notifications:** See NOTIFICATIONS.md
- **Authentication:** See AUTH.md
- **Error Codes Reference:** See ERROR_CODES.md

---

## 📞 Support & Troubleshooting

### Common Issues

**Profile Not Verified?**
- Admin must verify documents
- Upload clear, legible documents
- Check email for verification status updates

**Cannot Create Invoice?**
- Ensure you're the provider
- Profile must be verified
- Patient must exist in system
- Check invoice amounts are valid

**Reviews Not Showing?**
- Review must be ACTIVE status
- Context must be from completed service
- One review per user per context rule
- May be hidden by moderation

**Payment Not Recording?**
- Invoice must be SENT status
- Amount must match or be partial
- Payment method must be valid
- Reference number can help track

---

**Last Updated:** April 15, 2024
**API Version:** v1.0
**Document Version:** 2.0 (Complete with Profile + Invoices)
