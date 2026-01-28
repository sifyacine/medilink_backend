# Patients System - Frontend/Mobile Documentation

## Overview

The Medilink Patients System enables healthcare providers to manage patient records for patients who may or may not have Medilink accounts. The system supports:

- **Patient Records Without Accounts**: Providers create patient records that can later be linked to user accounts
- **Account Linking**: Patients receive a secure token to link their records to their new account
- **Secure Record Sharing**: Patients can share their medical records via time-limited QR codes/tokens
- **Provider Access Control**: Fine-grained access control for which providers can see which patients

---

## Authentication

All endpoints require JWT authentication unless otherwise specified.

```
Authorization: Bearer <access_token>
```

---

## Endpoints Reference

### 1. Patient Records (Provider Operations)

#### 1.1 List Patient Records
**GET** `/api/patients/`

List all patient records the authenticated provider has access to.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by name, phone, email, or national ID |
| `gender` | string | Filter by gender (MALE, FEMALE, OTHER) |
| `blood_type` | string | Filter by blood type |
| `city` | string | Filter by city |
| `country` | string | Filter by country |
| `ordering` | string | Order by field (first_name, last_name, date_of_birth, created_at) |
| `page` | int | Page number for pagination |

**Response (200 OK):**
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
      "age": 39,
      "gender": "MALE",
      "phone_number": "+213555123456",
      "is_active": true,
      "is_linked": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### 1.2 Create Patient Record
**POST** `/api/patients/`

Create a new patient record (providers only).

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
  "known_allergies": "Penicillin",
  "chronic_conditions": "Hypertension",
  "current_medications": "Lisinopril 10mg daily",
  "national_id": "123456789",
  "address": "123 Main Street",
  "city": "Algiers",
  "state": "Algiers",
  "country": "Algeria",
  "emergency_contact_name": "Fatima Benali",
  "emergency_contact_phone": "+213555987654",
  "notes": "Patient prefers morning appointments"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "patient_unique_id": "MED-A1B2C3D4",
  "first_name": "Ahmed",
  "last_name": "Benali",
  "full_name": "Ahmed Benali",
  "date_of_birth": "1985-03-15",
  "age": 39,
  "gender": "MALE",
  "phone_number": "+213555123456",
  "email": "ahmed@example.com",
  "emergency_contact_name": "Fatima Benali",
  "emergency_contact_phone": "+213555987654",
  "blood_type": "A+",
  "known_allergies": "Penicillin",
  "chronic_conditions": "Hypertension",
  "current_medications": "Lisinopril 10mg daily",
  "national_id": "123456789",
  "address": "123 Main Street",
  "city": "Algiers",
  "state": "Algiers",
  "country": "Algeria",
  "notes": "Patient prefers morning appointments",
  "is_active": true,
  "is_linked": false,
  "linking_token_masked": "abc12345...xyz9",
  "created_by_provider_name": "Dr. Mohamed Larbi",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### 1.3 Get Patient Record Details
**GET** `/api/patients/{id}/`

Get full details of a specific patient record.

**Response (200 OK):**
Same as create response.

---

#### 1.4 Update Patient Record
**PUT/PATCH** `/api/patients/{id}/`

Update a patient record (requires FULL access or creator).

**Request Body (PATCH - partial update):**
```json
{
  "phone_number": "+213555999888",
  "current_medications": "Lisinopril 20mg daily"
}
```

---

#### 1.5 Delete Patient Record
**DELETE** `/api/patients/{id}/`

Soft delete a patient record (sets is_active to false).

**Response (204 No Content)**

---

#### 1.6 Get Linking Token
**GET** `/api/patients/{id}/token/`

Get the full linking token for a patient record. Used to give to patients for account linking.

**Response (200 OK):**
```json
{
  "linking_token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234",
  "patient_name": "Ahmed Benali",
  "token_used": false,
  "is_linked": false
}
```

If already used:
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

#### 1.7 Regenerate Linking Token
**POST** `/api/patients/{id}/regenerate-token/`

Regenerate a lost or compromised linking token (creator only).

**Response (200 OK):**
```json
{
  "linking_token": "new123token456here789...",
  "patient_name": "Ahmed Benali",
  "message": "Token has been regenerated."
}
```

---

#### 1.8 Grant Provider Access
**POST** `/api/patients/{id}/grant-access/`

Grant another provider access to this patient's records.

**Request Body:**
```json
{
  "patient_record_id": 1,
  "provider_id": 5,
  "access_level": "READ_ONLY"
}
```

**Access Levels:**
- `FULL` - Full read/write access
- `READ_ONLY` - View only
- `LIMITED` - Limited view (excludes confidential records)

**Response (201 Created):**
```json
{
  "id": 1,
  "provider": 5,
  "provider_name": "Dr. Amira Hadj",
  "patient_record": 1,
  "patient_name": "Ahmed Benali",
  "access_level": "READ_ONLY",
  "created_at": "2024-01-15T11:00:00Z"
}
```

