# Patient Mobile App - Authentication & Profile API

## Overview

This documentation covers the authentication and profile management APIs for the **Patient Mobile App**. Patients can register, login, manage their profile, view their medical data, and browse healthcare providers.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication Flow](#authentication-flow)
3. [Patient Registration](#patient-registration)
4. [Login](#login)
5. [Logout](#logout)
6. [Profile Management](#profile-management)
   - [Get My Profile](#get-my-profile)
   - [Update My Profile](#update-my-profile)
7. [Managing Addresses](#managing-addresses)
   - [Address Types (Labels)](#address-types-labels)
   - [Primary Address](#primary-address)
   - [List All Addresses](#list-all-addresses)
   - [Create New Address](#create-new-address)
   - [Update Address](#update-address)
   - [Delete Address](#delete-address)
8. [Managing Patient Medical Information](#managing-patient-medical-information)
   - [View My Patient Record](#view-my-patient-record)
   - [Update My Medical Information](#update-my-medical-information)
9. [Viewing Provider Profiles](#viewing-provider-profiles)
10. [Error Handling](#error-handling)
11. [Mobile Integration Examples](#mobile-integration-examples)

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

### Patient Registration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PATIENT REGISTRATION FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌────────────────────────┐ │
│  │   1. Register    │───▶│  2. Receive      │───▶│  3. Access Profile     │ │
│  │   with email,    │    │     Token        │    │     via /auth/me/      │ │
│  │   password,      │    │                  │    │                        │ │
│  │   name, phone    │    │                  │    │                        │ │
│  └──────────────────┘    └──────────────────┘    └────────────────────────┘ │
│           │                                                │                 │
│           ▼                                                ▼                 │
│  ┌──────────────────┐                           ┌────────────────────────┐  │
│  │  4. Add          │                           │  5. Link Patient       │  │
│  │     Addresses    │                           │     Record (optional)  │  │
│  │     /addresses/  │                           │     /patients/link/    │  │
│  └──────────────────┘                           └────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Patient Registration

Register a new patient account with email, password, and basic identity information.

### Endpoint

```
POST /api/auth/patient/register/
```

### Headers

```
Content-Type: application/json
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address (unique) |
| `password` | string | ✅ | Strong password (min 8 chars, mixed case, numbers) |
| `password_confirm` | string | ✅ | Must match password |
| `first_name` | string | ✅ | Patient's first name |
| `last_name` | string | ✅ | Patient's last name |
| `phone_number` | string | ✅ | Patient's phone number (min 8 digits) |

### Example Request

```json
{
    "email": "patient@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "Ahmed",
    "last_name": "Benali",
    "phone_number": "+213555123456"
}
```

### Success Response (201 Created)

```json
{
    "user": {
        "id": 1,
        "email": "patient@example.com",
        "role": "PATIENT",
        "first_name": "Ahmed",
        "last_name": "Benali",
        "full_name": "Ahmed Benali",
        "phone_number": "+213555123456",
        "is_active": true,
        "email_verified": false,
        "profile_completed": false,
        "profile_completion_percentage": 25,
        "created_at": "2026-02-02T10:00:00Z"
    },
    "token": "abc123def456..."
}
```

### Error Responses

**400 Bad Request - Validation Errors**
```json
{
    "email": ["A user with this email already exists."],
    "password": ["This password is too common."],
    "phone_number": ["Phone number is too short."]
}
```

**400 Bad Request - Password Mismatch**
```json
{
    "password_confirm": ["Passwords do not match."]
}
```

---

## Login

Authenticate an existing patient account.

### Endpoint

```
POST /api/auth/login/
```

### Headers

```
Content-Type: application/json
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Registered email address |
| `password` | string | ✅ | Account password |

### Example Request

```json
{
    "email": "patient@example.com",
    "password": "SecurePass123!"
}
```

### Success Response (200 OK)

```json
{
    "user": {
        "id": 1,
        "email": "patient@example.com",
        "role": "PATIENT",
        "first_name": "Ahmed",
        "last_name": "Benali",
        "full_name": "Ahmed Benali",
        "phone_number": "+213555123456",
        "is_active": true,
        "email_verified": true,
        "profile_completed": true,
        "profile_completion_percentage": 85,
        "created_at": "2026-02-02T10:00:00Z"
    },
    "token": "abc123def456..."
}
```

### Error Responses

**401 Unauthorized - Invalid Credentials**
```json
{
    "error": "Invalid email or password."
}
```

**403 Forbidden - Account Inactive**
```json
{
    "error": "Account is inactive."
}
```

**403 Forbidden - Account Suspended**
```json
{
    "error": "Account is suspended. Access denied.",
    "account_status": "SUSPENDED"
}
```

---

## Logout

Invalidate the current authentication token.

### Endpoint

```
POST /api/auth/logout/
```

### Headers

```
Authorization: Token <your_token_here>
```

### Success Response (200 OK)

```json
{
    "message": "Successfully logged out."
}
```

---

## Profile Management

### Get My Profile

Retrieve the complete profile of the authenticated patient, including linked patient record, medical summary, and addresses.

### Endpoint

```
GET /api/auth/me/
```

### Headers

```
Authorization: Token <your_token_here>
```

### Success Response (200 OK)

```json
{
    "id": 1,
    "email": "patient@example.com",
    "role": "PATIENT",
    "role_display": "Patient",
    "first_name": "Ahmed",
    "last_name": "Benali",
    "full_name": "Ahmed Benali",
    "phone_number": "+213555123456",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "is_staff": false,
    "email_verified": true,
    "email_verified_at": "2026-02-02T12:00:00Z",
    "profile_completed": true,
    "profile_completion_percentage": 85,
    "last_login": "2026-02-02T09:00:00Z",
    "last_login_ip": "192.168.1.1",
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-02T09:30:00Z",
    "patient_profile": {
        "is_patient": true,
        "first_name": "Ahmed",
        "last_name": "Benali",
        "full_name": "Ahmed Benali",
        "phone_number": "+213555123456",
        "has_patient_record": true,
        "patient_record": {
            "id": 1,
            "patient_unique_id": "MED-A1B2C3D4",
            "first_name": "Ahmed",
            "last_name": "Benali",
            "full_name": "Ahmed Benali",
            "date_of_birth": "1990-05-15",
            "age": 35,
            "gender": "MALE",
            "phone_number": "+213555123456",
            "blood_type": "A+",
            "known_allergies": "Penicillin",
            "chronic_conditions": "None",
            "emergency_contact_name": "Fatima Benali",
            "emergency_contact_phone": "+213555654321"
        },
        "medical_summary": {
            "medical_records_count": 5,
            "prescriptions_count": 3,
            "appointments_count": 8
        }
    },
    "addresses": [
        {
            "id": 1,
            "street": "123 Rue Didouche Mourad",
            "city": "Algiers",
            "state": "Algiers",
            "zip_code": "16000",
            "country": "Algeria",
            "latitude": "36.7538",
            "longitude": "3.0588",
            "is_primary": true,
            "address_type": "HOME",
            "created_at": "2026-02-01T10:30:00Z"
        }
    ],
    "provider_profile": null,
    "provider_type": null,
    "provider_type_display": null
}
```

### Profile Data Structure

| Field | Description |
|-------|-------------|
| `patient_profile` | Patient-specific data including linked medical record |
| `patient_profile.has_patient_record` | Whether patient has a linked medical record |
| `patient_profile.patient_record` | Full patient medical record (if linked) |
| `patient_profile.medical_summary` | Counts of medical records, prescriptions, appointments |
| `addresses` | Array of patient's saved addresses |
| `profile_completion_percentage` | 0-100 indicating how complete the profile is |

---

### Update My Profile

Update the authenticated patient's profile information.

### Endpoint

```
PATCH /api/auth/me/
```

### Headers

```
Authorization: Token <your_token_here>
Content-Type: application/json
```

### Updatable Fields for Patients

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | Patient's first name |
| `last_name` | string | Patient's last name |
| `phone_number` | string | Patient's phone number |

### Example Request

```json
{
    "first_name": "Ahmed",
    "last_name": "Benali-Merah",
    "phone_number": "+213666123456"
}
```

### Success Response (200 OK)

Returns the full updated profile (same structure as GET /api/auth/me/).

### Read-Only Fields (Cannot be changed via API)

- `email` - Use dedicated email change flow
- `role` - Fixed at registration
- `account_status` - Managed by admins
- `email_verified` - Set via email verification flow

---

## Managing Addresses

> **📍 IMPORTANT: Multi-Address Support**
> 
> Patients can add **multiple addresses** to their profile. Each address can have a different label (type) and one address can be marked as the **primary address** which will be used as the default for home visits, deliveries, and appointment location suggestions.

### Address Types (Labels)

| Type | Description | Use Case |
|------|-------------|----------|
| `HOME` | Primary residence | Default for home visits |
| `WORK` | Workplace address | For appointments during work hours |
| `CLINIC` | Medical facility | For regular checkups |
| `HOSPITAL` | Hospital address | For emergency contacts |
| `OTHER` | Any other address | Custom locations |

### Primary Address

- **Only one address can be primary** at a time
- Set `is_primary: true` when creating or updating an address
- When you set a new address as primary, the previous primary is automatically unset
- Primary address is used as the default for home service appointments

---

### List All Addresses

```
GET /api/addresses/
```

**Response:**
```json
[
    {
        "id": 1,
        "street": "123 Rue Didouche Mourad",
        "city": "Algiers",
        "state": "Algiers",
        "zip_code": "16000",
        "country": "Algeria",
        "latitude": 36.7538,
        "longitude": 3.0588,
        "is_primary": true,
        "address_type": "HOME",
        "notes": "Apartment 4B, near the post office"
    },
    {
        "id": 2,
        "street": "45 Boulevard Mohamed V",
        "city": "Algiers",
        "state": "Algiers",
        "zip_code": "16001",
        "country": "Algeria",
        "latitude": 36.7600,
        "longitude": 3.0550,
        "is_primary": false,
        "address_type": "WORK",
        "notes": "Office building, 5th floor"
    }
]
```

---

### Create New Address

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
    "address_type": "HOME",
    "notes": "Apartment 4B, near the post office"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `street` | string | ✅ | Street address with number |
| `city` | string | ✅ | City name |
| `state` | string | ❌ | State/Province/Wilaya |
| `zip_code` | string | ❌ | Postal/ZIP code |
| `country` | string | ❌ | Country (defaults to Algeria) |
| `latitude` | decimal | ❌ | GPS latitude for map |
| `longitude` | decimal | ❌ | GPS longitude for map |
| `is_primary` | boolean | ❌ | Set as primary address (default: false) |
| `address_type` | string | ❌ | Label: HOME, WORK, CLINIC, HOSPITAL, OTHER (default: HOME) |
| `notes` | string | ❌ | Additional notes/instructions |

**Success Response (201 Created):**
```json
{
    "id": 3,
    "street": "123 Rue Didouche Mourad",
    "city": "Algiers",
    "state": "Algiers",
    "zip_code": "16000",
    "country": "Algeria",
    "latitude": "36.7538",
    "longitude": "3.0588",
    "is_primary": true,
    "address_type": "HOME",
    "notes": "Apartment 4B, near the post office"
}
```

---

### Update Address

```
PUT /api/addresses/{id}/     # Full update
PATCH /api/addresses/{id}/   # Partial update
```

**Example - Set as Primary:**
```json
{
    "is_primary": true
}
```

**Example - Change Label/Type:**
```json
{
    "address_type": "WORK"
}
```

---

### Delete Address

```
DELETE /api/addresses/{id}/
```

**Success Response (204 No Content)**

> ⚠️ If you delete the primary address, you should set another address as primary.

---

## Managing Patient Medical Information

> **🏥 IMPORTANT: Emergency Contacts & Allergies**
> 
> Patients can add and manage their own medical information including emergency contacts, allergies, blood type, chronic conditions, and current medications. This information is crucial for healthcare providers during appointments and emergencies.
>
> **Both patients AND providers can update this information.** When an appointment is confirmed, the provider will have access to view and update your medical profile.

### View My Patient Record

```
GET /api/patients/me/
```

**Response:**
```json
{
    "id": 1,
    "patient_unique_id": "PAT-2024-ABC123",
    "first_name": "Ahmed",
    "last_name": "Benali",
    "full_name": "Ahmed Benali",
    "date_of_birth": "1990-05-15",
    "age": 34,
    "gender": "M",
    "phone_number": "+213555123456",
    "email": "patient@example.com",
    "emergency_contact_name": "Fatima Benali",
    "emergency_contact_phone": "+213555987654",
    "blood_type": "A+",
    "known_allergies": "Penicillin, Peanuts",
    "chronic_conditions": "Hypertension",
    "current_medications": "Lisinopril 10mg daily",
    "address": "123 Rue Didouche Mourad",
    "city": "Algiers",
    "state": "Algiers",
    "country": "Algeria",
    "notes": "",
    "is_active": true,
    "is_linked": true,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-02-01T15:30:00Z"
}
```

---

### Update My Medical Information

```
PATCH /api/patients/me/
```

> **Note:** This endpoint is used via the patient record. Use `/api/auth/me/` for basic profile updates and this for medical information.

**Example - Update Emergency Contact:**
```json
{
    "emergency_contact_name": "Fatima Benali",
    "emergency_contact_phone": "+213555987654"
}
```

**Example - Update Allergies:**
```json
{
    "known_allergies": "Penicillin, Peanuts, Shellfish"
}
```

**Example - Update Full Medical Info:**
```json
{
    "emergency_contact_name": "Fatima Benali",
    "emergency_contact_phone": "+213555987654",
    "blood_type": "A+",
    "known_allergies": "Penicillin, Peanuts",
    "chronic_conditions": "Hypertension, Diabetes Type 2",
    "current_medications": "Lisinopril 10mg daily, Metformin 500mg twice daily"
}
```

### Medical Information Fields

| Field | Type | Description |
|-------|------|-------------|
| `emergency_contact_name` | string | Name of emergency contact person |
| `emergency_contact_phone` | string | Phone number for emergencies |
| `blood_type` | string | Blood type: A+, A-, B+, B-, AB+, AB-, O+, O- |
| `known_allergies` | text | List of known allergies (free text) |
| `chronic_conditions` | text | Any chronic medical conditions |
| `current_medications` | text | Current medications being taken |

> **💡 Tip:** Keep this information up-to-date. It helps providers make informed decisions about your care and can be critical in emergencies.

---

## Viewing Provider Profiles

Patients can browse and search healthcare providers (doctors, nurses, clinics, etc.).

### List All Providers

```
GET /api/provider/public/
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `provider_type` | string | Filter by type: `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY` |
| `search` | string | Search by name or specialty |
| `is_available` | boolean | Filter by availability |
| `is_home_service` | boolean | Filter by home service availability |
| `specialty` | string | Filter by specialty slug (doctors only) |
| `city` | string | Filter by city |
| `ordering` | string | Sort by field (e.g., `-created_at`) |

### Example Request

```
GET /api/provider/public/?provider_type=DOCTOR&is_available=true&city=Algiers
```

### Response

```json
{
    "count": 25,
    "next": "https://api.example.com/api/provider/public/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "provider_type": "DOCTOR",
            "provider_type_display": "Doctor",
            "first_name": "Mohamed",
            "last_name": "Kaddour",
            "full_name": "Dr. Mohamed Kaddour",
            "profile_image": "https://api.example.com/media/doctors/profile.jpg",
            "specialties": [
                {
                    "id": 1,
                    "name": "Cardiology",
                    "name_ar": "أمراض القلب",
                    "slug": "cardiology"
                }
            ],
            "years_of_experience": 15,
            "is_available": true,
            "is_home_service_available": true,
            "consultation_price": "3000.00",
            "currency": "DZD",
            "biography": "Experienced cardiologist with 15 years of practice...",
            "addresses": [
                {
                    "city": "Algiers",
                    "state": "Algiers"
                }
            ]
        }
    ]
}
```

### List Only Doctors

```
GET /api/provider/public/doctors/
```

### List Only Nurses

```
GET /api/provider/public/nurses/
```

### List Only Clinics

```
GET /api/provider/public/clinics/
```

### Get Provider Details

```
GET /api/provider/public/{id}/
```

Returns detailed provider information including:
- Full profile information
- All specialties
- Services offered
- Addresses
- Working hours
- Reviews (if available)

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Validation errors |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Access denied |
| 404 | Not Found |
| 500 | Server Error |

### Common Error Response Format

```json
{
    "error": "Error message description",
    "field_name": ["Specific field error"]
}
```

---

## Mobile Integration Examples

### Flutter/Dart Example

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class AuthService {
  static const String baseUrl = 'https://dzmedilink.duckdns.org/';
  String? _token;

  // Patient Registration
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String phoneNumber,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/patient/register/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'password_confirm': password,
        'first_name': firstName,
        'last_name': lastName,
        'phone_number': phoneNumber,
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body);
      _token = data['token'];
      return data;
    } else {
      throw Exception(jsonDecode(response.body));
    }
  }

  // Login
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _token = data['token'];
      return data;
    } else {
      throw Exception(jsonDecode(response.body));
    }
  }

  // Get Profile
  Future<Map<String, dynamic>> getProfile() async {
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $_token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(jsonDecode(response.body));
    }
  }

  // Update Profile
  Future<Map<String, dynamic>> updateProfile({
    String? firstName,
    String? lastName,
    String? phoneNumber,
  }) async {
    final body = <String, dynamic>{};
    if (firstName != null) body['first_name'] = firstName;
    if (lastName != null) body['last_name'] = lastName;
    if (phoneNumber != null) body['phone_number'] = phoneNumber;

    final response = await http.patch(
      Uri.parse('$baseUrl/auth/me/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $_token',
      },
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(jsonDecode(response.body));
    }
  }

  // Browse Doctors
  Future<Map<String, dynamic>> getDoctors({
    String? city,
    String? specialty,
    bool? isAvailable,
  }) async {
    final queryParams = <String, String>{};
    if (city != null) queryParams['city'] = city;
    if (specialty != null) queryParams['specialty'] = specialty;
    if (isAvailable != null) queryParams['is_available'] = isAvailable.toString();

    final uri = Uri.parse('$baseUrl/provider/public/doctors/')
        .replace(queryParameters: queryParams);

    final response = await http.get(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $_token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(jsonDecode(response.body));
    }
  }
}
```

### React Native Example

```javascript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://dzmedilink.duckdns.org/';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Auth Service
export const authService = {
  // Patient Registration
  async register({ email, password, firstName, lastName, phoneNumber }) {
    const response = await api.post('/auth/patient/register/', {
      email,
      password,
      password_confirm: password,
      first_name: firstName,
      last_name: lastName,
      phone_number: phoneNumber,
    });
    await AsyncStorage.setItem('authToken', response.data.token);
    return response.data;
  },

  // Login
  async login({ email, password }) {
    const response = await api.post('/auth/login/', { email, password });
    await AsyncStorage.setItem('authToken', response.data.token);
    return response.data;
  },

  // Logout
  async logout() {
    await api.post('/auth/logout/');
    await AsyncStorage.removeItem('authToken');
  },

  // Get Profile
  async getProfile() {
    const response = await api.get('/auth/me/');
    return response.data;
  },

  // Update Profile
  async updateProfile({ firstName, lastName, phoneNumber }) {
    const response = await api.patch('/auth/me/', {
      first_name: firstName,
      last_name: lastName,
      phone_number: phoneNumber,
    });
    return response.data;
  },
};

// Provider Service
export const providerService = {
  // Get Doctors
  async getDoctors({ city, specialty, isAvailable } = {}) {
    const params = {};
    if (city) params.city = city;
    if (specialty) params.specialty = specialty;
    if (isAvailable !== undefined) params.is_available = isAvailable;

    const response = await api.get('/provider/public/doctors/', { params });
    return response.data;
  },

  // Get Provider Details
  async getProviderDetails(providerId) {
    const response = await api.get(`/provider/public/${providerId}/`);
    return response.data;
  },
};
```

---

## Related Endpoints

For complete patient functionality, also see:

| Endpoint | Documentation |
|----------|---------------|
| `/api/patients/me/` | View linked patient record |
| `/api/patients/my-records/` | View medical records |
| `/api/prescriptions/my-prescriptions/` | View prescriptions |
| `/api/appointments/appointments/` | Manage appointments |

---

## Support

For API issues or questions, contact:
- Email: api-support@medilink.com
- Documentation: https://docs.medilink.com
