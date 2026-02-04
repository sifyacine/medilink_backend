# Frontend fix prompt – align with backend

Use this prompt when working on the **React frontend** (provider dashboard / Medilink web app) so the frontend matches the backend.

---

## Backend contract (current state)

### Notifications – FCM token registration

- **Endpoint:** `POST /api/notifications/register/`
- **Auth:** Required (Bearer token).
- **Body (JSON):**
  - `token` (string, required): FCM device token from Firebase.
  - `device_type` (string, optional): `"android"` | `"ios"` | `"web"`. Defaults to `"web"` if omitted.
- **Success (200/201):**
  ```json
  { "success": true, "message": "...", "device_id": "<uuid string>" }
  ```
- **Errors:** `400` (missing token / invalid device_type), `401` (unauthorized), `500` (server error; check backend logs).

Frontend should send `device_type: "web"` for the React web app when calling this endpoint.

---

## Frontend issues to fix

Fix the following in the **React frontend** so the app works with the backend above.

### 1. Doctor dashboard – undefined API config

- **Error:** `TypeError: Cannot read properties of undefined (reading 'DOCTOR_STATS')` in `doctorService.ts` (around line 16).
- **Error:** `TypeError: Cannot read properties of undefined (reading 'DOCTOR_APPOINTMENTS')` in `doctorService.ts` (around line 212).
- **Fix:** Ensure the object that holds `DOCTOR_STATS` and `DOCTOR_APPOINTMENTS` (e.g. API routes or endpoint constants) is defined and imported correctly before use. Add null checks or fix the import so it is never undefined when `getStats` and `getAppointments` run.

### 2. Doctor dashboard – appointment service method

- **Error:** `TypeError: appointmentService.getAppointments is not a function` (called from `doctorService.ts` fallback, around line 221).
- **Fix:** Ensure `appointmentService` is the correct module/object and that it exports a `getAppointments` function (or the correct method name used by the backend). Fix the import or the fallback call so it uses the existing method name (e.g. `getAppointments` or `getAppointmentList`).

### 3. Notifications – register request

- **Current behavior:** Frontend calls `POST .../api/notifications/register/` and receives **500** from the server.
- **Backend:** Already fixed (token handling, UUID, device_type default `"web"`). After deployment and migrations, the endpoint should return 200/201.
- **Frontend:** Ensure the request body is exactly:
  - `token`: the FCM token string.
  - `device_type`: `"web"` for the web app.
- **Optional:** On 500, show a user-friendly message (e.g. “Could not enable notifications. Try again later.”) and optionally log the response for debugging.

---

## Summary

- **Backend:** Notifications register endpoint is implemented and expects `token` + optional `device_type` (use `"web"` for web). Returns `success`, `message`, and `device_id` (UUID string).
- **Frontend:** Fix `doctorService.ts` so `DOCTOR_STATS` and `DOCTOR_APPOINTMENTS` are never read from undefined, and so the appointment fallback calls an existing method on `appointmentService`. Ensure FCM register sends `device_type: "web"` and handles 500 with a clear message.

Once these are done, backend and frontend are on the same page.
