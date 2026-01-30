# Medical Records API Documentation

## Overview

The Medical Records API provides comprehensive patient-centered healthcare data management with:

- **Complete EHR storage**: Diagnoses, prescriptions, allergies, attachments, notes
- **Dual patient linking**: Supports users with accounts AND patient records
- **Role-based access control (RBAC)**: Patient, provider, and admin permissions
- **Provider access grants**: Patients control who can access their records
- **Full audit logging**: All access is logged for compliance

---

## Authentication & Authorization

All endpoints require JWT authentication.

### Role Permissions Matrix

| Role | Own Records | Other Patient Records | Create Records | Delete Records |
|------|-------------|----------------------|----------------|----------------|
| **Patient** | Full CRUD | ❌ | ✅ (self only) | ✅ (soft delete) |
| **Provider** | N/A | Read (if authorized) | ✅ | ✅ (own created) |
| **Admin** | N/A | Full access | ✅ | ✅ |

### Provider Access System

Providers need explicit access grants to view patient records. Access can be:
- **FULL**: Read and write access
- **READ_ONLY**: View only
- **LIMITED**: Restricted access

Providers automatically have access to records they create.

---

## Data Models

### MedicalRecord (Core)

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Unique identifier |
| `patient` | FK → User | Patient with account (optional) |
| `patient_record` | FK → PatientRecord | Patient without account (optional) |
| `title` | String | Record title/summary |
| `record_type` | Enum | DIAGNOSIS, PRESCRIPTION, ALLERGY, LAB_RESULT, IMAGING, PROCEDURE, NOTE, VACCINATION, OTHER |
| `diagnosis_code` | String | ICD-10 or other code |
| `description` | Text | Detailed description |
| `symptoms` | Text | Reported/observed symptoms |
| `record_date` | Date | Date of medical event |
| `created_by` | FK → User | Creator (usually provider) |
| `updated_by` | FK → User | Last updater |
| `is_active` | Boolean | True = active, False = soft deleted |
| `is_confidential` | Boolean | Marked as confidential |
| `requires_followup` | Boolean | Needs follow-up |
| `followup_date` | Date | Scheduled follow-up date |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

**Validation Rule:** At least one of `patient` or `patient_record` must be set.

### Prescription (Nested)

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Unique identifier |
| `medical_record` | OneToOne → MedicalRecord | Parent record |
| `medication_name` | String | Medication name |
| `dosage` | String | Dosage information |
| `frequency` | String | Administration frequency |
| `duration` | String | Treatment duration |
| `instructions` | Text | Taking instructions |
| `quantity` | Integer | Prescribed quantity |
| `refills` | Integer | Number of refills (0-12) |

### Allergy (Nested)

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Unique identifier |
| `medical_record` | OneToOne → MedicalRecord | Parent record |
| `allergen` | String | Substance causing allergy |
| `severity` | Enum | MILD, MODERATE, SEVERE, LIFE_THREATENING |
| `reaction` | Text | Reaction description |
| `first_observed` | Date | First observation date |

### MedicalRecordAttachment

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Unique identifier |
| `medical_record` | FK → MedicalRecord | Parent record |
| `file` | FileField | Uploaded file (PDF, image, etc.) |
| `file_name` | String | Original filename |
| `file_type` | String | MIME type |
| `file_size` | Integer | Size in bytes |
| `description` | String | File description |
| `uploaded_by` | FK → User | Uploader |
| `uploaded_at` | DateTime | Upload timestamp |

### MedicalRecordNote

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Unique identifier |
| `medical_record` | FK → MedicalRecord | Parent record |
| `note_type` | Enum | PATIENT, PROVIDER, SYSTEM |
| `content` | Text | Note content |
| `created_by` | FK → User | Creator |
| `is_locked` | Boolean | Locked (provider notes) |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

### MedicalRecordAccessLog

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Unique identifier |
| `medical_record` | FK → MedicalRecord | Accessed record |
| `accessed_by` | FK → User | User who accessed |
| `access_type` | Enum | VIEW, CREATE, UPDATE, DELETE, PDF_EXPORT |
| `ip_address` | GenericIP | Client IP address |
| `accessed_at` | DateTime | Access timestamp |

