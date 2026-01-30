# Auth Me Endpoint (`/api/auth/me/`)

Central endpoint for the **current authenticated user** to:

- Fetch their account and role-specific profile
- Update a limited, safe subset of self-service profile fields

---

## 1. Endpoint Overview

- **Base URL:** `/api/auth/me/`
- **Methods:** `GET`, `PATCH`, `PUT`
- **Auth:** `Authorization: Token <token>`
- **Content-Type:**
  - `application/json` for normal updates
  - `multipart/form-data` when sending `profile_image`

---

## 2. GET `/api/auth/me/`

Returns a single JSON object representing the current user and their role-specific profile.

### 2.1 Top-level user fields (all roles)

Read-only in GET:

- `id` (int)
- `email` (string)
- `role` (`PATIENT` | `PROVIDER` | `ADMIN`)
- `role_display` (string)
- `account_status` (`ACTIVE` | `SUSPENDED` | `DEACTIVATED`)
- `account_status_display` (string)
- `is_active` (bool)
- `is_staff` (bool)
- `email_verified` (bool)
- `email_verified_at` (datetime or null)
- `profile_completed` (bool)
- `profile_completion_percentage` (0–100)
- `last_login` (datetime or null)
- `last_login_ip` (string or null)
- `created_at` (datetime)
- `updated_at` (datetime)

Additional provider hints (for `role = PROVIDER`):

- `provider_type` (`DOCTOR` | `NURSE` | `CLINIC` | `LABORATORY` | `SELLER` | `VTC`)
- `provider_type_display` (human label)
- `subtype` (alias of `provider_type`)
- `subtype_display` (alias of `provider_type_display`)

Other aggregates:

- `provider_profile` – object, only for providers (see below)
- `patient_profile` – minimal object for patients (currently placeholder)
- `addresses` – list of address objects linked to the user and related provider profiles

### 2.2 Provider profile structure (role = PROVIDER)

`provider_profile` combines provider status with the concrete subtype profile:

```json
"provider_profile": {
  "status": "APPROVED" | "PENDING" | "REFUSED" | "SUSPENDED",
  "refusal_reason": "..." | null,
  "approved_at": "2026-01-27T10:00:00Z" | null,
  "verified_at": "2026-01-27T10:00:00Z" | null,
  "provider_type": "DOCTOR",
  "provider_type_display": "Doctor",

  "doctor": { ... }
  // or "nurse": { ... }
  // or "clinic": { ... }
  // or "laboratory": { ... }
  // or "seller": { ... }
  // or "vtc": { ... }
}
```

#### 2.2.1 Doctor provider (`provider_type = DOCTOR`)

`provider_profile.doctor` fields (read-only from GET):

- Identity:
  - `id`, `email`
  - `first_name`, `last_name`, `full_name`
  - `gender`, `gender_display`, `date_of_birth`
  - `profile_image` (URL)
  - `phone_number` (string)
- Professional:
  - `license_number`
  - `years_of_experience`
  - `biography`
  - `degree_document` (URL)
- Availability:
  - `is_verified` (bool)
  - `is_available` (bool)
  - `is_home_service_available` (bool)
- Extra:
  - `specialties` [] (lightweight)
  - `services` [] (lightweight)
  - `provider_status` { status, provider_type, provider_type_display, approved_at, verified_at }
  - `created_at`, `updated_at`

#### 2.2.2 Nurse provider (`provider_type = NURSE`)

`provider_profile.nurse` fields (read-only from GET):

- Identity:
  - `id`, `email`
  - `first_name`, `last_name`, `full_name`
  - `gender`, `gender_display`, `date_of_birth`
  - `profile_image` (URL)
  - `phone_number` (string)
- Professional:
  - `license_number`, `certification`
  - `years_of_experience`
  - `biography`
  - `degree_document`
- Entrepreneur docs:
  - `entrepreneur_card_front`, `entrepreneur_card_back`, `entrepreneur_card_pdf`
- Availability:
  - `is_verified` (bool)
  - `is_available` (bool)
  - `is_home_service_available` (bool)
- Extra:
  - `services` []
  - `provider_status` {...}
  - `created_at`, `updated_at`

#### 2.2.3 Clinic provider (`provider_type = CLINIC`)

`provider_profile.clinic` fields:

- `id`, `email`
- `clinic_name`
- `license_number`
- `logo` (image URL)
- `phone_number`
- `email`, `website`
- `description`
- `number_of_beds`
- `has_emergency_services`, `is_24_hours`
- `outpatient_capacity_per_day`
- `license_document`
- `is_verified`, `is_available`

#### 2.2.4 Laboratory provider (`provider_type = LABORATORY`)

`provider_profile.laboratory` fields:

- `id`, `email`
- `lab_name`, `license_number`, `accreditation`
- `phone_number`, `email`, `website`
- `description`
- `license_document`, `accreditation_document`
- `is_verified`, `is_available`

#### 2.2.5 Seller provider (`provider_type = SELLER`)

`provider_profile.seller` fields:

- `id`, `email`
- `business_name`, `tax_id`, `business_type`
- `phone_number`, `email`, `website`
- `description`
- `business_license`, `tax_certificate`
- `is_verified`, `is_available`

#### 2.2.6 VTC provider (`provider_type = VTC`)

`provider_profile.vtc` fields:

- `id`, `email`
- `company_name`, `license_number`
- `phone_number`, `email`, `website`
- `fleet_size`, `vehicle_types`
- `transport_license`, `insurance_certificate`
- `is_verified`, `is_available`

