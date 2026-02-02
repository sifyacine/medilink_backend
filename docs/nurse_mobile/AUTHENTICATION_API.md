# Nurse Mobile App - Authentication & Profile API

## Overview

This documentation covers the authentication and profile management APIs for the **Nurse Mobile App**. Nurses are healthcare providers who must register with professional documents and get approved before accessing the platform.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication Flow](#authentication-flow)
3. [Nurse Registration](#nurse-registration)
4. [Required Documents](#required-documents)
5. [Login](#login)
6. [Account Status Check](#account-status-check)
7. [Profile Management](#profile-management)
   - [Get My Profile](#get-my-profile)
   - [Update My Profile](#update-my-profile)
8. [Managing Addresses](#managing-addresses)
9. [Provider Status](#provider-status)
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

### Nurse Registration & Approval Flow

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                         NURSE REGISTRATION FLOW                                    │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────────────────────────┐ │
│  │  1. Register   │───▶│  2. Upload     │───▶│  3. Account Status: PENDING      │ │
│  │  with email,   │    │  Required      │    │     Wait for admin approval      │ │
│  │  password,     │    │  Documents     │    │                                  │ │
│  │  identity      │    │                │    │                                  │ │
│  └────────────────┘    └────────────────┘    └──────────────────────────────────┘ │
│                                                          │                         │
│                                                          ▼                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐   │
│  │                         ADMIN REVIEW                                        │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────────────────┐│   │
│  │  │  APPROVED   │    │  REFUSED    │    │  SUSPENDED                       ││   │
│  │  │  ✓ Can      │    │  ✗ Cannot   │    │  ✗ Temporarily                   ││   │
│  │  │    login    │    │    login    │    │    cannot login                  ││   │
│  │  └─────────────┘    └─────────────┘    └──────────────────────────────────┘│   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### Provider Status States

| Status | Description | Can Login |
|--------|-------------|-----------|
| `PENDING` | Documents under review | ❌ No |
| `APPROVED` | Verified and active | ✅ Yes |
| `REFUSED` | Registration denied | ❌ No |
| `SUSPENDED` | Temporarily disabled | ❌ No |

---

## Nurse Registration

Register a new nurse provider account with professional documents.

### Endpoint

```
POST /api/auth/provider/register/
```

### Headers

```
Content-Type: multipart/form-data
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | Valid email address (unique) |
| `password` | string | ✅ | Strong password (min 8 chars) |
| `password_confirm` | string | ✅ | Must match password |
| `provider_type` | string | ✅ | Must be `NURSE` |
| `first_name` | string | ✅ | Nurse's first name |
| `last_name` | string | ✅ | Nurse's last name |
| `phone_number` | string | ✅ | Contact phone number |
| `license_number` | string | ✅ | Professional license number |
| `degree_document` | file | ✅ | Nursing degree document (PDF/Image) |
| `entrepreneur_card_front` | file | ✅ | Front of entrepreneur card |
| `entrepreneur_card_back` | file | ✅ | Back of entrepreneur card |

### Example Request (multipart/form-data)

```
POST /api/auth/provider/register/
Content-Type: multipart/form-data

email: nurse@example.com
password: SecurePass123!
password_confirm: SecurePass123!
provider_type: NURSE
first_name: Amina
last_name: Boudiaf
phone_number: +213555123456
license_number: NUR-2024-12345
degree_document: [FILE: nursing_diploma.pdf]
entrepreneur_card_front: [FILE: carte_front.jpg]
entrepreneur_card_back: [FILE: carte_back.jpg]
```

### Success Response (201 Created)

```json
{
    "user": {
        "id": 10,
        "email": "nurse@example.com",
        "role": "PROVIDER",
        "first_name": "Amina",
        "last_name": "Boudiaf",
        "full_name": "Amina Boudiaf",
        "phone_number": "+213555123456",
        "is_active": true,
        "email_verified": false,
        "profile_completed": false,
        "profile_completion_percentage": 60,
        "created_at": "2026-02-02T10:00:00Z"
    },
    "provider": {
        "id": 5,
        "status": "PENDING",
        "status_display": "Pending Verification",
        "provider_type": "NURSE",
        "provider_type_display": "Nurse",
        "refusal_reason": null,
        "verified_at": null,
        "created_at": "2026-02-02T10:00:00Z"
    },
    "token": "abc123def456..."
}
```

### Error Responses

**400 Bad Request - Missing Required Documents**
```json
{
    "degree_document": ["This field is required for nurse signup."],
    "entrepreneur_card_front": ["This field is required for nurse signup."],
    "entrepreneur_card_back": ["This field is required for nurse signup."]
}
```

**400 Bad Request - Email Already Exists**
```json
{
    "email": ["A user with this email already exists."]
}
```

---

## Required Documents

### For Nurse Registration

| Document | Format | Description |
|----------|--------|-------------|
| `degree_document` | PDF, JPG, PNG | Nursing diploma or degree certificate |
| `entrepreneur_card_front` | JPG, PNG | Front side of entrepreneur/business card |
| `entrepreneur_card_back` | JPG, PNG | Back side of entrepreneur/business card |

### Document Requirements

- Maximum file size: 10MB per file
- Supported formats: PDF, JPG, JPEG, PNG
- Documents must be clear and readable
- All documents will be verified by the medical board

---

## Login

Authenticate an existing nurse account.

### Endpoint

```
POST /api/auth/login/
```

### Headers

```
Content-Type: application/json
```

### Request Body

```json
{
    "email": "nurse@example.com",
    "password": "SecurePass123!"
}
```

### Success Response (200 OK) - Approved Nurse

```json
{
    "user": {
        "id": 10,
        "email": "nurse@example.com",
        "role": "PROVIDER",
        "first_name": "Amina",
        "last_name": "Boudiaf",
        "full_name": "Amina Boudiaf",
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
    "refusal_reason": "Documents provided are not valid. Please submit clear copies of your nursing degree.",
    "message": "Your account registration was refused for the following reason: Documents provided are not valid. Please submit clear copies of your nursing degree. Please contact support or re-upload your documents."
}
```

**403 Forbidden - Account Suspended**
```json
{
    "error": "Account suspended.",
    "provider_status": "SUSPENDED",
    "message": "Your account has been temporarily suspended for administrative reasons. Please contact support."
}
```

---

## Account Status Check

Check the status of a provider account without logging in (useful for pending accounts).

### Endpoint

```
GET /api/auth/status/?email=nurse@example.com
```

### Success Response (200 OK)

```json
{
    "email": "nurse@example.com",
    "role": "PROVIDER",
    "account_status": "ACTIVE",
    "provider_status": "PENDING",
    "message": "Your account is pending verification. Please wait for admin approval."
}
```

---

## Profile Management

### Get My Profile

Retrieve the complete profile of the authenticated nurse.

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
    "id": 10,
    "email": "nurse@example.com",
    "role": "PROVIDER",
    "role_display": "Provider",
    "first_name": "Amina",
    "last_name": "Boudiaf",
    "full_name": "Amina Boudiaf",
    "phone_number": "+213555123456",
    "account_status": "ACTIVE",
    "account_status_display": "Active",
    "is_active": true,
    "is_staff": false,
    "email_verified": true,
    "email_verified_at": "2026-02-02T12:00:00Z",
    "profile_completed": true,
    "profile_completion_percentage": 90,
    "last_login": "2026-02-02T09:00:00Z",
    "last_login_ip": "192.168.1.1",
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-02T09:30:00Z",
    "provider_profile": {
        "id": 5,
        "status": "APPROVED",
        "status_display": "Approved",
        "provider_type": "NURSE",
        "provider_type_display": "Nurse",
        "refusal_reason": null,
        "verified_at": "2026-02-02T14:00:00Z",
        "nurse": {
            "id": 3,
            "first_name": "Amina",
            "last_name": "Boudiaf",
            "full_name": "Amina Boudiaf",
            "gender": "FEMALE",
            "phone_number": "+213555123456",
            "license_number": "NUR-2024-12345",
            "years_of_experience": 5,
            "biography": "Experienced nurse specializing in home care...",
            "profile_image": "https://api.example.com/media/nurses/amina.jpg",
            "is_available": true,
            "is_home_service_available": true,
            "degree_document": "https://api.example.com/media/docs/diploma.pdf",
            "entrepreneur_card_front": "https://api.example.com/media/docs/card_front.jpg",
            "entrepreneur_card_back": "https://api.example.com/media/docs/card_back.jpg",
            "created_at": "2026-02-01T10:00:00Z"
        }
    },
    "addresses": [
        {
            "id": 5,
            "street": "45 Boulevard Mohamed V",
            "city": "Oran",
            "state": "Oran",
            "zip_code": "31000",
            "country": "Algeria",
            "latitude": "35.6969",
            "longitude": "-0.6331",
            "is_primary": true,
            "address_type": "WORK",
            "created_at": "2026-02-01T10:30:00Z"
        }
    ],
    "provider_type": "NURSE",
    "provider_type_display": "Nurse",
    "subtype": "NURSE",
    "subtype_display": "Nurse",
    "patient_profile": null
}
```

### Provider Profile Structure

| Field | Description |
|-------|-------------|
| `provider_profile.status` | Provider verification status |
| `provider_profile.nurse` | Nurse-specific profile data |
| `provider_profile.nurse.is_available` | Whether accepting new requests |
| `provider_profile.nurse.is_home_service_available` | Whether offering home visits |
| `addresses` | Array of work locations |

---

### Update My Profile

Update the authenticated nurse's profile information.

### Endpoint

```
PATCH /api/auth/me/
```

### Headers

```
Authorization: Token <your_token_here>
Content-Type: application/json
```

### Updatable Fields for Nurses

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | Nurse's first name |
| `last_name` | string | Nurse's last name |
| `phone_number` | string | Contact phone number |
| `gender` | string | `MALE`, `FEMALE`, `OTHER` |
| `biography` | string | Professional biography |
| `years_of_experience` | integer | Years of nursing experience |
| `is_available` | boolean | Currently accepting requests |
| `is_home_service_available` | boolean | Offering home visits |
| `profile_image` | file | Profile photo (multipart/form-data) |

### Example Request - Update Availability

```json
{
    "is_available": true,
    "is_home_service_available": true,
    "biography": "Experienced nurse with 5 years in home care, specializing in elderly care and post-operative recovery."
}
```

### Example Request - Update Profile Image

```
PATCH /api/auth/me/
Content-Type: multipart/form-data
Authorization: Token abc123...

profile_image: [FILE: new_profile.jpg]
```

### Success Response (200 OK)

Returns the full updated profile (same structure as GET /api/auth/me/).

### Read-Only Fields (Cannot be changed via API)

These fields require admin intervention:

| Field | Reason |
|-------|--------|
| `email` | Use dedicated email change flow |
| `license_number` | Verified by medical board |
| `degree_document` | Contact support to update |
| `entrepreneur_card_front` | Contact support to update |
| `entrepreneur_card_back` | Contact support to update |

**Error when trying to update read-only fields:**
```json
{
    "license_number": ["This field cannot be changed from the app. Please contact support."],
    "degree_document": ["This field cannot be changed from the app. Please contact support."]
}
```

---

## Managing Addresses

Nurses can manage their work addresses for service locations.

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
    "street": "45 Boulevard Mohamed V",
    "city": "Oran",
    "state": "Oran",
    "zip_code": "31000",
    "country": "Algeria",
    "latitude": 35.6969,
    "longitude": -0.6331,
    "is_primary": true,
    "address_type": "WORK",
    "notes": "Main practice location"
}
```

**Address Types for Nurses:**
- `WORK` - Primary work location
- `CLINIC` - Clinic location (if working at a clinic)
- `OTHER` - Other service location

---

## Provider Status

### Check Provider Status

```
GET /api/provider/status/
```

### Headers

```
Authorization: Token <your_token_here>
```

### Response

```json
{
    "id": 5,
    "status": "APPROVED",
    "status_display": "Approved",
    "provider_type": "NURSE",
    "provider_type_display": "Nurse",
    "refusal_reason": null,
    "verified_at": "2026-02-02T14:00:00Z",
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-02T14:00:00Z"
}
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
| 403 | Forbidden - Access denied or pending approval |
| 404 | Not Found |
| 500 | Server Error |

### Provider-Specific Errors

| Error | provider_status | Action |
|-------|-----------------|--------|
| Pending verification | `PENDING` | Wait for admin approval |
| Registration refused | `REFUSED` | Contact support or re-apply |
| Account suspended | `SUSPENDED` | Contact support |

---

## Mobile Integration Examples

### Flutter/Dart Example

```dart
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'dart:convert';
import 'dart:io';

class NurseAuthService {
  static const String baseUrl = 'https://dzmedilink.duckdns.org/';
  String? _token;

  // Nurse Registration with Documents
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String phoneNumber,
    required String licenseNumber,
    required File degreeDocument,
    required File entrepreneurCardFront,
    required File entrepreneurCardBack,
  }) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$baseUrl/auth/provider/register/'),
    );

    // Add text fields
    request.fields['email'] = email;
    request.fields['password'] = password;
    request.fields['password_confirm'] = password;
    request.fields['provider_type'] = 'NURSE';
    request.fields['first_name'] = firstName;
    request.fields['last_name'] = lastName;
    request.fields['phone_number'] = phoneNumber;
    request.fields['license_number'] = licenseNumber;

    // Add files
    request.files.add(await http.MultipartFile.fromPath(
      'degree_document',
      degreeDocument.path,
    ));
    request.files.add(await http.MultipartFile.fromPath(
      'entrepreneur_card_front',
      entrepreneurCardFront.path,
    ));
    request.files.add(await http.MultipartFile.fromPath(
      'entrepreneur_card_back',
      entrepreneurCardBack.path,
    ));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

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

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      _token = data['token'];
      return data;
    } else if (response.statusCode == 403) {
      // Handle provider status errors
      if (data['provider_status'] == 'PENDING') {
        throw PendingApprovalException(data['message']);
      } else if (data['provider_status'] == 'REFUSED') {
        throw RegistrationRefusedException(
          data['message'],
          data['refusal_reason'],
        );
      } else if (data['provider_status'] == 'SUSPENDED') {
        throw AccountSuspendedException(data['message']);
      }
      throw Exception(data['error']);
    } else {
      throw Exception(data['error']);
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
    String? biography,
    int? yearsOfExperience,
    bool? isAvailable,
    bool? isHomeServiceAvailable,
  }) async {
    final body = <String, dynamic>{};
    if (firstName != null) body['first_name'] = firstName;
    if (lastName != null) body['last_name'] = lastName;
    if (phoneNumber != null) body['phone_number'] = phoneNumber;
    if (biography != null) body['biography'] = biography;
    if (yearsOfExperience != null) body['years_of_experience'] = yearsOfExperience;
    if (isAvailable != null) body['is_available'] = isAvailable;
    if (isHomeServiceAvailable != null) body['is_home_service_available'] = isHomeServiceAvailable;

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

  // Update Profile Image
  Future<Map<String, dynamic>> updateProfileImage(File imageFile) async {
    var request = http.MultipartRequest(
      'PATCH',
      Uri.parse('$baseUrl/auth/me/'),
    );
    request.headers['Authorization'] = 'Token $_token';
    request.files.add(await http.MultipartFile.fromPath(
      'profile_image',
      imageFile.path,
    ));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(jsonDecode(response.body));
    }
  }

  // Check Provider Status
  Future<Map<String, dynamic>> getProviderStatus() async {
    final response = await http.get(
      Uri.parse('$baseUrl/provider/status/'),
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

// Custom Exceptions
class PendingApprovalException implements Exception {
  final String message;
  PendingApprovalException(this.message);
}

class RegistrationRefusedException implements Exception {
  final String message;
  final String? reason;
  RegistrationRefusedException(this.message, this.reason);
}

class AccountSuspendedException implements Exception {
  final String message;
  AccountSuspendedException(this.message);
}
```

### React Native Example

```javascript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://dzmedilink.duckdns.org/';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to requests
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Handle provider status errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 403) {
      const data = error.response.data;
      if (data.provider_status === 'PENDING') {
        throw { type: 'PENDING_APPROVAL', message: data.message };
      } else if (data.provider_status === 'REFUSED') {
        throw { type: 'REFUSED', message: data.message, reason: data.refusal_reason };
      } else if (data.provider_status === 'SUSPENDED') {
        throw { type: 'SUSPENDED', message: data.message };
      }
    }
    throw error;
  }
);

export const nurseAuthService = {
  // Nurse Registration
  async register({
    email,
    password,
    firstName,
    lastName,
    phoneNumber,
    licenseNumber,
    degreeDocument,
    entrepreneurCardFront,
    entrepreneurCardBack,
  }) {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('password', password);
    formData.append('password_confirm', password);
    formData.append('provider_type', 'NURSE');
    formData.append('first_name', firstName);
    formData.append('last_name', lastName);
    formData.append('phone_number', phoneNumber);
    formData.append('license_number', licenseNumber);
    formData.append('degree_document', {
      uri: degreeDocument.uri,
      type: degreeDocument.type,
      name: degreeDocument.name,
    });
    formData.append('entrepreneur_card_front', {
      uri: entrepreneurCardFront.uri,
      type: entrepreneurCardFront.type,
      name: entrepreneurCardFront.name,
    });
    formData.append('entrepreneur_card_back', {
      uri: entrepreneurCardBack.uri,
      type: entrepreneurCardBack.type,
      name: entrepreneurCardBack.name,
    });

    const response = await api.post('/auth/provider/register/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
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
  async updateProfile(data) {
    const response = await api.patch('/auth/me/', data);
    return response.data;
  },

  // Update Profile Image
  async updateProfileImage(imageFile) {
    const formData = new FormData();
    formData.append('profile_image', {
      uri: imageFile.uri,
      type: imageFile.type || 'image/jpeg',
      name: imageFile.name || 'profile.jpg',
    });

    const response = await api.patch('/auth/me/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Get Provider Status
  async getProviderStatus() {
    const response = await api.get('/provider/status/');
    return response.data;
  },
};
```

---

## Related Endpoints

For complete nurse functionality, also see:

| Endpoint | Documentation |
|----------|---------------|
| `/api/nurse-requests/` | Manage service requests |
| `/api/appointments/appointments/` | Manage appointments |
| `/api/provider/profile/` | Detailed provider profile |
| `/api/services/` | Manage offered services |

---

## Support

For API issues or questions, contact:
- Email: api-support@medilink.com
- Documentation: https://docs.medilink.com
