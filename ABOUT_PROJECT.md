# Medilink Backend — Project Reference

> **Purpose:** Quick-reference document for AI assistants and developers. Load this instead of re-exploring the codebase each session.

---

## 1. Overview

**Medilink** is a healthcare platform backend built with **Django 6.0** + **Django REST Framework 3.16**. It connects **patients** with **healthcare providers** (doctors, nurses, clinics, labs, medical sellers, VTC transport) and handles appointments, medical records, prescriptions, invoices, on-demand nursing, reviews, reports, and push notifications.

- **Auth:** Email-based (no username), Token authentication via `dj-rest-auth` + `django-allauth`
- **Database:** PostgreSQL (via `psycopg`)
- **Real-time:** Django Channels (WebSockets) for nurse requests & notifications
- **Push notifications:** Firebase Cloud Messaging (FCM)
- **File uploads:** Profile images, documents, certificates (Django media files)
- **i18n:** Multilingual fields (English, Arabic, French) on services, specialties, invoices
- **Settings:** Split settings (`core/settings/base.py`, `development.py`, `production.py`), env vars via `django-environ`

---

## 2. Tech Stack

| Component | Technology |
|---|---|
| Framework | Django 6.0.1, DRF 3.16.1 |
| Auth | dj-rest-auth 5.0.2, django-allauth 0.57.0, Token auth |
| Database | PostgreSQL (psycopg 3.3.2) |
| WebSockets | Django Channels 4.0.0, channels-redis 4.2.0 |
| Push Notifications | firebase-admin 7.1.0 (FCM) |
| Filtering | django-filter 24.3 |
| CORS | django-cors-headers 4.9.0 |
| Images | Pillow 12.1.0 |
| HTTP client | httpx 0.28.1 |
| Env | django-environ 0.12.0 |

---

## 3. Django Apps (16 apps)

| App | Purpose | Key Models |
|---|---|---|
| `accounts` | Custom User, auth, password reset | `User`, `PasswordResetToken` |
| `providers` | Provider profiles (6 types) | `Provider`, `Doctor`, `Nurse`, `Clinic`, `Laboratory`, `Seller`, `VTC`, `ProviderStatusHistory` |
| `patients` | Patient records (with/without accounts) | `PatientRecord`, `ProviderPatientAccess`, `MedicalRecordShareToken`, `ShareTokenAccessLog` |
| `appointments` | Scheduling, availability, time-off | `Appointment`, `ProviderAvailability`, `ProviderTimeOff`, `AppointmentService`, `AppointmentReminder` |
| `medical_record` | Clinical records, attachments, access | `MedicalRecord`, `Prescription` (inline), `Allergy`, `MedicalRecordAttachment`, `MedicalRecordNote`, `MedicalRecordAccessLog`, `ProviderAccess` |
| `prescriptions` | Standalone prescriptions with items | `Prescription`, `PrescriptionItem` |
| `invoices` | Billing, payments, activities | `Invoice`, `InvoiceItem`, `Payment`, `InvoiceActivity` |
| `nurse_requests` | On-demand nursing (Uber-like flow) | `NurseServiceRequest`, `NurseOffer`, `RequestHistory` |
| `notifications` | FCM push & in-app notifications | `DeviceToken`, `Notification` |
| `reviews` | Universal rating system | `Review`, `ReviewHelpful`, `ReviewAggregate` |
| `reports` | Content moderation, user bans | `Report`, `ReportAggregate`, `UserBan` |
| `services` | Service catalog | `Service`, `DoctorService`, `NurseService`, `ProviderCustomService` |
| `specialties` | Medical specialties | `Specialty`, `DoctorSpecialty` |
| `address` | Generic addresses (ContentType) | `Address` |
| `social_media` | Social links (ContentType) | `SocialMediaLink` |
| `admins` | Admin-specific views | (no models — uses `providers` models) |
| `common` | Shared utilities | Enums, validators, exception handlers, permissions, i18n helpers |

---

## 4. User Model & Roles

**Custom User** (`accounts.User`, table: `users`):
- **Auth:** Email-based login (`USERNAME_FIELD = 'email'`, no username)
- **Roles:** `PATIENT`, `PROVIDER`, `ADMIN` (enum: `common.enums.UserRole`)
- **Account status:** `ACTIVE`, `SUSPENDED`, `DEACTIVATED` (enum: `UserAccountStatus`)
- **Key fields:** `email`, `role`, `account_status`, `first_name`, `last_name`, `phone_number`, `email_verified`, `profile_completed`, `profile_completion_percentage`
- **Security:** `failed_login_attempts`, `locked_until` (brute-force protection), `last_login_ip`
- **Audit:** `created_at`, `updated_at`, `created_by`, `updated_by`

