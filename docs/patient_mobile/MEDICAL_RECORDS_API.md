# Patient Mobile App - Medical Records API

## Overview

This documentation covers the **Medical Records API** for the Patient Mobile Application. Patients can view, manage, and export their medical records. This enables patients to maintain a complete history of their health care and share information with providers when needed.

**Key Capabilities:**
- 📱 **View Medical History** - See all medical records organized by type and date
- ✏️ **Add Personal Notes** - Document your own observations and health information
- 📤 **Export Records** - Download individual records or complete medical summary as PDF
- 🔐 **Control Access** - Manage which providers can access your records
- 📎 **Manage Attachments** - Upload and view health documents
- 🏥 **Care Coordination** - Share information with multiple providers

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [My Medical Records](#my-medical-records)
   - [List My Records](#list-my-records)
   - [View Details](#view-single-record)
   - [Search & Filter](#search-and-filter)
4. [Record Types](#record-types)
5. [Add Personal Information](#add-personal-information)
6. [Attachments](#attachments)
   - [Add Attachment](#add-attachment)
   - [Download Files](#download-files)
7. [Personal Notes](#personal-notes)
   - [Add Notes](#add-note-to-record)
8. [Export Records](#export-records)
   - [Export Single Record](#export-single-record-as-pdf)
   - [Export All Records](#export-all-records-summary)
9. [Manage Provider Access](#manage-provider-access)
10. [Common Workflows](#common-workflows)
11. [Error Handling](#error-handling)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

All medical record endpoints are prefixed with `/api/medical-records/`

---

## Authentication

All medical record endpoints require authentication. Include your token in every request:

```
Authorization: Token <your_token_here>
```

**Important:** You must be logged in as a patient to access your medical records.

---

## My Medical Records

### List My Records

Get all your medical records in one place. Records are displayed in reverse chronological order (newest first).

**Endpoint:**
```http
GET /api/medical-records/records/my-records/
Authorization: Token your_auth_token
```

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `record_type` | string | Filter by record type | `DIAGNOSIS`, `ALLERGY`, `PRESCRIPTION` |
| `is_active` | boolean | Show active records only | `true` |
| `requires_followup` | boolean | Show records needing follow-up | `true` |
| `search` | string | Search by title or description | `blood pressure` |
| `ordering` | string | Sort order | `-record_date` (newest first) |
| `page` | integer | Page number (pagination) | `1` |

**Response:**
```json
{
  "count": 12,
  "next": "https://dzmedilink.duckdns.org/api/medical-records/records/my-records/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Diabetes Diagnosis",
      "record_type": "DIAGNOSIS",
      "record_date": "2026-02-15",
      "description": "Type 2 Diabetes Mellitus",
      "created_by": {
        "first_name": "Dr. Ahmed",
        "email": "doctor@clinic.com"
      },
      "requires_followup": true,
      "followup_date": "2026-04-15",
      "created_at": "2026-02-15T10:00:00Z"
    },
    {
      "id": 2,
      "title": "Blood Pressure Check",
      "record_type": "NOTE",
      "record_date": "2026-02-14",
      "description": "BP: 120/80 mmHg - Normal",
      "created_by": {
        "first_name": "Nurse Fatima",
        "email": "nurse@clinic.com"
      },
      "created_at": "2026-02-14T14:30:00Z"
    }
  ]
}
```

---

### View Single Record

Get complete details of a medical record including all attachments and notes.

**Endpoint:**
```http
GET /api/medical-records/records/{record_id}/
Authorization: Token your_auth_token
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `record_id` | integer | Medical record ID from list |

**Response:**
```json
{
  "id": 1,
  "title": "Diabetes Diagnosis",
  "record_type": "DIAGNOSIS",
  "record_date": "2026-02-15",
  "description": "Fasting glucose test indicates Type 2 Diabetes",
  "diagnosis_code": "E11.9",
  "symptoms": "Increased thirst, frequent urination, fatigue",
  "created_by": {
    "id": "doctor-uuid",
    "first_name": "Dr. Ahmed",
    "email": "doctor@clinic.com"
  },
  "is_confidential": false,
  "requires_followup": true,
  "followup_date": "2026-04-15",
  "created_at": "2026-02-15T10:00:00Z",
  "updated_at": "2026-02-15T10:00:00Z",
  
  "prescription": {
    "medication_name": "Metformin",
    "dosage": "500mg",
    "frequency": "Twice daily",
    "duration": "Ongoing",
    "instructions": "Take with meals to minimize stomach upset",
    "quantity": 60,
    "refills": 3
  },
  
  "allergy": null,
  
  "attachments": [
    {
      "id": 10,
      "file_name": "lab_results_2026_02_15.pdf",
      "description": "Fasting glucose and HbA1c test results",
      "file_type": "application/pdf",
      "file_size": 245678,
      "file": "https://dzmedilink.duckdns.org/media/medical_records/attachments/2026/02/15/lab_results_2026_02_15.pdf",
      "uploaded_at": "2026-02-15T10:30:00Z"
    }
  ],
  
  "notes": [
    {
      "id": 50,
      "note_type": "PROVIDER",
      "content": "Patient education provided on diet and lifestyle changes. Recommended to increase daily exercise and reduce sugar intake.",
      "created_by": {
        "first_name": "Dr. Ahmed",
        "email": "doctor@clinic.com"
      },
      "created_at": "2026-02-15T11:00:00Z",
      "is_locked": true
    },
    {
      "id": 51,
      "note_type": "PATIENT",
      "content": "Starting exercise routine. Will monitor blood sugar regularly.",
      "created_by": {
        "first_name": "Ahmed",
        "email": "ahmed@example.com"
      },
      "created_at": "2026-02-16T09:00:00Z",
      "is_locked": false
    }
  ]
}
```

---

### Search and Filter

Filter and search your medical records:

**List by Record Type:**
```http
GET /api/medical-records/records/my-records/?record_type=ALLERGY
```

**Find Records Requiring Follow-up:**
```http
GET /api/medical-records/records/my-records/?requires_followup=true
```

**Search by Keywords:**
```http
GET /api/medical-records/records/my-records/?search=blood
```

**Combine Filters:**
```http
GET /api/medical-records/records/my-records/?record_type=DIAGNOSIS&requires_followup=true&search=diabetes
```

---

## Record Types

Your medical records can be organized by type:

| Type | Examples | Who Creates | Important For |
|------|----------|-------------|----------------|
| `DIAGNOSIS` | Diabetes, Hypertension | Doctor | Understanding health conditions |
| `PRESCRIPTION` | Medications | Doctor | Tracking current medications |
| `ALLERGY` | Penicillin, Peanuts | Doctor/Patient | Safety and avoiding triggers |
| `LAB_RESULT` | Blood test, Urinalysis | Lab/Doctor | Health metrics and abnormalities |
| `IMAGING` | X-ray, MRI, CT scan | Hospital/Doctor | Visual health assessment |
| `PROCEDURE` | Surgery, Vaccination | Doctor | Medical history |
| `NOTE` | Clinical observations | Doctor/Nurse | Provider notes on your care |
| `VACCINATION` | COVID-19, Flu | Doctor/Clinic | Immunization record |
| `OTHER` | General notes | Anyone | Miscellaneous information |

---

## Add Personal Information

You can add notes and document your own health information.

### Add Note to Record

Add your personal observations or experiences related to a record:

**Endpoint:**
```http
POST /api/medical-records/records/{record_id}/notes/
Authorization: Token your_auth_token
Content-Type: application/json
```

**Request Body:**
```json
{
  "content": "Started new exercise routine. Energy levels improving. Some occasional mild headaches but manageable."
}
```

**Response:**
```json
{
  "id": 52,
  "note_type": "PATIENT",
  "content": "Started new exercise routine. Energy levels improving. Some occasional mild headaches but manageable.",
  "created_by": {
    "first_name": "Ahmed",
    "email": "ahmed@example.com"
  },
  "created_at": "2026-02-20T14:00:00Z",
  "is_locked": false
}
```

---

## Attachments

### Add Attachment

Upload documents, lab results, or medical reports to your records.

**Endpoint:**
```http
POST /api/medical-records/records/{record_id}/attachments/
Authorization: Token your_auth_token
Content-Type: multipart/form-data
```

**Form Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | file | Yes | PDF, image, or document file |
| `file_name` | string | Yes | Original file name |
| `description` | string | No | What this file is about |

**Request (using curl):**
```bash
curl -X POST \
  https://dzmedilink.duckdns.org/api/medical-records/records/1/attachments/ \
  -H "Authorization: Token your_token" \
  -F "file=@lab_results.pdf" \
  -F "file_name=lab_results_feb_2026" \
  -F "description=February lab results from clinic"
```

**Response:**
```json
{
  "id": 11,
  "file_name": "lab_results_feb_2026",
  "file_type": "application/pdf",
  "file_size": 234567,
  "description": "February lab results from clinic",
  "file": "https://dzmedilink.duckdns.org/media/medical_records/attachments/2026/02/20/lab_results_feb_2026.pdf",
  "uploaded_at": "2026-02-20T15:30:00Z"
}
```

### Download Files

Files are available via the `file` URL in responses. Simply click or download the URL:

```
https://dzmedilink.duckdns.org/media/medical_records/attachments/2026/02/20/lab_results_feb_2026.pdf
```

---

## Export Records

### Export Single Record as PDF

Export one medical record as a formatted PDF document.

**Endpoint:**
```http
GET /api/medical-records/records/{record_id}/export-pdf/?include_attachments=true
Authorization: Token your_auth_token
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_attachments` | boolean | false | Include references to attachments |

**Response:** PDF file download
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="medical_record_1_2026-02-15.pdf"
```

**Usage:**
```bash
curl -X GET \
  "https://dzmedilink.duckdns.org/api/medical-records/records/1/export-pdf/?include_attachments=true" \
  -H "Authorization: Token your_token" \
  -o my_medical_record.pdf
```

### Export All Records Summary

Get a comprehensive PDF summary of all your medical records.

**Endpoint:**
```http
GET /api/medical-records/records/export-summary/
Authorization: Token your_auth_token
```

**Response:** PDF file download
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="medical_records_summary_1.pdf"
```

**Includes:**
- Complete medical history
- All diagnoses
- Current prescriptions
- Allergies and warnings
- Recent notes
- Vaccination status

**Usage:**
```bash
curl -X GET \
  "https://dzmedilink.duckdns.org/api/medical-records/records/export-summary/" \
  -H "Authorization: Token your_token" \
  -o my_complete_medical_records.pdf
```

---

## Manage Provider Access

### View Your Providers

See which providers have access to your medical records.

**Endpoint:**
```http
GET /api/medical-records/provider-access/my-providers/
Authorization: Token your_auth_token
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "provider": {
        "id": "provider-uuid",
        "user": {
          "email": "doctor@clinic.com",
          "first_name": "Dr. Ahmed"
        },
        "provider_type": "DOCTOR"
      },
      "access_type": "FULL",
      "is_active": true,
      "granted_at": "2026-02-15T10:00:00Z",
      "expires_at": null,
      "reason": "Ongoing diabetes management"
    },
    {
      "id": 2,
      "provider": {
        "id": "nurse-uuid",
        "user": {
          "email": "nurse@clinic.com",
          "first_name": "Nurse Fatima"
        },
        "provider_type": "NURSE"
      },
      "access_type": "FULL",
      "is_active": true,
      "granted_at": "2026-02-20T14:30:00Z",
      "expires_at": null,
      "reason": "Home care - Wound dressing"
    }
  ]
}
```

### Grant Provider Access

Allow a provider to view your medical records:

**Endpoint:**
```http
POST /api/medical-records/provider-access/
Authorization: Token your_auth_token
Content-Type: application/json
```

**Request Body:**
```json
{
  "provider": "provider-uuid",
  "access_type": "FULL",
  "reason": "For follow-up consultation on diabetes management"
}
```

**Response:**
```json
{
  "id": 3,
  "provider": {
    "id": "provider-uuid",
    "user": {
      "email": "specialist@hospital.com",
      "first_name": "Dr. Specialist"
    }
  },
  "access_type": "FULL",
  "is_active": true,
  "granted_at": "2026-02-21T10:00:00Z",
  "reason": "For follow-up consultation on diabetes management"
}
```

### Revoke Provider Access

Remove a provider's access to your records:

**Endpoint:**
```http
POST /api/medical-records/provider-access/{access_id}/revoke/
Authorization: Token your_auth_token
```

**Response:**
```json
{
  "message": "Provider access has been revoked.",
  "access": {
    "id": 3,
    "is_active": false
  }
}
```

---

## Common Workflows

### Prepare for a Doctor's Appointment

```
1. Review your medical records
   GET /api/medical-records/records/my-records/

2. Export your medical summary
   GET /api/medical-records/records/export-summary/

3. Share with the doctor (optional)
   Print or email the exported PDF

4. Grant temporary access (optional)
   POST /api/medical-records/provider-access/
```

### Track Your Health Condition

```
1. Find records of your condition
   GET /api/medical-records/records/my-records/?search=diabetes

2. Review all related records
   GET /api/medical-records/records/{record_id}/

3. Add your observations
   POST /api/medical-records/records/{record_id}/notes/
   (e.g., "Blood sugar readings normal after diet change")

4. Share with providers as needed
   POST /api/medical-records/provider-access/
```

### Manage Medication Information

```
1. Find your prescription records
   GET /api/medical-records/records/my-records/?record_type=PRESCRIPTION

2. View each prescription details
   GET /api/medical-records/records/{record_id}/

3. Check current medications
   Review prescription.frequency and duration

4. Add notes about side effects or concerns
   POST /api/medical-records/records/{record_id}/notes/
```

### Review Your Allergy Information

```
1. Find all allergies
   GET /api/medical-records/records/my-records/?record_type=ALLERGY

2. Keep list current
   Review each allergy record

3. Share with providers
   Grant access OR export summary including allergies
```

---

## Error Handling

### Unauthorized Access

**Error Code:** 401 UNAUTHORIZED

**Response:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Solution:**
- Verify your token is in the Authorization header
- Re-login if token expired
- Check format: `Authorization: Token <token>`

### Record Not Found

**Error Code:** 404 NOT FOUND

**Response:**
```json
{
  "error": "Medical record not found."
}
```

**Solution:**
- Verify the record ID is correct
- The record may have been deleted or archived

### Permission Denied

**Error Code:** 403 FORBIDDEN

**Response:**
```json
{
  "error": "You do not have permission to access this resource."
}
```

**Solution:**
- Ensure you're logged in as the patient who owns the record
- Cannot access other patient's records

### PDF Generation Failed

**Error Code:** 503 SERVICE UNAVAILABLE

**Response:**
```json
{
  "error": "PDF generation is not available."
}
```

**Solution:**
- Server-side issue, try again later
- Contact support if problem persists

### Invalid Query Parameters

**Error Code:** 400 BAD REQUEST

**Response:**
```json
{
  "record_type": ["Invalid choice. Valid choices are: DIAGNOSIS, PRESCRIPTION, ..."]
}
```

**Solution:**
- Use valid values from the Record Types table
- Check parameter spelling

---

## Integration Checklist

Before fully connecting the patient app:

- [ ] Authentication working (token obtained)
- [ ] Can retrieve my medical records list
- [ ] Can view single record with all details
- [ ] Can add personal notes to records
- [ ] Can upload attachments
- [ ] Can download/export records as PDF
- [ ] Can view provider access list
- [ ] Can grant access to new providers
- [ ] Can revoke provider access
- [ ] Tested all error cases
- [ ] PDF export working
- [ ] Search and filter working

---

## Best Practices

1. **Keep Records Current** - Add notes about significant health events
2. **Regular Exports** - Periodically export your medical summary for personal records
3. **Grant Selective Access** - Only give providers the access they need
4. **Review Regularly** - Check your records for accuracy
5. **Manage Allergies** - Keep allergy information current and accurate
6. **Share Wisely** - Export/share records only when necessary for care

---

**Last Updated:** 2026-04-08
**API Version:** 1.0
