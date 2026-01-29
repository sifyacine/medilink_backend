# 📋 Medilink Patients Management System - Complete Report

## Executive Summary

The Medilink Patients Management System is a comprehensive healthcare data management solution that enables providers to manage patient records and allows patients to control access to their medical information. The system supports patients with and without Medilink accounts, secure record sharing via QR codes/tokens, and fine-grained access control.

---

## 📊 System Overview

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Patient Record** | Healthcare data for a patient (with or without account) |
| **Linking Token** | One-time secure token to link records to a user account |
| **Share Token** | Time-limited token for sharing records with providers |
| **Provider Access** | Permissions defining which providers can access which patients |

### User Roles

| Role | Description | Can Create Records | Can Link Account | Can Share Records |
|------|-------------|-------------------|------------------|-------------------|
| **PATIENT** | End user with Medilink account | ❌ | ✅ | ✅ (if linked) |
| **PROVIDER** | Healthcare professional (Doctor, Nurse, Clinic, Lab, etc.) | ✅ (if approved) | ❌ | ❌ |
| **ADMIN** | System administrator | ✅ | ❌ | ❌ |

---

## 🗄️ Data Models

### 1. PatientRecord

The core model storing patient information.

```
┌─────────────────────────────────────────────────────────────────┐
│                        PatientRecord                            │
├─────────────────────────────────────────────────────────────────┤
│ IDENTIFICATION                                                  │
│   • id (int) - Database primary key                             │
│   • patient_unique_id (string) - Format: MED-XXXXXXXX           │
│   • national_id (string, optional) - Government ID              │
├─────────────────────────────────────────────────────────────────┤
│ ACCOUNT LINKING                                                 │
│   • linked_user (FK → User, nullable) - Linked account          │
│   • linking_token (string, unique) - 256-bit secure token       │
│   • token_used (bool) - Whether token was used                  │
│   • token_used_at (datetime, nullable) - When token was used    │
├─────────────────────────────────────────────────────────────────┤
│ PERSONAL INFORMATION                                            │
│   • first_name (string, required)                               │
│   • last_name (string, required)                                │
│   • date_of_birth (date, required)                              │
│   • gender (enum: MALE, FEMALE, OTHER, PREFER_NOT_TO_SAY)       │
├─────────────────────────────────────────────────────────────────┤
│ CONTACT INFORMATION                                             │
│   • phone_number (string)                                       │
│   • email (email)                                               │
│   • emergency_contact_name (string)                             │
│   • emergency_contact_phone (string)                            │
├─────────────────────────────────────────────────────────────────┤
│ MEDICAL INFORMATION                                             │
│   • blood_type (enum: A+, A-, B+, B-, AB+, AB-, O+, O-, UNKNOWN)│
│   • known_allergies (text)                                      │
│   • chronic_conditions (text)                                   │
│   • current_medications (text)                                  │
├─────────────────────────────────────────────────────────────────┤
│ ADDRESS                                                         │
│   • address (text)                                              │
│   • city (string)                                               │
│   • state (string)                                              │
│   • country (string, default: "Algeria")                        │
├─────────────────────────────────────────────────────────────────┤
│ METADATA                                                        │
│   • notes (text)                                                │
│   • is_active (bool, default: true)                             │
│   • is_deleted (bool, default: false) - Soft delete flag        │
│   • deleted_at (datetime, nullable)                             │
│   • deleted_by (FK → User, nullable)                            │
│   • created_by_provider (FK → Provider)                         │
│   • created_at (datetime)                                       │
│   • updated_at (datetime, auto)                                 │
├─────────────────────────────────────────────────────────────────┤
│ COMPUTED PROPERTIES                                             │
│   • full_name → "{first_name} {last_name}"                      │
│   • age → calculated from date_of_birth                         │
│   • is_linked → linked_user is not None                         │
└─────────────────────────────────────────────────────────────────┘
```

### 2. ProviderPatientAccess

