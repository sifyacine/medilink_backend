# Medilink Frontend Integration Guide

**Version:** 2.0.0  
**Last Updated:** January 28, 2026

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication Flow](#authentication-flow)
3. [Patient Record Creation Flow](#patient-record-creation-flow)
4. [Patient Account Linking Flow](#patient-account-linking-flow)
5. [Services & Specialties Management](#services--specialties-management)
6. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
7. [Code Examples](#code-examples)

---

## Getting Started

### Base URL
```
Development: http://localhost:8000/api/
Production: https://your-domain.com/api/
```

### Authentication Header
All authenticated requests must include:
```
Authorization: Token <user-token>
```

### Content Type
```
Content-Type: application/json
```

---

## Authentication Flow

### 1. Patient Registration
```
POST /api/auth/patient/register/
```

```javascript
const registerPatient = async (email, password) => {
  const response = await fetch('/api/auth/patient/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      password2: password
    })
  });
  return response.json();
};
```

### 2. Provider Registration
```
POST /api/auth/provider/register/
```

Provider types: `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY`, `VTC`, `SELLER`

### 3. Login
```
POST /api/auth/login/
```

### 4. Get Current User Profile
```
GET /api/auth/me/
```

The response includes role-specific data:
- For providers: `provider_profile` with nested doctor/nurse/clinic data
- For patients: `patient_profile`
- For all: `addresses` array

---

## Patient Record Creation Flow

### Use Case
A provider (doctor, nurse, clinic, lab, etc.) needs to create a record for a patient who doesn't have a Medilink account.

### Step 1: Provider Creates Patient Record

**Endpoint:** `POST /api/patients/`

```javascript
const createPatientRecord = async (token, patientData) => {
  const response = await fetch('/api/patients/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify({
      first_name: patientData.firstName,
      last_name: patientData.lastName,
      date_of_birth: patientData.dateOfBirth, // Format: YYYY-MM-DD
      gender: patientData.gender, // MALE, FEMALE, OTHER, PREFER_NOT_TO_SAY
      phone_number: patientData.phone,
      email: patientData.email, // Optional
      blood_type: patientData.bloodType, // A+, A-, B+, B-, AB+, AB-, O+, O-, UNKNOWN
      known_allergies: patientData.allergies,
      chronic_conditions: patientData.conditions,
      current_medications: patientData.medications,
      address: patientData.address,
      city: patientData.city,
      country: patientData.country,
      notes: patientData.notes
    })
  });
  return response.json();
};
```

### Step 2: Provider Gets Linking Token

After creating the record, get the token to give to the patient:

**Endpoint:** `GET /api/patients/{id}/token/`

```javascript
const getLinkingToken = async (token, patientRecordId) => {
  const response = await fetch(`/api/patients/${patientRecordId}/token/`, {
    headers: { 'Authorization': `Token ${token}` }
  });
  return response.json();
};
```

**Response:**
```json
{
  "linking_token": "XyZ8h2KpmN3qR5tU7wY9aB1cD3eF5gH7...",
  "patient_name": "Ahmed Benali",
  "token_used": false,
  "is_linked": false
}
```

### Step 3: Provider Gives Token to Patient

The provider should:
1. Display the token to the patient
2. Print it on a card/receipt
3. Send it via SMS/email
4. Give written instructions

**Important:** The token is:
- **Unique** - Only works for this patient record
- **One-time use** - Cannot be reused after linking
- **Secure** - 256-bit cryptographically secure

---

## Patient Account Linking Flow

### Use Case
A patient has a linking token from their healthcare provider and now wants to create a Medilink account and link their existing medical records.

### Step 1: Patient Creates Account

```javascript
const registerPatient = async (email, password) => {
  const response = await fetch('/api/auth/patient/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, password2: password })
  });
  const data = await response.json();
  // Store the token
  localStorage.setItem('authToken', data.token);
  return data;
};
```

### Step 2: Patient Links Account with Token

**Endpoint:** `POST /api/patients/link-account/`

```javascript
const linkPatientAccount = async (authToken, linkingToken) => {
  const response = await fetch('/api/patients/link-account/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${authToken}`
    },
    body: JSON.stringify({
      linking_token: linkingToken
    })
  });
  return response.json();
};
```

**Success Response:**
```json
{
  "message": "Account successfully linked to patient record.",
  "patient_record": {
    "id": 10,
    "first_name": "Ahmed",
    "last_name": "Benali",
    "is_linked": true,
    ...
  }
}
```

### Step 3: Patient Accesses Their Record

**Endpoint:** `GET /api/patients/me/`

```javascript
const getMyPatientRecord = async (token) => {
  const response = await fetch('/api/patients/me/', {
    headers: { 'Authorization': `Token ${token}` }
  });
  return response.json();
};
```

---

## Services & Specialties Management

### Understanding the Architecture

- **Services** and **Specialties** are **global catalogs**
- Providers don't "own" services - they "attach" them
- Linking tables (`DoctorService`, `NurseService`, `DoctorSpecialty`) connect providers to catalog items

### Creating Services (Doctors & Clinics)

#### As a Doctor (Auto-Attach)
When a doctor creates a service, it's automatically attached to their profile.

```javascript
const createService = async (token, serviceData) => {
  const response = await fetch('/api/services/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify({
      title: "Cardiology Consultation",
      description: "Complete heart examination",
      price: "5000.00",
      currency: "DZD",
      duration_minutes: 45,
      is_home_service: false,
      specialty_id: 2 // Optional
    })
  });
  return response.json();
};
```

#### As a Clinic (Global Only)
When a clinic creates a service, it's added to the global catalog without attachment.

### Attaching Existing Services

#### Doctor Attaching a Service
```javascript
const attachServiceToDoctor = async (token, serviceId, customPrice = null) => {
  const response = await fetch('/api/services/doctor-services/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify({
      service_id: serviceId,
      custom_price: customPrice, // Override service default price
      is_available: true
    })
  });
  return response.json();
};
```

#### Nurse Attaching a Service
```javascript
const attachServiceToNurse = async (token, serviceId) => {
  const response = await fetch('/api/services/nurse-services/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify({
      service_id: serviceId,
      is_available: true
    })
  });
  return response.json();
};
```

### Creating Specialties (Doctors & Clinics)

```javascript
const createSpecialty = async (token, specialtyData) => {
  const response = await fetch('/api/specialties/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify({
      title: "Neurology",
      title_ar: "طب الأعصاب",
      title_fr: "Neurologie",
      description: "Brain and nervous system",
      medical_domain: "Internal Medicine"
    })
  });
  return response.json();
};
```

### Attaching Specialties to Doctor

```javascript
const attachSpecialtyToDoctor = async (token, specialtyId, isPrimary = false) => {
  const response = await fetch('/api/specialties/doctor-specialties/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Token ${token}`
    },
    body: JSON.stringify({
      specialty_id: specialtyId,
      is_primary: isPrimary,
      years_of_experience: 10
    })
  });
  return response.json();
};
```

---

## Common Mistakes to Avoid

### 1. ❌ Not Including Authentication Token
```javascript
// WRONG
fetch('/api/patients/');

