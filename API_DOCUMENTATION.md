# Medilink Backend API Documentation
**Frontend-Ready Documentation**  
*Generated: January 28, 2026*

---

## Table of Contents
1. [Authentication & Current User](#1-authentication--current-user)
2. [Update My Profile](#2-update-my-profile)
3. [Complete Backend Endpoints Usage](#3-complete-backend-endpoints-usage)
4. [Address App Documentation](#4-address-app-documentation)
5. [Frontend Integration Summary](#5-frontend-integration-summary)

---

## 1. Authentication & Current User

### Authentication Method
**Token-based authentication (Django Rest Framework Token Authentication)**

- Authentication type: `Token`
- Token storage: Database (persistent until logout)
- Token lifetime: No expiration (valid until explicitly deleted via logout)

### Required Headers

```http
Authorization: Token <your_token_here>
```

**Example:**
```http
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

---

### Get Current User Data

**Endpoint:** `/api/auth/me/`  
**Method:** `GET`  
**Authentication:** Required  
**Permissions:** Authenticated users only

#### Request Example

```bash
curl -X GET http://localhost:8000/api/auth/me/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

#### Full Response Example (Patient)

```json
{
  "id": 1,
  "email": "patient@example.com",
  "role": "PATIENT",
  "account_status": "ACTIVE",
  "is_active": true,
  "is_staff": false,
  "email_verified": false,
  "email_verified_at": null,
  "profile_completed": false,
  "profile_completion_percentage": 0,
  "last_login": "2026-01-28T10:30:00Z",
  "last_login_ip": "192.168.1.1",
  "created_at": "2026-01-25T08:00:00Z",
  "updated_at": "2026-01-28T10:30:00Z",
  "provider_profile": null,
  "patient_profile": {
    "is_patient": true
  },
  "addresses": []
}
```

#### Full Response Example (Provider - Doctor)

```json
{
  "id": 2,
  "email": "doctor@example.com",
  "role": "PROVIDER",
  "account_status": "ACTIVE",
  "is_active": true,
  "is_staff": false,
  "email_verified": false,
  "email_verified_at": null,
  "profile_completed": false,
  "profile_completion_percentage": 45,
  "last_login": "2026-01-28T11:00:00Z",
  "last_login_ip": "192.168.1.2",
  "created_at": "2026-01-26T09:00:00Z",
  "updated_at": "2026-01-28T11:00:00Z",
  "provider_profile": {
    "status": "PENDING",
    "refusal_reason": null,
    "approved_at": null,
    "verified_at": null,
    "doctor": {
      "id": 1,
      "email": "doctor@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "Dr. John Doe",
      "gender": "M",
      "gender_display": "Male",
      "date_of_birth": "1985-05-15",
      "profile_image": "http://localhost:8000/media/doctors/profile_images/john_doe.jpg",
      "license_number": "MD123456",
      "years_of_experience": 10,
      "biography": "Experienced cardiologist with 10 years of practice.",
      "degree_document": "http://localhost:8000/media/doctors/degrees/john_doe_degree.pdf",
      "is_verified": false,
      "is_available": true,
      "is_home_service_available": false,
      "provider_status": {
        "status": "PENDING",
        "refusal_reason": null,
        "approved_at": null,
        "verified_at": null
      },
      "created_at": "2026-01-26T09:00:00Z",
      "updated_at": "2026-01-28T11:00:00Z"
    }
  },
  "patient_profile": null,
  "addresses": [
    {
      "id": 1,
      "content_type": 15,
      "content_type_name": "doctor",
      "object_id": 1,
      "street": "123 Medical Center Blvd",
      "city": "Algiers",
      "state": "Algiers",
      "zip_code": "16000",
      "country": "Algeria",
      "latitude": "36.753768",
      "longitude": "3.058756",
      "is_primary": true,
      "address_type": "CLINIC",
      "notes": "Main clinic location",
      "created_at": "2026-01-26T10:00:00Z",
      "updated_at": "2026-01-26T10:00:00Z"
    }
  ]
}
```

#### Response Fields Description

| Field | Type | Read-Only | Description |
|-------|------|-----------|-------------|
| `id` | integer | ✅ Yes | User unique identifier |
| `email` | string | ✅ Yes | User email address (login identifier) |
| `role` | string | ✅ Yes | User role: `PATIENT`, `PROVIDER`, `ADMIN` |
| `account_status` | string | ✅ Yes | Account status: `ACTIVE`, `SUSPENDED`, `DEACTIVATED` |
| `is_active` | boolean | ✅ Yes | Django internal active flag |
| `is_staff` | boolean | ✅ Yes | Can access admin site |
| `email_verified` | boolean | ✅ Yes | Email verification status |
| `email_verified_at` | datetime/null | ✅ Yes | When email was verified |
| `profile_completed` | boolean | ✅ Yes | Whether profile is complete |
| `profile_completion_percentage` | integer | ✅ Yes | Profile completion (0-100) |
| `last_login` | datetime/null | ✅ Yes | Last login timestamp |
| `last_login_ip` | string/null | ✅ Yes | Last login IP address |
| `created_at` | datetime | ✅ Yes | Account creation timestamp |
| `updated_at` | datetime | ✅ Yes | Last update timestamp |
| `provider_profile` | object/null | ✅ Yes | Provider details (only if `role=PROVIDER`) |
| `patient_profile` | object/null | ✅ Yes | Patient details (only if `role=PATIENT`) |
| `addresses` | array | ✅ Yes | All addresses linked to this user/provider |

#### Provider Profile Structure

When `role=PROVIDER`, the `provider_profile` object contains:

```json
{
  "status": "PENDING|APPROVED|REFUSED|SUSPENDED",
  "refusal_reason": "Reason text or null",
  "approved_at": "2026-01-27T10:00:00Z or null",
  "verified_at": "2026-01-27T10:00:00Z or null (legacy)",
  "doctor": { /* Doctor profile if provider_type=DOCTOR */ },
  "nurse": { /* Nurse profile if provider_type=NURSE */ },
  "clinic": { /* Clinic profile if provider_type=CLINIC */ },
  "laboratory": { /* Laboratory profile if provider_type=LABORATORY */ },
  "seller": { /* Seller profile if provider_type=SELLER */ },
  "vtc": { /* VTC profile if provider_type=VTC */ }
}
```

**Provider Status Values:**
- `PENDING`: Awaiting admin approval (cannot access protected resources)
- `APPROVED`: Verified and can access all provider features
- `REFUSED`: Application rejected (see `refusal_reason`)
- `SUSPENDED`: Temporarily suspended after approval

---

## 2. Update My Profile

### Update Current User Profile

**Endpoint:** `/api/auth/me/`  
**Methods:** `PATCH` or `PUT`  
**Authentication:** Required  
**Permissions:** Authenticated users only

⚠️ **IMPORTANT:** This endpoint currently has **ALL fields set to read-only** in the `UserProfileUpdateSerializer`. The base User model fields cannot be updated through this endpoint.

To update provider-specific data (doctor profile, nurse profile, clinic, etc.), use the dedicated provider endpoints listed in Section 3.

#### Request Example

```bash
curl -X PATCH http://localhost:8000/api/auth/me/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Response

Returns the full user profile (same as GET `/api/auth/me/`)

```json
{
  "id": 1,
  "email": "patient@example.com",
  "role": "PATIENT",
  "account_status": "ACTIVE",
  ...
}
```

#### Fields That CANNOT Be Updated (Read-Only)

The following fields are **read-only** and cannot be changed via PATCH/PUT:

- ❌ `email` - Cannot be changed (use separate email change endpoint if needed)
- ❌ `role` - Admin-only field
- ❌ `account_status` - Admin-only field
- ❌ `is_active` - Admin-only field
- ❌ `is_staff` - Admin-only field
- ❌ `is_superuser` - Admin-only field
- ❌ `email_verified` - System-controlled
- ❌ `email_verified_at` - System-controlled
- ❌ `profile_completed` - Auto-calculated
- ❌ `profile_completion_percentage` - Auto-calculated
- ❌ `last_login` - System-tracked
- ❌ `last_login_ip` - System-tracked
- ❌ `created_at` - Immutable
- ❌ `updated_at` - Auto-updated

#### Updating Provider-Specific Profiles

To update doctor, nurse, clinic, or other provider details, use the dedicated endpoints:

- **Doctor Profile:** Use provider-specific endpoints (see Section 3)
- **Nurse Profile:** Use provider-specific endpoints (see Section 3)
- **Clinic Profile:** `GET/PATCH /api/provider/clinic/` (see Section 3)
- **Other Providers:** See Section 3 for complete list

---

## 3. Complete Backend Endpoints Usage

### 3.1 Authentication Endpoints

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/auth/patient/register/` | POST | No | Register new patient | ✅ Active |
| `/api/auth/provider/register/` | POST | No | Register new provider | ✅ Active |
| `/api/auth/login/` | POST | No | Login (all user types) | ✅ Active |
| `/api/auth/logout/` | POST | Yes | Logout and delete token | ✅ Active |
| `/api/auth/me/` | GET | Yes | Get current user profile | ✅ Active |
| `/api/auth/me/` | PATCH/PUT | Yes | Update profile (limited fields) | ✅ Active |
| `/api/auth/status/` | POST | No | Check account status by email | ✅ Active |
| `/api/auth/password/reset/` | POST | No | Request password reset | ✅ Active |
| `/api/auth/password/reset/confirm/` | POST | No | Confirm password reset | ✅ Active |

#### 3.1.1 Patient Registration

**POST** `/api/auth/patient/register/`

```json
// Request
{
  "email": "patient@example.com",
  "password": "securePassword123",
  "password_confirm": "securePassword123"
}

// Response (201 Created)
{
  "user": {
    "id": 1,
    "email": "patient@example.com",
    "role": "PATIENT",
    "is_active": true,
    "created_at": "2026-01-28T12:00:00Z"
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

#### 3.1.2 Provider Registration

**POST** `/api/auth/provider/register/`

⚠️ **Idempotent:** If provider already exists, returns existing provider with 200 status.

```json
// Request
{
  "email": "doctor@example.com",
  "password": "securePassword123",
  "password_confirm": "securePassword123",
  "provider_type": "DOCTOR"
}

// Response (201 Created or 200 OK if exists)
{
  "user": {
    "id": 2,
    "email": "doctor@example.com",
    "role": "PROVIDER",
    "is_active": true,
    "created_at": "2026-01-28T12:00:00Z"
  },
  "provider": {
    "status": "PENDING",
    "refusal_reason": null,
    "approved_at": null,
    "verified_at": null
  },
  "token": "abc123def456..."
}
```

**Provider Types:**
- `DOCTOR` - Individual doctor
- `NURSE` - Individual nurse
- `CLINIC` - Medical clinic/center
- `LABORATORY` - Medical laboratory
- `VTC` - Healthcare VTC service
- `SELLER` - Medical equipment/supplies seller

#### 3.1.3 Login

**POST** `/api/auth/login/`

```json
// Request
{
  "email": "user@example.com",
  "password": "password123"
}

// Response (200 OK)
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "PATIENT",
    "is_active": true,
    "created_at": "2026-01-25T08:00:00Z"
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}

// For providers, includes provider_type info:
{
  "user": {
    "id": 2,
    "email": "doctor@example.com",
    "role": "PROVIDER",
    "is_active": true,
    "created_at": "2026-01-26T09:00:00Z",
    "provider_type": "DOCTOR",
    "provider_type_display": "Doctor"
  },
  "token": "abc123..."
}

// Error Response - Provider Pending (403 Forbidden)
{
  "error": "Account verification in progress.",
  "provider_status": "PENDING",
  "message": "Your account is currently being reviewed by our medical board..."
}

// Error Response - Provider Refused (403 Forbidden)
{
  "error": "Account registration refused.",
  "provider_status": "REFUSED",
  "refusal_reason": "Invalid medical license number",
  "message": "Your account registration was refused for the following reason: Invalid medical license number..."
}

// Error Response - Account Locked (423 Locked)
{
  "error": "Account temporarily locked due to multiple failed login attempts.",
  "message": "Please try again later or contact support."
}
```

**Login Validation:**
- ✅ Email and password authentication
- ✅ Account status check (`ACTIVE` only)
- ✅ Provider status check (must be `APPROVED` to login)
- ✅ Account lock check (brute-force protection)
- ✅ Failed login attempt tracking
- ✅ IP address logging

#### 3.1.4 Logout

**POST** `/api/auth/logout/`

```json
// Request - Headers only
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

// Response (200 OK)
{
  "message": "Successfully logged out."
}
```

#### 3.1.5 Check Account Status

**POST** `/api/auth/status/`

Public endpoint to check if an email exists and its status.

```json
// Request
{
  "email": "doctor@example.com"
}

// Response - User Exists (200 OK)
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
    "verified_at": null
  }
}

// Response - User Not Found (200 OK)
{
  "email": "unknown@example.com",
  "exists": false
}
```

---

### 3.2 Provider Endpoints

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/provider/status/` | GET | Yes | Get provider status | ✅ Active |
| `/api/provider/clinic/` | GET/PATCH | Yes | Clinic profile management | ✅ Active |
| `/api/provider/public/` | GET | No | List public providers | ✅ Active |
| `/api/provider/clinic/` (ViewSet) | GET/POST/PUT/PATCH/DELETE | Yes | Clinic CRUD operations | ✅ Active |
| `/api/provider/laboratory/` | GET/POST/PUT/PATCH/DELETE | Yes | Laboratory CRUD operations | ✅ Active |
| `/api/provider/seller/` | GET/POST/PUT/PATCH/DELETE | Yes | Seller CRUD operations | ✅ Active |
| `/api/provider/vtc/` | GET/POST/PUT/PATCH/DELETE | Yes | VTC CRUD operations | ✅ Active |

**Authentication Guard:**
All provider endpoints (except `/public/`) use `ProviderTokenAuthentication` which enforces:
- User must be authenticated
- User must have `PROVIDER` role
- Provider status must be `APPROVED`

❌ **PENDING/REFUSED/SUSPENDED providers cannot access protected routes.**

#### 3.2.1 Get Provider Status

**GET** `/api/provider/status/`

```json
// Response (200 OK)
{
  "status": "APPROVED",
  "refusal_reason": null,
  "approved_at": "2026-01-27T10:00:00Z",
  "verified_at": "2026-01-27T10:00:00Z"
}
```

#### 3.2.2 Clinic Profile (Authenticated)

**GET** `/api/provider/clinic/`  
**PATCH** `/api/provider/clinic/`

Get or update the authenticated provider's clinic profile.

```json
// Response
{
  "id": 1,
  "clinic_name": "City Medical Center",
  "phone_number": "+213555123456",
  "license_number": "CL123456",
  "license_document": "http://localhost:8000/media/clinics/licenses/clinic_license.pdf",
  "description": "Full-service medical clinic",
  "created_at": "2026-01-26T09:00:00Z",
  "updated_at": "2026-01-28T11:00:00Z"
}
```

---

### 3.3 Address Endpoints

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/addresses/` | GET | Yes | List my addresses | ✅ Active |
| `/api/addresses/` | POST | Yes | Create new address | ✅ Active |
| `/api/addresses/{id}/` | GET | Yes | Get address details | ✅ Active |
| `/api/addresses/{id}/` | PUT/PATCH | Yes | Update address | ✅ Active |
| `/api/addresses/{id}/` | DELETE | Yes | Delete address | ✅ Active |

See Section 4 for detailed address documentation.

---

### 3.4 Admin Endpoints

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/admin/providers/` | GET | Admin | List all providers | ✅ Active |
| `/api/admin/providers/{id}/` | GET | Admin | Get provider details | ✅ Active |
| `/api/admin/providers/{id}/` | PATCH | Admin | Update provider (approve/refuse) | ✅ Active |

**Authentication:** Admin role required.

---

### 3.5 Specialties & Services Endpoints

#### 3.5.1 Specialties (Public Read, Admin Write)

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/specialties/` | GET | No | List all active specialties | ✅ Active |
| `/api/specialties/{id}/` | GET | No | Get specialty details | ✅ Active |
| `/api/specialties/` | POST | Admin | Create specialty | ✅ Active |
| `/api/specialties/{id}/` | PUT/PATCH | Admin | Update specialty | ✅ Active |
| `/api/specialties/{id}/` | DELETE | Admin | Delete specialty | ✅ Active |

**GET** `/api/specialties/`

```json
// Response (200 OK)
[
  {
    "id": 1,
    "title": "Cardiology",
    "title_ar": "أمراض القلب",
    "title_fr": "Cardiologie",
    "title_en": "Cardiology",
    "slug": "cardiology",
    "description": "Heart and cardiovascular system",
    "medical_domain": "Internal Medicine",
    "icon": "http://localhost:8000/media/specialties/icons/cardiology.png",
    "is_active": true,
    "created_at": "2026-01-28T10:00:00Z",
    "updated_at": "2026-01-28T10:00:00Z"
  }
]
```

#### 3.5.2 Doctor Specialties (Doctor Only)

| Endpoint | Method | Auth | Permission | Purpose | Status |
|----------|--------|------|------------|---------|--------|
| `/api/specialties/doctor-specialties/` | GET | Yes | Doctor | List my specialties | ✅ Active |
| `/api/specialties/doctor-specialties/` | POST | Yes | Doctor | Add specialty | ✅ Active |
| `/api/specialties/doctor-specialties/{id}/` | PUT/PATCH | Yes | Doctor | Update specialty | ✅ Active |
| `/api/specialties/doctor-specialties/{id}/` | DELETE | Yes | Doctor | Remove specialty | ✅ Active |
| `/api/specialties/doctor-specialties/assign/` | POST | Yes | Doctor | Assign specialty (alternative) | ✅ Active |

**POST** `/api/specialties/doctor-specialties/`

```json
// Request
{
  "specialty_id": 1,
  "is_primary": true,
  "years_of_experience": 5
}

// Response (201 Created)
{
  "id": 1,
  "doctor": 1,
  "doctor_name": "Dr. John Doe",
  "specialty": {
    "id": 1,
    "title": "Cardiology",
    "slug": "cardiology"
  },
  "is_primary": true,
  "years_of_experience": 5,
  "created_at": "2026-01-28T12:00:00Z"
}
```

#### 3.5.3 Services (Public Read, Admin Write)

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/services/` | GET | No | List all active services | ✅ Active |
| `/api/services/{id}/` | GET | No | Get service details | ✅ Active |
| `/api/services/` | POST | Admin | Create service | ✅ Active |
| `/api/services/{id}/` | PUT/PATCH | Admin | Update service | ✅ Active |
| `/api/services/{id}/` | DELETE | Admin | Delete service | ✅ Active |

**GET** `/api/services/`

```json
// Response (200 OK)
[
  {
    "id": 1,
    "title": "General Consultation",
    "slug": "general-consultation",
    "description": "Initial patient consultation and examination",
    "price": "3000.00",
    "currency": "DZD",
    "currency_display": "Algerian Dinar",
    "duration_minutes": 30,
    "icon": null,
    "is_home_service": false,
    "is_active": true,
    "specialty": {
      "id": 1,
      "title": "General Medicine"
    },
    "created_at": "2026-01-28T10:00:00Z",
    "updated_at": "2026-01-28T10:00:00Z"
  }
]
```

#### 3.5.4 Doctor Services (Doctor Only)

| Endpoint | Method | Auth | Permission | Purpose | Status |
|----------|--------|------|------------|---------|--------|
| `/api/services/doctor-services/` | GET | Yes | Doctor | List my services | ✅ Active |
| `/api/services/doctor-services/` | POST | Yes | Doctor | Add service | ✅ Active |
| `/api/services/doctor-services/{id}/` | PUT/PATCH | Yes | Doctor | Update service (price, availability) | ✅ Active |
| `/api/services/doctor-services/{id}/` | DELETE | Yes | Doctor | Remove service | ✅ Active |

**POST** `/api/services/doctor-services/`

```json
// Request
{
  "service_id": 1,
  "custom_price": "3500.00",
  "is_available": true
}

// Response (201 Created)
{
  "id": 1,
  "doctor": 1,
  "doctor_name": "Dr. John Doe",
  "service": {
    "id": 1,
    "title": "General Consultation",
    "price": "3000.00"
  },
  "custom_price": "3500.00",
  "final_price": "3500.00",
  "is_available": true,
  "created_at": "2026-01-28T12:00:00Z"
}
```

#### 3.5.5 Nurse Services (Nurse Only)

| Endpoint | Method | Auth | Permission | Purpose | Status |
|----------|--------|------|------------|---------|--------|
| `/api/services/nurse-services/` | GET | Yes | Nurse | List my services | ✅ Active |
| `/api/services/nurse-services/` | POST | Yes | Nurse | Add service | ✅ Active |
| `/api/services/nurse-services/{id}/` | PUT/PATCH | Yes | Nurse | Update service (price, availability) | ✅ Active |
| `/api/services/nurse-services/{id}/` | DELETE | Yes | Nurse | Remove service | ✅ Active |

**POST** `/api/services/nurse-services/`

```json
// Request
{
  "service_id": 5,
  "custom_price": "2000.00",
  "is_available": true
}

// Response (201 Created)
{
  "id": 1,
  "nurse": 1,
  "nurse_name": "Jane Smith",
  "service": {
    "id": 5,
    "title": "Home Injection",
    "price": "1500.00"
  },
  "custom_price": "2000.00",
  "final_price": "2000.00",
  "is_available": true,
  "created_at": "2026-01-28T12:00:00Z"
}
```

---

### 3.6 Provider Profile Endpoint

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/provider/profile/` | GET | Yes (Provider) | Get provider-specific profile | ✅ Active |
| `/api/provider/profile/` | PUT/PATCH | Yes (Provider) | Update provider-specific profile | ✅ Active |

This endpoint automatically routes to the appropriate serializer based on provider type (Doctor, Nurse, Clinic, etc.).

**GET** `/api/provider/profile/`

```json
// Response for Doctor (200 OK)
{
  "id": 1,
  "email": "doctor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "Dr. John Doe",
  "gender": "MALE",
  "gender_display": "Male",
  "date_of_birth": "1985-05-15",
  "profile_image": "http://localhost:8000/media/doctors/profiles/john_doe.jpg",
  "license_number": "MD123456",
  "years_of_experience": 10,
  "biography": "Experienced cardiologist",
  "degree_document": "http://localhost:8000/media/doctors/degrees/john_degree.pdf",
  "is_verified": true,
  "is_available": true,
  "is_home_service_available": false,
  "specialties": [
    {
      "id": 1,
      "title": "Cardiology",
      "title_ar": "أمراض القلب",
      "title_fr": "Cardiologie",
      "slug": "cardiology",
      "is_primary": true,
      "years_of_experience": 10
    }
  ],
  "services": [
    {
      "id": 1,
      "title": "General Consultation",
      "slug": "general-consultation",
      "description": "Initial patient consultation",
      "price": "3000.00",
      "custom_price": "3500.00",
      "final_price": "3500.00",
      "duration_minutes": 30,
      "is_home_service": false,
      "is_available": true
    }
  ],
  "provider_status": {
    "status": "APPROVED",
    "refusal_reason": null,
    "approved_at": "2026-01-27T10:00:00Z"
  },
  "created_at": "2026-01-26T09:00:00Z",
  "updated_at": "2026-01-28T11:00:00Z"
}
```

**PATCH** `/api/provider/profile/`

```json
// Request (Doctor)
{
  "first_name": "John",
  "last_name": "Doe",
  "biography": "Updated biography",
  "is_available": true,
  "is_home_service_available": true
}

// Response (200 OK)
{
  "id": 1,
  "email": "doctor@example.com",
  "first_name": "John",
  "last_name": "Doe",
  ...
}
```

---

### 3.7 Other Endpoints

---

### 3.7 Other Endpoints

| Endpoint | Method | Auth | Purpose | Status |
|----------|--------|------|---------|--------|
| `/api/medical-records/` | GET/POST | Yes | Medical records CRUD | ✅ Active |
| `/api/social-links/` | GET/POST | Yes | Social media links | ✅ Active |

---

### 3.8 Deprecated/Unused Endpoints

⚠️ **DO NOT USE** the following endpoints:

- None identified at this time. All exposed endpoints are active and intended for frontend use.

---

## 4. Address App Documentation

### 4.1 Address Data Model

The Address model uses **Django's Generic Foreign Key** system to attach addresses to any model (User, Provider, Doctor, Nurse, Clinic, etc.).

#### Address Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Auto | Unique identifier |
| `content_type` | integer | Auto* | ContentType ID (auto-set to User if omitted) |
| `content_type_name` | string | Read-only | Human-readable model name |
| `object_id` | integer | Auto* | Object ID (auto-set to current user if omitted) |
| `street` | string | No | Street address |
| `city` | string | No | City name |
| `state` | string | No | State/Province |
| `zip_code` | string | No | ZIP/Postal code |
| `country` | string | No | Country (default: "Algeria") |
| `latitude` | decimal | No | Latitude coordinate (9 digits, 6 decimal places) |
| `longitude` | decimal | No | Longitude coordinate (9 digits, 6 decimal places) |
| `is_primary` | boolean | No | Primary address flag (default: false) |
| `address_type` | string | No | Type: `HOME`, `WORK`, `CLINIC`, `HOSPITAL`, `OTHER` (default: `WORK`) |
| `notes` | text | No | Optional notes |
| `created_at` | datetime | Auto | Creation timestamp |
| `updated_at` | datetime | Auto | Last update timestamp |

*Auto-set: If `content_type` and `object_id` are not provided, they default to the current authenticated user.

### 4.2 Address Relationship to User

Addresses are linked to users using Generic Foreign Keys:

- **Patient:** Addresses attached to User model
- **Provider:** Can have addresses attached to:
  - User model
  - Provider model
  - Doctor/Nurse/Clinic profile models

When you call `GET /api/auth/me/`, the `addresses` field aggregates all addresses from all related models.

### 4.3 Address Operations

#### 4.3.1 List My Addresses

**GET** `/api/addresses/`

```bash
curl -X GET http://localhost:8000/api/addresses/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Response:**
```json
[
  {
    "id": 1,
    "content_type": 10,
    "content_type_name": "user",
    "object_id": 1,
    "street": "123 Main Street",
    "city": "Algiers",
    "state": "Algiers",
    "zip_code": "16000",
    "country": "Algeria",
    "latitude": "36.753768",
    "longitude": "3.058756",
    "is_primary": true,
    "address_type": "HOME",
    "notes": "Main residence",
    "created_at": "2026-01-28T10:00:00Z",
    "updated_at": "2026-01-28T10:00:00Z"
  }
]
```

**Query Parameters:**
- `?is_primary=true` - Filter primary addresses
- `?address_type=CLINIC` - Filter by type
- `?city=Algiers` - Filter by city
- `?country=Algeria` - Filter by country

#### 4.3.2 Create Address

**POST** `/api/addresses/`

```json
// Request
{
  "street": "456 Health Avenue",
  "city": "Oran",
  "state": "Oran",
  "zip_code": "31000",
  "country": "Algeria",
  "latitude": "35.696111",
  "longitude": "-0.633333",
  "is_primary": false,
  "address_type": "CLINIC",
  "notes": "Secondary clinic location"
}

// Response (201 Created)
{
  "id": 2,
  "content_type": 10,
  "content_type_name": "user",
  "object_id": 1,
  "street": "456 Health Avenue",
  "city": "Oran",
  "state": "Oran",
  "zip_code": "31000",
  "country": "Algeria",
  "latitude": "35.696111",
  "longitude": "-0.633333",
  "is_primary": false,
  "address_type": "CLINIC",
  "notes": "Secondary clinic location",
  "created_at": "2026-01-28T12:00:00Z",
  "updated_at": "2026-01-28T12:00:00Z"
}
```

**Default Behavior:**
- If `content_type` and `object_id` are **not provided**, the address is automatically attached to the current authenticated user.
- If you want to attach to a provider/doctor profile, you must explicitly provide `content_type` and `object_id`.

#### 4.3.3 Update Address

**PUT/PATCH** `/api/addresses/{id}/`

```json
// Request (PATCH)
{
  "is_primary": true,
  "notes": "Updated notes"
}

// Response (200 OK)
{
  "id": 2,
  "content_type": 10,
  "content_type_name": "user",
  "object_id": 1,
  "street": "456 Health Avenue",
  "city": "Oran",
  "state": "Oran",
  "zip_code": "31000",
  "country": "Algeria",
  "latitude": "35.696111",
  "longitude": "-0.633333",
  "is_primary": true,
  "address_type": "CLINIC",
  "notes": "Updated notes",
  "created_at": "2026-01-28T12:00:00Z",
  "updated_at": "2026-01-28T12:30:00Z"
}
```

#### 4.3.4 Delete Address

**DELETE** `/api/addresses/{id}/`

```bash
curl -X DELETE http://localhost:8000/api/addresses/2/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

**Response:** `204 No Content`

### 4.4 Address Type Choices

| Value | Display | Common Use Case |
|-------|---------|-----------------|
| `HOME` | Home | Patient home address |
| `WORK` | Work | Office/workplace |
| `CLINIC` | Clinic | Doctor/Nurse clinic location |
| `HOSPITAL` | Hospital | Hospital affiliation |
| `OTHER` | Other | Other locations |

---

## 5. Frontend Integration Summary

### 5.1 Quick Reference

| Task | Endpoint | Method | Auth |
|------|----------|--------|------|
| **Login** | `/api/auth/login/` | POST | No |
| **Get current user** | `/api/auth/me/` | GET | Yes |
| **Update profile** | `/api/auth/me/` | PATCH | Yes* |
| **List addresses** | `/api/addresses/` | GET | Yes |
| **Create address** | `/api/addresses/` | POST | Yes |
| **Update address** | `/api/addresses/{id}/` | PATCH | Yes |
| **Delete address** | `/api/addresses/{id}/` | DELETE | Yes |

*Currently all fields are read-only. Use provider-specific endpoints for profile updates.

### 5.2 Authentication Flow

```javascript
// 1. Login
const loginResponse = await fetch('http://localhost:8000/api/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { user, token } = await loginResponse.json();
// Store token: localStorage.setItem('authToken', token);

// 2. Get current user
const userResponse = await fetch('http://localhost:8000/api/auth/me/', {
  headers: {
    'Authorization': `Token ${token}`
  }
});

const currentUser = await userResponse.json();
```

### 5.3 Profile Completion Flow

For providers, guide users through profile completion:

```javascript
const user = await fetchCurrentUser(); // GET /api/auth/me/

if (user.role === 'PROVIDER') {
  // Check provider status
  if (user.provider_profile.status === 'PENDING') {
    // Show: "Your account is pending approval"
    // Completion: user.profile_completion_percentage
  } else if (user.provider_profile.status === 'REFUSED') {
    // Show refusal reason
    console.log(user.provider_profile.refusal_reason);
  } else if (user.provider_profile.status === 'APPROVED') {
    // Provider is approved - allow full access
  }
  
  // Check if address is needed
  if (user.addresses.length === 0) {
    // Prompt user to add address
  }
}
```

### 5.4 Address Management Flow

```javascript
// List addresses
const addresses = await fetch('http://localhost:8000/api/addresses/', {
  headers: { 'Authorization': `Token ${token}` }
}).then(r => r.json());

// Create address
const newAddress = await fetch('http://localhost:8000/api/addresses/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    street: '123 Main St',
    city: 'Algiers',
    country: 'Algeria',
    is_primary: true,
    address_type: 'HOME'
  })
}).then(r => r.json());