---

## 5. Provider Hierarchy

```
User (role=PROVIDER)
  └── Provider (OneToOne)
        ├── Doctor (OneToOne) + DoctorCertification (FK)
        ├── Nurse (OneToOne) + NurseCertification (FK)
        ├── Clinic (OneToOne)
        ├── Laboratory (OneToOne)
        ├── Seller (OneToOne)
        └── VTC (OneToOne)
```

- **Provider types:** `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY`, `VTC`, `SELLER` (enum: `ProviderType`)
- **Provider status:** `PENDING` → `APPROVED` / `REFUSED` / `SUSPENDED` (enum: `ProviderStatus`)
- Admin verifies/refuses providers via `admins` app
- Each subtype has: `license_number` (unique), verification docs, `is_verified`, `is_available`

---

## 6. Dual Patient Linking Pattern

Many models support **two patient types** (exactly one required):
- `patient_user` → FK to `User` (registered patient)
- `patient_record` → FK to `PatientRecord` (unregistered patient)

**Used in:** `Appointment`, `MedicalRecord`, `Prescription`, `Invoice`, `NurseServiceRequest`

**PatientRecord** features:
- `patient_unique_id` (auto: `MED-XXXXXXXX`)
- `linking_token` for account linking
- Soft-delete support (`is_deleted`, `deleted_at`, `deleted_by`)
- `MedicalRecordShareToken` for QR/link sharing with providers

---

## 7. Key Enums (`common/enums.py`)

| Enum | Values |
|---|---|
| `UserRole` | PATIENT, PROVIDER, ADMIN |
| `ProviderStatus` | PENDING, APPROVED, REFUSED, SUSPENDED |
| `ProviderType` | DOCTOR, NURSE, CLINIC, LABORATORY, VTC, SELLER |
| `UserAccountStatus` | ACTIVE, SUSPENDED, DEACTIVATED |

Additional enums are defined inline in models (appointment status, invoice status, etc.).

---

## 8. Architecture Patterns

| Pattern | Details |
|---|---|
| **Generic Foreign Keys** | `Address`, `SocialMediaLink`, `Review`, `Report` all use Django ContentType framework |
| **UUID primary keys** | `Appointment`, `Invoice`, `InvoiceItem`, `Payment`, `Review`, `Report`, `Notification`, `NurseServiceRequest`, `Prescription`, `PrescriptionItem` |
| **Multilingual fields** | `_en`, `_ar`, `_fr` suffixes on `Service`, `Specialty`, `ProviderCustomService`, `Invoice` notes/terms |
| **Soft delete** | `PatientRecord` (`is_deleted`, `deleted_at`, `deleted_by`) |
| **Audit trails** | `ProviderStatusHistory`, `RequestHistory`, `InvoiceActivity`, `MedicalRecordAccessLog`, `ShareTokenAccessLog` |
| **Service layer** | Many apps have `services.py` for business logic separation |
| **Signal handlers** | `appointments/signals.py`, `invoices/signals.py`, `medical_record/signals.py`, `nurse_requests/signals.py` |
| **Custom permissions** | Per-app `permissions.py` files |
| **Custom exception handler** | `common.exception_handlers.medilink_exception_handler` |

---

## 9. API Endpoints Summary

Base URL: All endpoints prefixed with `api/` except admin site and allauth.

### Auth (`api/auth/`)
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `patient/register/` | Register patient |
| POST | `provider/register/` | Register provider |
| POST | `login/` | Login |
| POST | `logout/` | Logout |
| GET/PATCH | `me/` | Get/update current user |
| POST | `status/` | Check account status |
| POST | `password/reset/` | Request password reset |
| POST | `password/reset/confirm/` | Confirm password reset |

### Providers (`api/provider/`)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `status/` | Provider approval status |
| GET/PUT/PATCH | `profile/` | Provider profile (Doctor/Nurse) |
| GET/PUT/PATCH | `clinic/` | Clinic profile |
| GET | `public/` | List public providers |
| GET | `public/{id}/` | Public provider detail |
| GET | `public/doctors/` | List public doctors |
| GET | `public/nurses/` | List public nurses |
| GET | `public/clinics/` | List public clinics |
| GET | `public/laboratories/` | List public labs |
| CRUD | `clinic/`, `laboratory/`, `seller/`, `vtc/` | Provider type management |

### Admin (`api/admin/`)
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `providers/` | List all providers |
| GET | `providers/{id}/` | Provider detail |
| POST | `providers/{id}/verify/` | Approve provider |
| POST | `providers/{id}/refuse/` | Refuse provider |

