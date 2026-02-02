# Provider Dashboards - Invoices API

## Overview

This documentation covers the **Invoices API** for Provider Web Dashboards. Providers can create, manage, and track invoices for healthcare services, products, and custom billing items.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Invoice Types](#invoice-types)
4. [Invoice Status Flow](#invoice-status-flow)
5. [Invoice Management](#invoice-management)
   - [List Invoices](#list-invoices)
   - [Create Invoice](#create-invoice)
   - [Get Invoice Details](#get-invoice-details)
   - [Update Invoice](#update-invoice-draft-only)
   - [Delete Invoice](#delete-invoice-draft-only)
6. [Invoice Actions](#invoice-actions)
   - [Send Invoice](#send-invoice)
   - [Cancel Invoice](#cancel-invoice)
   - [Add Item](#add-item)
   - [Remove Item](#remove-item)
   - [Record Payment](#record-payment)
   - [Get Activity Log](#get-activity-log)
7. [Create from Appointment](#create-from-appointment)
8. [Statistics & Reports](#statistics--reports)
9. [Payment Management](#payment-management)
   - [List Payments](#list-payments)
   - [Verify Payment](#verify-payment)
   - [Refund Payment](#refund-payment)
10. [Payment Methods](#payment-methods)
11. [Item Types](#item-types)
12. [Permissions](#permissions)
13. [Example Workflows](#example-workflows)

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

**Important:** Provider accounts must be `APPROVED` to access invoice management features.

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
│                      INVOICE STATUS FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │  DRAFT   │───▶│   SENT   │───▶│  VIEWED  │───▶│   PAID   │       │
│  │ (edit)   │    │          │    │          │    │          │       │
│  └──────────┘    └────┬─────┘    └────┬─────┘    └──────────┘       │
│       │               │               │               │              │
│       ▼               ▼               ▼               ▼              │
│  ┌──────────┐    ┌──────────┐    ┌───────────────┐  ┌─────────────┐ │
│  │ CANCELLED│    │ OVERDUE  │    │PARTIALLY_PAID │  │  REFUNDED   │ │
│  └──────────┘    └──────────┘    └───────────────┘  └─────────────┘ │
│                                                                      │
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

## Invoice Management

### List Invoices

```
GET /api/invoices/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: DRAFT, SENT, PAID, OVERDUE, etc. |
| `invoice_type` | string | Filter: SERVICE, PRODUCT, MIXED, CUSTOM |
| `start_date` | string | Filter by issue date from (YYYY-MM-DD) |
| `end_date` | string | Filter by issue date to (YYYY-MM-DD) |
| `search` | string | Search by invoice number or patient name |
| `ordering` | string | Sort by field (e.g., `-created_at`, `due_date`) |

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
            "quantity": 1
        },
        {
            "item_type": "CUSTOM",
            "description": "Additional consultation",
            "unit_price": "2000.00",
            "quantity": 1
        }
    ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `patient_user` | UUID | ✅* | Patient with account |
| `patient_record` | integer | ✅* | Patient record ID (for patients without accounts) |
| `invoice_type` | string | ❌ | SERVICE, PRODUCT, MIXED, CUSTOM (default: SERVICE) |
| `issue_date` | date | ❌ | Invoice date (default: today) |
| `due_date` | date | ❌ | Payment due date |
| `currency` | string | ❌ | DZD, USD, EUR (default: DZD) |
| `tax_rate` | decimal | ❌ | Tax percentage |
| `discount_type` | string | ❌ | PERCENTAGE or FIXED |
| `discount_value` | decimal | ❌ | Discount amount |
| `notes` | string | ❌ | Notes for the patient |
| `items` | array | ❌ | Line items (can add later) |

> *Either `patient_user` OR `patient_record` must be provided.

---

### Get Invoice Details

```
GET /api/invoices/{id}/
```

**Response (200 OK):**
```json
{
    "id": "invoice-uuid",
    "invoice_number": "INV-20260115-A1B2C3D4",
    "provider": "provider-uuid",
    "provider_name": "Dr. Ahmed Benali",
    "patient_user": "patient-uuid",
    "patient_display_name": "Mohammed Khalil",
    "invoice_type": "SERVICE",
    "status": "SENT",
    "status_display": "Sent",
    "issue_date": "2026-01-15",
    "due_date": "2026-02-14",
    "currency": "DZD",
    "subtotal": "5500.00",
    "tax_rate": "19.00",
    "tax_amount": "1045.00",
    "discount_type": "PERCENTAGE",
    "discount_value": "10.00",
    "discount_amount": "550.00",
    "total": "5995.00",
    "amount_paid": "2000.00",
    "amount_due": "3995.00",
    "notes": "Thank you for your visit",
    "items": [
        {
            "id": "item-uuid",
            "item_type": "SERVICE",
            "description": "General Consultation",
            "quantity": 1,
            "unit_price": "3000.00",
            "total": "3000.00"
        },
        {
            "id": "item-uuid-2",
            "item_type": "CUSTOM",
            "description": "Blood Test",
            "quantity": 1,
            "unit_price": "2500.00",
            "total": "2500.00"
        }
    ],
    "payments": [
        {
            "id": "payment-uuid",
            "amount": "2000.00",
            "payment_method": "CASH",
            "payment_date": "2026-01-15T14:00:00Z",
            "is_verified": true
        }
    ],
    "appointment": null,
    "prescription": null,
    "created_at": "2026-01-15T10:30:00Z"
}
```

---

### Update Invoice (Draft only)

```
PATCH /api/invoices/{id}/
```

> ⚠️ Only `DRAFT` invoices can be updated.

---

### Delete Invoice (Draft only)

```
DELETE /api/invoices/{id}/
```

> ⚠️ Only `DRAFT` invoices can be deleted. For sent invoices, use Cancel instead.

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

**Validation:**
- Invoice must be in `DRAFT` status
- Invoice must have at least one item

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

**Validation:**
- Cannot cancel `PAID` or already `CANCELLED` invoices

---

### Add Item

```
POST /api/invoices/{id}/add_item/
```

Add an item to a draft invoice.

**Request Body (Service):**
```json
{
    "item_type": "SERVICE",
    "service_id": "service-uuid",
    "quantity": 1,
    "notes": "Regular consultation"
}
```

**Request Body (Custom Item):**
```json
{
    "item_type": "CUSTOM",
    "description": "Home visit fee",
    "unit_price": "1500.00",
    "quantity": 1
}
```

---

### Remove Item

```
POST /api/invoices/{id}/remove_item/
```

**Request Body:**
```json
{
    "item_id": "item-uuid"
}
```

---

### Record Payment

```
POST /api/invoices/{id}/record_payment/
```

**Request Body:**
```json
{
    "amount": "2500.00",
    "payment_method": "CARD",
    "reference_number": "TXN123456",
    "notes": "First installment"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | decimal | ✅ | Payment amount |
| `payment_method` | string | ✅ | See Payment Methods below |
| `reference_number` | string | ❌ | Transaction reference |
| `notes` | string | ❌ | Payment notes |

---

### Get Activity Log

```
GET /api/invoices/{id}/activities/
```

Returns audit trail for the invoice (created, sent, payments, etc.).

---

## Create from Appointment

```
POST /api/invoices/from_appointment/
```

Create an invoice automatically from a completed appointment.

**Request Body:**
```json
{
    "appointment_id": "appointment-uuid",
    "include_services": true,
    "tax_rate": "19.00",
    "due_days": 30,
    "notes": "Invoice for consultation"
}
```

---

## Statistics & Reports

### Get Statistics

```
GET /api/invoices/statistics/
```

**Query Parameters:**
- `start_date`: Filter from date
- `end_date`: Filter to date

**Response:**
```json
{
    "total_invoices": 150,
    "total_amount": "750000.00",
    "total_paid": "500000.00",
    "total_outstanding": "250000.00",
    "by_status": {
        "draft_count": 5,
        "sent_count": 20,
        "paid_count": 100,
        "overdue_count": 10,
        "cancelled_count": 15
    },
    "by_type": {
        "service_invoices": 120,
        "product_invoices": 15,
        "mixed_invoices": 10,
        "custom_invoices": 5
    }
}
```

### Get Overdue Invoices

```
GET /api/invoices/overdue/
```

Returns list of overdue invoices and marks newly overdue ones.

---

## Payment Management

### List Payments

```
GET /api/invoices/payments/
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

| Type | Code | Description | Source |
|------|------|-------------|--------|
| Service | `SERVICE` | Catalog service | services.Service |
| Custom Service | `CUSTOM_SERVICE` | Provider's custom service | services.ProviderCustomService |
| Product | `PRODUCT` | Product (future) | - |
| Medication | `MEDICATION` | Prescription medication | prescriptions.PrescriptionItem |
| Custom | `CUSTOM` | Manual entry | None |

---

## Permissions

| Action | Provider | Admin |
|--------|----------|-------|
| List invoices | ✅ (own) | ✅ (all) |
| Create invoice | ✅ | ✅ |
| Update invoice | ✅ (own, draft) | ✅ |
| Delete invoice | ✅ (own, draft) | ✅ |
| Send invoice | ✅ (own) | ✅ |
| Cancel invoice | ✅ (own) | ✅ |
| Record payment | ✅ (own) | ✅ |
| View statistics | ✅ (own) | ✅ (all) |

---

## Example Workflows

### Create Invoice After Appointment

```
1. Complete the appointment
2. POST /api/invoices/from_appointment/
   - Provide appointment_id
   - System creates invoice with appointment services
3. Review and modify items if needed
   - POST /api/invoices/{id}/add_item/
4. Send to patient
   - POST /api/invoices/{id}/send/
5. Record payment when received
   - POST /api/invoices/{id}/record_payment/
```

### Partial Payment Flow

```
1. Invoice total: 10,000 DZD
2. First payment: 5,000 DZD
   - POST /api/invoices/{id}/record_payment/
   - Status changes to PARTIALLY_PAID
   - Amount due: 5,000 DZD
3. Second payment: 5,000 DZD
   - POST /api/invoices/{id}/record_payment/
   - Status changes to PAID
   - Amount due: 0 DZD
```

### Refund Flow

```
1. Invoice is PAID (10,000 DZD)
2. Issue partial refund (3,000 DZD)
   - POST /api/invoices/payments/{payment_id}/refund/
   - Status: PARTIALLY_REFUNDED
3. Or issue full refund
   - Status: REFUNDED
```