// Update address
const updated = await fetch(`http://localhost:8000/api/addresses/${addressId}/`, {
  method: 'PATCH',
  headers: {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ is_primary: true })
}).then(r => r.json());

// Delete address
await fetch(`http://localhost:8000/api/addresses/${addressId}/`, {
  method: 'DELETE',
  headers: { 'Authorization': `Token ${token}` }
});
```

### 5.5 Common Mistakes to Avoid

#### ❌ Mistake 1: Trying to update email via `/api/auth/me/`
```javascript
// DON'T DO THIS - email is read-only
await fetch('/api/auth/me/', {
  method: 'PATCH',
  body: JSON.stringify({ email: 'newemail@example.com' })
});
```

**✅ Solution:** Email cannot be changed. If needed, implement a separate email change endpoint.

---

#### ❌ Mistake 2: Forgetting to check provider status before allowing access
```javascript
// DON'T DO THIS
if (user.role === 'PROVIDER') {
  // Allow access to provider features
}
```

**✅ Solution:** Always check provider approval status:
```javascript
if (user.role === 'PROVIDER' && user.provider_profile.status === 'APPROVED') {
  // Allow access
} else if (user.provider_profile.status === 'PENDING') {
  // Show pending message
}
```

---

#### ❌ Mistake 3: Not handling 403 errors for PENDING providers
```javascript
// User tries to access protected provider endpoint
const response = await fetch('/api/provider/status/');
// Response: 403 Forbidden
```

**✅ Solution:** Handle 403 and show appropriate message:
```javascript
try {
  const response = await fetch('/api/provider/status/', {
    headers: { 'Authorization': `Token ${token}` }
  });
  
  if (response.status === 403) {
    const error = await response.json();
    // Show: error.error or error.message
    // Example: "Provider account is pending approval..."
  }
} catch (error) {
  // Handle network errors
}
```

---

#### ❌ Mistake 4: Manually setting content_type for addresses
```javascript
// DON'T DO THIS unless attaching to non-user model
await fetch('/api/addresses/', {
  method: 'POST',
  body: JSON.stringify({
    content_type: 10, // Manual content type
    object_id: 1,
    street: '123 Main St'
  })
});
```

**✅ Solution:** Omit `content_type` and `object_id` for user addresses:
```javascript
// Backend automatically attaches to current user
await fetch('/api/addresses/', {
  method: 'POST',
  body: JSON.stringify({
    street: '123 Main St',
    city: 'Algiers'
  })
});
```

---

#### ❌ Mistake 5: Not validating token expiration
```javascript
// Assuming token is always valid
const user = await fetch('/api/auth/me/', {
  headers: { 'Authorization': `Token ${token}` }
});
```

**✅ Solution:** Handle 401 Unauthorized:
```javascript
const response = await fetch('/api/auth/me/', {
  headers: { 'Authorization': `Token ${token}` }
});

