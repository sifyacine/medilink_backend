# Invoices API Documentation

## Overview

The Invoices system provides comprehensive billing and payment management for the Medilink platform. It supports:

- **Service Invoices**: For healthcare services (appointments, consultations)
- **Product Invoices**: For products sold (medications, medical supplies)
- **Mixed Invoices**: Combination of services and products
- **Custom Invoices**: Manual entries for any billable item

## Features

### Invoice Management
- Create invoices from appointments, nurse requests, or manually
- Automatic invoice number generation (INV-YYYYMMDD-XXXXXXXX)
- Multi-currency support (DZD, USD, EUR)
- Tax and discount calculations
- Due date tracking with overdue detection
- Multilingual notes support (English, Arabic, French)

### Payment Tracking
- Multiple payment methods (Cash, Card, Bank Transfer, Mobile Payment, Insurance)
- Partial payment support
- Payment verification workflow
- Refund management
- Payment history

### Notifications
- Invoice sent notifications
- Payment received confirmations
- Overdue reminders

## API Endpoints

### Invoices

#### List Invoices
```
GET /api/invoices/
```

Query parameters:
- `status`: Filter by status (DRAFT, SENT, PAID, OVERDUE, etc.)
- `invoice_type`: Filter by type (SERVICE, PRODUCT, MIXED, CUSTOM)
- `start_date`: Filter by issue date (from)
- `end_date`: Filter by issue date (to)

