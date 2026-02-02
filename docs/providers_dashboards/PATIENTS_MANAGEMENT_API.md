# Patients Management API - Provider Dashboard

## Overview

This documentation covers the complete patient management system for healthcare providers using the Medilink dashboard. Providers can manage two types of patients:

1. **Patients WITH Accounts** - Registered Medilink users who have created accounts
2. **Patients WITHOUT Accounts** - Patient records created by providers for patients who haven't registered yet

## Key Concepts

### Patient Types

| Type | Model | Description |
|------|-------|-------------|
| **Registered Patient** | `User` (role=PATIENT) | Has Medilink account, can log in, manage their own data |
| **Patient Record** | `PatientRecord` | Created by provider, no account, can be linked later |

### Access Control

Providers can only access patient information if:
- They created the patient record (PatientRecord)
- They have been granted explicit access (ProviderPatientAccess)
- Patient shared records via a share token (MedicalRecordShareToken)

### Medical Folder Visibility

- **Patient-controlled**: Patients can control who sees their medical folder
- **Share tokens**: Time-limited access via QR codes or token links
- **Provider access levels**: FULL, READ_ONLY, LIMITED

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Token <your_token>
```

---

## Patient Records Management (Patients WITHOUT Accounts)

### Create Patient Record

Create a new patient record for a patient who doesn't have a Medilink account.

```http
POST /api/patients/
```

**Request Body:**

```json
{
    "first_name": "Ahmed",
    "last_name": "Boumediene",
    "date_of_birth": "1985-03-15",
    "gender": "MALE",
    "phone_number": "+213555123456",
    "email": "ahmed.boumediene@email.com",
    "emergency_contact_name": "Fatima Boumediene",
    "emergency_contact_phone": "+213555789012",
    "blood_type": "O+",
    "known_allergies": "Penicillin, Peanuts",
    "chronic_conditions": "Type 2 Diabetes, Hypertension",
    "current_medications": "Metformin 500mg, Lisinopril 10mg",
    "national_id": "85315012345678",
    "address": "123 Rue Didouche Mourad",
    "city": "Algiers",
    "state": "Algiers",
    "country": "Algeria",
    "notes": "Patient prefers afternoon appointments"
}
```

**Response (201 Created):**

```json
{
    "id": 42,
    "patient_unique_id": "MED-A1B2C3D4",
    "first_name": "Ahmed",
    "last_name": "Boumediene",
    "full_name": "Ahmed Boumediene",
    "date_of_birth": "1985-03-15",
    "age": 40,
    "gender": "MALE",
    "phone_number": "+213555123456",
    "email": "ahmed.boumediene@email.com",
    "emergency_contact_name": "Fatima Boumediene",
    "emergency_contact_phone": "+213555789012",
    "blood_type": "O+",
    "known_allergies": "Penicillin, Peanuts",
    "chronic_conditions": "Type 2 Diabetes, Hypertension",
    "current_medications": "Metformin 500mg, Lisinopril 10mg",
    "national_id": "85315012345678",
    "address": "123 Rue Didouche Mourad",
    "city": "Algiers",
    "state": "Algiers",
    "country": "Algeria",
    "notes": "Patient prefers afternoon appointments",
    "is_active": true,
    "is_linked": false,
    "linking_token_masked": "aBcDeFgH...xYzW",
    "created_by_provider_name": "Dr. Karim Belhadj",
    "created_at": "2026-02-02T10:30:00Z",
    "updated_at": "2026-02-02T10:30:00Z"
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `first_name` | string | Yes | Patient's first name |
| `last_name` | string | Yes | Patient's last name |
| `date_of_birth` | date | Yes | Format: YYYY-MM-DD |
| `gender` | enum | Yes | MALE, FEMALE, OTHER, PREFER_NOT_TO_SAY |
| `phone_number` | string | No | Phone number with country code |
| `email` | string | No | Email address (not for login) |
| `blood_type` | enum | No | A+, A-, B+, B-, AB+, AB-, O+, O-, UNKNOWN |
| `known_allergies` | text | No | Free-text allergies |
| `chronic_conditions` | text | No | Free-text conditions |
| `current_medications` | text | No | Free-text medications |
| `national_id` | string | No | National ID number |
| `address` | text | No | Street address |
| `city` | string | No | City name |
| `state` | string | No | State/Province |
| `country` | string | No | Country (default: Algeria) |
| `notes` | text | No | Additional notes |

---

### List Patient Records

Get all patient records the provider has access to.

```http
GET /api/patients/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by name, phone, email, national_id |
| `gender` | enum | Filter by gender |
| `blood_type` | enum | Filter by blood type |
| `is_active` | boolean | Filter by active status |
| `city` | string | Filter by city |
| `ordering` | string | Sort by: first_name, last_name, date_of_birth, created_at |

**Example Request:**

```http
GET /api/patients/?search=Ahmed&blood_type=O%2B&ordering=-created_at
```

**Response (200 OK):**

```json
{
    "count": 15,
    "next": "https://dzmedilink.duckdns.org/api/patients/?page=2",
    "previous": null,
    "results": [
        {
            "id": 42,
            "patient_unique_id": "MED-A1B2C3D4",
            "first_name": "Ahmed",
            "last_name": "Boumediene",
            "full_name": "Ahmed Boumediene",
            "date_of_birth": "1985-03-15",
            "age": 40,
            "gender": "MALE",
            "phone_number": "+213555123456",
            "is_active": true,
            "is_linked": false,
            "created_at": "2026-02-02T10:30:00Z"
        },
        {
            "id": 38,
            "patient_unique_id": "MED-E5F6G7H8",
            "first_name": "Amina",
            "last_name": "Mansouri",
            "full_name": "Amina Mansouri",
            "date_of_birth": "1992-07-22",
            "age": 33,
            "gender": "FEMALE",
            "phone_number": "+213555654321",
            "is_active": true,
            "is_linked": true,
            "created_at": "2026-01-28T14:15:00Z"
        }
    ]
}
```

---

### Get Patient Record Details

```http
GET /api/patients/{id}/
```

**Response (200 OK):**

```json
{
    "id": 42,
    "patient_unique_id": "MED-A1B2C3D4",
    "first_name": "Ahmed",
    "last_name": "Boumediene",
    "full_name": "Ahmed Boumediene",
    "date_of_birth": "1985-03-15",
    "age": 40,
    "gender": "MALE",
    "phone_number": "+213555123456",
    "email": "ahmed.boumediene@email.com",
    "emergency_contact_name": "Fatima Boumediene",
    "emergency_contact_phone": "+213555789012",
    "blood_type": "O+",
    "known_allergies": "Penicillin, Peanuts",
    "chronic_conditions": "Type 2 Diabetes, Hypertension",
    "current_medications": "Metformin 500mg, Lisinopril 10mg",
    "national_id": "85315012345678",
    "address": "123 Rue Didouche Mourad",
    "city": "Algiers",
    "state": "Algiers",
    "country": "Algeria",
    "notes": "Patient prefers afternoon appointments",
    "is_active": true,
    "is_linked": false,
    "linking_token_masked": "aBcDeFgH...xYzW",
    "created_by_provider_name": "Dr. Karim Belhadj",
    "created_at": "2026-02-02T10:30:00Z",
    "updated_at": "2026-02-02T10:30:00Z"
}
```

---

### Update Patient Record

```http
PUT /api/patients/{id}/
PATCH /api/patients/{id}/
```

**Request Body (PATCH - partial update):**

```json
{
    "phone_number": "+213555999888",
    "current_medications": "Metformin 500mg, Lisinopril 20mg, Amlodipine 5mg",
    "notes": "Updated medication dosage"
}
```

**Response (200 OK):**

```json
{
    "id": 42,
    "patient_unique_id": "MED-A1B2C3D4",
    "first_name": "Ahmed",
    "last_name": "Boumediene",
    "phone_number": "+213555999888",
    "current_medications": "Metformin 500mg, Lisinopril 20mg, Amlodipine 5mg",
    "notes": "Updated medication dosage",
    "updated_at": "2026-02-02T11:45:00Z"
}
```

---

### Deactivate Patient Record (Soft Delete)

```http
DELETE /api/patients/{id}/
```

**Response (200 OK):**

```json
{
    "message": "Patient record has been deactivated."
}
```

> **Note**: This is a soft delete - the record is deactivated but not removed from the database for audit and medical record integrity purposes.

---

## Linking Token Management

When you create a patient record, a unique linking token is generated. Give this token to the patient so they can link their future Medilink account to their existing records.

### Get Linking Token

Retrieve the full linking token for a patient record.

```http
GET /api/patients/{id}/token/
```

**Response (200 OK) - Token Available:**

```json
{
    "linking_token": "aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789abcdef",
    "patient_name": "Ahmed Boumediene",
    "token_used": false,
    "is_linked": false
}
```

**Response (200 OK) - Already Linked:**

```json
{
    "linking_token": null,
    "patient_name": "Ahmed Boumediene",
    "token_used": true,
    "is_linked": true,
    "message": "Token has already been used or record is linked."
}
```

### Regenerate Linking Token

If the token was lost or needs to be reissued.

```http
POST /api/patients/{id}/regenerate-token/
```

**Response (200 OK):**

```json
{
    "linking_token": "newTokenAbCdEfGhIjKlMnOpQrStUvWxYz987654321",
    "patient_name": "Ahmed Boumediene",
    "message": "Token has been regenerated."
}
```

> **Note**: Only the creator of the patient record can regenerate the token. Cannot regenerate for already-linked records.

---

## Provider Access Management

Grant or manage access for other providers to your patient records.

### Grant Access to Another Provider

```http
POST /api/patients/{id}/grant-access/
```

**Request Body:**

```json
{
    "provider_id": 15,
    "access_level": "READ_ONLY"
}
```

**Access Levels:**

| Level | Description |
|-------|-------------|
| `FULL` | Can view, update, and manage all patient data |
| `READ_ONLY` | Can only view patient data |
| `LIMITED` | Can view basic info only, no confidential records |

**Response (201 Created):**

```json
{
    "id": 78,
    "provider": 15,
    "provider_name": "Dr. Salima Khelifi",
    "patient_record": 42,
    "patient_name": "Ahmed Boumediene",
    "access_level": "READ_ONLY",
    "created_at": "2026-02-02T12:00:00Z"
}
```

---

## Patient Medical History

### Get Complete Patient History

Access the full medical history for a patient you have access to.

```http
GET /api/patients/{patient_id}/history/
```

**Response (200 OK):**

```json
{
    "patient": {
        "id": 42,
        "patient_unique_id": "MED-A1B2C3D4",
        "full_name": "Ahmed Boumediene",
        "date_of_birth": "1985-03-15",
        "age": 40,
        "gender": "MALE",
        "blood_type": "O+",
        "known_allergies": "Penicillin, Peanuts",
        "chronic_conditions": "Type 2 Diabetes, Hypertension",
        "current_medications": "Metformin 500mg, Lisinopril 10mg",
        "emergency_contact_name": "Fatima Boumediene",
        "emergency_contact_phone": "+213555789012"
    },
    "medical_history": {
        "total_records": 12,
        "by_type": {
            "DIAGNOSIS": [
                {
                    "id": 156,
                    "title": "Type 2 Diabetes Mellitus",
                    "record_date": "2022-06-15",
                    "description": "Initial diagnosis of Type 2 Diabetes",
                    "diagnosis_code": "E11.9",
                    "symptoms": "Polyuria, polydipsia, fatigue",
                    "is_confidential": false,
                    "requires_followup": true,
                    "created_at": "2022-06-15T10:30:00Z"
                },
                {
                    "id": 167,
                    "title": "Essential Hypertension",
                    "record_date": "2023-01-20",
                    "description": "Primary hypertension diagnosis",
                    "diagnosis_code": "I10",
                    "symptoms": "Headaches, elevated BP readings",
                    "is_confidential": false,
                    "requires_followup": true,
                    "created_at": "2023-01-20T14:15:00Z"
                }
            ],
            "PRESCRIPTION": [
                {
                    "id": 178,
                    "title": "Metformin Prescription",
                    "record_date": "2022-06-15",
                    "description": "500mg twice daily",
                    "diagnosis_code": null,
                    "symptoms": null,
                    "is_confidential": false,
                    "requires_followup": false,
                    "created_at": "2022-06-15T10:35:00Z"
                }
            ],
            "LAB_RESULT": [
                {
                    "id": 189,
                    "title": "HbA1c Test",
                    "record_date": "2026-01-15",
                    "description": "HbA1c: 7.2% - Well controlled",
                    "diagnosis_code": null,
                    "symptoms": null,
                    "is_confidential": false,
                    "requires_followup": false,
                    "created_at": "2026-01-15T09:00:00Z"
                }
            ],
            "ALLERGY": [
                {
                    "id": 145,
                    "title": "Penicillin Allergy",
                    "record_date": "2015-03-10",
                    "description": "Severe allergic reaction to Penicillin",
                    "diagnosis_code": "T88.7",
                    "symptoms": "Anaphylaxis, hives, difficulty breathing",
                    "is_confidential": false,
                    "requires_followup": false,
                    "created_at": "2015-03-10T11:20:00Z"
                }
            ]
        }
    }
}
```

---

## Medical Records CRUD

### Create Medical Record for Patient

Add a new medical record to a patient's folder.

```http
POST /api/medical-records/records/
```

**Request Body:**

```json
{
    "patient": 85,
    "patient_record": 42,
    "title": "Follow-up Consultation - Diabetes",
    "record_type": "NOTE",
    "description": "Patient reports improved blood sugar control. No hypoglycemic episodes.",
    "symptoms": "None reported",
    "record_date": "2026-02-02",
    "diagnosis_code": "E11.9",
    "is_confidential": false,
    "requires_followup": true,
    "followup_date": "2026-05-02"
}
```

**Record Types:**

| Type | Description |
|------|-------------|
| `DIAGNOSIS` | Medical diagnosis |
| `PRESCRIPTION` | Medication prescription |
| `ALLERGY` | Allergy information |
| `LAB_RESULT` | Laboratory test results |
| `IMAGING` | Imaging studies (X-ray, MRI, etc.) |
| `PROCEDURE` | Medical procedures |
| `NOTE` | General clinical notes |
| `VACCINATION` | Vaccination records |
| `OTHER` | Other record types |

**Response (201 Created):**

```json
{
    "id": 201,
    "patient": 85,
    "patient_record": 42,
    "patient_email": null,
    "title": "Follow-up Consultation - Diabetes",
    "record_type": "NOTE",
    "diagnosis_code": "E11.9",
    "description": "Patient reports improved blood sugar control. No hypoglycemic episodes.",
    "symptoms": "None reported",
    "record_date": "2026-02-02",
    "created_by": 12,
    "created_by_email": "dr.belhadj@medilink.dz",
    "is_active": true,
    "is_confidential": false,
    "requires_followup": true,
    "followup_date": "2026-05-02",
    "created_at": "2026-02-02T14:30:00Z"
}
```

> **Important**: When adding records, you can specify either:
> - `patient` - For patients WITH Medilink accounts (User ID)
> - `patient_record` - For patients WITHOUT accounts (PatientRecord ID)
> 
> The record will be automatically added to the patient's medical folder.

---

### List Medical Records

```http
GET /api/medical-records/records/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `record_type` | enum | Filter by type |
| `patient` | integer | Filter by patient User ID |
| `is_active` | boolean | Filter active records |
| `requires_followup` | boolean | Filter records needing followup |
| `search` | string | Search title, description, symptoms |
| `ordering` | string | Sort by record_date, created_at |

**Response (200 OK):**

```json
{
    "count": 45,
    "next": "https://dzmedilink.duckdns.org/api/medical-records/records/?page=2",
    "previous": null,
    "results": [
        {
            "id": 201,
            "title": "Follow-up Consultation - Diabetes",
            "record_type": "NOTE",
            "record_date": "2026-02-02",
            "patient_email": null,
            "created_by_email": "dr.belhadj@medilink.dz",
            "is_active": true,
            "requires_followup": true,
            "followup_date": "2026-05-02",
            "created_at": "2026-02-02T14:30:00Z",
            "has_prescription": false,
            "has_allergy": false,
            "attachment_count": 0,
            "note_count": 1
        }
    ]
}
```

---

### Get Medical Record Details

```http
GET /api/medical-records/records/{id}/
```

**Response (200 OK):**

```json
{
    "id": 201,
    "patient": 85,
    "patient_email": "ahmed.b@medilink.dz",
    "title": "Follow-up Consultation - Diabetes",
    "record_type": "NOTE",
    "diagnosis_code": "E11.9",
    "description": "Patient reports improved blood sugar control. No hypoglycemic episodes.",
    "symptoms": "None reported",
    "record_date": "2026-02-02",
    "created_by": 12,
    "created_by_email": "dr.belhadj@medilink.dz",
    "updated_by": null,
    "updated_by_email": null,
    "is_active": true,
    "is_confidential": false,
    "requires_followup": true,
    "followup_date": "2026-05-02",
    "created_at": "2026-02-02T14:30:00Z",
    "updated_at": "2026-02-02T14:30:00Z",
    "prescription": null,
    "allergy": null,
    "attachments": [],
    "notes": [
        {
            "id": 89,
            "note_type": "PROVIDER",
            "content": "Continue current medication. Schedule lab work before next visit.",
            "created_by_email": "dr.belhadj@medilink.dz",
            "created_at": "2026-02-02T14:35:00Z",
            "updated_at": "2026-02-02T14:35:00Z",
            "is_locked": true
        }
    ]
}
```

---

### Update Medical Record

```http
PATCH /api/medical-records/records/{id}/
```

**Request Body:**

```json
{
    "description": "Updated: Patient reports improved blood sugar control. HbA1c down to 6.8%.",
    "requires_followup": true,
    "followup_date": "2026-08-02"
}
```

---

### Add Attachment to Medical Record

```http
POST /api/medical-records/records/{id}/attachments/
```

**Request (multipart/form-data):**

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | The file to upload |
| `description` | string | Optional description |

**Response (201 Created):**

```json
{
    "id": 45,
    "file": "https://dzmedilink.duckdns.org/media/attachments/lab_result_2026.pdf",
    "file_name": "lab_result_2026.pdf",
    "file_type": "application/pdf",
    "file_size": 125432,
    "description": "HbA1c lab results - January 2026",
    "uploaded_by_email": "dr.belhadj@medilink.dz",
    "uploaded_at": "2026-02-02T15:00:00Z"
}
```

---

### Add Note to Medical Record

```http
POST /api/medical-records/records/{id}/notes/
```

**Request Body:**

```json
{
    "note_type": "PROVIDER",
    "content": "Discussed lifestyle modifications. Patient committed to daily walking."
}
```

**Note Types:**

| Type | Description |
|------|-------------|
| `PROVIDER` | Notes from healthcare providers (auto-locked) |
| `PATIENT` | Notes from the patient |
| `SYSTEM` | System-generated notes |

**Response (201 Created):**

```json
{
    "id": 90,
    "note_type": "PROVIDER",
    "content": "Discussed lifestyle modifications. Patient committed to daily walking.",
    "created_by_email": "dr.belhadj@medilink.dz",
    "created_at": "2026-02-02T15:05:00Z",
    "updated_at": "2026-02-02T15:05:00Z",
    "is_locked": true
}
```

---

### Export Medical Record as PDF

```http
GET /api/medical-records/records/{id}/export-pdf/
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_attachments` | boolean | false | Include attachment list |

**Response:** PDF file download

---

## Accessing Records via Share Token

When a patient shares their medical records via a token, use this endpoint to access them.

### Access Records via Share Token

```http
GET /api/patients/records/share/{token}/
```

**Response (200 OK):**

```json
{
    "access_level": "READ_ONLY",
    "token_id": 23,
    "uses_remaining": 2,
    "expires_at": "2026-02-03T10:30:00Z",
    "patient": {
        "patient_unique_id": "MED-A1B2C3D4",
        "full_name": "Ahmed Boumediene",
        "date_of_birth": "1985-03-15",
        "age": 40,
        "gender": "MALE",
        "blood_type": "O+"
    },
    "medical_records": {
        "count": 12,
        "records": [
            {
                "id": 201,
                "title": "Follow-up Consultation - Diabetes",
                "record_type": "NOTE",
                "record_date": "2026-02-02",
                "is_confidential": false
            },
            {
                "id": 189,
                "title": "HbA1c Test",
                "record_type": "LAB_RESULT",
                "record_date": "2026-01-15",
                "is_confidential": false
            }
        ]
    },
    "access_granted": false
}
```

**Access Level Details:**

| Level | Patient Info | Medical Records | Notes |
|-------|-------------|-----------------|-------|
| `FULL` | Complete info + allergies, conditions, medications | All records with full details | Auto-grants READ_ONLY access |
| `READ_ONLY` | Complete info + allergies, conditions, medications | All records, basic info | View only |
| `LIMITED` | Basic info only | Non-confidential records only | Restricted view |

**Error Responses:**

```json
// Token expired
{
    "error": "This share token has expired."
}

// Token revoked
{
    "error": "This share token has been revoked."
}

// Wrong provider
{
    "error": "This share token is for a different provider."
}
```

---

## Provider Access to Patient Records

### View My Patients (Patients I Have Access To)

```http
GET /api/medical-records/access/my-patients/
```

**Response (200 OK):**

```json
[
    {
        "id": 45,
        "patient": 85,
        "provider": 12,
        "access_type": "FULL",
        "is_active": true,
        "granted_at": "2026-01-15T09:00:00Z",
        "expires_at": null
    },
    {
        "id": 52,
        "patient": 91,
        "provider": 12,
        "access_type": "READ_ONLY",
        "is_active": true,
        "granted_at": "2026-02-01T10:30:00Z",
        "expires_at": "2026-08-01T10:30:00Z"
    }
]
```

---

### Get Records for Specific Patient (Registered Users)

```http
GET /api/medical-records/records/patient/{patient_id}/
```

**Response (200 OK):**

```json
{
    "count": 8,
    "results": [
        {
            "id": 201,
            "title": "Follow-up Consultation - Diabetes",
            "record_type": "NOTE",
            "record_date": "2026-02-02",
            "patient_email": "ahmed.b@medilink.dz",
            "created_by_email": "dr.belhadj@medilink.dz",
            "is_active": true,
            "requires_followup": true,
            "followup_date": "2026-05-02"
        }
    ]
}
```

---

## Patient Identification System

### Patient Unique ID Format

Every patient record has a unique identifier in the format:

```
MED-XXXXXXXX
```

Example: `MED-A1B2C3D4`

This ID can be used to:
- Quickly identify patients
- Print on patient cards
- Reference in communications
- Search across providers

### Understanding Linked vs Unlinked Patients

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Patient Record States                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐                    ┌─────────────────┐          │
│  │  UNLINKED       │                    │  LINKED         │          │
│  │  PatientRecord  │  ───────────────►  │  PatientRecord  │          │
│  │                 │   Patient uses     │  + User Account │          │
│  │  is_linked=false│   linking token    │  is_linked=true │          │
│  │  linked_user=null│                   │  linked_user=85 │          │
│  └─────────────────┘                    └─────────────────┘          │
│                                                                       │
│  • Created by provider                  • Patient has full control   │
│  • Provider has full access             • Can manage their data      │
│  • Patient has linking token            • Token is consumed          │
│  • Give token to patient                • Medical records preserved  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Medical Folder Privacy Control

### How Patients Control Access

Patients with linked accounts can control access to their medical folder:

1. **Share Tokens** - Time-limited access via QR codes
2. **Provider Access Grants** - Explicit permission to specific providers
3. **Confidential Records** - Mark sensitive records as confidential

### Provider Visibility Rules

| Scenario | What Provider Can See |
|----------|----------------------|
| Provider created the PatientRecord | Full access to their own records |
| Provider has FULL access grant | All records including confidential |
| Provider has READ_ONLY access | All records, cannot modify |
| Provider has LIMITED access | Basic info, non-confidential only |
| Provider used FULL share token | All records (auto-grants READ_ONLY) |
| Provider used LIMITED share token | Non-confidential records only |

---

## Error Responses

### Common Error Codes

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | No permission to access resource |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate entry (e.g., national_id) |

### Error Response Format

```json
{
    "error": "You do not have access to this patient."
}
```

Or for validation errors:

```json
{
    "first_name": ["This field is required."],
    "date_of_birth": ["Enter a valid date."]
}
```

---

## Dashboard Integration Flow

### Complete Patient Management Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Provider Dashboard - Patient Management               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. NEW PATIENT (No Account)                                               │
│     ┌───────────────┐                                                      │
│     │ Create Record │ ──► PatientRecord created                           │
│     │ POST /patients│     with unique ID + linking token                  │
│     └───────────────┘                                                      │
│            │                                                               │
│            ▼                                                               │
│     ┌───────────────┐                                                      │
│     │ Print/Share   │ ──► Give linking token to patient                   │
│     │ Linking Token │     (QR code, card, etc.)                           │
│     └───────────────┘                                                      │
│                                                                            │
│  2. ADD MEDICAL RECORDS                                                    │
│     ┌───────────────────┐                                                  │
│     │ Create Record     │ ──► Medical record added to folder              │
│     │ POST /records     │     (diagnosis, prescription, etc.)             │
│     └───────────────────┘                                                  │
│            │                                                               │
│            ▼                                                               │
│     ┌───────────────────┐                                                  │
│     │ Add Attachments   │ ──► Lab results, images, PDFs                   │
│     │ Add Notes         │                                                  │
│     └───────────────────┘                                                  │
│                                                                            │
│  3. VIEW PATIENT HISTORY                                                   │
│     ┌───────────────────┐                                                  │
│     │ GET /{id}/history │ ──► Complete medical history                    │
│     └───────────────────┘     grouped by record type                      │
│                                                                            │
│  4. RECEIVE PATIENT VIA SHARE TOKEN                                        │
│     ┌───────────────────────────┐                                          │
│     │ Patient shares QR/token   │                                          │
│     │ GET /records/share/{token}│ ──► Access patient records              │
│     └───────────────────────────┘     based on access level               │
│                                                                            │
│  5. COLLABORATE WITH OTHER PROVIDERS                                       │
│     ┌─────────────────────────┐                                            │
│     │ Grant Access            │ ──► Other providers can                   │
│     │ POST /{id}/grant-access │     view/manage records                   │
│     └─────────────────────────┘                                            │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Summary

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/patients/` | GET | List all patient records |
| `/api/patients/` | POST | Create patient record |
| `/api/patients/{id}/` | GET | Get patient details |
| `/api/patients/{id}/` | PATCH | Update patient record |
| `/api/patients/{id}/` | DELETE | Deactivate patient record |
| `/api/patients/{id}/token/` | GET | Get linking token |
| `/api/patients/{id}/regenerate-token/` | POST | Regenerate linking token |
| `/api/patients/{id}/grant-access/` | POST | Grant access to provider |
| `/api/patients/{id}/history/` | GET | Get full medical history |
| `/api/patients/records/share/{token}/` | GET | Access via share token |
| `/api/medical-records/records/` | GET/POST | List/Create medical records |
| `/api/medical-records/records/{id}/` | GET/PATCH | Get/Update medical record |
| `/api/medical-records/records/{id}/attachments/` | POST | Add attachment |
| `/api/medical-records/records/{id}/notes/` | POST | Add note |
| `/api/medical-records/records/{id}/export-pdf/` | GET | Export as PDF |
| `/api/medical-records/records/patient/{id}/` | GET | Records for patient |
| `/api/medical-records/access/my-patients/` | GET | List my patients |

### Best Practices

1. **Always check `is_linked`** - To know if patient has an account
2. **Use `patient_unique_id`** - For patient identification and communication
3. **Respect access levels** - Don't attempt to access beyond your permission
4. **Log all access** - System automatically logs record access for audit
5. **Handle confidential records** - Mark sensitive records appropriately
6. **Provide linking tokens** - Help patients link their future accounts
