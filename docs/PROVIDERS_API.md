# Providers API Documentation

## Overview

This document describes the API endpoints for browsing and retrieving healthcare providers (doctors, nurses, clinics, and laboratories) in the MediLink mobile application.

**Base URL:** `https://dzmedilink.duckdns.org/api/`

## Provider Types

| Type | Value | Description |
|------|-------|-------------|
| Doctor | `DOCTOR` | Individual medical doctors with specialties |
| Nurse | `NURSE` | Individual nursing professionals |
| Clinic | `CLINIC` | Healthcare facilities/clinics |
| Laboratory | `LABORATORY` | Diagnostic laboratories |
| VTC | `VTC` | Virtual Telehealth Centers |
| Seller | `SELLER` | Medical equipment/supplies sellers |

---

## 📖 Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/provider/public/` | List all approved providers | ❌ No |
| `GET` | `/api/provider/public/{id}/` | Get provider details | ❌ No |
| `GET` | `/api/provider/public/doctors/` | List only doctors | ❌ No |
| `GET` | `/api/provider/public/nurses/` | List only nurses | ❌ No |
| `GET` | `/api/provider/public/clinics/` | List only clinics | ❌ No |
| `GET` | `/api/provider/public/laboratories/` | List only laboratories | ❌ No |
| `GET` | `/api/provider/public/provider_types/` | Get provider type counts | ❌ No |

---

## 🔍 List All Providers

### Endpoint

```
GET /api/provider/public/
```

### Description

Retrieves a paginated list of all approved providers. Supports filtering, searching, and sorting.

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `provider_type` | string | Filter by provider type | `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY` |
| `search` | string | Search by name | `?search=Ahmed` |
| `is_available` | boolean | Filter by availability | `?is_available=true` |
| `is_home_service` | boolean | Filter by home service availability | `?is_home_service=true` |
| `specialty` | string | Filter by specialty slug (doctors only) | `?specialty=cardiology` |
| `city` | string | Filter by city | `?city=Algiers` |
| `ordering` | string | Sort results | `?ordering=-created_at` |
| `page` | integer | Page number for pagination | `?page=1` |

### Request Example

```bash
# Get all available doctors who provide home service
curl -X GET "https://dzmedilink.duckdns.org/api/provider/public/?provider_type=DOCTOR&is_available=true&is_home_service=true"
```

### Response (200 OK)

```json
{
  "count": 25,
  "next": "https://dzmedilink.duckdns.org/api/provider/public/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "provider_type": "DOCTOR",
      "provider_type_display": "Doctor",
      "name": "Dr. Ahmed Benali",
      "profile_image": "https://dzmedilink.duckdns.org/media/doctors/profile_1.jpg",
      "specialty": {
        "id": 1,
        "title": "Cardiology",
        "slug": "cardiology"
      },
      "years_of_experience": 15,
      "is_available": true,
      "is_home_service_available": true,
      "rating": null,
      "city": "Algiers",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "provider_type": "NURSE",
      "provider_type_display": "Nurse",
      "name": "Fatima Zohra",
      "profile_image": "https://dzmedilink.duckdns.org/media/nurses/profile_2.jpg",
      "specialty": null,
      "years_of_experience": 8,
      "is_available": true,
      "is_home_service_available": true,
      "rating": null,
      "city": "Oran",
      "created_at": "2024-01-14T09:00:00Z"
    },
    {
      "id": 3,
      "provider_type": "CLINIC",
      "provider_type_display": "Clinic",
      "name": "El-Shifa Medical Center",
      "profile_image": "https://dzmedilink.duckdns.org/media/clinics/logo_3.jpg",
      "specialty": null,
      "years_of_experience": null,
      "is_available": true,
      "is_home_service_available": false,
      "rating": null,
      "city": "Constantine",
      "created_at": "2024-01-10T14:00:00Z"
    }
  ]
}
```