Controls which providers can access which patient records.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ProviderPatientAccess                       │
├─────────────────────────────────────────────────────────────────┤
│   • id (int)                                                    │
│   • provider (FK → Provider) - Who has access                   │
│   • patient_record (FK → PatientRecord) - To which patient      │
│   • access_level (enum: FULL, READ_ONLY, LIMITED)               │
│   • granted_by (FK → Provider, nullable) - Who granted access   │
│   • created_at (datetime)                                       │
│   • updated_at (datetime)                                       │
├─────────────────────────────────────────────────────────────────┤
│ UNIQUE CONSTRAINT: (provider, patient_record)                   │
└─────────────────────────────────────────────────────────────────┘
```

**Access Level Definitions:**

| Level | View Patient Info | View All Records | View Confidential | Modify Records | Grant Access |
|-------|-------------------|------------------|-------------------|----------------|--------------|
| **FULL** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **READ_ONLY** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **LIMITED** | ✅ | ✅ | ❌ | ❌ | ❌ |

### 3. MedicalRecordShareToken

Time-limited tokens for secure record sharing.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MedicalRecordShareToken                      │
├─────────────────────────────────────────────────────────────────┤
│ TOKEN IDENTIFICATION                                            │
│   • id (int)                                                    │
│   • token (string, unique) - 192-bit secure token               │
├─────────────────────────────────────────────────────────────────┤
│ RELATIONSHIPS                                                   │
│   • patient_record (FK → PatientRecord)                         │
│   • created_by_user (FK → User, nullable)                       │
│   • target_provider (FK → Provider, nullable) - Targeted share  │
├─────────────────────────────────────────────────────────────────┤
│ ACCESS CONFIGURATION                                            │
│   • access_level (enum: READ_ONLY, FULL, LIMITED)               │
│   • expires_at (datetime) - Token expiry                        │
│   • max_uses (int) - Maximum uses (0 = unlimited)               │
│   • use_count (int) - Current use count                         │
├─────────────────────────────────────────────────────────────────┤
│ STATUS                                                          │
│   • is_active (bool)                                            │
│   • is_revoked (bool)                                           │
│   • revoked_at (datetime, nullable)                             │
│   • notes (text)                                                │
│   • created_at (datetime)                                       │
├─────────────────────────────────────────────────────────────────┤
│ COMPUTED PROPERTIES                                             │
│   • is_expired → now() > expires_at                             │
│   • is_usable → active AND not revoked AND not expired          │
│                 AND use_count < max_uses                        │
└─────────────────────────────────────────────────────────────────┘
```

### 4. ShareTokenAccessLog

Audit trail for share token usage.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ShareTokenAccessLog                         │
├─────────────────────────────────────────────────────────────────┤
│   • id (int)                                                    │
│   • share_token (FK → MedicalRecordShareToken)                  │
│   • accessed_by_provider (FK → Provider, nullable)              │
│   • accessed_at (datetime)                                      │
│   • ip_address (IP address, nullable)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔗 API Endpoints Reference

### Base URL: `/api/patients/`

---

### 📌 Provider Endpoints

#### 1. List Patient Records
```
GET /api/patients/
```

**Description:** Get all patient records the provider has access to.

**Authentication:** Required (Provider)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by name, phone, email, national_id |
| `gender` | string | Filter: MALE, FEMALE, OTHER, PREFER_NOT_TO_SAY |
| `blood_type` | string | Filter: A+, A-, B+, B-, AB+, AB-, O+, O-, UNKNOWN |
| `is_active` | bool | Filter by active status |
| `city` | string | Filter by city |
| `country` | string | Filter by country |
| `ordering` | string | Order by: first_name, last_name, date_of_birth, created_at |
| `page` | int | Pagination page number |

