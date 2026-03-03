# Provider Dashboards - Authentication & Profile API

## Overview

This documentation covers the authentication and profile management APIs for **Provider Web Dashboards**. This includes all provider types: Doctors, Clinics, Laboratories, VTC (Medical Transport), and Sellers/Pharmacies.

Each provider type has specific registration requirements and profile structures.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication Flow](#authentication-flow)
3. [Provider Types](#provider-types)
4. [Registration by Provider Type](#registration-by-provider-type)
   - [Doctor Registration](#doctor-registration)
   - [Clinic Registration](#clinic-registration)
   - [Laboratory Registration](#laboratory-registration)
   - [VTC Registration](#vtc-registration)
   - [Seller/Pharmacy Registration](#sellerpharmacy-registration)
5. [Login](#login)
6. [Account Status & Verification](#account-status--verification)
   - [Provider Status Values](#provider-status-values)
   - [Check Account Status (Public)](#check-account-status-public---no-login-required)
   - [Check Status After Login](#check-status-after-login-authenticated)
7. [Profile Management](#profile-management)
   - [Get My Profile](#get-my-profile)
   - [Update My Profile](#update-my-profile)
8. [Managing Addresses](#managing-addresses)
9. [Error Handling](#error-handling)
10. [Web Integration Examples](#web-integration-examples)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

All authentication endpoints are prefixed with `/api/auth/`

---

## Authentication Flow

### Token-Based Authentication

MediLink uses **Token Authentication**. After successful login or registration, the API returns a token that must be included in all subsequent requests.

```
Authorization: Token <your_token_here>
```

### Provider Registration & Approval Flow

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                       PROVIDER REGISTRATION FLOW                                   │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────────────────────────┐ │
│  │  1. Register   │───▶│  2. Upload     │───▶│  3. Status: PENDING              │ │
│  │  with type-    │    │  Required      │    │     Await admin verification     │ │
│  │  specific      │    │  Documents     │    │                                  │ │
│  │  information   │    │                │    │                                  │ │
│  └────────────────┘    └────────────────┘    └──────────────────────────────────┘ │
│                                                          │                         │
│                                                          ▼                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐   │
│  │                         ADMIN REVIEW                                        │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────────────────┐│   │
│  │  │  APPROVED   │    │  REFUSED    │    │  SUSPENDED                       ││   │
│  │  │  ✓ Full     │    │  ✗ Cannot   │    │  ✗ Temporarily                   ││   │
│  │  │    access   │    │    login    │    │    disabled                      ││   │
│  │  └─────────────┘    └─────────────┘    └──────────────────────────────────┘│   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## Provider Types

| Type | Description | Key Documents Required |
|------|-------------|------------------------|
| `DOCTOR` | Medical doctors | License, Degree |
| `NURSE` | Nursing professionals | License, Degree, Entrepreneur Card |
| `CLINIC` | Medical clinics | License, Business documents |
| `LABORATORY` | Medical laboratories | License, Certifications |
| `VTC` | Medical transport | Transport license |
| `SELLER` | Pharmacies/Medical suppliers | Business license, Tax ID |

---

## Registration by Provider Type

All providers use the same registration endpoint with type-specific required fields.

### Endpoint

```
POST /api/auth/provider/register/
```

### Headers

```
Content-Type: multipart/form-data
```

---

### Doctor Registration

#### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address |
| `password` | string | ✅ | Strong password |
| `password_confirm` | string | ✅ | Must match password |
| `provider_type` | string | ✅ | Must be `DOCTOR` |
| `first_name` | string | ✅ | Doctor's first name |
| `last_name` | string | ✅ | Doctor's last name |
| `phone_number` | string | ✅ | Contact phone number |
| `license_number` | string | ✅ | Medical license number |
| `degree_document` | file | ✅ | Medical degree (PDF/Image) |

#### Example Request

```
POST /api/auth/provider/register/
Content-Type: multipart/form-data

email: doctor@example.com
password: SecurePass123!
password_confirm: SecurePass123!
provider_type: DOCTOR
first_name: Mohamed
last_name: Kaddour
phone_number: +213555123456
license_number: MED-2024-12345
degree_document: [FILE: medical_degree.pdf]
```

#### Success Response

```json
{
    "user": {
        "id": 15,
        "email": "doctor@example.com",
        "role": "PROVIDER",
        "first_name": "Mohamed",
        "last_name": "Kaddour",
        "full_name": "Mohamed Kaddour",
        "phone_number": "+213555123456",
        "is_active": true,
        "profile_completed": false,
        "profile_completion_percentage": 50,
        "created_at": "2026-02-02T10:00:00Z"
    },
    "provider": {
        "id": 10,
        "status": "PENDING",
        "status_display": "Pending Verification",
        "provider_type": "DOCTOR",
        "provider_type_display": "Doctor",
        "refusal_reason": null,
        "verified_at": null
    },
    "token": "abc123def456..."
}
```

---

### Clinic Registration

#### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address |
| `password` | string | ✅ | Strong password |
| `password_confirm` | string | ✅ | Must match password |
| `provider_type` | string | ✅ | Must be `CLINIC` |
| `clinic_name` | string | ✅ | Official clinic name |
| `phone_number` | string | ✅ | Contact phone number |
| `license_number` | string | ✅ | Clinic license number |

#### Example Request

```json
{
    "email": "clinic@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "provider_type": "CLINIC",
    "clinic_name": "Clinique El Shifa",
    "phone_number": "+213555123456",
    "license_number": "CLN-2024-12345"
}
```

---

### Laboratory Registration

#### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address |
| `password` | string | ✅ | Strong password |
| `password_confirm` | string | ✅ | Must match password |
| `provider_type` | string | ✅ | Must be `LABORATORY` |
| `lab_name` | string | ✅ | Official laboratory name |
| `phone_number` | string | ✅ | Contact phone number |
| `license_number` | string | ✅ | Laboratory license number |

#### Example Request

```json
{
    "email": "lab@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "provider_type": "LABORATORY",
    "lab_name": "Laboratoire Central d'Analyses",
    "phone_number": "+213555123456",
    "license_number": "LAB-2024-12345"
}
```

---

### VTC Registration

VTC (Véhicule de Transport avec Chauffeur) for medical transport services.

#### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address |
| `password` | string | ✅ | Strong password |
| `password_confirm` | string | ✅ | Must match password |
| `provider_type` | string | ✅ | Must be `VTC` |
| `company_name` | string | ✅ | Transport company name |
| `phone_number` | string | ✅ | Contact phone number |
| `license_number` | string | ✅ | Transport license number |

#### Example Request

```json
{
    "email": "vtc@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "provider_type": "VTC",
    "company_name": "MediTransport Algérie",
    "phone_number": "+213555123456",
    "license_number": "VTC-2024-12345"
}
```

---

### Seller/Pharmacy Registration

#### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address |
| `password` | string | ✅ | Strong password |
| `password_confirm` | string | ✅ | Must match password |
| `provider_type` | string | ✅ | Must be `SELLER` |
| `business_name` | string | ✅ | Business/Pharmacy name |
| `phone_number` | string | ✅ | Contact phone number |
| `tax_id` | string | ✅ | Tax identification number |

#### Example Request

```json
{
    "email": "pharmacy@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "provider_type": "SELLER",
    "business_name": "Pharmacie Centrale",
    "phone_number": "+213555123456",
    "tax_id": "TAX-2024-12345"
}
```

---

## Login

Authenticate any provider type.

### Endpoint

```
POST /api/auth/login/
```

### Request Body

```json
{
    "email": "provider@example.com",
    "password": "SecurePass123!"
}
```

### Success Response (200 OK)

```json
{
    "user": {
        "id": 15,
        "email": "doctor@example.com",
        "role": "PROVIDER",
        "first_name": "Mohamed",
        "last_name": "Kaddour",
        "full_name": "Mohamed Kaddour",
        "phone_number": "+213555123456",
        "is_active": true,
        "email_verified": true,
        "profile_completed": true,
        "profile_completion_percentage": 90,
        "created_at": "2026-02-02T10:00:00Z"
    },
    "token": "abc123def456..."
}
```

### Error Responses

**403 Forbidden - Pending Verification**
```json
{
    "error": "Account verification in progress.",
    "provider_status": "PENDING",
    "message": "Your account is currently being reviewed by our medical board. You will receive an email once your professional documents are verified."
}
```

**403 Forbidden - Registration Refused**
```json
{
    "error": "Account registration refused.",
    "provider_status": "REFUSED",
    "refusal_reason": "Invalid license number. Please provide a valid medical license.",
    "message": "Your account registration was refused for the following reason: Invalid license number. Please provide a valid medical license. Please contact support or re-upload your documents."
}
```

---

## Account Status & Verification

> **⚠️ IMPORTANT: Providers Must Be APPROVED to Login**
>
> After registration, provider accounts are in `PENDING` status and **cannot login** until an admin approves them. Use the public status check endpoint to see your current approval status without logging in.

### Provider Status Values

| Status | Description | Can Login? |
|--------|-------------|------------|
| `PENDING` | Awaiting admin review | ❌ No |
| `APPROVED` | Verified and approved | ✅ Yes |
| `REFUSED` | Application rejected (see reason) | ❌ No |
| `SUSPENDED` | Temporarily disabled by admin | ❌ No |

---

### Check Account Status (Public - No Login Required)

Use this endpoint to check your account and provider status by email. This is useful for:
- Checking if your registration is still pending
- Seeing if your account has been approved
- Understanding why you can't login (refused/suspended)
- Viewing the refusal reason if your application was rejected

```
POST /api/auth/status/
```

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "email": "doctor@example.com"
}
```

### Response - Account Exists (200 OK)

```json
{
    "email": "doctor@example.com",
    "exists": true,
    "role": "PROVIDER",
    "account_status": "ACTIVE",
    "can_login": false,
    "provider": {
        "status": "PENDING",
        "refusal_reason": null,
        "approved_at": null,
        "verified_at": null,
        "provider_type": "DOCTOR",
        "provider_type_display": "Doctor"
    }
}
```

### Response - Account Approved (200 OK)

```json
{
    "email": "doctor@example.com",
    "exists": true,
    "role": "PROVIDER",
    "account_status": "ACTIVE",
    "can_login": true,
    "provider": {
        "status": "APPROVED",
        "refusal_reason": null,
        "approved_at": "2026-02-02T14:00:00Z",
        "verified_at": "2026-02-02T14:00:00Z",
        "provider_type": "DOCTOR",
        "provider_type_display": "Doctor"
    }
}
```

### Response - Account Refused (200 OK)

```json
{
    "email": "doctor@example.com",
    "exists": true,
    "role": "PROVIDER",
    "account_status": "ACTIVE",
    "can_login": false,
    "provider": {
        "status": "REFUSED",
        "refusal_reason": "License document was not readable. Please upload a clearer copy.",
        "approved_at": null,
        "verified_at": null,
        "provider_type": "DOCTOR",
        "provider_type_display": "Doctor"
    }
}
```

### Response - Account Suspended (200 OK)

```json
{
    "email": "doctor@example.com",
    "exists": true,
    "role": "PROVIDER",
    "account_status": "SUSPENDED",
    "can_login": false,
    "provider": {
        "status": "SUSPENDED",
        "refusal_reason": "Account suspended pending investigation.",
        "approved_at": "2026-01-15T10:00:00Z",
        "verified_at": "2026-01-15T10:00:00Z",
        "provider_type": "DOCTOR",
        "provider_type_display": "Doctor"
    }
}
```

### Response - Email Not Found (200 OK)

```json
{
    "email": "unknown@example.com",
    "exists": false
}
```

### Response Fields Explained

| Field | Description |
|-------|-------------|
| `exists` | Whether an account with this email exists |
| `role` | User role: `PROVIDER`, `PATIENT`, `ADMIN` |
| `account_status` | Account status: `ACTIVE`, `SUSPENDED`, `DEACTIVATED` |
| `can_login` | Whether the user can currently login |
| `provider.status` | Provider approval status: `PENDING`, `APPROVED`, `REFUSED`, `SUSPENDED` |
| `provider.refusal_reason` | Reason for refusal/suspension (if applicable) |
| `provider.approved_at` | When the provider was approved |
| `provider.provider_type` | Type: `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY`, `VTC`, `SELLER` |

### Understanding `can_login`

A provider can only login if ALL of these are true:
- Account exists
- `account_status` is `ACTIVE`
- `provider.status` is `APPROVED`
- Account is not deactivated

---

### Check Status After Login (Authenticated)

If you are already logged in, you can get your provider status from your profile:

```
GET /api/auth/me/
```

The response includes `provider_profile.status` with the same status information.

---

## Profile Management

### Get My Profile

Retrieve the complete profile based on provider type.

### Endpoint

```
GET /api/auth/me/
```

### Understanding the Response Structure

> **⚠️ IMPORTANT: Name Fields Location**
>
> For **providers**, the `first_name` and `last_name` at the **top level** of the response are from the User model and may be empty.
> The provider's actual name is stored in the **provider-specific profile** object (e.g., `provider_profile.doctor.first_name`).
>
> | Field Location | Description |
> |----------------|-------------|
> | `first_name`, `last_name` (top-level) | User model fields - often empty for providers |
> | `provider_profile.doctor.first_name` | Doctor's actual first name |
> | `provider_profile.doctor.last_name` | Doctor's actual last name |
> | `provider_profile.doctor.full_name` | Doctor's full name with "Dr." prefix |

### Doctor Profile Response

```json
{
    "id": 2,
    "email": "doctor@example.com",
    "role": "PROVIDER",
    "role_display": "Provider",
    "first_name": "",
    "last_name": "",
    "full_name": "doctor@example.com",
    "phone_number": "",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "is_staff": false,
    "email_verified": false,
    "email_verified_at": null,
    "profile_completed": false,
    "profile_completion_percentage": 67,
    "last_login": "2026-02-02T13:42:18.862154Z",
    "last_login_ip": "105.103.114.153",
    "created_at": "2026-01-27T23:06:02.824369Z",
    "updated_at": "2026-01-29T15:59:55.758438Z",
    "provider_profile": {
        "status": "APPROVED",
        "refusal_reason": "",
        "approved_at": null,
        "verified_at": null,
        "provider_type": "DOCTOR",
        "provider_type_display": "Doctor",
        "doctor": {
            "id": 1,
            "email": "doctor@example.com",
            "first_name": "Mohamed",
            "last_name": "Kaddour",
            "full_name": "Dr. Mohamed Kaddour",
            "gender": "MALE",
            "gender_display": "Male",
            "date_of_birth": "1985-03-15",
            "profile_image": "https://dzmedilink.duckdns.org/media/doctors/profiles/photo.jpg",
            "phone_number": "+213555123456",
            "license_number": "MED-2024-12345",
            "years_of_experience": 15,
            "biography": "Board-certified cardiologist with 15 years of experience...",
            "degree_document": "https://dzmedilink.duckdns.org/media/doctors/documents/degrees/degree.pdf",
            "is_verified": false,
            "is_available": true,
            "is_home_service_available": false,
            "consultation_price": "3000.00",
            "home_visit_price": "5000.00",
            "online_consultation_price": "2000.00",
            "currency": "DZD",
            "specialties": [
                {
                    "id": 1,
                    "title": "Cardiology",
                    "title_ar": "أمراض القلب",
                    "title_fr": "Cardiologie",
                    "slug": "cardiology",
                    "is_primary": true,
                    "years_of_experience": 15
                }
            ],
            "services": [
                {
                    "id": 1,
                    "title": "General Consultation",
                    "slug": "general-consultation",
                    "description": "Standard medical consultation",
                    "price": "3000.00",
                    "custom_price": null,
                    "final_price": "3000.00",
                    "duration_minutes": 30,
                    "is_home_service": false,
                    "is_available": true
                }
            ],
            "provider_status": {
                "status": "APPROVED",
                "refusal_reason": "",
                "approved_at": null,
                "verified_at": null,
                "provider_type": "DOCTOR",
                "provider_type_display": "Doctor"
            },
            "created_at": "2026-01-27T23:06:03.482792Z",
            "updated_at": "2026-01-29T15:59:55.763761Z"
        }
    },
    "patient_profile": null,
    "addresses": [
        {
            "id": 1,
            "content_type": 15,
            "content_type_name": "user",
            "object_id": 2,
            "street": "123 Rue Didouche Mourad",
            "city": "Algiers",
            "state": "Algiers",
            "zip_code": "16000",
            "country": "Algeria",
            "latitude": null,
            "longitude": null,
            "is_primary": true,
            "address_type": "HOME",
            "notes": "",
            "created_at": "2026-01-28T17:19:59.330245Z",
            "updated_at": "2026-02-01T17:27:15.014170Z"
        }
    ],
    "provider_type": "DOCTOR",
    "provider_type_display": "Doctor",
    "subtype": "DOCTOR",
    "subtype_display": "Doctor"
}
```

### Doctor Profile Fields Explained

| Field Path | Type | Description |
|------------|------|-------------|
| `id` | integer | User ID |
| `email` | string | Login email |
| `role` | string | Always `PROVIDER` for providers |
| `first_name`, `last_name` | string | **Top-level User fields - typically empty for providers** |
| `full_name` | string | Falls back to email if name is empty |
| `account_status` | string | `ACTIVE`, `SUSPENDED`, `DEACTIVATED` |
| `profile_completion_percentage` | integer | 0-100 completion score |
| **provider_profile.doctor** | object | **Doctor's actual profile data** |
| `.first_name`, `.last_name` | string | **Doctor's actual name** |
| `.full_name` | string | Name with "Dr." prefix |
| `.gender` | string | `MALE`, `FEMALE`, `OTHER` |
| `.phone_number` | string | Doctor's contact number |
| `.license_number` | string | Medical license |
| `.years_of_experience` | integer | Years practicing |
| `.biography` | string | Professional bio |
| `.is_available` | boolean | Accepting appointments |
| `.is_home_service_available` | boolean | Offers home visits |
| `.consultation_price` | decimal | Standard clinic consultation price |
| `.home_visit_price` | decimal | Home visit price |
| `.online_consultation_price` | decimal | Online/video consultation price |
| `.currency` | string | Currency code (default: `DZD`) |
| `.specialties` | array | Doctor's specialties |
| `.services` | array | Services offered with pricing |
| `.provider_status` | object | Provider approval status |

### Clinic Profile Response

```json
{
    "id": 20,
    "email": "clinic@example.com",
    "role": "PROVIDER",
    "role_display": "Provider",
    "first_name": "",
    "last_name": "",
    "full_name": "clinic@example.com",
    "phone_number": "",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "is_staff": false,
    "email_verified": true,
    "email_verified_at": "2026-02-01T12:00:00Z",
    "profile_completed": true,
    "profile_completion_percentage": 85,
    "last_login": "2026-02-02T09:00:00Z",
    "last_login_ip": "105.103.114.153",
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-02T09:30:00Z",
    "provider_profile": {
        "status": "APPROVED",
        "refusal_reason": "",
        "approved_at": "2026-02-01T14:00:00Z",
        "verified_at": "2026-02-01T14:00:00Z",
        "provider_type": "CLINIC",
        "provider_type_display": "Clinic",
        "clinic": {
            "id": 3,
            "clinic_name": "Clinique El Shifa",
            "phone_number": "+213555123456",
            "license_number": "CLN-2024-12345",
            "description": "Full-service medical clinic offering...",
            "logo": "https://dzmedilink.duckdns.org/media/clinics/logo.jpg",
            "is_available": true,
            "opening_hours": "08:00-18:00",
            "services": ["General Medicine", "Pediatrics", "Cardiology"],
            "created_at": "2026-02-01T10:00:00Z"
        }
    },
    "patient_profile": null,
    "addresses": [],
    "provider_type": "CLINIC",
    "provider_type_display": "Clinic"
}
```

### Laboratory Profile Response

```json
{
    "id": 25,
    "email": "lab@example.com",
    "role": "PROVIDER",
    "provider_profile": {
        "id": 18,
        "status": "APPROVED",
        "provider_type": "LABORATORY",
        "laboratory": {
            "id": 2,
            "lab_name": "Laboratoire Central d'Analyses",
            "phone_number": "+213555123456",
            "license_number": "LAB-2024-12345",
            "description": "Certified medical laboratory...",
            "is_available": true,
            "test_types": ["Blood Tests", "Urine Analysis", "Radiology"],
            "created_at": "2026-02-01T10:00:00Z"
        }
    },
    "provider_type": "LABORATORY",
    "provider_type_display": "Laboratory"
}
```

---

### Update My Profile

Update profile based on provider type.

### Endpoint

```
PATCH /api/auth/me/
```

### Updatable Fields by Provider Type

#### Doctor Updatable Fields

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | Doctor's first name |
| `last_name` | string | Doctor's last name |
| `phone_number` | string | Contact phone |
| `gender` | string | `MALE`, `FEMALE`, `OTHER` |
| `biography` | string | Professional bio |
| `years_of_experience` | integer | Years of practice |
| `is_available` | boolean | Accepting appointments |
| `is_home_service_available` | boolean | Home visits available |
| `profile_image` | file | Profile photo |

#### Clinic Updatable Fields

| Field | Type | Description |
|-------|------|-------------|
| `phone_number` | string | Contact phone |
| `is_available` | boolean | Currently open |
| `profile_image` | file | Clinic logo |

#### Laboratory Updatable Fields

| Field | Type | Description |
|-------|------|-------------|
| `phone_number` | string | Contact phone |
| `is_available` | boolean | Accepting samples |

### Example: Update Doctor Profile

```json
{
    "first_name": "Mohamed",
    "last_name": "Kaddour",
    "biography": "Board-certified cardiologist with 15 years of experience in interventional cardiology...",
    "years_of_experience": 16,
    "is_available": true,
    "is_home_service_available": false
}
```

### Example: Update Availability

```json
{
    "is_available": false
}
```

### Read-Only Fields

These fields cannot be changed via the API:

| Field | Reason |
|-------|--------|
| `email` | Use dedicated email change flow |
| `license_number` | Verified document |
| `degree_document` | Contact support |
| `tax_id` | Contact support |

**Error Response for Read-Only Fields:**
```json
{
    "license_number": ["This field cannot be changed from the app. Please contact support."]
}
```

### Pricing & Scheduling Notes

- Retrieve consultation fees from your authenticated profile via `GET /api/auth/me/`. The doctor block in the response exposes `consultation_price`, `home_visit_price`, `online_consultation_price`, `currency`, and the detailed `services` list (each service carries `price` and `final_price`).
- No time selection is required on the dashboard when initiating a reschedule: the doctor selects the new time while performing the reschedule action. Client forms should avoid making time mandatory for rescheduling flows.

---

## Public Provider Profile Fields

When a patient or unauthenticated user fetches a provider via `GET /api/provider/public/{id}/`, the response now includes:

### Contact Information

| Field | Location | Description |
|-------|----------|-------------|
| `phone_number` | top-level | Contact phone number |
| `email` | top-level | Contact email (clinics may expose their own clinic email) |

#### Doctor sub-object additional fields

| Field | Description |
|-------|-------------|
| `phone_number` | Doctor's direct phone number |
| `email` | Doctor's account email |
| `consultation_price` | Standard clinic consultation price (DZD) |
| `home_visit_price` | Home visit price (DZD) |
| `online_consultation_price` | Online/video consultation price (DZD) |
| `currency` | Currency code (default: `DZD`) |
| `biography` | Professional biography |
| `specialties` | List of specialties with `title`, `title_ar`, `title_fr`, `slug`, `is_primary` |

#### Clinic sub-object additional fields

| Field | Description |
|-------|-------------|
| `phone_number` | Clinic contact phone |
| `email` | Clinic-specific email address |

#### Nurse sub-object additional fields

| Field | Description |
|-------|-------------|
| `phone_number` | Nurse contact phone |
| `email` | Nurse account email |

### Social Media Links

All public provider endpoints (`/api/provider/public/` list and `/api/provider/public/{id}/` detail) now return a `social_links` array:

```json
"social_links": [
    {
        "id": 1,
        "platform": "FACEBOOK",
        "url": "https://facebook.com/dr.kaddour",
        "display_order": 1,
        "is_visible": true
    },
    {
        "id": 2,
        "platform": "INSTAGRAM",
        "url": "https://instagram.com/dr.kaddour",
        "display_order": 2,
        "is_visible": true
    }
]
```

Only links with `is_visible: true` are returned.

### Addresses (with Coordinates)

All addresses returned in both the list (`primary_address`) and detail (`addresses` array) include full coordinate data for map display:

```json
"addresses": [
    {
        "id": 5,
        "street": "12 Rue Hassiba Ben Bouali",
        "city": "Algiers",
        "state": "Algiers",
        "zip_code": "16000",
        "country": "Algeria",
        "latitude": 36.7538,
        "longitude": 3.0588,
        "is_primary": true,
        "address_type": "CLINIC",
        "notes": "2nd floor, Cabinet 14"
    }
]
```

Use `latitude` and `longitude` to place a map pin on the provider profile page. The `primary_address` field in the list response gives the same structure for the most important address.

### Full Public Detail Response Example (Doctor)

```json
{
    "id": 10,
    "provider_type": "DOCTOR",
    "provider_type_display": "Doctor",
    "name": "Dr. Mohamed Kaddour",
    "phone_number": "+213555123456",
    "email": "doctor@example.com",
    "doctor": {
        "id": 1,
        "first_name": "Mohamed",
        "last_name": "Kaddour",
        "full_name": "Dr. Mohamed Kaddour",
        "email": "doctor@example.com",
        "phone_number": "+213555123456",
        "gender": "MALE",
        "profile_image": "https://dzmedilink.duckdns.org/media/doctors/profiles/photo.jpg",
        "years_of_experience": 15,
        "biography": "Board-certified cardiologist with 15 years of experience...",
        "consultation_price": "3000.00",
        "home_visit_price": "5000.00",
        "online_consultation_price": "2000.00",
        "currency": "DZD",
        "is_available": true,
        "is_home_service_available": false,
        "specialties": [
            {
                "id": 1,
                "title": "Cardiology",
                "title_ar": "أمراض القلب",
                "title_fr": "Cardiologie",
                "slug": "cardiology",
                "is_primary": true
            }
        ],
        "services": [
            {
                "id": 1,
                "title": "General Consultation",
                "price": "3000.00",
                "duration_minutes": 30,
                "is_home_service": false
            }
        ]
    },
    "addresses": [
        {
            "id": 5,
            "street": "12 Rue Hassiba Ben Bouali",
            "city": "Algiers",
            "state": "Algiers",
            "zip_code": "16000",
            "country": "Algeria",
            "latitude": 36.7538,
            "longitude": 3.0588,
            "is_primary": true,
            "address_type": "CLINIC"
        }
    ],
    "rating": {
        "average": 4.7,
        "count": 38,
        "distribution": { "1": 0, "2": 1, "3": 2, "4": 10, "5": 25 }
    },
    "social_links": [
        { "platform": "FACEBOOK", "url": "https://facebook.com/dr.kaddour", "is_visible": true },
        { "platform": "INSTAGRAM", "url": "https://instagram.com/dr.kaddour", "is_visible": true }
    ]
}
```

---

## Managing Addresses

### List Addresses

```
GET /api/addresses/
```

### Create Address

```
POST /api/addresses/
```

**Request Body:**
```json
{
    "street": "123 Rue Didouche Mourad",
    "city": "Algiers",
    "state": "Algiers",
    "zip_code": "16000",
    "country": "Algeria",
    "latitude": 36.7538,
    "longitude": 3.0588,
    "is_primary": true,
    "address_type": "CLINIC",
    "notes": "Main practice location"
}
```

**Address Types for Providers:**
- `CLINIC` - Medical clinic location
- `HOSPITAL` - Hospital location
- `WORK` - General work location
- `OTHER` - Other location

### Update Address

```
PUT /api/addresses/{id}/
PATCH /api/addresses/{id}/
```

### Delete Address

```
DELETE /api/addresses/{id}/
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Validation errors |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Pending/Refused/Suspended |
| 404 | Not Found |
| 500 | Server Error |

### Validation Error Format

```json
{
    "field_name": ["Error message 1", "Error message 2"],
    "another_field": ["Error message"]
}
```

### Provider Status Errors

| Error | Status | Action Required |
|-------|--------|-----------------|
| Pending verification | `PENDING` | Wait for admin approval |
| Registration refused | `REFUSED` | Contact support or re-apply |
| Account suspended | `SUSPENDED` | Contact support |

---

## Web Integration Examples

### JavaScript/TypeScript (Axios)

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = 'https://dzmedilink.duckdns.org/';

class AuthService {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to requests
    this.api.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Token ${this.token}`;
      }
      return config;
    });

    // Handle provider status errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 403) {
          const data = error.response.data;
          if (data.provider_status) {
            throw new ProviderStatusError(
              data.provider_status,
              data.message,
              data.refusal_reason
            );
          }
        }
        throw error;
      }
    );
  }

  // Load token from storage
  loadToken(): void {
    this.token = localStorage.getItem('authToken');
  }

  // Save token to storage
  private saveToken(token: string): void {
    this.token = token;
    localStorage.setItem('authToken', token);
  }

  // Provider Registration (JSON)
  async registerProvider(data: ProviderRegistrationData): Promise<RegistrationResponse> {
    const response = await this.api.post('/auth/provider/register/', data);
    this.saveToken(response.data.token);
    return response.data;
  }

  // Provider Registration with Files (FormData)
  async registerProviderWithFiles(data: FormData): Promise<RegistrationResponse> {
    const response = await this.api.post('/auth/provider/register/', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    this.saveToken(response.data.token);
    return response.data;
  }

  // Login
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await this.api.post('/auth/login/', { email, password });
    this.saveToken(response.data.token);
    return response.data;
  }

  // Logout
  async logout(): Promise<void> {
    await this.api.post('/auth/logout/');
    this.token = null;
    localStorage.removeItem('authToken');
  }

  // Get Profile
  async getProfile(): Promise<UserProfile> {
    const response = await this.api.get('/auth/me/');
    return response.data;
  }

  // Update Profile
  async updateProfile(data: ProfileUpdateData): Promise<UserProfile> {
    const response = await this.api.patch('/auth/me/', data);
    return response.data;
  }

  // Update Profile with Image
  async updateProfileImage(file: File): Promise<UserProfile> {
    const formData = new FormData();
    formData.append('profile_image', file);
    const response = await this.api.patch('/auth/me/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  // Get Provider Status
  async getProviderStatus(): Promise<ProviderStatus> {
    const response = await this.api.get('/provider/status/');
    return response.data;
  }
}

// Custom Error Class
class ProviderStatusError extends Error {
  constructor(
    public status: string,
    public message: string,
    public refusalReason?: string
  ) {
    super(message);
    this.name = 'ProviderStatusError';
  }
}

// Types
interface ProviderRegistrationData {
  email: string;
  password: string;
  password_confirm: string;
  provider_type: 'DOCTOR' | 'NURSE' | 'CLINIC' | 'LABORATORY' | 'VTC' | 'SELLER';
  first_name?: string;
  last_name?: string;
  phone_number: string;
  license_number?: string;
  clinic_name?: string;
  lab_name?: string;
  company_name?: string;
  business_name?: string;
  tax_id?: string;
}

interface RegistrationResponse {
  user: User;
  provider: Provider;
  token: string;
}

interface LoginResponse {
  user: User;
  token: string;
}

interface UserProfile {
  id: number;
  email: string;
  role: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number: string;
  account_status: string;
  profile_completed: boolean;
  profile_completion_percentage: number;
  provider_profile: ProviderProfile | null;
  addresses: Address[];
  provider_type: string | null;
}

interface ProviderProfile {
  id: number;
  status: string;
  provider_type: string;
  doctor?: DoctorProfile;
  nurse?: NurseProfile;
  clinic?: ClinicProfile;
  laboratory?: LaboratoryProfile;
}

interface ProfileUpdateData {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  gender?: string;
  biography?: string;
  years_of_experience?: number;
  is_available?: boolean;
  is_home_service_available?: boolean;
}

// Export singleton instance
export const authService = new AuthService();
```

### React Hook Example

```typescript
import { useState, useEffect, useCallback } from 'react';
import { authService } from './authService';

interface UseAuthReturn {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  providerStatus: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: ProfileUpdateData) => Promise<void>;
  refreshProfile: () => Promise<void>;
  error: Error | null;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Load user on mount
  useEffect(() => {
    authService.loadToken();
    refreshProfile();
  }, []);

  const refreshProfile = useCallback(async () => {
    try {
      setIsLoading(true);
      const profile = await authService.getProfile();
      setUser(profile);
      setError(null);
    } catch (err) {
      setUser(null);
      if (err instanceof ProviderStatusError) {
        setError(err);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    try {
      setIsLoading(true);
      await authService.login(email, password);
      await refreshProfile();
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [refreshProfile]);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (data: ProfileUpdateData) => {
    const updated = await authService.updateProfile(data);
    setUser(updated);
  }, []);

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    providerStatus: user?.provider_profile?.status || null,
    login,
    logout,
    updateProfile,
    refreshProfile,
    error,
  };
}
```

### Vue.js Composable Example

```typescript
import { ref, computed, onMounted } from 'vue';
import { authService } from './authService';

export function useAuth() {
  const user = ref<UserProfile | null>(null);
  const isLoading = ref(true);
  const error = ref<Error | null>(null);

  const isAuthenticated = computed(() => !!user.value);
  const providerStatus = computed(() => user.value?.provider_profile?.status);
  const providerType = computed(() => user.value?.provider_type);

  onMounted(async () => {
    authService.loadToken();
    await refreshProfile();
  });

  async function refreshProfile() {
    try {
      isLoading.value = true;
      user.value = await authService.getProfile();
      error.value = null;
    } catch (err) {
      user.value = null;
      error.value = err as Error;
    } finally {
      isLoading.value = false;
    }
  }

  async function login(email: string, password: string) {
    isLoading.value = true;
    try {
      await authService.login(email, password);
      await refreshProfile();
    } catch (err) {
      error.value = err as Error;
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  async function logout() {
    await authService.logout();
    user.value = null;
  }

  async function updateProfile(data: ProfileUpdateData) {
    user.value = await authService.updateProfile(data);
  }

  return {
    user,
    isLoading,
    isAuthenticated,
    providerStatus,
    providerType,
    error,
    login,
    logout,
    updateProfile,
    refreshProfile,
  };
}
```

---

## Related Endpoints

For complete provider functionality, also see:

| Provider Type | Key Endpoints |
|---------------|---------------|
| **All Providers** | `/api/provider/profile/`, `/api/appointments/` |
| **Doctors** | `/api/services/`, `/api/prescriptions/` |
| **Nurses** | `/api/nurse-requests/` |
| **Clinics** | `/api/provider/clinic/` |
| **Laboratories** | `/api/provider/laboratory/` |

---

## Support

For API issues or questions, contact:
- Email: api-support@medilink.com
- Documentation: https://docs.medilink.com
