# Prescriptions Management System - Comprehensive Report

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Data Models](#2-data-models)
3. [Enums & Constants](#3-enums--constants)
4. [API Endpoints](#4-api-endpoints)
5. [Business Logic & Workflows](#5-business-logic--workflows)
6. [Permission System](#6-permission-system)
7. [Dashboard Integration](#7-dashboard-integration)
8. [Error Codes](#8-error-codes)
9. [Frontend Integration Examples](#9-frontend-integration-examples)

---

## 1. System Overview

### Purpose
The Prescriptions Management System allows healthcare providers (doctors) to create, manage, and issue prescriptions to patients after consultations. Key features include:

- **Doctor-issued prescriptions**: Only doctors can create prescriptions
- **Appointment integration**: Prescriptions are linked to confirmed/completed appointments
- **PDF support**: Frontend generates PDFs, backend stores and serves them
- **Status lifecycle**: DRAFT → ISSUED → DISPENSED (with expiry and cancellation support)
- **Multiple medications**: Each prescription can contain multiple medication items
- **Patient history**: Full prescription history for patients and doctors

### Architecture
```
┌──────────────────────────────────────────────────────────────────┐
│                    PRESCRIPTIONS SYSTEM                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   PRESCRIPTION  │  │   PRESCRIPTION  │  │      PDF        │   │
│  │      CORE       │  │      ITEMS      │  │    STORAGE      │   │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤   │
│  │ • Create        │  │ • Medications   │  │ • Upload        │   │
│  │ • Issue         │  │ • Dosage        │  │ • Download      │   │
│  │ • Cancel        │  │ • Duration      │  │ • Secure Access │   │
│  │ • Status Mgmt   │  │ • Instructions  │  │                 │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     RELATIONSHIPS                            │ │
│  ├─────────────────────────────────────────────────────────────┤ │
│  │  Doctor ──── Prescription ──── Patient (User/PatientRecord) │ │
│  │                  │                                           │ │
│  │                  ├──── Appointment (OneToOne)                │ │
│  │                  ├──── Clinic (Optional)                     │ │
│  │                  └──── Items (OneToMany)                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions
| Decision | Rationale |
|----------|-----------|
| PDF generation on frontend | More flexibility for UI/UX, reduces backend complexity |
| OneToOne with Appointment | One prescription per appointment, ensures data integrity |
| Draft status before issue | Allows doctors to review before finalizing |
| Reference number auto-generation | Easy identification (format: `RX{YYMMDD}-{6CHARS}`) |

---

## 2. Data Models

### 2.1 Prescription Model
The core prescription model linking doctors, patients, and appointments.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto | Primary key |
| `reference_number` | CharField(50) | Auto | Unique reference (e.g., `RX250128-ABC123`) |
| `doctor` | FK → Doctor | ✅ | Doctor who issued the prescription |
| `patient` | FK → User | ❌* | Patient with user account |
| `patient_record` | FK → PatientRecord | ❌* | Patient without account |
| `clinic` | FK → Clinic | ❌ | Clinic where issued (optional) |
| `appointment` | OneToOne → Appointment | ❌ | Associated appointment |
| `diagnosis` | TextField | ❌ | Diagnosis or reason |
| `notes` | TextField | ❌ | Additional notes |
| `instructions` | TextField | ❌ | General patient instructions |
| `pdf_file` | FileField | ❌ | Uploaded PDF |
| `status` | CharField(20) | ✅ | Current status (default: DRAFT) |
| `valid_until` | DateField | ❌ | Expiration date |
| `issued_at` | DateTime | ❌ | When issued |
| `created_at` | DateTime | Auto | Creation timestamp |
| `updated_at` | DateTime | Auto | Last update timestamp |

**\*** Either `patient` OR `patient_record` must be provided (not both)

**Database Table:** `prescription_documents`

**Database Constraints:**
```python
# At least one patient identifier required
CheckConstraint(
    condition=Q(patient__isnull=False) | Q(patient_record__isnull=False),
    name='prescription_has_patient'
)

# Cannot have both patient types
CheckConstraint(
    condition=~(Q(patient__isnull=False) & Q(patient_record__isnull=False)),
    name='prescription_single_patient_type'
)
```

**Indexes:**
| Index Fields | Purpose |
|--------------|---------|
| `doctor, created_at` | Doctor's prescription list |
| `patient, created_at` | Patient's prescription history |
| `patient_record, created_at` | PatientRecord queries |
| `clinic, created_at` | Clinic prescription queries |
| `status` | Status filtering |
| `reference_number` | Reference lookup |

### 2.2 PrescriptionItem Model
Individual medication items within a prescription.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto | Primary key |
| `prescription` | FK → Prescription | ✅ | Parent prescription |
| `medication_name` | CharField(255) | ✅ | Medication name |
| `medication_type` | CharField(20) | ✅ | Type (TABLET, CAPSULE, etc.) |
| `generic_name` | CharField(255) | ❌ | Generic name |
| `strength` | CharField(100) | ❌ | Strength (e.g., "500mg") |
| `dosage` | CharField(100) | ✅ | Dosage amount (e.g., "1 tablet") |
| `frequency` | CharField(20) | ✅ | Frequency code (QD, BID, TID, etc.) |
| `custom_frequency` | CharField(200) | ❌ | Custom frequency text |
| `duration_days` | PositiveInteger | ❌ | Duration in days |
| `duration_text` | CharField(100) | ❌ | Human-readable duration |
| `quantity` | PositiveInteger | ❌ | Total quantity to dispense |
| `quantity_unit` | CharField(50) | ❌ | Unit (tablets, ml, etc.) |
| `instructions` | TextField | ❌ | Additional instructions |
| `order` | PositiveInteger | ✅ | Display order (default: 0) |
| `created_at` | DateTime | Auto | Creation timestamp |
| `updated_at` | DateTime | Auto | Last update timestamp |

**Database Table:** `prescription_items`

---

## 3. Enums & Constants

### 3.1 Prescription Status
| Value | Label | Description |
|-------|-------|-------------|
| `DRAFT` | Draft | Being drafted, can be edited |
| `ISSUED` | Issued | Finalized and given to patient |
| `DISPENSED` | Dispensed | Medication has been dispensed |
| `EXPIRED` | Expired | Prescription has expired |
| `CANCELLED` | Cancelled | Prescription was cancelled |

### 3.2 Status Transition Rules
```
         ┌──────────────────────────────────────────┐
         │                                          │
         ▼                                          │
      DRAFT ─────────────► ISSUED ─────────────► DISPENSED
         │                    │
         │                    │
         ▼                    ▼
     CANCELLED            EXPIRED (automatic)
```

| From | To | Who Can Transition | Conditions |
|------|----|--------------------|------------|
| DRAFT | ISSUED | Doctor (creator) | Can have items |
| DRAFT | CANCELLED | Doctor (creator) | Any time |
| ISSUED | DISPENSED | Doctor/Pharmacy | Patient received medication |
| ISSUED | CANCELLED | Doctor (creator) | Before dispensed |
| ISSUED | EXPIRED | System | After `valid_until` date |

### 3.3 Medication Types
| Value | Label | Description |
|-------|-------|-------------|
| `TABLET` | Tablet | Oral tablet |
| `CAPSULE` | Capsule | Oral capsule |
| `SYRUP` | Syrup | Liquid oral medication |
| `INJECTION` | Injection | Injectable medication |
| `CREAM` | Cream | Topical cream |
| `OINTMENT` | Ointment | Topical ointment |
| `DROPS` | Drops | Eye/ear/nose drops |
| `INHALER` | Inhaler | Respiratory inhaler |
| `PATCH` | Patch | Transdermal patch |
| `SUPPOSITORY` | Suppository | Rectal/vaginal |
| `OTHER` | Other | Other types |

### 3.4 Dosage Frequencies
| Value | Label | Medical Abbreviation |
|-------|-------|---------------------|
| `QD` | Once daily | q.d. |
| `BID` | Twice daily | b.i.d. |
| `TID` | Three times daily | t.i.d. |
| `QID` | Four times daily | q.i.d. |
| `QAM` | Every morning | q.a.m. |
| `QPM` | Every evening | q.p.m. |
| `QHS` | At bedtime | q.h.s. |
| `PRN` | As needed | p.r.n. |
| `Q4H` | Every 4 hours | q.4h. |
| `Q6H` | Every 6 hours | q.6h. |
| `Q8H` | Every 8 hours | q.8h. |
| `Q12H` | Every 12 hours | q.12h. |
| `QW` | Once weekly | q.w. |
| `CUSTOM` | Custom schedule | - |

---

## 4. API Endpoints

### 4.1 Endpoints Summary

| Method | Endpoint | Description | Auth | Roles |
|--------|----------|-------------|------|-------|
| POST | `/api/prescriptions/` | Create prescription | ✅ | Doctor |
| GET | `/api/prescriptions/` | List prescriptions | ✅ | Doctor, Patient |
| GET | `/api/prescriptions/{id}/` | Get prescription details | ✅ | Doctor, Patient |
| PUT/PATCH | `/api/prescriptions/{id}/` | Update prescription | ✅ | Doctor (creator) |
| DELETE | `/api/prescriptions/{id}/` | Delete prescription | ✅ | Doctor (creator) |
| POST | `/api/prescriptions/{id}/upload-pdf/` | Upload PDF file | ✅ | Doctor (creator) |
| POST | `/api/prescriptions/{id}/issue/` | Issue prescription | ✅ | Doctor (creator) |
| POST | `/api/prescriptions/{id}/cancel/` | Cancel prescription | ✅ | Doctor (creator) |
| GET | `/api/prescriptions/{id}/items/` | List items | ✅ | Doctor, Patient |
| POST | `/api/prescriptions/{id}/items/` | Add item | ✅ | Doctor (creator) |
| GET | `/api/prescriptions/my-prescriptions/` | Patient's prescriptions | ✅ | Patient |
| GET | `/api/prescriptions/my-issued/` | Doctor's prescriptions | ✅ | Doctor |
| GET | `/api/prescriptions/choices/` | Get enum choices | ✅ | Any |
| GET | `/api/prescription-items/{id}/` | Get item details | ✅ | Doctor, Patient |
| PUT/PATCH | `/api/prescription-items/{id}/` | Update item | ✅ | Doctor (creator) |
| DELETE | `/api/prescription-items/{id}/` | Delete item | ✅ | Doctor (creator) |

---

### 4.2 Create Prescription

**POST** `/api/prescriptions/`

Creates a new prescription. Only doctors can create prescriptions.

**Request Headers:**
```
Authorization: Token <token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "appointment_id": "660e8400-e29b-41d4-a716-446655440000",
  "clinic_id": "770e8400-e29b-41d4-a716-446655440000",
  "diagnosis": "Upper respiratory tract infection",
  "notes": "Follow-up in 7 days if symptoms persist",
  "instructions": "Complete the full course of antibiotics. Take with food.",
  "valid_until": "2025-02-28",
  "items": [
    {
      "medication_name": "Amoxicillin",
      "medication_type": "CAPSULE",
      "generic_name": "Amoxicillin Trihydrate",
      "strength": "500mg",
      "dosage": "1 capsule",
      "frequency": "TID",
      "duration_days": 7,
      "quantity": 21,
      "quantity_unit": "capsules",
      "instructions": "Take after meals"
    },
    {
      "medication_name": "Paracetamol",
      "medication_type": "TABLET",
      "strength": "500mg",
      "dosage": "1-2 tablets",
      "frequency": "PRN",
      "duration_text": "As needed for fever",
      "quantity": 20,
      "quantity_unit": "tablets",
      "instructions": "Maximum 8 tablets per day"
    }
  ]
}
```

**Alternative - Patient Record (without account):**
```json
{
  "patient_record_id": "880e8400-e29b-41d4-a716-446655440000",
  "diagnosis": "...",
  "items": [...]
}
```

**Response:** `201 Created`
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "reference_number": "RX250128-X7K9M2",
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_name": "John Doe",
  "doctor_id": "aa0e8400-e29b-41d4-a716-446655440000",
  "doctor_name": "Dr. Sarah Smith",
  "clinic_id": "770e8400-e29b-41d4-a716-446655440000",
  "clinic_name": "Central Medical Clinic",
  "appointment_id": "660e8400-e29b-41d4-a716-446655440000",
  "diagnosis": "Upper respiratory tract infection",
  "notes": "Follow-up in 7 days if symptoms persist",
  "instructions": "Complete the full course of antibiotics. Take with food.",
  "items": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440000",
      "medication_name": "Amoxicillin",
      "medication_type": "CAPSULE",
      "medication_type_display": "Capsule",
      "generic_name": "Amoxicillin Trihydrate",
      "strength": "500mg",
      "dosage": "1 capsule",
      "frequency": "TID",
      "frequency_display": "Three times daily",
      "duration_days": 7,
      "quantity": 21,
      "quantity_unit": "capsules",
      "instructions": "Take after meals",
      "full_instructions": "1 capsule Three times daily for 7 days. Take after meals",
      "order": 0
    }
  ],
  "status": "DRAFT",
  "status_display": "Draft",
  "is_valid": false,
  "valid_until": "2025-02-28",
  "pdf_file": null,
  "pdf_url": null,
  "issued_at": null,
  "created_at": "2025-01-28T10:00:00Z",
  "updated_at": "2025-01-28T10:00:00Z"
}
```

**Error Responses:**

| Status | Error | Description |
|--------|-------|-------------|
| 400 | `patient_id is required` | Neither patient_id nor patient_record_id provided |
| 400 | `Cannot specify both...` | Both patient types provided |
| 400 | `Prescription can only be created for confirmed or completed appointments` | Invalid appointment status |
| 400 | `This appointment already has a prescription` | Appointment already has prescription |
| 403 | `Only doctors can create prescriptions` | User is not a doctor |
| 404 | `Patient not found` | Invalid patient_id |
| 404 | `Appointment not found` | Invalid appointment_id |

---

### 4.3 List Prescriptions

**GET** `/api/prescriptions/`

Lists prescriptions based on user role:
- **Doctors**: See prescriptions they created
- **Patients**: See their own prescriptions
- **Admins**: See all prescriptions

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (DRAFT, ISSUED, etc.) |
| `ordering` | string | Order by field (default: `-created_at`) |
| `page` | integer | Page number for pagination |

**Response:** `200 OK`
```json
{
  "count": 25,
  "next": "https://api.example.com/api/prescriptions/?page=2",
  "previous": null,
  "results": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "reference_number": "RX250128-X7K9M2",
      "patient_name": "John Doe",
      "doctor_name": "Dr. Sarah Smith",
      "clinic_name": "Central Medical Clinic",
      "diagnosis": "Upper respiratory tract infection",
      "status": "ISSUED",
      "status_display": "Issued",
      "items_count": 2,
      "valid_until": "2025-02-28",
      "issued_at": "2025-01-28T10:30:00Z",
      "created_at": "2025-01-28T10:00:00Z"
    }
  ]
}
```

---

### 4.4 Get Prescription Details

**GET** `/api/prescriptions/{id}/`

**Response:** `200 OK`
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "reference_number": "RX250128-X7K9M2",
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_name": "John Doe",
  "doctor_id": "aa0e8400-e29b-41d4-a716-446655440000",
  "doctor_name": "Dr. Sarah Smith",
  "clinic_id": "770e8400-e29b-41d4-a716-446655440000",
  "clinic_name": "Central Medical Clinic",
  "appointment_id": "660e8400-e29b-41d4-a716-446655440000",
  "diagnosis": "Upper respiratory tract infection",
  "notes": "Follow-up in 7 days if symptoms persist",
  "instructions": "Complete the full course of antibiotics.",
  "items": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440000",
      "medication_name": "Amoxicillin",
      "medication_type": "CAPSULE",
      "medication_type_display": "Capsule",
      "generic_name": "Amoxicillin Trihydrate",
      "strength": "500mg",
      "dosage": "1 capsule",
      "frequency": "TID",
      "frequency_display": "Three times daily",
      "custom_frequency": "",
      "duration_days": 7,
      "duration_text": "",
      "quantity": 21,
      "quantity_unit": "capsules",
      "instructions": "Take after meals",
      "full_instructions": "1 capsule Three times daily for 7 days. Take after meals",
      "order": 0,
      "created_at": "2025-01-28T10:00:00Z"
    }
  ],
  "status": "ISSUED",
  "status_display": "Issued",
  "is_valid": true,
  "valid_until": "2025-02-28",
  "pdf_file": "/media/prescriptions/patient-uuid/rx-uuid/prescription.pdf",
  "pdf_url": "https://api.example.com/media/prescriptions/patient-uuid/rx-uuid/prescription.pdf",
  "issued_at": "2025-01-28T10:30:00Z",
  "created_at": "2025-01-28T10:00:00Z",
  "updated_at": "2025-01-28T10:30:00Z"
}
```

---

### 4.5 Update Prescription

**PUT/PATCH** `/api/prescriptions/{id}/`

Updates a prescription. **Only works for DRAFT status.**

**Request Body:**
```json
{
  "diagnosis": "Updated diagnosis",
  "notes": "Updated notes",
  "instructions": "Updated instructions",
  "valid_until": "2025-03-15",
  "items": [
    {
      "medication_name": "Amoxicillin",
      "medication_type": "CAPSULE",
      "strength": "500mg",
      "dosage": "1 capsule",
      "frequency": "BID",
      "duration_days": 10
    }
  ]
}
```

**Note:** When `items` is provided, all existing items are replaced with the new list.

**Error Responses:**
| Status | Error | Description |
|--------|-------|-------------|
| 400 | `Can only update prescriptions in DRAFT status` | Prescription already issued |
| 403 | `You can only modify prescriptions you created` | Not the creator |

---

### 4.6 Upload PDF

**POST** `/api/prescriptions/{id}/upload-pdf/`

Uploads a PDF file for the prescription. The PDF should be generated by the frontend.

**Request:** `multipart/form-data`
```
Content-Type: multipart/form-data

pdf_file: <file.pdf>
```

**Response:** `200 OK`
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "reference_number": "RX250128-X7K9M2",
  "pdf_file": "/media/prescriptions/patient-uuid/rx-uuid/prescription.pdf",
  "pdf_url": "https://api.example.com/media/prescriptions/patient-uuid/rx-uuid/prescription.pdf",
  "...": "..."
}
```

**Validation:**
- Only `.pdf` files allowed
- Maximum file size: 10MB

---

### 4.7 Issue Prescription

**POST** `/api/prescriptions/{id}/issue/`

Issues a prescription (changes status from DRAFT to ISSUED).

**Request Body:** None required

**Response:** `200 OK`
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "reference_number": "RX250128-X7K9M2",
  "status": "ISSUED",
  "status_display": "Issued",
  "issued_at": "2025-01-28T10:30:00Z",
  "...": "..."
}
```

**Error Responses:**
| Status | Error | Description |
|--------|-------|-------------|
| 400 | `Cannot issue prescription with status ISSUED` | Already issued |
| 403 | Permission denied | Not the creator |

---

### 4.8 Cancel Prescription

**POST** `/api/prescriptions/{id}/cancel/`

Cancels a prescription.

**Request Body:** None required

**Response:** `200 OK`
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "status": "CANCELLED",
  "status_display": "Cancelled",
  "...": "..."
}
```

**Error Responses:**
| Status | Error | Description |
|--------|-------|-------------|
| 400 | `Cannot cancel prescription with status DISPENSED` | Already dispensed |

---

### 4.9 Manage Items

#### List Items
**GET** `/api/prescriptions/{id}/items/`

**Response:** `200 OK`
```json
[
  {
    "id": "bb0e8400-e29b-41d4-a716-446655440000",
    "medication_name": "Amoxicillin",
    "medication_type": "CAPSULE",
    "medication_type_display": "Capsule",
    "strength": "500mg",
    "dosage": "1 capsule",
    "frequency": "TID",
    "frequency_display": "Three times daily",
    "duration_days": 7,
    "full_instructions": "1 capsule Three times daily for 7 days",
    "order": 0
  }
]
```

#### Add Item
**POST** `/api/prescriptions/{id}/items/`

**Request Body:**
```json
{
  "medication_name": "Ibuprofen",
  "medication_type": "TABLET",
  "strength": "400mg",
  "dosage": "1 tablet",
  "frequency": "TID",
  "duration_days": 5,
  "instructions": "Take after meals"
}
```

**Response:** `201 Created`

**Error:** Can only add items to DRAFT prescriptions.

---

### 4.10 My Prescriptions (Patient)

**GET** `/api/prescriptions/my-prescriptions/`

Gets the current patient's prescription history.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `ordering` | string | Order by field (default: `-created_at`) |

**Response:** Same format as List Prescriptions

---

### 4.11 My Issued (Doctor)

**GET** `/api/prescriptions/my-issued/`

Gets prescriptions issued by the current doctor.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `patient_id` | uuid | Filter by patient |
| `from_date` | date | From date (YYYY-MM-DD) |
| `to_date` | date | To date (YYYY-MM-DD) |
| `ordering` | string | Order by field (default: `-created_at`) |

**Response:** Same format as List Prescriptions

---

### 4.12 Get Choices

**GET** `/api/prescriptions/choices/`

Returns enum choices for frontend forms.

**Response:** `200 OK`
```json
{
  "status": [
    {"value": "DRAFT", "label": "Draft"},
    {"value": "ISSUED", "label": "Issued"},
    {"value": "DISPENSED", "label": "Dispensed"},
    {"value": "EXPIRED", "label": "Expired"},
    {"value": "CANCELLED", "label": "Cancelled"}
  ],
  "medication_type": [
    {"value": "TABLET", "label": "Tablet"},
    {"value": "CAPSULE", "label": "Capsule"},
    {"value": "SYRUP", "label": "Syrup"},
    {"value": "INJECTION", "label": "Injection"},
    {"value": "CREAM", "label": "Cream"},
    {"value": "OINTMENT", "label": "Ointment"},
    {"value": "DROPS", "label": "Drops"},
    {"value": "INHALER", "label": "Inhaler"},
    {"value": "PATCH", "label": "Patch"},
    {"value": "SUPPOSITORY", "label": "Suppository"},
    {"value": "OTHER", "label": "Other"}
  ],
  "dosage_frequency": [
    {"value": "QD", "label": "Once daily"},
    {"value": "BID", "label": "Twice daily"},
    {"value": "TID", "label": "Three times daily"},
    {"value": "QID", "label": "Four times daily"},
    {"value": "QAM", "label": "Every morning"},
    {"value": "QPM", "label": "Every evening"},
    {"value": "QHS", "label": "At bedtime"},
    {"value": "PRN", "label": "As needed"},
    {"value": "Q4H", "label": "Every 4 hours"},
    {"value": "Q6H", "label": "Every 6 hours"},
    {"value": "Q8H", "label": "Every 8 hours"},
    {"value": "Q12H", "label": "Every 12 hours"},
    {"value": "QW", "label": "Once weekly"},
    {"value": "CUSTOM", "label": "Custom schedule"}
  ]
}
```

---

## 5. Business Logic & Workflows

### 5.1 Prescription Creation Flow (Doctor)

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESCRIPTION CREATION FLOW                   │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ Appointment  │ ←── Must be CONFIRMED or COMPLETED
  │  Completed   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Doctor opens │
  │ prescription │
  │    form      │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Add diagnosis│     ┌──────────────┐
  │ Add items    │────►│   DRAFT      │
  │ Add notes    │     │   status     │
  └──────┬───────┘     └──────────────┘
         │
         ▼
  ┌──────────────┐
  │ Frontend     │
  │ generates    │
  │ PDF          │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Upload PDF   │ ←── POST /prescriptions/{id}/upload-pdf/
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐     ┌──────────────┐
  │ Issue        │────►│   ISSUED     │
  │ prescription │     │   status     │
  └──────┬───────┘     └──────────────┘
         │
         ▼
  ┌──────────────┐
  │ Patient can  │
  │ view & print │
  └──────────────┘
```

### 5.2 Viewing Prescriptions (Patient)

```
Patient Login
     │
     ▼
GET /prescriptions/my-prescriptions/
     │
     ▼
┌────────────────────────────────────┐
│        PRESCRIPTION LIST           │
├────────────────────────────────────┤
│ • RX250128-X7K9M2 - ISSUED        │
│   Dr. Smith - Central Clinic       │
│   Date: Jan 28, 2025               │
│   [View] [Download PDF]            │
├────────────────────────────────────┤
│ • RX250115-Y8L3N4 - DISPENSED     │
│   Dr. Johnson - Health Center      │
│   Date: Jan 15, 2025               │
│   [View] [Download PDF]            │
└────────────────────────────────────┘
     │
     ▼ Click [View]
     │
GET /prescriptions/{id}/
     │
     ▼
┌────────────────────────────────────┐
│        PRESCRIPTION DETAILS        │
├────────────────────────────────────┤
│ Reference: RX250128-X7K9M2         │
│ Doctor: Dr. Sarah Smith            │
│ Clinic: Central Medical Clinic     │
│ Date: January 28, 2025             │
│                                    │
│ Diagnosis:                         │
│ Upper respiratory tract infection  │
│                                    │
│ Medications:                       │
│ 1. Amoxicillin 500mg               │
│    1 capsule - Three times daily   │
│    Duration: 7 days                │
│    Instructions: Take after meals  │
│                                    │
│ 2. Paracetamol 500mg               │
│    1-2 tablets - As needed         │
│    Instructions: Max 8 per day     │
│                                    │
│ Valid Until: February 28, 2025     │
│                                    │
│ [Download PDF] [Share]             │
└────────────────────────────────────┘
```

---

## 6. Permission System

### 6.1 Permission Classes

| Permission Class | Description |
|------------------|-------------|
| `IsDoctorUser` | User must have a doctor profile |
| `IsPrescriptionDoctor` | User must be the doctor who created the prescription |
| `CanViewPrescription` | User is doctor (creator), patient, or admin |
| `CanModifyPrescription` | User is creator AND prescription is DRAFT |

### 6.2 Permission Matrix

| Action | Doctor (Creator) | Doctor (Other) | Patient (Own) | Admin |
|--------|------------------|----------------|---------------|-------|
| Create | ✅ | ✅ (own patients) | ❌ | ✅ |
| View | ✅ | ❌ | ✅ | ✅ |
| Update | ✅ (draft only) | ❌ | ❌ | ✅ |
| Delete | ✅ (draft only) | ❌ | ❌ | ✅ |
| Upload PDF | ✅ | ❌ | ❌ | ✅ |
| Issue | ✅ | ❌ | ❌ | ✅ |
| Cancel | ✅ | ❌ | ❌ | ✅ |
| Add Items | ✅ (draft only) | ❌ | ❌ | ✅ |

---

## 7. Dashboard Integration

### 7.1 Doctor Dashboard

#### Today's Prescriptions Widget
```
GET /api/prescriptions/my-issued/?from_date=2025-01-28&to_date=2025-01-28
```

#### Recent Prescriptions Widget
```
GET /api/prescriptions/my-issued/?ordering=-created_at&page_size=5
```

#### Draft Prescriptions (Pending Action)
```
GET /api/prescriptions/my-issued/?status=DRAFT
```

### 7.2 Patient Dashboard

#### My Prescriptions Widget
```
GET /api/prescriptions/my-prescriptions/?status=ISSUED
```

#### Active Prescriptions (Valid)
Filter locally where `is_valid == true`

---

## 8. Error Codes

### 8.1 Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `patient_id or patient_record_id required` | No patient specified | Provide one patient identifier |
| `Cannot specify both patient_id and patient_record_id` | Both provided | Use only one |
| `Prescription can only be created for confirmed or completed appointments` | Invalid appointment status | Wait for appointment confirmation |
| `This appointment already has a prescription` | Duplicate prescription | View existing prescription |
| `Can only update prescriptions in DRAFT status` | Already issued | Create new prescription |
| `Can only add items to draft prescriptions` | Already issued | Create new prescription |
| `Custom frequency text is required when frequency is CUSTOM` | Missing custom_frequency | Provide custom_frequency value |
| `Only PDF files are allowed` | Wrong file type | Upload .pdf file |
| `File size must not exceed 10MB` | File too large | Reduce file size |

### 8.2 Status Transition Errors

| Error | Cause |
|-------|-------|
| `Cannot issue prescription with status ISSUED` | Already issued |
| `Cannot issue prescription with status CANCELLED` | Already cancelled |
| `Cannot cancel prescription with status DISPENSED` | Already dispensed |
| `Cannot cancel prescription with status CANCELLED` | Already cancelled |

---

## 9. Frontend Integration Examples

### 9.1 Flutter - Create Prescription

```dart
class PrescriptionService {
  final ApiClient _client;
  
  Future<Prescription> createPrescription({
    required String patientId,
    String? appointmentId,
    String? clinicId,
    required String diagnosis,
    String? notes,
    String? instructions,
    DateTime? validUntil,
    required List<PrescriptionItem> items,
  }) async {
    final response = await _client.post(
      '/api/prescriptions/',
      data: {
        'patient_id': patientId,
        if (appointmentId != null) 'appointment_id': appointmentId,
        if (clinicId != null) 'clinic_id': clinicId,
        'diagnosis': diagnosis,
        if (notes != null) 'notes': notes,
        if (instructions != null) 'instructions': instructions,
        if (validUntil != null) 'valid_until': validUntil.toIso8601String().split('T')[0],
        'items': items.map((item) => item.toJson()).toList(),
      },
    );
    
    return Prescription.fromJson(response.data);
  }
  
  Future<Prescription> uploadPdf(String prescriptionId, File pdfFile) async {
    final formData = FormData.fromMap({
      'pdf_file': await MultipartFile.fromFile(pdfFile.path),
    });
    
    final response = await _client.post(
      '/api/prescriptions/$prescriptionId/upload-pdf/',
      data: formData,
    );
    
    return Prescription.fromJson(response.data);
  }
  
  Future<Prescription> issuePrescription(String prescriptionId) async {
    final response = await _client.post(
      '/api/prescriptions/$prescriptionId/issue/',
    );
    
    return Prescription.fromJson(response.data);
  }
}
```

### 9.2 React - Patient Prescription List

```typescript
import { useQuery } from '@tanstack/react-query';

interface Prescription {
  id: string;
  reference_number: string;
  doctor_name: string;
  clinic_name: string;
  diagnosis: string;
  status: string;
  status_display: string;
  items_count: number;
  valid_until: string;
  issued_at: string;
  pdf_url: string | null;
}

function useMyPrescriptions(status?: string) {
  return useQuery({
    queryKey: ['my-prescriptions', status],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      
      const response = await fetch(
        `/api/prescriptions/my-prescriptions/?${params}`,
        {
          headers: {
            'Authorization': `Token ${getToken()}`,
          },
        }
      );
      
      return response.json();
    },
  });
}

function PrescriptionList() {
  const { data, isLoading } = useMyPrescriptions('ISSUED');
  
  if (isLoading) return <Loading />;
  
  return (
    <div className="prescription-list">
      {data.results.map((rx: Prescription) => (
        <PrescriptionCard key={rx.id} prescription={rx} />
      ))}
    </div>
  );
}

function PrescriptionCard({ prescription }: { prescription: Prescription }) {
  return (
    <div className="card">
      <h3>{prescription.reference_number}</h3>
      <p>Dr. {prescription.doctor_name}</p>
      <p>{prescription.clinic_name}</p>
      <p>Diagnosis: {prescription.diagnosis}</p>
      <span className={`badge ${prescription.status.toLowerCase()}`}>
        {prescription.status_display}
      </span>
      <p>{prescription.items_count} medications</p>
      {prescription.pdf_url && (
        <a href={prescription.pdf_url} download>Download PDF</a>
      )}
    </div>
  );
}
```

### 9.3 PDF Generation (Frontend)

The frontend is responsible for generating the prescription PDF. Here's a suggested structure:

```
┌────────────────────────────────────────────────────────┐
│                    PRESCRIPTION                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  [Clinic Logo]        CENTRAL MEDICAL CLINIC            │
│                       123 Healthcare Avenue              │
│                       Phone: (555) 123-4567              │
│                                                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Reference: RX250128-X7K9M2    Date: January 28, 2025   │
│                                                         │
│  Patient: John Doe                                      │
│  Age: 35 years                                          │
│                                                         │
├────────────────────────────────────────────────────────┤
│  DIAGNOSIS                                              │
│  Upper respiratory tract infection                      │
│                                                         │
├────────────────────────────────────────────────────────┤
│  MEDICATIONS                                            │
│                                                         │
│  1. Amoxicillin 500mg (Capsule)                        │
│     Sig: 1 capsule three times daily for 7 days        │
│     Qty: 21 capsules                                   │
│     Note: Take after meals                             │
│                                                         │
│  2. Paracetamol 500mg (Tablet)                         │
│     Sig: 1-2 tablets as needed for fever               │
│     Qty: 20 tablets                                    │
│     Note: Maximum 8 tablets per day                    │
│                                                         │
├────────────────────────────────────────────────────────┤
│  INSTRUCTIONS                                           │
│  Complete the full course of antibiotics.               │
│  Take with food. Follow-up in 7 days if symptoms        │
│  persist.                                               │
│                                                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Valid Until: February 28, 2025                         │
│                                                         │
│                            ________________________     │
│                            Dr. Sarah Smith              │
│                            License No: MD-12345         │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 10. Migration Commands

```bash
# Create migrations
python manage.py makemigrations prescriptions

# Apply migrations
python manage.py migrate prescriptions

# Verify
python manage.py check
```

---

## 11. Verification Checklist

- [ ] Prescription CRUD operations work
- [ ] Only doctors can create prescriptions
- [ ] Prescriptions require confirmed/completed appointments
- [ ] PDF upload works (max 10MB, PDF only)
- [ ] Issue/Cancel status transitions work correctly
- [ ] Patients can view their own prescriptions
- [ ] Patients cannot modify prescriptions
- [ ] Reference numbers are unique and auto-generated
- [ ] Items can be added/updated/deleted (draft only)
- [ ] My-prescriptions endpoint works for patients
- [ ] My-issued endpoint works for doctors
- [ ] Choices endpoint returns all enums
- [ ] Pagination works on list endpoints
- [ ] Filtering by status works
- [ ] Date range filtering works (my-issued)
