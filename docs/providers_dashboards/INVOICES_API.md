# Provider Dashboards - Invoices API

## Overview

This documentation covers the **Invoices API** for Provider Web Dashboards. Providers (doctors, nurses, clinics) can create, manage, and track invoices for healthcare services, consultations, and custom billing items.

**Key Features for Doctors:**
- Invoice Consultations - Create invoices from completed appointments
- Invoice Services - Bill for medical services you provide
- Financial Dashboard - Track revenue, outstanding payments, and trends
- Uninvoiced Appointments - Easily find appointments that need billing
- Payment Tracking - Record and verify payments with multiple methods

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Quick Start for Doctors](#quick-start-for-doctors)
4. [Invoice Types](#invoice-types)
5. [Invoice Status Flow](#invoice-status-flow)
6. [Financial Dashboard](#financial-dashboard)
   - [Financial Summary](#financial-summary)
   - [Get Statistics](#get-statistics)
   - [Uninvoiced Appointments](#uninvoiced-appointments)
   - [Overdue Invoices](#overdue-invoices)
7. [Invoice Management](#invoice-management)
   - [List My Invoices (Provider)](#list-my-invoices-provider)
   - [List My Invoices (Patient)](#list-my-invoices-patient)
   - [Create Invoice](#create-invoice)
   - [Get Invoice Details](#get-invoice-details)
   - [Update Invoice (Draft only)](#update-invoice-draft-only)
   - [Delete Invoice (Draft only)](#delete-invoice-draft-only)
8. [Invoice Actions](#invoice-actions)
   - [Send Invoice](#send-invoice)
   - [Cancel Invoice](#cancel-invoice)
   - [Mark Viewed](#mark-viewed)
   - [Add Item](#add-item)
   - [Remove Item](#remove-item)
   - [Record Payment](#record-payment)
   - [Get Activity Log](#get-activity-log)
9. [Create from Appointment](#create-from-appointment)
10. [Payment Management](#payment-management)
11. [Item Types](#item-types)
12. [Example Workflows](#example-workflows)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

---

## Authentication

All invoice endpoints require authentication. Include your token in every request:

```
Authorization: Token <your_token_here>
```

---

## Quick Start for Doctors

### Typical Invoice Workflow

1. **Complete an appointment** with your patient
2. **Check uninvoiced appointments** to see what needs billing
3. **Create invoice from appointment** (auto-populates with services)
4. **Add additional items** if needed (tests, medications, etc.)
5. **Send to patient**
6. **Record payment** when received

### Quick API Calls

```bash
# 1. Get appointments that need invoicing
GET /api/invoices/uninvoiced_appointments/

# 2. Create invoice from appointment
POST /api/invoices/from_appointment/
{
    "appointment_id": "uuid",
    "include_services": true,
    "tax_rate": "0.00",
    "due_days": 30
}

# 3. Send invoice to patient
POST /api/invoices/{id}/send/

# 4. Record payment
POST /api/invoices/{id}/record_payment/
{
    "amount": "3000.00",
    "payment_method": "CASH"
}
```

---

## Invoice Types

| Type | Description | Use Case |
|------|-------------|----------|
| `SERVICE` | Healthcare services | Appointments, consultations, procedures |
| `PRODUCT` | Products sold | Medications, medical supplies |
| `MIXED` | Combination | Services + Products in one invoice |
| `CUSTOM` | Manual/custom items | Any other billable items |

---

## Invoice Status Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      INVOICE STATUS FLOW                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  DRAFT   │───▶│   SENT   │───▶│  VIEWED  │───▶│   PAID   │      │
│  │ (edit)   │    │          │    │          │    │          │      │
│  └──────────┘    └────┬─────┘    └────┬─────┘    └──────────┘      │
│       │               │               │               │             │
│       ▼               ▼               ▼               ▼             │
│  ┌──────────┐    ┌──────────┐    ┌───────────────┐  ┌───────────┐  │
│  │CANCELLED │    │ OVERDUE  │    │PARTIALLY_PAID │  │ REFUNDED  │  │
│  └──────────┘    └──────────┘    └───────────────┘  └───────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

| Status | Description |
|--------|-------------|
| `DRAFT` | Invoice created but not sent (can edit/delete) |
| `SENT` | Invoice sent to patient |
| `VIEWED` | Patient has viewed the invoice |
| `PARTIALLY_PAID` | Partial payment received |
| `PAID` | Fully paid |
| `OVERDUE` | Past due date |
| `CANCELLED` | Invoice cancelled |
| `REFUNDED` | Full refund issued |
| `PARTIALLY_REFUNDED` | Partial refund issued |

---

## Financial Dashboard

These endpoints help you track your financial performance and identify what needs attention.

### Financial Summary

Get a comprehensive financial overview.

```
GET /api/invoices/financial_summary/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | `week`, `month`, `quarter`, `year` (default: `month`) |
| `start_date` | string | Custom start date (YYYY-MM-DD) |
| `end_date` | string | Custom end date (YYYY-MM-DD) |

**Response (200 OK):**
```json
{
    "period": "month",
    "start_date": "2026-02-01",
    "end_date": "2026-03-03",
    "total_revenue": "150000.00",
    "total_outstanding": "35000.00",
    "uninvoiced_appointments": 5,
    "revenue_by_type": [
        {"invoice_type": "SERVICE", "total": "140000.00", "count": 45},
        {"invoice_type": "CUSTOM", "total": "10000.00", "count": 3}
    ],
    "payment_methods": [
        {"payment_method": "CASH", "total": "100000.00", "count": 30},
        {"payment_method": "CARD", "total": "40000.00", "count": 12},
        {"payment_method": "MOBILE_PAYMENT", "total": "10000.00", "count": 5}
    ],
    "monthly_revenue": [
        {"month": "2026-02-01T00:00:00Z", "total": "75000.00", "count": 25},
        {"month": "2026-03-01T00:00:00Z", "total": "75000.00", "count": 23}
    ],
    "invoices_count": 50,
    "paid_count": 42,
    "pending_count": 5,
    "overdue_count": 3
}
```

---

### Get Statistics

Get invoice statistics summary.

```
GET /api/invoices/statistics/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | Filter from date (YYYY-MM-DD) |
| `end_date` | string | Filter to date (YYYY-MM-DD) |

**Response (200 OK):**
```json
{
    "total_invoices": 150,
    "total_amount": "750000.00",
    "total_paid": "500000.00",
    "total_outstanding": "250000.00",
    "draft_count": 5,
    "sent_count": 20,
    "paid_count": 100,
    "overdue_count": 10,
    "cancelled_count": 15,
    "service_invoices": 120,
    "product_invoices": 15,
    "mixed_invoices": 10,
    "custom_invoices": 5
}
```

> **Note:** `sent_count` includes both `SENT` and `VIEWED` statuses.

---

### Uninvoiced Appointments

Get completed appointments that haven't been invoiced yet.

```
GET /api/invoices/uninvoiced_appointments/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | Filter from date (YYYY-MM-DD) |
| `end_date` | string | Filter to date (YYYY-MM-DD) |

**Response (200 OK):** Returns up to 50 appointments, using `AppointmentListSerializer`.

```json
[
    {
        "id": "appointment-uuid",
        "patient_display_name": "Mohammed Khalil",
        "scheduled_date": "2026-01-28",
        "scheduled_time": "10:00:00",
        "status": "COMPLETED",
        "service": {
            "id": "service-uuid",
            "title": "General Consultation",
            "price": "3000.00"
        },
        "location_type": "CLINIC",
        "completed_at": "2026-01-28T10:45:00Z"
    }
]
```

> **Tip:** Use this endpoint to show doctors which appointments need to be billed!

---

### Overdue Invoices

Get list of overdue invoices. Also automatically marks newly overdue invoices (past `due_date` with status `SENT`/`VIEWED`/`PARTIALLY_PAID`).

```
GET /api/invoices/overdue/
```

**Response (200 OK):** Uses `InvoiceListSerializer` (same shape as [List Invoices](#list-my-invoices-provider)).

```json
[
    {
        "id": "invoice-uuid",
        "invoice_number": "INV-20260115-A1B2C3D4",
        "provider_name": "Dr. Ahmed Benali",
        "patient_display_name": "Ahmed Khelifi",
        "invoice_type": "SERVICE",
        "status": "OVERDUE",
        "status_display": "Overdue",
        "issue_date": "2026-01-15",
        "due_date": "2026-01-20",
        "currency": "DZD",
        "total": "5000.00",
        "amount_paid": "0.00",
        "amount_due": "5000.00",
        "items_count": 2,
        "created_at": "2026-01-15T10:30:00Z"
    }
]
```

---

## Invoice Management

### List My Invoices (Provider)

Returns invoices **owned by the authenticated provider**. Admins see all invoices. Patients see invoices addressed to them.

```
GET /api/invoices/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: `DRAFT`, `SENT`, `VIEWED`, `PARTIALLY_PAID`, `PAID`, `OVERDUE`, `CANCELLED`, `REFUNDED`, `PARTIALLY_REFUNDED` |
| `invoice_type` | string | Filter: `SERVICE`, `PRODUCT`, `MIXED`, `CUSTOM` |
| `start_date` | string | Filter by issue date from (YYYY-MM-DD) |
| `end_date` | string | Filter by issue date to (YYYY-MM-DD) |
| `search` | string | Search by invoice number, patient first/last name |
| `ordering` | string | Sort: `created_at`, `-created_at`, `issue_date`, `-issue_date`, `due_date`, `total`, `status`, `invoice_type` |
| `page` | integer | Page number (default: 1, page size: 20) |

**Response (200 OK):**
```json
{
    "count": 25,
    "next": "https://dzmedilink.duckdns.org/api/invoices/?page=2",
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "invoice_number": "INV-20260115-A1B2C3D4",
            "provider_name": "Dr. Ahmed Benali",
            "patient_display_name": "Mohammed Khalil",
            "invoice_type": "SERVICE",
            "status": "SENT",
            "status_display": "Sent",
            "issue_date": "2026-01-15",
            "due_date": "2026-02-14",
            "currency": "DZD",
            "total": "5000.00",
            "amount_paid": "0.00",
            "amount_due": "5000.00",
            "items_count": 2,
            "created_at": "2026-01-15T10:30:00Z"
        }
    ]
}
```

**Important — auto-filtering by role:**
- **Provider** → only invoices where `provider = your_profile`
- **Patient** → only invoices where `patient_user = you` OR `patient_record.linked_user = you`
- **Admin** → all invoices

---

### List My Invoices (Patient)

Simplified endpoint for patient-facing apps. Returns invoices addressed to the authenticated patient, **excluding DRAFT** invoices.

```
GET /api/invoices/my/
```

**Response (200 OK):** Same paginated shape as the provider list above (`InvoiceListSerializer`).

> **Why does this return 0?** This endpoint only shows invoices that have been **sent** (status ≠ `DRAFT`). If a provider created an invoice but hasn't sent it yet, patients won't see it. Providers should use `GET /api/invoices/` instead.

---

### Create Invoice

```
POST /api/invoices/
```

**Request Body:**
```json
{
    "patient_user": "patient-uuid",
    "invoice_type": "SERVICE",
    "issue_date": "2026-01-15",
    "due_date": "2026-02-14",
    "currency": "DZD",
    "tax_rate": "19.00",
    "discount_type": "PERCENTAGE",
    "discount_value": "10.00",
    "discount_reason": "Loyalty discount",
    "notes": "Thank you for your visit",
    "items": [
        {
            "item_type": "SERVICE",
            "service_id": "service-uuid",
            "quantity": "1.00"
        },
        {
            "item_type": "CUSTOM",
            "description": "Additional consultation",
            "unit_price": "2000.00",
            "quantity": "1.00"
        }
    ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | UUID | No | **Auto-set** from authenticated provider. Only needed for admins creating on behalf of a provider. |
| `patient_user` | UUID | Yes* | Patient with account |
| `patient_record` | integer | Yes* | Patient record ID (for patients without accounts) |
| `invoice_type` | string | No | `SERVICE`, `PRODUCT`, `MIXED`, `CUSTOM` (default: `SERVICE`) |
| `appointment` | UUID | No | Link to appointment |
| `prescription` | UUID | No | Link to prescription |
| `nurse_request` | UUID | No | Link to nurse request |
| `issue_date` | date | No | Invoice date (default: today) |
| `due_date` | date | No | Payment due date |
| `currency` | string | No | `DZD`, `USD`, `EUR` (default: `DZD`) |
| `tax_rate` | decimal | No | Tax percentage (default: `0.00`) |
| `discount_type` | string | No | `PERCENTAGE` or `FIXED` (default: `FIXED`) |
| `discount_value` | decimal | No | Discount amount (default: `0.00`) |
| `discount_reason` | string | No | Reason for discount |
| `notes` | string | No | Notes for the patient |
| `notes_en` | string | No | English notes |
| `notes_ar` | string | No | Arabic notes |
| `notes_fr` | string | No | French notes |
| `terms` | string | No | Payment terms |
| `internal_notes` | string | No | Internal notes (not visible to patient) |
| `items` | array | No | Line items (can add later via `/add_item/`) |

> *Either `patient_user` OR `patient_record` must be provided (not both).

**Response (201 Created):** Returns the full invoice detail (`InvoiceSerializer`):
```json
{
    "id": "invoice-uuid",
    "invoice_number": "INV-20260303-A1B2C3D4",
    "provider": "provider-uuid",
    "provider_name": "Dr. Ahmed Benali",
    "provider_type": "DOCTOR",
    "patient_user": "patient-uuid",
    "patient_record": null,
    "patient_display_name": "Mohammed Khalil",
    "invoice_type": "SERVICE",
    "invoice_type_display": "Service Invoice",
    "status": "DRAFT",
    "status_display": "Draft",
    "appointment": null,
    "prescription": null,
    "nurse_request": null,
    "issue_date": "2026-03-03",
    "due_date": "2026-04-02",
    "sent_at": null,
    "viewed_at": null,
    "paid_at": null,
    "currency": "DZD",
    "subtotal": "5000.00",
    "tax_rate": "19.00",
    "tax_amount": "855.00",
    "discount_type": "PERCENTAGE",
    "discount_value": "10.00",
    "discount_amount": "500.00",
    "discount_reason": "Loyalty discount",
    "total": "5355.00",
    "amount_paid": "0.00",
    "amount_due": "5355.00",
    "notes": "Thank you for your visit",
    "notes_en": "",
    "notes_ar": "",
    "notes_fr": "",
    "localized_notes": "Thank you for your visit",
    "terms": "",
    "internal_notes": "",
    "cancelled_at": null,
    "cancelled_by": null,
    "cancellation_reason": "",
    "created_by": "user-uuid",
    "created_at": "2026-03-03T10:30:00Z",
    "updated_at": "2026-03-03T10:30:00Z",
    "items": [
        {
            "id": "item-uuid",
            "invoice": "invoice-uuid",
            "item_type": "SERVICE",
            "order": 0,
            "service": "service-uuid",
            "custom_service": null,
            "prescription_item": null,
            "description": "General Consultation",
            "description_en": "General Consultation",
            "description_ar": "",
            "description_fr": "",
            "localized_description": "General Consultation",
            "quantity": "1.00",
            "unit": "session",
            "unit_price": "3000.00",
            "discount_percentage": "0.00",
            "total": "3000.00",
            "notes": "",
            "service_details": {
                "id": "service-uuid",
                "title": "General Consultation",
                "price": "3000.00",
                "currency": "DZD"
            },
            "custom_service_details": null,
            "created_at": "2026-03-03T10:30:00Z",
            "updated_at": "2026-03-03T10:30:00Z"
        },
        {
            "id": "item-uuid-2",
            "invoice": "invoice-uuid",
            "item_type": "CUSTOM",
            "order": 1,
            "service": null,
            "custom_service": null,
            "prescription_item": null,
            "description": "Additional consultation",
            "description_en": "Additional consultation",
            "description_ar": "",
            "description_fr": "",
            "localized_description": "Additional consultation",
            "quantity": "1.00",
            "unit": "unit",
            "unit_price": "2000.00",
            "discount_percentage": "0.00",
            "total": "2000.00",
            "notes": "",
            "service_details": null,
            "custom_service_details": null,
            "created_at": "2026-03-03T10:30:00Z",
            "updated_at": "2026-03-03T10:30:00Z"
        }
    ],
    "payments": []
}
```

---

### Get Invoice Details

```
GET /api/invoices/{id}/
```

**Response (200 OK):** Same shape as the create response above (`InvoiceSerializer`).

---

### Update Invoice (Draft only)

```
PATCH /api/invoices/{id}/
```

Uses `InvoiceSerializer`. You can update any writable field. Read-only fields are ignored.

**Writable fields:** `provider`, `patient_user`, `patient_record`, `invoice_type`, `appointment`, `prescription`, `nurse_request`, `issue_date`, `due_date`, `currency`, `tax_rate`, `discount_type`, `discount_value`, `discount_reason`, `notes`, `notes_en`, `notes_ar`, `notes_fr`, `terms`, `internal_notes`

> **Note:** Only DRAFT invoices should be updated. The backend enforces status checks on delete but not on update - best practice is to only update drafts.

---

### Delete Invoice (Draft only)

```
DELETE /api/invoices/{id}/
```

Returns `204 No Content` on success.

> Only `DRAFT` invoices can be deleted. For sent invoices, use Cancel instead.

---

## Invoice Actions

### Send Invoice

```
POST /api/invoices/{id}/send/
```

Sends the invoice to the patient and changes status from `DRAFT` to `SENT`.

**Request Body:**
```json
{
    "send_notification": true,
    "message": "Please review your invoice"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `send_notification` | boolean | No | Default: `true` |
| `message` | string | No | Optional message to patient |

**Validation:**
- Invoice must be in `DRAFT` status
- Invoice must have at least one item

**Response (200 OK):** Full `InvoiceSerializer` with updated status.

---

### Cancel Invoice

```
POST /api/invoices/{id}/cancel/
```

**Request Body:**
```json
{
    "reason": "Duplicate invoice"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | Yes | Cancellation reason |

**Validation:**
- Cannot cancel `PAID` or already `CANCELLED` invoices

**Response (200 OK):** Full `InvoiceSerializer` with `status: "CANCELLED"`.

---

### Mark Viewed

```
POST /api/invoices/{id}/mark_viewed/
```

Only the **patient** who received the invoice (or admin) can call this. Changes status from `SENT` to `VIEWED`.

**Request Body:** Empty `{}`

**Response (200 OK):** Full `InvoiceSerializer`.

---

### Add Item

```
POST /api/invoices/{id}/add_item/
```

Add an item to a **draft** invoice. Totals are automatically recalculated.

**Request Body (Service from catalog):**
```json
{
    "item_type": "SERVICE",
    "service_id": "service-uuid",
    "quantity": "1.00",
    "notes": "Regular consultation"
}
```

**Request Body (Custom Service):**
```json
{
    "item_type": "CUSTOM_SERVICE",
    "custom_service_id": "custom-service-uuid",
    "quantity": "1.00"
}
```

**Request Body (Custom Item):**
```json
{
    "item_type": "CUSTOM",
    "description": "Home visit fee",
    "unit_price": "1500.00",
    "quantity": "1.00"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_type` | string | No | `SERVICE`, `CUSTOM_SERVICE`, `PRODUCT`, `MEDICATION`, `CUSTOM` (default: `CUSTOM`) |
| `service_id` | UUID | If SERVICE | From services catalog |
| `custom_service_id` | UUID | If CUSTOM_SERVICE | Provider's custom service |
| `description` | string | If CUSTOM | Item description |
| `description_en` | string | No | English description |
| `description_ar` | string | No | Arabic description |
| `description_fr` | string | No | French description |
| `quantity` | decimal | No | Default: `1.00` |
| `unit` | string | No | Default: `unit` (auto-set to `session` for services) |
| `unit_price` | decimal | If CUSTOM | Price per unit (auto-set from service) |
| `discount_percentage` | decimal | No | Item-level discount % (default: `0.00`) |
| `notes` | string | No | Item notes |
| `order` | integer | No | Display order (default: `0`) |

**Validation:**
- Invoice must be in `DRAFT` status
- `SERVICE` type requires valid `service_id`
- `CUSTOM_SERVICE` type requires valid `custom_service_id`
- `CUSTOM` type requires `description` and `unit_price`

**Response (201 Created):** Full `InvoiceSerializer` with updated items and totals.

---

### Remove Item

```
POST /api/invoices/{id}/remove_item/
```

Remove an item from a **draft** invoice. Totals are automatically recalculated.

**Request Body:**
```json
{
    "item_id": "item-uuid"
}
```

**Response (200 OK):** Full `InvoiceSerializer` with updated items and totals.

---

### Record Payment

```
POST /api/invoices/{id}/record_payment/
```

Record a payment for a non-draft, non-cancelled invoice. The invoice status is automatically updated based on the payment amount.

**Request Body:**
```json
{
    "amount": "2500.00",
    "payment_method": "CARD",
    "payment_date": "2026-03-03T14:00:00Z",
    "reference_number": "TXN123456",
    "notes": "First installment"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | decimal | Yes | Payment amount (> 0) |
| `payment_method` | string | Yes | See [Payment Methods](#payment-methods) |
| `payment_date` | datetime | No | Default: now |
| `reference_number` | string | No | Transaction reference |
| `insurance_claim_number` | string | No | For insurance payments |
| `insurance_provider` | string | No | Insurance provider name |
| `is_refund` | boolean | No | Default: `false` |
| `refund_reason` | string | If refund | Required when `is_refund: true` |
| `original_payment` | UUID | No | Original payment (for refunds) |
| `notes` | string | No | Payment notes |

**Validation:**
- Invoice must NOT be `DRAFT` or `CANCELLED`
- Payment amount cannot exceed `amount_due` (unless refund)
- Refunds require `refund_reason`

**Response (201 Created):** Full `InvoiceSerializer` with updated payments and status.

---

### Get Activity Log

```
GET /api/invoices/{id}/activities/
```

Returns audit trail for the invoice.

**Response (200 OK):**
```json
[
    {
        "id": "activity-uuid",
        "invoice": "invoice-uuid",
        "activity_type": "CREATED",
        "description": "Invoice INV-20260303-A1B2C3D4 created",
        "old_value": null,
        "new_value": null,
        "performed_by": "user-uuid",
        "performed_by_name": "Dr. Ahmed Benali",
        "ip_address": null,
        "created_at": "2026-03-03T10:30:00Z"
    },
    {
        "id": "activity-uuid-2",
        "invoice": "invoice-uuid",
        "activity_type": "SENT",
        "description": "Invoice sent to Mohammed Khalil",
        "old_value": null,
        "new_value": null,
        "performed_by": "user-uuid",
        "performed_by_name": "Dr. Ahmed Benali",
        "ip_address": null,
        "created_at": "2026-03-03T11:00:00Z"
    }
]
```

**Activity Types:** `CREATED`, `UPDATED`, `SENT`, `VIEWED`, `ITEM_ADDED`, `ITEM_REMOVED`, `ITEM_UPDATED`, `PAYMENT_RECEIVED`, `PAYMENT_REFUNDED`, `STATUS_CHANGED`, `CANCELLED`, `REMINDER_SENT`, `NOTE_ADDED`

---

## Create from Appointment

```
POST /api/invoices/from_appointment/
```

Create an invoice automatically from a completed appointment. Auto-populates line items from the appointment's services.

**Request Body:**
```json
{
    "appointment_id": "appointment-uuid",
    "include_services": true,
    "tax_rate": "0.00",
    "due_days": 30,
    "notes": "Invoice for consultation"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `appointment_id` | UUID | Yes | Must be a COMPLETED appointment |
| `include_services` | boolean | No | Auto-add appointment services as items (default: `true`) |
| `tax_rate` | decimal | No | Tax rate % (default: `0.00`) |
| `due_days` | integer | No | Days until due (default: `30`, min: `0`) |
| `notes` | string | No | Invoice notes |

**Validation:**
- Appointment must exist and have status `COMPLETED`
- No invoice must already exist for this appointment
- Caller must be the appointment's provider (or admin)

**Response (201 Created):** Full `InvoiceSerializer`.

**What gets auto-populated:**
- `provider` → from appointment
- `patient_user` / `patient_record` → from appointment
- `invoice_type` → `SERVICE`
- `issue_date` → today
- `due_date` → today + `due_days`
- Items → primary service + each additional appointment service (with price, title, etc.)

---

## Payment Management

### List Payments

```
GET /api/invoices/payments/
```

Returns payments for the authenticated provider's invoices (or all for admins).

**Response (200 OK):**
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "payment-uuid",
            "invoice": "invoice-uuid",
            "invoice_number": "INV-20260303-A1B2C3D4",
            "amount": "3000.00",
            "currency": "DZD",
            "payment_method": "CASH",
            "payment_date": "2026-03-03T14:00:00Z",
            "reference_number": "",
            "insurance_claim_number": "",
            "insurance_provider": "",
            "is_verified": false,
            "verified_at": null,
            "verified_by": null,
            "is_refund": false,
            "refund_reason": "",
            "original_payment": null,
            "notes": "",
            "recorded_by": "user-uuid",
            "recorded_by_name": "Dr. Ahmed Benali",
            "created_at": "2026-03-03T14:00:00Z",
            "updated_at": "2026-03-03T14:00:00Z"
        }
    ]
}
```

### Verify Payment

```
POST /api/invoices/payments/{id}/verify/
```

**Request Body:**
```json
{
    "is_verified": true,
    "notes": "Verified via bank statement"
}
```

**Response (200 OK):** `PaymentSerializer` with updated verification fields.

### Refund Payment

```
POST /api/invoices/payments/{id}/refund/
```

**Request Body:**
```json
{
    "amount": "1000.00",
    "reason": "Service not provided"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | decimal | No | Refund amount (default: full original amount) |
| `reason` | string | Yes | Refund reason |

**Validation:**
- Total refunds cannot exceed original payment amount
- Reason is required

**Response (201 Created):** `PaymentSerializer` for the refund record.

---

## Payment Methods

| Method | Code | Description |
|--------|------|-------------|
| Cash | `CASH` | Cash payment |
| Card | `CARD` | Credit/Debit card |
| Bank Transfer | `BANK_TRANSFER` | Bank wire transfer |
| Mobile Payment | `MOBILE_PAYMENT` | CCP, BaridiMob, etc. |
| Insurance | `INSURANCE` | Insurance claim |
| Cheque | `CHEQUE` | Cheque payment |
| Other | `OTHER` | Other methods |

---

## Item Types

| Type | Code | Description | Required Fields |
|------|------|-------------|----------------|
| Service | `SERVICE` | Catalog service | `service_id` |
| Custom Service | `CUSTOM_SERVICE` | Provider's custom service | `custom_service_id` |
| Product | `PRODUCT` | Product (future) | `description`, `unit_price` |
| Medication | `MEDICATION` | Prescription medication | `description`, `unit_price` |
| Custom | `CUSTOM` | Manual entry | `description`, `unit_price` |

---

## Currencies

| Code | Name |
|------|------|
| `DZD` | Algerian Dinar (default) |
| `USD` | US Dollar |
| `EUR` | Euro |

---

## Permissions

| Action | Provider | Patient | Admin |
|--------|----------|---------|-------|
| List invoices (`GET /`) | Own invoices | Own invoices | All |
| My invoices (`GET /my/`) | - | Own (non-draft) | - |
| Create invoice | Yes | No | Yes |
| Update invoice | Own, draft | No | Yes |
| Delete invoice | Own, draft | No | Yes |
| Send invoice | Own | No | Yes |
| Cancel invoice | Own | No | Yes |
| Mark viewed | No | Own | Yes |
| Record payment | Own | No | Yes |
| Financial summary | Own data | No | All data |
| Uninvoiced appointments | Own | No | All |
| Verify payment | Own | No | Yes |
| Refund payment | Own | No | Yes |

---

## Example Workflows

### 1. Doctor's Daily Invoice Routine

```javascript
// Morning: Check what needs billing
const uninvoiced = await api.get('/api/invoices/uninvoiced_appointments/');

// For each uninvoiced appointment:
for (const apt of uninvoiced.data) {
    const { data: invoice } = await api.post('/api/invoices/from_appointment/', {
        appointment_id: apt.id,
        include_services: true,
        due_days: 30
    });
    
    // Send immediately
    await api.post(`/api/invoices/${invoice.id}/send/`);
}
```

### 2. Create Invoice After Appointment

```javascript
// Step 1: Complete the appointment
await api.post(`/api/appointments/${appointmentId}/complete/`);

// Step 2: Create invoice from appointment
const { data: invoice } = await api.post('/api/invoices/from_appointment/', {
    appointment_id: appointmentId,
    include_services: true,
    tax_rate: "0.00",
    due_days: 30,
    notes: "Thank you for your visit"
});

// Step 3: Add any extra items (tests, medications, etc.)
await api.post(`/api/invoices/${invoice.id}/add_item/`, {
    item_type: "CUSTOM",
    description: "Blood Test - CBC",
    unit_price: "1500.00",
    quantity: "1.00"
});

// Step 4: Send to patient
await api.post(`/api/invoices/${invoice.id}/send/`, {
    send_notification: true
});
```

### 3. Create Manual Invoice with Multiple Services

```javascript
const { data: invoice } = await api.post('/api/invoices/', {
    patient_user: patientId,
    invoice_type: "SERVICE",
    items: [
        {
            item_type: "SERVICE",
            service_id: consultationServiceId,
            quantity: "1.00"
        },
        {
            item_type: "SERVICE",
            service_id: ecgServiceId,
            quantity: "1.00"
        },
        {
            item_type: "CUSTOM",
            description: "Home Visit Fee",
            unit_price: "1500.00",
            quantity: "1.00"
        }
    ],
    tax_rate: "0.00",
    discount_type: "PERCENTAGE",
    discount_value: "10.00",
    discount_reason: "Returning patient"
});

// invoice.id, invoice.invoice_number, invoice.total are all available immediately
console.log(`Created: ${invoice.invoice_number}, Total: ${invoice.total} DZD`);
```

### 4. Partial Payment Flow

```javascript
// Invoice total: 10,000 DZD

// First payment: 5,000 DZD
await api.post(`/api/invoices/${invoiceId}/record_payment/`, {
    amount: "5000.00",
    payment_method: "CASH"
});
// Status → PARTIALLY_PAID, amount_due → 5000.00

// Second payment: 5,000 DZD
await api.post(`/api/invoices/${invoiceId}/record_payment/`, {
    amount: "5000.00",
    payment_method: "CARD",
    reference_number: "TXN789"
});
// Status → PAID, amount_due → 0.00
```

### 5. Financial Dashboard Integration

```javascript
const { data: summary } = await api.get('/api/invoices/financial_summary/', {
    params: { period: 'month' }
});

console.log(`Total Revenue: ${summary.total_revenue} DZD`);
console.log(`Outstanding: ${summary.total_outstanding} DZD`);
console.log(`Uninvoiced Appointments: ${summary.uninvoiced_appointments}`);
console.log(`Overdue Invoices: ${summary.overdue_count}`);
```

### 6. Filtering Invoices

```javascript
// Get only overdue invoices
const overdue = await api.get('/api/invoices/', {
    params: { status: 'OVERDUE' }
});

// Search by patient name
const search = await api.get('/api/invoices/', {
    params: { search: 'Mohammed' }
});

// Date range + type
const filtered = await api.get('/api/invoices/', {
    params: {
        start_date: '2026-01-01',
        end_date: '2026-03-31',
        invoice_type: 'SERVICE',
        ordering: '-total'
    }
});
```

### 7. React Dashboard Component

```jsx
import React, { useState, useEffect } from 'react';

const InvoiceDashboard = () => {
    const [summary, setSummary] = useState(null);
    const [invoices, setInvoices] = useState([]);
    const [uninvoiced, setUninvoiced] = useState([]);
    const [statusFilter, setStatusFilter] = useState('');
    
    useEffect(() => {
        fetchDashboardData();
    }, []);
    
    useEffect(() => {
        fetchInvoices();
    }, [statusFilter]);
    
    const fetchDashboardData = async () => {
        const [summaryRes, uninvoicedRes] = await Promise.all([
            api.get('/api/invoices/financial_summary/?period=month'),
            api.get('/api/invoices/uninvoiced_appointments/')
        ]);
        setSummary(summaryRes.data);
        setUninvoiced(uninvoicedRes.data);
    };
    
    const fetchInvoices = async () => {
        const params = {};
        if (statusFilter) params.status = statusFilter;
        const res = await api.get('/api/invoices/', { params });
        setInvoices(res.data.results);
    };
    
    const createFromAppointment = async (appointmentId) => {
        const { data: invoice } = await api.post('/api/invoices/from_appointment/', {
            appointment_id: appointmentId,
            include_services: true,
            due_days: 30
        });
        fetchDashboardData();
        fetchInvoices();
        return invoice;
    };
    
    return (
        <div className="invoice-dashboard">
            {/* Financial Summary Cards */}
            <div className="summary-cards">
                <div className="card">
                    <h3>Revenue This Month</h3>
                    <p>{summary?.total_revenue} DZD</p>
                </div>
                <div className="card">
                    <h3>Outstanding</h3>
                    <p>{summary?.total_outstanding} DZD</p>
                </div>
                <div className="card alert">
                    <h3>Needs Invoicing</h3>
                    <p>{uninvoiced.length} appointments</p>
                </div>
            </div>
            
            {/* Status Filter */}
            <select onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="">All</option>
                <option value="DRAFT">Draft</option>
                <option value="SENT">Sent</option>
                <option value="PAID">Paid</option>
                <option value="OVERDUE">Overdue</option>
            </select>
            
            {/* Uninvoiced Appointments */}
            {uninvoiced.length > 0 && (
                <div className="uninvoiced-section">
                    <h3>Appointments Needing Invoices</h3>
                    <ul>
                        {uninvoiced.map(apt => (
                            <li key={apt.id}>
                                <span>{apt.patient_display_name}</span>
                                <span>{apt.scheduled_date}</span>
                                <button onClick={() => createFromAppointment(apt.id)}>
                                    Create Invoice
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
            
            {/* Invoice List */}
            <table>
                <thead>
                    <tr>
                        <th>Invoice #</th>
                        <th>Patient</th>
                        <th>Total</th>
                        <th>Due</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {invoices.map(inv => (
                        <tr key={inv.id}>
                            <td>{inv.invoice_number}</td>
                            <td>{inv.patient_display_name}</td>
                            <td>{inv.total} {inv.currency}</td>
                            <td>{inv.amount_due} {inv.currency}</td>
                            <td>{inv.status_display}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
```

---

## Error Responses

All errors follow a consistent format:

**400 Bad Request** (validation error):
```json
{
    "patient_user": ["This field is required."],
    "items": [{"unit_price": ["Required for CUSTOM type items."]}]
}
```

**403 Forbidden** (permission denied):
```json
{
    "detail": "Only providers can manage invoices."
}
```

**404 Not Found**:
```json
{
    "detail": "Not found."
}
```
