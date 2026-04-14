# Medical Folder Workflow - Implementation Guide

Last verified: 2026-04-14

## Goal

Ensure the patient medical folder is complete, consistent, and usable across:
- Patient self-history review
- Provider and nurse access
- Appointment and nurse-request based care flows
- Health data collection/export

## What Was Fixed

### 1) Unified Access Across Two Access Systems

Your codebase uses two access models:
- `medical_record.ProviderAccess` (patient user based)
- `patients.ProviderPatientAccess` (patient record based)

Medical-record permission/query logic was updated to support both, so nurse/provider visibility no longer breaks when only one grant type exists.

### 2) Patient Ownership Resolution Improved

Patients can now access records when linked by either:
- `medical_record.patient`
- `medical_record.patient_record.linked_user`

This fixed hidden-history cases where records existed under `patient_record` only.

### 3) Provider/Nurse Auto-Grant Sync Improved

Auto-grant workflows now sync both access systems:
- Appointment confirmation/reschedule path now also updates `medical_record.ProviderAccess`.
- Nurse-request acceptance path now auto-grants access in both models.

### 4) Complete Patient Data Bundle Endpoint Added

New endpoint:
- `GET /api/medical-records/records/my-health-data/`

This returns one consolidated payload for patient verification and data collection, including:
- Medical records
- Prescriptions
- Appointments
- Nurse requests
- Provider access grants
- Summary counters

### 5) Record Creation Extended

Medical record create serializer now supports either:
- `patient`
- `patient_record_id`

with role-safe validation.

## Key Endpoints

Base prefix:
- `/api/medical-records/`
- `/api/patients/` (legacy/support endpoints)

### Patient History and Folder

1. List medical records (patient scope)
- `GET /api/medical-records/records/my-records/`

2. Get full record details
- `GET /api/medical-records/records/{id}/`

3. Export one record as PDF
- `GET /api/medical-records/records/{id}/export-pdf/?include_attachments=true`

4. Export all records summary PDF
- `GET /api/medical-records/records/export-summary/`

5. Consolidated health data bundle (new)
- `GET /api/medical-records/records/my-health-data/`

Example:
```bash
curl -X GET "http://localhost:8000/api/medical-records/records/my-health-data/" \
  -H "Authorization: Bearer <token>"
```

Example response shape:
```json
{
  "generated_at": "2026-04-14T12:10:00Z",
  "patient": {
    "id": "...",
    "email": "patient@example.com"
  },
  "summary": {
    "medical_records": 12,
    "prescriptions": 6,
    "appointments": 9,
    "nurse_requests": 3,
    "provider_access_grants": 5
  },
  "medical_records": [],
  "prescriptions": [],
  "appointments": [],
  "nurse_requests": [],
  "provider_access": []
}
```

### Provider/Nurse Access

1. Get patient records (provider/nurse/admin)
- `GET /api/medical-records/records/patient/{patient_user_id}/`

2. Add note to record
- `POST /api/medical-records/records/{id}/notes/`

3. Add attachment
- `POST /api/medical-records/records/{id}/attachments/`

4. Check provider access grants
- `GET /api/medical-records/access/`
- `GET /api/medical-records/access/my-patients/`

### Access Management

1. Patient grants provider access
- `POST /api/medical-records/access/`

2. Revoke grant
- `POST /api/medical-records/access/{id}/revoke/`

3. Renew grant
- `POST /api/medical-records/access/{id}/renew/`

## Nurse Request and Appointment Integration

### Appointment flow
When appointment is confirmed/rescheduled:
- provider-patient relationship is created/updated in `patients.ProviderPatientAccess`
- corresponding `medical_record.ProviderAccess` is now also synced for linked users

### Nurse request flow
When nurse request is accepted:
- patient record is resolved/created if needed
- nurse gets `FULL` access in `patients.ProviderPatientAccess`
- nurse also gets synced `FULL` access in `medical_record.ProviderAccess` for linked user

This aligns behavior with nurse docs expecting immediate medical-folder access after acceptance.

## Validation Checklist

1. Patient can list records linked through patient user and patient_record.
2. Nurse/provider can view records after appointment confirmation.
3. Nurse/provider can view records after nurse-request acceptance.
4. Patient can export single record and full summary PDF.
5. Patient can call `my-health-data` and retrieve complete health history bundle.
6. Provider can add notes only when access and permissions allow.

## Recommended Frontend Usage

1. For patient timeline screen, call:
- `/api/medical-records/records/my-health-data/`

2. For detailed records UI, still use:
- `/api/medical-records/records/my-records/`
- `/api/medical-records/records/{id}/`

3. For nurse app "before visit" safety checks:
- `/api/medical-records/records/patient/{patient_user_id}/?record_type=ALLERGY`
- `/api/medical-records/records/patient/{patient_user_id}/?record_type=PRESCRIPTION`

4. For privacy and sharing:
- use `/api/medical-records/access/*` and `/api/patients/share-tokens/*`

## Notes

- Django project check passes after these updates.
- Existing API contracts are preserved; new endpoint is additive.
