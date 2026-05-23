# Medical Dossier — Patient App Integration Guide

**Base URL:** `/api/medical-records/`  
**Auth:** `Authorization: Token <token>` on all requests  
**Role required:** `PATIENT`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Supported Record Types](#2-supported-record-types)
3. [My Folder (Structured Dashboard)](#3-my-folder-structured-dashboard)
4. [My Health Data (Full Bundle)](#4-my-health-data-full-bundle)
5. [Browsing Records (Paginated List)](#5-browsing-records-paginated-list)
6. [Record Detail](#6-record-detail)
7. [Creating a Record (Self-Entered)](#7-creating-a-record-self-entered)
8. [Updating a Record](#8-updating-a-record)
9. [Deactivating (Archiving) a Record](#9-deactivating-archiving-a-record)
10. [Attachments — Upload & View](#10-attachments--upload--view)
11. [Notes — Add & View](#11-notes--add--view)
12. [Access Audit Log](#12-access-audit-log)
13. [Export as PDF](#13-export-as-pdf)
14. [Who Has Access to My Records](#14-who-has-access-to-my-records)
15. [Grant / Revoke Provider Access](#15-grant--revoke-provider-access)
16. [Field Reference](#16-field-reference)
17. [Feature Gaps vs. Landing Page](#17-feature-gaps-vs-landing-page)

---

## 1. Overview

A patient's medical dossier is built from **medical records**, each representing a distinct clinical event (a diagnosis, an allergy, a lab result, an imaging study, a prescription, a vaccination, etc.).

Records are created either by the patient themselves or by providers after a consultation or nursing visit. Patients can read all their records, write patient-type notes, upload attachments, and control which providers can access the folder.

Patients with no Medilink account are supported via `PatientRecord` (identifier format `MED-XXXXXX`); if they later create an account and link their patient record, all historical records become accessible under their account.

---

## 2. Supported Record Types

| `record_type` | Display |
|---|---|
| `DIAGNOSIS` | Diagnosis |
| `PRESCRIPTION` | Prescription |
| `ALLERGY` | Allergy |
| `LAB_RESULT` | Lab Result |
| `IMAGING` | Imaging Study |
| `PROCEDURE` | Procedure |
| `NOTE` | General Note |
| `VACCINATION` | Vaccination |
| `OTHER` | Other |

**Severity levels** (`severity_level`):

| Value | Meaning |
|---|---|
| `CRITICAL` | Requires immediate attention |
| `HIGH` | Significant risk |
| `MEDIUM` | Standard clinical significance (default) |
| `LOW` | Minor / informational |
| `INFO` | Purely informational |

---

## 3. My Folder (Structured Dashboard)

Returns the patient's complete medical dossier in a structured format: demographics, a full timeline, records grouped by type and custom folder, active allergies, pending follow-ups, and recent activity.

```
GET /api/medical-records/records/my-folder/
```

### Response shape

```json
{
  "generated_at": "2026-05-11T10:00:00Z",
  "patient": {
    "id": "42",
    "email": "patient@example.com",
    "full_name": "Ahmed Mansouri",
    "date_of_birth": "1990-03-15",
    "age": 36,
    "gender": "MALE",
    "blood_type": "O+",
    "known_allergies": "Penicillin",
    "chronic_conditions": "Type 2 Diabetes",
    "current_medications": "Metformin 500mg",
    "emergency_contact_name": "Sara Mansouri",
    "emergency_contact_phone": "+213 555 0001",
    "patient_unique_id": "MED-123456"
  },
  "summary": {
    "total_records": 14,
    "active_allergies": 2,
    "pending_followups": 1,
    "critical_or_high": 3,
    "recent_30_days": 4,
    "record_types": {
      "DIAGNOSIS": 5,
      "LAB_RESULT": 3,
      "ALLERGY": 2,
      "PRESCRIPTION": 2,
      "IMAGING": 1,
      "VACCINATION": 1
    }
  },
  "medical_records": {
    "timeline": [ /* MedicalRecordDetail objects, newest first */ ],
    "by_type": {
      "DIAGNOSIS": [ /* records */ ],
      "LAB_RESULT": [ /* records */ ]
    },
    "by_folder": {
      "Cardiology": [ /* records */ ],
      "General": [ /* records */ ]
    },
    "critical_or_high": [ /* records with severity CRITICAL or HIGH */ ],
    "recent_30_days": [ /* records from the last 30 days */ ],
    "pending_followups": [ /* records where requires_followup=true and followup_date is set */ ]
  },
  "active_allergies": [ /* records where record_type=ALLERGY */ ]
}
```

**Notes:**
- `patient` demographics come from the linked `PatientRecord` if available; otherwise only `id` and `email` are returned.
- `patient_unique_id` is only present if a `PatientRecord` exists.
- All records in `timeline` are active (`is_active=true`), ordered by `record_date` descending.

---

## 4. My Health Data (Full Bundle)

A comprehensive health bundle that includes medical records **plus** data from other apps: prescriptions (from the prescriptions app), appointment history, nurse request history, and provider access grants.

```
GET /api/medical-records/records/my-health-data/
```

### Response shape

```json
{
  "generated_at": "2026-05-11T10:00:00Z",
  "patient": { "id": "42", "email": "patient@example.com" },
  "summary": {
    "total_records": 14,
    "critical_or_high": 3,
    "recent_30_days": 4,
    "pending_followups": 1,
    "prescriptions": 5,
    "appointments": 8,
    "nurse_requests": 2,
    "provider_access_grants": 3
  },
  "medical_records": {
    "timeline": [ /* MedicalRecordList objects */ ],
    "by_type": { "DIAGNOSIS": [ /* ... */ ] },
    "by_folder": { "Cardiology": [ /* ... */ ] },
    "recent_30_days": [ /* ... */ ],
    "critical_or_high_priority": [ /* ... */ ],
    "pending_followups": [ /* ... */ ]
  },
  "prescriptions": [
    {
      "id": "uuid",
      "reference_number": "RX-2026-001",
      "status": "ACTIVE",
      "valid_until": "2026-11-01",
      "issued_at": "2026-05-01T09:00:00Z",
      "created_at": "2026-05-01T09:00:00Z",
      "doctor_name": "Dr. Karim Benali",
      "clinic_name": "Clinique El Shifa",
      "items": [
        {
          "id": "uuid",
          "medication_name": "Metformin",
          "dosage": "500mg",
          "frequency": "twice daily",
          "duration_days": 30,
          "duration_text": "1 month",
          "instructions": "Take with meals"
        }
      ]
    }
  ],
  "appointments": [
    {
      "id": "uuid",
      "status": "COMPLETED",
      "appointment_date": "2026-04-20",
      "appointment_time": "10:00:00",
      "created_at": "2026-04-15T08:00:00Z"
    }
  ],
  "nurse_requests": [
    {
      "id": 7,
      "status": "COMPLETED",
      "service_title": "Post-operative care",
      "city": "Algiers",
      "final_price": "3500.00",
      "created_at": "2026-04-28T14:00:00Z",
      "completed_at": "2026-04-28T16:00:00Z"
    }
  ],
  "provider_access": [ /* ProviderAccess objects — see Section 14 */ ]
}
```

**Use this endpoint** for the app's main health overview screen. Use `my-folder` if you only need the medical records section with groupings.

---

## 5. Browsing Records (Paginated List)

```
GET /api/medical-records/records/my-records/
```

Returns active records belonging to the patient, paginated. Supports filtering and search.

### Query parameters

| Parameter | Type | Description |
|---|---|---|
| `record_type` | string | Filter: `DIAGNOSIS`, `LAB_RESULT`, `IMAGING`, `PRESCRIPTION`, `ALLERGY`, `VACCINATION`, `PROCEDURE`, `NOTE`, `OTHER` |
| `severity_level` | string | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO` |
| `requires_followup` | boolean | Filter: `true` or `false` |
| `folder_name` | string | Filter by custom folder name |
| `is_active` | boolean | Default `true`; pass `false` to see archived records |
| `search` | string | Full-text search across `title`, `description`, `symptoms`, `diagnosis_code` |
| `ordering` | string | `record_date`, `-record_date`, `created_at`, `-created_at`, `severity_level` |
| `page` | int | Page number |

### List item shape

```json
{
  "id": 101,
  "title": "Blood glucose test",
  "record_type": "LAB_RESULT",
  "record_type_display": "Lab Result",
  "record_date": "2026-05-01",
  "patient_email": "patient@example.com",
  "patient_name": "Ahmed Mansouri",
  "patient_record_id": null,
  "created_by_email": "dr.benali@example.com",
  "created_by_name": "Dr. Karim Benali",
  "is_active": true,
  "is_confidential": false,
  "requires_followup": false,
  "followup_date": null,
  "folder_name": "Endocrinology",
  "severity_level": "MEDIUM",
  "severity_display": "Medium",
  "sequence_number": 14,
  "has_prescription": false,
  "has_allergy": false,
  "attachment_count": 1,
  "note_count": 2,
  "created_at": "2026-05-01T10:30:00Z",
  "updated_at": "2026-05-01T10:30:00Z"
}
```

---

## 6. Record Detail

```
GET /api/medical-records/records/{id}/
```

Fetches the full record including embedded prescription, allergy, attachments, and notes. **Every call to this endpoint creates a `VIEW` entry in the access audit log.**

### Detail shape (additional fields beyond the list shape)

```json
{
  "id": 101,
  "patient": 42,
  "patient_email": "patient@example.com",
  "patient_name": "Ahmed Mansouri",
  "patient_record_id": null,
  "patient_unique_id": null,
  "title": "Penicillin allergy",
  "record_type": "ALLERGY",
  "record_type_display": "Allergy",
  "diagnosis_code": "",
  "description": "Severe allergic reaction to penicillin antibiotics",
  "symptoms": "Rash, hives, throat swelling",
  "record_date": "2020-06-15",
  "created_by": 8,
  "created_by_email": "dr.benali@example.com",
  "created_by_name": "Dr. Karim Benali",
  "updated_by": 8,
  "updated_by_email": "dr.benali@example.com",
  "is_active": true,
  "is_confidential": false,
  "requires_followup": false,
  "followup_date": null,
  "folder_name": "Allergies",
  "severity_level": "HIGH",
  "severity_display": "High",
  "sequence_number": 3,
  "timeline_order": 0,
  "created_at": "2026-04-01T08:00:00Z",
  "updated_at": "2026-04-01T08:00:00Z",
  "prescription": null,
  "allergy": {
    "id": 5,
    "allergen": "Penicillin",
    "severity": "SEVERE",
    "reaction": "Anaphylaxis, hives, throat swelling",
    "first_observed": "2020-06-15"
  },
  "attachments": [],
  "notes": [
    {
      "id": 12,
      "note_type": "PROVIDER",
      "content": "Patient confirmed allergy. Avoid all beta-lactam antibiotics.",
      "created_by_email": "dr.benali@example.com",
      "created_by_role": "PROVIDER",
      "created_at": "2026-04-01T08:05:00Z",
      "updated_at": "2026-04-01T08:05:00Z",
      "is_locked": true
    }
  ]
}
```

**Embedded sub-objects:**

- `prescription` — present only when `record_type = PRESCRIPTION`. Fields: `medication_name`, `dosage`, `frequency`, `duration`, `instructions`, `quantity`, `refills`.
- `allergy` — present only when `record_type = ALLERGY`. Fields: `allergen`, `severity` (`MILD`/`MODERATE`/`SEVERE`/`LIFE_THREATENING`), `reaction`, `first_observed`.
- `attachments` — array; may be empty.
- `notes` — array; may be empty.

---

## 7. Creating a Record (Self-Entered)

Patients can self-enter health events (personal notes, allergies they are aware of, vaccination history, etc.).

```
POST /api/medical-records/records/
Content-Type: application/json
```

### Request body

```json
{
  "title": "Flu vaccination",
  "record_type": "VACCINATION",
  "description": "Seasonal flu vaccine (Influenza quadrivalent)",
  "symptoms": "",
  "record_date": "2026-10-05",
  "severity_level": "INFO",
  "folder_name": "Vaccinations",
  "requires_followup": false,
  "is_confidential": false,
  "sequence_number": null
}
```

For an allergy record, include an `allergy` block:

```json
{
  "title": "Aspirin hypersensitivity",
  "record_type": "ALLERGY",
  "description": "Aspirin causes stomach upset and rash",
  "record_date": "2024-01-10",
  "severity_level": "MEDIUM",
  "allergy": {
    "allergen": "Aspirin",
    "severity": "MODERATE",
    "reaction": "Stomach upset, skin rash",
    "first_observed": "2024-01-10"
  }
}
```

For a prescription record (self-entered, e.g., tracking an OTC medication), include a `prescription` block:

```json
{
  "title": "Ibuprofen self-medication",
  "record_type": "PRESCRIPTION",
  "description": "Self-prescribed ibuprofen for lower back pain",
  "record_date": "2026-05-08",
  "severity_level": "LOW",
  "prescription": {
    "medication_name": "Ibuprofen",
    "dosage": "400mg",
    "frequency": "three times daily with food",
    "duration": "5 days",
    "quantity": 15,
    "refills": 0
  }
}
```

**Validation rules:**
- `record_date` is required.
- `requires_followup: true` requires `followup_date` (must be today or future).
- Patients cannot set `record_type` to values that imply a clinical provider (this is not enforced at API level — providers create those via their own flow).
- Patients cannot modify `diagnosis_code` or `record_type` on records created by a provider.

### 201 Response

Returns the full `MedicalRecordDetail` shape (see Section 6).

---

## 8. Updating a Record

```
PATCH /api/medical-records/records/{id}/
Content-Type: application/json
```

All fields are optional (partial update). Patients cannot change `diagnosis_code` or `record_type` on records created by a provider.

```json
{
  "title": "Flu vaccine 2026 — Booster",
  "folder_name": "Vaccinations",
  "severity_level": "INFO",
  "requires_followup": true,
  "followup_date": "2027-10-01"
}
```

To update the embedded allergy on an existing allergy record:

```json
{
  "allergy": {
    "severity": "LIFE_THREATENING",
    "reaction": "Anaphylactic shock requiring epinephrine"
  }
}
```

Returns the updated `MedicalRecordDetail`.

---

## 9. Deactivating (Archiving) a Record

Records are never hard-deleted. Deleting sets `is_active = false`.

```
DELETE /api/medical-records/records/{id}/
```

**200 OK**:
```json
{ "message": "Medical record deactivated." }
```

To view archived records, pass `?is_active=false` to the list endpoint.

---

## 10. Attachments — Upload & View

### List attachments on a record

```
GET /api/medical-records/records/{id}/attachments/
```

```json
[
  {
    "id": 33,
    "file": "https://api.medilink.dz/media/medical_records/attachments/2026/05/01/labresult.pdf",
    "file_name": "labresult.pdf",
    "file_type": "application/pdf",
    "file_size": 204800,
    "description": "Full blood count results",
    "uploaded_by_email": "patient@example.com",
    "uploaded_at": "2026-05-01T11:00:00Z"
  }
]
```

### Upload an attachment

```
POST /api/medical-records/records/{id}/attachments/
Content-Type: multipart/form-data
```

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | Yes | Binary file (PDF, JPEG, PNG, DICOM, etc.) |
| `file_name` | string | Yes | Original file name |
| `file_type` | string | No | MIME type (e.g., `application/pdf`) |
| `file_size` | integer | No | File size in bytes |
| `description` | string | No | What the file contains |

**201 Created** — returns the attachment object.

---

## 11. Notes — Add & View

### List notes on a record

```
GET /api/medical-records/records/{id}/notes/
```

```json
[
  {
    "id": 22,
    "note_type": "PATIENT",
    "content": "Started feeling better on day 3",
    "created_by_email": "patient@example.com",
    "created_by_role": "PATIENT",
    "created_at": "2026-05-02T09:00:00Z",
    "updated_at": "2026-05-02T09:00:00Z",
    "is_locked": false
  },
  {
    "id": 23,
    "note_type": "PROVIDER",
    "content": "Follow up in 2 weeks if symptoms persist",
    "created_by_email": "dr.benali@example.com",
    "created_by_role": "PROVIDER",
    "created_at": "2026-05-01T10:30:00Z",
    "updated_at": "2026-05-01T10:30:00Z",
    "is_locked": true
  }
]
```

### Add a patient note

```
POST /api/medical-records/records/{id}/notes/
Content-Type: application/json
```

```json
{
  "note_type": "PATIENT",
  "content": "Noticed mild dizziness when taking medication on an empty stomach"
}
```

**Rules:**
- Patients can only create `PATIENT`-type notes; sending `note_type: "PROVIDER"` returns a 400 error.
- Provider notes (`is_locked: true`) cannot be modified by patients.

**201 Created** — returns the created note object.

---

## 12. Access Audit Log

View every access event (view, create, update, delete, PDF export) on a specific record.

```
GET /api/medical-records/records/{id}/access-logs/
```

**Only accessible to the owning patient or admins.**

```json
[
  {
    "id": 88,
    "accessed_by_email": "dr.benali@example.com",
    "accessed_by_role": "PROVIDER",
    "access_type": "VIEW",
    "ip_address": "102.158.12.45",
    "accessed_at": "2026-05-10T14:22:00Z"
  },
  {
    "id": 87,
    "accessed_by_email": "dr.benali@example.com",
    "accessed_by_role": "PROVIDER",
    "access_type": "CREATE",
    "ip_address": "102.158.12.45",
    "accessed_at": "2026-04-30T09:00:00Z"
  }
]
```

`access_type` values: `VIEW`, `CREATE`, `UPDATE`, `DELETE`, `PDF_EXPORT`.

---

## 13. Export as PDF

### Export a single record

```
GET /api/medical-records/records/{id}/export-pdf/
GET /api/medical-records/records/{id}/export-pdf/?include_attachments=true
```

Returns a PDF file (`Content-Type: application/pdf`).  
**Requires `reportlab` to be installed** on the server. If not available, returns `503 Service Unavailable`.

### Export full medical summary

```
GET /api/medical-records/records/export-summary/
```

Exports all of the patient's active records as a single summary PDF. Patient-only endpoint.

**Note:** Both export endpoints log a `PDF_EXPORT` entry in the access audit log.

---

## 14. Who Has Access to My Records

```
GET /api/medical-records/access/my-providers/
```

Returns all providers who have (or previously had) an access grant for the patient's records, including revoked/expired ones.

```json
[
  {
    "id": 5,
    "patient": 42,
    "patient_email": "patient@example.com",
    "patient_name": "Ahmed Mansouri",
    "provider": 3,
    "provider_email": "dr.benali@example.com",
    "provider_name": "Dr. Karim Benali",
    "provider_type": "DOCTOR",
    "access_type": "READ_ONLY",
    "access_type_display": "Read Only",
    "granted_at": "2026-03-10T08:00:00Z",
    "expires_at": "2027-03-10T08:00:00Z",
    "is_active": true,
    "is_expired": false,
    "is_valid": true,
    "reason": "Regular follow-up care"
  }
]
```

`access_type` values:

| Value | Meaning |
|---|---|
| `FULL` | Provider can read all records including confidential ones and write new records |
| `READ_ONLY` | Provider can read all records including confidential ones, but cannot create |
| `LIMITED` | Provider can read non-confidential records only |

---

## 15. Grant / Revoke Provider Access

### Grant access to a provider

```
POST /api/medical-records/access/
Content-Type: application/json
```

```json
{
  "provider_id": 3,
  "access_type": "READ_ONLY",
  "expires_at": "2027-05-11T00:00:00Z",
  "reason": "Long-term diabetes management"
}
```

- `provider_id` — integer ID of the provider (must be `APPROVED`).
- `access_type` — `FULL`, `READ_ONLY` (default), or `LIMITED`.
- `expires_at` — ISO 8601 datetime, optional (null = permanent).
- `reason` — optional text.

If a grant already exists for this provider (e.g., previously revoked), it is **reactivated** with the new terms instead of creating a duplicate.

**201 / 200 Created** — returns the `ProviderAccess` object.

### Revoke access

```
POST /api/medical-records/access/{id}/revoke/
```

```json
{ "message": "Provider access revoked.", "access": { /* ProviderAccess object */ } }
```

### Renew (reactivate) a revoked grant

```
POST /api/medical-records/access/{id}/renew/
Content-Type: application/json
```

```json
{ "expires_at": "2028-01-01T00:00:00Z" }
```

`expires_at` is optional — omit it to grant permanent access.

---

## 16. Field Reference

### MedicalRecord core fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Record PK |
| `title` | string | Summary title |
| `record_type` | string | See Section 2 |
| `record_date` | date | When the event occurred |
| `description` | string | Full description |
| `symptoms` | string | Symptoms at the time |
| `diagnosis_code` | string | ICD-10 code (provider-set) |
| `severity_level` | string | `CRITICAL`/`HIGH`/`MEDIUM`/`LOW`/`INFO` |
| `folder_name` | string | Custom folder label (e.g., "Cardiology") |
| `is_confidential` | boolean | Hidden from LIMITED-access providers |
| `requires_followup` | boolean | Flags a required follow-up |
| `followup_date` | date | Required if `requires_followup=true` |
| `sequence_number` | integer | Manual ordering within the patient's timeline |
| `timeline_order` | integer | Numeric sort key for timeline display |
| `is_active` | boolean | `false` = archived/deleted |

### Allergy severity values

| Value | Meaning |
|---|---|
| `MILD` | Minor reaction |
| `MODERATE` | Noticeable but manageable |
| `SEVERE` | Significant health impact |
| `LIFE_THREATENING` | Anaphylaxis / requires emergency care |

---

## 17. Feature Gaps vs. Landing Page

The following features are advertised on the landing page but **are not yet implemented** in the backend. No endpoints exist for these — do not attempt to call them.

| Landing Page Feature | Status | Notes |
|---|---|---|
| **Vital signs / biometric curves** (blood pressure, glucose, weight trend) | ❌ Not implemented | No `VitalSign` model. Only static text fields on `PatientRecord` (e.g., `known_allergies`, `chronic_conditions`). |
| **Drug interaction checking** | ❌ Not implemented | Allergies are recorded but there is no interaction checker service. |
| **Vaccination schedule / dose tracking** | ⚠️ Partial | Records with `record_type=VACCINATION` can be created, but there is no dedicated model for dose number, schedule, or booster tracking. |
| **Home nursing visit history** | ✅ Available | Available via `my-health-data` under `nurse_requests`. |
| **Lab results with trend data** | ⚠️ Partial | Lab results can be stored as `LAB_RESULT` records with attachments. No built-in trend/graph data structure — the app must derive trends from repeated records. |
| **Medical imaging reports** | ⚠️ Partial | `IMAGING` record type exists; DICOM files can be uploaded as attachments. No DICOM viewer integration. |
| **Active prescriptions** | ✅ Available | Via `my-health-data.prescriptions` (from the prescriptions app) and via records with `record_type=PRESCRIPTION`. |
| **Clinical notes** | ✅ Available | Via record notes (`/notes/`) with `note_type=PROVIDER` or `PATIENT`. |
| **Uploaded documents** | ✅ Available | Via record attachments (`/attachments/`). |
| **Medical history** | ✅ Available | Via records with `record_type=DIAGNOSIS`, `PROCEDURE`. |
| **Allergy records** | ✅ Available | Via records with `record_type=ALLERGY` and embedded `allergy` object. |
| **Access control** | ✅ Available | Full grant/revoke flow via `ProviderAccess`. |
| **PDF export** | ✅ Available | Requires `reportlab` installed on server. |