### Appointments (`api/appointments/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `/`, `{id}/` | Appointment CRUD |
| POST | `{id}/confirm/` | Confirm appointment |
| POST | `{id}/reject/` | Reject appointment |
| POST | `{id}/cancel/` | Cancel appointment |
| POST | `{id}/complete/` | Complete appointment |
| POST | `{id}/no_show/` | Mark no-show |
| POST | `{id}/reschedule/` | Reschedule |
| GET | `upcoming/`, `past/`, `today/`, `week/` | Filtered lists |
| GET | `stats/`, `history/`, `search/` | Analytics & search |
| CRUD | `{id}/services/` | Manage appointment services |

### Availability (`api/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `provider-availability/` | Manage schedule slots |
| GET | `provider-availability/my_schedule/` | Current provider schedule |
| POST | `provider-availability/bulk_update/` | Bulk schedule update |
| CRUD | `provider-time-off/` | Manage time off |
| GET | `available-slots/` | Get available booking slots |
| GET | `provider-schedule/` | View provider schedule |

### Medical Records (`api/medical-records/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `records/` | Medical record CRUD |
| POST | `records/{id}/attachments/` | Add attachment |
| POST | `records/{id}/notes/` | Add note |
| GET | `records/{id}/export-pdf/` | Export PDF |
| GET | `records/my-records/` | Patient's own records |
| GET | `records/patient/{id}/` | Records by patient |
| CRUD | `access/` | Provider access management |

### Patients (`api/patients/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `/` | Patient record CRUD |
| POST | `link-account/` | Link record to user account |
| GET | `me/` | Current patient record |
| GET | `my-records/` | My medical records |
| CRUD | `share-tokens/` | Manage share tokens |
| GET | `records/share/{token}/` | Access via share token |

### Prescriptions (`api/prescriptions/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `/` | Prescription CRUD |
| POST | `{id}/issue/` | Issue prescription |
| POST | `{id}/cancel/` | Cancel prescription |
| POST | `{id}/upload-pdf/` | Upload PDF |
| GET/POST | `{id}/items/` | Manage items |
| GET | `my-prescriptions/` | Patient's prescriptions |
| GET | `my-issued/` | Doctor's issued prescriptions |

### Invoices (`api/invoices/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `/` | Invoice CRUD |
| POST | `{id}/send/` | Send invoice |
| POST | `{id}/cancel/` | Cancel invoice |
| POST | `{id}/record_payment/` | Record payment |
| POST | `from_appointment/` | Create from appointment |
| GET | `my/` | Patient's invoices |
| GET | `statistics/`, `financial_summary/` | Financial analytics |
| CRUD | `payments/` | Payment management |

### Nurse Requests (`api/nurse-requests/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `patient/nurse-requests/` | Patient creates/manages requests |
| POST | `patient/nurse-requests/{id}/accept/` | Accept nurse offer |
| POST | `patient/nurse-requests/{id}/start/` | Start service |
| POST | `patient/nurse-requests/{id}/complete/` | Complete service |
| GET | `nurse/available-requests/` | Nurse sees available requests |
| POST | `nurse/available-requests/{id}/accept/` | Nurse accepts request |
| POST | `nurse/available-requests/{id}/counter-offer/` | Nurse counter-offers |
| CRUD | `nurse/my-services/` | Nurse manages their services |

### Notifications (`api/notifications/`)
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `register/` | Register device token |
| POST | `unregister/` | Unregister device |
| GET | `/` | List notifications |
| PATCH | `{id}/read/` | Mark as read |
| POST | `mark-all-read/` | Mark all read |
| DELETE | `{id}/`, `clear-all/` | Delete notifications |

### Reviews (`api/reviews/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `/` | Review CRUD |
| POST | `{id}/respond/` | Provider responds |
| POST/DELETE | `{id}/helpful/` | Helpful vote |
| POST | `{id}/flag/` | Flag review |
| GET | `my-reviews/`, `received/`, `aggregate/` | Filtered views |

### Reports (`api/reports/`)
| Method | Endpoint | Purpose |
|---|---|---|
| CRUD | `reports/` | Report CRUD |
| POST | `reports/{id}/take_action/` | Admin action |
| GET | `reports/pending/` | Pending reports |
| CRUD | `bans/` | User ban management |
| POST | `bans/{id}/lift/` | Lift ban |

