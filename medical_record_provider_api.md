# Medical Dossier — Provider App Integration Guide

**Base URL:** `/api/medical-records/`  
**Auth:** `Authorization: Token <token>` on all requests  
**Role required:** `PROVIDER` (approved) — specific access level noted per endpoint  
**Also relevant:** `ADMIN` (full access, no grant required)

---

## Table of Contents

1. [Access Control Overview](#1-access-control-overview)
2. [Access Types and What They Allow](#2-access-types-and-what-they-allow)
3. [How a Provider Gets Access](#3-how-a-provider-gets-access)
4. [Patient Folder (Full Structured View)](#4-patient-folder-full-structured-view)
5. [Patient Records List (Paginated)](#5-patient-records-list-paginated)
6. [Record Detail](#6-record-detail)
7. [Creating a Record for a Patient](#7-creating-a-record-for-a-patient)
8. [Updating a Record](#8-updating-a-record)
9. [Deactivating a Record](#9-deactivating-a-record)
10. [Attachments — Upload & View](#10-attachments--upload--view)
11. [Clinical Notes — Add & View](#11-clinical-notes--add--view)
12. [Export Patient Record as PDF](#12-export-patient-record-as-pdf)
13. [My Authorized Patients](#13-my-authorized-patients)
14. [Managing Your Own Access Grant (Admin / Specialized Flows)](#14-managing-your-own-access-grant-admin--specialized-flows)
15. [Access Granted Automatically (Nurse Requests)](#15-access-granted-automatically-nurse-requests)
16. [Field Reference](#16-field-reference)
17. [Error Codes](#17-error-codes)
18. [Feature Gaps vs. Landing Page](#18-feature-gaps-vs-landing-page)

---

## 1. Access Control Overview

Providers do **not** have blanket access to all patient records. Access is controlled per `(provider, patient)` pair through `ProviderAccess` grants.

A provider can see a patient's records only if at least one of the following is true:

1. An active, non-expired `ProviderAccess` grant exists for this (provider, patient) pair.
2. A legacy `ProviderPatientAccess` grant exists (created automatically when a nurse request is accepted — treated as `READ_ONLY`).

If neither exists, all provider-facing endpoints return `403 Forbidden`.

**Confidential records:** Records marked `is_confidential=true` are hidden from providers with `LIMITED` access. Providers with `FULL` or `READ_ONLY` access see them.

---

## 2. Access Types and What They Allow

| Access Type | Read Records | Read Confidential | Create Records | Update Records |
|---|---|---|---|---|
| `FULL` | ✅ | ✅ | ✅ | ✅ |
| `READ_ONLY` | ✅ | ✅ | ❌ | ❌ |
| `LIMITED` | ✅ (non-confidential only) | ❌ | ❌ | ❌ |

**Important:** Doctors typically receive `FULL` access. Nurses accepted on a nurse request receive `READ_ONLY` (via the automatic legacy grant). Patients can grant any access type manually.

---

## 3. How a Provider Gets Access

### Option A — Patient grants access manually

The patient posts to `POST /api/medical-records/access/` with the provider's ID.  
See the Patient API guide for the patient side of this flow.

### Option B — Automatic grant on nurse request acceptance

When a patient accepts a nurse's offer, the system automatically creates a `ProviderPatientAccess` entry (legacy model). This gives the nurse `READ_ONLY`-equivalent access to the patient's folder for the duration of the request.

No action is needed from the provider; access is available as soon as the request moves to `ACCEPTED` status.

### Option C — Admin grant

An admin can POST to `POST /api/medical-records/access/` supplying both `provider_id` and `patient_id`.

---

## 4. Patient Folder (Full Structured View)

The primary endpoint for viewing a patient's complete medical dossier. Returns demographics, grouped records, allergies, and pending follow-ups in a single response.

```
GET /api/medical-records/records/patient-folder/{patient_id}/
```

`patient_id` is the integer user ID of the patient (a `PATIENT`-role user).

**Requires:** Active `ProviderAccess` grant or legacy `ProviderPatientAccess` grant.  
**403 returned** if no valid grant exists.

### Response shape

```json
{
  "generated_at": "2026-05-11T10:00:00Z",
  "access_type": "READ_ONLY",
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
    "pending_followups": [ /* records with requires_followup=true */ ]
  },
  "active_allergies": [ /* full detail of allergy-type records */ ]
}
```

**`access_type` field:** Tells the app what level of access the current provider has (`FULL`, `READ_ONLY`, `LIMITED`, or `null` for admins). Use this to decide which UI controls to show (e.g., hide the "Add record" button for `READ_ONLY`).

**`patient` demographics:** Comes from the linked `PatientRecord` if available. If the patient has no linked record, only `id` and `email` are returned.

---

## 5. Patient Records List (Paginated)

```
GET /api/medical-records/records/patient/{patient_id}/
```

Returns a paginated list of records for the specified patient. Supports the same filters as the patient's own `my-records` endpoint.

**Requires:** Active access grant.

### Query parameters

| Parameter | Type | Description |
|---|---|---|
| `record_type` | string | `DIAGNOSIS`, `LAB_RESULT`, `IMAGING`, `PRESCRIPTION`, `ALLERGY`, `VACCINATION`, `PROCEDURE`, `NOTE`, `OTHER` |
| `severity_level` | string | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO` |
| `requires_followup` | boolean | `true`/`false` |
| `folder_name` | string | Filter by custom folder |
| `is_active` | boolean | Default: all; pass `true` for active only |
| `search` | string | Search `title`, `description`, `symptoms`, `diagnosis_code` |
| `ordering` | string | `record_date`, `-record_date`, `created_at`, `severity_level` |
| `page` | int | Page number |

### List item shape

Same as the patient list item (Section 5 of the Patient API guide). Key fields:

```json
{
  "id": 101,
  "title": "Post-op wound check",
  "record_type": "PROCEDURE",
  "record_type_display": "Procedure",
  "record_date": "2026-04-28",
  "severity_level": "MEDIUM",
  "severity_display": "Medium",
  "folder_name": "Surgery",
  "has_prescription": false,
  "has_allergy": false,
  "attachment_count": 2,
  "note_count": 1,
  "created_by_name": "Dr. Karim Benali",
  "is_confidential": false,
  "requires_followup": true,
  "followup_date": "2026-05-12"
}
```

---

## 6. Record Detail

```
GET /api/medical-records/records/{id}/
```

Fetches the full record. **Every call creates a `VIEW` entry in the access audit log** — the patient can see this in their access log.

**Requires:** Active access grant for the record's patient.  
**Confidential records:** Returned only if the provider has `FULL` or `READ_ONLY` access (not `LIMITED`).

Response shape: same as Section 6 of the Patient API guide (full detail with embedded `prescription`, `allergy`, `attachments`, `notes`).

---

## 7. Creating a Record for a Patient

Providers with `FULL` access can create records directly linked to a patient's dossier. This is the primary flow for documenting consultations, lab deliveries, and imaging reports.

```
POST /api/medical-records/records/
Content-Type: application/json
```

**Requires:** `FULL` access grant for the patient.

### Request body

```json
{
  "patient": 42,
  "title": "HbA1c blood test",
  "record_type": "LAB_RESULT",
  "diagnosis_code": "E11",
  "description": "Glycated hemoglobin result: 7.2% (target <7%)",
  "symptoms": "Fatigue reported",
  "record_date": "2026-05-10",
  "severity_level": "MEDIUM",
  "folder_name": "Endocrinology",
  "requires_followup": true,
  "followup_date": "2026-08-10",
  "is_confidential": false
}
```

For a patient without an account (offline patient), use `patient_record_id` instead of `patient`:

```json
{
  "patient_record_id": 15,
  "title": "Post-surgery wound assessment",
  "record_type": "PROCEDURE",
  "description": "Wound healing well, no signs of infection",
  "record_date": "2026-05-10",
  "severity_level": "LOW"
}
```

### Creating a record with an embedded allergy

```json
{
  "patient": 42,
  "title": "New allergy identified — Sulfonamides",
  "record_type": "ALLERGY",
  "description": "Patient developed rash after sulfonamide antibiotic course",
  "record_date": "2026-05-08",
  "severity_level": "HIGH",
  "is_confidential": false,
  "allergy": {
    "allergen": "Sulfonamides",
    "severity": "SEVERE",
    "reaction": "Widespread rash, fever, conjunctivitis",
    "first_observed": "2026-05-08"
  }
}
```

### Creating a record with an embedded prescription

```json
{
  "patient": 42,
  "title": "Metformin prescription renewal",
  "record_type": "PRESCRIPTION",
  "description": "Renewing Metformin for T2DM management",
  "record_date": "2026-05-10",
  "severity_level": "MEDIUM",
  "folder_name": "Endocrinology",
  "prescription": {
    "medication_name": "Metformin",
    "dosage": "500mg",
    "frequency": "twice daily with meals",
    "duration": "3 months",
    "quantity": 180,
    "refills": 2,
    "instructions": "Take with breakfast and dinner. Monitor blood glucose weekly."
  }
}
```

**Validation rules:**
- `patient` or `patient_record_id` must be provided (not both pointing to inconsistent records).
- `requires_followup: true` requires `followup_date` (must be today or future).
- `patient` must refer to a user with role `PATIENT`.

### 201 Response

Returns the full `MedicalRecordDetail` shape.

---

## 8. Updating a Record

```
PATCH /api/medical-records/records/{id}/
Content-Type: application/json
```

Providers can update records they created. All fields are optional.

```json
{
  "title": "HbA1c — June follow-up",
  "description": "Result improved to 6.8% after medication adjustment",
  "severity_level": "LOW",
  "requires_followup": true,
  "followup_date": "2026-09-10"
}
```

To update the embedded allergy or prescription on an existing record, include the nested object:

```json
{
  "allergy": {
    "severity": "LIFE_THREATENING"
  }
}
```

Returns the updated `MedicalRecordDetail`.

---

## 9. Deactivating a Record

```
DELETE /api/medical-records/records/{id}/
```

Sets `is_active = false` (soft delete). Logs a `DELETE` access event.

**200 OK:**
```json
{ "message": "Medical record deactivated." }
```

---

## 10. Attachments — Upload & View

### List attachments

```
GET /api/medical-records/records/{id}/attachments/
```

```json
[
  {
    "id": 41,
    "file": "https://api.medilink.dz/media/medical_records/attachments/2026/05/10/scan.pdf",
    "file_name": "thoracic_scan_report.pdf",
    "file_type": "application/pdf",
    "file_size": 512000,
    "description": "Thoracic CT scan — no abnormalities detected",
    "uploaded_by_email": "dr.benali@example.com",
    "uploaded_at": "2026-05-10T11:00:00Z"
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
| `file` | file | Yes | PDF, JPEG, PNG, DICOM, etc. |
| `file_name` | string | Yes | Original file name |
| `file_type` | string | No | MIME type |
| `file_size` | integer | No | Size in bytes |
| `description` | string | No | What the file contains |

**201 Created** — returns the attachment object.

Typical use cases:
- Lab result PDF delivered by a laboratory provider
- DICOM or imaging report PDF from a radiology provider
- Wound photo from a nurse's post-operative visit
- Signed prescription scan

---

## 11. Clinical Notes — Add & View

### List notes

```
GET /api/medical-records/records/{id}/notes/
```

Returns all notes (patient and provider) on the record.

### Add a clinical note

```
POST /api/medical-records/records/{id}/notes/
Content-Type: application/json
```

```json
{
  "note_type": "PROVIDER",
  "content": "Patient reports pain level 4/10 post-medication. Continue current dosage."
}
```

**Rules:**
- Notes created by providers are automatically set to `note_type=PROVIDER` and `is_locked=true` — patients cannot edit them.
- Providers can only create `PROVIDER`-type notes.

**201 Created** — returns the note object.

---

## 12. Export Patient Record as PDF

```
GET /api/medical-records/records/{id}/export-pdf/
GET /api/medical-records/records/{id}/export-pdf/?include_attachments=true
```

Returns the record as a downloadable PDF (`Content-Type: application/pdf`).  
**Requires `reportlab`** installed on the server. Returns `503` otherwise.

Logs a `PDF_EXPORT` access event visible in the patient's audit log.

---

## 13. My Authorized Patients

```
GET /api/medical-records/access/my-patients/
```

Returns all patients the authenticated provider currently has **active, non-expired** access to.

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
    "access_type": "FULL",
    "access_type_display": "Full Access",
    "granted_at": "2026-03-10T08:00:00Z",
    "expires_at": "2027-03-10T08:00:00Z",
    "is_active": true,
    "is_expired": false,
    "is_valid": true,
    "reason": "Regular follow-up care"
  }
]
```

Use this endpoint to display the list of patients accessible from the provider's dashboard.

---

## 14. Managing Your Own Access Grant (Admin / Specialized Flows)

### View all access grants (admin or patient)

```
GET /api/medical-records/access/
```

- **Patient:** sees their own grants.
- **Provider:** sees their own grants (all, including expired/revoked).
- **Admin:** sees all grants in the system.

Supports filters: `?is_active=true`, `?access_type=FULL`.

### Grant access (admin only — or patient self-granting)

```
POST /api/medical-records/access/
Content-Type: application/json
```

```json
{
  "provider_id": 3,
  "patient_id": 42,
  "access_type": "FULL",
  "expires_at": "2027-05-11T00:00:00Z",
  "reason": "Assigned treating physician"
}
```

`patient_id` is required when the caller is an admin. Patients omit it (they are the patient).

### Revoke an access grant

```
POST /api/medical-records/access/{id}/revoke/
```

Sets `is_active = false`. The patient or admin may do this.

### Renew a revoked grant

```
POST /api/medical-records/access/{id}/renew/
Content-Type: application/json
```

```json
{ "expires_at": "2028-01-01T00:00:00Z" }
```

Omit `expires_at` to grant permanent access. Resets `granted_at` to now.

---

## 15. Access Granted Automatically (Nurse Requests)

When a patient accepts a nurse's offer via the nurse request flow, the system creates an access grant in the background via `NurseRequest` signal handlers:

```
signals.py → _grant_medical_access_for_accepted_request()
```

Two grants are created:
1. `ProviderPatientAccess` (legacy) — links the nurse's `Provider` to the patient's `PatientRecord`.
2. `ProviderAccess` — `access_type=READ_ONLY`, no expiry (`expires_at=null`).

The nurse can immediately call `patient-folder/{patient_id}/` after the request is accepted without any additional setup.

**The nurse sees `access_type: "READ_ONLY"` in the `patient-folder` response.** This means they can view all non-confidential records and confidential records, but cannot create or modify records.

To create a record as part of a nursing visit (e.g., wound assessment), the nurse's access type must be upgraded to `FULL` — either manually by the patient or by an admin.

---

## 16. Field Reference

### ProviderAccess fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Grant PK |
| `patient` | integer | Patient user ID |
| `patient_email` | string | Patient email |
| `patient_name` | string | Patient full name or email |
| `provider` | integer | Provider PK |
| `provider_email` | string | Provider user email |
| `provider_name` | string | Provider display name (e.g., "Dr. Karim Benali") |
| `provider_type` | string | `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY`, etc. |
| `access_type` | string | `FULL`, `READ_ONLY`, `LIMITED` |
| `granted_at` | datetime | When the grant was created or last renewed |
| `expires_at` | datetime\|null | Expiry; `null` = permanent |
| `is_active` | boolean | Whether the grant is active |
| `is_expired` | boolean | Whether `expires_at` has passed |
| `is_valid` | boolean | `is_active AND NOT is_expired` |
| `reason` | string | Free-text reason |

### MedicalRecord record_type choices

| Value | Typical creator | Notes |
|---|---|---|
| `DIAGNOSIS` | Doctor | Principal diagnosis from a consultation |
| `PRESCRIPTION` | Doctor | Medication prescribed; includes embedded `prescription` |
| `ALLERGY` | Doctor or patient | Includes embedded `allergy` |
| `LAB_RESULT` | Laboratory | Lab result PDF usually attached |
| `IMAGING` | Radiology / VTC | Imaging report PDF usually attached |
| `PROCEDURE` | Doctor / Nurse | Surgical or nursing procedure |
| `NOTE` | Any | General clinical or patient note |
| `VACCINATION` | Doctor / Nurse | Vaccination event |
| `OTHER` | Any | Catch-all |

### Severity levels

| Value | Clinical use |
|---|---|
| `CRITICAL` | Immediate clinical action required |
| `HIGH` | Significant risk or urgent follow-up |
| `MEDIUM` | Standard significance |
| `LOW` | Minor, informational |
| `INFO` | No action required |

---

## 17. Error Codes

| HTTP Status | Body | Meaning |
|---|---|---|
| 403 | `{"error": "You do not have access to this patient's medical folder."}` | No valid grant for this (provider, patient) pair |
| 403 | `{"error": "You do not have access to this patient's records."}` | Same, from the records list endpoint |
| 403 | `{"error": "Provider profile not found."}` | The authenticated user has no linked `Provider` profile |
| 404 | `{"error": "Patient not found."}` | No `PATIENT`-role user with the given ID |
| 400 | `{"provider_id": "Access can only be granted to approved providers."}` | Provider status is not `APPROVED` |
| 400 | `{"provider_id": "Provider not found."}` | No provider with that ID |
| 400 | `{"followup_date": "followup_date is required when requires_followup is True."}` | Validation |
| 503 | `{"error": "PDF generation is not available. Install reportlab."}` | `reportlab` not installed |

---

## 18. Feature Gaps vs. Landing Page

| Landing Page Feature | Status | Notes |
|---|---|---|
| **Full folder access at consultation** | ✅ Implemented | Doctors with `FULL` access see all records including confidential |
| **Limited access for nurses (accepted requests)** | ✅ Implemented | Automatic `READ_ONLY` grant on request acceptance |
| **Lab result delivery** | ✅ Implemented | Laboratory provider creates a `LAB_RESULT` record with PDF attachment |
| **Imaging report delivery** | ✅ Implemented | Radiology/VTC provider creates `IMAGING` record with attachment |
| **Access grant / revoke** | ✅ Implemented | Full CRUD on `ProviderAccess` |
| **Access audit logs** | ✅ Implemented | `VIEW`, `CREATE`, `UPDATE`, `DELETE`, `PDF_EXPORT` events |
| **Clinical notes** | ✅ Implemented | Provider notes are locked; patients cannot edit them |
| **Record creation at consultation** | ✅ Implemented | Requires `FULL` access grant |
| **Confidential record visibility** | ✅ Implemented | Only `FULL`/`READ_ONLY` providers see confidential records |
| **Vital signs / biometric curves** | ❌ Not implemented | No model exists; cannot be stored or retrieved |
| **Drug interaction checking** | ❌ Not implemented | No interaction engine; allergies stored but not cross-referenced |
| **Vaccination schedule tracking** | ⚠️ Partial | `VACCINATION` record type exists; no dose-number or schedule model |
| **Nurse write access after visit** | ⚠️ Partial | Nurse auto-grant is `READ_ONLY`; upgrade to `FULL` requires manual action |
| **Provider-to-provider access transfer** | ❌ Not implemented | No referral/handoff mechanism; each grant must be set up independently |