if (response.status === 401) {
  // Token invalid - redirect to login
  localStorage.removeItem('authToken');
  window.location.href = '/login';
}
```

---

### 5.6 Error Response Format

All endpoints return consistent error responses:

```json
// Validation Error (400)
{
  "email": ["A user with this email already exists."],
  "password": ["This password is too short."]
}

// Authentication Error (401)
{
  "error": "Invalid email or password."
}

// Permission Error (403)
{
  "error": "Account is pending. Access denied.",
  "account_status": "PENDING"
}

// Not Found (404)
{
  "detail": "Not found."
}
```

---

### 5.7 Complete Integration Checklist

- [ ] Store token securely (localStorage/sessionStorage)
- [ ] Add `Authorization: Token <token>` header to all authenticated requests
- [ ] Handle 401 (redirect to login)
- [ ] Handle 403 (show status messages for PENDING/REFUSED providers)
- [ ] Check `user.role` to show role-specific UI
- [ ] Check `user.provider_profile.status` for providers
- [ ] Use `user.profile_completion_percentage` for progress indicators
- [ ] Display `user.addresses` array for address management
- [ ] Validate provider status before showing protected features
- [ ] Show clear error messages from backend responses
- [ ] Implement logout (DELETE token)

---

## Appendix: Base URL Configuration

**Development:** `http://localhost:8000`  
**Production:** Update with your production domain

All endpoints are prefixed with the base URL:
- Development: `http://localhost:8000/api/auth/login/`
- Production: `https://api.yourdomain.com/api/auth/login/`

---

## Document Version

**Version:** 1.0  
**Last Updated:** January 28, 2026  
**Author:** Senior Backend Engineer & Technical Writer  
**Status:** Production-Ready Documentation

---

**End of Documentation**