### Other
| Prefix | App |
|---|---|
| `api/services/` | Service catalog CRUD, DoctorService, NurseService |
| `api/specialties/` | Specialty CRUD, DoctorSpecialty |
| `api/addresses/` | Address CRUD (generic) |
| `api/social-links/` | Social media links CRUD (generic) |

---

## 10. WebSocket Endpoints

| Path | Consumer | Purpose |
|---|---|---|
| `ws/nurse-requests/{request_id}/` | `NurseRequestConsumer` | Patient subscribes to specific request updates |
| `ws/nurse-requests/available/` | `NurseRequestConsumer` | Nurse subscribes to available requests |
| `ws/notifications/` | (notifications app) | Real-time notification delivery |

Auth: Token-based WebSocket authentication via `WebSocketAuthMiddlewareStack`.

---

## 11. Project Structure

```
medilink_backend/
├── core/                    # Django project config
│   ├── settings/
│   │   ├── base.py          # Shared settings (DB, apps, REST config)
│   │   ├── development.py   # Dev overrides
│   │   └── production.py    # Prod overrides
│   ├── urls.py              # Root URL config
│   ├── asgi.py              # ASGI + WebSocket routing
│   └── wsgi.py              # WSGI entry point
├── accounts/                # User auth & management
│   ├── models/              # User, PasswordResetToken
│   ├── views/               # auth, profile, registration, password_reset, status, user_profile
│   ├── serializers/         # auth, profile, user
│   ├── adapters.py          # Custom allauth adapter
│   ├── permissions.py
│   ├── services.py          # Auth business logic
│   └── utils.py
├── providers/               # Provider profiles
│   ├── models/              # Provider, Doctor, Nurse, Clinic, Lab, Seller, VTC, StatusHistory
│   ├── views/
│   └── serializers/
├── admins/                  # Admin-only endpoints
│   ├── views/
│   └── serializers/
├── patients/                # Patient records
├── appointments/            # Scheduling
├── medical_record/          # Clinical records
├── prescriptions/           # Prescription management
├── invoices/                # Billing & payments
├── nurse_requests/          # On-demand nursing
│   ├── consumers.py         # WebSocket consumers
│   └── routing.py           # WebSocket URL patterns
├── notifications/           # Push & in-app notifications
├── reviews/                 # Rating system
├── reports/                 # Moderation & bans
├── services/                # Service catalog
├── specialties/             # Medical specialties
├── address/                 # Generic addresses
├── social_media/            # Social links
├── common/                  # Shared utilities
│   ├── enums.py             # UserRole, ProviderType, ProviderStatus, UserAccountStatus
│   ├── validators.py
│   ├── permissions.py
│   ├── exception_handlers.py
│   ├── i18n.py
│   └── utils.py
├── docs/                    # Documentation
├── manage.py
├── requirements.txt
├── ERD.md                   # Entity Relationship Diagram (Mermaid)
└── firebase-credentials.json
```

---

## 12. Key Settings

| Setting | Value |
|---|---|
| `AUTH_USER_MODEL` | `accounts.User` |
| `DEFAULT_AUTHENTICATION` | `TokenAuthentication`, `SessionAuthentication` |
| `DEFAULT_PERMISSION` | `IsAuthenticated` |
| `PAGINATION` | `PageNumberPagination`, PAGE_SIZE=20 |
| `EXCEPTION_HANDLER` | `common.exception_handlers.medilink_exception_handler` |
| `ACCOUNT_AUTHENTICATION_METHOD` | `email` |
| `ACCOUNT_USERNAME_REQUIRED` | `False` |
| `ACCOUNT_EMAIL_VERIFICATION` | `none` |
| `CHANNEL_LAYERS` | InMemoryChannelLayer (dev), Redis (prod) |
| `ASGI_APPLICATION` | `core.asgi.application` |
| Database | PostgreSQL |
| `SITE_ID` | 1 |

---

## 13. Invoice Settings

| Setting | Default | Purpose |
|---|---|---|
| `MEDILINK_AUTO_INVOICE_APPOINTMENTS` | `False` | Auto-create invoice on appointment completion |
| `MEDILINK_AUTO_INVOICE_NURSE_REQUESTS` | `False` | Auto-create invoice on nurse request completion |
| `MEDILINK_AUTO_SEND_INVOICES` | `False` | Auto-send invoices when created |

---

## 14. Deployment Info

- **Domain:** `dzmedilink.duckdns.org` (backend), `dzmedilink.netlify.app` (frontend)
- **CORS:** Configured for localhost (3000, 5173, 8080, 8000) + production domains
- **Static files:** Served from `staticfiles/` directory
- **Media files:** Uploaded to `media/` directory (served in dev via Django)

---

*Last updated: March 2, 2026*
