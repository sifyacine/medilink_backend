# Provider Dashboards - Appointments API

## Overview

This documentation covers the **Appointments API** for Provider Web Dashboards. This includes all provider types: **Doctors**, **Clinics**, **Laboratories**, **VTC** (Medical Transport), and **Sellers/Pharmacies**.

Providers can manage their appointment schedule, respond to patient requests, track appointments, manage availability, and generate reports.

---

## Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Daily Appointment Limit](#daily-appointment-limit)
4. [Provider Appointment Workflow](#provider-appointment-workflow)
5. [Provider-Patient Relationship](#-provider-patient-relationship)
6. [Appointments Management](#appointments-management)
   - [List Appointments](#list-appointments)
   - [Get Appointment Details](#get-appointment-details)
   - [Advanced Search](#advanced-search)
   - [Create Appointment](#create-appointment)
   - [Update Appointment](#update-appointment)
7. [Quick Access Endpoints](#quick-access-endpoints)
8. [Appointment Actions](#appointment-actions)
   - [Confirm Appointment](#confirm-appointment)
   - [Reject Appointment](#reject-appointment)
   - [Cancel Appointment](#cancel-appointment)
   - [Complete Appointment](#complete-appointment)
   - [Mark No-Show](#mark-no-show)
   - [Reschedule Appointment](#reschedule-appointment)
9. [Services Management](#services-management)
10. [Prescription from Appointment](#prescription-from-appointment)
11. [Statistics & Reports](#statistics--reports)
12. [Availability Management](#availability-management)
13. [Time Off Management](#time-off-management)
14. [Available Slots API](#available-slots-api)
15. [Provider Schedule View](#provider-schedule-view)
16. [Appointment Choices](#appointment-choices)
17. [Error Handling](#error-handling)
18. [Web Integration Examples](#web-integration-examples)

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

**Important:** Provider accounts must be `APPROVED` to access appointment management features.

---

## Daily Appointment Limit

Providers can set a **daily appointment limit** to control how many appointments can be booked per day. This helps manage workload and ensure quality care.

### How It Works

| `daily_appointment_limit` | Behavior |
|---------------------------|----------|
| `0` (default) | **Unlimited** - No restriction on daily bookings |
| Any positive number (e.g., `20`) | Maximum appointments allowed per day |

### Setting Your Daily Limit

Update your provider profile to set the limit:

```
PATCH /api/doctors/profile/
```

```json
{
    "daily_appointment_limit": 20
}
```

### What Happens When Limit is Reached

When a patient tries to book an appointment on a date that has reached the daily limit:

- **API Response:** `400 Bad Request`
- **Error Message:** `"Daily appointment limit (20) reached for this date. Please choose another date."`

### Checking Remaining Slots

When viewing available slots, the system automatically excludes dates that have reached their daily limit.

---

## Provider Appointment Workflow

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                       PROVIDER APPOINTMENT WORKFLOW                                │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                    INCOMING PATIENT REQUESTS                                  │ │
│  │  Patient books via app ──▶ Notification ──▶ Dashboard (Status: PENDING)     │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                            │
│                     ┌────────────────┴────────────────┐                          │
│                     ▼                                  ▼                          │
│             ┌──────────────┐                   ┌──────────────┐                   │
│             │   CONFIRM    │                   │    REJECT    │                   │
│             │  ✓ Accept    │                   │  ✗ Decline   │                   │
│             │    booking   │                   │  with reason │                   │
│             └──────┬───────┘                   └──────────────┘                   │
│                    │                                                              │
│                    ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                    APPOINTMENT DAY                                            │ │
│  │  • View patient info  • Access records  • Add services  • Create prescription│ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                    │                                                              │
│       ┌────────────┼────────────┬────────────┐                                   │
│       ▼            ▼            ▼            ▼                                   │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                              │
│ │ COMPLETE │ │ NO_SHOW  │ │  CANCEL  │ │RESCHEDULE│                              │
│ │ ✓ Visit  │ │ Patient  │ │ Provider │ │ Move to  │                              │
│ │   done   │ │ absent   │ │ cancels  │ │ new slot │                              │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘                              │
│       │                                                                           │
│       ▼                                                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                    POST-APPOINTMENT                                           │ │
│  │  • Create prescription  • Update medical record  • Generate invoice          │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔗 Provider-Patient Relationship

> **⚠️ IMPORTANT: Automatic Patient Record Creation on Confirmation**
>
> When you **confirm** (or **reschedule**) an appointment, the system automatically establishes a provider-patient relationship. This is a crucial business logic:

### What Happens When You Confirm an Appointment

1. **Patient Record Created**: If the patient doesn't have a record yet, one is automatically created using their account information (name, email, phone, date of birth).

2. **Access Granted**: You are automatically granted **FULL access** to this patient's medical record. This means you can:
   - View and update their medical history
   - Add emergency contact information
   - Add/update allergies and chronic conditions
   - Create prescriptions and medical records
   - Manage their care in your patient list

3. **Patient Added to Your List**: The patient now appears in your patient list (`GET /api/patients/`).

### Managing Patient Medical Information

After an appointment is confirmed, you can update the patient's medical info:

```
GET /api/patients/{patient_id}/
PATCH /api/patients/{patient_id}/
```

**Updatable Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `emergency_contact_name` | string | Emergency contact person name |
| `emergency_contact_phone` | string | Emergency phone number |
| `blood_type` | string | A+, A-, B+, B-, AB+, AB-, O+, O- |
| `known_allergies` | text | List of known allergies |
| `chronic_conditions` | text | Chronic medical conditions |
| `current_medications` | text | Current medications |
| `notes` | text | Additional notes |

**Example - Update Patient Allergies:**
```json
PATCH /api/patients/{patient_id}/

{
    "known_allergies": "Penicillin, Ibuprofen",
    "emergency_contact_name": "Fatima Benali",
    "emergency_contact_phone": "+213555987654"
}
```

> **💡 Note:** Both patients AND providers can update this information. The patient can also update their own medical info via their profile.

### Access Levels

Your access level to patient records:

| Access Level | What You Can Do |
|--------------|-----------------|
| `FULL` | View and edit all patient information (default for confirming provider) |
| `READ_ONLY` | Only view medical records, cannot modify |
| `LIMITED` | Access only specific records/appointments |

---

## Appointments Management

### List Appointments

Get all appointments for your provider account.

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
    "count": 150,
    "next": "https://dzmedilink.duckdns.org/api/appointments/?page=2",
    "previous": null,
    "results": [
        {
            "id": "uuid-here",
            "provider": "provider-uuid",
            "provider_name": "Dr. Mohamed Kaddour",
            "patient_name": "Ahmed Benali",
            "service_name": "General Consultation",
            "scheduled_date": "2026-02-03",
            "scheduled_time": "09:00:00",
            "duration_minutes": 30,
            "location_type": "CLINIC",
            "location_type_display": "At Clinic",
            "status": "PENDING",
            "status_display": "Pending",
            "reason": "Routine checkup",
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
    "provider": "provider-uuid",
    "provider_name": "Dr. Mohamed Kaddour",
    "provider_email": "doctor@example.com",
    "provider_type": "DOCTOR",
    "patient_user": "patient-uuid",
    "patient_record": null,
    "patient_name": "Ahmed Benali",
    "patient_email": "ahmed@example.com",
    "patient_phone": "+213555123456",
    "service": "service-uuid",
    "service_name": "General Consultation",
    "service_description": "Complete health checkup",
    "scheduled_date": "2026-02-03",
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
    "reason": "Annual health checkup",
    "notes": "Patient has history of hypertension",
    "provider_notes": "Monitor blood pressure closely",
    "rejection_reason": "",
    "rejected_at": null,
    "cancellation_reason": null,
    "cancellation_notes": null,
    "cancelled_by": null,
    "cancelled_by_name": null,
    "cancelled_at": null,
    "created_by": "patient-uuid",
    "created_by_name": "Ahmed Benali",
    "created_by_role": "PATIENT",
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

#### Field Notes

| Field | Type | Description |
|-------|------|-------------|
| `scheduled_date` | string | **Required** - The appointment date (`YYYY-MM-DD`) |
| `scheduled_time` | string \| null | **Optional** - The appointment time (`HH:MM:SS`). Can be `null` for date-only appointments |
| `duration_minutes` | integer \| null | **Optional** - Duration in minutes (defaults to 30 if not set) |
| `meeting_link` | string \| null | Video call URL. **Required for ONLINE appointments** when confirming |
```

### Advanced Search

```
GET /api/appointments/search/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (patient name, email, reason, notes, service) |
| `status` | string | Filter by status |
| `date_from` | string | Start date (`YYYY-MM-DD`) |
| `date_to` | string | End date (`YYYY-MM-DD`) |
| `location_type` | string | Filter by location |
| `created_by_role` | string | `PATIENT`, `PROVIDER`, `ADMIN` |

### Create Appointment

Providers can create appointments for patients.

```
POST /api/appointments/
```

#### Required vs Optional Fields

| Field | Required | Description |
|-------|----------|-------------|
| `scheduled_date` | ✅ Yes | The appointment date (`YYYY-MM-DD`) |
| `patient_user` OR `patient_record` | ✅ One required | Patient identifier |
| `location_type` | ❌ No | `CLINIC`, `HOME`, or `ONLINE` (defaults to `CLINIC`) |
| `scheduled_time` | ❌ No | Specific time (`HH:MM`). If omitted, patient comes on that day without fixed time |
| `duration_minutes` | ❌ No | Duration in minutes (defaults to 30) |
| `service` | ❌ No | Service UUID |
| `reason` | ❌ No | Visit reason |
| `notes` | ❌ No | Additional notes |
| `meeting_link` | ❌ No | Required later when confirming ONLINE appointments |

> **💡 Flexible Scheduling:** The `scheduled_time` is optional. Providers can book appointments for a specific date without specifying a time. This is useful for walk-in clinics or when patients are expected to come during working hours without a fixed slot.

#### For Registered Patient (User Account)

```json
{
    "patient_user": "patient-user-uuid",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "10:00",
    "duration_minutes": 30,
    "location_type": "CLINIC",
    "service": "service-uuid",
    "reason": "Follow-up consultation",
    "notes": "Post-surgery review"
}
```

#### For Date-Only Appointment (No Fixed Time)

```json
{
    "patient_user": "patient-user-uuid",
    "scheduled_date": "2026-02-05",
    "location_type": "CLINIC",
    "reason": "Walk-in consultation"
}
```

#### For Non-Registered Patient (Patient Record)

```json
{
    "patient_record": "patient-record-uuid",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "14:00",
    "duration_minutes": 45,
    "location_type": "CLINIC",
    "reason": "New patient consultation"
}
```

#### For Online Appointment

```json
{
    "patient_user": "patient-user-uuid",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "16:00",
    "duration_minutes": 20,
    "location_type": "ONLINE",
    "reason": "Telemedicine consultation"
}
```

> **⚠️ Note for Online Appointments:** When creating an online appointment, you don't need to provide the `meeting_link` immediately. However, you **MUST** provide it when **confirming** the appointment. See [Confirm Appointment](#confirm-appointment).
```

### Response (201 Created)

```json
{
    "id": "new-appointment-uuid",
    "provider": "provider-uuid",
    "patient_name": "Ahmed Benali",
    "scheduled_date": "2026-02-05",
    "scheduled_time": "10:00:00",
    "status": "CONFIRMED",
    "status_display": "Confirmed",
    "created_by_role": "PROVIDER",
    "created_at": "2026-02-02T12:00:00Z"
}
```

**Note:** When providers create appointments, they are typically auto-confirmed.

### Update Appointment

```
PATCH /api/appointments/{id}/
```

#### Updatable Fields

| Field | Description |
|-------|-------------|
| `scheduled_date` | New date (restrictions apply for confirmed) |
| `scheduled_time` | New time (restrictions apply for confirmed) |
| `duration_minutes` | Duration in minutes |
| `location_type` | Location type |
| `clinic_address` | Clinic address UUID |
| `home_address` | Home address UUID |
| `meeting_link` | Video call link |
| `reason` | Visit reason |
| `notes` | General notes |
| `provider_notes` | Private provider notes |

```json
{
    "provider_notes": "Patient needs ECG before consultation",
    "duration_minutes": 45
}
```

**Note:** For CONFIRMED appointments, date/time changes are restricted to the provider or require rescheduling.

---

## Quick Access Endpoints

### Today's Appointments

```
GET /api/appointments/today/
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
    "appointments": [...]
}
```

### Appointment History

```
GET /api/appointments/history/
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_upcoming` | boolean | Include upcoming (default: false) |
| `date_from` | string | Start date filter |
| `date_to` | string | End date filter |

---

## Appointment Actions

### Confirm Appointment

Accept a patient's appointment request.

```
POST /api/appointments/{id}/confirm/
```

#### Request Body

```json
{
    "notes": "Confirmed. Please arrive 10 minutes early."
}
```

#### For Online Appointments - Meeting Link Required

> **⚠️ IMPORTANT:** When confirming an **ONLINE** appointment, you **MUST** provide the `meeting_link`. The system will reject the confirmation without it.

```json
{
    "meeting_link": "https://meet.medilink.dz/dr-kaddour-123abc",
    "notes": "Confirmed. Please join the meeting link 5 minutes before your scheduled time."
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
        "meeting_link": "https://meet.medilink.dz/dr-kaddour-123abc",
        "provider_notes": "Confirmed. Please join the meeting link 5 minutes before your scheduled time."
    }
}
```

#### Error Response - Missing Meeting Link (Online Appointments)

```json
{
    "meeting_link": ["Meeting link is required for online appointments."]
}
```
```

### Reject Appointment

Decline a patient's appointment request.

```
POST /api/appointments/{id}/reject/
```

#### Request Body

```json
{
    "rejection_reason": "Fully booked on this date. Please choose another day."
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
        "rejection_reason": "Fully booked on this date. Please choose another day.",
        "rejected_at": "2026-02-02T10:00:00Z"
    }
}
```

### Cancel Appointment

Cancel an appointment.

```
POST /api/appointments/{id}/cancel/
```

#### Request Body

```json
{
    "reason": "PROVIDER_UNAVAILABLE",
    "notes": "Emergency surgery. All appointments rescheduled."
}
```

#### Cancellation Reason Codes

| Code | Description |
|------|-------------|
| `PATIENT_REQUEST` | Patient Request |
| `PROVIDER_UNAVAILABLE` | Provider Unavailable |
| `EMERGENCY` | Emergency |
| `RESCHEDULED` | Rescheduled |
| `NO_RESPONSE` | No Response |
| `OTHER` | Other |

### Complete Appointment

Mark an appointment as completed after the visit.

```
POST /api/appointments/{id}/complete/
```

#### Request Body (Optional)

```json
{
    "provider_notes": "Consultation completed. Blood pressure: 120/80. Prescribed medication for 30 days. Follow-up in 2 weeks."
}
```

> **⚠️ For Online Appointments:** The system validates that a `meeting_link` exists on the appointment before allowing completion. If the appointment is ONLINE and no meeting link was set during confirmation, completion will fail.

#### Response (200 OK)

```json
{
    "status": "completed",
    "message": "Appointment marked as completed",
    "data": {
        "id": "appointment-uuid",
        "status": "COMPLETED",
        "status_display": "Completed",
        "completed_at": "2026-02-03T09:45:00Z"
    }
}
```

#### Error Response - Missing Meeting Link (Online Appointments)

```json
{
    "meeting_link": ["Online appointment cannot be completed without a meeting link. Please add the meeting link first."]
}
```
```

### Mark No-Show

Mark when a patient doesn't show up.

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
    "scheduled_date": "2026-02-07",
    "scheduled_time": "11:00",
    "notes": "Rescheduled per patient request"
}
```

#### Response (200 OK)

```json
{
    "status": "rescheduled",
    "message": "Appointment rescheduled successfully",
    "data": {
        "id": "new-appointment-uuid",
        "scheduled_date": "2026-02-07",
        "scheduled_time": "11:00:00",
        "status": "PENDING"
    }
}
```

---

## Services Management

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
                "name": "General Consultation",
                "price": "3000.00",
                "currency": "DZD",
                "duration_minutes": 30
            },
            "notes": "",
            "created_at": "2026-02-03T09:00:00Z"
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
    "service_ids": ["service-uuid-1", "service-uuid-2", "service-uuid-3"]
}
```

#### Response (200 OK)

```json
{
    "message": "3 services attached successfully",
    "added_service_ids": ["service-uuid-1", "service-uuid-2", "service-uuid-3"],
    "data": {...}
}
```

### Remove Service

```
DELETE /api/appointments/{id}/services/{service_id}/
```

---

## Prescription from Appointment

Get the prescription associated with an appointment.

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
    "diagnosis": "Essential Hypertension - Stage 1",
    "medications": [
        {
            "name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily in the morning",
            "duration": "30 days",
            "notes": "Take on empty stomach"
        },
        {
            "name": "Hydrochlorothiazide",
            "dosage": "12.5mg",
            "frequency": "Once daily",
            "duration": "30 days",
            "notes": "Take with food"
        }
    ],
    "instructions": "Monitor blood pressure daily. Reduce sodium intake. Exercise 30 minutes daily.",
    "follow_up_date": "2026-03-03",
    "created_at": "2026-02-03T10:00:00Z"
}
```

### Error (404 Not Found)

```json
{
    "error": "No prescription for this appointment."
}
```

**Note:** To create a prescription, use the Prescriptions API: `POST /api/prescriptions/`

---

## Statistics & Reports

### Appointment Statistics

```
GET /api/appointments/stats/
```

### Response

```json
{
    "total": 500,
    "pending": 12,
    "confirmed": 25,
    "completed": 450,
    "cancelled": 10,
    "no_show": 3,
    "today": 8,
    "upcoming": 37
}
```

---

## Availability Management

### List Availability Slots

```
GET /api/provider-availability/
```

### Response

```json
[
    {
        "id": "slot-uuid",
        "provider": "provider-uuid",
        "day_of_week": 0,
        "day_of_week_display": "Monday",
        "start_time": "08:00:00",
        "end_time": "12:00:00",
        "is_active": true,
        "location_type": "CLINIC",
        "max_appointments": 1,
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-15T14:00:00Z"
    },
    {
        "id": "slot-uuid-2",
        "provider": "provider-uuid",
        "day_of_week": 0,
        "day_of_week_display": "Monday",
        "start_time": "14:00:00",
        "end_time": "18:00:00",
        "is_active": true,
        "location_type": "CLINIC",
        "max_appointments": 1
    }
]
```

### Get My Schedule

```
GET /api/provider-availability/my_schedule/
```

Returns only active availability slots for the current provider.

### Create Availability Slot

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
    "day_of_week": 0,
    "start_time": "08:00",
    "end_time": "12:00",
    "is_active": true,
    "location_type": "CLINIC",
    "max_appointments": 1
}
```

### Update Availability Slot

```
PATCH /api/provider-availability/{id}/
```

```json
{
    "end_time": "13:00",
    "max_appointments": 2
}
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
        "location_type": "CLINIC"
    },
    {
        "day_of_week": 0,
        "start_time": "14:00",
        "end_time": "18:00",
        "location_type": "CLINIC"
    },
    {
        "day_of_week": 1,
        "start_time": "08:00",
        "end_time": "17:00",
        "location_type": "CLINIC"
    },
    {
        "day_of_week": 2,
        "start_time": "08:00",
        "end_time": "17:00",
        "location_type": "CLINIC"
    },
    {
        "day_of_week": 3,
        "start_time": "08:00",
        "end_time": "17:00",
        "location_type": "CLINIC"
    },
    {
        "day_of_week": 4,
        "start_time": "08:00",
        "end_time": "12:00",
        "location_type": "CLINIC"
    }
]
```

---

## Time Off Management

### List Time Off Periods

```
GET /api/provider-time-off/
```

### Response

```json
[
    {
        "id": "time-off-uuid",
        "provider": "provider-uuid",
        "start_datetime": "2026-02-15T00:00:00Z",
        "end_datetime": "2026-02-20T23:59:00Z",
        "reason": "Annual conference",
        "is_recurring_annual": false,
        "created_at": "2026-02-01T10:00:00Z",
        "updated_at": "2026-02-01T10:00:00Z"
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
    "reason": "Annual medical conference",
    "is_recurring_annual": false
}
```

### Update Time Off

```
PATCH /api/provider-time-off/{id}/
```

### Delete Time Off

```
DELETE /api/provider-time-off/{id}/
```

### Get Upcoming Time Off

```
GET /api/provider-time-off/upcoming/
```

---

## Available Slots API

Get available time slots for booking.

```
GET /api/available-slots/
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | UUID | ✅ | Provider ID |
| `date` | string | ✅ | Date (`YYYY-MM-DD`) |
| `duration_minutes` | integer | ❌ | Duration (default: 30) |
| `location_type` | string | ❌ | `CLINIC`, `HOME`, `ONLINE` |

### Response

```json
{
    "provider": "provider-uuid",
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
            "start_time": "10:00",
            "end_time": "10:30",
            "duration_minutes": 30
        }
    ]
}
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
| `provider` | UUID | Provider ID (optional if logged in as provider) |
| `start_date` | string | Start date (`YYYY-MM-DD`) |
| `end_date` | string | End date (`YYYY-MM-DD`) |

### Response

```json
{
    "provider": "provider-uuid",
    "start_date": "2026-02-02",
    "end_date": "2026-02-08",
    "availability": [
        {
            "day_of_week": 0,
            "day_of_week_display": "Monday",
            "start_time": "08:00:00",
            "end_time": "12:00:00",
            "location_type": "CLINIC"
        },
        {
            "day_of_week": 0,
            "day_of_week_display": "Monday",
            "start_time": "14:00:00",
            "end_time": "18:00:00",
            "location_type": "CLINIC"
        }
    ],
    "time_off": [],
    "appointments": [
        {
            "id": "uuid",
            "scheduled_date": "2026-02-03",
            "scheduled_time": "09:00:00",
            "duration_minutes": 30,
            "patient_name": "Ahmed Benali",
            "status": "CONFIRMED",
            "location_type": "CLINIC"
        },
        {
            "id": "uuid",
            "scheduled_date": "2026-02-03",
            "scheduled_time": "10:00:00",
            "duration_minutes": 30,
            "patient_name": "Fatima Cherif",
            "status": "PENDING",
            "location_type": "CLINIC"
        }
    ]
}
```

---

## Appointment Choices

Get available status and location type options.

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
| 403 | Forbidden - Not your appointment / Account pending |
| 404 | Not Found |
| 500 | Server Error |

### Common Error Responses

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

**Scheduling Conflict:**
```json
{
    "scheduled_time": ["Provider has a conflicting appointment at this time."]
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

## Web Integration Examples

### JavaScript/TypeScript (Axios)

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = 'https://dzmedilink.duckdns.org/api';

interface Appointment {
  id: string;
  provider: string;
  provider_name: string;
  patient_name: string;
  patient_email: string;
  patient_phone: string;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
  status: AppointmentStatus;
  status_display: string;
  location_type: LocationType;
  location_type_display: string;
  reason: string;
  notes: string;
  provider_notes: string;
  allowed_actions: AllowedActions;
  created_at: string;
}

type AppointmentStatus = 
  | 'PENDING' 
  | 'CONFIRMED' 
  | 'REJECTED' 
  | 'CANCELLED' 
  | 'COMPLETED' 
  | 'NO_SHOW';

type LocationType = 'CLINIC' | 'HOME' | 'ONLINE';

interface AllowedActions {
  can_confirm: boolean;
  can_reject: boolean;
  can_cancel: boolean;
  can_complete: boolean;
  can_mark_no_show: boolean;
  can_reschedule: boolean;
  is_terminal: boolean;
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

interface AvailabilitySlot {
  id: string;
  day_of_week: number;
  day_of_week_display: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
  location_type: string;
  max_appointments: number;
}

interface TimeSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
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

  // ==================== APPOINTMENTS ====================

  async getAppointments(filters?: {
    status?: AppointmentStatus;
    date_from?: string;
    date_to?: string;
    location_type?: LocationType;
  }): Promise<{ count: number; results: Appointment[] }> {
    const response = await this.api.get('/appointments/', { params: filters });
    return response.data;
  }

  async getAppointment(id: string): Promise<Appointment> {
    const response = await this.api.get(`/appointments/${id}/`);
    return response.data;
  }

  async getTodayAppointments(): Promise<Appointment[]> {
    const response = await this.api.get('/appointments/today/');
    return response.data;
  }

  async getUpcomingAppointments(): Promise<Appointment[]> {
    const response = await this.api.get('/appointments/upcoming/');
    return response.data.results;
  }

  async getWeekAppointments(weekOffset: number = 0): Promise<{
    week_start: string;
    week_end: string;
    appointments: Appointment[];
  }> {
    const response = await this.api.get('/appointments/week/', {
      params: { week_offset: weekOffset },
    });
    return response.data;
  }

  async searchAppointments(query: string, filters?: {
    status?: AppointmentStatus;
    date_from?: string;
    date_to?: string;
  }): Promise<Appointment[]> {
    const response = await this.api.get('/appointments/search/', {
      params: { q: query, ...filters },
    });
    return response.data.results;
  }

  async createAppointment(data: {
    patient_user?: string;
    patient_record?: string;
    scheduled_date: string;
    scheduled_time: string;
    duration_minutes?: number;
    location_type?: LocationType;
    service?: string;
    reason?: string;
    notes?: string;
    meeting_link?: string;
  }): Promise<Appointment> {
    const response = await this.api.post('/appointments/', data);
    return response.data;
  }

  async updateAppointment(id: string, data: Partial<{
    scheduled_date: string;
    scheduled_time: string;
    duration_minutes: number;
    location_type: LocationType;
    reason: string;
    notes: string;
    provider_notes: string;
  }>): Promise<Appointment> {
    const response = await this.api.patch(`/appointments/${id}/`, data);
    return response.data;
  }

  // ==================== APPOINTMENT ACTIONS ====================

  async confirmAppointment(id: string, notes?: string): Promise<Appointment> {
    const response = await this.api.post(`/appointments/${id}/confirm/`, {
      notes,
    });
    return response.data.data;
  }

  async rejectAppointment(id: string, reason: string): Promise<Appointment> {
    const response = await this.api.post(`/appointments/${id}/reject/`, {
      rejection_reason: reason,
    });
    return response.data.data;
  }

  async cancelAppointment(
    id: string,
    reason: string = 'OTHER',
    notes?: string
  ): Promise<Appointment> {
    const response = await this.api.post(`/appointments/${id}/cancel/`, {
      reason,
      notes,
    });
    return response.data.data;
  }

  async completeAppointment(id: string, providerNotes?: string): Promise<Appointment> {
    const response = await this.api.post(`/appointments/${id}/complete/`, {
      provider_notes: providerNotes,
    });
    return response.data.data;
  }

  async markNoShow(id: string): Promise<Appointment> {
    const response = await this.api.post(`/appointments/${id}/no_show/`);
    return response.data.data;
  }

  async rescheduleAppointment(
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

  // ==================== STATISTICS ====================

  async getStats(): Promise<AppointmentStats> {
    const response = await this.api.get('/appointments/stats/');
    return response.data;
  }

  // ==================== AVAILABILITY ====================

  async getMySchedule(): Promise<AvailabilitySlot[]> {
    const response = await this.api.get('/provider-availability/my_schedule/');
    return response.data;
  }

  async createAvailability(data: {
    day_of_week: number;
    start_time: string;
    end_time: string;
    is_active?: boolean;
    location_type?: string;
    max_appointments?: number;
  }): Promise<AvailabilitySlot> {
    const response = await this.api.post('/provider-availability/', data);
    return response.data;
  }

  async updateAvailability(id: string, data: Partial<{
    start_time: string;
    end_time: string;
    is_active: boolean;
    location_type: string;
    max_appointments: number;
  }>): Promise<AvailabilitySlot> {
    const response = await this.api.patch(`/provider-availability/${id}/`, data);
    return response.data;
  }

  async deleteAvailability(id: string): Promise<void> {
    await this.api.delete(`/provider-availability/${id}/`);
  }

  async bulkUpdateSchedule(slots: Array<{
    day_of_week: number;
    start_time: string;
    end_time: string;
    location_type?: string;
  }>): Promise<AvailabilitySlot[]> {
    const response = await this.api.post('/provider-availability/bulk_update/', slots);
    return response.data;
  }

  // ==================== TIME OFF ====================

  async getTimeOff(): Promise<TimeOff[]> {
    const response = await this.api.get('/provider-time-off/');
    return response.data;
  }

  async createTimeOff(data: {
    start_datetime: string;
    end_datetime: string;
    reason?: string;
    is_recurring_annual?: boolean;
  }): Promise<TimeOff> {
    const response = await this.api.post('/provider-time-off/', data);
    return response.data;
  }

  async deleteTimeOff(id: string): Promise<void> {
    await this.api.delete(`/provider-time-off/${id}/`);
  }

  // ==================== AVAILABLE SLOTS ====================

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

  // ==================== PROVIDER SCHEDULE ====================

  async getProviderSchedule(startDate: string, endDate: string): Promise<{
    availability: AvailabilitySlot[];
    time_off: TimeOff[];
    appointments: Appointment[];
  }> {
    const response = await this.api.get('/provider-schedule/', {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  }
}

interface TimeOff {
  id: string;
  start_datetime: string;
  end_datetime: string;
  reason: string;
  is_recurring_annual: boolean;
}

export default AppointmentService;
```

### React Hook Example

```typescript
import { useState, useEffect, useCallback } from 'react';
import AppointmentService, { Appointment, AppointmentStats } from './appointmentService';

export function useAppointments(token: string) {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [todayAppointments, setTodayAppointments] = useState<Appointment[]>([]);
  const [stats, setStats] = useState<AppointmentStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const service = new AppointmentService(token);

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      const [appts, today, statistics] = await Promise.all([
        service.getUpcomingAppointments(),
        service.getTodayAppointments(),
        service.getStats(),
      ]);
      setAppointments(appts);
      setTodayAppointments(today);
      setStats(statistics);
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const confirmAppointment = async (id: string, notes?: string) => {
    const updated = await service.confirmAppointment(id, notes);
    await refresh();
    return updated;
  };

  const rejectAppointment = async (id: string, reason: string) => {
    const updated = await service.rejectAppointment(id, reason);
    await refresh();
    return updated;
  };

  const completeAppointment = async (id: string, notes?: string) => {
    const updated = await service.completeAppointment(id, notes);
    await refresh();
    return updated;
  };

  const cancelAppointment = async (id: string, reason?: string, notes?: string) => {
    const updated = await service.cancelAppointment(id, reason, notes);
    await refresh();
    return updated;
  };

  return {
    appointments,
    todayAppointments,
    stats,
    isLoading,
    error,
    refresh,
    confirmAppointment,
    rejectAppointment,
    completeAppointment,
    cancelAppointment,
  };
}
```

---

## Related Documentation

- [Authentication API](./AUTHENTICATION_API.md)
- [Prescriptions API](../PRESCRIPTIONS_API.md)
- [Medical Records API](../MEDICAL_RECORDS_API.md)
- [Services API](../PROVIDERS_API.md)
- [Invoices API](../INVOICES_API.md)

---

## Support

For API issues or questions:
- API Documentation: https://dzmedilink.duckdns.org/docs
- Support Email: api-support@medilink.dz