Response:
```json
{
  "count": 25,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "invoice_number": "INV-20240115-A1B2C3D4",
      "provider_name": "Dr. Ahmed Benali",
      "patient_display_name": "Mohammed Khalil",
      "invoice_type": "SERVICE",
      "status": "SENT",
      "status_display": "Sent",
      "issue_date": "2024-01-15",
      "due_date": "2024-02-14",
      "currency": "DZD",
      "total": "5000.00",
      "amount_paid": "0.00",
      "amount_due": "5000.00",
      "items_count": 2,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Create Invoice
```
POST /api/invoices/
```

Request body:
```json
{
  "provider": "provider-uuid",
  "patient_user": "patient-uuid",
  "invoice_type": "SERVICE",
  "issue_date": "2024-01-15",
  "due_date": "2024-02-14",
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

#### Get Invoice Details
```
GET /api/invoices/{id}/
```

#### Update Invoice (Draft only)
```
PATCH /api/invoices/{id}/
```

#### Delete Invoice (Draft only)
```
DELETE /api/invoices/{id}/
```

### Invoice Actions

#### Send Invoice
```
POST /api/invoices/{id}/send/
```

Sends the invoice to the patient and changes status from DRAFT to SENT.

Request body:
```json
{
  "send_notification": true,
  "message": "Please review your invoice"
}
```

#### Cancel Invoice
```
POST /api/invoices/{id}/cancel/
```

Request body:
```json
{
  "reason": "Duplicate invoice"
}
```

#### Mark as Viewed
```
POST /api/invoices/{id}/mark_viewed/
```

Called when patient views the invoice.

#### Add Item
```
POST /api/invoices/{id}/add_item/
```

Add an item to a draft invoice.

Request body:
```json
{
  "item_type": "SERVICE",
  "service_id": "service-uuid",
  "quantity": 1,
  "notes": "Additional service"
}
```

#### Remove Item
```
POST /api/invoices/{id}/remove_item/
```

Request body:
```json
{
  "item_id": "item-uuid"
}
```

#### Record Payment
```
POST /api/invoices/{id}/record_payment/
```

Request body:
```json
{
  "amount": "2500.00",
  "payment_method": "CARD",
  "reference_number": "TXN123456",
  "notes": "First installment"
}
```

#### Get Activity Log
```
GET /api/invoices/{id}/activities/
```

Returns audit trail for the invoice.

### Special Endpoints

#### Create from Appointment
```
POST /api/invoices/from_appointment/
```

Create an invoice from a completed appointment.

Request body:
```json
{
  "appointment_id": "appointment-uuid",
  "include_services": true,
  "tax_rate": "19.00",
  "due_days": 30,
  "notes": "Invoice for consultation"
}
```

#### Get Statistics
```
GET /api/invoices/statistics/
```

Query parameters:
- `start_date`: Optional date filter
- `end_date`: Optional date filter

Response:
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

#### Get Overdue Invoices
```
GET /api/invoices/overdue/
```

Returns list of overdue invoices and marks newly overdue ones.

### Payments

#### List Payments
```
GET /api/invoices/payments/
```

#### Create Payment
```
POST /api/invoices/payments/
```

#### Verify Payment
```
POST /api/invoices/payments/{id}/verify/
```

Request body:
```json
{
  "is_verified": true,
  "notes": "Verified via bank statement"
}
```

#### Refund Payment
```
POST /api/invoices/payments/{id}/refund/
```

Request body:
```json
{
  "amount": "1000.00",
  "reason": "Service not provided"
}
```

### Patient Invoices

#### My Invoices
```
GET /api/invoices/my/
```

Simplified endpoint for patients to view their invoices.

## Invoice Status Flow

```
DRAFT → SENT → VIEWED → PAID
           ↓       ↓
        OVERDUE  PARTIALLY_PAID → PAID
           ↓
      CANCELLED

PAID → PARTIALLY_REFUNDED → REFUNDED
```

## Invoice Types

| Type | Description |
|------|-------------|
| SERVICE | Healthcare services (appointments, consultations) |
| PRODUCT | Products sold (medications, supplies) |
| MIXED | Combination of services and products |
| CUSTOM | Manual/custom items |

## Payment Methods

| Method | Description |
|--------|-------------|
| CASH | Cash payment |
| CARD | Credit/Debit card |
| BANK_TRANSFER | Bank wire transfer |
| MOBILE_PAYMENT | CCP, BaridiMob, etc. |
| INSURANCE | Insurance claim |
| CHEQUE | Cheque payment |
| OTHER | Other methods |

## Item Types

| Type | Description | Source |
|------|-------------|--------|
| SERVICE | Catalog service | services.Service |
| CUSTOM_SERVICE | Provider's custom service | services.ProviderCustomService |
| PRODUCT | Product (future) | - |
| MEDICATION | Prescription medication | prescriptions.PrescriptionItem |
| CUSTOM | Manual entry | None |

## Configuration

Add to Django settings:

```python
# Auto-create invoice when appointment is completed
MEDILINK_AUTO_INVOICE_APPOINTMENTS = False

# Auto-create invoice when nurse request is completed
MEDILINK_AUTO_INVOICE_NURSE_REQUESTS = False

# Auto-send invoices immediately after creation
MEDILINK_AUTO_SEND_INVOICES = False
```

## Permissions

| Action | Patient | Provider | Admin |
|--------|---------|----------|-------|
| List own invoices | ✅ | ✅ | ✅ |
| List all invoices | ❌ | ❌ | ✅ |
| Create invoice | ❌ | ✅ | ✅ |
| Update invoice | ❌ | ✅ (own) | ✅ |
| Delete invoice | ❌ | ✅ (draft) | ✅ |
| Send invoice | ❌ | ✅ (own) | ✅ |
| View invoice | ✅ (own) | ✅ (own) | ✅ |
| Record payment | ❌ | ✅ (own) | ✅ |
| Mark viewed | ✅ (own) | ❌ | ✅ |

## Example Workflows

### Provider Creates Invoice After Appointment

1. Appointment is completed
2. Provider calls `POST /api/invoices/from_appointment/`
3. System creates invoice with services from appointment
4. Provider can modify items if needed
5. Provider calls `POST /api/invoices/{id}/send/`
6. Patient receives notification
7. Patient views invoice (status changes to VIEWED)
8. Provider records payment when received
9. Invoice marked as PAID when fully paid

### Automatic Invoice Creation

Enable in settings:
```python
MEDILINK_AUTO_INVOICE_APPOINTMENTS = True
MEDILINK_AUTO_SEND_INVOICES = True
```

When appointment is completed:
1. Signal triggers invoice creation
2. Invoice automatically sent to patient
3. Provider sees invoice in dashboard

### Partial Payment

1. Invoice total: 10,000 DZD
2. First payment: 5,000 DZD
   - Status: PARTIALLY_PAID
   - Amount due: 5,000 DZD
3. Second payment: 5,000 DZD
   - Status: PAID
   - Amount due: 0 DZD

### Refund Flow

1. Payment of 10,000 DZD recorded
2. Provider issues partial refund of 3,000 DZD
   - Status: PARTIALLY_REFUNDED
3. Or provider issues full refund
   - Status: REFUNDED
