# Patient Integration README - My Medical Records

## Scope
This guide covers patient-facing medical record access and export APIs.

Base API root: `/api/`
Auth header: `Authorization: Token <token>`

## Main Endpoints For Patients
1. `GET /api/medical-records/records/my-records/`
2. `GET /api/medical-records/records/`
3. `GET /api/medical-records/records/{id}/`
4. `PATCH /api/medical-records/records/{id}/`
5. `POST /api/medical-records/records/{id}/attachments/`
6. `POST /api/medical-records/records/{id}/notes/`
7. `GET /api/medical-records/records/{id}/export-pdf/`
8. `GET /api/medical-records/records/export-summary/`
9. `GET /api/patients/my-records/` (linked patient-record aggregate)

## Which Endpoint To Use
1. Use `/api/medical-records/records/my-records/` for account-linked patient records.
2. Use `/api/patients/my-records/` when your app depends on linked `PatientRecord` aggregation and simplified shape.
3. If your patient always has account-linked records only, use the medical-record endpoint family for consistency.

## Get My Medical Records
Endpoint: `GET /api/medical-records/records/my-records/`

Query support follows the underlying viewset filters (record_type, ordering, search where applicable).

## Update My Medical Record
Endpoint: `PATCH /api/medical-records/records/{id}/`

Example:
```json
{
  "title": "Updated blood pressure check",
  "description": "Feeling better",
  "requires_followup": true,
  "followup_date": "2026-03-25"
}
```

Rule:
1. Patients can only modify their own records.
2. On provider-created records, restricted fields (like `diagnosis_code`, `record_type`) are blocked for patients.

## Add Attachment
Endpoint: `POST /api/medical-records/records/{id}/attachments/`

Send as `multipart/form-data`:
1. `file`
2. `file_name`
3. `description` (optional)

## Export PDFs
1. Single record: `GET /api/medical-records/records/{id}/export-pdf/?include_attachments=true`
2. Summary: `GET /api/medical-records/records/export-summary/`

If PDF service is missing (reportlab), backend returns `503`.
