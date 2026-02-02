# Doctor Specialties & Services API

## Overview

This documentation covers how **Doctors** can manage their **Specialties** and **Medical Services** through the MediLink API. Doctors can:

1. **Specialties**: Browse existing specialties, add them to their profile, set a primary specialty, and track years of experience
2. **Services**: Browse existing services, create custom services, set custom pricing, and manage availability

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Specialties Management](#specialties-management)
   - [List All Specialties](#list-all-specialties)
   - [Get Specialty Details](#get-specialty-details)
   - [My Specialties](#my-specialties)
   - [Add Specialty to Profile](#add-specialty-to-profile)
   - [Update My Specialty](#update-my-specialty)
   - [Remove Specialty](#remove-specialty)
   - [Create New Specialty](#create-new-specialty)
4. [Services Management](#services-management)
   - [List All Services](#list-all-services)
   - [Get Service Details](#get-service-details)
   - [My Services](#my-services)
   - [Add Service to Profile](#add-service-to-profile)
   - [Update My Service](#update-my-service)
   - [Remove Service](#remove-service)
   - [Create New Service](#create-new-service)
5. [Integration Examples](#integration-examples)
6. [Error Handling](#error-handling)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

---

## Authentication

All doctor-specific endpoints require authentication. Include your token in every request:

```
Authorization: Token <your_token_here>
```

> **Note:** Only users with Doctor role can access doctor-specific endpoints like `/doctor-specialties/` and `/doctor-services/`.

---

## Specialties Management

Medical specialties are a **global catalog** maintained by the platform. Doctors can:
- Browse and search existing specialties
- Add specialties to their profile
- Set one specialty as their **primary** specialty
- Track years of experience in each specialty
- Create new specialties (which are auto-attached to their profile)

### List All Specialties

Get all available specialties from the global catalog.

```
GET /api/specialties/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by title (en/ar/fr) or description |
| `medical_domain` | string | Filter by medical domain |
| `is_active` | boolean | Filter active/inactive specialties |
| `ordering` | string | Order by: `title`, `created_at` |
| `lang` | string | Response language: `en`, `ar`, `fr` |

#### Response (200 OK)

```json
[
    {
        "id": 1,
        "title": "Cardiology",
        "slug": "cardiology",
        "description": "Diagnosis and treatment of heart and cardiovascular conditions",
        "medical_domain": "Internal Medicine",
        "icon": "https://dzmedilink.duckdns.org/media/specialties/icons/cardiology.png",
        "is_active": true,
        "doctors_count": 45,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 2,
        "title": "Dermatology",
        "slug": "dermatology",
        "description": "Treatment of skin, hair, and nail conditions",
        "medical_domain": "Dermatology",
        "icon": "https://dzmedilink.duckdns.org/media/specialties/icons/dermatology.png",
        "is_active": true,
        "doctors_count": 32,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 3,
        "title": "Pediatrics",
        "slug": "pediatrics",
        "description": "Medical care for infants, children, and adolescents",
        "medical_domain": "Pediatrics",
        "icon": null,
        "is_active": true,
        "doctors_count": 28,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
    }
]
```

#### With Multilingual Support

```
GET /api/specialties/?lang=ar
```

Returns titles and descriptions in Arabic (if available).

```
GET /api/specialties/?include_all_translations=true
```

Returns all language versions:

```json
{
    "id": 1,
    "title": "Cardiology",
    "title_en": "Cardiology",
    "title_ar": "أمراض القلب",
    "title_fr": "Cardiologie",
    "description_en": "Diagnosis and treatment of heart conditions",
    "description_ar": "تشخيص وعلاج أمراض القلب",
    "description_fr": "Diagnostic et traitement des maladies cardiaques",
    ...
}
```

---

### Get Specialty Details

Get details of a specific specialty.

```
GET /api/specialties/{id}/
```

#### Response (200 OK)

```json
{
    "id": 1,
    "title": "Cardiology",
    "slug": "cardiology",
    "description": "Diagnosis and treatment of heart and cardiovascular conditions",
    "medical_domain": "Internal Medicine",
    "icon": "https://dzmedilink.duckdns.org/media/specialties/icons/cardiology.png",
    "is_active": true,
    "doctors_count": 45,
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
}
```

---

### My Specialties

Get all specialties assigned to your doctor profile.

```
GET /api/specialties/doctor-specialties/
```

#### Response (200 OK)

```json
[
    {
        "id": 1,
        "doctor": "doctor-uuid",
        "doctor_name": "Dr. Mohamed Kaddour",
        "specialty": {
            "id": 1,
            "title": "Cardiology",
            "slug": "cardiology",
            "description": "Diagnosis and treatment of heart conditions",
            "medical_domain": "Internal Medicine",
            "icon": "https://dzmedilink.duckdns.org/media/specialties/icons/cardiology.png",
            "doctors_count": 45
        },
        "is_primary": true,
        "years_of_experience": 15,
        "created_at": "2025-06-01T09:00:00Z"
    },
    {
        "id": 2,
        "doctor": "doctor-uuid",
        "doctor_name": "Dr. Mohamed Kaddour",
        "specialty": {
            "id": 5,
            "title": "Internal Medicine",
            "slug": "internal-medicine",
            "description": "General internal medicine practice",
            "medical_domain": "Internal Medicine",
            "icon": null,
            "doctors_count": 78
        },
        "is_primary": false,
        "years_of_experience": 20,
        "created_at": "2025-06-01T09:05:00Z"
    }
]
```

---

### Add Specialty to Profile

Add an existing specialty to your doctor profile.

```
POST /api/specialties/doctor-specialties/
```

#### Request Body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `specialty_id` | ✅ Yes | integer | ID of the specialty to add |
| `is_primary` | ❌ No | boolean | Set as primary specialty (default: `false`) |
| `years_of_experience` | ❌ No | integer | Years of experience in this specialty |

#### Example Request

```json
{
    "specialty_id": 1,
    "is_primary": true,
    "years_of_experience": 15
}
```

#### Response (201 Created)

```json
{
    "id": 1,
    "doctor": "doctor-uuid",
    "doctor_name": "Dr. Mohamed Kaddour",
    "specialty": {
        "id": 1,
        "title": "Cardiology",
        "slug": "cardiology",
        "description": "Diagnosis and treatment of heart conditions",
        "medical_domain": "Internal Medicine",
        "icon": "https://dzmedilink.duckdns.org/media/specialties/icons/cardiology.png",
        "doctors_count": 46
    },
    "is_primary": true,
    "years_of_experience": 15,
    "created_at": "2026-02-02T14:30:00Z"
}
```

#### Alternative Endpoint

```
POST /api/specialties/doctor-specialties/assign/
```

Same request body and response.

---

### Update My Specialty

Update your specialty relationship (change primary status or years of experience).

```
PATCH /api/specialties/doctor-specialties/{id}/
```

#### Request Body

```json
{
    "is_primary": true,
    "years_of_experience": 18
}
```

> **Note:** When you set a specialty as primary (`is_primary: true`), any other specialty that was previously marked as primary will be automatically unmarked.

#### Response (200 OK)

```json
{
    "id": 1,
    "doctor": "doctor-uuid",
    "doctor_name": "Dr. Mohamed Kaddour",
    "specialty": {
        "id": 1,
        "title": "Cardiology",
        ...
    },
    "is_primary": true,
    "years_of_experience": 18,
    "created_at": "2026-02-02T14:30:00Z"
}
```

---

### Remove Specialty

Remove a specialty from your profile.

```
DELETE /api/specialties/doctor-specialties/{id}/
```

#### Response (204 No Content)

No content is returned on successful deletion.

---

### Create New Specialty

If the specialty you need doesn't exist in the catalog, you can create it. When a doctor creates a specialty, it is **automatically attached** to their profile.

```
POST /api/specialties/
```

#### Request Body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `title` | ✅ Yes | string | Primary title (English) |
| `description` | ❌ No | string | Primary description |
| `medical_domain` | ❌ No | string | Medical domain category |
| `title_ar` | ❌ No | string | Arabic title |
| `title_fr` | ❌ No | string | French title |
| `description_ar` | ❌ No | string | Arabic description |
| `description_fr` | ❌ No | string | French description |

#### Example Request

```json
{
    "title": "Sports Medicine",
    "description": "Treatment of sports-related injuries and athletic performance",
    "medical_domain": "Orthopedics",
    "title_ar": "الطب الرياضي",
    "title_fr": "Médecine du sport"
}
```

#### Response (201 Created)

```json
{
    "id": 25,
    "title": "Sports Medicine",
    "slug": "sports-medicine",
    "description": "Treatment of sports-related injuries and athletic performance",
    "medical_domain": "Orthopedics",
    "icon": null,
    "is_active": true,
    "doctors_count": 1,
    "created_at": "2026-02-02T15:00:00Z",
    "updated_at": "2026-02-02T15:00:00Z"
}
```

> **Auto-Attach:** The newly created specialty is automatically added to your doctor profile with `is_primary: false`.

---

## Services Management

Medical services are also a **global catalog**. Doctors can:
- Browse existing services
- Add services to their profile
- Set **custom pricing** for each service
- Set **custom duration** for each service
- Control availability of each service
- Create new services (auto-attached to their profile)

### List All Services

Get all available services from the global catalog.

```
GET /api/services/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by title or description |
| `is_home_service` | boolean | Filter home visit services |
| `is_active` | boolean | Filter active/inactive services |
| `specialty` | integer | Filter by specialty ID |
| `ordering` | string | Order by: `title`, `price`, `created_at` |
| `lang` | string | Response language: `en`, `ar`, `fr` |

#### Response (200 OK)

```json
[
    {
        "id": 1,
        "title": "General Consultation",
        "slug": "general-consultation",
        "description": "Standard medical consultation for diagnosis and treatment planning",
        "service_type": "DOCTOR",
        "service_type_display": "Doctor Service",
        "price": "2500.00",
        "currency": "DZD",
        "currency_display": "Algerian Dinar",
        "duration_minutes": 30,
        "icon": null,
        "is_home_service": false,
        "is_on_demand": false,
        "is_active": true,
        "specialty": {
            "id": 1,
            "title": "General Practice",
            "slug": "general-practice"
        },
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 2,
        "title": "ECG (Electrocardiogram)",
        "slug": "ecg-electrocardiogram",
        "description": "Heart rhythm and electrical activity test",
        "service_type": "DOCTOR",
        "service_type_display": "Doctor Service",
        "price": "3500.00",
        "currency": "DZD",
        "currency_display": "Algerian Dinar",
        "duration_minutes": 20,
        "icon": null,
        "is_home_service": false,
        "is_on_demand": false,
        "is_active": true,
        "specialty": {
            "id": 1,
            "title": "Cardiology",
            "slug": "cardiology"
        },
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
    }
]
```

---

### Get Service Details

Get details of a specific service.

```
GET /api/services/{id}/
```

#### Response (200 OK)

```json
{
    "id": 1,
    "title": "General Consultation",
    "slug": "general-consultation",
    "description": "Standard medical consultation for diagnosis and treatment planning",
    "service_type": "DOCTOR",
    "service_type_display": "Doctor Service",
    "price": "2500.00",
    "currency": "DZD",
    "currency_display": "Algerian Dinar",
    "duration_minutes": 30,
    "icon": null,
    "is_home_service": false,
    "is_on_demand": false,
    "is_active": true,
    "specialty": {
        "id": 1,
        "title": "General Practice",
        "slug": "general-practice",
        "description": "General medical practice"
    },
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
}
```

---

### My Services

Get all services assigned to your doctor profile.

```
GET /api/services/doctor-services/
```

#### Response (200 OK)

```json
[
    {
        "id": 1,
        "doctor": "doctor-uuid",
        "doctor_name": "Dr. Mohamed Kaddour",
        "service": {
            "id": 1,
            "title": "General Consultation",
            "slug": "general-consultation",
            "description": "Standard medical consultation",
            "service_type": "DOCTOR",
            "service_type_display": "Doctor Service",
            "price": "2500.00",
            "currency": "DZD",
            "duration_minutes": 30,
            "icon": null,
            "is_home_service": false,
            "is_on_demand": false,
            "specialty_name": "General Practice"
        },
        "custom_price": "3000.00",
        "custom_duration_minutes": 45,
        "effective_price": "3000.00",
        "effective_duration": 45,
        "is_available": true,
        "notes": "Includes follow-up consultation within 7 days",
        "created_at": "2026-01-01T09:00:00Z"
    },
    {
        "id": 2,
        "doctor": "doctor-uuid",
        "doctor_name": "Dr. Mohamed Kaddour",
        "service": {
            "id": 2,
            "title": "ECG (Electrocardiogram)",
            "slug": "ecg-electrocardiogram",
            "description": "Heart rhythm test",
            "service_type": "DOCTOR",
            "service_type_display": "Doctor Service",
            "price": "3500.00",
            "currency": "DZD",
            "duration_minutes": 20,
            "icon": null,
            "is_home_service": false,
            "is_on_demand": false,
            "specialty_name": "Cardiology"
        },
        "custom_price": null,
        "custom_duration_minutes": null,
        "effective_price": "3500.00",
        "effective_duration": 20,
        "is_available": true,
        "notes": "",
        "created_at": "2026-01-01T09:05:00Z"
    }
]
```

#### Understanding Price Fields

| Field | Description |
|-------|-------------|
| `service.price` | Default service price from global catalog |
| `custom_price` | Your custom price (if set) |
| `effective_price` | Actual price used: `custom_price` if set, otherwise `service.price` |

---

### Add Service to Profile

Add an existing service to your doctor profile.

```
POST /api/services/doctor-services/
```

#### Request Body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `service_id` | ✅ Yes | integer | ID of the service to add |
| `custom_price` | ❌ No | decimal | Your custom price (overrides default) |
| `custom_duration_minutes` | ❌ No | integer | Your custom duration (overrides default) |
| `is_available` | ❌ No | boolean | Whether you're currently offering this (default: `true`) |
| `notes` | ❌ No | string | Additional notes about your service offering |

#### Example Request

```json
{
    "service_id": 1,
    "custom_price": "3500.00",
    "custom_duration_minutes": 45,
    "is_available": true,
    "notes": "Includes detailed diagnosis report and follow-up consultation"
}
```

#### Response (201 Created)

```json
{
    "id": 3,
    "doctor": "doctor-uuid",
    "doctor_name": "Dr. Mohamed Kaddour",
    "service": {
        "id": 1,
        "title": "General Consultation",
        "slug": "general-consultation",
        "description": "Standard medical consultation",
        "service_type": "DOCTOR",
        "service_type_display": "Doctor Service",
        "price": "2500.00",
        "currency": "DZD",
        "duration_minutes": 30,
        "icon": null,
        "is_home_service": false,
        "is_on_demand": false,
        "specialty_name": "General Practice"
    },
    "custom_price": "3500.00",
    "custom_duration_minutes": 45,
    "effective_price": "3500.00",
    "effective_duration": 45,
    "is_available": true,
    "notes": "Includes detailed diagnosis report and follow-up consultation",
    "created_at": "2026-02-02T15:30:00Z"
}
```

---

### Update My Service

Update your service offering (change price, duration, or availability).

```
PATCH /api/services/doctor-services/{id}/
```

#### Request Body

```json
{
    "custom_price": "4000.00",
    "is_available": false,
    "notes": "Service temporarily unavailable"
}
```

#### Response (200 OK)

```json
{
    "id": 1,
    "doctor": "doctor-uuid",
    "doctor_name": "Dr. Mohamed Kaddour",
    "service": {
        "id": 1,
        "title": "General Consultation",
        ...
    },
    "custom_price": "4000.00",
    "custom_duration_minutes": 45,
    "effective_price": "4000.00",
    "effective_duration": 45,
    "is_available": false,
    "notes": "Service temporarily unavailable",
    "created_at": "2026-01-01T09:00:00Z"
}
```

---

### Remove Service

Remove a service from your profile.

```
DELETE /api/services/doctor-services/{id}/
```

#### Response (204 No Content)

No content is returned on successful deletion.

---

### Create New Service

If the service you need doesn't exist in the catalog, you can create it. When a doctor creates a service, it is **automatically attached** to their profile.

```
POST /api/services/
```

#### Request Body

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `title` | ✅ Yes | string | Service title (English) |
| `description` | ❌ No | string | Service description |
| `price` | ✅ Yes | decimal | Base price for the service |
| `currency` | ❌ No | string | Currency code: `DZD`, `USD`, `EUR` (default: `DZD`) |
| `duration_minutes` | ✅ Yes | integer | Service duration in minutes |
| `service_type` | ❌ No | string | `DOCTOR`, `NURSE`, `VTC`, `GENERAL` (default: `GENERAL`) |
| `is_home_service` | ❌ No | boolean | Can be performed at patient's home |
| `is_on_demand` | ❌ No | boolean | Available for on-demand booking |
| `specialty_id` | ❌ No | integer | Related specialty ID |
| `title_ar` | ❌ No | string | Arabic title |
| `title_fr` | ❌ No | string | French title |
| `description_ar` | ❌ No | string | Arabic description |
| `description_fr` | ❌ No | string | French description |

#### Example Request

```json
{
    "title": "Cardiac Stress Test",
    "description": "Exercise stress test to evaluate heart function under physical stress",
    "price": "8000.00",
    "currency": "DZD",
    "duration_minutes": 60,
    "service_type": "DOCTOR",
    "is_home_service": false,
    "specialty_id": 1,
    "title_ar": "اختبار إجهاد القلب",
    "title_fr": "Test d'effort cardiaque"
}
```

#### Response (201 Created)

```json
{
    "id": 50,
    "title": "Cardiac Stress Test",
    "slug": "cardiac-stress-test",
    "description": "Exercise stress test to evaluate heart function under physical stress",
    "service_type": "DOCTOR",
    "service_type_display": "Doctor Service",
    "price": "8000.00",
    "currency": "DZD",
    "currency_display": "Algerian Dinar",
    "duration_minutes": 60,
    "icon": null,
    "is_home_service": false,
    "is_on_demand": false,
    "is_active": true,
    "specialty": {
        "id": 1,
        "title": "Cardiology",
        "slug": "cardiology"
    },
    "created_at": "2026-02-02T16:00:00Z",
    "updated_at": "2026-02-02T16:00:00Z"
}
```

> **Auto-Attach:** The newly created service is automatically added to your doctor profile with `is_available: true`.

---

## Integration Examples

### JavaScript - Load and Display Doctor's Specialties

```javascript
// Fetch doctor's specialties
async function loadMySpecialties() {
    const response = await fetch('https://dzmedilink.duckdns.org/api/specialties/doctor-specialties/', {
        headers: {
            'Authorization': `Token ${token}`
        }
    });
    
    const specialties = await response.json();
    
    // Display with primary indicator
    specialties.forEach(item => {
        console.log(`${item.specialty.title} ${item.is_primary ? '(Primary)' : ''} - ${item.years_of_experience} years`);
    });
    
    return specialties;
}
```

### JavaScript - Add Specialty to Profile

```javascript
// Add a specialty
async function addSpecialty(specialtyId, isPrimary = false, yearsExp = null) {
    const response = await fetch('https://dzmedilink.duckdns.org/api/specialties/doctor-specialties/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            specialty_id: specialtyId,
            is_primary: isPrimary,
            years_of_experience: yearsExp
        })
    });
    
    if (response.status === 201) {
        return await response.json();
    } else {
        const error = await response.json();
        throw new Error(error.specialty || error.detail || 'Failed to add specialty');
    }
}
```

### JavaScript - Add Service with Custom Price

```javascript
// Add a service with custom pricing
async function addService(serviceId, customPrice = null, customDuration = null) {
    const response = await fetch('https://dzmedilink.duckdns.org/api/services/doctor-services/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            service_id: serviceId,
            custom_price: customPrice,
            custom_duration_minutes: customDuration,
            is_available: true
        })
    });
    
    return await response.json();
}

// Example: Add service with custom price of 4000 DZD
addService(1, "4000.00", 45);
```

### React Component - Specialty Manager

```jsx
import React, { useState, useEffect } from 'react';

const SpecialtyManager = () => {
    const [allSpecialties, setAllSpecialties] = useState([]);
    const [mySpecialties, setMySpecialties] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    
    useEffect(() => {
        fetchAllSpecialties();
        fetchMySpecialties();
    }, []);
    
    const fetchAllSpecialties = async () => {
        const response = await api.get('/specialties/');
        setAllSpecialties(response.data);
    };
    
    const fetchMySpecialties = async () => {
        const response = await api.get('/specialties/doctor-specialties/');
        setMySpecialties(response.data);
    };
    
    const addSpecialty = async (specialtyId) => {
        await api.post('/specialties/doctor-specialties/', {
            specialty_id: specialtyId,
            is_primary: mySpecialties.length === 0 // First one is primary
        });
        fetchMySpecialties();
    };
    
    const removeSpecialty = async (doctorSpecialtyId) => {
        await api.delete(`/specialties/doctor-specialties/${doctorSpecialtyId}/`);
        fetchMySpecialties();
    };
    
    const setPrimary = async (doctorSpecialtyId) => {
        await api.patch(`/specialties/doctor-specialties/${doctorSpecialtyId}/`, {
            is_primary: true
        });
        fetchMySpecialties();
    };
    
    const mySpecialtyIds = mySpecialties.map(s => s.specialty.id);
    const availableSpecialties = allSpecialties.filter(s => 
        !mySpecialtyIds.includes(s.id) &&
        s.title.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    return (
        <div className="specialty-manager">
            <h2>My Specialties</h2>
            <ul className="my-specialties">
                {mySpecialties.map(item => (
                    <li key={item.id} className={item.is_primary ? 'primary' : ''}>
                        <span className="title">{item.specialty.title}</span>
                        {item.is_primary && <span className="badge">Primary</span>}
                        <span className="experience">{item.years_of_experience} years</span>
                        {!item.is_primary && (
                            <button onClick={() => setPrimary(item.id)}>Set Primary</button>
                        )}
                        <button onClick={() => removeSpecialty(item.id)}>Remove</button>
                    </li>
                ))}
            </ul>
            
            <h3>Add Specialty</h3>
            <input
                type="text"
                placeholder="Search specialties..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
            />
            <ul className="available-specialties">
                {availableSpecialties.map(specialty => (
                    <li key={specialty.id}>
                        <span>{specialty.title}</span>
                        <span className="domain">{specialty.medical_domain}</span>
                        <button onClick={() => addSpecialty(specialty.id)}>Add</button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default SpecialtyManager;
```

---

## Error Handling

### Common Errors

#### Specialty Already Assigned

```json
{
    "specialty": ["Specialty already assigned to this doctor."]
}
```

#### Service Already Assigned

```json
{
    "service": ["Service already assigned to this doctor."]
}
```

#### Doctor Profile Not Found

```json
{
    "detail": "Doctor profile not found."
}
```

#### Specialty/Service Not Found

```json
{
    "specialty_id": ["Invalid pk \"999\" - object does not exist."]
}
```

#### Permission Denied

```json
{
    "detail": "You do not have permission to perform this action."
}
```

---

## Summary

| Action | Endpoint | Method |
|--------|----------|--------|
| List all specialties | `/api/specialties/` | GET |
| Get specialty details | `/api/specialties/{id}/` | GET |
| Create new specialty | `/api/specialties/` | POST |
| My specialties | `/api/specialties/doctor-specialties/` | GET |
| Add specialty to profile | `/api/specialties/doctor-specialties/` | POST |
| Update my specialty | `/api/specialties/doctor-specialties/{id}/` | PATCH |
| Remove specialty | `/api/specialties/doctor-specialties/{id}/` | DELETE |
| List all services | `/api/services/` | GET |
| Get service details | `/api/services/{id}/` | GET |
| Create new service | `/api/services/` | POST |
| My services | `/api/services/doctor-services/` | GET |
| Add service to profile | `/api/services/doctor-services/` | POST |
| Update my service | `/api/services/doctor-services/{id}/` | PATCH |
| Remove service | `/api/services/doctor-services/{id}/` | DELETE |
