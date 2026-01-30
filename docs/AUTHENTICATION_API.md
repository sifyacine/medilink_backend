# MediLink Authentication API Documentation

## Overview

This documentation provides a comprehensive guide for integrating the MediLink authentication system into your mobile application. The API supports two primary user types:

1. **Patients** - Regular users who access healthcare services
2. **Nurse Providers** - Healthcare professionals who provide nursing services

Both user types follow a similar authentication flow but with different registration requirements.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication Flow](#authentication-flow)
3. [Patient Authentication](#patient-authentication)
   - [Patient Registration](#patient-registration)
   - [Patient Login](#patient-login)
4. [Nurse Provider Authentication](#nurse-provider-authentication)
   - [Nurse Registration](#nurse-registration)
   - [Required Documents](#required-documents-for-nurse)
   - [Nurse Login](#nurse-login)
5. [Auth/Me Endpoint](#authme-endpoint)
   - [GET - Retrieve Profile](#get-profile)
   - [PATCH - Update Profile](#patch-update-profile)
6. [Logout](#logout)
7. [Account Status Check](#account-status-check)
8. [Password Reset](#password-reset)
9. [Error Handling](#error-handling)
10. [Mobile Integration Examples](#mobile-integration-examples)

---

## Base URL

All API endpoints use the following base URL:

```
https://your-api-domain.com/api/auth/
```

---

## Authentication Flow

### Token-Based Authentication

MediLink uses **Token Authentication**. After successful login or registration, the API returns a token that must be included in all subsequent requests.

```
Authorization: Token <your_token_here>
```

### General Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   Register   │───▶│    Login     │───▶│  Access API      │  │
│  │   /register/ │    │   /login/    │    │  with Token      │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                     │             │
│         ▼                   ▼                     ▼             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Receive     │    │  Receive     │    │  Use /api/auth/  │  │
│  │  Token       │    │  Token       │    │  me/ to manage   │  │
│  └──────────────┘    └──────────────┘    │  profile         │  │
│                                          └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Patient Authentication

### Patient Registration

Patients can register with minimal information initially and complete their profile later.

**Endpoint:** `POST /api/auth/patient/register/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "email": "patient@example.com",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ Yes | Patient's email address (must be unique) |
| `password` | string | ✅ Yes | Password (minimum 8 characters, must include letters and numbers) |
| `password_confirm` | string | ✅ Yes | Password confirmation (must match `password`) |

#### Success Response (201 Created)

```json
{
    "user": {
        "id": 1,
        "email": "patient@example.com",
        "role": "PATIENT",
        "is_active": true,
        "created_at": "2026-01-30T10:00:00Z"
    },
    "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

#### Error Responses

**400 Bad Request - Email Already Exists:**
```json
{
    "email": ["A user with this email already exists."]
}
```

**400 Bad Request - Password Mismatch:**
```json
{
    "password_confirm": ["Passwords do not match."]
}
```

**400 Bad Request - Weak Password:**
```json
{
    "password": [
        "This password is too short. It must contain at least 8 characters.",
        "This password is too common."
    ]
}
```

---

### Patient Login

**Endpoint:** `POST /api/auth/login/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "email": "patient@example.com",
    "password": "SecurePassword123!"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ Yes | Patient's email address |
| `password` | string | ✅ Yes | Patient's password |

#### Success Response (200 OK)

```json
{
    "user": {
        "id": 1,
        "email": "patient@example.com",
        "role": "PATIENT",
        "is_active": true,
        "created_at": "2026-01-30T10:00:00Z"
    },
    "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

#### Error Responses

**401 Unauthorized - Invalid Credentials:**
```json
{
    "error": "Invalid email or password."
}
```

**403 Forbidden - Inactive Account:**
```json
{
    "error": "Account is inactive."
}
```

**423 Locked - Too Many Failed Attempts:**
```json
{
    "error": "Account temporarily locked due to multiple failed login attempts.",
    "message": "Please try again later or contact support."
}
```

---

## Nurse Provider Authentication

### Required Documents for Nurse

Nurses must provide verification documents during registration:

| Document | Type | Required | Description |
|----------|------|----------|-------------|
| `degree_document` | File (PDF/Image) | ✅ Yes | Nursing degree certificate |
| `entrepreneur_card_front` | Image | ✅ Yes | Front of entrepreneur card |
| `entrepreneur_card_back` | Image | ✅ Yes | Back of entrepreneur card |

### Nurse Registration

**Endpoint:** `POST /api/auth/provider/register/`

**Headers:**
```
Content-Type: multipart/form-data
```

> ⚠️ **Important:** Since files are included, use `multipart/form-data` instead of `application/json`

**Request Body (Form Data):**

```
email: nurse@example.com
password: SecurePassword123!
password_confirm: SecurePassword123!
provider_type: NURSE
first_name: Marie
last_name: Dupont
phone_number: +33612345678
license_number: INF-2024-12345
degree_document: [FILE - nursing_degree.pdf]
entrepreneur_card_front: [FILE - card_front.jpg]
entrepreneur_card_back: [FILE - card_back.jpg]
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ Yes | Nurse's email address (must be unique) |
| `password` | string | ✅ Yes | Password (minimum 8 characters) |
| `password_confirm` | string | ✅ Yes | Password confirmation |
| `provider_type` | string | ✅ Yes | Must be `"NURSE"` |
| `first_name` | string | ✅ Yes | Nurse's first name |
| `last_name` | string | ✅ Yes | Nurse's last name |
| `phone_number` | string | ✅ Yes | Contact phone number |
| `license_number` | string | ✅ Yes | Professional nursing license number |
| `degree_document` | file | ✅ Yes | Nursing degree document (PDF or image) |
| `entrepreneur_card_front` | image | ✅ Yes | Front of entrepreneur card (JPEG/PNG) |
| `entrepreneur_card_back` | image | ✅ Yes | Back of entrepreneur card (JPEG/PNG) |

#### Success Response (201 Created)

```json
{
    "user": {
        "id": 2,
        "email": "nurse@example.com",
        "role": "PROVIDER",
        "is_active": true,
        "created_at": "2026-01-30T10:00:00Z"
    },
    "provider": {
        "status": "PENDING",
        "refusal_reason": null,
        "approved_at": null,
        "verified_at": null,
        "provider_type": "NURSE",
        "provider_type_display": "Nurse"
    },
    "token": "x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0"
}
```

> 📝 **Note:** After registration, the nurse account has `status: "PENDING"`. The account must be approved by an administrator before the nurse can log in and access the platform.

#### Error Responses

**400 Bad Request - Missing Required Documents:**
```json
{
    "degree_document": ["This field is required for nurse signup."],
    "entrepreneur_card_front": ["This field is required for nurse signup."],
    "entrepreneur_card_back": ["This field is required for nurse signup."]
}
```

**400 Bad Request - Missing Personal Information:**
```json
{
    "first_name": ["This field is required for nurse signup."],
    "last_name": ["This field is required for nurse signup."],
    "phone_number": ["This field is required for nurse signup."],
    "license_number": ["This field is required for nurse signup."]
}
```

**400 Bad Request - Email Already Exists with Different Role:**
```json
{
    "email": ["User with this email already exists with role PATIENT. Cannot create provider account."]
}
```

---

### Nurse Login

After admin approval, nurses can log in using the same login endpoint as patients.

**Endpoint:** `POST /api/auth/login/`

**Request Body:**
```json
{
    "email": "nurse@example.com",
    "password": "SecurePassword123!"
}
```

#### Success Response (200 OK) - Approved Nurse

```json
{
    "user": {
        "id": 2,
        "email": "nurse@example.com",
        "role": "PROVIDER",
        "provider_type": "NURSE",
        "provider_type_display": "Nurse",
        "is_active": true,
        "created_at": "2026-01-30T10:00:00Z"
    },
    "token": "x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0"
}
```

#### Provider Status Errors

**403 Forbidden - Pending Verification:**
```json
{
    "error": "Account verification in progress.",
    "provider_status": "PENDING",
    "message": "Your account is currently being reviewed by our medical board. You will receive an email once your professional documents are verified."
}
```

**403 Forbidden - Registration Refused:**
```json
{
    "error": "Account registration refused.",
    "provider_status": "REFUSED",
    "refusal_reason": "Invalid license number. Please re-submit with correct documentation.",
    "message": "Your account registration was refused for the following reason: Invalid license number. Please re-submit with correct documentation. Please contact support or re-upload your documents."
}
```

**403 Forbidden - Account Suspended:**
```json
{
    "error": "Account suspended.",
    "provider_status": "SUSPENDED",
    "message": "Your account has been temporarily suspended for administrative reasons. Please contact support."
}
```

---

## Auth/Me Endpoint

The `/api/auth/me/` endpoint allows authenticated users to retrieve and update their profile information.

### GET Profile

Retrieves the complete profile information for the authenticated user.

**Endpoint:** `GET /api/auth/me/`

**Headers:**
```
Authorization: Token <your_token_here>
```

---

#### Patient GET Response

**Case 1: Patient WITHOUT linked PatientRecord (new account, no medical history)**

```json
{
    "id": 1,
    "email": "patient@example.com",
    "role": "PATIENT",
    "role_display": "Patient",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "is_staff": false,
    "email_verified": false,
    "email_verified_at": null,
    "profile_completed": false,
    "profile_completion_percentage": 0,
    "last_login": "2026-01-30T10:00:00Z",
    "last_login_ip": "192.168.1.1",
    "created_at": "2026-01-30T09:00:00Z",
    "updated_at": "2026-01-30T10:00:00Z",
    "provider_profile": null,
    "patient_profile": {
        "is_patient": true,
        "has_patient_record": false,
        "patient_record": null
    },
    "addresses": [],
    "provider_type": null,
    "provider_type_display": null,
    "subtype": null,
    "subtype_display": null
}
```

**Case 2: Patient WITH linked PatientRecord (account linked to medical history created by a provider)**

```json
{
    "id": 3,
    "email": "yacinesif@gmail.com",
    "role": "PATIENT",
    "role_display": "Patient",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "is_staff": false,
    "email_verified": false,
    "email_verified_at": null,
    "profile_completed": false,
    "profile_completion_percentage": 0,
    "last_login": "2026-01-30T15:58:16.244249Z",
    "last_login_ip": "105.111.20.54",
    "created_at": "2026-01-30T15:39:41.505581Z",
    "updated_at": "2026-01-30T15:39:41.965744Z",
    "provider_profile": null,
    "patient_profile": {
        "is_patient": true,
        "has_patient_record": true,
        "patient_record": {
            "id": 5,
            "patient_unique_id": "MED-A1B2C3D4",
            "first_name": "Yacine",
            "last_name": "Sif",
            "full_name": "Yacine Sif",
            "date_of_birth": "1990-05-15",
            "age": 35,
            "gender": "MALE",
            "phone_number": "+213555123456",
            "email": "yacinesif@gmail.com",
            "emergency_contact_name": "Ahmed Sif",
            "emergency_contact_phone": "+213555654321",
            "blood_type": "A+",
            "known_allergies": "Penicillin",
            "chronic_conditions": "None",
            "current_medications": "None",
            "national_id": "123456789",
            "address": "123 Main Street",
            "city": "Algiers",
            "state": "Algiers",
            "country": "Algeria",
            "notes": "Regular checkup patient",
            "is_active": true,
            "is_linked": true,
            "linking_token_masked": "***LINKED***",
            "created_by_provider_name": "Dr. Ahmed Benali",
            "created_at": "2026-01-25T10:00:00Z",
            "updated_at": "2026-01-30T15:39:41Z"
        }
    },
    "addresses": [],
    "provider_type": null,
    "provider_type_display": null,
    "subtype": null,
    "subtype_display": null
}
```

#### Understanding Patient Profile States

| Field | Value | Meaning |
|-------|-------|---------|
| `patient_profile.is_patient` | `true` | User is a patient |
| `patient_profile.has_patient_record` | `false` | No medical history exists (new patient) |
| `patient_profile.has_patient_record` | `true` | Medical history exists (linked to provider-created record) |
| `patient_profile.patient_record` | `null` | No linked medical record |
| `patient_profile.patient_record` | `{...}` | Full medical record data |

#### Mobile App Logic for Patient Profile

```dart
// Example Flutter/Dart logic
void handlePatientProfile(Map<String, dynamic> response) {
  final patientProfile = response['patient_profile'];
  
  if (patientProfile == null) {
    // User is not a patient (might be a provider)
    return;
  }
  
  final hasPatientRecord = patientProfile['has_patient_record'] ?? false;
  
  if (hasPatientRecord) {
    // Patient has linked medical record from a provider
    final patientRecord = patientProfile['patient_record'];
    
    // Display patient info from the record
    String firstName = patientRecord['first_name'];
    String lastName = patientRecord['last_name'];
    String fullName = patientRecord['full_name'];
    String bloodType = patientRecord['blood_type'];
    String allergies = patientRecord['known_allergies'];
    String patientId = patientRecord['patient_unique_id']; // e.g., "MED-A1B2C3D4"
    
    // Show complete profile screen with medical info
  } else {
    // New patient without medical history
    // Show profile completion wizard or empty state
    // Prompt user to add personal/medical information
  }
}
```

#### Response Fields for Patient

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique user ID |
| `email` | string | User's email address |
| `role` | string | User role: `"PATIENT"` |
| `role_display` | string | Human-readable role: `"Patient"` |
| `account_status` | string | Account status: `ACTIVE`, `SUSPENDED`, `DEACTIVATED` |
| `account_status_display` | string | Human-readable account status |
| `is_active` | boolean | Whether the account can log in |
| `email_verified` | boolean | Whether email has been verified |
| `email_verified_at` | datetime | When email was verified |
| `profile_completed` | boolean | Whether profile is complete |
| `profile_completion_percentage` | integer | Profile completion (0-100) |
| `last_login` | datetime | Last login timestamp |
| `last_login_ip` | string | IP address of last login |
| `created_at` | datetime | Account creation timestamp |
| `updated_at` | datetime | Last profile update timestamp |
| `patient_profile` | object | Patient-specific profile data |
| `patient_profile.is_patient` | boolean | Always `true` for patients |
| `patient_profile.has_patient_record` | boolean | Whether linked to provider-created medical record |
| `patient_profile.patient_record` | object/null | Full medical record if linked |
| `addresses` | array | List of addresses associated with user |

#### Patient Record Fields (when `has_patient_record` is `true`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | PatientRecord ID |
| `patient_unique_id` | string | Unique patient identifier (e.g., "MED-A1B2C3D4") |
| `first_name` | string | Patient's first name |
| `last_name` | string | Patient's last name |
| `full_name` | string | Combined first and last name |
| `date_of_birth` | date | Date of birth (YYYY-MM-DD) |
| `age` | integer | Calculated age in years |
| `gender` | string | `MALE`, `FEMALE`, `OTHER`, `PREFER_NOT_TO_SAY` |
| `phone_number` | string | Contact phone number |
| `email` | string | Email address |
| `emergency_contact_name` | string | Emergency contact name |
| `emergency_contact_phone` | string | Emergency contact phone |
| `blood_type` | string | `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-`, `UNKNOWN` |
| `known_allergies` | string | Known allergies (free text) |
| `chronic_conditions` | string | Chronic conditions (free text) |
| `current_medications` | string | Current medications (free text) |
| `national_id` | string | National ID number |
| `address` | string | Street address |
| `city` | string | City |
| `state` | string | State/Province |
| `country` | string | Country |
| `notes` | string | Additional notes |
| `is_active` | boolean | Whether record is active |
| `is_linked` | boolean | Whether linked to a user account |
| `linking_token_masked` | string | Masked linking token (for security) |
| `created_by_provider_name` | string | Name of provider who created the record |
| `created_at` | datetime | Record creation timestamp |
| `updated_at` | datetime | Last update timestamp |

---

#### Nurse Provider GET Response

```json
{
    "id": 2,
    "email": "nurse@example.com",
    "role": "PROVIDER",
    "role_display": "Provider",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "is_staff": false,
    "email_verified": false,
    "email_verified_at": null,
    "profile_completed": false,
    "profile_completion_percentage": 45,
    "last_login": "2026-01-30T12:00:00Z",
    "last_login_ip": "192.168.1.50",
    "created_at": "2026-01-30T09:00:00Z",
    "updated_at": "2026-01-30T12:00:00Z",
    "provider_profile": {
        "status": "APPROVED",
        "refusal_reason": null,
        "approved_at": "2026-01-30T11:00:00Z",
        "verified_at": "2026-01-30T11:00:00Z",
        "provider_type": "NURSE",
        "provider_type_display": "Nurse",
        "nurse": {
            "id": 1,
            "email": "nurse@example.com",
            "first_name": "Marie",
            "last_name": "Dupont",
            "full_name": "Marie Dupont",
            "gender": "FEMALE",
            "gender_display": "Female",
            "date_of_birth": "1985-05-15",
            "profile_image": "https://api.medilink.com/media/nurses/profiles/marie_dupont.jpg",
            "phone_number": "+33612345678",
            "license_number": "INF-2024-12345",
            "certification": "Certified Nurse",
            "years_of_experience": 10,
            "biography": "Experienced nurse specializing in home care and elderly patient support.",
            "degree_document": "https://api.medilink.com/media/nurses/documents/degrees/nursing_degree.pdf",
            "entrepreneur_card_front": "https://api.medilink.com/media/nurses/documents/entrepreneur_cards/front.jpg",
            "entrepreneur_card_back": "https://api.medilink.com/media/nurses/documents/entrepreneur_cards/back.jpg",
            "entrepreneur_card_pdf": null,
            "is_verified": true,
            "is_available": true,
            "is_home_service_available": true,
            "services": [
                {
                    "id": 1,
                    "title": "Home Blood Pressure Check",
                    "slug": "home-blood-pressure-check",
                    "description": "Blood pressure monitoring at patient's home",
                    "price": "25.00",
                    "custom_price": null,
                    "final_price": "25.00",
                    "duration_minutes": 30,
                    "is_home_service": true,
                    "is_available": true
                }
            ],
            "provider_status": {
                "status": "APPROVED",
                "refusal_reason": null,
                "approved_at": "2026-01-30T11:00:00Z",
                "verified_at": "2026-01-30T11:00:00Z",
                "provider_type": "NURSE",
                "provider_type_display": "Nurse"
            },
            "created_at": "2026-01-30T09:00:00Z",
            "updated_at": "2026-01-30T12:00:00Z"
        }
    },
    "patient_profile": null,
    "addresses": [
        {
            "id": 1,
            "address_line_1": "123 Healthcare Street",
            "address_line_2": "Apt 4B",
            "city": "Paris",
            "state": "Île-de-France",
            "postal_code": "75001",
            "country": "France",
            "is_primary": true,
            "latitude": 48.8566,
            "longitude": 2.3522
        }
    ],
    "provider_type": "NURSE",
    "provider_type_display": "Nurse",
    "subtype": "NURSE",
    "subtype_display": "Nurse"
}
```

#### Response Fields for Nurse Provider

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | User role: `"PROVIDER"` |
| `provider_type` | string | Provider subtype: `"NURSE"` |
| `provider_type_display` | string | Human-readable: `"Nurse"` |
| `provider_profile` | object | Complete provider profile data |
| `provider_profile.status` | string | `PENDING`, `APPROVED`, `REFUSED`, `SUSPENDED` |
| `provider_profile.nurse` | object | Nurse-specific profile details |

#### Nested Nurse Profile Fields

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | Nurse's first name |
| `last_name` | string | Nurse's last name |
| `full_name` | string | Combined first and last name |
| `gender` | string | `MALE`, `FEMALE`, `OTHER`, `PREFER_NOT_TO_SAY` |
| `date_of_birth` | date | Date of birth |
| `profile_image` | url | URL to profile photo |
| `phone_number` | string | Contact phone number |
| `license_number` | string | Professional license number |
| `certification` | string | Nursing certification type |
| `years_of_experience` | integer | Years of professional experience |
| `biography` | string | Professional bio |
| `degree_document` | url | URL to degree document |
| `entrepreneur_card_front` | url | URL to entrepreneur card front image |
| `entrepreneur_card_back` | url | URL to entrepreneur card back image |
| `is_verified` | boolean | Whether documents are verified |
| `is_available` | boolean | Whether accepting appointments |
| `is_home_service_available` | boolean | Whether providing home visits |
| `services` | array | List of services offered |

---

### PATCH Update Profile

Update specific profile fields for the authenticated user.

**Endpoint:** `PATCH /api/auth/me/`

**Headers:**
```
Authorization: Token <your_token_here>
Content-Type: application/json
```
*(Or `multipart/form-data` if uploading files)*

#### Editable Fields for Patients

| Field | Type | Description |
|-------|------|-------------|
| `profile_completed` | boolean | Mark profile as complete |
| `profile_completion_percentage` | integer | Profile completion (0-100) |

#### Editable Fields for Nurse Providers

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | Update first name |
| `last_name` | string | Update last name |
| `gender` | string | Update gender |
| `biography` | string | Update professional bio |
| `years_of_experience` | integer | Update experience years |
| `is_available` | boolean | Toggle availability |
| `is_home_service_available` | boolean | Toggle home service |
| `phone_number` | string | Update phone number |
| `profile_image` | file | Update profile photo |
| `profile_completed` | boolean | Mark profile as complete |
| `profile_completion_percentage` | integer | Profile completion (0-100) |

> ⚠️ **Read-Only Fields:** The following fields cannot be changed via `/api/auth/me/`:
> - `email` (requires separate endpoint)
> - `role`, `account_status`, `is_active`
> - `license_number`, `degree_document` (contact support)
> - `entrepreneur_card_front`, `entrepreneur_card_back` (contact support)

#### Example: Update Nurse Availability

**Request:**
```json
{
    "is_available": false,
    "biography": "Currently on vacation. Back on February 15, 2026."
}
```

**Response (200 OK):**
Returns the full updated profile (same format as GET response).

#### Error Responses

**400 Bad Request - Attempting to Change Sensitive Field:**
```json
{
    "license_number": ["This field cannot be changed from the app. Please contact support."]
}
```

**400 Bad Request - No Updatable Fields:**
```json
{
    "detail": "No updatable fields were provided. The /api/auth/me/ endpoint only accepts a limited set of profile fields (for example name, availability, and profile completion flags). Other account changes must be handled by support."
}
```

**400 Bad Request - Field Not Available for Role:**
```json
{
    "biography": ["This field is only available for provider accounts."]
}
```

---

## Logout

**Endpoint:** `POST /api/auth/logout/`

**Headers:**
```
Authorization: Token <your_token_here>
```

**Request Body:** None required

**Success Response (200 OK):**
```json
{
    "message": "Successfully logged out."
}
```

> 📝 **Note:** After logout, the token is invalidated and cannot be used again. The user must log in again to get a new token.

---

## Account Status Check

Check the status of an account by email (useful for forgot password flows).

**Endpoint:** `POST /api/auth/status/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
    "email": "user@example.com",
    "exists": true,
    "role": "PATIENT",
    "is_active": true
}
```

---

## Password Reset

### Request Password Reset

**Endpoint:** `POST /api/auth/password/reset/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
    "message": "If an account exists with this email, a password reset link has been sent."
}
```

### Confirm Password Reset

**Endpoint:** `POST /api/auth/password/reset/confirm/`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "uid": "encoded_user_id",
    "token": "reset_token_from_email",
    "new_password": "NewSecurePassword123!",
    "new_password_confirm": "NewSecurePassword123!"
}
```

**Success Response (200 OK):**
```json
{
    "message": "Password has been reset successfully."
}
```

---

## Error Handling

### Common Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid credentials |
| 403 | Forbidden - Account inactive, suspended, or pending |
| 404 | Not Found - Resource doesn't exist |
| 423 | Locked - Account temporarily locked (brute force protection) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
    "error": "Human-readable error message",
    "field_name": ["List of validation errors for specific field"]
}
```

---

## Mobile Integration Examples

### Swift (iOS)

```swift
// Patient Registration
func registerPatient(email: String, password: String) {
    let url = URL(string: "https://api.medilink.com/api/auth/patient/register/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body: [String: Any] = [
        "email": email,
        "password": password,
        "password_confirm": password
    ]
    request.httpBody = try? JSONSerialization.data(withJSONObject: body)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        // Handle response
    }.resume()
}

// Nurse Registration with Documents
func registerNurse(email: String, password: String, firstName: String, lastName: String,
                   phoneNumber: String, licenseNumber: String,
                   degreeDocument: Data, cardFront: Data, cardBack: Data) {
    let url = URL(string: "https://api.medilink.com/api/auth/provider/register/")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    
    let boundary = UUID().uuidString
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    
    // Add text fields
    let fields: [String: String] = [
        "email": email,
        "password": password,
        "password_confirm": password,
        "provider_type": "NURSE",
        "first_name": firstName,
        "last_name": lastName,
        "phone_number": phoneNumber,
        "license_number": licenseNumber
    ]
    
    for (key, value) in fields {
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(value)\r\n".data(using: .utf8)!)
    }
    
    // Add degree document
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"degree_document\"; filename=\"degree.pdf\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: application/pdf\r\n\r\n".data(using: .utf8)!)
    body.append(degreeDocument)
    body.append("\r\n".data(using: .utf8)!)
    
    // Add entrepreneur card front
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"entrepreneur_card_front\"; filename=\"card_front.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(cardFront)
    body.append("\r\n".data(using: .utf8)!)
    
    // Add entrepreneur card back
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"entrepreneur_card_back\"; filename=\"card_back.jpg\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
    body.append(cardBack)
    body.append("\r\n".data(using: .utf8)!)
    
    body.append("--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        // Handle response
    }.resume()
}

// Get User Profile
func getProfile(token: String) {
    let url = URL(string: "https://api.medilink.com/api/auth/me/")!
    var request = URLRequest(url: url)
    request.httpMethod = "GET"
    request.setValue("Token \(token)", forHTTPHeaderField: "Authorization")
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        // Handle response
    }.resume()
}
```

### Kotlin (Android)

```kotlin
// Patient Registration
suspend fun registerPatient(email: String, password: String): Response<AuthResponse> {
    val request = PatientRegisterRequest(
        email = email,
        password = password,
        passwordConfirm = password
    )
    return apiService.registerPatient(request)
}

// Nurse Registration with Documents
suspend fun registerNurse(
    email: String,
    password: String,
    firstName: String,
    lastName: String,
    phoneNumber: String,
    licenseNumber: String,
    degreeDocument: File,
    cardFront: File,
    cardBack: File
): Response<ProviderAuthResponse> {
    val emailPart = email.toRequestBody("text/plain".toMediaType())
    val passwordPart = password.toRequestBody("text/plain".toMediaType())
    val passwordConfirmPart = password.toRequestBody("text/plain".toMediaType())
    val providerTypePart = "NURSE".toRequestBody("text/plain".toMediaType())
    val firstNamePart = firstName.toRequestBody("text/plain".toMediaType())
    val lastNamePart = lastName.toRequestBody("text/plain".toMediaType())
    val phonePart = phoneNumber.toRequestBody("text/plain".toMediaType())
    val licensePart = licenseNumber.toRequestBody("text/plain".toMediaType())
    
    val degreePart = MultipartBody.Part.createFormData(
        "degree_document",
        degreeDocument.name,
        degreeDocument.asRequestBody("application/pdf".toMediaType())
    )
    
    val cardFrontPart = MultipartBody.Part.createFormData(
        "entrepreneur_card_front",
        cardFront.name,
        cardFront.asRequestBody("image/jpeg".toMediaType())
    )
    
    val cardBackPart = MultipartBody.Part.createFormData(
        "entrepreneur_card_back",
        cardBack.name,
        cardBack.asRequestBody("image/jpeg".toMediaType())
    )
    
    return apiService.registerProvider(
        email = emailPart,
        password = passwordPart,
        passwordConfirm = passwordConfirmPart,
        providerType = providerTypePart,
        firstName = firstNamePart,
        lastName = lastNamePart,
        phoneNumber = phonePart,
        licenseNumber = licensePart,
        degreeDocument = degreePart,
        entrepreneurCardFront = cardFrontPart,
        entrepreneurCardBack = cardBackPart
    )
}

// Get User Profile
suspend fun getProfile(token: String): Response<UserProfile> {
    return apiService.getProfile("Token $token")
}

// Update Profile
suspend fun updateProfile(token: String, updates: Map<String, Any>): Response<UserProfile> {
    return apiService.updateProfile("Token $token", updates)
}
```

### Flutter (Dart)

```dart
import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';

// Patient Registration
Future<Map<String, dynamic>> registerPatient(String email, String password) async {
  final response = await http.post(
    Uri.parse('https://api.medilink.com/api/auth/patient/register/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
      'password_confirm': password,
    }),
  );
  return jsonDecode(response.body);
}

// Nurse Registration with Documents
Future<Map<String, dynamic>> registerNurse({
  required String email,
  required String password,
  required String firstName,
  required String lastName,
  required String phoneNumber,
  required String licenseNumber,
  required File degreeDocument,
  required File cardFront,
  required File cardBack,
}) async {
  final request = http.MultipartRequest(
    'POST',
    Uri.parse('https://api.medilink.com/api/auth/provider/register/'),
  );
  
  request.fields.addAll({
    'email': email,
    'password': password,
    'password_confirm': password,
    'provider_type': 'NURSE',
    'first_name': firstName,
    'last_name': lastName,
    'phone_number': phoneNumber,
    'license_number': licenseNumber,
  });
  
  request.files.add(await http.MultipartFile.fromPath(
    'degree_document',
    degreeDocument.path,
  ));
  
  request.files.add(await http.MultipartFile.fromPath(
    'entrepreneur_card_front',
    cardFront.path,
  ));
  
  request.files.add(await http.MultipartFile.fromPath(
    'entrepreneur_card_back',
    cardBack.path,
  ));
  
  final streamedResponse = await request.send();
  final response = await http.Response.fromStream(streamedResponse);
  return jsonDecode(response.body);
}

// Get User Profile
Future<Map<String, dynamic>> getProfile(String token) async {
  final response = await http.get(
    Uri.parse('https://api.medilink.com/api/auth/me/'),
    headers: {'Authorization': 'Token $token'},
  );
  return jsonDecode(response.body);
}

// Update Profile
Future<Map<String, dynamic>> updateProfile(
  String token,
  Map<String, dynamic> updates,
) async {
  final response = await http.patch(
    Uri.parse('https://api.medilink.com/api/auth/me/'),
    headers: {
      'Authorization': 'Token $token',
      'Content-Type': 'application/json',
    },
    body: jsonEncode(updates),
  );
  return jsonDecode(response.body);
}
```

---

## Provider Status Workflow

```
┌───────────────────────────────────────────────────────────────────────┐
│                    NURSE REGISTRATION WORKFLOW                        │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. REGISTRATION                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ POST /api/auth/provider/register/                               │ │
│  │ - Email, password                                               │ │
│  │ - First name, last name, phone number                          │ │
│  │ - License number                                                │ │
│  │ - Degree document (PDF/image)                                  │ │
│  │ - Entrepreneur card front & back (images)                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                        │
│                              ▼                                        │
│  2. PENDING STATUS                                                    │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ Account created with status = "PENDING"                        │ │
│  │ Token returned but LOGIN is BLOCKED until approval             │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                              │                                        │
│              ┌───────────────┼───────────────┐                       │
│              ▼               ▼               ▼                        │
│  3a. APPROVED            3b. REFUSED      3c. SUSPENDED              │
│  ┌────────────────┐   ┌────────────────┐  ┌────────────────┐         │
│  │ Admin approves │   │ Admin refuses  │  │ Admin suspends │         │
│  │ documents      │   │ with reason    │  │ for violation  │         │
│  │                │   │                │  │                │         │
│  │ ✅ Can login   │   │ ❌ Cannot login│  │ ❌ Cannot login│         │
│  │ ✅ Full access │   │ ❌ Must reapply│  │ ❌ Contact     │         │
│  │                │   │                │  │    support     │         │
│  └────────────────┘   └────────────────┘  └────────────────┘         │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/patient/register/` | POST | ❌ No | Register a new patient |
| `/api/auth/provider/register/` | POST | ❌ No | Register a new provider (nurse) |
| `/api/auth/login/` | POST | ❌ No | Login (all user types) |
| `/api/auth/logout/` | POST | ✅ Yes | Logout and invalidate token |
| `/api/auth/me/` | GET | ✅ Yes | Get current user profile |
| `/api/auth/me/` | PATCH | ✅ Yes | Update current user profile |
| `/api/auth/status/` | POST | ❌ No | Check account status by email |
| `/api/auth/password/reset/` | POST | ❌ No | Request password reset |
| `/api/auth/password/reset/confirm/` | POST | ❌ No | Confirm password reset |

---

## Support

For issues with:
- **Document verification**: Contact admin support
- **Account suspension**: Contact support@medilink.com
- **Technical issues**: Submit a bug report

---

*Last updated: January 30, 2026*
