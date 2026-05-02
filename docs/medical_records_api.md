# Medical Records — API Documentation

> **For:** Flutter Mobile Developer  
> **Applies to:** Patient app and Provider (nurse/doctor) app  
> **Auth:** All endpoints require `Authorization: Token <token>` header  
> **Base prefix:** `/api/medical-records/`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Roles & Access Model](#2-roles--access-model)
3. [Patient Endpoints](#3-patient-endpoints)
   - [My records (paginated list)](#31-my-records-paginated-list)
   - [My folder (structured view)](#32-my-folder-structured-view)
   - [My health data (full bundle)](#33-my-health-data-full-bundle)
   - [Record detail](#34-record-detail)
   - [Attachments](#35-attachments)
   - [Notes](#36-notes)
   - [Access audit log](#37-access-audit-log)
   - [PDF export (single)](#38-pdf-export-single)
   - [PDF export (summary)](#39-pdf-export-summary)
4. [Provider Endpoints](#4-provider-endpoints)
   - [Patient records list](#41-patient-records-list)
   - [Patient folder (structured)](#42-patient-folder-structured)
5. [Provider Access Management](#5-provider-access-management)
   - [Grant access](#51-grant-access)
   - [My providers (patient view)](#52-my-providers-patient-view)
   - [My patients (provider view)](#53-my-patients-provider-view)
   - [Revoke access](#54-revoke-access)
   - [Renew access](#55-renew-access)
6. [Record Types Reference](#6-record-types-reference)
7. [Severity Levels](#7-severity-levels)
8. [Flutter Implementation Checklist](#8-flutter-implementation-checklist)

---

## 1. Overview

The medical records system stores a patient's complete clinical history, organized into typed records (diagnoses, prescriptions, allergies, lab results, etc.).

Key design principles:
- **Patient-owned**: only the patient can grant providers access.
- **Audit-logged**: every view, create, update, and delete is logged with the actor's IP.
- **Confidentiality**: records flagged `is_confidential` are hidden from providers with `LIMITED` access.
- **Dual-patient support**: works for patients with accounts (`patient_user`) and offline patients (`patient_record`).

---

## 2. Roles & Access Model

| Role | What they see |
|---|---|
| **Patient** | Own records only (all endpoints prefixed `/records/my-*`) |
| **Provider (FULL access)** | All non-deleted records for patients they have a valid access grant for |
| **Provider (READ_ONLY)** | Same as FULL but cannot modify |
| **Provider (LIMITED)** | Non-confidential records only |
| **Admin** | All records |

Access grants are managed through the `ProviderAccess` model and can have an optional expiry date.

---

## 3. Patient Endpoints

### 3.1 My records (paginated list)

```
GET /api/medical-records/records/my-records/
```

Returns a paginated list of the patient's own active records.

**Query parameters:**

| Param | Type | Description |
|---|---|---|
| `record_type` | string | Filter: `DIAGNOSIS`, `PRESCRIPTION`, `ALLERGY`, `LAB_RESULT`, `IMAGING`, `PROCEDURE`, `NOTE`, `VACCINATION`, `OTHER` |
| `severity_level` | string | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO` |
| `folder_name` | string | Filter by folder name |
| `requires_followup` | bool | `true` to see only records with pending follow-ups |
| `search` | string | Full-text search across title, description, symptoms, diagnosis code |
| `ordering` | string | `record_date`, `-record_date`, `created_at`, `-created_at` |

**Response:**
```json
{
  "count": 12,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "record_type": "DIAGNOSIS",
      "title": "Hypertension Assessment",
      "description": "...",
      "record_date": "2025-03-15",
      "severity_level": "HIGH",
      "folder_name": "Cardiology",
      "requires_followup": true,
      "followup_date": "2025-06-15",
      "is_confidential": false,
      "created_at": "2025-03-15T10:30:00Z"
    }
  ]
}
```

---

### 3.2 My folder (structured view)

```
GET /api/medical-records/records/my-folder/
```

Returns the patient's complete medical folder in a structured, clinically organized format. Mirrors the view that authorized providers see. Use this as the main "medical history" screen for the patient.

**Response:**
```json
{
  "generated_at": "2025-05-02T14:00:00Z",
  "patient": {
    "id": "abc123",
    "email": "patient@example.com",
    "full_name": "Amina Benali",
    "date_of_birth": "1990-05-15",
    "age": 34,
    "gender": "FEMALE",
    "blood_type": "O+",
    "known_allergies": "Penicillin",
    "chronic_conditions": "Type 2 Diabetes",
    "current_medications": "Metformin 500mg",
    "emergency_contact_name": "Karim Benali",
    "emergency_contact_phone": "+213 555 000000",
    "patient_unique_id": "MED-001234"
  },
  "summary": {
    "total_records": 15,
    "active_allergies": 1,
    "pending_followups": 2,
    "critical_or_high": 3,
    "recent_30_days": 4,
    "record_types": {
      "DIAGNOSIS": 5,
      "PRESCRIPTION": 4,
      "ALLERGY": 1,
      "LAB_RESULT": 3,
      "VACCINATION": 2
    }
  },
  "medical_records": {
    "timeline": [ ... ],
    "by_type": {
      "DIAGNOSIS": [ ... ],
      "ALLERGY": [ ... ]
    },
    "by_folder": {
      "Cardiology": [ ... ],
      "General": [ ... ]
    },
    "critical_or_high": [ ... ],
    "recent_30_days": [ ... ],
    "pending_followups": [ ... ]
  },
  "active_allergies": [ ... ]
}
```

---

### 3.3 My health data (full bundle)

```
GET /api/medical-records/records/my-health-data/
```

Comprehensive data bundle including medical records **plus** prescriptions, appointments, nurse requests, and provider access grants. Use this to pre-load everything on the health dashboard home screen.

**Response keys:**

| Key | Description |
|---|---|
| `summary` | Counts across all categories |
| `medical_records` | Records grouped by type, folder, recency, criticality, and pending follow-ups |
| `prescriptions` | All prescription history with medication items |
| `appointments` | All appointment history |
| `nurse_requests` | All on-demand nurse request history |
| `provider_access` | Current provider access grants |

---

### 3.4 Record detail

```
GET /api/medical-records/records/{id}/
```

Returns full detail for a single record. Access is logged automatically.

**Record type-specific nested objects:**

| Record type | Nested key | Fields |
|---|---|---|
| `PRESCRIPTION` | `prescription` | `medication_name`, `dosage`, `frequency`, `duration`, `instructions`, `quantity`, `refills` |
| `ALLERGY` | `allergy` | `allergen`, `severity`, `reaction`, `first_observed` |

---

### 3.5 Attachments

```
GET  /api/medical-records/records/{id}/attachments/
POST /api/medical-records/records/{id}/attachments/
```

Upload files (images, PDFs, etc.) to a record.

**POST body:** `multipart/form-data` with `file` field and optional `description`.

---

### 3.6 Notes

```
GET  /api/medical-records/records/{id}/notes/
POST /api/medical-records/records/{id}/notes/
```

Patient notes are tagged `note_type: PATIENT`. Provider notes are automatically tagged `PROVIDER` and locked.

---

### 3.7 Access audit log

```
GET /api/medical-records/records/{id}/access-logs/
```

Returns a list of every access event for this record: viewer identity, access type (`VIEW`, `CREATE`, `UPDATE`, `DELETE`, `PDF_EXPORT`), IP address, and timestamp.

**Access:** Patient and Admin only.

---

### 3.8 PDF export (single)

```
GET /api/medical-records/records/{id}/export-pdf/
GET /api/medical-records/records/{id}/export-pdf/?include_attachments=true
```

Returns a PDF file for a single record. Logs a `PDF_EXPORT` access event.

---

### 3.9 PDF export (summary)

```
GET /api/medical-records/records/export-summary/
```

Exports all active records as a summary PDF. Patient only.

---

## 4. Provider Endpoints

> Providers must have a valid `ProviderAccess` grant before calling these endpoints.  
> See [Section 5](#5-provider-access-management) for granting access.

### 4.1 Patient records list

```
GET /api/medical-records/records/patient/{patient_id}/
```

Paginated list of a specific patient's records. Supports the same query parameters as `my-records`.

**Errors:**

| HTTP | Meaning |
|---|---|
| 403 | Provider has no valid access grant for this patient |
| 404 | Patient not found |

---

### 4.2 Patient folder (structured)

```
GET /api/medical-records/records/patient-folder/{patient_id}/
```

Full structured medical folder for a patient — same shape as [Section 3.2](#32-my-folder-structured-view) but for a specific patient. Includes `access_type` field (`FULL`, `READ_ONLY`, `LIMITED`) so the provider UI can show/hide edit actions accordingly.

> **Nurses in nurse requests:** Use the dedicated `GET /api/nurse-requests/nurse/request-history/{id}/patient-folder/` endpoint instead, which requires only the nurse request relationship (no separate ProviderAccess grant) and filters out confidential records automatically. See the [Nurse Requests API docs](nurse_requests_api.md#11-patient-medical-folder-nurse-access).

---

## 5. Provider Access Management

### 5.1 Grant access

```
POST /api/medical-records/access/
```

**Body:**
```json
{
  "patient": "patient-user-id",
  "provider": "provider-id",
  "access_type": "READ_ONLY",
  "expires_at": "2026-12-31T00:00:00Z"
}
```

`access_type`: `FULL`, `READ_ONLY`, or `LIMITED` (excludes confidential records).  
`expires_at`: optional. Omit for indefinite access.

If an inactive grant already exists for this patient/provider pair, it is reactivated instead of creating a duplicate.

---

### 5.2 My providers (patient view)

```
GET /api/medical-records/access/my-providers/
```

List all providers who have (or had) access to the patient's records, including inactive/expired grants.

---

### 5.3 My patients (provider view)

```
GET /api/medical-records/access/my-patients/
```

List all patients the provider currently has active, non-expired access to.

---

### 5.4 Revoke access

```
POST /api/medical-records/access/{id}/revoke/
```

Marks the access grant as inactive. The provider immediately loses access.

---

### 5.5 Renew access

```
POST /api/medical-records/access/{id}/renew/
```

Reactivates a revoked grant.

**Optional body:**
```json
{
  "expires_at": "2027-06-01T00:00:00Z"
}
```

---

## 6. Record Types Reference

| Value | Display |
|---|---|
| `DIAGNOSIS` | Diagnosis |
| `PRESCRIPTION` | Prescription |
| `ALLERGY` | Allergy |
| `LAB_RESULT` | Lab Result |
| `IMAGING` | Imaging |
| `PROCEDURE` | Procedure |
| `NOTE` | Clinical Note |
| `VACCINATION` | Vaccination |
| `OTHER` | Other |

---

## 7. Severity Levels

| Value | Display | Color hint |
|---|---|---|
| `CRITICAL` | Critical | Red |
| `HIGH` | High | Orange |
| `MEDIUM` | Medium | Yellow |
| `LOW` | Low | Blue |
| `INFO` | Info | Gray |

---

## 8. Flutter Implementation Checklist

### Patient App

- [ ] **Medical Folder screen** → `GET /api/medical-records/records/my-folder/`  
      Use `summary` for a stat bar. Use `medical_records.by_folder` for the folder tabs. Use `active_allergies` for an alert banner at the top.
- [ ] **Health Dashboard (home)** → `GET /api/medical-records/records/my-health-data/`  
      Pre-loads records, prescriptions, appointments, and nurse requests in one call.
- [ ] **Record list** → `GET /api/medical-records/records/my-records/`  
      Use `record_type` and `folder_name` filters for category tabs.
- [ ] **Record detail** → `GET /api/medical-records/records/{id}/`  
      Render `prescription` or `allergy` nested objects if present.
- [ ] **Attachments** → Show in a scrollable row at the bottom of the detail screen.
- [ ] **Audit log** → `GET /api/medical-records/records/{id}/access-logs/`  
      Show as a "who viewed this" timeline, patient-facing only.
- [ ] **PDF export** → `GET /api/medical-records/records/export-summary/`  
      Offer a share sheet after downloading the PDF bytes.
- [ ] **Provider access tab** → `GET /api/medical-records/access/my-providers/`  
      Show active grants with an `is_active` badge. Offer a "Revoke" button.

### Provider (Nurse) App

- [ ] **Patient folder during/after service** → `GET /api/nurse-requests/nurse/request-history/{id}/patient-folder/`  
      Available only when request status is `ACCEPTED`, `IN_PROGRESS`, or `COMPLETED`.  
      Show `patient_clinical_info` (blood type, allergies, medications) as an always-visible clinical header.
- [ ] Show `access_note` so the nurse knows confidential records are excluded.
- [ ] Highlight `active_allergies` prominently with a warning icon.
- [ ] `critical_or_high` records should appear at the top of the timeline.
- [ ] If patient has no records yet, show a helpful empty state ("No medical records on file").
