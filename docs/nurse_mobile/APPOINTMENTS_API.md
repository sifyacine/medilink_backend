# Nurse Mobile App - Appointments API

## Overview

This documentation covers the **Appointments API** for the Nurse Mobile Application. Nurses can manage their appointment schedule, accept/reject patient requests, mark appointments as completed, handle home visits, and manage their availability.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Nurse Appointment Flow](#nurse-appointment-flow)
4. [Provider-Patient Relationship](#-provider-patient-relationship)
5. [My Appointments](#my-appointments)
   - [List All Appointments](#list-all-appointments)
   - [Get Appointment Details](#get-appointment-details)
   - [Filter & Search Appointments](#filter--search-appointments)
6. [Quick Access Endpoints](#quick-access-endpoints)
   - [Today's Appointments](#todays-appointments)
   - [Upcoming Appointments](#upcoming-appointments)
   - [Past Appointments](#past-appointments)
   - [This Week's Appointments](#this-weeks-appointments)
7. [Appointment Actions](#appointment-actions)
   - [Confirm Appointment](#confirm-appointment)
   - [Reject Appointment](#reject-appointment)
   - [Cancel Appointment](#cancel-appointment)
   - [Complete Appointment](#complete-appointment)
   - [Mark No-Show](#mark-no-show)
   - [Reschedule Appointment](#reschedule-appointment)
8. [Create Appointment for Patient](#create-appointment-for-patient)
9. [Appointment Services Management](#appointment-services-management)
10. [Appointment Statistics](#appointment-statistics)
11. [Availability Management](#availability-management)
    - [Get My Schedule](#get-my-schedule)
    - [Set Availability](#set-availability)
    - [Bulk Update Schedule](#bulk-update-schedule)
12. [Time Off Management](#time-off-management)
13. [Provider Schedule View](#provider-schedule-view)
14. [Error Handling](#error-handling)
15. [Mobile Integration Examples](#mobile-integration-examples)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

---

## Authentication

All endpoints require authentication. Include your token in every request:

```
Authorization: Token <your_token_here>
```

**Important:** Your provider account must be `APPROVED` to access appointment management features.

---

## Nurse Appointment Flow

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                         NURSE APPOINTMENT WORKFLOW                                 │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐   │
│  │                     INCOMING REQUESTS                                       │   │
│  │  Patient books ───▶ Notification ───▶ Review request (Status: PENDING)    │   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                            │
│                     ┌────────────────┴────────────────┐                          │
│                     ▼                                  ▼                          │
│             ┌──────────────┐                   ┌──────────────┐                   │
│             │   CONFIRM    │                   │    REJECT    │                   │
│             │  ✓ Accept    │                   │  ✗ Decline   │                   │
│             │    request   │                   │    request   │                   │
│             └──────┬───────┘                   └──────────────┘                   │
│                    │                                                              │
│                    ▼                                                              │
│  ┌────────────────────────────────────────────────────────────────────────────┐   │
│  │                     DURING APPOINTMENT                                      │   │
│  │  • View patient details  • Access medical records  • Navigate to location  │   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                    │                                                              │
│       ┌────────────┼────────────┬────────────┐                                   │
│       ▼            ▼            ▼            ▼                                   │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                              │
│ │ COMPLETE │ │ NO_SHOW  │ │  CANCEL  │ │RESCHEDULE│                              │
│ │ ✓ Done   │ │ Patient  │ │ Cancel   │ │ Move to  │                              │
│ │          │ │ absent   │ │ visit    │ │ new time │                              │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘                              │
│                                                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Provider-Patient Relationship

> **⚠️ IMPORTANT: Automatic Patient Record Creation on Confirmation**
>
> When you **confirm** (or **reschedule**) an appointment, the system automatically establishes a nurse-patient relationship. This is crucial for care continuity:

### What Happens When You Confirm an Appointment

1. **Patient Record Created**: If the patient doesn't have a record yet, one is automatically created using their account information.

2. **Access Granted**: You are automatically granted **FULL access** to this patient's medical record:
   - View and update their emergency contacts
   - View and update allergies and chronic conditions
   - Access their medical history
   - Add notes about care provided

3. **Patient Added to Your List**: The patient now appears in your patient list.

### Managing Patient Medical Information

After an appointment is confirmed, you can update the patient's info:

```
PATCH /api/patients/{patient_id}/
```

**Updatable Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `emergency_contact_name` | string | Emergency contact person |
| `emergency_contact_phone` | string | Emergency phone number |
| `blood_type` | string | Blood type |
| `known_allergies` | text | Known allergies |
| `chronic_conditions` | text | Chronic conditions |
| `current_medications` | text | Current medications |
| `notes` | text | Additional notes |

**Example - Update After Home Visit:**
```json
{
    "current_medications": "Insulin 10 units twice daily, Metformin 500mg",
    "notes": "Patient managing diabetes well. Blood glucose stable."
}
```

> **💡 Note:** Both patients AND nurses can update this information. Keep it current for better care coordination.

---

## My Appointments

### List All Appointments

Get all appointments where you are the assigned provider.

```
GET /api/appointments/
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter: `PENDING`, `CONFIRMED`, `COMPLETED`, etc. |
| `date_from` | string | Start date (`YYYY-MM-DD`) |
| `date_to` | string | End date (`YYYY-MM-DD`) |
| `patient` | UUID | Filter by patient ID |
| `location_type` | string | `CLINIC`, `HOME`, `ONLINE` |
| `search` | string | Search in reason/notes |

### Response (200 OK)

```json
{
    "count": 25,
    "next": "https://dzmedilink.duckdns.org/api/appointments/?page=2",
    "previous": null,
    "results": [
        {
            "id": "appointment-uuid",
            "provider": "your-provider-uuid",
            "provider_name": "Nurse Fatima Zahra",
            "patient_name": "Ahmed Benali",
            "service_name": "Home Injection",
            "scheduled_date": "2026-02-03",
            "scheduled_time": "09:00:00",
            "duration_minutes": 30,
            "location_type": "HOME",
            "location_type_display": "Home Visit",
            "status": "PENDING",
            "status_display": "Pending",
            "reason": "Daily insulin injection",
            "is_upcoming": true,
            "allowed_actions": {
                "can_confirm": true,
                "can_reject": true,
                "can_cancel": true,
                "can_complete": false,
                "can_mark_no_show": false,
                "can_reschedule": true,
                "is_terminal": false
            },
            "created_at": "2026-02-02T08:00:00Z"
        }
    ]
}
```

### Get Appointment Details

```
GET /api/appointments/{id}/
```

### Response (200 OK)

```json
{
    "id": "appointment-uuid",
    "provider": "your-provider-uuid",
    "provider_name": "Nurse Fatima Zahra",
    "provider_email": "nurse@example.com",
    "provider_type": "NURSE",
    "patient_user": "patient-uuid",
    "patient_record": null,
    "patient_name": "Ahmed Benali",
    "patient_email": "ahmed@example.com",
    "patient_phone": "+213555123456",
    "service": "service-uuid",
    "service_name": "Home Injection",
    "service_description": "Professional injection service at home",
    "scheduled_date": "2026-02-03",
    "scheduled_time": "09:00:00",
    "duration_minutes": 30,
    "location_type": "HOME",
    "location_type_display": "Home Visit",
    "clinic_address": null,
    "home_address": {
        "id": "address-uuid",
        "street": "45 Rue des Jardins",
        "city": "Oran",
        "state": "Oran",
        "zip_code": "31000",
        "latitude": "35.6976",
        "longitude": "-0.6337",
        "notes": "Building A, 3rd floor, Apartment 12"
    },
    "meeting_link": null,
    "status": "CONFIRMED",
    "status_display": "Confirmed",
    "reason": "Daily insulin injection for diabetic patient",
    "notes": "Patient prefers morning visits",
    "provider_notes": "Bring extra supplies",
    "cancellation_reason": null,
    "cancellation_notes": null,
    "cancelled_by": null,
    "cancelled_by_name": null,
    "cancelled_at": null,
    "created_by": "patient-uuid",
    "created_by_name": "Ahmed Benali",
    "confirmed_at": "2026-02-02T10:00:00Z",
    "completed_at": null,
    "is_upcoming": true,
    "is_past": false,
    "allowed_actions": {
        "can_confirm": false,
        "can_reject": false,
        "can_cancel": true,
        "can_complete": true,
        "can_mark_no_show": true,
        "can_reschedule": true,
        "is_terminal": false
    },
    "created_at": "2026-02-02T08:00:00Z",
    "updated_at": "2026-02-02T10:00:00Z"
}
```

### Filter & Search Appointments

```
GET /api/appointments/search/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search in patient name, email, reason, notes |
| `status` | string | Filter by status |
| `date_from` | string | Start date |
| `date_to` | string | End date |
| `location_type` | string | Filter by location type |
| `created_by_role` | string | `PATIENT`, `PROVIDER`, `ADMIN` |

---

## Quick Access Endpoints

### Today's Appointments

```
GET /api/appointments/today/
```

### Response

```json
[
    {
        "id": "uuid",
        "patient_name": "Ahmed Benali",
        "scheduled_time": "09:00:00",
        "location_type": "HOME",
        "status": "CONFIRMED",
        "home_address": {...}
    },
    {
        "id": "uuid",
        "patient_name": "Fatima Cherif",
        "scheduled_time": "11:00:00",
        "location_type": "HOME",
        "status": "PENDING"
    }
]
```

### Upcoming Appointments

```
GET /api/appointments/upcoming/
```

Returns `PENDING` and `CONFIRMED` appointments from today onwards.

### Past Appointments

```
GET /api/appointments/past/
```

Returns `COMPLETED`, `CANCELLED`, and `NO_SHOW` appointments.

### This Week's Appointments

```
GET /api/appointments/week/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `week_offset` | integer | 0 = this week, 1 = next week, -1 = last week |

### Response

```json
{
    "week_start": "2026-02-02",
    "week_end": "2026-02-08",
    "appointments": [
        {
            "id": "uuid",
            "patient_name": "Ahmed Benali",
            "scheduled_date": "2026-02-03",
            "scheduled_time": "09:00:00",
            "status": "CONFIRMED"
        }
    ]
}
```

---

## Appointment Actions

### Confirm Appointment

Accept a patient's appointment request.

```
POST /api/appointments/{id}/confirm/
```

#### Request Body (Optional)

```json
{
    "notes": "Confirmed. Will bring all necessary supplies."
}
```

#### Response (200 OK)

```json
{
    "status": "confirmed",
    "message": "Appointment confirmed successfully",
    "data": {
        "id": "appointment-uuid",
        "status": "CONFIRMED",
        "status_display": "Confirmed",
        "confirmed_at": "2026-02-02T10:00:00Z",
        "provider_notes": "Confirmed. Will bring all necessary supplies."
    }
}
```

### Reject Appointment

Decline a patient's appointment request.

```
POST /api/appointments/{id}/reject/
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rejection_reason` | string | ✅ | Reason for rejection |

```json
{
    "rejection_reason": "Not available on this date. Please reschedule to next week."
}
```

#### Response (200 OK)

```json
{
    "status": "rejected",
    "message": "Appointment rejected successfully",
    "data": {
        "id": "appointment-uuid",
        "status": "REJECTED",
        "status_display": "Rejected",
        "rejection_reason": "Not available on this date. Please reschedule to next week.",
        "rejected_at": "2026-02-02T10:00:00Z"
    }
}
```

### Cancel Appointment

Cancel an appointment (as provider).

```
POST /api/appointments/{id}/cancel/
```

#### Request Body

```json
{
    "reason": "PROVIDER_UNAVAILABLE",
    "notes": "Emergency personal matter. Patient has been notified."
}
```

#### Cancellation Reasons

| Code | Description |
|------|-------------|
| `PATIENT_REQUEST` | Patient Request |
| `PROVIDER_UNAVAILABLE` | Provider Unavailable |
| `EMERGENCY` | Emergency |
| `RESCHEDULED` | Rescheduled |
| `NO_RESPONSE` | No Response |
| `OTHER` | Other |

#### Response (200 OK)

```json
{
    "status": "cancelled",
    "message": "Appointment cancelled successfully",
    "data": {
        "id": "appointment-uuid",
        "status": "CANCELLED",
        "cancellation_reason": "PROVIDER_UNAVAILABLE",
        "cancelled_at": "2026-02-02T10:00:00Z"
    }
}
```

### Complete Appointment

Mark an appointment as completed after the visit.

```
POST /api/appointments/{id}/complete/
```

#### Request Body (Optional)

```json
{
    "provider_notes": "Injection administered successfully. No adverse reactions observed. Next visit scheduled for tomorrow."
}
```

#### Response (200 OK)

```json
{
    "status": "completed",
    "message": "Appointment marked as completed",
    "data": {
        "id": "appointment-uuid",
        "status": "COMPLETED",
        "status_display": "Completed",
        "completed_at": "2026-02-03T09:30:00Z",
        "provider_notes": "Injection administered successfully..."
    }
}
```

### Mark No-Show

Mark when a patient doesn't show up for the appointment.

```
POST /api/appointments/{id}/no_show/
```

#### Response (200 OK)

```json
{
    "status": "no_show",
    "message": "Appointment marked as no-show",
    "data": {
        "id": "appointment-uuid",
        "status": "NO_SHOW",
        "status_display": "No Show"
    }
}
```

### Reschedule Appointment

Move an appointment to a new date/time.

```
POST /api/appointments/{id}/reschedule/
```

#### Request Body

```json
{
    "scheduled_date": "2026-02-05",
    "scheduled_time": "10:00",
    "notes": "Rescheduled due to weather conditions"
}
```

#### Response (200 OK)

```json
{
    "status": "rescheduled",
    "message": "Appointment rescheduled successfully",
    "data": {
        "id": "new-appointment-uuid",
        "scheduled_date": "2026-02-05",
        "scheduled_time": "10:00:00",
        "status": "PENDING"
    }
}
```

---

## Create Appointment for Patient

Nurses can create appointments for patients (useful for recurring visits).

### Endpoint

```
POST /api/appointments/
```

### For Registered Patient

```json
{
    "patient_user": "patient-user-uuid",
    "scheduled_date": "2026-02-04",
    "scheduled_time": "09:00",
    "duration_minutes": 30,
    "location_type": "HOME",
    "home_address": "patient-address-uuid",
    "service": "service-uuid",
    "reason": "Daily insulin injection",
    "notes": "Part of regular care plan"
}
```

### For Unregistered Patient (using PatientRecord)

```json
{
    "patient_record": "patient-record-uuid",
    "scheduled_date": "2026-02-04",
    "scheduled_time": "09:00",
    "duration_minutes": 30,
    "location_type": "HOME",
    "reason": "Wound dressing change"
}
```

### Response (201 Created)

```json
{
    "id": "new-appointment-uuid",
    "provider": "your-provider-uuid",
    "patient_name": "Ahmed Benali",
    "scheduled_date": "2026-02-04",
    "scheduled_time": "09:00:00",
    "status": "CONFIRMED",
    "created_by_role": "PROVIDER"
}
```

**Note:** When a nurse creates an appointment, it can be auto-confirmed based on settings.

---

## Appointment Services Management

### View Attached Services

```
GET /api/appointments/{id}/services/
```

### Response

```json
{
    "appointment_id": "appointment-uuid",
    "services": [
        {
            "id": "apt-service-uuid",
            "service": {
                "id": "service-uuid",
                "name": "Insulin Injection",
                "price": "500.00",
                "currency": "DZD"
            },
            "notes": "",
            "created_at": "2026-02-02T10:00:00Z"
        }
    ]
}
```

### Attach Services

```
POST /api/appointments/{id}/services/
```

#### Request Body

```json
{
    "service_ids": ["service-uuid-1", "service-uuid-2"]
}
```

### Remove Service

```
DELETE /api/appointments/{id}/services/{service_id}/
```

---

## Appointment Statistics

```
GET /api/appointments/stats/
```

### Response

```json
{
    "total": 150,
    "pending": 5,
    "confirmed": 8,
    "completed": 130,
    "cancelled": 5,
    "no_show": 2,
    "today": 3,
    "upcoming": 13
}
```

---

## Availability Management

### Get My Schedule

View your current weekly availability.

```
GET /api/provider-availability/my_schedule/
```

### Response

```json
[
    {
        "id": "slot-uuid",
        "provider": "your-provider-uuid",
        "day_of_week": 0,
        "day_of_week_display": "Monday",
        "start_time": "08:00:00",
        "end_time": "12:00:00",
        "is_active": true,
        "location_type": "ALL",
        "max_appointments": 1
    },
    {
        "id": "slot-uuid",
        "provider": "your-provider-uuid",
        "day_of_week": 0,
        "day_of_week_display": "Monday",
        "start_time": "14:00:00",
        "end_time": "18:00:00",
        "is_active": true,
        "location_type": "HOME",
        "max_appointments": 1
    }
]
```

### Set Availability

Create a new availability slot.

```
POST /api/provider-availability/
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `day_of_week` | integer | ✅ | 0=Monday, 1=Tuesday, ..., 6=Sunday |
| `start_time` | string | ✅ | Start time (`HH:MM`) |
| `end_time` | string | ✅ | End time (`HH:MM`) |
| `is_active` | boolean | ❌ | Active slot (default: true) |
| `location_type` | string | ❌ | `CLINIC`, `HOME`, `ONLINE`, `ALL` |
| `max_appointments` | integer | ❌ | Max concurrent appointments |

```json
{
    "day_of_week": 1,
    "start_time": "09:00",
    "end_time": "17:00",
    "is_active": true,
    "location_type": "HOME",
    "max_appointments": 1
}
```

### Update Availability Slot

```
PATCH /api/provider-availability/{id}/
```

### Delete Availability Slot

```
DELETE /api/provider-availability/{id}/
```

### Bulk Update Schedule

Replace entire weekly schedule.

```
POST /api/provider-availability/bulk_update/
```

#### Request Body

```json
[
    {
        "day_of_week": 0,
        "start_time": "08:00",
        "end_time": "12:00",
        "location_type": "HOME"
    },
    {
        "day_of_week": 0,
        "start_time": "14:00",
        "end_time": "18:00",
        "location_type": "HOME"
    },
    {
        "day_of_week": 1,
        "start_time": "08:00",
        "end_time": "17:00",
        "location_type": "HOME"
    },
    {
        "day_of_week": 2,
        "start_time": "08:00",
        "end_time": "17:00",
        "location_type": "HOME"
    },
    {
        "day_of_week": 3,
        "start_time": "08:00",
        "end_time": "17:00",
        "location_type": "HOME"
    },
    {
        "day_of_week": 4,
        "start_time": "08:00",
        "end_time": "12:00",
        "location_type": "HOME"
    }
]
```

---

## Time Off Management

### List My Time Off

```
GET /api/provider-time-off/
```

### Response

```json
[
    {
        "id": "time-off-uuid",
        "provider": "your-provider-uuid",
        "start_datetime": "2026-02-15T00:00:00Z",
        "end_datetime": "2026-02-20T23:59:00Z",
        "reason": "Family vacation",
        "is_recurring_annual": false
    }
]
```

### Create Time Off

```
POST /api/provider-time-off/
```

#### Request Body

```json
{
    "start_datetime": "2026-02-15T00:00:00Z",
    "end_datetime": "2026-02-20T23:59:00Z",
    "reason": "Family vacation",
    "is_recurring_annual": false
}
```

### Get Upcoming Time Off

```
GET /api/provider-time-off/upcoming/
```

### Delete Time Off

```
DELETE /api/provider-time-off/{id}/
```

---

## Provider Schedule View

Get complete schedule for a date range.

```
GET /api/provider-schedule/
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | Start date (`YYYY-MM-DD`) |
| `end_date` | string | End date (`YYYY-MM-DD`) |

### Response

```json
{
    "provider": "your-provider-uuid",
    "start_date": "2026-02-02",
    "end_date": "2026-02-08",
    "availability": [
        {
            "day_of_week": 0,
            "day_of_week_display": "Monday",
            "start_time": "08:00:00",
            "end_time": "17:00:00"
        }
    ],
    "time_off": [],
    "appointments": [
        {
            "id": "uuid",
            "scheduled_date": "2026-02-03",
            "scheduled_time": "09:00:00",
            "patient_name": "Ahmed Benali",
            "status": "CONFIRMED"
        }
    ]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Validation error |
| 401 | Unauthorized - Invalid/missing token |
| 403 | Forbidden - Not your appointment / Not approved |
| 404 | Not Found |

### Common Errors

**Cannot Confirm:**
```json
{
    "error": "Cannot confirm appointment with status COMPLETED."
}
```

**Missing Rejection Reason:**
```json
{
    "error": "Rejection reason is required."
}
```

**Not Your Appointment:**
```json
{
    "error": "You can only modify your own appointments."
}
```

**Provider Not Approved:**
```json
{
    "error": "Your account is pending verification.",
    "provider_status": "PENDING"
}
```

---

## Mobile Integration Examples

### Flutter/Dart

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class NurseAppointmentService {
  static const String baseUrl = 'https://dzmedilink.duckdns.org/api';
  final String token;

  NurseAppointmentService(this.token);

  Map<String, String> get _headers => {
    'Authorization': 'Token $token',
    'Content-Type': 'application/json',
  };

  // Get today's appointments
  Future<List<Appointment>> getTodayAppointments() async {
    final response = await http.get(
      Uri.parse('$baseUrl/appointments/today/'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body);
      return data.map((a) => Appointment.fromJson(a)).toList();
    }
    throw ApiException('Failed to load today\'s appointments');
  }

  // Confirm appointment
  Future<Appointment> confirmAppointment(String id, {String? notes}) async {
    final body = notes != null ? {'notes': notes} : {};
    
    final response = await http.post(
      Uri.parse('$baseUrl/appointments/$id/confirm/'),
      headers: _headers,
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return Appointment.fromJson(data['data']);
    }
    throw ApiException(jsonDecode(response.body)['error'] ?? 'Failed to confirm');
  }

  // Reject appointment
  Future<Appointment> rejectAppointment(String id, String reason) async {
    final response = await http.post(
      Uri.parse('$baseUrl/appointments/$id/reject/'),
      headers: _headers,
      body: jsonEncode({'rejection_reason': reason}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return Appointment.fromJson(data['data']);
    }
    throw ApiException(jsonDecode(response.body)['error'] ?? 'Failed to reject');
  }

  // Complete appointment
  Future<Appointment> completeAppointment(String id, {String? notes}) async {
    final body = notes != null ? {'provider_notes': notes} : {};
    
    final response = await http.post(
      Uri.parse('$baseUrl/appointments/$id/complete/'),
      headers: _headers,
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return Appointment.fromJson(data['data']);
    }
    throw ApiException(jsonDecode(response.body)['error'] ?? 'Failed to complete');
  }

  // Mark no-show
  Future<Appointment> markNoShow(String id) async {
    final response = await http.post(
      Uri.parse('$baseUrl/appointments/$id/no_show/'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return Appointment.fromJson(data['data']);
    }
    throw ApiException('Failed to mark as no-show');
  }

  // Get my schedule (availability)
  Future<List<AvailabilitySlot>> getMySchedule() async {
    final response = await http.get(
      Uri.parse('$baseUrl/provider-availability/my_schedule/'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body);
      return data.map((s) => AvailabilitySlot.fromJson(s)).toList();
    }
    throw ApiException('Failed to load schedule');
  }

  // Update availability
  Future<List<AvailabilitySlot>> bulkUpdateSchedule(
    List<Map<String, dynamic>> slots
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/provider-availability/bulk_update/'),
      headers: _headers,
      body: jsonEncode(slots),
    );

    if (response.statusCode == 200) {
      final List data = jsonDecode(response.body);
      return data.map((s) => AvailabilitySlot.fromJson(s)).toList();
    }
    throw ApiException('Failed to update schedule');
  }

  // Create time off
  Future<TimeOff> createTimeOff({
    required DateTime startDate,
    required DateTime endDate,
    String? reason,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/provider-time-off/'),
      headers: _headers,
      body: jsonEncode({
        'start_datetime': startDate.toIso8601String(),
        'end_datetime': endDate.toIso8601String(),
        'reason': reason ?? '',
      }),
    );

    if (response.statusCode == 201) {
      return TimeOff.fromJson(jsonDecode(response.body));
    }
    throw ApiException('Failed to create time off');
  }

  // Get statistics
  Future<AppointmentStats> getStats() async {
    final response = await http.get(
      Uri.parse('$baseUrl/appointments/stats/'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return AppointmentStats.fromJson(jsonDecode(response.body));
    }
    throw ApiException('Failed to load stats');
  }
}

// Models
class Appointment {
  final String id;
  final String patientName;
  final String? patientPhone;
  final String scheduledDate;
  final String scheduledTime;
  final String status;
  final String locationType;
  final Map<String, dynamic>? homeAddress;
  final Map<String, bool> allowedActions;

  Appointment({
    required this.id,
    required this.patientName,
    this.patientPhone,
    required this.scheduledDate,
    required this.scheduledTime,
    required this.status,
    required this.locationType,
    this.homeAddress,
    required this.allowedActions,
  });

  factory Appointment.fromJson(Map<String, dynamic> json) => Appointment(
    id: json['id'],
    patientName: json['patient_name'],
    patientPhone: json['patient_phone'],
    scheduledDate: json['scheduled_date'],
    scheduledTime: json['scheduled_time'],
    status: json['status'],
    locationType: json['location_type'],
    homeAddress: json['home_address'],
    allowedActions: Map<String, bool>.from(json['allowed_actions'] ?? {}),
  );

  bool get canConfirm => allowedActions['can_confirm'] ?? false;
  bool get canReject => allowedActions['can_reject'] ?? false;
  bool get canComplete => allowedActions['can_complete'] ?? false;
  bool get canMarkNoShow => allowedActions['can_mark_no_show'] ?? false;
  
  bool get isHomeVisit => locationType == 'HOME';
  
  String? get navigationAddress {
    if (homeAddress == null) return null;
    return '${homeAddress!['street']}, ${homeAddress!['city']}';
  }
}

class AvailabilitySlot {
  final String id;
  final int dayOfWeek;
  final String dayOfWeekDisplay;
  final String startTime;
  final String endTime;
  final bool isActive;
  final String locationType;

  AvailabilitySlot({
    required this.id,
    required this.dayOfWeek,
    required this.dayOfWeekDisplay,
    required this.startTime,
    required this.endTime,
    required this.isActive,
    required this.locationType,
  });

  factory AvailabilitySlot.fromJson(Map<String, dynamic> json) => AvailabilitySlot(
    id: json['id'],
    dayOfWeek: json['day_of_week'],
    dayOfWeekDisplay: json['day_of_week_display'],
    startTime: json['start_time'],
    endTime: json['end_time'],
    isActive: json['is_active'],
    locationType: json['location_type'],
  );
}

class TimeOff {
  final String id;
  final DateTime startDatetime;
  final DateTime endDatetime;
  final String reason;

  TimeOff({
    required this.id,
    required this.startDatetime,
    required this.endDatetime,
    required this.reason,
  });

  factory TimeOff.fromJson(Map<String, dynamic> json) => TimeOff(
    id: json['id'],
    startDatetime: DateTime.parse(json['start_datetime']),
    endDatetime: DateTime.parse(json['end_datetime']),
    reason: json['reason'] ?? '',
  );
}

class AppointmentStats {
  final int total;
  final int pending;
  final int confirmed;
  final int completed;
  final int today;
  final int upcoming;

  AppointmentStats({
    required this.total,
    required this.pending,
    required this.confirmed,
    required this.completed,
    required this.today,
    required this.upcoming,
  });

  factory AppointmentStats.fromJson(Map<String, dynamic> json) => AppointmentStats(
    total: json['total'],
    pending: json['pending'],
    confirmed: json['confirmed'],
    completed: json['completed'],
    today: json['today'],
    upcoming: json['upcoming'],
  );
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  
  @override
  String toString() => message;
}
```

---

## Related Documentation

- [Authentication API](./AUTHENTICATION_API.md)
- [Nurse Requests API](../NURSE_REQUESTS_API.md)
- [Medical Records API](../MEDICAL_RECORDS_API.md)

---

## Support

For API issues or questions:
- API Documentation: https://dzmedilink.duckdns.org/docs
- Support Email: api-support@medilink.dz