**Response (200):**
```json
{
  "count": 42,
  "next": "http://api.medilink.com/api/patients/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient_unique_id": "MED-A1B2C3D4",
      "first_name": "Ahmed",
      "last_name": "Benali",
      "full_name": "Ahmed Benali",
      "date_of_birth": "1985-03-15",
      "age": 40,
      "gender": "MALE",
      "phone_number": "+213555123456",
      "is_active": true,
      "is_linked": false,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

#### 2. Create Patient Record
```
POST /api/patients/
```

**Description:** Create a new patient record for a patient without an account.

**Authentication:** Required (Approved Provider only)

**Request Body:**
```json
{
  "first_name": "Ahmed",
  "last_name": "Benali",
  "date_of_birth": "1985-03-15",
  "gender": "MALE",
  "phone_number": "+213555123456",
  "email": "ahmed@example.com",
  "blood_type": "A+",
  "known_allergies": "Penicillin, Shellfish",
  "chronic_conditions": "Hypertension, Type 2 Diabetes",
  "current_medications": "Lisinopril 10mg daily, Metformin 500mg twice daily",
  "national_id": "123456789012345",
  "address": "123 Main Street, Apt 4B",
  "city": "Algiers",
  "state": "Algiers",
  "country": "Algeria",
  "emergency_contact_name": "Fatima Benali",
  "emergency_contact_phone": "+213555987654",
  "notes": "Patient prefers morning appointments. Arabic speaker."
}
```

**Required Fields:** `first_name`, `last_name`, `date_of_birth`, `gender`

**Response (201):**
```json
{
  "id": 1,
  "patient_unique_id": "MED-A1B2C3D4",
  "first_name": "Ahmed",
  "last_name": "Benali",
  "full_name": "Ahmed Benali",
  "date_of_birth": "1985-03-15",
  "age": 40,
  "gender": "MALE",
  "phone_number": "+213555123456",
  "email": "ahmed@example.com",
  "emergency_contact_name": "Fatima Benali",
  "emergency_contact_phone": "+213555987654",
  "blood_type": "A+",
  "known_allergies": "Penicillin, Shellfish",
  "chronic_conditions": "Hypertension, Type 2 Diabetes",
  "current_medications": "Lisinopril 10mg daily, Metformin 500mg twice daily",
  "national_id": "123456789012345",
  "address": "123 Main Street, Apt 4B",
  "city": "Algiers",
  "state": "Algiers",
  "country": "Algeria",
  "notes": "Patient prefers morning appointments. Arabic speaker.",
  "is_active": true,
  "is_linked": false,
  "linking_token_masked": "abc12345...xyz9",
  "created_by_provider_name": "Dr. Mohamed Larbi",
  "created_at": "2025-01-28T10:30:00Z",
  "updated_at": "2025-01-28T10:30:00Z"
}
```

**Auto-Generated:**
- `patient_unique_id` - Format: MED-XXXXXXXX
- `linking_token` - 256-bit secure token (masked in response)
- `created_by_provider` - Set to authenticated provider
- Provider automatically granted FULL access

---

#### 3. Get Patient Record Details
```
GET /api/patients/{id}/
```

**Description:** Get full details of a specific patient record.

**Authentication:** Required (Provider with access)

**Response (200):** Same as create response.

**Errors:**
- `403 Forbidden` - No access to this patient
- `404 Not Found` - Patient record doesn't exist

---

#### 4. Update Patient Record
```
PUT /api/patients/{id}/
PATCH /api/patients/{id}/
```

**Description:** Update patient record information.

**Authentication:** Required (Provider with FULL access or creator)

**Request Body (PATCH - partial update):**
```json
{
  "phone_number": "+213555999888",
  "current_medications": "Lisinopril 20mg daily, Metformin 1000mg twice daily",
  "notes": "Increased dosage as of January 2025"
}
```

**Updatable Fields:**
- `first_name`, `last_name`, `date_of_birth`, `gender`
- `phone_number`, `email`
- `emergency_contact_name`, `emergency_contact_phone`
- `blood_type`, `known_allergies`, `chronic_conditions`, `current_medications`
- `address`, `city`, `state`, `country`
- `notes`, `is_active`

**Non-Updatable Fields:** `patient_unique_id`, `linking_token`, `national_id`

---

#### 5. Delete Patient Record (Soft Delete)
```
DELETE /api/patients/{id}/
```

**Description:** Soft delete a patient record (sets `is_active = false`).

**Authentication:** Required (Provider with FULL access or creator)

**Response (204):** No content

**Note:** Record is not permanently deleted; can be restored by admin.

---

#### 6. Get Linking Token
```
GET /api/patients/{id}/token/
```

**Description:** Get the full linking token to give to the patient.

**Authentication:** Required (Provider with FULL access or creator)

**Response (200) - Token available:**
```json
{
  "linking_token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
  "patient_name": "Ahmed Benali",
  "token_used": false,
  "is_linked": false
}
```

**Response (200) - Token already used:**
```json
{
  "linking_token": null,
  "patient_name": "Ahmed Benali",
  "token_used": true,
  "is_linked": true,
  "message": "Token has already been used or record is linked."
}
```

---

#### 7. Regenerate Linking Token
```
POST /api/patients/{id}/regenerate-token/
```

**Description:** Regenerate a lost or compromised linking token.

**Authentication:** Required (Creator only)

**Conditions:** Cannot regenerate if record is already linked.

**Response (200):**
```json
{
  "linking_token": "new123token456here789abc012def345ghi678jkl901mno234",
  "patient_name": "Ahmed Benali",
  "message": "Token has been regenerated."
}
```

---

#### 8. Grant Provider Access
```
POST /api/patients/{id}/grant-access/
```

**Description:** Grant another provider access to this patient's records.

**Authentication:** Required (Provider with FULL access or creator)

**Request Body:**
```json
{
  "patient_record_id": 1,
  "provider_id": 5,
  "access_level": "READ_ONLY"
}
```

**Access Levels:** `FULL`, `READ_ONLY`, `LIMITED`

**Response (201):**
```json
{
  "id": 12,
  "provider": 5,
  "provider_name": "Dr. Amira Hadj",
  "patient_record": 1,
  "patient_name": "Ahmed Benali",
  "access_level": "READ_ONLY",
  "created_at": "2025-01-28T11:00:00Z"
}
```

---

#### 9. Get Patient Medical History
```
GET /api/patients/{patient_id}/history/
```

**Description:** Get complete medical history for a patient.

**Authentication:** Required (Provider with access)

**Response (200):**
```json
{
  "patient": {
    "id": 1,
    "patient_unique_id": "MED-A1B2C3D4",
    "full_name": "Ahmed Benali",
    "date_of_birth": "1985-03-15",
    "age": 40,
    "gender": "MALE",
    "blood_type": "A+",
    "known_allergies": "Penicillin, Shellfish",
    "chronic_conditions": "Hypertension, Type 2 Diabetes",
    "current_medications": "Lisinopril 20mg daily, Metformin 1000mg twice daily",
    "emergency_contact_name": "Fatima Benali",
    "emergency_contact_phone": "+213555987654"
  },
  "medical_history": {
    "total_records": 15,
    "by_type": {
      "DIAGNOSIS": [
        {
          "id": 1,
          "title": "Essential Hypertension",
          "record_date": "2024-01-10",
          "description": "Stage 1 hypertension diagnosed",
          "diagnosis_code": "I10",
          "symptoms": "Elevated BP readings: 145/95",
          "is_confidential": false,
          "requires_followup": true,
          "created_at": "2024-01-10T09:30:00Z"
        }
      ],
      "PRESCRIPTION": [...],
      "LAB_RESULT": [...],
      "VACCINATION": [...]
    }
  }
}
```

---

#### 10. Access Records via Share Token
```
GET /api/patients/records/share/{token}/
```

**Description:** Access patient records using a share token (from QR code).

**Authentication:** Required (Provider)

**Response (200):**
```json
{
  "access_level": "READ_ONLY",
  "token_id": 5,
  "uses_remaining": 0,
  "expires_at": "2025-01-29T10:30:00Z",
  "patient": {
    "patient_unique_id": "MED-A1B2C3D4",
    "full_name": "Ahmed Benali",
    "date_of_birth": "1985-03-15",
    "age": 40,
    "gender": "MALE",
    "blood_type": "A+",
    "known_allergies": "Penicillin, Shellfish",
    "chronic_conditions": "Hypertension, Type 2 Diabetes",
    "current_medications": "Lisinopril 20mg daily",
    "emergency_contact_name": "Fatima Benali",
    "emergency_contact_phone": "+213555987654"
  },
  "medical_records": {
    "count": 15,
    "records": [
      {
        "id": 1,
        "title": "Essential Hypertension",
        "record_type": "DIAGNOSIS",
        "record_date": "2024-01-10",
        "is_confidential": false,
        "description": "Stage 1 hypertension diagnosed",
        "symptoms": "Elevated BP readings",
        "diagnosis_code": "I10"
      }
    ]
  },
  "access_granted": true
}
```

**Errors:**
```json
// Token expired
{"error": "This share token has expired."}