// CORRECT
fetch('/api/patients/', {
  headers: { 'Authorization': `Token ${token}` }
});
```

### 2. ❌ Using Wrong Date Format
```javascript
// WRONG
date_of_birth: "15/03/1990"
date_of_birth: "March 15, 1990"

// CORRECT
date_of_birth: "1990-03-15" // ISO 8601 format
```

### 3. ❌ Nurses Trying to Create Services
Nurses **cannot** create services. They can only attach existing ones.

```javascript
// This will return 403 Forbidden for nurses
POST /api/services/ 

// Nurses should use this instead
POST /api/services/nurse-services/
```

### 4. ❌ Reusing Linking Tokens
Each linking token can only be used **once**. After a patient links their account, the token becomes invalid.

### 5. ❌ Not Handling Provider Status
Providers need to be **APPROVED** before they can create patient records.

```javascript
// Check provider status before allowing actions
const checkProviderStatus = (user) => {
  if (user.provider_profile?.status !== 'APPROVED') {
    alert('Your provider account is pending approval');
    return false;
  }
  return true;
};
```

### 6. ❌ Not Checking Response Status
```javascript
// WRONG
const data = await response.json();
showData(data);

// CORRECT
if (!response.ok) {
  const error = await response.json();
  throw new Error(error.detail || error.error || 'Request failed');
}
const data = await response.json();
showData(data);
```

### 7. ❌ Missing Required Fields for Patient Records
```javascript
// These fields are REQUIRED:
{
  first_name: "...",      // Required
  last_name: "...",       // Required
  date_of_birth: "...",   // Required
  gender: "..."           // Required
}
```

---

## Code Examples

### Complete Patient Record Workflow (React/JavaScript)

```javascript
// services/patientService.js

