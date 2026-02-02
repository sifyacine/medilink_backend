# Provider Dashboards - Invoices API

## Overview

This documentation covers the **Invoices API** for Provider Web Dashboards. Providers (doctors, nurses, clinics) can create, manage, and track invoices for healthcare services, consultations, and custom billing items.

**Key Features for Doctors:**
- 🏥 **Invoice Consultations** - Create invoices from completed appointments
- 💊 **Invoice Services** - Bill for medical services you provide
- 📊 **Financial Dashboard** - Track revenue, outstanding payments, and trends
- 🔔 **Uninvoiced Appointments** - Easily find appointments that need billing
- 💳 **Payment Tracking** - Record and verify payments with multiple methods

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
   - [List Invoices](#list-invoices)
   - [Create Invoice](#create-invoice)
   - [Get Invoice Details](#get-invoice-details)
   - [Update Invoice](#update-invoice-draft-only)
   - [Delete Invoice](#delete-invoice-draft-only)
8. [Invoice Actions](#invoice-actions)
   - [Send Invoice](#send-invoice)
   - [Cancel Invoice](#cancel-invoice)
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

**Important:** Provider accounts must be `APPROVED` to access invoice management features.

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
    "start_date": "2026-01-02",
    "end_date": "2026-02-02",
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
        {"month": "2026-01-01", "total": "75000.00", "count": 25},
        {"month": "2026-02-01", "total": "75000.00", "count": 23}
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
- `start_date`: Filter from date (YYYY-MM-DD)
- `end_date`: Filter to date (YYYY-MM-DD)

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

**Response (200 OK):**
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
    },
    {
        "id": "appointment-uuid-2",
        "patient_display_name": "Fatima Benali",
        "scheduled_date": "2026-01-29",
        "scheduled_time": "14:30:00",
        "status": "COMPLETED",
        "service": {
            "id": "service-uuid",
            "title": "Follow-up Visit",
            "price": "2000.00"
        },
        "location_type": "ONLINE",
        "completed_at": "2026-01-29T15:00:00Z"
    }
]
```

> **Tip:** Use this endpoint to show doctors which appointments need to be billed!

---

### Overdue Invoices

Get list of overdue invoices and automatically mark newly overdue ones.

```
GET /api/invoices/overdue/
```

**Response (200 OK):**
```json
[
    {
        "id": "invoice-uuid",
        "invoice_number": "INV-20260115-A1B2C3D4",
        "patient_display_name": "Ahmed Khelifi",
        "total": "5000.00",
        "amount_paid": "0.00",
        "amount_due": "5000.00",
        "due_date": "2026-01-20",
        "status": "OVERDUE"
    }
]
```

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

### 1. Doctor's Daily Invoice Routine

```
# Morning: Check what needs billing
GET /api/invoices/uninvoiced_appointments/

# For each uninvoiced appointment:
POST /api/invoices/from_appointment/
{
    "appointment_id": "uuid",
    "include_services": true
}

# Send to patient
POST /api/invoices/{id}/send/
```

### 2. Create Invoice After Appointment

```javascript
// Step 1: Complete the appointment
await api.post(`/appointments/${appointmentId}/complete/`);

// Step 2: Create invoice from appointment
const invoice = await api.post('/invoices/from_appointment/', {
    appointment_id: appointmentId,
    include_services: true,
    tax_rate: "0.00",
    due_days: 30,
    notes: "Thank you for your visit"
});

// Step 3: Add any extra items (tests, medications, etc.)
await api.post(`/invoices/${invoice.id}/add_item/`, {
    item_type: "CUSTOM",
    description: "Blood Test - CBC",
    unit_price: "1500.00",
    quantity: 1
});

// Step 4: Send to patient
await api.post(`/invoices/${invoice.id}/send/`, {
    send_notification: true
});
```

### 3. Invoice Multiple Services

```javascript
// Create invoice with multiple items
const invoice = await api.post('/invoices/', {
    patient_user: patientId,
    invoice_type: "SERVICE",
    items: [
        {
            item_type: "SERVICE",
            service_id: consultationServiceId,
            quantity: 1
        },
        {
            item_type: "SERVICE",
            service_id: ecgServiceId,
            quantity: 1
        },
        {
            item_type: "CUSTOM",
            description: "Home Visit Fee",
            unit_price: "1500.00",
            quantity: 1
        }
    ],
    tax_rate: "0.00",
    discount_type: "PERCENTAGE",
    discount_value: "10.00",
    discount_reason: "Returning patient"
});
```

### 4. Partial Payment Flow

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

### 5. Financial Dashboard Integration

```javascript
// Get financial summary for dashboard
const summary = await api.get('/invoices/financial_summary/', {
    params: { period: 'month' }
});

// Display on dashboard
console.log(`Total Revenue: ${summary.total_revenue} DZD`);
console.log(`Outstanding: ${summary.total_outstanding} DZD`);
console.log(`Uninvoiced Appointments: ${summary.uninvoiced_appointments}`);
console.log(`Overdue Invoices: ${summary.overdue_count}`);
```

### 6. React Dashboard Component

```jsx
import React, { useState, useEffect } from 'react';

const InvoiceDashboard = () => {
    const [summary, setSummary] = useState(null);
    const [uninvoiced, setUninvoiced] = useState([]);
    
    useEffect(() => {
        fetchDashboardData();
    }, []);
    
    const fetchDashboardData = async () => {
        const [summaryRes, uninvoicedRes] = await Promise.all([
            api.get('/invoices/financial_summary/?period=month'),
            api.get('/invoices/uninvoiced_appointments/')
        ]);
        setSummary(summaryRes.data);
        setUninvoiced(uninvoicedRes.data);
    };
    
    const createInvoiceFromAppointment = async (appointmentId) => {
        const response = await api.post('/invoices/from_appointment/', {
            appointment_id: appointmentId,
            include_services: true,
            due_days: 30
        });
        // Refresh data
        fetchDashboardData();
        return response.data;
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
            
            {/* Uninvoiced Appointments */}
            {uninvoiced.length > 0 && (
                <div className="uninvoiced-section">
                    <h3>📋 Appointments Needing Invoices</h3>
                    <ul>
                        {uninvoiced.map(apt => (
                            <li key={apt.id}>
                                <span>{apt.patient_display_name}</span>
                                <span>{apt.scheduled_date}</span>
                                <span>{apt.service?.title}</span>
                                <button onClick={() => createInvoiceFromAppointment(apt.id)}>
                                    Create Invoice
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};
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
| Financial summary | ✅ (own) | ✅ (all) |
| Uninvoiced appointments | ✅ (own) | ✅ (all) |
