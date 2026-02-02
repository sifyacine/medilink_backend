# Patient Mobile App - Appointments API

## Overview

This documentation covers the **Appointments API** for the Patient Mobile Application. Patients can book appointments with healthcare providers, manage their bookings, view appointment history, and receive real-time status updates.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Appointment Flow](#appointment-flow)
4. [Provider-Patient Relationship](#-provider-patient-relationship)
5. [Browse Available Providers](#browse-available-providers)
6. [Check Available Slots](#check-available-slots)
7. [Book an Appointment](#book-an-appointment)
8. [My Appointments](#my-appointments)
   - [List All Appointments](#list-all-appointments)
   - [Get Appointment Details](#get-appointment-details)
   - [Upcoming Appointments](#upcoming-appointments)
   - [Past Appointments](#past-appointments)
   - [Today's Appointments](#todays-appointments)
9. [Appointment Statistics](#appointment-statistics)
10. [Cancel an Appointment](#cancel-an-appointment)
11. [Reschedule an Appointment](#reschedule-an-appointment)
12. [View Appointment Prescription](#view-appointment-prescription)
13. [Appointment Status Reference](#appointment-status-reference)
14. [Location Types](#location-types)
15. [Error Handling](#error-handling)
16. [Mobile Integration Examples](#mobile-integration-examples)

---

## Base URL

```
https://dzmedilink.duckdns.org/api/
```

---

## Authentication

All appointment endpoints require authentication. Include the token in every request:

```
Authorization: Token <your_token_here>
```

---

## Appointment Flow

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                         PATIENT APPOINTMENT FLOW                                   │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────────────────────────┐ │
│  │  1. Browse     │───▶│  2. Check      │───▶│  3. Book Appointment             │ │
│  │  Providers     │    │  Available     │    │     Status: PENDING              │ │
│  │                │    │  Slots         │    │                                  │ │
│  └────────────────┘    └────────────────┘    └──────────────────────────────────┘ │
│                                                          │                         │
│                                                          ▼                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐   │
│  │                     PROVIDER RESPONSE                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────────────────┐│   │
│  │  │  CONFIRMED  │    │  REJECTED   │    │  (Patient can CANCEL at any      ││   │
│  │  │  ✓ Ready    │    │  ✗ Request  │    │   point before completion)       ││   │
│  │  │    to visit │    │    denied   │    │                                  ││   │
│  │  └─────────────┘    └─────────────┘    └──────────────────────────────────┘│   │
│  └────────────────────────────────────────────────────────────────────────────┘   │
│                            │                                                       │
│                            ▼                                                       │
│         ┌─────────────────────────────────────────────────┐                       │
│         │  After Visit: COMPLETED or NO_SHOW              │                       │
│         └─────────────────────────────────────────────────┘                       │
│                                                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Provider-Patient Relationship

> **⚠️ IMPORTANT: What Happens When Your Appointment is Confirmed**
>
> When a provider **confirms** (or **reschedules**) your appointment, you automatically become a **patient of that provider**. This is a crucial business logic to understand:

### Automatic Actions on Appointment Confirmation

When your appointment status changes to `CONFIRMED` or `RESCHEDULED`:

1. **Patient Record Created**: If you don't already have a patient record in the system, one is automatically created for you using your account information (name, email, phone, date of birth).

2. **Provider Access Granted**: The provider who confirmed your appointment is automatically granted **FULL access** to your patient record. This allows them to:
   - View your medical history
   - Add medical records, prescriptions, and notes
   - Update your emergency contacts and allergies
   - View and manage your health information

3. **You Become Their Patient**: You are now officially a patient of this provider. They can see you in their patient list and manage your care.

### What This Means for You

| Before Confirmation | After Confirmation |
|--------------------|-------------------|
| You are just a user | You have a patient record |
| Provider cannot see your details | Provider has full access to your medical info |
| No medical records accessible | Provider can add/view medical records |
| No prescriptions can be issued | Provider can issue prescriptions |

### Access Levels

Providers can have different access levels to your patient record:

| Access Level | Description |
|--------------|-------------|
| `FULL` | Can view and edit everything (default for confirming provider) |
| `READ_ONLY` | Can only view medical records |
| `LIMITED` | Restricted access to specific records |

> **💡 Note:** You can control who has access to your medical records via share tokens and access management (see Authentication API documentation for details).

---

## Browse Available Providers

Before booking, patients can browse providers and view their public profiles.

### List Providers

```
GET /api/provider/public/
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `provider_type` | string | Filter by type: `DOCTOR`, `NURSE`, `CLINIC`, `LABORATORY` |
| `specialty` | UUID | Filter by specialty ID |
| `city` | string | Filter by city |
| `is_available` | boolean | Only show available providers |
| `search` | string | Search by name |

### Response

```json
{
    "count": 50,
    "next": "https://dzmedilink.duckdns.org/api/provider/public/?page=2",
    "previous": null,
    "results": [
        {
            "id": "uuid-here",
            "provider_type": "DOCTOR",
            "provider_type_display": "Doctor",
            "display_name": "Dr. Mohamed Kaddour",
            "first_name": "Mohamed",
            "last_name": "Kaddour",
            "profile_image": "https://dzmedilink.duckdns.org/media/doctors/photo.jpg",
            "specialties": [
                {
                    "id": "uuid",
                    "name": "Cardiology",
                    "name_ar": "أمراض القلب"
                }
            ],
            "years_of_experience": 15,
            "is_available": true,
            "is_home_service_available": true,
            "consultation_price": "3000.00",
            "currency": "DZD",
            "rating": 4.8,
            "review_count": 120,
            "address": {
                "city": "Algiers",
                "state": "Algiers"
            }
        }
    ]
}
```

### Get Provider Details

```
GET /api/provider/public/{provider_id}/
```

---

## Check Available Slots

Get available time slots for a specific provider on a given date.

### Endpoint

```
GET /api/available-slots/
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | UUID | ✅ | Provider ID |
| `date` | string | ✅ | Date in `YYYY-MM-DD` format |
| `duration_minutes` | integer | ❌ | Duration (default: 30) |
| `location_type` | string | ❌ | `CLINIC`, `HOME`, `ONLINE` (default: `CLINIC`) |

### Request Example

```
GET /api/available-slots/?provider=abc-123&date=2026-02-05&duration_minutes=30&location_type=CLINIC
```

### Response (200 OK)

```json
{
    "provider": "abc-123",
    "date": "2026-02-05",
    "duration_minutes": 30,
    "location_type": "CLINIC",
    "available_slots": [
        {
            "start_time": "08:00",
            "end_time": "08:30",
            "duration_minutes": 30
        },
        {
            "start_time": "08:30",
            "end_time": "09:00",
            "duration_minutes": 30
        },
        {
            "start_time": "09:00",
            "end_time": "09:30",
            "duration_minutes": 30
        },
        {
            "start_time": "10:00",
            "end_time": "10:30",
            "duration_minutes": 30
        }
    ]
}
```

**Note:** Gaps in slots indicate booked appointments or provider breaks.

---

## Book an Appointment

Create a new appointment with a provider.

### Endpoint

```
POST /api/appointments/
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | UUID | ✅ | Provider ID |
| `scheduled_date` | string | ✅ | Date (`YYYY-MM-DD`) |
| `scheduled_time` | string | ✅ | Time (`HH:MM`) |
| `duration_minutes` | integer | ❌ | Duration (default: 30) |
| `location_type` | string | ❌ | `CLINIC`, `HOME`, `ONLINE` |
| `service` | UUID | ❌ | Service ID if applicable |
| `home_address` | UUID | ❌ | Required for `HOME` visits |
| `reason` | string | ❌ | Reason for visit |
| `notes` | string | ❌ | Additional notes |

### Example: Book Clinic Appointment

```json
{
    "provider": "abc-123-provider-uuid",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "09:00",
    "duration_minutes": 30,
    "location_type": "CLINIC",
    "reason": "Regular checkup and blood pressure monitoring",
    "notes": "I've been experiencing occasional headaches"
}
```

### Example: Book Home Visit

```json
{
    "provider": "abc-123-provider-uuid",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "14:00",
    "duration_minutes": 45,
    "location_type": "HOME",
    "home_address": "my-address-uuid",
    "reason": "Home care for elderly parent"
}
```

### Example: Book Online Consultation

```json
{
    "provider": "abc-123-provider-uuid",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "16:00",
    "duration_minutes": 20,
    "location_type": "ONLINE",
    "reason": "Follow-up consultation"
}
```

### Success Response (201 Created)

```json
{
    "id": "appointment-uuid",
    "provider": "abc-123-provider-uuid",
    "provider_name": "Dr. Mohamed Kaddour",
    "provider_email": "doctor@example.com",
    "provider_type": "DOCTOR",
    "patient_user": "patient-uuid",
    "patient_name": "Ahmed Benali",
    "service": null,
    "service_name": null,
    "scheduled_date": "2026-02-05",
    "scheduled_time": "09:00:00",
    "duration_minutes": 30,
    "location_type": "CLINIC",
    "location_type_display": "At Clinic",
    "clinic_address": {
        "street": "123 Rue Didouche Mourad",
        "city": "Algiers",
        "state": "Algiers"
    },
    "status": "PENDING",
    "status_display": "Pending",
    "reason": "Regular checkup and blood pressure monitoring",
    "notes": "I've been experiencing occasional headaches",
    "is_upcoming": true,
    "allowed_actions": {
        "can_confirm": false,
        "can_reject": false,
        "can_cancel": true,
        "can_complete": false,
        "can_mark_no_show": false,
        "can_reschedule": true,
        "is_terminal": false
    },
    "created_at": "2026-02-02T10:00:00Z"
}
```

### Error Response (400 Bad Request)

```json
{
    "scheduled_time": ["Provider is not available at this time. Please choose another slot."]
}
```

---

## My Appointments

### List All Appointments

```
GET /api/appointments/
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `PENDING`, `CONFIRMED`, `CANCELLED`, etc. |
| `date_from` | string | Start date filter (`YYYY-MM-DD`) |
| `date_to` | string | End date filter (`YYYY-MM-DD`) |
| `provider` | UUID | Filter by provider |
| `location_type` | string | Filter by location type |
| `search` | string | Search in reason/notes |

### Response (200 OK)

```json
{
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "appointment-uuid",
            "provider": "provider-uuid",
            "provider_name": "Dr. Mohamed Kaddour",
            "patient_name": "Ahmed Benali",
            "service_name": null,
            "scheduled_date": "2026-02-05",
            "scheduled_time": "09:00:00",
            "duration_minutes": 30,
            "location_type": "CLINIC",
            "location_type_display": "At Clinic",
            "status": "CONFIRMED",
            "status_display": "Confirmed",
            "reason": "Regular checkup",
            "is_upcoming": true,
            "allowed_actions": {
                "can_confirm": false,
                "can_cancel": true,
                "can_complete": false,
                "can_reschedule": true,
                "is_terminal": false
            },
            "created_at": "2026-02-01T10:00:00Z"
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
    "provider": "provider-uuid",
    "provider_name": "Dr. Mohamed Kaddour",
    "provider_email": "doctor@example.com",
    "provider_type": "DOCTOR",
    "patient_user": "patient-uuid",
    "patient_record": null,
    "patient_name": "Ahmed Benali",
    "patient_email": "ahmed@example.com",
    "patient_phone": "+213555123456",
    "service": null,
    "service_name": null,
    "service_description": null,
    "scheduled_date": "2026-02-05",
    "scheduled_time": "09:00:00",
    "duration_minutes": 30,
    "location_type": "CLINIC",
    "location_type_display": "At Clinic",
    "clinic_address": {
        "id": "address-uuid",
        "street": "123 Rue Didouche Mourad",
        "city": "Algiers",
        "state": "Algiers",
        "zip_code": "16000",
        "latitude": "36.7538",
        "longitude": "3.0588"
    },
    "home_address": null,
    "meeting_link": null,
    "status": "CONFIRMED",
    "status_display": "Confirmed",
    "reason": "Regular checkup and blood pressure monitoring",
    "notes": "I've been experiencing occasional headaches",
    "cancellation_reason": null,
    "cancellation_notes": null,
    "cancelled_by": null,
    "cancelled_by_name": null,
    "cancelled_at": null,
    "created_by": "patient-uuid",
    "created_by_name": "Ahmed Benali",
    "confirmed_at": "2026-02-02T14:00:00Z",
    "completed_at": null,
    "is_upcoming": true,
    "is_past": false,
    "allowed_actions": {
        "can_confirm": false,
        "can_reject": false,
        "can_cancel": true,
        "can_complete": false,
        "can_mark_no_show": false,
        "can_reschedule": true,
        "is_terminal": false
    },
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-02T14:00:00Z"
}
```

### Upcoming Appointments

```
GET /api/appointments/upcoming/
```

Returns only `PENDING` and `CONFIRMED` appointments scheduled from today onwards.

### Past Appointments

```
GET /api/appointments/past/
```

Returns `COMPLETED`, `CANCELLED`, and `NO_SHOW` appointments.

### Today's Appointments

```
GET /api/appointments/today/
```

Returns all appointments scheduled for today.

---

## Appointment Statistics

Get a summary of your appointment statistics.

### Endpoint

```
GET /api/appointments/stats/
```

### Response (200 OK)

```json
{
    "total": 25,
    "pending": 2,
    "confirmed": 3,
    "completed": 18,
    "cancelled": 2,
    "no_show": 0,
    "today": 1,
    "upcoming": 5
}
```

---

## Cancel an Appointment

Cancel a pending or confirmed appointment.

### Endpoint

```
POST /api/appointments/{id}/cancel/
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | ❌ | Cancellation reason code |
| `notes` | string | ❌ | Additional explanation |

### Cancellation Reasons

| Code | Description |
|------|-------------|
| `PATIENT_REQUEST` | Patient Request |
| `EMERGENCY` | Emergency |
| `RESCHEDULED` | Rescheduled |
| `OTHER` | Other |

### Request Example

```json
{
    "reason": "PATIENT_REQUEST",
    "notes": "Unable to attend due to work commitment"
}
```

### Success Response (200 OK)

```json
{
    "status": "cancelled",
    "message": "Appointment cancelled successfully",
    "data": {
        "id": "appointment-uuid",
        "status": "CANCELLED",
        "status_display": "Cancelled",
        "cancellation_reason": "PATIENT_REQUEST",
        "cancellation_notes": "Unable to attend due to work commitment",
        "cancelled_by_name": "Ahmed Benali",
        "cancelled_at": "2026-02-02T12:00:00Z"
    }
}
```

### Error Response (400 Bad Request)

```json
{
    "error": "Cannot cancel a completed appointment."
}
```

---

## Reschedule an Appointment

Request to reschedule a pending or confirmed appointment.

### Endpoint

```
POST /api/appointments/{id}/reschedule/
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scheduled_date` | string | ✅ | New date (`YYYY-MM-DD`) |
| `scheduled_time` | string | ✅ | New time (`HH:MM`) |
| `notes` | string | ❌ | Reason for rescheduling |

### Request Example

```json
{
    "scheduled_date": "2026-02-07",
    "scheduled_time": "10:00",
    "notes": "Conflicting appointment, need to move to later date"
}
```

### Success Response (200 OK)

```json
{
    "status": "rescheduled",
    "message": "Appointment rescheduled successfully",
    "data": {
        "id": "new-appointment-uuid",
        "scheduled_date": "2026-02-07",
        "scheduled_time": "10:00:00",
        "status": "PENDING",
        "status_display": "Pending"
    }
}
```

### Error Response (400 Bad Request)

```json
{
    "scheduled_time": ["Provider is not available at this time."]
}
```

---

## View Appointment Prescription

If the provider has created a prescription for the appointment, retrieve it.

### Endpoint

```
GET /api/appointments/{id}/prescription/
```

### Response (200 OK)

```json
{
    "id": "prescription-uuid",
    "appointment": "appointment-uuid",
    "provider_name": "Dr. Mohamed Kaddour",
    "patient_name": "Ahmed Benali",
    "diagnosis": "Hypertension - Stage 1",
    "medications": [
        {
            "name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily",
            "duration": "30 days",
            "notes": "Take in the morning"
        }
    ],
    "instructions": "Monitor blood pressure daily. Follow low-sodium diet.",
    "follow_up_date": "2026-03-05",
    "created_at": "2026-02-05T10:30:00Z"
}
```

### Error Response (404 Not Found)

```json
{
    "error": "No prescription for this appointment."
}
```

---

## Appointment Status Reference

| Status | Description | Patient Actions |
|--------|-------------|-----------------|
| `PENDING` | Awaiting provider confirmation | Cancel, Reschedule |
| `CONFIRMED` | Provider confirmed | Cancel, Reschedule |
| `REJECTED` | Provider rejected the request | View only |
| `CANCELLED` | Appointment cancelled | View only |
| `COMPLETED` | Visit completed | View prescription |
| `NO_SHOW` | Patient didn't show up | View only |
| `RESCHEDULED` | Moved to new date/time | New appointment created |

### Status Transition Diagram

```
           ┌──────────────────┐
           │     PENDING      │
           └────────┬─────────┘
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ CONFIRMED│  │ REJECTED │  │CANCELLED │
└────┬─────┘  └──────────┘  └──────────┘
     │
     ├─────────────┬────────────┐
     ▼             ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│COMPLETED │  │ NO_SHOW  │  │CANCELLED │
└──────────┘  └──────────┘  └──────────┘
```

---

## Location Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `CLINIC` | At provider's clinic | - |
| `HOME` | Home visit | `home_address` |
| `ONLINE` | Video call | `meeting_link` (provider adds) |

### Get Appointment Choices

```
GET /api/appointment-choices/
```

### Response

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
| 403 | Forbidden - Not allowed |
| 404 | Not Found |
| 500 | Server Error |

### Common Error Responses

**Slot Not Available:**
```json
{
    "scheduled_time": ["Provider is not available at this time. Please choose another slot."]
}
```

**Past Date:**
```json
{
    "scheduled_date": ["Appointment cannot be scheduled in the past."]
}
```

**Home Address Required:**
```json
{
    "home_address": ["Home address is required for home visit appointments."]
}
```

**Cannot Cancel:**
```json
{
    "error": "Cannot cancel appointment with status COMPLETED."
}
```

---

## Mobile Integration Examples

### Flutter/Dart

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class AppointmentService {
  static const String baseUrl = 'https://dzmedilink.duckdns.org/api';
  final String token;

  AppointmentService(this.token);

  Map<String, String> get _headers => {
    'Authorization': 'Token $token',
    'Content-Type': 'application/json',
  };

  // Get available slots for a provider
  Future<List<TimeSlot>> getAvailableSlots({
    required String providerId,
    required DateTime date,
    int durationMinutes = 30,
    String locationType = 'CLINIC',
  }) async {
    final dateStr = date.toIso8601String().split('T')[0];
    final response = await http.get(
      Uri.parse('$baseUrl/available-slots/')
          .replace(queryParameters: {
        'provider': providerId,
        'date': dateStr,
        'duration_minutes': durationMinutes.toString(),
        'location_type': locationType,
      }),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['available_slots'] as List)
          .map((slot) => TimeSlot.fromJson(slot))
          .toList();
    }
    throw AppointmentException('Failed to load slots');
  }

  // Book an appointment
  Future<Appointment> bookAppointment({
    required String providerId,
    required DateTime date,
    required String time,
    required String locationType,
    String? homeAddressId,
    String? reason,
    String? notes,
  }) async {
    final body = {
      'provider': providerId,
      'scheduled_date': date.toIso8601String().split('T')[0],
      'scheduled_time': time,
      'location_type': locationType,
      if (homeAddressId != null) 'home_address': homeAddressId,
      if (reason != null) 'reason': reason,
      if (notes != null) 'notes': notes,
    };

    final response = await http.post(
      Uri.parse('$baseUrl/appointments/'),
      headers: _headers,
      body: jsonEncode(body),
    );

    if (response.statusCode == 201) {
      return Appointment.fromJson(jsonDecode(response.body));
    }
    
    final error = jsonDecode(response.body);
    throw AppointmentException(error.toString());
  }

  // Get my appointments
  Future<List<Appointment>> getMyAppointments({
    String? status,
    DateTime? dateFrom,
    DateTime? dateTo,
  }) async {
    final queryParams = <String, String>{};
    if (status != null) queryParams['status'] = status;
    if (dateFrom != null) {
      queryParams['date_from'] = dateFrom.toIso8601String().split('T')[0];
    }
    if (dateTo != null) {
      queryParams['date_to'] = dateTo.toIso8601String().split('T')[0];
    }

    final response = await http.get(
      Uri.parse('$baseUrl/appointments/').replace(queryParameters: queryParams),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['results'] as List)
          .map((a) => Appointment.fromJson(a))
          .toList();
    }
    throw AppointmentException('Failed to load appointments');
  }

  // Get upcoming appointments
  Future<List<Appointment>> getUpcomingAppointments() async {
    final response = await http.get(
      Uri.parse('$baseUrl/appointments/upcoming/'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return (data['results'] as List)
          .map((a) => Appointment.fromJson(a))
          .toList();
    }
    throw AppointmentException('Failed to load upcoming appointments');
  }

  // Cancel an appointment
  Future<Appointment> cancelAppointment(
    String appointmentId, {
    String reason = 'PATIENT_REQUEST',
    String? notes,
  }) async {
    final body = {
      'reason': reason,
      if (notes != null) 'notes': notes,
    };

    final response = await http.post(
      Uri.parse('$baseUrl/appointments/$appointmentId/cancel/'),
      headers: _headers,
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return Appointment.fromJson(data['data']);
    }
    
    final error = jsonDecode(response.body);
    throw AppointmentException(error['error'] ?? 'Failed to cancel');
  }

  // Reschedule an appointment
  Future<Appointment> rescheduleAppointment(
    String appointmentId, {
    required DateTime newDate,
    required String newTime,
    String? notes,
  }) async {
    final body = {
      'scheduled_date': newDate.toIso8601String().split('T')[0],
      'scheduled_time': newTime,
      if (notes != null) 'notes': notes,
    };

    final response = await http.post(
      Uri.parse('$baseUrl/appointments/$appointmentId/reschedule/'),
      headers: _headers,
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return Appointment.fromJson(data['data']);
    }
    
    final error = jsonDecode(response.body);
    throw AppointmentException(error['error'] ?? 'Failed to reschedule');
  }

  // Get appointment statistics
  Future<AppointmentStats> getStats() async {
    final response = await http.get(
      Uri.parse('$baseUrl/appointments/stats/'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return AppointmentStats.fromJson(jsonDecode(response.body));
    }
    throw AppointmentException('Failed to load stats');
  }
}

// Models
class TimeSlot {
  final String startTime;
  final String endTime;
  final int durationMinutes;

  TimeSlot({
    required this.startTime,
    required this.endTime,
    required this.durationMinutes,
  });

  factory TimeSlot.fromJson(Map<String, dynamic> json) => TimeSlot(
    startTime: json['start_time'],
    endTime: json['end_time'],
    durationMinutes: json['duration_minutes'],
  );
}

class Appointment {
  final String id;
  final String providerId;
  final String providerName;
  final String scheduledDate;
  final String scheduledTime;
  final String status;
  final String statusDisplay;
  final String locationType;
  final bool isUpcoming;
  final Map<String, bool> allowedActions;

  Appointment({
    required this.id,
    required this.providerId,
    required this.providerName,
    required this.scheduledDate,
    required this.scheduledTime,
    required this.status,
    required this.statusDisplay,
    required this.locationType,
    required this.isUpcoming,
    required this.allowedActions,
  });

  factory Appointment.fromJson(Map<String, dynamic> json) => Appointment(
    id: json['id'],
    providerId: json['provider'],
    providerName: json['provider_name'],
    scheduledDate: json['scheduled_date'],
    scheduledTime: json['scheduled_time'],
    status: json['status'],
    statusDisplay: json['status_display'],
    locationType: json['location_type'],
    isUpcoming: json['is_upcoming'] ?? false,
    allowedActions: Map<String, bool>.from(json['allowed_actions'] ?? {}),
  );

  bool get canCancel => allowedActions['can_cancel'] ?? false;
  bool get canReschedule => allowedActions['can_reschedule'] ?? false;
}

class AppointmentStats {
  final int total;
  final int pending;
  final int confirmed;
  final int completed;
  final int cancelled;
  final int noShow;
  final int today;
  final int upcoming;

  AppointmentStats({
    required this.total,
    required this.pending,
    required this.confirmed,
    required this.completed,
    required this.cancelled,
    required this.noShow,
    required this.today,
    required this.upcoming,
  });

  factory AppointmentStats.fromJson(Map<String, dynamic> json) => AppointmentStats(
    total: json['total'],
    pending: json['pending'],
    confirmed: json['confirmed'],
    completed: json['completed'],
    cancelled: json['cancelled'],
    noShow: json['no_show'],
    today: json['today'],
    upcoming: json['upcoming'],
  );
}

class AppointmentException implements Exception {
  final String message;
  AppointmentException(this.message);

  @override
  String toString() => message;
}
```

### React Native

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = 'https://dzmedilink.duckdns.org/api';

interface TimeSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

interface Appointment {
  id: string;
  provider: string;
  provider_name: string;
  scheduled_date: string;
  scheduled_time: string;
  status: 'PENDING' | 'CONFIRMED' | 'REJECTED' | 'CANCELLED' | 'COMPLETED' | 'NO_SHOW';
  status_display: string;
  location_type: 'CLINIC' | 'HOME' | 'ONLINE';
  location_type_display: string;
  reason: string;
  is_upcoming: boolean;
  allowed_actions: {
    can_confirm: boolean;
    can_cancel: boolean;
    can_complete: boolean;
    can_reschedule: boolean;
    is_terminal: boolean;
  };
}

interface AppointmentStats {
  total: number;
  pending: number;
  confirmed: number;
  completed: number;
  cancelled: number;
  no_show: number;
  today: number;
  upcoming: number;
}

class AppointmentService {
  private api: AxiosInstance;

  constructor(token: string) {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
      },
    });
  }

  // Get available slots
  async getAvailableSlots(
    providerId: string,
    date: string,
    durationMinutes: number = 30,
    locationType: string = 'CLINIC'
  ): Promise<TimeSlot[]> {
    const response = await this.api.get('/available-slots/', {
      params: {
        provider: providerId,
        date,
        duration_minutes: durationMinutes,
        location_type: locationType,
      },
    });
    return response.data.available_slots;
  }

  // Book appointment
  async bookAppointment(data: {
    provider: string;
    scheduled_date: string;
    scheduled_time: string;
    location_type: string;
    home_address?: string;
    reason?: string;
    notes?: string;
  }): Promise<Appointment> {
    const response = await this.api.post('/appointments/', data);
    return response.data;
  }

  // Get appointments
  async getAppointments(filters?: {
    status?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<Appointment[]> {
    const response = await this.api.get('/appointments/', { params: filters });
    return response.data.results;
  }

  // Get upcoming
  async getUpcoming(): Promise<Appointment[]> {
    const response = await this.api.get('/appointments/upcoming/');
    return response.data.results;
  }

  // Cancel
  async cancel(id: string, reason?: string, notes?: string): Promise<Appointment> {
    const response = await this.api.post(`/appointments/${id}/cancel/`, {
      reason: reason || 'PATIENT_REQUEST',
      notes,
    });
    return response.data.data;
  }

  // Reschedule
  async reschedule(
    id: string,
    newDate: string,
    newTime: string,
    notes?: string
  ): Promise<Appointment> {
    const response = await this.api.post(`/appointments/${id}/reschedule/`, {
      scheduled_date: newDate,
      scheduled_time: newTime,
      notes,
    });
    return response.data.data;
  }

  // Get stats
  async getStats(): Promise<AppointmentStats> {
    const response = await this.api.get('/appointments/stats/');
    return response.data;
  }
}

export default AppointmentService;
```

---

## Related Documentation

- [Authentication API](./AUTHENTICATION_API.md)
- [Medical Records API](../MEDICAL_RECORDS_API.md)
- [Prescriptions API](../PRESCRIPTIONS_API.md)

---

## Support

For API issues or questions:
- API Documentation: https://dzmedilink.duckdns.org/docs
- Support Email: api-support@medilink.dz
