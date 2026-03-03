# Appointments Frontend Integration Guide

This doc describes the full appointment UX flow, the REST/WebSocket endpoints to call, what data to show on provider profiles (doctor/clinic/nurse), and how pricing/limits/ratings/social links fit in.

## Public provider discovery
- List providers: `GET /api/provider/public/` (filters: `provider_type`, `search`, `is_available`, `is_home_service`, `specialty`, `city`, `ordering`).
- Detail provider: `GET /api/provider/public/{provider_id}/`.
- Type-specific lists: `/api/provider/public/doctors/`, `/nurses/`, `/clinics/`.
- Serializer source: provider list/detail serializers in docs: [providers/serializers/provider.py](../providers/serializers/provider.py#L1-L200) (list) and [providers/serializers/provider.py](../providers/serializers/provider.py#L200-L360) (detail).
- What the public detail returns (per type):
  - `doctor`: [DoctorPublicSerializer](../providers/serializers/doctor.py#L84-L160) — name, gender, experience, bio, availability flags, specialties, services (title/description/price/duration/is_home_service), profile image.
  - `nurse`: analogous public serializer (fields: name, experience, availability, home service flag, services).
  - `clinic`: clinic public serializer (name/logo/availability/addresses; see providers/serializers/clinic.py).
  - `services`: bundled under the detail serializer for doctors/nurses; for clinics you’ll typically fetch services via their providers or service catalog.
  - `addresses`: returned in provider detail via address generic relation.
- Ratings: provider public list/detail now return rating aggregates (average + count, and distribution on detail) sourced from `ReviewAggregate`.
- Social media: provider detail now returns visible social links (platform, url, label) from `SocialMediaLink`.

## Provider profile UI (what to show)
- Identity: `name`, `provider_type`, profile image (doctor profile_image, clinic logo, nurse profile_image).
- Status: provider is already approved in public endpoints (no pending ones shown).
- Availability flags: `is_available`, `is_home_service_available` (doctor/nurse); clinics have `is_available`.
- Experience: `years_of_experience` (doctor/nurse).
- Specialties: list from doctor public serializer.
- Services (for booking): from doctor/nurse public serializer — each has `id`, `title`, `description`, `price` (custom if set, else base), `duration_minutes`, `is_home_service`.
- Consultation pricing: doctor profile carries `consultation_price`, `home_visit_price`, `online_consultation_price`, `currency` ([providers/models/doctor.py](../providers/models/doctor.py#L60-L140)). If the user leaves “services” empty during booking, treat it as consultation-only and price from these fields.
- Daily appointment limit: `Provider.daily_appointment_limit` (default 0 = unlimited). If you want a limit of 20/day, set this field to 20 on the provider; booking create validates against this.
- Addresses: provided in provider detail serializer via generic Address relation; provider list now also returns the primary address for quick access (choose primary in address data to control what shows). **Note:** addresses may be stored against the `User` content type rather than the `Provider` content type — the public serializers now query both, so all addresses are returned correctly.
- Ratings/social: see notes above (not wired into provider public serializer yet).

### Example: Provider detail (doctor)

```json
{
   "id": "prov-123",
   "provider_type": "DOCTOR",
   "name": "Dr. Jane Doe",
   "rating": {"average": 4.7, "count": 128, "distribution": {"5": 90, "4": 28, "3": 8, "2": 1, "1": 1}},
   "social_links": [
      {"platform": "FACEBOOK", "platform_display": "Facebook", "url": "https://fb.com/drjane", "custom_label": null},
      {"platform": "LINKEDIN", "platform_display": "LinkedIn", "url": "https://linkedin.com/in/drjane", "custom_label": null}
   ],
   "services": [
      {"id": 201, "title": "General Consultation", "description": "30 min in-clinic", "price": "3500.00", "duration_minutes": 30, "is_home_service": false},
      {"id": 202, "title": "Home Visit", "description": "Home check-up", "price": "5000.00", "duration_minutes": 45, "is_home_service": true}
   ],
   "doctor": {
      "full_name": "Dr. Jane Doe",
      "gender_display": "Female",
      "years_of_experience": 12,
      "biography": "Family medicine specialist...",
      "consultation_price": "3500.00",
      "home_visit_price": "5000.00",
      "online_consultation_price": "3000.00",
      "currency": "DZD",
      "specialties": [
         {"id": 10, "title": "Family Medicine", "slug": "family-medicine", "is_primary": true}
      ]
   },
   "addresses": [
      {"id": 1, "street": "12 Clinic St", "city": "Algiers", "state": "AL", "zip_code": "16000", "country": "Algeria", "is_primary": true, "address_type": "CLINIC"},
      {"id": 2, "street": "45 Home Ave", "city": "Algiers", "state": "AL", "zip_code": "16010", "country": "Algeria", "is_primary": false, "address_type": "HOME"}
   ],
   "primary_address": {"id": 1, "street": "12 Clinic St", "city": "Algiers", "state": "AL", "zip_code": "16000", "country": "Algeria", "is_primary": true, "address_type": "CLINIC"}
}
```

## Booking flow (patient side)
1) User opens provider detail (public endpoint).
2) User taps “Book now”. Show:
   - Date selector and time selector.
   - Location type: `CLINIC`, `HOME`, `ONLINE`. Enforce address if HOME, meeting link later if ONLINE (provider sets during confirm).
   - Service picker (multi-select). If empty, it becomes consultation-only; use provider consultation prices for display.
   - Optional notes/reason.
3) Submit appointment create: `POST /api/appointments/`
   - Payload (key fields): `provider`, optional `service` or `service_ids` (list, multi-service), `scheduled_date`, optional `scheduled_time`, optional `duration_minutes` (defaults to 30), `location_type`, `clinic_address`/`home_address` as applicable, `reason`, `notes`.
   - Validation: date/time not in past; provider availability + double-booking; provider daily limit; home address required for HOME.
   - Status: new appointment is `PENDING`.
   - Notifications/WebSocket: `new_appointment` sent to provider groups and appointment group.

### Example: Appointment create request

```json
{
   "provider": "prov-123",
   "service_ids": [201, 202],
   "scheduled_date": "2026-03-10",
   "scheduled_time": "15:30:00",
   "duration_minutes": 45,
   "location_type": "CLINIC",
   "clinic_address": 1,
   "reason": "Follow-up for blood pressure",
   "notes": "Prefer afternoon slots"
}
```
4) Provider confirms/rejects:
   - Confirm: `POST /api/appointments/{id}/confirm/` (provider only). For ONLINE, must pass `meeting_link`. Status -> `CONFIRMED`; WS `appointment_confirmed` to patient + group.
   - Reject: `POST /api/appointments/{id}/reject/` with `rejection_reason`. Status -> `REJECTED`; WS `appointment_rejected` to patient + group.
