# Services — Admin Dashboard Integration Guide

> **Audience:** Medilink back-office / dashboard developer  
> **Auth:** All endpoints require `Authorization: Token <token>` from an **ADMIN** account  
> **Base prefix:** `/api/admin/`  
> **Django admin panel:** `http://<host>/admin/`

---

## Table of Contents

1. [Concept: The Services Catalog](#1-concept-the-services-catalog)
2. [Service Types & App Visibility](#2-service-types--app-visibility)
3. [The Two Flags That Control Everything](#3-the-two-flags-that-control-everything)
4. [Provider Adoption — How Nurses & Doctors Join a Service](#4-provider-adoption--how-nurses--doctors-join-a-service)
5. [Admin REST API Reference](#5-admin-rest-api-reference)
   - [Service Catalog CRUD](#51-service-catalog-crud)
   - [Toggle active / on-demand](#52-toggle-active--on-demand)
   - [Catalog statistics](#53-catalog-statistics)
   - [Nurse-Service assignments](#54-nurse-service-assignments)
   - [Doctor-Service assignments](#55-doctor-service-assignments)
   - [Provider custom services](#56-provider-custom-services)
6. [Public / Provider API Reference](#6-public--provider-api-reference)
7. [Django Admin Panel](#7-django-admin-panel)
8. [Multilingual Content](#8-multilingual-content)
9. [End-to-End Workflows](#9-end-to-end-workflows)
   - [Create a new on-demand nurse service](#91-create-a-new-on-demand-nurse-service)
   - [Deactivate a service that's causing issues](#92-deactivate-a-service-thats-causing-issues)
   - [Change the base price of a nurse service](#93-change-the-base-price-of-a-nurse-service)
   - [Audit which nurses offer a service](#94-audit-which-nurses-offer-a-service)
   - [Disable a provider custom service](#95-disable-a-provider-custom-service)
10. [Error Reference](#10-error-reference)
11. [Dashboard UI Checklist](#11-dashboard-ui-checklist)

---

## 1. Concept: The Services Catalog

The **global services catalog** (`services.Service`) is the single source of truth for every service that appears in the Medilink apps. Think of it as a menu: Medilink defines what exists on the menu, and providers choose which items they want to offer.

```
Global Catalog (Service)
      │
      ├── Nurse picks it ──► NurseService  (nurse's custom price + availability)
      ├── Doctor picks it ──► DoctorService (doctor's custom price + availability)
      └── Appears in:
              • Nurse on-demand flow  (is_on_demand=True, service_type=NURSE)
              • Appointment booking   (all types)
              • App service browser   (is_active=True)
```

Providers **do not create** services in the global catalog (nurses cannot; doctors/clinics technically can via the provider API, but it is admin-controlled in practice). Providers only **adopt** catalog entries and optionally override pricing.

**Provider Custom Services** (`ProviderCustomService`) are a separate model — private services a doctor/clinic creates only for their own profile. They do **not** feed the on-demand nurse flow.

---

## 2. Service Types & App Visibility

| `service_type` | Who offers it | Appears in |
|---|---|---|
| `NURSE` | Nurses | Nurse on-demand flow (**only** when `is_on_demand=True`) + appointment booking |
| `DOCTOR` | Doctors / Clinics | Appointment booking (doctor profile, service selection) |
| `VTC` | VTC providers | Health transport booking (future feature) |
| `GENERAL` | Any provider | Generic listings, appointment booking |

> **Rule:** A service only appears in the **on-demand nurse request flow** when **both** `service_type=NURSE` **and** `is_on_demand=True`. Changing either flag immediately removes it from the on-demand feed.

---

## 3. The Two Flags That Control Everything

### `is_active`

The master on/off switch.

| `is_active` | Effect |
|---|---|
| `True` | Service is visible to patients browsing the app, can be offered by nurses/doctors |
| `False` | **Hidden everywhere** — does not appear in search, on-demand feed, or appointment booking. Nurses who already have it in their profile will silently stop receiving requests for it until it is reactivated. |

> Toggling `is_active=False` is the safe way to temporarily remove a service without deleting it or losing nurse assignment history.

### `is_on_demand`

Controls whether the service participates in the **Uber-like nurse request flow**.

| `is_on_demand` | Effect |
|---|---|
| `True` | Nurses who have added this service to their profile will receive real-time FCM notifications when a patient creates a request. The service appears in `GET /api/nurse-requests/services/`. |
| `False` | Service exists only as a regular appointment service. No on-demand requests, no notifications. |

> `is_on_demand=True` **requires** `service_type=NURSE`. Setting it on a DOCTOR service is harmless (it won't break anything) but has no effect on the nurse request flow.

---

## 4. Provider Adoption — How Nurses & Doctors Join a Service

Providers independently opt into catalog services. The admin cannot directly assign a service to a nurse — the nurse must do it themselves (or it can be done through the Django admin `NurseService` form).

```
Nurse App flow:
  GET  /api/nurse-requests/nurse/my-services/          ← shows available services to add
  POST /api/nurse-requests/nurse/my-services/add/       ← nurse opts in
  DELETE /api/nurse-requests/nurse/my-services/{id}/remove/  ← nurse opts out

Doctor App flow:
  GET  /api/services/doctor-services/
  POST /api/services/doctor-services/
  DELETE /api/services/doctor-services/{id}/
```

Once a nurse adopts a service, a `NurseService` row is created linking nurse → service, optionally storing `custom_price` and `custom_duration_minutes`. The `effective_price` used at request time is `custom_price` if set, otherwise `service.price`.

**Admin can:**
- View all assignments via `GET /api/admin/nurse-services/` or `GET /api/admin/doctor-services/`
- Edit `custom_price` / `is_available` via `PATCH /api/admin/nurse-services/{id}/`
- Remove an assignment via `DELETE /api/admin/nurse-services/{id}/`

---

## 5. Admin REST API Reference

All admin endpoints require `Authorization: Token <token>` from an ADMIN user.

### 5.1 Service Catalog CRUD

#### List services

```
GET /api/admin/services/
```

Returns all services (active and inactive) with nurse/doctor adoption counts.

**Query parameters:**

| Param | Type | Example | Description |
|---|---|---|---|
| `service_type` | string | `NURSE` | Filter by type: `NURSE`, `DOCTOR`, `VTC`, `GENERAL` |
| `is_active` | bool | `true` | Show only active or inactive services |
| `is_on_demand` | bool | `true` | Show only on-demand services |
| `is_home_service` | bool | `false` | Filter by home-service flag |
| `specialty` | int | `3` | Filter by specialty ID |
| `currency` | string | `DZD` | Filter by currency |
| `search` | string | `wound` | Full-text search across title (all languages), description, slug |
| `ordering` | string | `-price` | Sort field — prefix `-` for descending |

**Sample response:**
```json
{
  "count": 12,
  "results": [
    {
      "id": 1,
      "title": "Wound Care",
      "slug": "wound-care",
      "service_type": "NURSE",
      "service_type_display": "Nursing Service",
      "price": "750.00",
      "currency": "DZD",
      "currency_display": "Algerian Dinar",
      "duration_minutes": 45,
      "specialty_name": null,
      "is_active": true,
      "is_home_service": true,
      "is_on_demand": true,
      "nurse_count": 8,
      "doctor_count": 0,
      "created_at": "2025-01-10T08:00:00Z",
      "updated_at": "2025-04-20T14:30:00Z"
    }
  ]
}
```

---

#### Create service

```
POST /api/admin/services/
Content-Type: application/json
```

**Required fields:**

| Field | Type | Description |
|---|---|---|
| `title` | string | Primary title (English fallback) |
| `service_type` | string | `NURSE`, `DOCTOR`, `VTC`, or `GENERAL` |
| `price` | decimal | Base price (minimum offer price for on-demand) |
| `currency` | string | `DZD`, `USD`, or `EUR` |
| `duration_minutes` | int | Estimated service duration |

**Optional fields:**

| Field | Type | Description |
|---|---|---|
| `title_en` / `title_ar` / `title_fr` | string | Translated titles |
| `description` / `description_en/ar/fr` | string | Descriptions |
| `specialty_id` | int | Link to a specialty |
| `is_active` | bool | Default `true` |
| `is_home_service` | bool | Default `false` |
| `is_on_demand` | bool | Default `false` — set `true` only for NURSE type |
| `icon` | file | Service icon image |

**Minimal example (new nurse on-demand service):**
```json
{
  "title": "Blood Draw",
  "title_ar": "سحب الدم",
  "title_fr": "Prise de sang",
  "service_type": "NURSE",
  "price": "500.00",
  "currency": "DZD",
  "duration_minutes": 20,
  "is_active": true,
  "is_home_service": true,
  "is_on_demand": true
}
```

**Response:** `201 Created` with full `AdminServiceDetailSerializer` body.

---

#### Get service detail

```
GET /api/admin/services/{id}/
```

Returns full detail including all translations, all nurse and doctor assignments with their custom pricing.

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Wound Care",
    "title_en": "Wound Care",
    "title_ar": "تضميد الجروح",
    "title_fr": "Soins de plaies",
    "description": "...",
    "service_type": "NURSE",
    "price": "750.00",
    "currency": "DZD",
    "is_active": true,
    "is_on_demand": true,
    "nurse_count": 3,
    "nurse_assignments": [
      {
        "id": 12,
        "nurse_id": 5,
        "nurse_name": "Fatima Zohra",
        "custom_price": "800.00",
        "effective_price": "800.00",
        "is_available": true
      }
    ],
    "doctor_count": 0,
    "doctor_assignments": []
  }
}
```

---

#### Update service

```
PATCH /api/admin/services/{id}/
Content-Type: application/json
```

Send only the fields to update. All fields from the create endpoint are writable.

```json
{ "price": "850.00", "title_ar": "رعاية الجروح" }
```

---

#### Delete service

```
DELETE /api/admin/services/{id}/
```

Hard-deletes the service and all nurse/doctor assignments. **Prefer deactivation** (`toggle-active`) unless you are certain no historical data references this service.

---

### 5.2 Toggle active / on-demand

These one-liner actions avoid the need to send a full PATCH body.

#### Toggle `is_active`
```
POST /api/admin/services/{id}/toggle-active/
```
```json
{ "success": true, "is_active": false, "message": "Service \"Wound Care\" deactivated." }
```

#### Toggle `is_on_demand`
```
POST /api/admin/services/{id}/toggle-on-demand/
```
```json
{ "success": true, "is_on_demand": true, "message": "On-demand enabled for \"Blood Draw\"." }
```

---

### 5.3 Catalog statistics

```
GET /api/admin/services/stats/
```

```json
{
  "success": true,
  "data": {
    "total_services": 18,
    "active_services": 15,
    "inactive_services": 3,
    "on_demand_nurse_services": 7,
    "nurse_provider_assignments": 42,
    "doctor_provider_assignments": 31,
    "provider_custom_services": 9,
    "by_type": {
      "NURSE":   { "total": 8,  "active": 7, "on_demand": 7 },
      "DOCTOR":  { "total": 7,  "active": 6, "on_demand": 0 },
      "GENERAL": { "total": 3,  "active": 2, "on_demand": 0 }
    }
  }
}
```

---

### 5.4 Nurse-Service assignments

#### List all nurse assignments
```
GET /api/admin/nurse-services/
```

Useful to audit who is offering what and at what price.

**Filters:** `?is_available=true`, `?service=<id>`, `?service__service_type=NURSE`  
**Search:** nurse name, service title

```json
{
  "count": 42,
  "results": [
    {
      "id": 12,
      "nurse": 3,
      "nurse_name": "Fatima Zohra",
      "nurse_provider_id": 5,
      "service": 1,
      "service_title": "Wound Care",
      "service_type": "NURSE",
      "custom_price": "800.00",
      "effective_price": "800.00",
      "is_available": true,
      "notes": "",
      "created_at": "2025-02-14T10:00:00Z"
    }
  ]
}
```

#### Update an assignment (e.g., correct custom price)
```
PATCH /api/admin/nurse-services/{id}/
```
```json
{ "custom_price": null, "is_available": false }
```
Setting `custom_price` to `null` resets the nurse back to the service's default base price.

#### Remove an assignment
```
DELETE /api/admin/nurse-services/{id}/
```
The nurse will no longer receive on-demand request notifications for this service.

---

### 5.5 Doctor-Service assignments

Same endpoints as nurse services but under `/api/admin/doctor-services/`.

```
GET    /api/admin/doctor-services/
PATCH  /api/admin/doctor-services/{id}/
DELETE /api/admin/doctor-services/{id}/
```

---

### 5.6 Provider custom services

These are services doctors/clinics create privately (not in the global catalog).

```
GET    /api/admin/custom-services/
PATCH  /api/admin/custom-services/{id}/
DELETE /api/admin/custom-services/{id}/
POST   /api/admin/custom-services/{id}/toggle-active/
```

Admins typically use this to **deactivate** a custom service that violates platform guidelines.

---

## 6. Public / Provider API Reference

These endpoints are used by the mobile apps — listed here so you understand the full picture.

| Endpoint | Who calls it | Purpose |
|---|---|---|
| `GET /api/services/` | Anyone | Browse active global services (app home screen) |
| `GET /api/services/?service_type=NURSE&is_on_demand=true` | Patient app | Filter nurse on-demand services |
| `GET /api/services/?service_type=DOCTOR` | Patient app | Filter doctor services for appointment booking |
| `GET /api/services/{id}/` | Anyone | Service detail page |
| `GET /api/nurse-requests/services/` | Patient app | Services available for on-demand nurse request |
| `GET /api/services/nurse-services/` | Nurse app | Nurse's own service profile |
| `POST /api/nurse-requests/nurse/my-services/add/` | Nurse app | Nurse adopts a service |
| `DELETE /api/nurse-requests/nurse/my-services/{id}/remove/` | Nurse app | Nurse drops a service |
| `GET /api/services/doctor-services/` | Doctor app | Doctor's own service profile |

---

## 7. Django Admin Panel

Access at `http://<host>/admin/` with a staff/superuser account.

### Services section

| Model | What you can do |
|---|---|
| **Services → Service** | Full CRUD, bulk activate/deactivate, toggle on-demand. Inline tables show every nurse and doctor who has adopted the service with their custom pricing. |
| **Services → Doctor Service** | View/edit all doctor↔service assignments. Bulk mark available/unavailable. |
| **Services → Nurse Service** | View/edit all nurse↔service assignments. Bulk mark available/unavailable. |
| **Services → Provider Custom Service** | View/deactivate provider-created services. |

### Key admin features

- **Bulk actions** on the Service list: activate, deactivate, enable on-demand, disable on-demand — select multiple rows and apply in one click.
- **Inline nurse/doctor tables** on each Service detail page — instantly see who offers it without leaving the page.
- **Colour-coded type badges** (`NURSE` in blue, `DOCTOR` in purple, `VTC` in amber, `GENERAL` in grey).
- **Search** works across all language variants (EN, AR, FR) so you can find a service by its Arabic name.
- **Translation fieldset** is collapsed by default — expand it to fill in Arabic and French translations.
- The `Availability & Flags` fieldset has inline help text explaining what each flag does.

---

## 8. Multilingual Content

Each service has three title and description fields: `_en`, `_ar`, `_fr`. The primary `title` / `description` fields serve as the English fallback.

### How the app receives the right language

The mobile app should send the `Accept-Language` header (or `?lang=ar`) and the serializer automatically returns the matching field. If the requested language has no content, it falls back to the primary `title`.

```
GET /api/services/?lang=ar
GET /api/services/?lang=fr
GET /api/services/          ← defaults to English
```

### Admin: request all translations at once

```
GET /api/admin/services/{id}/
```
The admin serializer (`AdminServiceDetailSerializer`) always returns all three language fields so the dashboard form can render all translation inputs simultaneously.

### Recommended translation workflow

1. Create the service in English only.
2. Send the `id` to your translator.
3. `PATCH /api/admin/services/{id}/` with `{ "title_ar": "...", "description_ar": "...", "title_fr": "...", "description_fr": "..." }`.
4. The app immediately shows translated text on the next request.

---

## 9. End-to-End Workflows

### 9.1 Create a new on-demand nurse service

**Goal:** Add "IV Infusion Therapy" to the nurse on-demand catalog.

```
POST /api/admin/services/
{
  "title": "IV Infusion Therapy",
  "title_ar": "العلاج بالتسريب الوريدي",
  "title_fr": "Thérapie par perfusion IV",
  "description": "Intravenous fluid and medication delivery at home.",
  "service_type": "NURSE",
  "price": "1500.00",
  "currency": "DZD",
  "duration_minutes": 60,
  "is_active": true,
  "is_home_service": true,
  "is_on_demand": true
}
```

**What happens next:**
- The service immediately appears in `GET /api/nurse-requests/services/` (patient app).
- Nurses who browse `GET /api/nurse-requests/nurse/my-services/` will see it in the "available to add" list.
- When a nurse adds it via the app, they start receiving FCM notifications for patient requests.

---

### 9.2 Deactivate a service that's causing issues

**Goal:** Temporarily hide "Vitamin B12 Injection" while reviewing pricing.

```
POST /api/admin/services/7/toggle-active/
```

**Immediate effects:**
- Disappears from the patient app service browser.
- Disappears from `GET /api/nurse-requests/services/` (nurses will no longer receive requests for it).
- The 4 nurses who had it in their profile keep their `NurseService` rows — they simply stop seeing requests until you reactivate.
- No historical request data is affected.

**To reactivate:**
```
POST /api/admin/services/7/toggle-active/
```

---

### 9.3 Change the base price of a nurse service

```
PATCH /api/admin/services/1/
{ "price": "850.00" }
```

**What changes:**
- All nurses without a `custom_price` set now show `effective_price = 850.00` to patients.
- Nurses who set a `custom_price` are unaffected (their custom price takes precedence).
- Existing completed requests keep their recorded `base_price` — historical records are not changed.
- The patient app shows the new base price as the minimum offer on new requests.

---

### 9.4 Audit which nurses offer a service

**Option A — via detail endpoint:**
```
GET /api/admin/services/1/
```
Returns `nurse_assignments` array with every nurse, their `custom_price`, and `is_available`.

**Option B — via assignments endpoint (paginated, filterable):**
```
GET /api/admin/nurse-services/?service=1
```

**To disable a specific nurse from offering it without removing the assignment:**
```
PATCH /api/admin/nurse-services/12/
{ "is_available": false }
```

---

### 9.5 Disable a provider custom service

A doctor created a custom service with misleading information. Deactivate it without deleting:

```
GET /api/admin/custom-services/?search=provider@email.com
→ find id=3

POST /api/admin/custom-services/3/toggle-active/
{ "success": true, "is_active": false, "message": "Custom service \"..\" deactivated." }
```

The service disappears from the doctor's public profile immediately. The doctor can still see it in their own app as inactive.

---

## 10. Error Reference

| HTTP | Meaning | Fix |
|---|---|---|
| `400 Bad Request` | Validation error — check `detail` or field-level errors | Fix the invalid field |
| `401 Unauthorized` | Missing or invalid token | Include `Authorization: Token <token>` |
| `403 Forbidden` | Authenticated user is not an admin | Use an ADMIN account |
| `404 Not Found` | Service / assignment ID doesn't exist | Check the ID |
| `405 Method Not Allowed` | Wrong HTTP method (e.g. PUT instead of PATCH) | Use PATCH for partial updates |

**Common validation errors:**

```json
{ "price": ["Ensure this value is greater than or equal to 0."] }
{ "service_type": ["\"INVALID\" is not a valid choice."] }
{ "duration_minutes": ["A valid integer is required."] }
```

---

## 11. Dashboard UI Checklist

### Services catalog page

- [ ] Table with columns: Title, Type badge (colour-coded), Price, Duration, Home 🏠, On-demand ⚡, Active toggle, Nurses #, Doctors #
- [ ] Filter bar: service type tabs (`ALL` / `NURSE` / `DOCTOR` / `VTC` / `GENERAL`), Active toggle, On-demand toggle
- [ ] Search box hitting `?search=`
- [ ] **Stats bar** at top: fetch from `GET /api/admin/services/stats/` — show Total, Active, On-Demand Nurse, Nurse Assignments

### Service create / edit form

- [ ] **Basic** tab: Title (EN), Service Type dropdown, Price + Currency, Duration, Specialty picker, Icon upload
- [ ] **Translations** tab: EN / AR / FR title and description inputs side-by-side
- [ ] **Flags** section: Active toggle, Home-service toggle, On-demand toggle (only show when type = NURSE)
- [ ] Disable On-demand toggle when `service_type ≠ NURSE` and explain why

### Service detail / drill-down

- [ ] Show nurse assignments table: nurse name, custom price vs default, is_available toggle, remove button
- [ ] Show doctor assignments table (same)
- [ ] Quick-action buttons: "Deactivate", "Toggle On-Demand"

### Nurse/Doctor assignments page (admin)

- [ ] Fetch from `GET /api/admin/nurse-services/` with filters
- [ ] Allow editing `custom_price` and `is_available` inline
- [ ] Allow removing assignment with confirmation dialog

### Provider custom services page

- [ ] List with provider email, title, price, active status
- [ ] Deactivate / Activate toggle per row
- [ ] Hard-delete option with confirmation dialog