---

#### 1.9 Get Patient Medical History
**GET** `/api/patients/{patient_id}/history/`

Get complete medical history for a patient (providers only).

**Response (200 OK):**
```json
{
  "patient": {
    "id": 1,
    "patient_unique_id": "MED-A1B2C3D4",
    "full_name": "Ahmed Benali",
    "date_of_birth": "1985-03-15",
    "age": 39,
    "gender": "MALE",
    "blood_type": "A+",
    "known_allergies": "Penicillin",
    "chronic_conditions": "Hypertension",
    "current_medications": "Lisinopril 10mg daily",
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
          "description": "Patient diagnosed with stage 1 hypertension",
          "diagnosis_code": "I10",
          "symptoms": "Elevated blood pressure readings",
          "is_confidential": false,
          "requires_followup": true,
          "created_at": "2024-01-10T09:30:00Z"
        }
      ],
      "PRESCRIPTION": [
        {
          "id": 2,
          "title": "Lisinopril Prescription",
          "record_date": "2024-01-10",
          "description": "Starting antihypertensive therapy",
          "diagnosis_code": "",
          "symptoms": "",
          "is_confidential": false,
          "requires_followup": false,
          "created_at": "2024-01-10T09:45:00Z"
        }
      ],
      "LAB_RESULT": [...],
      "VACCINATION": [...]
    }
  }
}
```

---

### 2. Patient Operations (Patient Account)

#### 2.1 Link Account to Patient Record
**POST** `/api/patients/link-account/`

Link the authenticated patient's account to an existing patient record using the linking token.

**Request Body:**
```json
{
  "linking_token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234"
}
```

**Response (200 OK):**
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

**Error Responses:**
```json
// Invalid token
{
  "error": "Invalid linking token."
}

// Token already used
{
  "linking_token": ["This linking token has already been used."]
}

// Account already linked
{
  "error": "Your account is already linked to a patient record."
}
```

---

#### 2.2 Get My Patient Record
**GET** `/api/patients/me/`

Get the current patient's linked patient record.

**Response (200 OK):**
Full patient record object.

**Response (404 Not Found):**
```json
{
  "error": "No linked patient record found."
}
```

---

#### 2.3 Get My Medical Records
**GET** `/api/patients/my-records/`

Get the current patient's medical records.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `record_type` | string | Filter by type (DIAGNOSIS, PRESCRIPTION, etc.) |
| `limit` | int | Max records to return (default 50, max 100) |