### ProviderAccess

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Unique identifier |
| `patient` | FK → User | Patient granting access |
| `provider` | FK → Provider | Provider receiving access |
| `access_granted_by` | FK → User | Who granted access |
| `access_type` | Enum | FULL, READ_ONLY, LIMITED |
| `granted_at` | DateTime | Grant timestamp |
| `expires_at` | DateTime | Expiration (null = permanent) |
| `is_active` | Boolean | Active status |
| `reason` | Text | Reason for granting access |

---

## API Endpoints

### Medical Records ViewSet

**Base URL:** `/api/medical-records/`

#### List Medical Records

**GET** `/api/medical-records/`

Returns records based on user role:
- **Patients**: Own records only
- **Providers**: Records of authorized patients + self-created
- **Admins**: All records

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `record_type` | string | Filter by type |
| `is_active` | boolean | Filter by active status |
| `requires_followup` | boolean | Filter by follow-up flag |
| `patient` | UUID | Filter by patient (admin/provider only) |
| `search` | string | Search in title, description, symptoms, diagnosis_code |
| `ordering` | string | Order by field (default: `-record_date,-created_at`) |

**Response (200 OK):**
```json
{
  "count": 15,
  "next": "/api/medical-records/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Annual Physical Examination",
      "record_type": "NOTE",
      "record_date": "2025-06-15",
      "patient_email": "patient@example.com",
      "created_by_email": "doctor@example.com",
      "is_active": true,
      "requires_followup": false,
      "followup_date": null,
      "created_at": "2025-06-15T10:00:00Z",
      "has_prescription": false,
      "has_allergy": false,
      "attachment_count": 2,
      "note_count": 1
    }
  ]
}
```

---

#### Create Medical Record

**POST** `/api/medical-records/`

**Request Body:**
```json
{
  "patient": "uuid-of-patient",
  "title": "Annual Physical Examination",
  "record_type": "NOTE",
  "diagnosis_code": "Z00.00",
  "description": "Routine annual physical. All vitals normal.",
  "symptoms": "None reported",
  "record_date": "2025-06-15",
  "is_confidential": false,
  "requires_followup": true,
  "followup_date": "2026-06-15",
  "prescription": {
    "medication_name": "Vitamin D",
    "dosage": "2000 IU",
    "frequency": "Once daily",
    "duration": "3 months",
    "quantity": 90,
    "refills": 2
  },
  "allergy": {
    "allergen": "Penicillin",
    "severity": "SEVERE",
    "reaction": "Anaphylaxis",
    "first_observed": "2010-03-15"
  }
}
```

**Validation Rules:**
- Patients can only create records for themselves
- Providers can create records for any patient
- Nested `prescription` and `allergy` are optional

**Response (201 Created):** Full medical record object with nested data

**Access Logging:** CREATE event logged with IP address

---

#### Retrieve Medical Record

**GET** `/api/medical-records/{id}/`

Returns full record details with nested prescription, allergy, attachments, and notes.

