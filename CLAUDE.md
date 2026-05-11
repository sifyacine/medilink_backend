# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --settings=core.settings.development

# Start dev server
python manage.py runserver --settings=core.settings.development

# Collect static files (production)
python manage.py collectstatic --noinput --settings=core.settings.production

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts

# Run a specific test class or method
python manage.py test accounts.tests.TestClassName.test_method_name
```

No linting or formatting tools are configured in this project.

## Architecture Overview

Medilink is a healthcare marketplace backend built with **Django 6 + DRF 3.16**, deployed with **Daphne (ASGI)** for WebSocket support. There is no Celery — async work is handled via Django signals and Django Channels consumers.

### Settings

- Default (manage.py): `core.settings.development` — SQLite/Postgres local, in-memory channel layer, console email backend
- Production: `core.settings.production` — DigitalOcean Postgres (SSL), Redis channel layer, SMTP email, HTTPS enforced
- Pass `--settings=core.settings.production` explicitly when needed

### User & Role System

- Custom email-based `AbstractBaseUser` in [accounts/models/user.py](accounts/models/user.py)
- Three top-level roles: `PATIENT`, `PROVIDER`, `ADMIN` (with sub-roles: `SUPER_ADMIN`, `MODERATOR`, `SUPPORT`, `CONTENT_EDITOR`)
- All role enums live in [common/enums.py](common/enums.py)
- DRF permission classes live in [common/permissions.py](common/permissions.py) (`IsPatient`, `IsVerifiedProvider`, `IsDoctor`, `IsNurse`, `IsAdmin`, etc.)

### Provider Polymorphism

Providers have a base `Provider` model (FK to `User`) with a `provider_type` field, then one-to-one submodels per type: `Doctor`, `Nurse`, `Clinic`, `Laboratory`, `VTC`, `Seller` — all in [providers/models/](providers/models/).

Provider status flow: `PENDING → APPROVED | REFUSED | SUSPENDED`.

### Key App Responsibilities

| App | Responsibility |
|-----|---------------|
| `accounts` | User model, registration/login (dj-rest-auth + django-allauth), password reset |
| `providers` | Provider profiles and type-specific submodels |
| `patients` | PatientRecord for patients without accounts (MED-XXXXXX IDs + linking tokens) |
| `appointments` | Scheduling, availability, time-off; double-booking prevention via `SchedulingService` |
| `nurse_requests` | On-demand nursing: NurseRequest + NurseOffer with real-time WebSocket flow |
| `prescriptions` | Prescription + PrescriptionItem management |
| `invoices` | Invoice + InvoiceLineItem + payment tracking |
| `medical_record` | Patient medical history and attachments |
| `notifications` | Firebase FCM push + WebSocket live notification stream |
| `reviews` | Universal ratings system |
| `reports` | Content moderation reports |
| `services` | Medical services catalog; `DoctorService`/`NurseService` store custom per-provider pricing |
| `address` | Generic address via Django ContentType (multiple addresses per any model) |
| `platform_content` | CMS: landing page, FAQs, blog posts, legal documents, announcements |
| `common` | Shared utilities, enums, validators, exceptions, permission classes (no models) |
| `admins` | Admin-facing views and user management |

### Business Logic Pattern

Each app has a `services.py` containing business logic extracted from views. Views/viewsets call service functions rather than implementing logic directly.

### Real-time / WebSocket

WebSocket consumers are in each app's `consumers.py`; routes are registered in `core/asgi.py`:

- `ws/notifications/` → per-user notification stream
- `ws/appointments/` → appointment status updates
- `ws/nurse-requests/` → nursing request flow
- `ws/dashboard/` → admin/provider dashboard

All WebSocket connections require token authentication via `WebSocketAuthMiddlewareStack`.

Channel layer: in-memory for development, Redis (`REDIS_URL`) for production.

### Notifications

Notifications are dispatched via Django signals (`*/signals.py` in each app). The `notifications` app handles both:
1. Firebase FCM push via `firebase-admin` (credentials in `firebase-credentials.json`)
2. WebSocket delivery through the Channels consumer

### Patient Record Linking

`PatientRecord` (in `patients`) supports patients without accounts. They get a `patient_unique_id` (format `MED-XXXXXX`) and a one-time `linking_token` that lets them later create an account and link their record.

### Custom Service Pricing

Providers can override base service prices. `DoctorService` and `NurseService` store custom prices per provider. Serializers check for a custom price first, falling back to the base `Service` price.

### Authentication

Token-based (`DRF TokenAuthentication`) + session auth. Registration and login use `dj-rest-auth` with a custom `django-allauth` adapter in [accounts/adapters.py](accounts/adapters.py).

### Generic Addresses

The `address` app uses `django.contrib.contenttypes` so a single `Address` model can relate to any model (providers, clinics, patients). Each entity can have multiple addresses with a type (`HOME`, `WORK`, `CLINIC`, etc.).

## Deployment

Production runs on a Linux server with:
- **Nginx** as reverse proxy (serves static/media from `/var/www/medilink/`)
- **Daphne** as the ASGI server for HTTP + WebSockets
- Systemd service files: `daphne.service`, `gunicorn.service`
