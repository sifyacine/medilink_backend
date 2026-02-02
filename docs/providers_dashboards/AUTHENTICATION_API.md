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

### Doctor Profile Response

```json
{
    "id": 15,
    "email": "doctor@example.com",
    "role": "PROVIDER",
    "role_display": "Provider",
    "first_name": "Mohamed",
    "last_name": "Kaddour",
    "full_name": "Mohamed Kaddour",
    "phone_number": "+213555123456",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "email_verified": true,
    "profile_completed": true,
    "profile_completion_percentage": 90,
    "last_login": "2026-02-02T09:00:00Z",
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-02T09:30:00Z",
    "provider_profile": {
        "id": 10,
        "status": "APPROVED",
        "status_display": "Approved",
        "provider_type": "DOCTOR",
        "provider_type_display": "Doctor",
        "refusal_reason": null,
        "verified_at": "2026-02-02T14:00:00Z",
        "doctor": {
            "id": 5,
            "first_name": "Mohamed",
            "last_name": "Kaddour",
            "full_name": "Dr. Mohamed Kaddour",
            "gender": "MALE",
            "phone_number": "+213555123456",
            "license_number": "MED-2024-12345",
            "years_of_experience": 15,
            "biography": "Board-certified cardiologist with 15 years of experience...",
            "profile_image": "https://api.example.com/media/doctors/mohamed.jpg",
            "is_available": true,
            "is_home_service_available": false,
            "consultation_price": "3000.00",
            "currency": "DZD",
            "degree_document": "https://api.example.com/media/docs/degree.pdf",
            "specialties": [
                {
                    "id": 1,
                    "name": "Cardiology",
                    "name_ar": "أمراض القلب",
                    "slug": "cardiology"
                }
            ],
            "created_at": "2026-02-01T10:00:00Z"
        }
    },
    "addresses": [
        {
            "id": 10,
            "street": "123 Rue Didouche Mourad",
            "city": "Algiers",
            "state": "Algiers",
            "zip_code": "16000",
            "country": "Algeria",
            "latitude": "36.7538",
            "longitude": "3.0588",
            "is_primary": true,
            "address_type": "CLINIC",
            "notes": "Main practice",
            "created_at": "2026-02-01T10:30:00Z"
        }
    ],
    "provider_type": "DOCTOR",
    "provider_type_display": "Doctor",
    "subtype": "DOCTOR",
    "subtype_display": "Doctor",
    "patient_profile": null
}
```

### Clinic Profile Response

```json
{
    "id": 20,
    "email": "clinic@example.com",
    "role": "PROVIDER",
    "role_display": "Provider",
    "provider_profile": {
        "id": 15,
        "status": "APPROVED",
        "provider_type": "CLINIC",
        "provider_type_display": "Clinic",
        "clinic": {
            "id": 3,
            "clinic_name": "Clinique El Shifa",
            "phone_number": "+213555123456",
            "license_number": "CLN-2024-12345",
            "description": "Full-service medical clinic offering...",
            "logo": "https://api.example.com/media/clinics/logo.jpg",
            "is_available": true,
            "opening_hours": "08:00-18:00",
            "services": ["General Medicine", "Pediatrics", "Cardiology"],
            "created_at": "2026-02-01T10:00:00Z"
        }
    },
    "addresses": [...],
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