const API_BASE = '/api';

export const patientService = {
  // Create a patient record (provider only)
  async createRecord(token, patientData) {
    const response = await fetch(`${API_BASE}/patients/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify(patientData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(JSON.stringify(error));
    }
    
    return response.json();
  },

  // Get linking token (provider only)
  async getToken(token, recordId) {
    const response = await fetch(`${API_BASE}/patients/${recordId}/token/`, {
      headers: { 'Authorization': `Token ${token}` }
    });
    
    if (!response.ok) {
      throw new Error('Failed to get linking token');
    }
    
    return response.json();
  },

  // Link account with token (patient only)
  async linkAccount(token, linkingToken) {
    const response = await fetch(`${API_BASE}/patients/link-account/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify({ linking_token: linkingToken })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to link account');
    }
    
    return response.json();
  },

  // Get my patient record (patient only)
  async getMyRecord(token) {
    const response = await fetch(`${API_BASE}/patients/me/`, {
      headers: { 'Authorization': `Token ${token}` }
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        return null; // No linked record
      }
      throw new Error('Failed to get patient record');
    }
    
    return response.json();
  },

  // List accessible patient records (provider only)
  async listRecords(token, filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${API_BASE}/patients/?${params}`, {
      headers: { 'Authorization': `Token ${token}` }
    });
    
    if (!response.ok) {
      throw new Error('Failed to list patient records');
    }
    
    return response.json();
  },

  // Grant access to another provider
  async grantAccess(token, recordId, providerId, accessLevel = 'FULL') {
    const response = await fetch(`${API_BASE}/patients/${recordId}/grant-access/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify({
        provider_id: providerId,
        access_level: accessLevel
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to grant access');
    }
    
    return response.json();
  }
};
```

### React Component Example

```jsx
// components/PatientLinkingForm.jsx
import React, { useState } from 'react';
import { patientService } from '../services/patientService';

export function PatientLinkingForm({ authToken, onSuccess }) {
  const [linkingToken, setLinkingToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const result = await patientService.linkAccount(authToken, linkingToken);
      onSuccess(result.patient_record);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Link Your Medical Records</h2>
      <p>Enter the token provided by your healthcare provider:</p>
      
      <input
        type="text"
        value={linkingToken}
        onChange={(e) => setLinkingToken(e.target.value)}
        placeholder="Enter linking token"
        required
      />
      
      {error && <div className="error">{error}</div>}
      
      <button type="submit" disabled={loading}>
        {loading ? 'Linking...' : 'Link My Records'}
      </button>
    </form>
  );
}
```

---

## Quick Reference

### Endpoints Summary

| Action | Method | Endpoint | Auth | Role |
|--------|--------|----------|------|------|
| Create patient record | POST | `/api/patients/` | ✅ | Provider |
| Get linking token | GET | `/api/patients/{id}/token/` | ✅ | Provider |
| Link account | POST | `/api/patients/link-account/` | ✅ | Patient |
| Get my record | GET | `/api/patients/me/` | ✅ | Patient |
| Create service | POST | `/api/services/` | ✅ | Doctor/Clinic/Admin |
| Attach service (doctor) | POST | `/api/services/doctor-services/` | ✅ | Doctor |
| Attach service (nurse) | POST | `/api/services/nurse-services/` | ✅ | Nurse |
| Create specialty | POST | `/api/specialties/` | ✅ | Doctor/Clinic/Admin |
| Attach specialty | POST | `/api/specialties/doctor-specialties/` | ✅ | Doctor |

### Role Capabilities

| Capability | Patient | Doctor | Nurse | Clinic | Lab | VTC |
|------------|---------|--------|-------|--------|-----|-----|
| Create patient record | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Link account | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Create service | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Attach service | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Create specialty | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Attach specialty | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
