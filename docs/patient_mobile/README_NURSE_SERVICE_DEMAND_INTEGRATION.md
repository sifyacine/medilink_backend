# Patient Integration README - Nurse Service Demand

## Scope
This guide covers the patient on-demand nurse workflow.

Base API root: `/api/nurse-requests/`
Auth header: `Authorization: Token <token>`

## Endpoints Used By Patients
1. `GET /api/nurse-requests/services/`
2. `GET /api/nurse-requests/services/{id}/`
3. `GET /api/nurse-requests/patient/nurse-requests/`
4. `POST /api/nurse-requests/patient/nurse-requests/`
5. `GET /api/nurse-requests/patient/nurse-requests/{id}/`
6. `POST /api/nurse-requests/patient/nurse-requests/{id}/accept/`
7. `POST /api/nurse-requests/patient/nurse-requests/{id}/cancel/`
8. `GET /api/nurse-requests/patient/nurse-requests/saved-addresses/`
9. `POST /api/nurse-requests/patient/nurse-requests/use-saved-address/`

## Create Demand Request (Map Coordinates)
Endpoint: `POST /api/nurse-requests/patient/nurse-requests/`

```json
{
  "service": 1,
  "patient_offered_price": "1500.00",
  "latitude": "36.752500",
  "longitude": "3.042000",
  "city": "Algiers",
  "address_line": "Hydra, Algiers",
  "notes": "Please call before arrival"
}
```

Validation:
1. Service must be active, `service_type=NURSE`, `is_on_demand=true`.
2. `patient_offered_price` must be greater than or equal to service base price.

## Create Demand Request (Saved Address)
Endpoint: `POST /api/nurse-requests/patient/nurse-requests/use-saved-address/`

```json
{
  "service": 1,
  "patient_offered_price": "1500.00",
  "address_id": 5,
  "notes": "Please use the side gate"
}
```

## Accept Nurse Offer
Endpoint: `POST /api/nurse-requests/patient/nurse-requests/{id}/accept/`

```json
{
  "offer_id": 123
}
```

## Cancel Demand Request
Endpoint: `POST /api/nurse-requests/patient/nurse-requests/{id}/cancel/`

```json
{
  "cancellation_reason": "No longer needed"
}
```

## Statuses To Handle In UI
1. `CREATED`
2. `SEARCHING`
3. `NURSE_RESPONDED`
4. `PATIENT_DECISION`
5. `ACCEPTED`
6. `IN_PROGRESS`
7. `COMPLETED`
8. `CANCELLED`

## Error Response Contract
This module uses structured errors:
```json
{
  "success": false,
  "error": {
    "code": "NR3003",
    "message": "Cannot accept offers at this stage"
  }
}
```

Use `error.code` for deterministic client behavior.