### Flutter/Dart Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ProviderService {
  static const String baseUrl = 'https://dzmedilink.duckdns.org/api';

  /// Fetch list of providers with optional filters
  Future<PaginatedResponse<ProviderSummary>> getProviders({
    String? providerType,
    String? search,
    bool? isAvailable,
    bool? isHomeService,
    String? specialty,
    String? city,
    String? ordering,
    int page = 1,
  }) async {
    final queryParams = <String, String>{
      'page': page.toString(),
    };

    if (providerType != null) queryParams['provider_type'] = providerType;
    if (search != null) queryParams['search'] = search;
    if (isAvailable != null) queryParams['is_available'] = isAvailable.toString();
    if (isHomeService != null) queryParams['is_home_service'] = isHomeService.toString();
    if (specialty != null) queryParams['specialty'] = specialty;
    if (city != null) queryParams['city'] = city;
    if (ordering != null) queryParams['ordering'] = ordering;

    final uri = Uri.parse('$baseUrl/provider/public/').replace(queryParameters: queryParams);
    
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return PaginatedResponse<ProviderSummary>.fromJson(
        data,
        (json) => ProviderSummary.fromJson(json),
      );
    } else {
      throw Exception('Failed to load providers');
    }
  }
}

class PaginatedResponse<T> {
  final int count;
  final String? next;
  final String? previous;
  final List<T> results;

