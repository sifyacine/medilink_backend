# Patient Integration README - My Invoices

## Scope
Use this guide to integrate patient invoice listing and detail screens.

Base API root: `/api/invoices/`
Auth header: `Authorization: Token <token>`

## Endpoints Used By Patients
1. `GET /api/invoices/my/`
2. `GET /api/invoices/`
3. `GET /api/invoices/{id}/`
4. `POST /api/invoices/{id}/mark_viewed/`

## Recommended Flow
1. Load `GET /api/invoices/my/` for patient-friendly list.
2. Open details with `GET /api/invoices/{id}/`.
3. Immediately call `POST /api/invoices/{id}/mark_viewed/` after opening detail.
4. Filter using `GET /api/invoices/?status=<STATUS>` for tabs (SENT, OVERDUE, PAID).

## My Invoices List
Endpoint: `GET /api/invoices/my/`

Returns invoices for:
1. Direct `patient_user == request.user`
2. Linked patient record `patient_record.linked_user == request.user`

Draft invoices are excluded from patient view.

## Mark As Viewed
Endpoint: `POST /api/invoices/{id}/mark_viewed/`

Empty body is accepted:
```json
{}
```

Behavior:
1. If status is `SENT`, backend changes to `VIEWED`.
2. Non-owner patients get `403`.

## Common Errors
1. `403`: invoice does not belong to current patient.
2. `404`: invoice id not found.
3. `400`: invalid state transitions on restricted actions.
