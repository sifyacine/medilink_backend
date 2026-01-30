# MediLink Appointments API Documentation

## Overview

This documentation covers the complete appointment flow between **Patients** (mobile app users) and **Providers** (doctors, nurses, etc.). The system supports:

- Patients booking appointments with providers
- Providers accepting, rejecting, or modifying appointments
- Automatic patient linking after appointment completion
- Full appointment lifecycle management

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Appointment Flow Overview](#appointment-flow-overview)
4. [Appointment Statuses](#appointment-statuses)
5. [Patient Endpoints](#patient-endpoints)
   - [Create Appointment Request](#1-create-appointment-request-patient)
   - [View My Appointments](#2-view-my-appointments-patient)
   - [Cancel Appointment](#3-cancel-appointment-patient)
6. [Provider Endpoints](#provider-endpoints)
   - [View Appointment Requests](#4-view-appointment-requests-provider)
   - [Confirm Appointment](#5-confirm-appointment-provider)
   - [Reject Appointment](#6-reject-appointment-provider)
   - [Update Appointment](#7-update-appointment-provider)
   - [Complete Appointment](#8-complete-appointment-provider)
   - [Mark No-Show](#9-mark-no-show-provider)
7. [Available Slots](#available-slots)
8. [Appointment Choices](#appointment-choices)
9. [Error Handling](#error-handling)
10. [Mobile Integration Examples](#mobile-integration-examples)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

---

## Authentication

All appointment endpoints require authentication:

```
Authorization: Token <your_token_here>
```

---

## Appointment Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         APPOINTMENT FLOW                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PATIENT (Mobile App)                    PROVIDER (Doctor/Nurse)                │
│  ─────────────────────                   ──────────────────────                 │
│                                                                                 │
│  1. Browse providers                                                            │
│     └─▶ GET /api/provider/list/                                                │
│                                                                                 │
│  2. Check available slots                                                       │
│     └─▶ GET /api/available-slots/?provider=<id>&date=2026-02-01               │
│                                                                                 │
│  3. Create appointment request           4. View pending requests              │
│     └─▶ POST /api/appointments/              └─▶ GET /api/appointments/        │
│         {                                        ?status=PENDING               │
│           "provider": "<provider_id>",                                         │
│           "scheduled_date": "2026-02-01",   5a. CONFIRM appointment            │
│           "scheduled_time": "10:00",            └─▶ POST /appointments/{id}/   │
│           "reason": "Check-up" (optional)           confirm/                   │
│         }                                                                       │
│         Status: PENDING ──────────────────▶  5b. REJECT appointment            │
│                                                  └─▶ POST /appointments/{id}/  │
│                                                      reject/                   │
│                                                      {"rejection_reason": ".."}│
│                                                                                 │
│  6. Receive notification                 5c. UPDATE & CONFIRM                  │
│     └─▶ Check status via                     └─▶ PATCH /appointments/{id}/     │
│         GET /api/appointments/                   + POST .../confirm/           │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ If CONFIRMED: Patient attends appointment                               │   │
│  │                                                                         │   │
│  │ 7. Provider completes appointment                                       │   │
│  │    └─▶ POST /api/appointments/{id}/complete/                           │   │
│  │                                                                         │   │
│  │ 8. Patient becomes part of provider's patient list (automatic)         │   │
│  │    └─▶ PatientRecord linked to provider for future visits              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Appointment Statuses

| Status | Description | Who Can Trigger |
|--------|-------------|-----------------|
| `PENDING` | Initial state when patient creates request | System (on creation) |
| `CONFIRMED` | Provider accepted the appointment | Provider only |
| `REJECTED` | Provider rejected the appointment | Provider only |
| `CANCELLED` | Appointment was cancelled | Patient or Provider |
| `COMPLETED` | Appointment was successfully completed | Provider only |
| `NO_SHOW` | Patient didn't show up | Provider only |
| `RESCHEDULED` | Appointment was rescheduled | Provider (typically) |

### Status Transitions

```
                    ┌──────────────┐
                    │   PENDING    │ ◀── Created by Patient
                    └──────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │  CONFIRMED   │ │   REJECTED   │ │  CANCELLED   │
   └──────────────┘ └──────────────┘ └──────────────┘
          │
          ├─────────────────┬─────────────────┐
          ▼                 ▼                 ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │  COMPLETED   │  │   NO_SHOW    │  │  CANCELLED   │
   └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Patient Endpoints

### 1. Create Appointment Request (Patient)

Patient sends an appointment request to a provider.

**Endpoint:** `POST /api/appointments/`

**Headers:**
```
Authorization: Token <patient_token>
Content-Type: application/json
```

**Minimal Request (Patient just selects provider, date, time):**
```json
{
    "provider": "uuid-of-provider",
    "scheduled_date": "2026-02-01",
    "scheduled_time": "10:00"
}
```

**Full Request (with optional fields):**
```json
{
    "provider": "uuid-of-provider",
    "scheduled_date": "2026-02-01",
    "scheduled_time": "10:00",
    "duration_minutes": 30,
    "location_type": "CLINIC",
    "reason": "Annual check-up and blood pressure monitoring",
    "notes": "I've been feeling dizzy lately"
}
```

#### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `provider` | UUID | ✅ Yes | - | Provider's UUID |
| `scheduled_date` | date | ✅ Yes | - | Date (YYYY-MM-DD) |
| `scheduled_time` | time | ✅ Yes | - | Time (HH:MM) |
| `duration_minutes` | integer | ❌ No | 30 | Duration in minutes |
| `location_type` | string | ❌ No | `"CLINIC"` | `CLINIC`, `HOME`, `ONLINE` |
| `reason` | string | ❌ No | - | Reason for visit |
| `notes` | string | ❌ No | - | Additional notes |
| `home_address` | UUID | ❌ No* | - | *Required if `location_type` is `HOME` |
| `service` | UUID | ❌ No | - | Specific service requested |

> **Note:** The `patient_user` field is automatically set from the authenticated user's token.

#### Success Response (201 Created)

```json
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "provider": "uuid-of-provider",
    "provider_name": "Dr. Ahmed Benali",
    "provider_email": "doctor@medilink.com",
    "provider_type": "DOCTOR",
    "patient_user": 3,
    "patient_record": null,
    "patient_name": "Yacine Sif",
    "patient_email": "yacinesif@gmail.com",
    "patient_phone": "+213555123456",
    "service": null,
    "service_name": null,
    "scheduled_date": "2026-02-01",
    "scheduled_time": "10:00:00",
    "duration_minutes": 30,
    "location_type": "CLINIC",
    "location_type_display": "At Clinic",
    "status": "PENDING",
    "status_display": "Pending",
    "reason": "Annual check-up",
    "notes": "",
    "created_by": 3,
    "created_by_name": "Yacine Sif",
    "is_upcoming": true,
    "is_past": false,
    "created_at": "2026-01-30T16:00:00Z",
    "updated_at": "2026-01-30T16:00:00Z"
}
```

#### Error Responses

**400 Bad Request - Time slot not available:**
```json
{
    "scheduled_time": ["Provider is not available at this time."]
}
```

**400 Bad Request - Past date:**
```json
{
    "scheduled_date": ["Appointment cannot be scheduled in the past."]
}
```

**400 Bad Request - Missing home address for home visit:**
```json
{
    "home_address": ["Home address is required for home visit appointments."]
}
```

---

### 2. View My Appointments (Patient)

Get all appointments for the logged-in patient.

**Endpoint:** `GET /api/appointments/`

**Headers:**
```
Authorization: Token <patient_token>
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `PENDING`, `CONFIRMED`, etc. |
| `date_from` | date | Start date filter |
| `date_to` | date | End date filter |

**Example Requests:**
```
GET /api/appointments/
GET /api/appointments/?status=PENDING
GET /api/appointments/?status=CONFIRMED
GET /api/appointments/?date_from=2026-02-01&date_to=2026-02-28
```

**Shortcut Endpoints:**
```
GET /api/appointments/upcoming/    # All upcoming appointments
GET /api/appointments/past/        # All past appointments
GET /api/appointments/today/       # Today's appointments
```

#### Success Response (200 OK)

```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "provider": "uuid-of-provider",
            "provider_name": "Dr. Ahmed Benali",
            "patient_name": "Yacine Sif",
            "service_name": null,
            "scheduled_date": "2026-02-01",
            "scheduled_time": "10:00:00",
            "duration_minutes": 30,
            "location_type": "CLINIC",
            "location_type_display": "At Clinic",
            "status": "PENDING",
            "status_display": "Pending",
            "reason": "Annual check-up",
            "is_upcoming": true,
            "created_at": "2026-01-30T16:00:00Z"
        },
        {
            "id": "b2c3d4e5-f6a7-8901-bcde-f23456789012",
            "provider": "uuid-of-nurse",
            "provider_name": "Marie Dupont",
            "patient_name": "Yacine Sif",
            "service_name": "Home Blood Pressure Check",
            "scheduled_date": "2026-02-05",
            "scheduled_time": "14:00:00",
            "duration_minutes": 30,
            "location_type": "HOME",
            "location_type_display": "Home Visit",
            "status": "CONFIRMED",
            "status_display": "Confirmed",
            "reason": "Blood pressure monitoring",
            "is_upcoming": true,
            "created_at": "2026-01-28T10:00:00Z"
        }
    ]
}
```

---

### 3. Cancel Appointment (Patient)

Patient cancels their appointment.

**Endpoint:** `POST /api/appointments/{id}/cancel/`

**Headers:**
```
Authorization: Token <patient_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "reason": "PATIENT_REQUEST",
    "notes": "I need to reschedule due to work conflict"
}
```

#### Cancellation Reasons

| Value | Description |
|-------|-------------|
| `PATIENT_REQUEST` | Patient requested cancellation |
| `EMERGENCY` | Emergency situation |
| `RESCHEDULED` | Will reschedule |
| `OTHER` | Other reason |

#### Success Response (200 OK)

```json
{
    "status": "cancelled",
    "message": "Appointment cancelled successfully",
    "data": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "CANCELLED",
        "status_display": "Cancelled",
        "cancelled_by": 3,
        "cancelled_by_name": "Yacine Sif",
        "cancelled_at": "2026-01-30T18:00:00Z",
        "cancellation_reason": "PATIENT_REQUEST",
        "cancellation_notes": "I need to reschedule due to work conflict"
    }
}
```

---

## Provider Endpoints

### 4. View Appointment Requests (Provider)

Get all appointments for the logged-in provider.

**Endpoint:** `GET /api/appointments/`

**Headers:**
```
Authorization: Token <provider_token>
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `date_from` | date | Start date |
| `date_to` | date | End date |
| `patient` | integer | Filter by patient ID |
| `search` | string | Search in reason/notes |

**Example: Get all pending requests:**
```
GET /api/appointments/?status=PENDING
```

#### Success Response (200 OK)

```json
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "provider": "uuid-of-provider",
            "provider_name": "Dr. Ahmed Benali",
            "patient_name": "Yacine Sif",
            "service_name": null,
            "scheduled_date": "2026-02-01",
            "scheduled_time": "10:00:00",
            "duration_minutes": 30,
            "location_type": "CLINIC",
            "location_type_display": "At Clinic",
            "status": "PENDING",
            "status_display": "Pending",
            "reason": "Annual check-up",
            "is_upcoming": true,
            "created_at": "2026-01-30T16:00:00Z"
        }
    ]
}
```

---

### 5. Confirm Appointment (Provider)

Provider accepts a patient's appointment request.

**Endpoint:** `POST /api/appointments/{id}/confirm/`

**Headers:**
```
Authorization: Token <provider_token>
Content-Type: application/json
```

**Request Body (optional):**
```json
{
    "notes": "Please arrive 10 minutes early"
}
```

#### Success Response (200 OK)

```json
{
    "status": "confirmed",
    "message": "Appointment confirmed successfully",
    "data": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "CONFIRMED",
        "status_display": "Confirmed",
        "confirmed_at": "2026-01-30T17:00:00Z",
        "scheduled_date": "2026-02-01",
        "scheduled_time": "10:00:00"
    }
}
```

---

### 6. Reject Appointment (Provider)

Provider rejects a patient's appointment request.

**Endpoint:** `POST /api/appointments/{id}/reject/`

**Headers:**
```
Authorization: Token <provider_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "rejection_reason": "I am fully booked on this day. Please try another date."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rejection_reason` | string | ✅ Yes | Reason for rejecting |

#### Success Response (200 OK)

```json
{
    "status": "rejected",
    "message": "Appointment rejected successfully",
    "data": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "REJECTED",
        "status_display": "Rejected",
        "rejection_reason": "I am fully booked on this day. Please try another date.",
        "rejected_at": "2026-01-30T17:00:00Z"
    }
}
```

---

### 7. Update Appointment (Provider)

Provider can update appointment details (reschedule time, add notes, etc.).

**Endpoint:** `PATCH /api/appointments/{id}/`

**Headers:**
```
Authorization: Token <provider_token>
Content-Type: application/json
```

**Request Body:**
```json
{
    "scheduled_date": "2026-02-02",
    "scheduled_time": "11:00",
    "duration_minutes": 45,
    "provider_notes": "Patient needs extended consultation"
}
```

#### Updatable Fields

| Field | Description |
|-------|-------------|
| `scheduled_date` | Reschedule to new date |
| `scheduled_time` | Reschedule to new time |
| `duration_minutes` | Change duration |
| `location_type` | Change location type |
| `meeting_link` | Add/update video call link (for ONLINE) |
| `reason` | Update reason |
| `notes` | Update notes |
| `provider_notes` | Private notes (only visible to provider) |

> **Important:** After updating, provider should call `/confirm/` to confirm the changes.

---

### 8. Complete Appointment (Provider)

Mark appointment as completed after the visit.

**Endpoint:** `POST /api/appointments/{id}/complete/`

**Headers:**
```
Authorization: Token <provider_token>
Content-Type: application/json
```

**Request Body (optional):**
```json
{
    "provider_notes": "Patient's blood pressure is normal. Recommended follow-up in 3 months."
}
```

#### Success Response (200 OK)

```json
{
    "status": "completed",
    "message": "Appointment marked as completed",
    "data": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "COMPLETED",
        "status_display": "Completed",
        "completed_at": "2026-02-01T10:45:00Z"
    }
}
```

> **Note:** When an appointment is completed, the patient automatically becomes part of the provider's patient list for future reference.

---

### 9. Mark No-Show (Provider)

Mark when patient doesn't show up for appointment.

**Endpoint:** `POST /api/appointments/{id}/no_show/`

**Headers:**
```
Authorization: Token <provider_token>
```

#### Success Response (200 OK)

```json
{
    "status": "no_show",
    "message": "Appointment marked as no-show",
    "data": {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": "NO_SHOW",
        "status_display": "No Show"
    }
}
```

---

## Available Slots

Check available time slots for a provider on a specific date.

**Endpoint:** `GET /api/available-slots/`

**Headers:**
```
Authorization: Token <token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | UUID | ✅ Yes | Provider's UUID |
| `date` | date | ✅ Yes | Date to check (YYYY-MM-DD) |
| `location_type` | string | ❌ No | `CLINIC`, `HOME`, `ONLINE` |

**Example:**
```
GET /api/available-slots/?provider=uuid-here&date=2026-02-01
```

#### Success Response (200 OK)

```json
{
    "provider": "uuid-of-provider",
    "date": "2026-02-01",
    "location_type": "ALL",
    "slots": [
        {
            "start_time": "09:00",
            "end_time": "09:30",
            "is_available": true,
            "location_type": "ALL"
        },
        {
            "start_time": "09:30",
            "end_time": "10:00",
            "is_available": true,
            "location_type": "ALL"
        },
        {
            "start_time": "10:00",
            "end_time": "10:30",
            "is_available": false,
            "location_type": "ALL",
            "reason": "Already booked"
        },
        {
            "start_time": "10:30",
            "end_time": "11:00",
            "is_available": true,
            "location_type": "ALL"
        }
    ]
}
```

---

## Appointment Choices

Get available options for appointment creation.

**Endpoint:** `GET /api/appointment-choices/`

#### Success Response (200 OK)

```json
{
    "statuses": [
        {"value": "PENDING", "label": "Pending"},
        {"value": "CONFIRMED", "label": "Confirmed"},
        {"value": "REJECTED", "label": "Rejected"},
        {"value": "CANCELLED", "label": "Cancelled"},
        {"value": "COMPLETED", "label": "Completed"},
        {"value": "NO_SHOW", "label": "No Show"},
        {"value": "RESCHEDULED", "label": "Rescheduled"}
    ],
    "location_types": [
        {"value": "CLINIC", "label": "At Clinic"},
        {"value": "HOME", "label": "Home Visit"},
        {"value": "ONLINE", "label": "Online/Video Call"}
    ],
    "cancellation_reasons": [
        {"value": "PATIENT_REQUEST", "label": "Patient Request"},
        {"value": "PROVIDER_UNAVAILABLE", "label": "Provider Unavailable"},
        {"value": "EMERGENCY", "label": "Emergency"},
        {"value": "RESCHEDULED", "label": "Rescheduled"},
        {"value": "NO_RESPONSE", "label": "No Response"},
        {"value": "OTHER", "label": "Other"}
    ]
}
```

---

## Error Handling

### Common Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 400 | Bad Request - Invalid data or validation error |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Not allowed (e.g., patient trying to confirm) |
| 404 | Not Found - Appointment doesn't exist |

### Error Response Format

```json
{
    "error": "Human-readable error message"
}
```

Or for validation errors:

```json
{
    "field_name": ["List of validation errors"]
}
```

---

## Mobile Integration Examples

### Flutter/Dart

```dart
import 'package:dio/dio.dart';

class AppointmentService {
  final Dio _dio;
  final String _baseUrl = 'https://dzmedilink.duckdns.org/api';
  
  AppointmentService(String token) : _dio = Dio() {
    _dio.options.headers['Authorization'] = 'Token $token';
    _dio.options.headers['Content-Type'] = 'application/json';
  }
  
  // Patient: Create appointment request
  Future<Map<String, dynamic>> createAppointment({
    required String providerId,
    required String date,
    required String time,
    String? reason,
    String locationType = 'CLINIC',
  }) async {
    final response = await _dio.post('$_baseUrl/appointments/', data: {
      'provider': providerId,
      'scheduled_date': date,
      'scheduled_time': time,
      'location_type': locationType,
      if (reason != null) 'reason': reason,
    });
    return response.data;
  }
  
  // Get appointments with optional filters
  Future<List<dynamic>> getAppointments({String? status}) async {
    String url = '$_baseUrl/appointments/';
    if (status != null) url += '?status=$status';
    
    final response = await _dio.get(url);
    return response.data['results'];
  }
  
  // Get upcoming appointments
  Future<List<dynamic>> getUpcomingAppointments() async {
    final response = await _dio.get('$_baseUrl/appointments/upcoming/');
    return response.data['results'] ?? response.data;
  }
  
  // Patient: Cancel appointment
  Future<Map<String, dynamic>> cancelAppointment(
    String appointmentId, {
    String reason = 'PATIENT_REQUEST',
    String? notes,
  }) async {
    final response = await _dio.post(
      '$_baseUrl/appointments/$appointmentId/cancel/',
      data: {
        'reason': reason,
        if (notes != null) 'notes': notes,
      },
    );
    return response.data;
  }
  
  // Provider: Confirm appointment
  Future<Map<String, dynamic>> confirmAppointment(
    String appointmentId, {
    String? notes,
  }) async {
    final response = await _dio.post(
      '$_baseUrl/appointments/$appointmentId/confirm/',
      data: {
        if (notes != null) 'notes': notes,
      },
    );
    return response.data;
  }
  
  // Provider: Reject appointment
  Future<Map<String, dynamic>> rejectAppointment(
    String appointmentId,
    String rejectionReason,
  ) async {
    final response = await _dio.post(
      '$_baseUrl/appointments/$appointmentId/reject/',
      data: {'rejection_reason': rejectionReason},
    );
    return response.data;
  }
  
  // Provider: Update appointment (reschedule)
  Future<Map<String, dynamic>> updateAppointment(
    String appointmentId, {
    String? date,
    String? time,
    int? durationMinutes,
    String? providerNotes,
  }) async {
    final response = await _dio.patch(
      '$_baseUrl/appointments/$appointmentId/',
      data: {
        if (date != null) 'scheduled_date': date,
        if (time != null) 'scheduled_time': time,
        if (durationMinutes != null) 'duration_minutes': durationMinutes,
        if (providerNotes != null) 'provider_notes': providerNotes,
      },
    );
    return response.data;
  }
  
  // Provider: Complete appointment
  Future<Map<String, dynamic>> completeAppointment(
    String appointmentId, {
    String? providerNotes,
  }) async {
    final response = await _dio.post(
      '$_baseUrl/appointments/$appointmentId/complete/',
      data: {
        if (providerNotes != null) 'provider_notes': providerNotes,
      },
    );
    return response.data;
  }
  
  // Get available time slots
  Future<Map<String, dynamic>> getAvailableSlots(
    String providerId,
    String date, {
    String? locationType,
  }) async {
    String url = '$_baseUrl/available-slots/?provider=$providerId&date=$date';
    if (locationType != null) url += '&location_type=$locationType';
    
    final response = await _dio.get(url);
    return response.data;
  }
}

// Usage Example
void main() async {
  final token = 'your-auth-token';
  final appointmentService = AppointmentService(token);
  
  // Patient: Book an appointment
  try {
    final appointment = await appointmentService.createAppointment(
      providerId: 'provider-uuid-here',
      date: '2026-02-01',
      time: '10:00',
      reason: 'Annual check-up',
    );
    print('Appointment created: ${appointment['id']}');
    print('Status: ${appointment['status']}'); // PENDING
  } catch (e) {
    print('Error creating appointment: $e');
  }
  
  // Patient: Get my pending appointments
  try {
    final pending = await appointmentService.getAppointments(status: 'PENDING');
    print('Pending appointments: ${pending.length}');
  } catch (e) {
    print('Error: $e');
  }
  
  // Provider: Get pending requests and confirm
  try {
    final requests = await appointmentService.getAppointments(status: 'PENDING');
    for (var request in requests) {
      // Option 1: Confirm as-is
      await appointmentService.confirmAppointment(request['id']);
      
      // Option 2: Reschedule then confirm
      // await appointmentService.updateAppointment(
      //   request['id'],
      //   time: '14:00',
      // );
      // await appointmentService.confirmAppointment(request['id']);
    }
  } catch (e) {
    print('Error: $e');
  }
}
```

---

## Summary of Endpoints

| Action | Method | Endpoint | Who |
|--------|--------|----------|-----|
| Create appointment | POST | `/api/appointments/` | Patient |
| List appointments | GET | `/api/appointments/` | Both |
| Get appointment details | GET | `/api/appointments/{id}/` | Both |
| Update appointment | PATCH | `/api/appointments/{id}/` | Provider |
| Confirm appointment | POST | `/api/appointments/{id}/confirm/` | Provider |
| Reject appointment | POST | `/api/appointments/{id}/reject/` | Provider |
| Cancel appointment | POST | `/api/appointments/{id}/cancel/` | Both |
| Complete appointment | POST | `/api/appointments/{id}/complete/` | Provider |
| Mark no-show | POST | `/api/appointments/{id}/no_show/` | Provider |
| Get upcoming | GET | `/api/appointments/upcoming/` | Both |
| Get past | GET | `/api/appointments/past/` | Both |
| Get today's | GET | `/api/appointments/today/` | Both |
| Get stats | GET | `/api/appointments/stats/` | Both |
| Get available slots | GET | `/api/available-slots/` | Both |
| Get choices | GET | `/api/appointment-choices/` | Both |

---

## Patient-Provider Relationship

When an appointment is **COMPLETED**:

1. If the patient doesn't have a `PatientRecord`, one can be created by the provider
2. The `PatientRecord` is linked to the provider via `ProviderPatientAccess`
3. Future appointments can reference this patient's medical history
4. The patient appears in the provider's patient list

This creates a persistent relationship where:
- Providers can see all their patients (those who have completed appointments)
- Patients can see their appointment history with each provider
- Medical records can be attached to completed appointments

---

*Last updated: January 30, 2026*