**Response (200 OK):**
```json
{
  "id": 1,
  "patient": "uuid",
  "patient_email": "patient@example.com",
  "title": "Annual Physical Examination",
  "record_type": "NOTE",
  "diagnosis_code": "Z00.00",
  "description": "Routine annual physical. All vitals normal.",
  "symptoms": "None reported",
  "record_date": "2025-06-15",
  "created_by": "uuid",
  "created_by_email": "doctor@example.com",
  "updated_by": "uuid",
  "updated_by_email": "doctor@example.com",
  "is_active": true,
  "is_confidential": false,
  "requires_followup": true,
  "followup_date": "2026-06-15",
  "created_at": "2025-06-15T10:00:00Z",
  "updated_at": "2025-06-15T10:00:00Z",
  "prescription": {
    "id": 1,
    "medication_name": "Vitamin D",
    "dosage": "2000 IU",
    "frequency": "Once daily",
    "duration": "3 months",
    "instructions": "",
    "quantity": 90,
    "refills": 2
  },
  "allergy": {
    "id": 1,
    "allergen": "Penicillin",
    "severity": "SEVERE",
    "reaction": "Anaphylaxis",
    "first_observed": "2010-03-15"
  },
  "attachments": [
    {
      "id": 1,
      "file": "/media/medical_records/attachments/2025/06/15/lab_results.pdf",
      "file_name": "lab_results.pdf",
      "file_type": "application/pdf",
      "file_size": 102400,
      "description": "Blood work results",
      "uploaded_by_email": "doctor@example.com",
      "uploaded_at": "2025-06-15T10:30:00Z"
    }
  ],
  "notes": [
    {
      "id": 1,
      "note_type": "PROVIDER",
      "content": "Patient in good health. Recommend continued vitamin D supplementation.",
      "created_by_email": "doctor@example.com",
      "created_at": "2025-06-15T10:15:00Z",
      "updated_at": "2025-06-15T10:15:00Z",
      "is_locked": true
    }
  ]
}
```

**Access Logging:** VIEW event logged

---

#### Update Medical Record

**PUT/PATCH** `/api/medical-records/{id}/`

**Request Body (PATCH):**
```json
{
  "description": "Updated description",
  "requires_followup": false
}
```

**Restrictions:**
- Patients cannot modify `diagnosis_code` or `record_type` on provider-created records
- Providers need FULL access or be the creator to modify

**Access Logging:** UPDATE event logged

---

#### Delete Medical Record (Soft Delete)

**DELETE** `/api/medical-records/{id}/`

Performs soft delete by setting `is_active = False`.

**Response (200 OK):**
```json
{
  "message": "Medical record has been deactivated."
}
```

**Access Logging:** DELETE event logged

---

#### Add Attachment

**POST** `/api/medical-records/{id}/attachments/`

**Headers:**
```
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <file>
description: "Lab results from annual physical"
```

**Response (201 Created):** Attachment object

---

#### Add Note

**POST** `/api/medical-records/{id}/notes/`

**Request Body:**
```json
{
  "content": "Patient reported improved energy levels."
}
```

**Note Type Assignment:**
- Patients → PATIENT notes
- Providers → PROVIDER notes (auto-locked)

**Response (201 Created):** Note object

---

#### Get Patient's Records

**GET** `/api/medical-records/my-records/`

Shortcut for patients to get their own records.

**Available only for:** Patients

---

#### Get Records for Specific Patient

**GET** `/api/medical-records/patient/{patient_id}/`

Get all records for a specific patient.

**Available for:** Providers and Admins only

---

#### Export Single Record as PDF

**GET** `/api/medical-records/{id}/export-pdf/`

Generate and download PDF of a single medical record.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `include_attachments` | boolean | Include attachment list (default: false) |

**Response:** PDF file download

**Requirements:** `reportlab` package must be installed

**Access Logging:** PDF_EXPORT event logged

---

#### Export All Records as Summary PDF

**GET** `/api/medical-records/export-summary/`

Generate and download PDF summary of all patient's records.

**Available only for:** Patients (their own records)

**Response:** PDF file download

---

### Provider Access ViewSet

**Base URL:** `/api/provider-access/`

#### List Access Grants

**GET** `/api/provider-access/`

Returns access grants based on user role:
- **Patients**: Access grants for their records
- **Providers**: Access grants given to them
- **Admins**: All access grants

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `is_active` | boolean | Filter by active status |
| `access_type` | string | Filter by access type |
| `ordering` | string | Order by field |

**Response (200 OK):**
```json
{
  "results": [
    {
      "id": 1,
      "patient": "uuid",
      "patient_email": "patient@example.com",
      "patient_name": "John Doe",
      "provider": "uuid",
      "provider_email": "doctor@example.com",
      "provider_name": "Dr. Jane Smith",
      "access_type": "FULL",
      "access_type_display": "Full Access",
      "granted_at": "2025-06-01T10:00:00Z",
      "expires_at": null,
      "is_active": true,
      "is_expired": false,
      "is_valid": true,
      "reason": "Primary care physician"
    }
  ]
}
```

