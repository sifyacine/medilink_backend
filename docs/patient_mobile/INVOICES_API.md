# Patient Mobile App - Invoices API

## Overview

This documentation covers the **Invoices API** for the Patient Mobile Application. Patients can view invoices sent to them by healthcare providers, track payment status, and mark invoices as viewed.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Understanding Invoice Status](#understanding-invoice-status)
4. [My Invoices](#my-invoices)
   - [List My Invoices](#list-my-invoices)
   - [Get Invoice Details](#get-invoice-details)
   - [Mark Invoice as Viewed](#mark-invoice-as-viewed)
5. [Payment Information](#payment-information)
6. [Invoice Notifications](#invoice-notifications)
7. [Error Handling](#error-handling)

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

## Understanding Invoice Status

When you receive an invoice from a healthcare provider, it goes through these statuses:

| Status | What It Means | Action Required |
|--------|---------------|-----------------|
| `SENT` | Invoice has been sent to you | Review and pay |
| `VIEWED` | You've opened/viewed the invoice | Pay when ready |
| `PARTIALLY_PAID` | You've made a partial payment | Pay remaining balance |
| `PAID` | Fully paid | No action needed ✓ |
| `OVERDUE` | Payment is past due date | Pay immediately |
| `CANCELLED` | Provider cancelled the invoice | No action needed |

> **Note:** You will never see `DRAFT` invoices - those are only visible to the provider before they send them to you.

---

## My Invoices

### List My Invoices

Get all invoices issued to you.

```
GET /api/invoices/my/
```

This is a simplified endpoint specifically for patients.

**Response (200 OK):**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "invoice-uuid",
            "invoice_number": "INV-20260202-A1B2C3D4",
            "provider_name": "Dr. Mohamed Kaddour",
            "patient_display_name": "Ahmed Benali",
            "invoice_type": "SERVICE",
            "status": "SENT",
            "status_display": "Sent",
            "issue_date": "2026-02-02",
            "due_date": "2026-03-02",
            "currency": "DZD",
            "total": "5000.00",
            "amount_paid": "0.00",
            "amount_due": "5000.00",
            "items_count": 2,
            "created_at": "2026-02-02T10:30:00Z"
        },
        {
            "id": "invoice-uuid-2",
            "invoice_number": "INV-20260115-E5F6G7H8",
            "provider_name": "Nurse Fatima Zahra",
            "invoice_type": "SERVICE",
            "status": "PAID",
            "status_display": "Paid",
            "issue_date": "2026-01-15",
            "due_date": "2026-02-14",
            "currency": "DZD",
            "total": "3000.00",
            "amount_paid": "3000.00",
            "amount_due": "0.00",
            "items_count": 1,
            "created_at": "2026-01-15T14:00:00Z"
        }
    ]
}
```

### Alternative: Using Main Invoices Endpoint

You can also use the main invoices endpoint, which will automatically filter to show only your invoices:

```
GET /api/invoices/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: SENT, PAID, OVERDUE, etc. |
| `start_date` | string | Filter by issue date from (YYYY-MM-DD) |
| `end_date` | string | Filter by issue date to (YYYY-MM-DD) |

**Example - Get Unpaid Invoices:**
```
GET /api/invoices/?status=SENT
```

**Example - Get Overdue Invoices:**
```
GET /api/invoices/?status=OVERDUE
```

---

### Get Invoice Details

View the full details of an invoice including all line items and payment history.

```
GET /api/invoices/{id}/
```

**Response (200 OK):**
```json
{
    "id": "invoice-uuid",
    "invoice_number": "INV-20260202-A1B2C3D4",
    "provider": "provider-uuid",
    "provider_name": "Dr. Mohamed Kaddour",
    "patient_display_name": "Ahmed Benali",
    "invoice_type": "SERVICE",
    "status": "SENT",
    "status_display": "Sent",
    "issue_date": "2026-02-02",
    "due_date": "2026-03-02",
    "currency": "DZD",
    "subtotal": "5500.00",
    "tax_rate": "0.00",
    "tax_amount": "0.00",
    "discount_type": "PERCENTAGE",
    "discount_value": "10.00",
    "discount_amount": "550.00",
    "total": "4950.00",
    "amount_paid": "0.00",
    "amount_due": "4950.00",
    "notes": "Thank you for your visit. Payment due within 30 days.",
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
            "item_type": "SERVICE",
            "description": "ECG Test",
            "quantity": 1,
            "unit_price": "2500.00",
            "total": "2500.00"
        }
    ],
    "payments": [],
    "appointment": {
        "id": "appointment-uuid",
        "scheduled_date": "2026-02-01",
        "scheduled_time": "10:00:00"
    },
    "created_at": "2026-02-02T10:30:00Z"
}
```

### Invoice Fields Explained

| Field | Description |
|-------|-------------|
| `invoice_number` | Unique invoice reference (e.g., INV-20260202-A1B2C3D4) |
| `provider_name` | Name of the doctor/nurse/clinic who issued the invoice |
| `issue_date` | Date the invoice was created |
| `due_date` | Date by which payment is expected |
| `subtotal` | Total before tax and discounts |
| `tax_amount` | Tax applied (if any) |
| `discount_amount` | Discount applied (if any) |
| `total` | Final amount to pay |
| `amount_paid` | Amount already paid |
| `amount_due` | Remaining amount to pay |
| `items` | List of services/products being billed |
| `payments` | History of payments made |

---

### Mark Invoice as Viewed

When you open an invoice, call this endpoint to mark it as viewed. This helps the provider know you've received and seen the invoice.

```
POST /api/invoices/{id}/mark_viewed/
```

**Request Body:** (empty or optional)
```json
{}
```

**Response (200 OK):**
```json
{
    "id": "invoice-uuid",
    "invoice_number": "INV-20260202-A1B2C3D4",
    "status": "VIEWED",
    "status_display": "Viewed",
    ...
}
```

> **💡 Tip:** Call this endpoint automatically when the user opens an invoice detail screen in your app.

---

## Payment Information

### How Payments Work

Payments are recorded by the provider, not by patients directly through the API. Here's the typical flow:

1. **You receive an invoice** (notification + appears in your list)
2. **You view the invoice** (call `mark_viewed`)
3. **You pay the provider** via:
   - Cash (during visit or at their office)
   - Bank transfer
   - Mobile payment (CCP, BaridiMob)
   - Card payment at their facility
4. **Provider records the payment** in the system
5. **Invoice status updates** to PAID or PARTIALLY_PAID

### Viewing Payment History

Payment history is included in the invoice details response:

```json
{
    "payments": [
        {
            "id": "payment-uuid",
            "amount": "2000.00",
            "payment_method": "CASH",
            "payment_method_display": "Cash",
            "payment_date": "2026-02-05T14:00:00Z",
            "reference_number": null,
            "notes": "Partial payment",
            "is_verified": true
        },
        {
            "id": "payment-uuid-2",
            "amount": "2950.00",
            "payment_method": "MOBILE_PAYMENT",
            "payment_method_display": "Mobile Payment",
            "payment_date": "2026-02-10T09:30:00Z",
            "reference_number": "BARIDIMOB123456",
            "notes": "Remaining balance",
            "is_verified": true
        }
    ]
}
```

### Payment Methods Providers Accept

| Method | Description |
|--------|-------------|
| `CASH` | Cash payment |
| `CARD` | Credit/Debit card |
| `BANK_TRANSFER` | Bank wire transfer |
| `MOBILE_PAYMENT` | CCP, BaridiMob, etc. |
| `INSURANCE` | Insurance coverage |
| `CHEQUE` | Cheque payment |

---

## Invoice Notifications

You will receive notifications when:

1. **New Invoice Sent** - A provider sends you an invoice
2. **Payment Recorded** - The provider confirms your payment
3. **Invoice Overdue** - Your invoice is past the due date

### Notification Example

```json
{
    "type": "INVOICE_SENT",
    "title": "New Invoice",
    "message": "Dr. Mohamed Kaddour has sent you an invoice for 5,000.00 DZD",
    "data": {
        "invoice_id": "invoice-uuid",
        "invoice_number": "INV-20260202-A1B2C3D4",
        "amount": "5000.00",
        "currency": "DZD"
    }
}
```

---

## Error Handling

### Common Errors

**401 Unauthorized - Not Logged In**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden - Not Your Invoice**
```json
{
    "detail": "You do not have permission to perform this action."
}
```

**404 Not Found - Invoice Doesn't Exist**
```json
{
    "detail": "Not found."
}
```

---

## Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| List my invoices | `/api/invoices/my/` | GET |
| List invoices (filtered) | `/api/invoices/` | GET |
| Get invoice details | `/api/invoices/{id}/` | GET |
| Mark as viewed | `/api/invoices/{id}/mark_viewed/` | POST |

---

## Mobile App Integration Tips

### Invoice List Screen
```
1. Call GET /api/invoices/my/
2. Display invoices sorted by date (newest first)
3. Show status badges (color-coded):
   - SENT: Blue
   - VIEWED: Gray
   - PARTIALLY_PAID: Orange
   - PAID: Green
   - OVERDUE: Red
4. Show amount_due prominently
```

### Invoice Detail Screen
```
1. Call GET /api/invoices/{id}/
2. Immediately call POST /api/invoices/{id}/mark_viewed/
3. Display:
   - Provider name and invoice number
   - Due date (highlight if overdue)
   - List of items with prices
   - Total, amount paid, amount due
   - Payment history (if any)
4. Show payment instructions from notes field
```

### Handling Overdue Invoices
```
1. Filter: GET /api/invoices/?status=OVERDUE
2. Show prominently in dashboard/home
3. Display urgent notification badge
4. Consider push notification for overdue invoices
```