5) Patient or provider cancel: `POST /api/appointments/{id}/cancel/` with `reason`, `notes`. Status -> `CANCELLED`; WS `appointment_cancelled` to counterpart + group.
6) Reschedule (either participant): `POST /api/appointments/{id}/reschedule/` with `scheduled_date`, `scheduled_time`, optional `notes`. Validates availability and transitions. Status -> `RESCHEDULED`; WS `appointment_rescheduled` to both + group.
7) Completion & no-show (provider only): `POST /api/appointments/{id}/complete/`, `POST /api/appointments/{id}/no_show/`; emit respective WS events.
8) Deletion: `DELETE /api/appointments/{id}/` deletes without WS; prefer cancel to keep audit trail.

## Availability & limits
- Availability checks live in `SchedulingService.check_provider_available` ([appointments/services.py](../appointments/services.py#L1-L120)): enforces booking window, provider time off, weekly availability slots, and conflict detection.
- Daily limit: `Provider.daily_appointment_limit` respected during create validation; 0 means unlimited. Set to 20 for the initial cap.
- Time slots helper endpoints: `/api/available-slots/`, `/api/provider-schedule/` to build calendars.

## Multi-service & pricing
- Primary service (optional) plus `service_ids` multi-select; stored via `AppointmentService` through table. If empty, treat as consultation-only and show consultation price from doctor profile.
- Doctor service pricing: base `Service.price` plus optional `DoctorService.custom_price`; front end should display `price = custom_price or service.price` (same for nurses via `NurseService`).
- Total price on appointment detail is computed server-side ([appointments/serializers.py](../appointments/serializers.py#L128-L220)).

## WebSocket real-time updates
- Connect authenticated user to: `ws/appointments/` (all their appointments) and optionally `ws/appointments/{appointment_id}/` on detail pages.
- Event types handled by consumer: `new_appointment`, `appointment_confirmed`, `appointment_rejected`, `appointment_cancelled`, `appointment_rescheduled`, `appointment_completed`, `appointment_no_show`, `appointment_reminder`, `appointment_updated` ([appointments/consumers.py](../appointments/consumers.py#L1-L110)).
- Group names: `user_{user_id}_appointments`, `appointment_{appointment_id}`. Backend broadcasts via `WebSocketBroadcaster`.

## Auto-cancel of expired appointments
- Helper: `AppointmentService.auto_cancel_past_appointments(grace_minutes=15)` cancels PENDING/CONFIRMED/RESCHEDULED whose scheduled time passed, marking reason `NO_RESPONSE`.
- Notifications: cancellation signals will notify both sides with `cancelled_by: system`.
- Scheduled job: run `python manage.py auto_cancel_past_appointments --grace-minutes 15` via cron/Task Scheduler.

## Frontend integration checklist
- Provider profile page: show name, type, profile image/logo, availability, experience, specialties, services (with price/duration/home flag), consultation prices, addresses, ratings (when wired), social links (when wired), daily slots left if you surface limit (compute from limit minus existing active for the day).
- Booking form: provider id, date/time, location type, address (if HOME), services multi-select (or none for consultation), notes/reason. Validate time is in future; display provider-specific booking errors to user.
- Post-booking: listen on WS; refresh appointment detail on any event type; show meeting link after provider confirms ONLINE.
- Show allowed actions per appointment using `allowed_actions` from appointment list/detail serializers (avoid showing buttons the server will reject).

## Appointment UI building blocks

### Appointment card (list item)
- Required fields from appointment list serializer: `id`, `provider_name`, `patient_name` (if patient-facing skip), `service_name` or `selected_services`, `scheduled_date`, `scheduled_time`, `location_type_display`, `status_display`, `is_upcoming`, `allowed_actions`.
- Optional enrich: `meeting_link` when status is `CONFIRMED` and location `ONLINE`.

Example card payload snippet:
```json
{
   "id": "appt-789",
   "provider": "prov-123",
   "provider_name": "Dr. Jane Doe",
   "patient_name": "You",
   "service_name": "General Consultation",
   "scheduled_date": "2026-03-10",
   "scheduled_time": "15:30:00",
   "location_type_display": "At Clinic",
   "status": "PENDING",
   "status_display": "Pending",
   "is_upcoming": true,
   "allowed_actions": {
      "can_confirm": false,
      "can_cancel": true,
      "can_reschedule": true
   }
}
```

### Appointment detail
- Fields from detail serializer: provider info (name/email/type), patient info (name/email/phone), `selected_services` (with prices), `total_price`, `scheduled_date/time`, `location_type`, addresses, `meeting_link`, `status`, `reason`, `notes`, cancellation info, `allowed_actions`, timestamps.

Example detail payload snippet:
```json
{
   "id": "appt-789",
   "provider_name": "Dr. Jane Doe",
   "provider_email": "jane@example.com",
   "patient_name": "You",
   "selected_services": [
      {"service_id": "201", "service_name": "General Consultation", "price": "3500.00", "currency": "DZD"},
      {"service_id": "202", "service_name": "Home Visit", "price": "5000.00", "currency": "DZD"}
   ],
   "total_price": "8500.00",
   "scheduled_date": "2026-03-10",
   "scheduled_time": "15:30:00",
   "duration_minutes": 45,
   "location_type": "CLINIC",
   "clinic_address": 1,
   "meeting_link": null,
   "status": "PENDING",
   "reason": "Follow-up for blood pressure",
   "notes": "Prefer afternoon slots",
   "allowed_actions": {"can_cancel": true, "can_reschedule": true, "can_confirm": false},
   "created_at": "2026-03-02T11:00:00Z"
}
```

## Known gaps / TODOs
- (None for providers in this flow) — addresses now resolved correctly via dual content-type lookup (User + Provider); city and primary_address in list also fixed.
