# Nurse Mobile App - Invoices API

## Overview

This documentation covers the **Invoices API** for the Nurse Mobile Application. Nurses can create, manage, and track invoices for their nursing services, home visits, and care sessions.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Invoice Types](#invoice-types)
4. [Invoice Status Flow](#invoice-status-flow)
5. [Automatic Invoice Creation](#automatic-invoice-creation)
6. [Invoice Management](#invoice-management)
   - [List My Invoices](#list-my-invoices)
   - [Create Invoice](#create-invoice)
   - [Get Invoice Details](#get-invoice-details)
   - [Update Invoice](#update-invoice-draft-only)
   - [Delete Invoice](#delete-invoice-draft-only)
7. [Invoice Actions](#invoice-actions)
   - [Send Invoice](#send-invoice)
   - [Cancel Invoice](#cancel-invoice)
   - [Add Item](#add-item)
   - [Remove Item](#remove-item)
   - [Record Payment](#record-payment)
8. [Create from Appointment](#create-from-appointment)
9. [Statistics](#statistics)
10. [Payment Methods](#payment-methods)
11. [Common Workflows](#common-workflows)
12. [Error Handling](#error-handling)

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

**Important:** Your nurse provider account must be `APPROVED` to access invoice features.

---

## Invoice Types

| Type | Description | Common Use Case for Nurses |
|------|-------------|---------------------------|
| `SERVICE` | Healthcare services | Home visits, injections, wound care |
| `CUSTOM` | Manual/custom items | Special care sessions, supplies |

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
│                       │               │                              │
│                       ▼               ▼                              │
│                  ┌──────────┐    ┌───────────────┐                   │
│                  │ OVERDUE  │    │PARTIALLY_PAID │                   │
│                  └──────────┘    └───────────────┘                   │
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

---

## Automatic Invoice Creation

> **💡 Automatic Invoicing for Nurse Requests**
>
> When you complete a nurse service request, the system can automatically create an invoice. This is controlled by backend settings. If enabled, you'll see the invoice in your list immediately after marking the request as completed.

---

## Invoice Management

### List My Invoices

```
GET /api/invoices/
```

Returns all invoices you've created.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: DRAFT, SENT, PAID, OVERDUE |
| `start_date` | string | Filter from date (YYYY-MM-DD) |
| `end_date` | string | Filter to date (YYYY-MM-DD) |
| `search` | string | Search by invoice number or patient name |

**Response (200 OK):**
```json
{
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "invoice-uuid",
            "invoice_number": "INV-20260202-A1B2C3D4",
            "provider_name": "Nurse Fatima Zahra",
            "patient_display_name": "Ahmed Benali",
            "invoice_type": "SERVICE",
            "status": "SENT",
            "status_display": "Sent",
            "issue_date": "2026-02-02",
            "due_date": "2026-03-02",
            "currency": "DZD",
            "total": "3500.00",
            "amount_paid": "0.00",
            "amount_due": "3500.00",
            "items_count": 2,
            "created_at": "2026-02-02T10:30:00Z"
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
    "issue_date": "2026-02-02",
    "due_date": "2026-03-02",
    "currency": "DZD",
    "notes": "Thank you for choosing our nursing services",
    "items": [
        {
            "item_type": "SERVICE",
            "service_id": "service-uuid",
            "quantity": 1
        },
        {
            "item_type": "CUSTOM",
            "description": "Home visit - wound dressing",
            "unit_price": "1500.00",
            "quantity": 2
        }
    ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `patient_user` | UUID | ✅* | Patient with account |
| `patient_record` | integer | ✅* | Patient record ID |
| `invoice_type` | string | ❌ | SERVICE or CUSTOM (default: SERVICE) |
| `issue_date` | date | ❌ | Invoice date (default: today) |
| `due_date` | date | ❌ | Payment due date |
| `currency` | string | ❌ | DZD, USD, EUR (default: DZD) |
| `notes` | string | ❌ | Notes for the patient |
| `items` | array | ❌ | Line items |

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
    "invoice_number": "INV-20260202-A1B2C3D4",
    "provider_name": "Nurse Fatima Zahra",
    "patient_display_name": "Ahmed Benali",
    "invoice_type": "SERVICE",
    "status": "SENT",
    "issue_date": "2026-02-02",
    "due_date": "2026-03-02",
    "currency": "DZD",
    "subtotal": "4500.00",
    "tax_amount": "0.00",
    "discount_amount": "0.00",
    "total": "4500.00",
    "amount_paid": "1500.00",
    "amount_due": "3000.00",
    "notes": "Thank you for choosing our nursing services",
    "items": [
        {
            "id": "item-uuid",
            "item_type": "SERVICE",
            "description": "Insulin Injection",
            "quantity": 1,
            "unit_price": "1500.00",
            "total": "1500.00"
        },
        {
            "id": "item-uuid-2",
            "item_type": "CUSTOM",
            "description": "Home visit - wound dressing",
            "quantity": 2,
            "unit_price": "1500.00",
            "total": "3000.00"
        }
    ],
    "payments": [
        {
            "id": "payment-uuid",
            "amount": "1500.00",
            "payment_method": "CASH",
            "payment_date": "2026-02-02T14:00:00Z",
            "is_verified": true
        }
    ],
    "created_at": "2026-02-02T10:30:00Z"
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

> ⚠️ Only `DRAFT` invoices can be deleted.

---

## Invoice Actions

### Send Invoice

```
POST /api/invoices/{id}/send/
```

Sends the invoice to the patient (changes status from DRAFT to SENT).

**Request Body:**
```json
{
    "send_notification": true,
    "message": "Please find attached your invoice for nursing services"
}
```

---

### Cancel Invoice

```
POST /api/invoices/{id}/cancel/
```

**Request Body:**
```json
{
    "reason": "Service was rescheduled"
}
```

---

### Add Item

```
POST /api/invoices/{id}/add_item/
```

Add an item to a draft invoice.

**Request Body (Custom Item):**
```json
{
    "item_type": "CUSTOM",
    "description": "Additional wound dressing supplies",
    "unit_price": "500.00",
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

Record a payment from the patient (especially useful for cash payments during home visits).

**Request Body:**
```json
{
    "amount": "1500.00",
    "payment_method": "CASH",
    "notes": "Paid during home visit"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | decimal | ✅ | Payment amount |
| `payment_method` | string | ✅ | CASH, CARD, MOBILE_PAYMENT, etc. |
| `reference_number` | string | ❌ | Transaction reference |
| `notes` | string | ❌ | Payment notes |

---

## Create from Appointment

```
POST /api/invoices/from_appointment/
```

Create an invoice from a completed nursing appointment.

**Request Body:**
```json
{
    "appointment_id": "appointment-uuid",
    "include_services": true,
    "due_days": 30,
    "notes": "Invoice for home nursing visit"
}
```

---

## Statistics

### Get My Invoice Statistics

```
GET /api/invoices/statistics/
```

**Query Parameters:**
- `start_date`: Filter from date
- `end_date`: Filter to date

**Response:**
```json
{
    "total_invoices": 45,
    "total_amount": "157500.00",
    "total_paid": "120000.00",
    "total_outstanding": "37500.00",
    "by_status": {
        "draft_count": 2,
        "sent_count": 8,
        "paid_count": 30,
        "overdue_count": 5
    }
}
```

---

## Payment Methods

| Method | Code | Best For |
|--------|------|----------|
| Cash | `CASH` | Home visits (most common) |
| Card | `CARD` | Clinic payments |
| Mobile Payment | `MOBILE_PAYMENT` | CCP, BaridiMob |
| Bank Transfer | `BANK_TRANSFER` | Larger amounts |
| Other | `OTHER` | Any other method |

---

## Common Workflows

### After Completing a Home Visit

```
1. Complete the appointment/nurse request
2. Create invoice:
   POST /api/invoices/from_appointment/
   (or invoice may be auto-created)

3. If patient pays cash immediately:
   POST /api/invoices/{id}/record_payment/
   - amount: full amount
   - payment_method: "CASH"
   
4. If patient will pay later:
   POST /api/invoices/{id}/send/
   - Patient receives notification
   - Record payment when received
```

### Partial Payment During Visit

```
1. Invoice total: 3,000 DZD
2. Patient pays 1,500 DZD cash now:
   POST /api/invoices/{id}/record_payment/
   {
     "amount": "1500.00",
     "payment_method": "CASH",
     "notes": "Partial payment during visit"
   }
   → Status: PARTIALLY_PAID
   
3. Later, patient sends remaining via BaridiMob:
   POST /api/invoices/{id}/record_payment/
   {
     "amount": "1500.00",
     "payment_method": "MOBILE_PAYMENT",
     "reference_number": "BARIDIMOB123"
   }
   → Status: PAID
```

### Quick Invoice After Service

```
1. Patient already in your list
2. Create manual invoice:
   POST /api/invoices/
   {
     "patient_user": "patient-uuid",
     "items": [
       {
         "item_type": "CUSTOM",
         "description": "Daily insulin injection - home visit",
         "unit_price": "1500.00",
         "quantity": 1
       }
     ]
   }
3. Record cash payment if paid immediately
4. Or send to patient for later payment
```

---

## Error Handling

### Common Errors

**400 Bad Request - Cannot Send Empty Invoice**
```json
{
    "error": "Cannot send invoice without items."
}
```

**400 Bad Request - Cannot Modify Sent Invoice**
```json
{
    "error": "Can only add items to draft invoices."
}
```

**400 Bad Request - Invoice Already Exists**
```json
{
    "error": "An invoice already exists for this appointment."
}
```

**403 Forbidden - Not Your Invoice**
```json
{
    "error": "You can only create invoices for your own appointments."
}
```

---

## Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| List invoices | `/api/invoices/` | GET |
| Create invoice | `/api/invoices/` | POST |
| Get invoice | `/api/invoices/{id}/` | GET |
| Send invoice | `/api/invoices/{id}/send/` | POST |
| Cancel invoice | `/api/invoices/{id}/cancel/` | POST |
| Add item | `/api/invoices/{id}/add_item/` | POST |
| Record payment | `/api/invoices/{id}/record_payment/` | POST |
| From appointment | `/api/invoices/from_appointment/` | POST |
| Statistics | `/api/invoices/statistics/` | GET |