  PaginatedResponse({
    required this.count,
    this.next,
    this.previous,
    required this.results,
  });

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) fromJson,
  ) {
    return PaginatedResponse(
      count: json['count'],
      next: json['next'],
      previous: json['previous'],
      results: (json['results'] as List)
          .map((item) => fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}

class ProviderSummary {
  final int id;
  final String providerType;
  final String providerTypeDisplay;
  final String name;
  final String? profileImage;
  final Specialty? specialty;
  final int? yearsOfExperience;
  final bool isAvailable;
  final bool isHomeServiceAvailable;
  final double? rating;
  final String? city;
  final DateTime createdAt;

  ProviderSummary({
    required this.id,
    required this.providerType,
    required this.providerTypeDisplay,
    required this.name,
    this.profileImage,
    this.specialty,
    this.yearsOfExperience,
    required this.isAvailable,
    required this.isHomeServiceAvailable,
    this.rating,
    this.city,
    required this.createdAt,
  });

  factory ProviderSummary.fromJson(Map<String, dynamic> json) {
    return ProviderSummary(
      id: json['id'],
      providerType: json['provider_type'],
      providerTypeDisplay: json['provider_type_display'],
      name: json['name'],
      profileImage: json['profile_image'],
      specialty: json['specialty'] != null
          ? Specialty.fromJson(json['specialty'])
          : null,
      yearsOfExperience: json['years_of_experience'],
      isAvailable: json['is_available'] ?? true,
      isHomeServiceAvailable: json['is_home_service_available'] ?? false,
      rating: json['rating']?.toDouble(),
      city: json['city'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class Specialty {
  final int id;
  final String title;
  final String slug;

  Specialty({
    required this.id,
    required this.title,
    required this.slug,
  });

  factory Specialty.fromJson(Map<String, dynamic> json) {
    return Specialty(
      id: json['id'],
      title: json['title'],
      slug: json['slug'],
    );
  }
}
```

---

## 👤 Get Provider Details

### Endpoint

```
GET /api/provider/public/{id}/
```

### Description

Retrieves detailed information about a specific provider, including their full profile, services, and addresses.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Provider ID |

### Request Example

```bash
# Get details for provider with ID 1
curl -X GET "https://dzmedilink.duckdns.org/api/provider/public/1/"
```

### Response (200 OK) - Doctor Example

```json
{
  "id": 1,
  "provider_type": "DOCTOR",
  "provider_type_display": "Doctor",
  "name": "Dr. Ahmed Benali",
  "doctor": {
    "id": 1,
    "first_name": "Ahmed",
    "last_name": "Benali",
    "full_name": "Ahmed Benali",
    "gender": "M",
    "gender_display": "Male",
    "profile_image": "https://dzmedilink.duckdns.org/media/doctors/profile_1.jpg",
    "years_of_experience": 15,
    "biography": "Board-certified cardiologist with 15 years of experience...",
    "is_available": true,
    "is_home_service_available": true,
    "languages_spoken": ["Arabic", "French", "English"],
    "specialties": [
      {
        "id": 1,
        "specialty": {
          "id": 1,
          "title": "Cardiology",
          "slug": "cardiology",
          "description": "Heart and cardiovascular system",
          "icon": "https://dzmedilink.duckdns.org/media/specialties/cardiology.svg"
        },
        "is_primary": true
      }
    ],
    "services": [
      {
        "id": 1,
        "title": "General Consultation",
        "description": "Comprehensive health checkup",
        "price": "3000.00",
        "duration_minutes": 30,
        "is_home_service": false
      },
      {
        "id": 2,
        "title": "ECG Test",
        "description": "Electrocardiogram examination",
        "price": "5000.00",
        "duration_minutes": 45,
        "is_home_service": false
      }
    ],
    "created_at": "2024-01-15T10:30:00Z"
  },
  "nurse": null,
  "clinic": null,
  "laboratory": null,
  "services": [
    {
      "id": 1,
      "title": "General Consultation",
      "description": "Comprehensive health checkup",
      "price": "3000.00",
      "duration_minutes": 30,
      "is_home_service": false
    },
    {
      "id": 2,
      "title": "ECG Test",
      "description": "Electrocardiogram examination",
      "price": "5000.00",
      "duration_minutes": 45,
      "is_home_service": false
    }
  ],
  "addresses": [
    {
      "id": 1,
      "street_address": "123 Medical Street",
      "city": "Algiers",
      "state": "Algiers",
      "postal_code": "16000",
      "country": "Algeria",
      "is_primary": true
    }
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Response (200 OK) - Nurse Example

```json
{
  "id": 2,
  "provider_type": "NURSE",
  "provider_type_display": "Nurse",
  "name": "Fatima Zohra",
  "doctor": null,
  "nurse": {
    "id": 1,
    "first_name": "Fatima",
    "last_name": "Zohra",
    "full_name": "Fatima Zohra",
    "gender": "F",
    "gender_display": "Female",
    "profile_image": "https://dzmedilink.duckdns.org/media/nurses/profile_2.jpg",
    "certification": "Registered Nurse (RN)",
    "years_of_experience": 8,
    "biography": "Experienced nurse specializing in home care...",
    "is_available": true,
    "is_home_service_available": true,
    "services": [
      {
        "id": 5,
        "title": "Home Injection",
        "description": "Intramuscular or intravenous injection at home",
        "price": "1000.00",
        "duration_minutes": 15,
        "is_home_service": true
      },
      {
        "id": 6,
        "title": "Wound Dressing",
        "description": "Professional wound care and dressing",
        "price": "1500.00",
        "duration_minutes": 30,
        "is_home_service": true
      }
    ],
    "created_at": "2024-01-14T09:00:00Z"
  },
  "clinic": null,
  "laboratory": null,
  "services": [...],
  "addresses": [...],
  "created_at": "2024-01-14T09:00:00Z"
}
```

### Response (200 OK) - Clinic Example

```json
{
  "id": 3,
  "provider_type": "CLINIC",
  "provider_type_display": "Clinic",
  "name": "El-Shifa Medical Center",
  "doctor": null,
  "nurse": null,
  "clinic": {
    "id": 1,
    "clinic_name": "El-Shifa Medical Center",
    "logo": "https://dzmedilink.duckdns.org/media/clinics/logo_3.jpg",
    "website": "https://elshifa-clinic.dz",
    "description": "A comprehensive healthcare facility offering...",
    "number_of_beds": 50,
    "has_emergency_services": true,
    "is_24_hours": true,
    "outpatient_capacity_per_day": 100,
    "is_available": true,
    "services": [...],
    "created_at": "2024-01-10T14:00:00Z"
  },
  "laboratory": null,
  "services": [...],
  "addresses": [...],
  "created_at": "2024-01-10T14:00:00Z"
}
```

### Response (200 OK) - Laboratory Example

```json
{
  "id": 4,
  "provider_type": "LABORATORY",
  "provider_type_display": "Laboratory",
  "name": "Al-Hayat Diagnostics",
  "doctor": null,
  "nurse": null,
  "clinic": null,
  "laboratory": {
    "id": 1,
    "lab_name": "Al-Hayat Diagnostics",
    "accreditation": "ISO 15189",
    "website": "https://alhayat-lab.dz",
    "description": "Accredited diagnostic laboratory...",
    "is_available": true,
    "services": [
      {
        "id": 10,
        "title": "Complete Blood Count (CBC)",
        "description": "Full blood panel analysis",
        "price": "1500.00",
        "duration_minutes": 30,
        "is_home_service": false
      },
      {
        "id": 11,
        "title": "Blood Glucose Test",
        "description": "Fasting blood sugar test",
        "price": "500.00",
        "duration_minutes": 15,
        "is_home_service": true
      }
    ],
    "created_at": "2024-01-08T11:00:00Z"
  },
  "services": [...],
  "addresses": [...],
  "created_at": "2024-01-08T11:00:00Z"
}
```

### Flutter/Dart Example

```dart
/// Fetch provider details by ID
Future<ProviderDetail> getProviderDetail(int providerId) async {
  final response = await http.get(
    Uri.parse('$baseUrl/provider/public/$providerId/'),
  );

  if (response.statusCode == 200) {
    return ProviderDetail.fromJson(json.decode(response.body));
  } else if (response.statusCode == 404) {
    throw Exception('Provider not found');
  } else {
    throw Exception('Failed to load provider details');
  }
}

class ProviderDetail {
  final int id;
  final String providerType;
  final String providerTypeDisplay;
  final String name;
  final DoctorProfile? doctor;
  final NurseProfile? nurse;
  final ClinicProfile? clinic;
  final LaboratoryProfile? laboratory;
  final List<ServiceInfo> services;
  final List<AddressInfo> addresses;
  final DateTime createdAt;

  ProviderDetail({
    required this.id,
    required this.providerType,
    required this.providerTypeDisplay,
    required this.name,
    this.doctor,
    this.nurse,
    this.clinic,
    this.laboratory,
    required this.services,
    required this.addresses,
    required this.createdAt,
  });

  factory ProviderDetail.fromJson(Map<String, dynamic> json) {
    return ProviderDetail(
      id: json['id'],
      providerType: json['provider_type'],
      providerTypeDisplay: json['provider_type_display'],
      name: json['name'],
      doctor: json['doctor'] != null 
          ? DoctorProfile.fromJson(json['doctor']) 
          : null,
      nurse: json['nurse'] != null 
          ? NurseProfile.fromJson(json['nurse']) 
          : null,
      clinic: json['clinic'] != null 
          ? ClinicProfile.fromJson(json['clinic']) 
          : null,
      laboratory: json['laboratory'] != null 
          ? LaboratoryProfile.fromJson(json['laboratory']) 
          : null,
      services: (json['services'] as List?)
          ?.map((s) => ServiceInfo.fromJson(s))
          .toList() ?? [],
      addresses: (json['addresses'] as List?)
          ?.map((a) => AddressInfo.fromJson(a))
          .toList() ?? [],
      createdAt: DateTime.parse(json['created_at']),
    );
  }

  /// Get the profile image URL based on provider type
  String? get profileImage {
    switch (providerType) {
      case 'DOCTOR':
        return doctor?.profileImage;
      case 'NURSE':
        return nurse?.profileImage;
      case 'CLINIC':
        return clinic?.logo;
      default:
        return null;
    }
  }

  /// Check if provider offers home service
  bool get offersHomeService {
    switch (providerType) {
      case 'DOCTOR':
        return doctor?.isHomeServiceAvailable ?? false;
      case 'NURSE':
        return nurse?.isHomeServiceAvailable ?? false;
      default:
        return false;
    }
  }
}

class DoctorProfile {
  final int id;
  final String firstName;
  final String lastName;
  final String fullName;
  final String gender;
  final String genderDisplay;
  final String? profileImage;
  final int? yearsOfExperience;
  final String? biography;
  final bool isAvailable;
  final bool isHomeServiceAvailable;
  final List<String>? languagesSpoken;
  final List<DoctorSpecialtyInfo> specialties;
  final List<ServiceInfo> services;

  DoctorProfile({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.fullName,
    required this.gender,
    required this.genderDisplay,
    this.profileImage,
    this.yearsOfExperience,
    this.biography,
    required this.isAvailable,
    required this.isHomeServiceAvailable,
    this.languagesSpoken,
    required this.specialties,
    required this.services,
  });

  factory DoctorProfile.fromJson(Map<String, dynamic> json) {
    return DoctorProfile(
      id: json['id'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      fullName: json['full_name'],
      gender: json['gender'],
      genderDisplay: json['gender_display'],
      profileImage: json['profile_image'],
      yearsOfExperience: json['years_of_experience'],
      biography: json['biography'],
      isAvailable: json['is_available'] ?? true,
      isHomeServiceAvailable: json['is_home_service_available'] ?? false,
      languagesSpoken: (json['languages_spoken'] as List?)?.cast<String>(),
      specialties: (json['specialties'] as List?)
          ?.map((s) => DoctorSpecialtyInfo.fromJson(s))
          .toList() ?? [],
      services: (json['services'] as List?)
          ?.map((s) => ServiceInfo.fromJson(s))
          .toList() ?? [],
    );
  }

  /// Get primary specialty
  Specialty? get primarySpecialty {
    final primary = specialties.where((s) => s.isPrimary).firstOrNull;
    return primary?.specialty;
  }
}

class NurseProfile {
  final int id;
  final String firstName;
  final String lastName;
  final String fullName;
  final String gender;
  final String genderDisplay;
  final String? profileImage;
  final String? certification;
  final int? yearsOfExperience;
  final String? biography;
  final bool isAvailable;
  final bool isHomeServiceAvailable;
  final List<ServiceInfo> services;

  NurseProfile({
    required this.id,
    required this.firstName,
    required this.lastName,
    required this.fullName,
    required this.gender,
    required this.genderDisplay,
    this.profileImage,
    this.certification,
    this.yearsOfExperience,
    this.biography,
    required this.isAvailable,
    required this.isHomeServiceAvailable,
    required this.services,
  });

  factory NurseProfile.fromJson(Map<String, dynamic> json) {
    return NurseProfile(
      id: json['id'],
      firstName: json['first_name'],
      lastName: json['last_name'],
      fullName: json['full_name'],
      gender: json['gender'],
      genderDisplay: json['gender_display'],
      profileImage: json['profile_image'],
      certification: json['certification'],
      yearsOfExperience: json['years_of_experience'],
      biography: json['biography'],
      isAvailable: json['is_available'] ?? true,
      isHomeServiceAvailable: json['is_home_service_available'] ?? false,
      services: (json['services'] as List?)
          ?.map((s) => ServiceInfo.fromJson(s))
          .toList() ?? [],
    );
  }
}

class ClinicProfile {
  final int id;
  final String clinicName;
  final String? logo;
  final String? website;
  final String? description;
  final int? numberOfBeds;
  final bool hasEmergencyServices;
  final bool is24Hours;
  final int? outpatientCapacityPerDay;
  final bool isAvailable;
  final List<ServiceInfo> services;

  ClinicProfile({
    required this.id,
    required this.clinicName,
    this.logo,
    this.website,
    this.description,
    this.numberOfBeds,
    required this.hasEmergencyServices,
    required this.is24Hours,
    this.outpatientCapacityPerDay,
    required this.isAvailable,
    required this.services,
  });

  factory ClinicProfile.fromJson(Map<String, dynamic> json) {
    return ClinicProfile(
      id: json['id'],
      clinicName: json['clinic_name'],
      logo: json['logo'],
      website: json['website'],
      description: json['description'],
      numberOfBeds: json['number_of_beds'],
      hasEmergencyServices: json['has_emergency_services'] ?? false,
      is24Hours: json['is_24_hours'] ?? false,
      outpatientCapacityPerDay: json['outpatient_capacity_per_day'],
      isAvailable: json['is_available'] ?? true,
      services: (json['services'] as List?)
          ?.map((s) => ServiceInfo.fromJson(s))
          .toList() ?? [],
    );
  }
}

class LaboratoryProfile {
  final int id;
  final String labName;
  final String? accreditation;
  final String? website;
  final String? description;
  final bool isAvailable;
  final List<ServiceInfo> services;

  LaboratoryProfile({
    required this.id,
    required this.labName,
    this.accreditation,
    this.website,
    this.description,
    required this.isAvailable,
    required this.services,
  });

  factory LaboratoryProfile.fromJson(Map<String, dynamic> json) {
    return LaboratoryProfile(
      id: json['id'],
      labName: json['lab_name'],
      accreditation: json['accreditation'],
      website: json['website'],
      description: json['description'],
      isAvailable: json['is_available'] ?? true,
      services: (json['services'] as List?)
          ?.map((s) => ServiceInfo.fromJson(s))
          .toList() ?? [],
    );
  }
}

class DoctorSpecialtyInfo {
  final int id;
  final Specialty specialty;
  final bool isPrimary;

  DoctorSpecialtyInfo({
    required this.id,
    required this.specialty,
    required this.isPrimary,
  });

  factory DoctorSpecialtyInfo.fromJson(Map<String, dynamic> json) {
    return DoctorSpecialtyInfo(
      id: json['id'],
      specialty: Specialty.fromJson(json['specialty']),
      isPrimary: json['is_primary'] ?? false,
    );
  }
}

class ServiceInfo {
  final int id;
  final String title;
  final String? description;
  final String price;
  final int? durationMinutes;
  final bool isHomeService;

  ServiceInfo({
    required this.id,
    required this.title,
    this.description,
    required this.price,
    this.durationMinutes,
    required this.isHomeService,
  });

  factory ServiceInfo.fromJson(Map<String, dynamic> json) {
    return ServiceInfo(
      id: json['id'],
      title: json['title'],
      description: json['description'],
      price: json['price']?.toString() ?? '0',
      durationMinutes: json['duration_minutes'],
      isHomeService: json['is_home_service'] ?? false,
    );
  }
}

class AddressInfo {
  final int id;
  final String? streetAddress;
  final String? city;
  final String? state;
  final String? postalCode;
  final String? country;
  final bool isPrimary;

  AddressInfo({
    required this.id,
    this.streetAddress,
    this.city,
    this.state,
    this.postalCode,
    this.country,
    required this.isPrimary,
  });

  factory AddressInfo.fromJson(Map<String, dynamic> json) {
    return AddressInfo(
      id: json['id'],
      streetAddress: json['street_address'],
      city: json['city'],
      state: json['state'],
      postalCode: json['postal_code'],
      country: json['country'],
      isPrimary: json['is_primary'] ?? false,
    );
  }
}
```

---

## 👨‍⚕️ List Doctors Only

### Endpoint

```
GET /api/provider/public/doctors/
```

### Description

Retrieves a paginated list of approved doctors only. Supports the same filtering options as the main list.

### Request Example

```bash
# Get all cardiologists who provide home service
curl -X GET "https://dzmedilink.duckdns.org/api/provider/public/doctors/?specialty=cardiology&is_home_service=true"
```

### Response (200 OK)

Same format as the main provider list, but only includes providers with `provider_type: "DOCTOR"`.

---

## 👩‍⚕️ List Nurses Only

### Endpoint

```
GET /api/provider/public/nurses/
```

### Description

Retrieves a paginated list of approved nurses only.

### Request Example

```bash
# Get all available nurses who provide home service
curl -X GET "https://dzmedilink.duckdns.org/api/provider/public/nurses/?is_available=true&is_home_service=true"
```

---

## 🏥 List Clinics Only

### Endpoint

```
GET /api/provider/public/clinics/
```

### Description

Retrieves a paginated list of approved clinics only.

### Request Example

```bash
# Get all 24-hour clinics (use search for now)
curl -X GET "https://dzmedilink.duckdns.org/api/provider/public/clinics/?is_available=true"
```

---

## 🔬 List Laboratories Only

### Endpoint

```
GET /api/provider/public/laboratories/
```

### Description

Retrieves a paginated list of approved laboratories only.

### Request Example

```bash
curl -X GET "https://dzmedilink.duckdns.org/api/provider/public/laboratories/?is_available=true"
```

---

## 📊 Get Provider Type Counts

### Endpoint

```
GET /api/provider/public/provider_types/
```

### Description

Retrieves the count of approved providers by type. Useful for showing category counts in the UI.

### Request Example

```bash
curl -X GET "https://dzmedilink.duckdns.org/api/provider/public/provider_types/"
```

### Response (200 OK)

```json
[
  {
    "value": "DOCTOR",
    "label": "Doctor",
    "count": 45
  },
  {
    "value": "NURSE",
    "label": "Nurse",
    "count": 23
  },
  {
    "value": "CLINIC",
    "label": "Clinic",
    "count": 12
  },
  {
    "value": "LABORATORY",
    "label": "Laboratory",
    "count": 8
  }
]
```

### Flutter/Dart Example

```dart
/// Fetch provider type counts
Future<List<ProviderTypeCount>> getProviderTypeCounts() async {
  final response = await http.get(
    Uri.parse('$baseUrl/provider/public/provider_types/'),
  );

  if (response.statusCode == 200) {
    final List<dynamic> data = json.decode(response.body);
    return data.map((item) => ProviderTypeCount.fromJson(item)).toList();
  } else {
    throw Exception('Failed to load provider types');
  }
}

class ProviderTypeCount {
  final String value;
  final String label;
  final int count;

  ProviderTypeCount({
    required this.value,
    required this.label,
    required this.count,
  });

  factory ProviderTypeCount.fromJson(Map<String, dynamic> json) {
    return ProviderTypeCount(
      value: json['value'],
      label: json['label'],
      count: json['count'],
    );
  }
}
```

---

## 🔄 Complete Provider Browsing Flow

### Typical User Flow

```
┌─────────────────┐
│   Home Screen   │
│  (Categories)   │
└────────┬────────┘
         │
         │ GET /provider/public/provider_types/
         ▼
┌─────────────────┐
│  Show Category  │
│    Cards with   │
│     Counts      │
└────────┬────────┘
         │
         │ User taps "Doctors"
         ▼
┌─────────────────┐
│ GET /provider/  │
│ public/doctors/ │
│ ?is_available   │
│ =true           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Show Doctor    │
│     List        │
│  (Summary View) │
└────────┬────────┘
         │
         │ User taps on a doctor
         ▼
┌─────────────────┐
│ GET /provider/  │
│ public/{id}/    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Show Doctor    │
│   Detail Page   │
│ (Full Profile)  │
└────────┬────────┘
         │
         │ User taps "Book Appointment"
         ▼
┌─────────────────┐
│  Appointment    │
│  Booking Flow   │
│ (See APPTS API) │
└─────────────────┘
```

### Flutter Example: Complete Provider Browser Widget

```dart
import 'package:flutter/material.dart';

class ProviderBrowserScreen extends StatefulWidget {
  @override
  _ProviderBrowserScreenState createState() => _ProviderBrowserScreenState();
}

class _ProviderBrowserScreenState extends State<ProviderBrowserScreen> {
  final ProviderService _providerService = ProviderService();
  
  String? _selectedProviderType;
  bool _showAvailableOnly = true;
  bool _showHomeServiceOnly = false;
  String? _searchQuery;
  
  List<ProviderSummary> _providers = [];
  List<ProviderTypeCount> _categories = [];
  bool _isLoading = false;
  int _currentPage = 1;
  bool _hasMore = true;

  @override
  void initState() {
    super.initState();
    _loadCategories();
    _loadProviders();
  }

  Future<void> _loadCategories() async {
    try {
      final categories = await _providerService.getProviderTypeCounts();
      setState(() {
        _categories = categories;
      });
    } catch (e) {
      print('Error loading categories: $e');
    }
  }

  Future<void> _loadProviders({bool refresh = false}) async {
    if (_isLoading) return;
    
    if (refresh) {
      _currentPage = 1;
      _hasMore = true;
    }
    
    if (!_hasMore) return;

    setState(() => _isLoading = true);

    try {
      final response = await _providerService.getProviders(
        providerType: _selectedProviderType,
        search: _searchQuery,
        isAvailable: _showAvailableOnly ? true : null,
        isHomeService: _showHomeServiceOnly ? true : null,
        page: _currentPage,
      );

      setState(() {
        if (refresh) {
          _providers = response.results;
        } else {
          _providers.addAll(response.results);
        }
        _hasMore = response.next != null;
        _currentPage++;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading providers: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _filterByType(String? type) {
    setState(() {
      _selectedProviderType = type;
    });
    _loadProviders(refresh: true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Find Healthcare Providers'),
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: EdgeInsets.all(16),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Search providers...',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onSubmitted: (value) {
                setState(() => _searchQuery = value.isEmpty ? null : value);
                _loadProviders(refresh: true);
              },
            ),
          ),
          
          // Category Filter Chips
          SizedBox(
            height: 50,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: EdgeInsets.symmetric(horizontal: 16),
              children: [
                FilterChip(
                  label: Text('All'),
                  selected: _selectedProviderType == null,
                  onSelected: (_) => _filterByType(null),
                ),
                SizedBox(width: 8),
                ..._categories.map((cat) => Padding(
                  padding: EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text('${cat.label} (${cat.count})'),
                    selected: _selectedProviderType == cat.value,
                    onSelected: (_) => _filterByType(cat.value),
                  ),
                )),
              ],
            ),
          ),
          
          // Filter Switches
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                FilterChip(
                  label: Text('Available Now'),
                  selected: _showAvailableOnly,
                  onSelected: (value) {
                    setState(() => _showAvailableOnly = value);
                    _loadProviders(refresh: true);
                  },
                ),
                SizedBox(width: 8),
                FilterChip(
                  label: Text('Home Service'),
                  selected: _showHomeServiceOnly,
                  onSelected: (value) {
                    setState(() => _showHomeServiceOnly = value);
                    _loadProviders(refresh: true);
                  },
                ),
              ],
            ),
          ),
          
          // Provider List
          Expanded(
            child: RefreshIndicator(
              onRefresh: () => _loadProviders(refresh: true),
              child: ListView.builder(
                itemCount: _providers.length + (_hasMore ? 1 : 0),
                itemBuilder: (context, index) {
                  if (index >= _providers.length) {
                    _loadProviders();
                    return Center(child: CircularProgressIndicator());
                  }
                  
                  final provider = _providers[index];
                  return ProviderCard(
                    provider: provider,
                    onTap: () => _openProviderDetail(provider.id),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _openProviderDetail(int providerId) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ProviderDetailScreen(providerId: providerId),
      ),
    );
  }
}

class ProviderCard extends StatelessWidget {
  final ProviderSummary provider;
  final VoidCallback onTap;

  const ProviderCard({
    required this.provider,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Row(
            children: [
              // Profile Image
              CircleAvatar(
                radius: 30,
                backgroundImage: provider.profileImage != null
                    ? NetworkImage(provider.profileImage!)
                    : null,
                child: provider.profileImage == null
                    ? Icon(Icons.person, size: 30)
                    : null,
              ),
              SizedBox(width: 16),
              
              // Info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      provider.name,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      provider.providerTypeDisplay,
                      style: TextStyle(color: Colors.grey[600]),
                    ),
                    if (provider.specialty != null) ...[
                      SizedBox(height: 4),
                      Text(
                        provider.specialty!.title,
                        style: TextStyle(color: Theme.of(context).primaryColor),
                      ),
                    ],
                    SizedBox(height: 8),
                    Row(
                      children: [
                        if (provider.isAvailable)
                          Chip(
                            label: Text('Available'),
                            backgroundColor: Colors.green[100],
                            labelStyle: TextStyle(color: Colors.green[800]),
                          ),
                        if (provider.isHomeServiceAvailable) ...[
                          SizedBox(width: 8),
                          Chip(
                            label: Text('Home Service'),
                            backgroundColor: Colors.blue[100],
                            labelStyle: TextStyle(color: Colors.blue[800]),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              
              Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

class ProviderDetailScreen extends StatefulWidget {
  final int providerId;

  const ProviderDetailScreen({required this.providerId});

  @override
  _ProviderDetailScreenState createState() => _ProviderDetailScreenState();
}

class _ProviderDetailScreenState extends State<ProviderDetailScreen> {
  final ProviderService _providerService = ProviderService();
  ProviderDetail? _provider;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProvider();
  }

  Future<void> _loadProvider() async {
    try {
      final provider = await _providerService.getProviderDetail(widget.providerId);
      setState(() {
        _provider = provider;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error loading provider: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(),
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_provider == null) {
      return Scaffold(
        appBar: AppBar(),
        body: Center(child: Text('Provider not found')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_provider!.name),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with profile
            Container(
              padding: EdgeInsets.all(16),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 50,
                    backgroundImage: _provider!.profileImage != null
                        ? NetworkImage(_provider!.profileImage!)
                        : null,
                    child: _provider!.profileImage == null
                        ? Icon(Icons.person, size: 50)
                        : null,
                  ),
                  SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _provider!.name,
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(_provider!.providerTypeDisplay),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            
            Divider(),
            
            // Services
            Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Services',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 8),
                  ..._provider!.services.map((service) => Card(
                    child: ListTile(
                      title: Text(service.title),
                      subtitle: Text(service.description ?? ''),
                      trailing: Text(
                        '${service.price} DZD',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).primaryColor,
                        ),
                      ),
                    ),
                  )),
                ],
              ),
            ),
            
            // Book Appointment Button
            Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    // Navigate to appointment booking
                    // See APPOINTMENTS_API.md for the flow
                  },
                  child: Text('Book Appointment'),
                  style: ElevatedButton.styleFrom(
                    padding: EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## ⚠️ Error Responses

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error."
}
```

---

## 📝 Notes

1. **Public Endpoints**: All endpoints in this document are public and do not require authentication.

2. **Only Approved Providers**: These endpoints only return providers with `status = APPROVED`. Pending, refused, or suspended providers are not visible.

3. **Sensitive Data Excluded**: Public serializers exclude sensitive information like:
   - License numbers
   - Phone numbers
   - Date of birth
   - License documents
   - Entrepreneur cards

4. **Pagination**: All list endpoints are paginated. Use the `next` and `previous` URLs to navigate pages.

5. **Related Documentation**:
   - [Authentication API](./AUTHENTICATION_API.md) - For user registration and login
   - [Appointments API](./APPOINTMENTS_API.md) - For booking appointments with providers
