# Medilink Backend API Documentation

**Version:** 2.0.0  
**Last Updated:** January 28, 2026

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Profile Endpoints](#profile-endpoints)
4. [Addresses Endpoints](#addresses-endpoints)
5. [Services Endpoints](#services-endpoints)
6. [Specialties Endpoints](#specialties-endpoints)
7. [Patient Records Endpoints](#patient-records-endpoints)
8. [Error Handling](#error-handling)

---

## Overview

Medilink is a healthcare platform connecting patients with doctors, nurses, clinics, laboratories, VTC health providers, and other healthcare providers.

### Base URL
```
http://localhost:8000/api/
```

### Authentication
All authenticated endpoints require a Token in the header:
```
Authorization: Token <your-token>
```

---

## Authentication

### Login
**POST** `/api/auth/login/`

**Purpose:** Authenticate user and get access token.

**Auth Required:** No

**Request:**
```json
{
    "email": "user@example.com",
    "password": "your-password"
}
```

**Response (200):**
```json
{
    "token": "abc123...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "role": "PATIENT"
    }
}
```

### Logout
**POST** `/api/auth/logout/`

**Purpose:** Invalidate current access token.

**Auth Required:** Yes

**Response (200):**
```json
{
    "message": "Successfully logged out."
}
```

### Patient Registration
**POST** `/api/auth/patient/register/`

**Purpose:** Register a new patient account.

**Auth Required:** No

**Request:**
```json
{
    "email": "patient@example.com",
    "password": "secure-password",
    "password2": "secure-password"
}
```

**Response (201):**
```json
{
    "token": "abc123...",
    "user": {
        "id": 1,
        "email": "patient@example.com",
        "role": "PATIENT"
    }
}
```

### Provider Registration
**POST** `/api/auth/provider/register/`

**Purpose:** Register a new provider account (doctor, nurse, clinic, etc.).

**Auth Required:** No

**Request:**
```json
{
    "email": "doctor@example.com",
    "password": "secure-password",
    "password2": "secure-password",
    "provider_type": "DOCTOR"
}
```

**Provider Types:** `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY`, `VTC`, `SELLER`

**Response (201):**
```json
{
    "token": "abc123...",
    "user": {
        "id": 2,
        "email": "doctor@example.com",
        "role": "PROVIDER"
    },
    "provider": {
        "status": "PENDING"
    }
}
```

---

## Profile Endpoints

### Get Current User Profile
**GET** `/api/auth/me/`

**Purpose:** Get complete profile information for the authenticated user.

**Auth Required:** Yes

**Allowed Roles:** All authenticated users

**Response (200):**
```json
{
    "id": 1,
    "email": "user@example.com",
    "role": "PROVIDER",
    "account_status": "ACTIVE",
    "is_active": true,
    "email_verified": false,
    "profile_completion_percentage": 45,
    "last_login": "2026-01-26T10:00:00Z",
    "created_at": "2026-01-25T10:00:00Z",
    "provider_profile": {
        "status": "PENDING",
        "provider_type": "DOCTOR",
        "doctor": {
            "first_name": "John",
            "last_name": "Smith",
            "license_number": "DOC123"
        }
    },
    "addresses": [
        {
            "id": 1,
            "street": "123 Main St",
            "city": "Algiers",
            "country": "Algeria"
        }
    ]
}
```

### Update Current User Profile
**PATCH** `/api/auth/me/`

**Purpose:** Update current user's profile (safe fields only).

**Auth Required:** Yes

**Note:** Most fields are read-only. Role-specific profile updates should use separate provider endpoints.

---

## Addresses Endpoints

### List Addresses
**GET** `/api/addresses/`

**Purpose:** Get all addresses for the authenticated user.

**Auth Required:** Yes

**Query Parameters:**
- `is_primary`: Filter by primary status (true/false)
- `address_type`: Filter by type (HOME, WORK, CLINIC, HOSPITAL, OTHER)
- `city`: Filter by city
- `country`: Filter by country

**Response (200):**
```json
{
    "count": 1,
    "results": [
        {
            "id": 1,
            "content_type": 5,
            "content_type_name": "user",
            "object_id": 1,
            "street": "123 Main St",
            "city": "Algiers",
            "state": "Algiers Province",
            "zip_code": "16000",
            "country": "Algeria",
            "latitude": "36.752887",
            "longitude": "3.042048",
            "is_primary": true,
            "address_type": "WORK",
            "notes": "Main office",
            "created_at": "2026-01-25T10:00:00Z",
            "updated_at": "2026-01-25T10:00:00Z"
        }
    ]
}
```

### Create Address
**POST** `/api/addresses/`

**Purpose:** Create a new address for the authenticated user.

**Auth Required:** Yes

**Request:**
```json
{
    "street": "456 New Ave",
    "city": "Oran",
    "state": "Oran Province",
    "zip_code": "31000",
    "country": "Algeria",
    "is_primary": false,
    "address_type": "CLINIC",
    "notes": "Branch office"
}
```

**Note:** `content_type` and `object_id` are automatically set to the current user if not provided.

**Response (201):**
```json
{
    "id": 2,
    "street": "456 New Ave",
    "city": "Oran",
    ...
}
```

### Update Address
**PUT/PATCH** `/api/addresses/{id}/`

**Purpose:** Update an existing address.

**Auth Required:** Yes

### Delete Address
**DELETE** `/api/addresses/{id}/`

**Purpose:** Delete an address.

**Auth Required:** Yes

---

## Services Endpoints

Services are a **global catalog**. Providers do not own services directly. Provider ↔ Service relationships are handled via linking tables (DoctorService, NurseService).

### List Services
**GET** `/api/services/`

**Purpose:** Get all active services.

**Auth Required:** No (public)

**Query Parameters:**
- `is_home_service`: Filter by home service availability (true/false)
- `specialty`: Filter by specialty ID
- `search`: Search in title and description
- `ordering`: Sort by title, price, created_at

**Response (200):**
```json
{
    "count": 10,
    "results": [
        {
            "id": 1,
            "title": "General Consultation",
            "slug": "general-consultation",
            "description": "Basic medical consultation",
            "price": "3000.00",
            "currency": "DZD",
            "currency_display": "Algerian Dinar",
            "duration_minutes": 30,
            "is_home_service": false,
            "is_active": true,
            "specialty": {
                "id": 1,
                "title": "General Medicine"
            }
        }
    ]
}
```

### Create Service
**POST** `/api/services/`

**Purpose:** Create a new service (global catalog).

**Auth Required:** Yes

**Allowed Roles:**
| Role   | Can Create |
|--------|-----------|
| Admin  | ✅ Yes     |
| Doctor | ✅ Yes (auto-attached) |
| Clinic | ✅ Yes     |
| Nurse  | ❌ No      |

**Request:**
```json
{
    "title": "Cardiology Checkup",
    "description": "Complete heart examination",
    "price": "5000.00",
    "currency": "DZD",
    "duration_minutes": 45,
    "is_home_service": false,
    "specialty_id": 2
}
```

**Behavior:**
- **Doctor creates:** Service is created AND automatically linked via DoctorService
- **Clinic creates:** Service is created (global catalog, no automatic attachment)
- **Admin creates:** Service is created (global catalog)

**Response (201):**
```json
{
    "id": 5,
    "title": "Cardiology Checkup",
    "slug": "cardiology-checkup",
    ...
}
```

### Doctor Services (Attach/Detach)

#### List Doctor's Services
**GET** `/api/services/doctor-services/`

**Purpose:** Get services attached to the authenticated doctor.

**Auth Required:** Yes

**Allowed Roles:** Doctor only

**Response (200):**
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "doctor": 1,
            "doctor_name": "John Smith",
            "service": {
                "id": 1,
                "title": "General Consultation"
            },
            "custom_price": null,
            "final_price": "3000.00",
            "is_available": true
        }
    ]
}
```

#### Attach Service to Doctor
**POST** `/api/services/doctor-services/`

**Purpose:** Attach an existing service to the authenticated doctor.

**Auth Required:** Yes

**Allowed Roles:** Doctor only

**Request:**
```json
{
    "service_id": 3,
    "custom_price": "3500.00",
    "is_available": true
}
```

#### Detach Service from Doctor
**DELETE** `/api/services/doctor-services/{id}/`

**Purpose:** Remove a service from the authenticated doctor.

**Auth Required:** Yes

### Nurse Services (Attach/Detach)

#### List Nurse's Services
**GET** `/api/services/nurse-services/`

**Auth Required:** Yes | **Allowed Roles:** Nurse only

#### Attach Service to Nurse
**POST** `/api/services/nurse-services/`

**Auth Required:** Yes | **Allowed Roles:** Nurse only

**Note:** Nurses can attach existing services but **cannot create** new services.

---

## Specialties Endpoints

Specialties are a **global catalog**. Doctor ↔ Specialty relationships are handled via DoctorSpecialty.

### List Specialties
**GET** `/api/specialties/`

**Purpose:** Get all active specialties.

**Auth Required:** No (public)

**Response (200):**
```json
{
    "count": 15,
    "results": [
        {
            "id": 1,
            "title": "Cardiology",
            "title_ar": "أمراض القلب",
            "title_fr": "Cardiologie",
            "slug": "cardiology",
            "description": "Heart and cardiovascular system",
            "medical_domain": "Internal Medicine",
            "is_active": true
        }
    ]
}
```

### Create Specialty
**POST** `/api/specialties/`

**Purpose:** Create a new specialty (global catalog).

**Auth Required:** Yes

**Allowed Roles:**
| Role   | Can Create |
|--------|-----------|
| Admin  | ✅ Yes     |
| Doctor | ✅ Yes (auto-attached) |
| Clinic | ✅ Yes     |
| Nurse  | ❌ No      |

**Request:**
```json
{
    "title": "Neurology",
    "title_ar": "طب الأعصاب",
    "title_fr": "Neurologie",
    "description": "Brain and nervous system",
    "medical_domain": "Internal Medicine"
}
```

**Behavior:**
- **Doctor creates:** Specialty is created AND automatically linked via DoctorSpecialty
- **Clinic creates:** Specialty is created (global catalog, no automatic attachment)

### Doctor Specialties (Attach/Detach)

#### List Doctor's Specialties
**GET** `/api/specialties/doctor-specialties/`

**Auth Required:** Yes | **Allowed Roles:** Doctor only

#### Attach Specialty to Doctor
**POST** `/api/specialties/doctor-specialties/`

**Request:**
```json
{
    "specialty_id": 3,
    "is_primary": true,
    "years_of_experience": 10
}
```

---

## Patient Records Endpoints

This feature allows **any provider** (doctor, nurse, clinic, lab, VTC, etc.) to create patient records for patients who do not have Medilink accounts yet.

### List Patient Records
**GET** `/api/patients/`

**Purpose:** Get patient records accessible to the authenticated user.

**Auth Required:** Yes

**Access Rules:**
- **Patients:** Only see their linked record
- **Providers:** See records they created or have access to
- **Admins:** See all records

**Query Parameters:**
- `gender`: Filter by gender
- `blood_type`: Filter by blood type
- `city`: Filter by city
- `search`: Search by name, phone, email, national ID

**Response (200):**
```json
{
    "count": 5,
    "results": [
        {
            "id": 1,
            "first_name": "Ahmed",
            "last_name": "Benali",
            "full_name": "Ahmed Benali",
            "date_of_birth": "1990-05-15",
            "age": 35,
            "gender": "MALE",
            "phone_number": "+213555123456",
            "is_active": true,
            "is_linked": false,
            "created_at": "2026-01-25T10:00:00Z"
        }
    ]
}
```

### Create Patient Record
**POST** `/api/patients/`

**Purpose:** Create a patient record for a patient without a Medilink account.

**Auth Required:** Yes

**Allowed Roles:** Verified providers only (all types)

**Request:**
```json
{
    "first_name": "Fatima",
    "last_name": "Rahmani",
    "date_of_birth": "1985-03-20",
    "gender": "FEMALE",
    "phone_number": "+213555789012",
    "email": "fatima@email.com",
    "emergency_contact_name": "Mohamed Rahmani",
    "emergency_contact_phone": "+213555111222",
    "blood_type": "A+",
    "known_allergies": "Penicillin",
    "chronic_conditions": "None",
    "current_medications": "None",
    "address": "123 Rue Didouche Mourad",
    "city": "Algiers",
    "state": "Algiers Province",
    "country": "Algeria",
    "notes": "New patient referred by Dr. Smith"
}
```

**Response (201):**
```json
{
    "id": 10,
    "first_name": "Fatima",
    "last_name": "Rahmani",
    "full_name": "Fatima Rahmani",
    "date_of_birth": "1985-03-20",
    "age": 40,
    "gender": "FEMALE",
    "linking_token_masked": "XyZ8h2Kp...9fGn",
    "is_linked": false,
    "created_by_provider_name": "Dr. John Smith",
    ...
}
```

### Get Patient Record
**GET** `/api/patients/{id}/`

**Purpose:** Get full details of a patient record.

**Auth Required:** Yes

### Update Patient Record
**PUT/PATCH** `/api/patients/{id}/`

**Purpose:** Update patient record information.

**Auth Required:** Yes

**Allowed:** Creator or providers with FULL access

### Get Linking Token
**GET** `/api/patients/{id}/token/`

**Purpose:** Get the linking token to give to the patient.

**Auth Required:** Yes

**Allowed:** Creator or providers with FULL access

**Response (200):**
```json
{
    "linking_token": "XyZ8h2KpmN3qR5tU7wY9aB1cD3eF5gH7iJ9kL1mN3oP5qR7sT9uV1wX3y",
    "patient_name": "Fatima Rahmani",
    "token_used": false,
    "is_linked": false
}
```

### Regenerate Linking Token
**POST** `/api/patients/{id}/regenerate-token/`

**Purpose:** Generate a new linking token (if lost).

**Auth Required:** Yes

**Allowed:** Creator only

### Grant Access to Another Provider
**POST** `/api/patients/{id}/grant-access/`

**Purpose:** Grant another provider access to this patient record.

**Auth Required:** Yes

**Allowed:** Creator or providers with FULL access

**Request:**
```json
{
    "provider_id": 5,
    "access_level": "FULL"
}
```

**Access Levels:** `FULL`, `READ_ONLY`, `LIMITED`

### Link Patient Account
**POST** `/api/patients/link-account/`

**Purpose:** Link a patient's Medilink account to their existing patient record.

**Auth Required:** Yes

**Allowed Roles:** Patients only

**Request:**
```json
{
    "linking_token": "XyZ8h2KpmN3qR5tU7wY9aB1cD3eF5gH7iJ9kL1mN3oP5qR7sT9uV1wX3y"
}
```

**Response (200):**
```json
{
    "message": "Account successfully linked to patient record.",
    "patient_record": {
        "id": 10,
        "first_name": "Fatima",
        "last_name": "Rahmani",
        "is_linked": true,
        ...
    }
}
```

### Get My Patient Record
**GET** `/api/patients/me/`

**Purpose:** Get the current patient's linked record.

**Auth Required:** Yes

**Allowed Roles:** Patients only

---

## Error Handling

### Standard Error Response
```json
{
    "error": "Error message describing what went wrong"
}
```

### Validation Error Response
```json
{
    "field_name": ["Error message for this field."],
    "another_field": ["Another error message."]
}
```

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not authenticated) |
| 403 | Forbidden (no permission) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Permissions Summary

### Role Permissions Matrix

| Endpoint | Patient | Doctor | Nurse | Clinic | Admin |
|----------|---------|--------|-------|--------|-------|
| Create Service | ❌ | ✅ Auto-attach | ❌ | ✅ | ✅ |
| Attach Service | ❌ | ✅ | ✅ | ❌ | ✅ |
| Create Specialty | ❌ | ✅ Auto-attach | ❌ | ✅ | ✅ |
| Attach Specialty | ❌ | ✅ | ❌ | ❌ | ✅ |
| Create Patient Record | ❌ | ✅ | ✅ | ✅ | ✅ |
| Link Patient Account | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Changelog

### Version 2.0.0 (2026-01-28)
- Added Patient Records Without Accounts feature
- Updated Services permissions (doctors/clinics can create)
- Updated Specialties permissions (doctors/clinics can create)
- Added auto-attach behavior for doctor-created services/specialties
- Added IsClinic and IsDoctorOrClinic permission classes
- Added comprehensive patient record management endpoints