### 2.3 Patient profile (role = PATIENT)

Currently minimal:

```json
"patient_profile": {
  "is_patient": true
}
```

Detailed patient medical data is exposed via dedicated patients endpoints, not `/api/auth/me/`.

### 2.4 Addresses

`addresses` is a list of address objects for the user and (if applicable) their provider/doctor/nurse profiles, with fields like:

- `id`, `street`, `city`, `state`, `zip_code`, `country`
- `latitude`, `longitude`
- `is_primary`, `address_type`, `notes`
- `content_type_name` (e.g. `user`, `doctor`, `clinic`)

---

## 3. PATCH/PUT `/api/auth/me/`

Allows the current user to update a **limited, safe** subset of profile fields.

- **Methods:** `PATCH` (preferred), `PUT` (treated as partial)
- **Body:** JSON, except when uploading `profile_image` (use `multipart/form-data`)
- **Response:** On success, the same payload shape as `GET /api/auth/me/` (full updated profile).

If the request only includes read-only or unknown fields, the API returns:

```json
{
  "detail": "No updatable fields were provided. The /api/auth/me/ endpoint only accepts a limited set of profile fields (for example name, availability, and profile completion flags). Other account changes must be handled by support."
}
```

### 3.1 Editable fields – all roles

Top-level fields that any authenticated user can change via `/api/auth/me/`:

- `profile_completed` (bool)
- `profile_completion_percentage` (int 0–100)

### 3.2 Editable fields – provider doctors & nurses

For `role = PROVIDER` and `provider_type` in `{ DOCTOR, NURSE }`:

Send fields **at the top level** of the JSON body (not nested under `provider_profile`). Accepted fields:

- Personal:
  - `first_name`
  - `last_name`
  - `gender` (one of the allowed enum values)
  - `profile_image` (file field; use `multipart/form-data`)
  - `phone_number`
- Professional:
  - `biography`
  - `years_of_experience` (0–100)
- Availability:
  - `is_available` (available for appointments)
  - `is_home_service_available` (home visits available)

These are written directly to the underlying `Doctor` or `Nurse` model.

**Example (doctor):**

```json
{
  "first_name": "Sara",
  "last_name": "Benkhedda",
  "gender": "FEMALE",
  "biography": "Cardiologist with 8 years of experience.",
  "years_of_experience": 8,
  "phone_number": "+213555000111",
  "is_available": true,
  "is_home_service_available": false,
  "profile_completed": true,
  "profile_completion_percentage": 90
}
```

### 3.3 Editable fields – clinic / laboratory / seller / VTC

For `role = PROVIDER` and `provider_type` in `{ CLINIC, LABORATORY, SELLER, VTC }`:

Accepted top-level fields:

- `phone_number`
- `is_available`
- For clinics only:
  - `profile_image` (stored as `logo` on the Clinic model)

**Example (clinic):**

```json
{
  "phone_number": "+213555000222",
  "is_available": true,
  "profile_completed": true,
  "profile_completion_percentage": 80
}
```

### 3.4 Protected fields (return concise "contact support" errors)

Sensitive provider fields cannot be changed via `/api/auth/me/`:

- `license_number`
- `degree_document`

If the user sends them, the API responds with `400` and short error messages, for example:

```json
{
  "license_number": [
    "This field cannot be changed from the app. Please contact support."
  ],
  "degree_document": [
    "This field cannot be changed from the app. Please contact support."
  ]
}
```

No changes are saved when such errors occur.

### 3.5 Non-provider users sending provider-only fields

If a user who is not a provider (e.g. `PATIENT` or `ADMIN`) sends provider-only fields like `first_name`, `is_available`, etc., the API returns per-field errors:

```json
{
  "first_name": ["This field is only available for provider accounts."],
  "is_available": ["This field is only available for provider accounts."]
}
```

### 3.6 Misconfigured or missing provider profiles

If a provider account has no linked subtype profile (e.g., missing `doctor_profile`), any provider-field update fails with a generic support message:

```json
{
  "detail": "Provider profile is not configured for this account. Please contact support."
}
```

or

```json
{
  "detail": "Profile for this provider type is not available. Please contact support."
}
```

---

## 4. Role-by-role summary

### 4.1 PATIENT

- Can see:
  - All common user fields
  - `patient_profile` placeholder
  - `addresses`
- Can edit via `/api/auth/me/`:
  - `profile_completed`
  - `profile_completion_percentage`
- All medical record changes: use patients/medical_record APIs.

### 4.2 PROVIDER (all subtypes)

- Can see:
  - All common user fields
  - `provider_profile` with subtype block (`doctor`, `nurse`, `clinic`, `laboratory`, `seller`, `vtc`)
  - `addresses`
- Can edit via `/api/auth/me/`:
  - `profile_completed`, `profile_completion_percentage`
  - Plus subtype-specific fields as described above
- Cannot edit via `/api/auth/me/`:
  - Account status (ACTIVE/SUSPENDED/DEACTIVATED)
  - Provider approval/verification status
  - License numbers and core verification documents.

### 4.3 ADMIN

- Can see:
  - All common user fields
  - `addresses`
- Can edit via `/api/auth/me/`:
  - `profile_completed`
  - `profile_completion_percentage`
- All admin and provider approvals: via separate admin endpoints, not `/api/auth/me/`.