**Response (200 OK):**
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
      "description": "Patient diagnosed with stage 1 hypertension",
      "diagnosis_code": "I10",
      "symptoms": "Elevated blood pressure readings",
      "is_confidential": false,
      "requires_followup": true,
      "followup_date": "2024-02-10",
      "created_at": "2024-01-10T09:30:00Z"
    }
  ]
}
```

---

### 3. Share Token Operations (Patient Account)

#### 3.1 List My Share Tokens
**GET** `/api/patients/share-tokens/`
or
**GET** `/api/patients/my-share-tokens/`

List all share tokens created by the patient.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `active_only` | bool | Only show usable tokens |

**Response (200 OK):**
```json
{
  "count": 3,
  "tokens": [
    {
      "id": 1,
      "token": "abc123...",
      "access_level": "READ_ONLY",
      "expires_at": "2024-01-16T10:30:00Z",
      "max_uses": 1,
      "use_count": 0,
      "is_active": true,
      "is_revoked": false,
      "is_expired": false,
      "is_usable": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### 3.2 Create Share Token
**POST** `/api/patients/share-tokens/`

Create a new share token for sharing medical records.

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
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_level` | string | No | READ_ONLY (default), FULL, LIMITED |
| `expires_in_hours` | int | No | 1-720 hours (default 24) |
| `max_uses` | int | No | 0-100 (0 = unlimited, default 1) |
| `target_provider_id` | int | No | Restrict to specific provider |
| `notes` | string | No | Optional notes |

**Response (201 Created):**
```json
{
  "id": 1,
  "token": "Xk9_mN2pQr5sT8uV1wY4zA7bC0dE3fG6hI",
  "patient_name": "Ahmed Benali",
  "patient_unique_id": "MED-A1B2C3D4",
  "access_level": "READ_ONLY",
  "expires_at": "2024-01-16T10:30:00Z",
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
    "expires_at": "2024-01-16T10:30:00Z"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### 3.3 Get Share Token Details
**GET** `/api/patients/share-tokens/{id}/`

Get details of a specific share token.

**Response (200 OK):**
Same as create response.

---

#### 3.4 Revoke Share Token
**POST** `/api/patients/share-tokens/{id}/revoke/`

Revoke a share token to prevent further use.

**Response (200 OK):**
```json
{
  "message": "Share token has been revoked.",
  "token_id": 1
}
```

---

#### 3.5 Get Share Token Access Logs
**GET** `/api/patients/share-tokens/{id}/access-logs/`

View who has accessed records using this token.

**Response (200 OK):**
```json
{
  "token_id": 1,
  "use_count": 2,
  "logs": [
    {
      "id": 1,
      "share_token": 1,
      "accessed_by_provider_name": "Dr. Amira Hadj",
      "accessed_at": "2024-01-15T11:00:00Z",
      "ip_address": "192.168.1.100"
    },
    {
      "id": 2,
      "share_token": 1,
      "accessed_by_provider_name": "Clinique El-Hakim",
      "accessed_at": "2024-01-15T12:30:00Z",
      "ip_address": "192.168.1.105"
    }
  ]
}
```

---

### 4. Share Token Access (Provider Operations)

#### 4.1 Access Patient Records via Share Token
**GET** `/api/patients/records/share/{token}/`

Access patient records using a share token. This is used by providers when a patient shares their QR code or token.

**Response (200 OK):**
```json
{
  "access_level": "READ_ONLY",
  "token_id": 1,
  "uses_remaining": 0,
  "expires_at": "2024-01-16T10:30:00Z",
  "patient": {
    "patient_unique_id": "MED-A1B2C3D4",
    "full_name": "Ahmed Benali",
    "date_of_birth": "1985-03-15",
    "age": 39,
    "gender": "MALE",
    "blood_type": "A+",
    "known_allergies": "Penicillin",
    "chronic_conditions": "Hypertension",
    "current_medications": "Lisinopril 10mg daily",
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
        "is_confidential": false
      }
    ]
  },
  "access_granted": true
}
```

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

// Wrong provider (targeted token)
{
  "error": "This share token is for a different provider."
}
```

---

## Common Flows

### Flow 1: Provider Creates Patient Record

```
1. Provider logs in
2. POST /api/patients/ (create patient record)
3. GET /api/patients/{id}/token/ (get linking token)
4. Give linking token to patient (verbally, printed, etc.)
```

### Flow 2: Patient Links Account

```
1. Patient downloads Medilink app
2. Patient creates account (role: PATIENT)
3. POST /api/patients/link-account/ with linking_token
4. GET /api/patients/me/ (verify linked record)
```

### Flow 3: Patient Shares Records with New Provider

```
1. Patient logs in
2. POST /api/patients/share-tokens/ (create share token)
3. Display QR code from qr_code_data.url
4. New provider scans QR code
5. Provider GET /api/patients/records/share/{token}/
6. Provider views patient records
```

### Flow 4: Provider Accesses Existing Patient

```
1. Provider logs in
2. GET /api/patients/ (list accessible patients)
3. GET /api/patients/{id}/ (get details)
4. GET /api/patients/{id}/history/ (get full medical history)
```

---

## QR Code Generation (Frontend)

The `qr_code_data` object returned when creating a share token contains all the data needed to generate a QR code:

```javascript
// Example using qrcode.js library
import QRCode from 'qrcode';

const shareTokenResponse = await createShareToken({
  access_level: 'READ_ONLY',
  expires_in_hours: 24
});

// Generate QR code from the URL
const qrCodeDataUrl = await QRCode.toDataURL(
  shareTokenResponse.qr_code_data.url
);

// Display in image element
document.getElementById('qrCode').src = qrCodeDataUrl;

// Also display expiry info
const expiresAt = new Date(shareTokenResponse.qr_code_data.expires_at);
console.log(`Token expires: ${expiresAt.toLocaleString()}`);
```

---

## Patient Identifier Display

When displaying patient information, use the `patient_unique_id` field for user-facing displays:

```javascript
// Good - user-friendly
"Patient ID: MED-A1B2C3D4"

// Avoid - internal database ID
"Patient ID: 12345"
```

The `patient_unique_id` format is:
- Prefix: `MED-`
- 8 alphanumeric characters (uppercase)
- Example: `MED-A1B2C3D4`

---

## Access Level Descriptions

| Level | Description | Use Case |
|-------|-------------|----------|
| `FULL` | Complete access to all records, including confidential | Primary care physician |
| `READ_ONLY` | View all records but cannot modify | Specialist consultation |
| `LIMITED` | View non-confidential records only | Emergency access |

---

## Error Handling

All errors follow this format:

```json
{
  "error": "Error message here"
}
```

Or for validation errors:

```json
{
  "field_name": ["Validation error message"]
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not logged in) |
| 403 | Forbidden (no permission) |
| 404 | Not Found |
| 500 | Server Error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Create share token | 10/hour per patient |
| Access via share token | 100/hour per provider |
| General API | 1000/hour per user |

---

## Changelog

### Version 2.0 (Current)
- Added `patient_unique_id` field for user-friendly identification
- Added share token system for secure record sharing
- Added QR code data in share token responses
- Added soft delete support
- Added medical history endpoint for providers
- Added access logging for share tokens
