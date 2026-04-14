# Prescriptions API

Last verified: 2026-04-14
Base URL prefix: `/api/`
Auth: `Authorization: Bearer <access_token>`

## Verification Summary

The prescriptions module is implemented and working, and Django startup checks pass.

What was verified in code:
- Prescription create/list/retrieve/update/delete flow via `PrescriptionViewSet`
- Status actions: issue, cancel
- PDF upload action with PDF + size validation
- Patient and doctor scoped listing endpoints
- Choice endpoint for enums used by frontend forms
- Prescription item management via nested route and item viewset

Fixes applied during verification:
- Fixed runtime bug in item ordering aggregation (`models.Max` -> imported `Max`) in `prescriptions/views.py`.
- Fixed permission gap so `POST /api/prescriptions/{id}/items/` now requires the prescription doctor.
- Fixed `POST /api/prescription-items/` creation flow to correctly require `prescription`, enforce draft-only + ownership, and create item safely.

## Status and Business Rules

- Allowed prescription statuses: `DRAFT`, `ISSUED`, `DISPENSED`, `EXPIRED`, `CANCELLED`
- A prescription must reference exactly one patient identity:
  - `patient` (user account) OR
  - `patient_record` (offline record)
- Prescription can be linked to an appointment only if appointment status is `CONFIRMED` or `COMPLETED`.
- A single appointment can have only one prescription.
- Only draft prescriptions can be edited, deleted, or have items added/updated/deleted.
- Issuing is allowed only from draft and only when at least one item exists.

## Endpoint List

### 1) Create Prescription (Doctor only)

- Method: `POST`
- URL: `/api/prescriptions/`
- Permission: authenticated approved doctor

Request example:
```bash
curl -X POST "http://localhost:8000/api/prescriptions/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "9e5f78a9-92ab-4f84-8d09-7f55a0d7d4d1",
    "appointment_id": "ad5e5e16-2e18-4d4e-bb93-cf9d5ea6f911",
    "clinic_id": "8fb2f6be-3ea7-4de3-8268-81d8fd074bcf",
    "diagnosis": "Acute upper respiratory infection",
    "notes": "No penicillin allergy reported",
    "instructions": "Hydrate well and rest",
    "valid_until": "2026-05-01",
    "items": [
      {
        "medication_name": "Paracetamol",
        "medication_type": "TABLET",
        "strength": "500mg",
        "dosage": "1 tablet",
        "frequency": "QID",
        "duration_days": 5,
        "quantity": 20,
        "quantity_unit": "tablets",
        "instructions": "After meals"
      }
    ]
  }'
```

Success response: `201 Created` (detailed prescription object)

Common errors:
- `400` if both/none of `patient_id` and `patient_record_id` are sent
- `400` if appointment is not confirmed/completed
- `400` if appointment already has a prescription
- `403` if requester is not an approved doctor

### 2) List Prescriptions

- Method: `GET`
- URL: `/api/prescriptions/`
- Permission: authenticated
- Scope:
  - Admin: all
  - Doctor: own prescriptions
  - Patient: own prescriptions

Example:
```bash
curl -X GET "http://localhost:8000/api/prescriptions/?ordering=-created_at" \
  -H "Authorization: Bearer <token>"
```

Success response: `200 OK` (list serializer payload, paginated if pagination is enabled)

### 3) Get Prescription Details

- Method: `GET`
- URL: `/api/prescriptions/{prescription_id}/`
- Permission: doctor owner, linked patient, or admin

Example:
```bash
curl -X GET "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/" \
  -H "Authorization: Bearer <token>"
```

### 4) Update Prescription (Draft only)

- Method: `PUT` or `PATCH`
- URL: `/api/prescriptions/{prescription_id}/`
- Permission: doctor owner (or admin per permission class), draft only

PATCH example:
```bash
curl -X PATCH "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Updated notes",
    "instructions": "Take medicine with food"
  }'
```

### 5) Delete Prescription (Draft only)

- Method: `DELETE`
- URL: `/api/prescriptions/{prescription_id}/`
- Permission: doctor owner (or admin per permission class), draft only

Example:
```bash
curl -X DELETE "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/" \
  -H "Authorization: Bearer <token>"
```

### 6) Upload Prescription PDF

- Method: `POST`
- URL: `/api/prescriptions/{prescription_id}/upload-pdf/`
- Content type: `multipart/form-data`
- Permission: prescription doctor
- Validation: must be `.pdf`, max 10 MB

Example:
```bash
curl -X POST "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/upload-pdf/" \
  -H "Authorization: Bearer <token>" \
  -F "pdf_file=@./prescription.pdf"
```

Success response includes `pdf_url`.

### 7) Issue Prescription

- Method: `POST`
- URL: `/api/prescriptions/{prescription_id}/issue/`
- Permission: prescription doctor
- Rules:
  - Current status must be `DRAFT`
  - At least one medication item must exist

Example:
```bash
curl -X POST "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/issue/" \
  -H "Authorization: Bearer <token>"
```

### 8) Cancel Prescription