// Token revoked
{"error": "This share token has been revoked."}

// Wrong provider (targeted token)
{"error": "This share token is for a different provider."}

// Max uses reached
{"error": "This share token has reached maximum uses."}
```

---

### 📌 Patient Endpoints

#### 1. Link Account to Patient Record
```
POST /api/patients/link-account/
```

**Description:** Link patient's account to an existing patient record.

**Authentication:** Required (Patient role only)

**Request Body:**
```json
{
  "linking_token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz"
}
```

**Response (200):**
```json
{
  "message": "Account successfully linked to patient record.",
  "patient_record": {
    "id": 1,
    "patient_unique_id": "MED-A1B2C3D4",
    "first_name": "Ahmed",
    "last_name": "Benali",
    "full_name": "Ahmed Benali",
    ...
  }
}
```

**Errors:**
```json
// Invalid token
{"error": "Invalid linking token."}

// Token already used
{"linking_token": ["This linking token has already been used."]}

// Account already linked
{"error": "Your account is already linked to a patient record."}

// User not a patient
{"error": "User must have PATIENT role to link patient records."}
```

---

#### 2. Get My Patient Record
```
GET /api/patients/me/
```

**Description:** Get the current patient's linked patient record.

**Authentication:** Required (Patient role only)

**Response (200):** Full patient record object.

**Response (404):**
```json
{"error": "No linked patient record found."}
```

---

#### 3. Get My Medical Records
```
GET /api/patients/my-records/
```

**Description:** Get the patient's own medical records.

**Authentication:** Required (Patient role only)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `record_type` | string | Filter: DIAGNOSIS, PRESCRIPTION, LAB_RESULT, etc. |
| `limit` | int | Max records (default 50, max 100) |

**Response (200):**
```json
{
  "patient_unique_id": "MED-A1B2C3D4",
  "patient_name": "Ahmed Benali",
  "count": 15,
  "records": [
    {
      "id": 1,
      "title": "Essential Hypertension",
      "record_type": "DIAGNOSIS",
      "record_date": "2024-01-10",
      "description": "Stage 1 hypertension diagnosed",
      "diagnosis_code": "I10",
      "symptoms": "Elevated BP readings",
      "is_confidential": false,
      "requires_followup": true,
      "followup_date": "2024-02-10",
      "created_at": "2024-01-10T09:30:00Z"
    }
  ]
}
```

---

#### 4. List My Share Tokens
```
GET /api/patients/share-tokens/
GET /api/patients/my-share-tokens/
```

**Description:** List all share tokens created by the patient.

**Authentication:** Required (Patient with linked record)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `active_only` | bool | Only show usable tokens |

**Response (200):**
```json
{
  "count": 3,
  "tokens": [
    {
      "id": 1,
      "token": "Xk9_mN2pQr5sT8uV1wY4zA7bC0dE3fG6hI",
      "patient_name": "Ahmed Benali",
      "patient_unique_id": "MED-A1B2C3D4",
      "access_level": "READ_ONLY",
      "expires_at": "2025-01-29T10:30:00Z",
      "max_uses": 1,
      "use_count": 0,
      "is_active": true,
      "is_revoked": false,
      "is_expired": false,
      "is_usable": true,
      "target_provider_name": null,
      "notes": "For Dr. Smith consultation",
      "qr_code_data": {
        "token": "Xk9_mN2pQr5sT8uV1wY4zA7bC0dE3fG6hI",
        "url": "https://api.medilink.com/api/patients/records/share/Xk9_mN2pQr5sT8uV1wY4zA7bC0dE3fG6hI/",
        "patient_id": "MED-A1B2C3D4",
        "expires_at": "2025-01-29T10:30:00Z"
      },
      "created_at": "2025-01-28T10:30:00Z"
    }
  ]
}
```

---

#### 5. Create Share Token
```
POST /api/patients/share-tokens/
```

**Description:** Create a new share token for sharing medical records.

**Authentication:** Required (Patient with linked record)

**Request Body:**
```json
{
  "access_level": "READ_ONLY",
  "expires_in_hours": 24,
  "max_uses": 1,
  "target_provider_id": null,
  "notes": "For Dr. Smith consultation"
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `access_level` | string | No | READ_ONLY | READ_ONLY, FULL, LIMITED |
| `expires_in_hours` | int | No | 24 | 1-720 (30 days max) |
| `max_uses` | int | No | 1 | 0-100 (0 = unlimited) |
| `target_provider_id` | int | No | null | Restrict to specific provider |
| `notes` | string | No | "" | Optional description |

**Response (201):** Same as list item above.

---

#### 6. Get Share Token Details
```
GET /api/patients/share-tokens/{id}/
```

**Description:** Get details of a specific share token.

**Authentication:** Required (Token owner only)

**Response (200):** Same as list item above.

---

#### 7. Revoke Share Token
```
POST /api/patients/share-tokens/{id}/revoke/
```

**Description:** Revoke a share token to prevent further use.

**Authentication:** Required (Token owner only)

**Response (200):**
```json
{
  "message": "Share token has been revoked.",
  "token_id": 5
}
```

---

#### 8. Get Share Token Access Logs
```
GET /api/patients/share-tokens/{id}/access-logs/
```

**Description:** View who has accessed records using this token.

**Authentication:** Required (Token owner only)

**Response (200):**
```json
{
  "token_id": 5,
  "use_count": 2,
  "logs": [
    {
      "id": 1,
      "share_token": 5,
      "accessed_by_provider_name": "Dr. Amira Hadj",
      "accessed_at": "2025-01-28T11:00:00Z",
      "ip_address": "192.168.1.100"
    },
    {
      "id": 2,
      "share_token": 5,
      "accessed_by_provider_name": "Clinique El-Hakim",
      "accessed_at": "2025-01-28T12:30:00Z",
      "ip_address": "192.168.1.105"
    }
  ]
}
```

---

## 🔄 Business Logic & Workflows

### Workflow 1: Provider Creates Patient Without Account

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Provider   │     │     API      │     │   Database   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ POST /patients/    │                    │
       │ {patient_data}     │                    │
       │───────────────────>│                    │
       │                    │                    │
       │                    │ Generate:          │
       │                    │ • patient_unique_id│
       │                    │ • linking_token    │
       │                    │                    │
       │                    │ Create Record      │
       │                    │───────────────────>│
       │                    │                    │
       │                    │ Create Access      │
       │                    │ (FULL for creator) │
       │                    │───────────────────>│
       │                    │                    │
       │   201 + record     │                    │
       │<───────────────────│                    │
       │                    │                    │
       │ GET /patients/{id}/│                    │
       │ token/             │                    │
       │───────────────────>│                    │
       │                    │                    │
       │ {linking_token}    │                    │
       │<───────────────────│                    │
       │                    │                    │
       │  Give token to     │                    │
       │  patient verbally  │                    │
       │  or printed        │                    │
```

### Workflow 2: Patient Links Account

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Patient    │     │     API      │     │   Database   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ 1. Download app    │                    │
       │ 2. Create account  │                    │
       │    (role: PATIENT) │                    │
       │                    │                    │
       │ POST /link-account/│                    │
       │ {linking_token}    │                    │
       │───────────────────>│                    │
       │                    │                    │
       │                    │ Validate:          │
       │                    │ • Token exists?    │
       │                    │ • Token used?      │
       │                    │ • Record linked?   │
       │                    │ • User is patient? │
       │                    │ • User has record? │
       │                    │───────────────────>│
       │                    │                    │
       │                    │ Update:            │
       │                    │ • linked_user      │
       │                    │ • token_used=true  │
       │                    │ • token_used_at    │
       │                    │───────────────────>│
       │                    │                    │
       │  200 + record      │                    │
       │<───────────────────│                    │
```

### Workflow 3: Patient Shares Records via QR Code

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Patient    │     │     API      │     │  Provider    │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ POST /share-tokens/│                    │
       │ {access_level,     │                    │
       │  expires_in_hours} │                    │
       │───────────────────>│                    │
       │                    │                    │
       │ 201 + token +      │                    │
       │ qr_code_data       │                    │
       │<───────────────────│                    │
       │                    │                    │
       │ Display QR code    │                    │
       │ on phone screen    │                    │
       │ ~~~~~~~~~~~~~~~~>  │                    │
       │                    │                    │
       │                    │     Scan QR code   │
       │                    │<~~~~~~~~~~~~~~~~~~ │
       │                    │                    │
       │                    │ GET /records/share/│
       │                    │ {token}/           │
       │                    │<───────────────────│
       │                    │                    │
       │                    │ Validate token     │
       │                    │ Record usage       │
       │                    │ Log access         │
       │                    │                    │
       │                    │ 200 + patient_data │
       │                    │ + medical_records  │
       │                    │───────────────────>│
```

### Workflow 4: Provider Refers Patient to Another Provider

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Provider A  │     │     API      │     │  Provider B  │
│  (Creator)   │     │              │     │  (Referred)  │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       │ POST /patients/    │                    │
       │ {id}/grant-access/ │                    │
       │ {provider_id: B,   │                    │
       │  access: READ_ONLY}│                    │
       │───────────────────>│                    │
       │                    │                    │
       │ 201 + access       │                    │
       │<───────────────────│                    │
       │                    │                    │
       │  Notify Provider B │                    │
       │  (out of band)     ├───────────────────>│
       │                    │                    │
       │                    │ GET /patients/     │
       │                    │<───────────────────│
       │                    │                    │
       │                    │ [patient in list]  │
       │                    │───────────────────>│
       │                    │                    │
       │                    │ GET /patients/{id}/│
       │                    │ history/           │
       │                    │<───────────────────│
       │                    │                    │
       │                    │ full medical hist. │
       │                    │───────────────────>│
```

---

## 🔐 Permission System

### Permission Classes

| Class | Description | Checks |
|-------|-------------|--------|
| `IsVerifiedProvider` | User is an approved provider | is_authenticated, role=PROVIDER, provider.is_approved |
| `CanAccessPatientRecord` | User can access specific patient | is_linked_patient OR is_creator OR has_access_grant OR is_admin |
| `CanModifyPatientRecord` | User can modify patient record | is_creator OR has_FULL_access OR is_admin |
| `CanLinkPatientAccount` | User can link account | is_authenticated, role=PATIENT, can_login |

### Access Decision Matrix

```
                    ┌─────────┬───────────┬───────────┬───────────┐
                    │ Creator │ Has Access│ Is Patient│ Is Admin  │
┌───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ View Record       │    ✅   │     ✅    │ ✅ (own)  │    ✅     │
├───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ Update Record     │    ✅   │ ✅ (FULL) │    ❌     │    ✅     │
├───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ Delete Record     │    ✅   │ ✅ (FULL) │    ❌     │    ✅     │
├───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ Get Token         │    ✅   │ ✅ (FULL) │    ❌     │    ✅     │
├───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ Regenerate Token  │    ✅   │    ❌     │    ❌     │    ✅     │
├───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ Grant Access      │    ✅   │ ✅ (FULL) │    ❌     │    ✅     │
├───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ Create Share Token│    ❌   │    ❌     │ ✅ (linked)│   ❌     │
├───────────────────┼─────────┼───────────┼───────────┼───────────┤
│ Use Share Token   │    ✅   │    ✅     │    ❌     │    ❌     │
└───────────────────┴─────────┴───────────┴───────────┴───────────┘
```

---

## 📈 Dashboard Integration

### Provider Dashboard Widgets

#### 1. Patient Statistics
```json
{
  "total_patients": 142,
  "linked_patients": 89,
  "unlinked_patients": 53,
  "patients_this_month": 12,
  "patients_by_gender": {
    "MALE": 68,
    "FEMALE": 72,
    "OTHER": 2
  }
}
```

#### 2. Recent Patients
```
GET /api/patients/?ordering=-created_at&limit=5
```

#### 3. Patients Needing Follow-up
```
GET /api/patients/?has_pending_followup=true
```

### Patient Dashboard Widgets

#### 1. My Health Summary
```
GET /api/patients/me/
```

#### 2. My Medical Records
```
GET /api/patients/my-records/?limit=10
```

#### 3. Active Share Tokens
```
GET /api/patients/share-tokens/?active_only=true
```

#### 4. Recent Access History
```
GET /api/patients/share-tokens/{id}/access-logs/
```

---

## ⚠️ Error Codes Reference

| HTTP Code | Scenario | Response |
|-----------|----------|----------|
| 200 | Success | Data returned |
| 201 | Created | New resource returned |
| 204 | Deleted | No content |
| 400 | Validation error | `{"field": ["error message"]}` |
| 401 | Not authenticated | `{"detail": "Authentication credentials were not provided."}` |
| 403 | No permission | `{"error": "You do not have permission..."}` |
| 404 | Not found | `{"error": "Patient record not found."}` |
| 500 | Server error | `{"error": "Internal server error."}` |

---

## 📱 QR Code Generation (Frontend)

The `qr_code_data` object contains everything needed:

```javascript
// Using qrcode.js
import QRCode from 'qrcode';

const response = await api.post('/patients/share-tokens/', {
  access_level: 'READ_ONLY',
  expires_in_hours: 24
});

const { qr_code_data } = response.data;

// Generate QR code image
const qrImage = await QRCode.toDataURL(qr_code_data.url);
document.getElementById('qr').src = qrImage;

// Display expiry countdown
const expiresAt = new Date(qr_code_data.expires_at);
const timeLeft = expiresAt - new Date();
console.log(`Expires in: ${Math.round(timeLeft / 3600000)} hours`);
```

---

## 🔧 Configuration Options

### Share Token Limits

| Setting | Value | Description |
|---------|-------|-------------|
| Min expiry | 1 hour | Minimum token lifetime |
| Max expiry | 720 hours | Maximum token lifetime (30 days) |
| Default expiry | 24 hours | Default if not specified |
| Max uses limit | 0-100 | 0 = unlimited |
| Default max uses | 1 | Single use by default |

### Patient Identifier Format

- Format: `MED-XXXXXXXX`
- Prefix: `MED-`
- Length: 8 uppercase alphanumeric characters
- Example: `MED-A1B2C3D4`

---

## 📊 Audit & Compliance

### Tracked Events

| Event | Data Logged |
|-------|-------------|
| Patient Created | provider_id, timestamp, patient_unique_id |
| Patient Updated | user_id, timestamp, changed_fields |
| Patient Deleted | user_id, timestamp, reason |
| Account Linked | user_id, patient_unique_id, timestamp |
| Access Granted | granting_provider, receiving_provider, access_level |
| Share Token Created | patient_id, access_level, expiry, target_provider |
| Share Token Used | provider_id, token_id, ip_address, timestamp |
| Share Token Revoked | patient_id, token_id, timestamp |

---

*Document Version: 2.0*
*Last Updated: January 28, 2026*
*Medilink Healthcare Platform*
