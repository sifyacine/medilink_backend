# Nurse Mobile App - Medical Records API

## Overview

This documentation covers the **Medical Records API** for the Nurse Mobile Application. Nurses can access and view patient medical records for patients they are authorized to treat. This enables nurses to make informed decisions about care and understand patient history before providing services.

**Key Principles:**
- 🔐 **Access Control**: Nurses can ONLY access records of patients they have been granted access to
- 📋 **Patient History**: View complete medical history, allergies, prescriptions, and previous care notes
- 📝 **Documentation**: Add nurse observations and care notes to patient records
- 📊 **Care Coordination**: See patient context before starting services

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [How Access Is Granted](#how-access-is-granted)
4. [Patient Medical Records](#patient-medical-records)
   - [List My Patients](#list-my-patients)
   - [Get Patient Medical Records](#get-patient-medical-records)
   - [View Single Medical Record](#view-single-medical-record)
5. [Medical Record Details](#medical-record-details)
   - [Record Types](#record-types)
   - [Important Fields](#important-fields)
6. [Patient Information](#patient-information)
   - [View Patient Details](#view-patient-details)
7. [Adding Care Notes](#adding-care-notes)
8. [Provider Access Management](#provider-access-management)
9. [Common Workflows](#common-workflows)
10. [Error Handling](#error-handling)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

All medical records endpoints are prefixed with `/api/medical-records/`

---

## Authentication

All medical records endpoints require authentication. Include your token in every request:

```
Authorization: Token <your_token_here>
```

**Important:** Your nurse provider account must be `APPROVED` to access medical records.

---

## How Access Is Granted

### Automatic Access After Appointment

When you confirm an appointment with a patient, you are **automatically granted FULL access** to their medical records:

```
┌─────────────────────────────────────────────────┐
│      APPOINTMENT CONFIRMED OR RESCHEDULED       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Patient Record Created (if needed)             │
│  ProviderAccess Record Created                  │
│  Access Type: FULL                              │
│  Status: ACTIVE                                 │
└─────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  You can now:                                   │
│  ✓ View patient medical records                 │
│  ✓ Add care notes and observations              │
│  ✓ See patient complete medical history         │
│  ✓ Check allergies and medications              │
└─────────────────────────────────────────────────┘
```

### Manual Access (Admin/Patient Granted)

Patients or admins can also grant you access to their records. Use the [Provider Access Endpoints](#provider-access-management) to check your access list.

---

## Patient Medical Records

### List My Patients

Get list of all patients you have active access to and their latest medical records.

**Endpoint:**
```http
GET /api/medical-records/provider-access/my-patients/
Authorization: Token your_auth_token
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `is_active` | boolean | Filter by active access (default: true) |
| `access_type` | string | Filter by access type: `FULL`, `READ_ONLY`, `LIMITED` |
| `ordering` | string | Sort by field: `granted_at`, `expires_at` |

**Response:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient": {
        "id": "uuid-1234",
        "email": "ahmed@example.com",
        "first_name": "Ahmed",
        "last_name": "Benali",
        "phone_number": "+213555123456"
      },
      "access_type": "FULL",
      "is_active": true,
      "granted_at": "2026-02-15T10:30:00Z",
      "reason": "Appointment confirmed for home care",
      "expires_at": null
    }
  ]
}
```

---

### Get Patient Medical Records

Get all medical records for a specific patient.

**Endpoint:**
```http
GET /api/medical-records/records/patient/{patient_id}/
Authorization: Token your_auth_token
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `patient_id` | UUID | Patient ID from access list |

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `record_type` | string | Filter by type: `DIAGNOSIS`, `PRESCRIPTION`, `ALLERGY`, `LAB_RESULT`, `IMAGING`, `PROCEDURE`, `NOTE`, `VACCINATION`, `OTHER` |
| `is_active` | boolean | Filter active records (default: true) |
| `requires_followup` | boolean | Filter records needing follow-up |
| `search` | string | Search by title, description, diagnosis code |
| `ordering` | string | Sort by: `record_date`, `created_at`, `updated_at` Default: `-record_date` |

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 101,
      "title": "Blood Pressure Check",
      "record_type": "NOTE",
      "record_date": "2026-02-14",
      "description": "BP: 120/80 mmHg - Normal",
      "diagnosis_code": "",
      "created_by": {
        "id": "doctor-uuid",
        "email": "doctor@clinic.com",
        "first_name": "Dr. Tariq"
      },
      "is_active": true,
      "requires_followup": false,
      "created_at": "2026-02-14T09:00:00Z",
      "updated_at": "2026-02-14T09:00:00Z"
    },
    {
      "id": 102,
      "title": "Diabetes Diagnosis",
      "record_type": "DIAGNOSIS",
      "record_date": "2026-01-20",
      "description": "Type 2 Diabetes Mellitus",
      "diagnosis_code": "E11",
      "created_by": {
        "id": "doctor-uuid",
        "email": "doctor@clinic.com",
        "first_name": "Dr. Tariq"
      },
      "is_active": true,
      "requires_followup": true,
      "followup_date": "2026-03-20",
      "created_at": "2026-01-20T14:30:00Z"
    },
    {
      "id": 103,
      "title": "Penicillin Allergy",
      "record_type": "ALLERGY",
      "record_date": "2026-01-15",
      "description": "Allergic to Penicillin",
      "created_by": null,
      "is_active": true,
      "created_at": "2026-01-15T11:00:00Z"
    }
  ]
}
```

---

### View Single Medical Record

Get complete details of a single medical record including attachments and notes.

**Endpoint:**
```http
GET /api/medical-records/records/{record_id}/
Authorization: Token your_auth_token
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `record_id` | integer | Medical record ID |

**Response:**
```json
{
  "id": 102,
  "title": "Diabetes Diagnosis",
  "record_type": "DIAGNOSIS",
  "record_date": "2026-01-20",
  "description": "Type 2 Diabetes Mellitus diagnosed after fasting glucose test",
  "diagnosis_code": "E11",
  "symptoms": "Increased thirst, frequent urination, fatigue",
  "created_by": {
    "id": "doctor-uuid",
    "email": "doctor@clinic.com",
    "first_name": "Dr. Tariq"
  },
  "updated_by": null,
  "is_active": true,
  "is_confidential": false,
  "requires_followup": true,
  "followup_date": "2026-03-20",
  "created_at": "2026-01-20T14:30:00Z",
  "updated_at": "2026-01-20T14:30:00Z",
  
  "prescription": {
    "medication_name": "Metformin",
    "dosage": "500mg",
    "frequency": "Twice daily",
    "duration": "Ongoing",
    "instructions": "Take with meals to reduce stomach upset",
    "quantity": 60,
    "refills": 3
  },
  
  "attachments": [
    {
      "id": 1,
      "file_name": "lab_results.pdf",
      "file_type": "application/pdf",
      "file_size": 245678,
      "description": "Fasting glucose test results",
      "file": "https://dzmedilink.duckdns.org/media/medical_records/attachments/2026/01/20/lab_results.pdf",
      "uploaded_at": "2026-01-20T14:30:00Z"
    }
  ],
  
  "notes": [
    {
      "id": 1,
      "note_type": "PROVIDER",
      "content": "Patient education provided on diet and exercise",
      "created_by": {
        "email": "doctor@clinic.com",
        "first_name": "Dr. Tariq"
      },
      "created_at": "2026-01-20T15:00:00Z",
      "is_locked": true
    },
    {
      "id": 2,
      "note_type": "PATIENT",
      "content": "Understanding the condition better after discussion",
      "created_by": {
        "email": "ahmed@example.com",
        "first_name": "Ahmed"
      },
      "created_at": "2026-01-21T10:00:00Z"
    }
  ]
}
```

---

## Medical Record Details

### Record Types

When viewing medical records, you'll encounter different types:

| Type | Use Case | Key Information |
|------|----------|-----------------|
| `DIAGNOSIS` | Medical condition identified | Has diagnosis_code (ICD-10) |
| `PRESCRIPTION` | Medications prescribed | Links to Prescription object |
| `ALLERGY` | Known allergies/intolerances | Has severity (MILD, MODERATE, SEVERE, LIFE_THREATENING) |
| `LAB_RESULT` | Lab test results | Usually has attachments |
| `IMAGING` | Imaging studies (X-ray, CT, etc.) | Usually has attachments |
| `PROCEDURE` | Medical procedures performed | Detailed description provided |
| `NOTE` | General clinical notes | Created by provider or patient |
| `VACCINATION` | Vaccination records | Date of administration |
| `OTHER` | Miscellaneous | Free-form content |

### Important Fields

**Before Starting a Service:**

1. **Allergies** - ⚠️ CRITICAL - Check for any allergies, especially:
   - Medication allergies
   - Chemical allergies (disinfectants, etc.)
   - Latex allergies (if using gloves)
   - Food allergies (if providing nutrition)

2. **Prescriptions** - Understand current medications:
   - Dosage and frequency
   - Potential interactions
   - Contraindications with your care

3. **Recent Diagnoses** - Context on patient's health status:
   - Active conditions
   - Chronic diseases
   - Recent infections

4. **Follow-up Requirements** - Flag if care needed:
   - Records with `requires_followup: true`
   - Note the `followup_date`
   - Plan accordingly

---

## Patient Information

### View Patient Details

Get complete patient information and their linked medical records.

**Endpoint:**
```http
GET /api/patients/{patient_id}/
Authorization: Token your_auth_token
```

**Response:**
```json
{
  "patient_unique_id": "PAT-2026-001234",
  "linked_user": "uuid-1234",
  "first_name": "Ahmed",
  "last_name": "Benali",
  "email": "ahmed@example.com",
  "phone_number": "+213555123456",
  "date_of_birth": "1985-03-15",
  "gender": "MALE",
  "blood_type": "O+",
  "address": "123 Main Street",
  "city": "Algiers",
  "postal_code": "16000",
  "height_cm": 180,
  "weight_kg": 75,
  "emergency_contact_name": "Fatima Benali",
  "emergency_contact_phone": "+213555123457",
  "medical_notes": "Diabetic patient, requires regular monitoring",
  "created_at": "2026-02-15T10:30:00Z",
  "updated_at": "2026-02-15T10:30:00Z"
}
```

---

## Adding Care Notes

### Add Note to Medical Record

After providing care or making observations, add notes to the patient's medical record.

**Endpoint:**
```http
POST /api/medical-records/records/{record_id}/notes/
Authorization: Token your_auth_token
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Wound dressing changed, no signs of infection. Patient reports pain level 3/10. Applied antibiotic ointment and sterile bandage."
}
```

**Response:**
```json
{
  "id": 5,
  "note_type": "PROVIDER",
  "content": "Wound dressing changed, no signs of infection. Patient reports pain level 3/10. Applied antibiotic ointment and sterile bandage.",
  "created_by": {
    "email": "nurse@medilink.com",
    "first_name": "Fatima"
  },
  "created_at": "2026-02-15T14:30:00Z",
  "is_locked": true
}
```

**Important:** 
- Notes you create are automatically marked as `PROVIDER` notes
- Provider notes are automatically locked to prevent patient modification
- Your notes become part of the permanent medical record

---

## Provider Access Management

### Check Your Access Status

View all patients you have access to and your access permissions.

**Endpoint:**
```http
GET /api/medical-records/provider-access/my-patients/
Authorization: Token your_auth_token
```

**Access Types Explained:**

| Access Type | Can Do |
|-------------|--------|
| `FULL` | ✅ View all records, add notes, see all details |
| `READ_ONLY` | 🔍 View all records, cannot add notes (rare) |
| `LIMITED` | 📋 Limited to specific record types (rare) |

### View Your Active Accesses

**Endpoint:**
```http
GET /api/medical-records/provider-access/
Authorization: Token your_auth_token
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "patient": {
        "id": "uuid-1234",
        "email": "ahmed@example.com",
        "first_name": "Ahmed",
        "last_name": "Benali"
      },
      "access_type": "FULL",
      "is_active": true,
      "granted_at": "2026-02-15T10:30:00Z",
      "expires_at": null,
      "reason": "Appointment confirmed - Home care for wound dressing"
    }
  ]
}
```

---

## Common Workflows

### Before Starting a Home Care Service

```
1. Get patient details
   GET /api/patients/{patient_id}/

2. Review patient medical records
   GET /api/medical-records/records/patient/{patient_id}/?record_type=ALLERGY,DIAGNOSIS,PRESCRIPTION

3. Check for specific critical information:
   - Allergies to your supplies/medications
   - Contraindications for your service
   - Recent complications or infections

4. Review appointment details
   GET /api/appointments/{appointment_id}/

5. Start the appointment
   POST /api/appointments/{appointment_id}/start/
```

### After Completing a Service

```
1. Mark appointment as complete
   POST /api/appointments/{appointment_id}/complete/

2. Create invoice (if applicable)
   POST /api/invoices/

3. Add care notes to patient record
   POST /api/medical-records/records/{record_id}/notes/
   
   Include:
   - Service performed
   - Patient response/observations
   - Any complications or concerns
   - Follow-up recommendations
```

### Checking Patient History Before Providing Service

```
1. List all patient records
   GET /api/medical-records/records/patient/{patient_id}/

2. Filter by relevant types
   GET /api/medical-records/records/patient/{patient_id}/?record_type=DIAGNOSIS,ALLERGY

3. For each critical record, get full details
   GET /api/medical-records/records/{record_id}/
   
4. Check attachments and notes
   - Lab results
   - Previous provider notes
   - Patient observations
```

---

## Error Handling

### Access Denied

**Error Code:** 403 FORBIDDEN

**When:** You don't have access to view this patient's records

**Response:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Solution:** 
- Confirm the appointment was successfully confirmed
- Check your access list: `GET /api/medical-records/provider-access/my-patients/`
- Contact admin if access was supposed to be granted

### Patient Not Found

**Error Code:** 404 NOT FOUND

**Response:**
```json
{
  "error": "Patient not found."
}
```

**Solution:** Verify the patient ID is correct

### Medical Record Not Found

**Error Code:** 404 NOT FOUND

**Response:**
```json
{
  "error": "Medical record not found."
}
```

**Solution:** The record ID may be incorrect or the record may have been deleted

### Unauthorized (Invalid Token)

**Error Code:** 401 UNAUTHORIZED

**Response:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Solution:** 
- Check your token is valid
- Re-login if token expired
- Include `Authorization: Token <token>` in header

### Account Not Approved

**Error Code:** 403 FORBIDDEN

**Response:**
```json
{
  "error": "Your account is not approved yet."
}
```

**Solution:** Wait for admin approval of your nurse registration

---

## Integration Checklist

Before connecting the nurse app to use medical records:

- [ ] Nurse account is created and `APPROVED`
- [ ] Token authentication is working
- [ ] Can view list of accessible patients
- [ ] Can retrieve patient medical records
- [ ] Can view single record with all details
- [ ] Can add notes to records after service
- [ ] Understand allergy/prescription critical information
- [ ] Successfully integrated error handling
- [ ] Tested complete workflow (view records → provide service → add notes)

---

## Rate Limiting

- **List Patients**: 100 requests per minute
- **Get Records**: 200 requests per minute
- **Add Notes**: 50 requests per minute

If you exceed limits, you'll receive a `429 Too Many Requests` response.

---

## Security Notes

⚠️ **Patient Privacy is Critical:**

1. **Only access records of patients you're treating** - Unauthorized access is tracked and logged
2. **Don't share patient data** - All data is confidential per healthcare regulations
3. **Log out properly** - Especially on shared devices
4. **Use HTTPS only** - Never use HTTP for authentication or patient data
5. **Secure your token** - Treat it like a password, never share it

---

**Last Updated:** 2026-04-08
**API Version:** 1.0