- Method: `POST`
- URL: `/api/prescriptions/{prescription_id}/cancel/`
- Permission: prescription doctor
- Rules: cannot cancel if already `DISPENSED` or `CANCELLED`

Example:
```bash
curl -X POST "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/cancel/" \
  -H "Authorization: Bearer <token>"
```

### 9) List or Add Items on a Prescription

- Method: `GET`, `POST`
- URL: `/api/prescriptions/{prescription_id}/items/`
- `GET` permission: can view prescription
- `POST` permission: prescription doctor only
- `POST` rule: prescription must be `DRAFT`

GET example:
```bash
curl -X GET "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/items/" \
  -H "Authorization: Bearer <token>"
```

POST example:
```bash
curl -X POST "http://localhost:8000/api/prescriptions/6fce744f-d5ae-4f60-9dc0-ebd6be43dfef/items/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "medication_name": "Amoxicillin",
    "medication_type": "CAPSULE",
    "strength": "500mg",
    "dosage": "1 capsule",
    "frequency": "TID",
    "duration_days": 7,
    "quantity": 21,
    "quantity_unit": "capsules",
    "instructions": "After meals"
  }'
```

### 10) Patient Prescriptions Endpoint

- Method: `GET`
- URL: `/api/prescriptions/my-prescriptions/`
- Permission: authenticated patient
- Query params:
  - `status`
  - `ordering` (allowed: `created_at`, `issued_at`, `valid_until`, `status`, `updated_at` with optional `-`)

Example:
```bash
curl -X GET "http://localhost:8000/api/prescriptions/my-prescriptions/?status=ISSUED&ordering=-issued_at" \
  -H "Authorization: Bearer <token>"
```

### 11) Doctor Issued Prescriptions Endpoint

- Method: `GET`
- URL: `/api/prescriptions/my-issued/`
- Permission: authenticated doctor
- Query params:
  - `status`
  - `patient_id`
  - `from_date` (YYYY-MM-DD)
  - `to_date` (YYYY-MM-DD)
  - `ordering`

Example:
```bash
curl -X GET "http://localhost:8000/api/prescriptions/my-issued/?status=ISSUED&from_date=2026-04-01&to_date=2026-04-14" \
  -H "Authorization: Bearer <token>"
```

### 12) Enum Choices for Frontend Forms

- Method: `GET`
- URL: `/api/prescriptions/choices/`
- Permission: authenticated

Example:
```bash
curl -X GET "http://localhost:8000/api/prescriptions/choices/" \
  -H "Authorization: Bearer <token>"
```

Sample response:
```json
{
  "status": [
    {"value": "DRAFT", "label": "Draft"},
    {"value": "ISSUED", "label": "Issued"}
  ],
  "medication_type": [
    {"value": "TABLET", "label": "Tablet"}
  ],
  "dosage_frequency": [
    {"value": "QD", "label": "Once daily"},
    {"value": "CUSTOM", "label": "Custom schedule"}
  ]
}
```

### 13) Standalone Prescription Item Endpoints

Base route: `/api/prescription-items/`

Available endpoints:
- `GET /api/prescription-items/`
- `POST /api/prescription-items/` (requires `prescription` in body)
- `GET /api/prescription-items/{id}/`
- `PATCH /api/prescription-items/{id}/`
- `DELETE /api/prescription-items/{id}/`

Rules:
- Create/update/delete only for items under draft prescriptions
- Non-admin users can only act on their own doctor-owned prescriptions

Create example:
```bash
curl -X POST "http://localhost:8000/api/prescription-items/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prescription": "6fce744f-d5ae-4f60-9dc0-ebd6be43dfef",
    "medication_name": "Ibuprofen",
    "medication_type": "TABLET",
    "dosage": "1 tablet",
    "frequency": "BID",
    "duration_days": 3,
    "quantity": 6,
    "quantity_unit": "tablets"
  }'
```

## Common Response Fields (Prescription Detail)

Typical fields returned by detail endpoints:
- `id`, `reference_number`
- `patient_id`, `patient_name`
- `doctor_id`, `doctor_name`
- `clinic_id`, `clinic_name`
- `appointment_id`
- `diagnosis`, `notes`, `instructions`
- `items` (array)
- `status`, `status_display`, `is_valid`
- `valid_until`, `issued_at`, `created_at`, `updated_at`
- `pdf_file`, `pdf_url`

## Frontend Implementation Checklist

- Always send auth token.
- Use `/api/prescriptions/choices/` to render enums dynamically.
- Keep editing UI enabled only for `DRAFT` prescriptions.
- Block issue button unless at least one item exists.
- For item creation, prefer nested route (`/api/prescriptions/{id}/items/`) for simpler UX.
- Enforce client-side file type/size checks before calling upload endpoint.
- Handle pagination when listing prescriptions.

## Validation/Error Examples

Invalid custom frequency payload:
```json
{
  "frequency": "CUSTOM"
}
```
Response:
```json
{
  "custom_frequency": ["Custom frequency text is required when frequency is CUSTOM."]
}
```

Duplicate appointment prescription attempt:
```json
{
  "appointment_id": ["This appointment already has a prescription."]
}
```