---

#### Create Access Grant

**POST** `/api/provider-access/`

Grant a provider access to patient records.

**Request Body (Patient):**
```json
{
  "provider_id": "uuid-of-provider",
  "access_type": "READ_ONLY",
  "expires_at": "2026-06-01T00:00:00Z",
  "reason": "Second opinion consultation"
}
```

**Request Body (Admin):**
```json
{
  "provider_id": "uuid-of-provider",
  "patient_id": "uuid-of-patient",
  "access_type": "FULL",
  "reason": "Primary care provider assignment"
}
```

**Validation Rules:**
- Patients can only grant access to their own records (no `patient_id` needed)
- Admins must specify `patient_id`
- Cannot create duplicate access grants (use update instead)
- `expires_at` must be in the future

**Response (201 Created):** Access grant object

---

#### Get My Providers (Patient)

**GET** `/api/provider-access/my-providers/`

List providers who have access to patient's records.

**Available only for:** Patients

---

#### Get My Patients (Provider)

**GET** `/api/provider-access/my-patients/`

List patients the provider has access to.

**Available only for:** Providers

---

#### Revoke Access

**POST** `/api/provider-access/{id}/revoke/`

Revoke a provider's access to patient records.

**Response (200 OK):**
```json
{
  "message": "Provider access has been revoked.",
  "access": { ... }
}
```

---

#### Renew Access

**POST** `/api/provider-access/{id}/renew/`

Reactivate a revoked access grant and remove expiration.

**Response (200 OK):**
```json
{
  "message": "Provider access has been renewed.",
  "access": { ... }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "patient": ["Medical records can only be created for patients."],
  "diagnosis_code": ["Patients cannot modify diagnosis_code on provider-created records."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 503 Service Unavailable
```json
{
  "error": "PDF generation is not available. Install reportlab package."
}
```

---

## Common Use Cases

### 1. Patient Views Their Medical History

```
1. GET /api/medical-records/my-records/ → List all records
2. GET /api/medical-records/{id}/ → View specific record details
3. GET /api/medical-records/export-summary/ → Download PDF summary
```

### 2. Provider Creates Record After Appointment

```
1. POST /api/medical-records/ → Create record with diagnosis, prescription
2. POST /api/medical-records/{id}/attachments/ → Upload lab results
3. POST /api/medical-records/{id}/notes/ → Add clinical notes
```

### 3. Patient Grants Provider Access

```
1. POST /api/provider-access/ → Grant access to new provider
2. GET /api/provider-access/my-providers/ → View who has access
3. POST /api/provider-access/{id}/revoke/ → Remove access when done
```

### 4. Provider Reviews Patient History

```
1. GET /api/provider-access/my-patients/ → List authorized patients
2. GET /api/medical-records/?patient={id} → Get patient's records
3. GET /api/medical-records/{id}/ → View specific record
```

---

## Audit Trail

All access to medical records is logged in the `MedicalRecordAccessLog` table:

| Event | Trigger |
|-------|---------|
| VIEW | Retrieving a record |
| CREATE | Creating a new record |
| UPDATE | Modifying a record |
| DELETE | Soft-deleting a record |
| PDF_EXPORT | Downloading a PDF |

Log entries include:
- User who accessed
- Access type
- IP address
- Timestamp

---

## Security Best Practices

1. **Least Privilege**: Default access type is READ_ONLY
2. **Expiring Access**: Set `expires_at` for temporary access grants
3. **Provider Approval**: Only approved providers can access records
4. **Patient Control**: Patients can revoke access at any time
5. **Soft Delete**: Records are never permanently deleted (is_active flag)
6. **Confidential Flag**: Sensitive records can be marked confidential
7. **Provider Notes Locked**: Provider notes cannot be modified by patients

---

## Related Documentation

- [Prescriptions API](PRESCRIPTIONS_API.md) - Prescription management
- [Auth/Me Endpoint](AUTH_ME_ENDPOINT.md) - User profile management
