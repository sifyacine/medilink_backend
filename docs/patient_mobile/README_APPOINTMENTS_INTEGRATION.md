# Patient Integration README - Appointments

## Scope
Use this guide to integrate patient appointment flows with the current backend.

Base API root: `/api/`
Auth header: `Authorization: Token <token>`

## Endpoints Used By Patients
1. `GET /api/appointments/`
2. `POST /api/appointments/`
3. `GET /api/appointments/{id}/`
4. `POST /api/appointments/{id}/cancel/`
5. `POST /api/appointments/{id}/reschedule/`
6. `GET /api/appointments/upcoming/`
7. `GET /api/appointments/past/`
8. `GET /api/appointments/history/`
9. `GET /api/appointments/{id}/prescription/`
10. `GET /api/available-slots/?provider=<provider_id>&date=YYYY-MM-DD`
11. `GET /api/appointment-choices/`

## Typical Patient Flow
1. Fetch provider list from provider public APIs.
2. Fetch available slots with `GET /api/available-slots/`.
3. Create appointment with `POST /api/appointments/`.
4. Poll or refresh `GET /api/appointments/upcoming/` for status changes.
5. Allow patient cancellation/rescheduling while status allows.
6. Move completed/cancelled records to `GET /api/appointments/past/`.

## Create Appointment (Patient)
Endpoint: `POST /api/appointments/`

Minimal body example:
```json
{
  "provider": "<provider_uuid>",
  "scheduled_date": "2026-03-20",
  "scheduled_time": "10:30:00",
  "duration_minutes": 30,
  "location_type": "CLINIC",
  "reason": "Follow-up"
}
```

Multi-service booking example:
```json
{
  "provider": "<provider_uuid>",
  "scheduled_date": "2026-03-20",
  "scheduled_time": "10:30:00",
  "duration_minutes": 45,
  "location_type": "HOME",
  "service_ids": ["<service_uuid_1>", "<service_uuid_2>"],
  "home_address": "<address_uuid>",
  "reason": "Home nursing + follow-up"
}
```

## Cancel Appointment
Endpoint: `POST /api/appointments/{id}/cancel/`

```json
{
  "reason": "PATIENT_REQUEST",
  "notes": "Conflict in schedule"
}
```

## Reschedule Appointment
Endpoint: `POST /api/appointments/{id}/reschedule/`

```json
{
  "scheduled_date": "2026-03-21",
  "scheduled_time": "12:00:00",
  "notes": "Need later slot"
}
```

## Notes For Frontend
1. Appointment list/detail serializers return `allowed_actions`; use it to drive UI buttons.
2. For online appointments, provider must confirm with a meeting link.
3. Use `history` for timeline tabs and `upcoming` for active cards.
4. Keep date/time values in ISO formats expected by DRF.

## Common Errors
1. `400`: scheduling conflict, invalid slot, invalid status transition.
2. `403`: user not participant of appointment.
3. `404`: appointment/provider not found.
