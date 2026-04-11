# Nurse Mobile App - Complete Integration Guide

## Overview

This guide provides a comprehensive overview of all APIs, features, and workflows available for the Nurse Mobile Application. Use this as the starting point for mobile app development and integration.

---

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [API Documentation Index](#api-documentation-index)
3. [Authentication & Authorization](#authentication--authorization)
4. [Complete Nurse Workflow](#complete-nurse-workflow)
5. [Feature Overview](#feature-overview)
6. [Database Models](#database-models)
7. [Error Handling](#error-handling)
8. [Testing Checklist](#testing-checklist)
9. [Common Issues & Troubleshooting](#common-issues--troubleshooting)

---

## Getting Started

### Base URL

```
https://dzmedilink.duckdns.org/api/
```

### Authentication

All endpoints require token authentication:

```
Authorization: Token <your_auth_token>
```

### Quick Start Steps

1. **Register as Nurse Provider**
   - POST `/auth/provider/register/`
   - Provide required documents (license, entrepreneur card)
   - Account status becomes `PENDING`

2. **Wait for Admin Approval**
   - Admin reviews documents
   - Account status changes to `APPROVED`

3. **Set Up Your Profile**
   - Complete PATCH `/provider/profile/`
   - Add personal information
   - Upload profile image

4. **Add Services**
   - GET `/nurse-requests/nurse/my-services/` to see available services
   - POST `/nurse-requests/nurse/my-services/add/` to add services you offer

5. **Start Receiving Requests**
   - GET `/nurse-requests/nurse/available-requests/` to see patient requests
   - Accept requests or make counter-offers

---

## API Documentation Index

### Core Authentication & Profile

| Document | Purpose | Key Features |
|----------|---------|--------------|
| [AUTHENTICATION_API.md](./AUTHENTICATION_API.md) | Registration, login, profile management | Account creation, status tracking, profile updates |
| [Provider Profile View](../README.md#profile-endpoints) | Profile access endpoint | Get/update nurse professional information |

### Patient & Service Management

| Document | Purpose | Key Features |
|----------|---------|--------------|
| [APPOINTMENTS_API.md](./APPOINTMENTS_API.md) | Appointment tracking & management | Schedule management, patient relationship, location data |
| [NURSE_REQUESTS_API.md](./NURSE_REQUESTS_API.md) | On-demand service requests | Available requests, counter-offers, service completion |
| [MEDICAL_RECORDS_API.md](./MEDICAL_RECORDS_API.md) | Patient medical records access | View patient history, allergies, diagnoses, add notes |

### Financial Management

| Document | Purpose | Key Features |
|----------|---------|--------------|
| [INVOICES_API.md](./INVOICES_API.md) | Invoice creation & management | Create invoices, track payments, payment methods, statistics |

---

## Authentication & Authorization

### Registration Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. REGISTRATION                                         │
├─────────────────────────────────────────────────────────┤
│ POST /auth/provider/register/                           │
│ ├── Email                                               │
│ ├── Password                                            │
│ ├── Provider Type: "NURSE"                              │
│ └── Required Documents                                  │
│     ├── License Number                                  │
│     ├── Degree Document (PDF/Image)                     │
│     ├── Entrepreneur Card Front                         │
│     └── Entrepreneur Card Back                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. STATUS: PENDING (Admin Review)                       │
├─────────────────────────────────────────────────────────┤
│ GET /auth/account-status/  ← Check your status          │
│ Status: "PENDING"                                       │
│ Reason: "Under review"                                  │
└────────────────────┬────────────────────────────────────┘
                     │
            ┌────────┴────────┐
            │                 │
            ▼                 ▼
    ┌─────────────┐   ┌─────────────┐
    │   APPROVED  │   │   REFUSED   │
    │             │   │             │
    │ Can login & │   │ Cannot use  │
    │ use app     │   │ the app     │
    └─────────────┘   └─────────────┘
```

### Required Documents for Registration

All documents must be uploaded during registration:

**License Number** (Text)
- Example: `RN-2024-001234`
- Required for nurse identification

**Degree Document** (PDF or Image)
- Bachelor of Science in Nursing or equivalent
- File size: ≤ 5MB
- Formats: PDF, JPG, PNG

**Entrepreneur Card Front** (Image)
- Official government-issued entrepreneur card
- File size: ≤ 3MB
- Format: JPG, PNG, WebP

**Entrepreneur Card Back** (Image)
- Same card, back side
- File size: ≤ 3MB
- Format: JPG, PNG, WebP

### Account Status States

| Status | Meaning | Can Access App |
|--------|---------|----------------|
| `PENDING` | Documents under review by admin | ❌ No |
| `APPROVED` | Verified and active | ✅ Yes |
| `REFUSED` | Application denied | ❌ No |
| `SUSPENDED` | Temporarily disabled (compliance issue) | ❌ No |

### Accessing Your Status

```http
GET /auth/account-status/
Authorization: Token your_token
```

Response:
```json
{
  "status": "APPROVED",
  "verified_at": "2026-02-15T10:00:00Z",
  "profile_completion": 85
}
```

---

## Complete Nurse Workflow

### 1. During Appointment Booking

When a patient books an appointment with you or you confirm an appointment:

```
Patient Books Appointment
        │
        ▼
Payment Processed (if applicable)
        │
        ▼
Appointment Created in System
        │
        ▼
✅ Automatic: Patient Record Created
✅ Automatic: Provider Access Granted (FULL)
✅ Automatic: You can access patient medical records
```

**What You Get Access To:**
- Patient's complete medical history
- Allergies (⚠️ CRITICAL)
- Current prescriptions
- Previous diagnoses
- Lab results
- Vaccination records
- Notes from other providers

### 2. Before Providing Service

```
GET /api/patients/{patient_id}/
    │
    ├─ Name, age, contact info
    ├─ Medical history
    └─ Emergency contact

GET /api/medical-records/records/patient/{patient_id}/?record_type=ALLERGY
    │
    └─ All known allergies and severity

GET /api/medical-records/records/patient/{patient_id}/?record_type=DIAGNOSIS
    │
    └─ Active medical conditions

POST /api/appointments/{id}/start/
    │
    └─ Mark appointment as in-progress
```

### 3. After Providing Service

```
POST /api/appointments/{id}/complete/
    │
    ├─ Mark appointment as completed
    └─ Automatic: Invoice created (if applicable)

POST /api/medical-records/records/{record_id}/notes/
    │
    └─ Add care notes, observations, patient response

POST /api/invoices/
    │
    ├─ Manual invoice creation (for on-demand services)
    └─ Add items, set prices, send to patient

GET /api/invoices/{id}/
    │
    └─ Track invoice status and payments
```

### 4. On-Demand Service Request Flow

```
┌─────────────────────────────────────┐
│ ONE-TIME SETUP                      │
├─────────────────────────────────────┤
│ 1. Get available services           │
│    GET /nurse-requests/nurse/       │
│        my-services/                 │
│                                     │
│ 2. Add services you offer           │
│    POST /nurse-requests/nurse/      │
│        my-services/add/             │
│                                     │
│ 3. Set custom prices (optional)     │
│    PATCH /nurse-requests/nurse/     │
│        my-services/{id}/            │
└────────────────┬────────────────────┘
                 │
                 ▼
    ┌───────────────────────────┐
    │ ACTIVE LISTENING MODE     │
    │ (Continuously running)    │
    │                           │
    │ GET /nurse-requests/nurse/│
    │  available-requests/      │
    │                           │
    │ Check periodically for:   │
    │ - New requests from       │
    │   patients in your area   │
    │ - Requests for your       │
    │   services at your price  │
    └────────┬──────────────────┘
             │
             ▼
    ┌───────────────────────────┐
    │ NEW REQUEST ARRIVES!      │
    │                           │
    │ Details provided:         │
    │ - Patient name & location │
    │ - Requested service       │
    │ - Offered price           │
    │ - Distance from you       │
    └────────┬──────────────────┘
             │
  ┌──────────┼──────────┐
  │          │          │
  ▼          ▼          ▼
[ACCEPT]  [COUNTER-  [REJECT]
          OFFER]
  │          │          │
  ▼          ▼          ▼
Await      Await     Request
Patient    Patient   Done
Response   Response

✅ Accepted → Appointment created
              Invoice ready
              Medical records available
              Go to patient location
```

---

## Feature Overview

### Account Management

**Profile Setup**
- Complete personal information
- Upload profile image
- Set availability status
- Add professional certifications
- List specializations

**Document Management**
- Uplo professional credentials
- License verification
- Entrepreneur card storage
- Certificate management

### Appointment Management

**Viewing Appointments**
- List active appointments
- See appointment details
- View patient contact info
- Check appointment location

**Managing Appointments**
- Confirm appointments
- Start appointments
- Complete appointments
- Add notes after completion

### On-Demand Services

**Service Management**
- Browse available nursing services
- Add services to your profile
- Set custom prices
- Update availability

**Handling Requests**
- See available patient requests
- View request details
- Accept requests
- Make counter-offers
- Reject requests
- Track your offers

### Patient Care

**Accessing Patient Information**
- View patient profile
- Access medical records
- Check allergies and medications
- See appointment history

**Providing Care**
- Add observations and notes
- Document care provided
- Track patient progress
- Communicate issues

### Financial Management

**Invoice Management**
- Create invoices for services
- Add multiple items
- Set payment methods
- Track invoice status
- Send invoices to patients
- Record payments
- View payment history

**Income Tracking**
- View completed services
- Track earnings
- Generate income reports
- Monitor payment status

---

## Database Models

### Core Models Involved

```
┌─────────────┐
│    User     │◄──────┐
├─────────────┤       │
│ email       │       │
│ password    │       │
│ role        │       │
│ is_active   │       │
└─────────────┘       │
       △              │
       │              │
       │         ┌────────────┐
       │         │ Provider   │
       │         ├────────────┤
       │         │ status     │
       │         │ type       │
       │         └────┬───────┘
       └──────────────┘ │
                        │
                        ▼
                  ┌───────────┐
                  │   Nurse   │
                  ├───────────┤
                  │ first_name│
                  │ last_name │
                  │ license_# │
                  │ verified  │
                  └───────────┘

┌──────────────┐
│   Patient    │
├──────────────┤
│ patient_id   │
│ name         │
│ contact_info │
│ medical_info │
└──────────────┘
       △
       │
       │
┌──────┴───────────┐
│ Appointment      │
├──────────────────┤
│ nurse_id         │
│ patient_id       │
│ scheduled_time   │
│ status           │
│ location         │
└──────────────────┘

┌──────────────────┐
│ MedicalRecord    │
├──────────────────┤
│ patient_id       │
│ record_type      │
│ title            │
│ description      │
│ created_by       │
│ record_date      │
└──────────────────┘
       △
       │ (1-1)
   ┌───┴────┐
   │         │
[Prescription] [Allergy]

┌──────────────┐
│   Invoice    │
├──────────────┤
│ provider_id  │
│ patient_id   │
│ total_amount │
│ status       │
│ due_date     │
└──────────────┘
```

---

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | When It Occurs |
|--------|---------|----------------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource successfully created |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Missing or invalid token |
| `403` | Forbidden | Insufficient permissions |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Request conflicts with existing data |
| `429` | Rate Limited | Too many requests |
| `500` | Server Error | Backend error |

### Error Response Format

```json
{
  "error": "Description of what went wrong",
  "details": {
    "field_name": ["Error message for this field"]
  }
}
```

### Common Error Scenarios

**Account Not Approved**
```json
{
  "error": "Your account is not approved yet.",
  "status": "PENDING"
}
```

**Unauthorized Access**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Patient Record Not Found**
```json
{
  "error": "Patient not found."
}
```

**Allergy Information Critical**

Always check for allergies before providing care:

```http
GET /api/medical-records/records/patient/{patient_id}/?record_type=ALLERGY
```

If allergies exist, ensure your care plan accounts for:
- Medication allergies
- Contact allergies (latex, disinfectants)
- Food allergies (if providing nutrition-related care)

---

## Testing Checklist

### Pre-Launch Testing

#### Authentication & Registration
- [ ] Can register as nurse provider
- [ ] Receives email confirmation
- [ ] Status shows PENDING
- [ ] Admin approval changes status to APPROVED
- [ ] Can login after approval
- [ ] Token authentication working
- [ ] Session management working

#### Profile Management
- [ ] Can view my profile
- [ ] Can update profile information
- [ ] Can upload profile image
- [ ] Can update availability status
- [ ] Can add professional certifications

#### Appointment Management
- [ ] Can view list of appointments
- [ ] Can see appointment details
- [ ] Can start appointment
- [ ] Can complete appointment
- [ ] Can add notes after appointment
- [ ] Appointment status updates correctly

#### Medical Records Access
- [ ] Can view list of my patients
- [ ] Can view patient details
- [ ] Can list all patient medical records
- [ ] Can view single medical record with full details
- [ ] Can see allergies for patient
- [ ] Can see prescriptions for patient
- [ ] Can add notes to medical record
- [ ] Medical records are correctly filtered by type

#### On-Demand Services
- [ ] Can view available nursing services
- [ ] Can add service to my profile
- [ ] Can update service availability
- [ ] Can view available requests
- [ ] Can accept request
- [ ] Can make counter-offer
- [ ] Can reject request
- [ ] Can view my submitted offers

#### Invoice Management
- [ ] Can create invoice
- [ ] Can add items to invoice
- [ ] Can set payment method
- [ ] Can send invoice to patient
- [ ] Can record payment
- [ ] Can view invoice status
- [ ] Can generate invoice PDF

#### Error Handling
- [ ] Proper error messages for all failures
- [ ] Correct HTTP status codes
- [ ] Helpful error descriptions
- [ ] No sensitive data in error responses

#### Performance
- [ ] Medical records load quickly
- [ ] Patient list loads efficiently
- [ ] Pagination working correctly
- [ ] Search functionality working
- [ ] Filtering working correctly

#### Security
- [ ] Cannot access other nurse's data
- [ ] Cannot access unauthorized patient records
- [ ] API validates all inputs
- [ ] Token expiration working
- [ ] HTTPS enforced

---

## Common Issues & Troubleshooting

### "Account Not Approved" Error

**Problem:** Cannot access app features

**Cause:** Your account status is still `PENDING`

**Solution:**
1. Check account status: `GET /auth/account-status/`
2. Ensure all documents were submitted during registration
3. Wait for admin approval (usually 1-2 business days)
4. Contact support if approval takes longer

### "Patient Not Found" Error

**Problem:** Cannot access patient's medical records

**Cause:** Invalid patient ID or no access to this patient

**Solution:**
1. Verify patient ID from your appointment or access list
2. Ensure appointment was confirmed (automatic access granting)
3. Check provider access list: `GET /medical-records/provider-access/my-patients/`
4. Contact admin if access should exist but doesn't

### "Cannot Add Service" Error

**Problem:** Service addition fails

**Cause:** Service doesn't exist or invalid data

**Solution:**
1. Get available services: `GET /nurse-requests/nurse/my-services/`
2. Verify service ID is correct
3. Check that all required fields are provided
4. Ensure service availability is properly set

### "Token Expired" Error

**Problem:** Requests failing with 401 Unauthorized

**Cause:** Authentication token has expired

**Solution:**
1. Re-login: `POST /auth/login/`
2. Obtain new token
3. Update token in app
4. Retry request

### Slow Medical Records Loading

**Problem:** Medical records endpoint responding slowly

**Cause:** Large volume of data or database query issues

**Solution:**
1. Use pagination: `?page=1&page_size=10`
2. Filter by record type: `?record_type=ALLERGY`
3. Use search filter for specific records
4. Avoid fetching all records at once

### Invoice Payment Tracking

**Problem:** Cannot track payment status

**Cause:** Payment method or status not set correctly

**Solution:**
1. Create invoice with correct payment method
2. Send invoice to patient
3. Record payment when received: `POST /invoices/{id}/record-payment/`
4. Check invoice status continuously: `GET /invoices/{id}/`

---

## Integration Checklist Summary

### Backend Ready
- [x] Nurse models created and tested
- [x] Authentication system operational
- [x] Medical records access control implemented
- [x] Appointment appointment system working
- [x] On-demand service request system ready
- [x] Invoice system operational
- [x] Provider access management configured

### Frontend Development
- [ ] Implement authentication flow
- [ ] Build profile setup screens
- [ ] Create appointment management UI
- [ ] Build medical records viewer
- [ ] Create on-demand services interface
- [ ] Build invoice management screens
- [ ] Implement error handling

### Testing
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Load testing completed
- [ ] Security audit completed

### Deployment
- [ ] API documentation production-ready
- [ ] Database backups configured
- [ ] Monitoring and logging setup
- [ ] Error tracking configured
- [ ] Performance optimization complete

---

## Support & Resources

### Documentation Files

| File | Purpose |
|------|---------|
| [AUTHENTICATION_API.md](./AUTHENTICATION_API.md) | User registration and login ]]|
| [APPOINTMENTS_API.md](./APPOINTMENTS_API.md) | Appointment scheduling and management |
| [NURSE_REQUESTS_API.md](./NURSE_REQUESTS_API.md) | On-demand service requests |
| [MEDICAL_RECORDS_API.md](./MEDICAL_RECORDS_API.md) | Patient medical records access |
| [INVOICES_API.md](./INVOICES_API.md) | Invoice and payment management |

### API Endpoints Summary

**Auth**
- `POST /auth/provider/register/` - Register as nurse
- `POST /auth/login/` - Login
- `GET /auth/account-status/` - Check approval status

**Profile**
- `GET /provider/profile/` - View my profile
- `PUT/PATCH /provider/profile/` - Update my profile

**Appointments**
- `GET /appointments/` - List my appointments
- `GET /appointments/{id}/` - View appointment details
- `POST /appointments/{id}/start/` - Start appointment
- `POST /appointments/{id}/complete/` - Complete appointment

**Medical Records**
- `GET /medical-records/provider-access/my-patients/` - My patients list
- `GET /medical-records/records/patient/{patient_id}/` - Patient medical records
- `GET /medical-records/records/{id}/` - View single record details
- `POST /medical-records/records/{id}/notes/` - Add note to record

**On-Demand Services**
- `GET /nurse-requests/nurse/my-services/` - My services
- `POST /nurse-requests/nurse/my-services/add/` - Add service
- `GET /nurse-requests/nurse/available-requests/` - Available requests
- `POST /nurse-requests/nurse/available-requests/{id}/accept/` - Accept request

**Invoices**
- `GET /invoices/` - My invoices
- `POST /invoices/` - Create invoice
- `GET /invoices/{id}/` - View invoice
- `POST /invoices/{id}/record-payment/` - Record payment

---

## Contact & Support

For issues or questions about the API:

1. Check the relevant API documentation file
2. Review the troubleshooting section above
3. Check the error response message for hints
4. Contact the development team for support

---

**Last Updated:** 2026-04-08
**API Version:** 1.0
**Status:** Production Ready ✅
