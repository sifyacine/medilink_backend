# Appointments Management System - Comprehensive Report

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Data Models](#2-data-models)
3. [Enums & Constants](#3-enums--constants)
4. [API Endpoints](#4-api-endpoints)
5. [Business Logic & Workflows](#5-business-logic--workflows)
6. [Permission System](#6-permission-system)
7. [Scheduling Service](#7-scheduling-service)
8. [Dashboard Integration](#8-dashboard-integration)
9. [Error Codes](#9-error-codes)
10. [Configuration Constants](#10-configuration-constants)

---

## 1. System Overview

### Purpose
The Appointments Management System provides a complete scheduling solution for healthcare providers and patients. It supports:

- **Multi-location appointments**: Clinic visits, home visits, and online/video consultations
- **Flexible patient identification**: Works with registered users AND provider-created patient records
- **Double-booking prevention**: Intelligent conflict detection with configurable concurrent appointment limits
- **Provider availability management**: Weekly schedules with time-off/vacation handling
- **Full appointment lifecycle**: Pending → Confirmed → Completed (with cancellation, no-show, reschedule support)

### Architecture
```
┌──────────────────────────────────────────────────────────────────┐
│                      APPOINTMENTS SYSTEM                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │   SCHEDULING    │  │   APPOINTMENTS  │  │    REMINDERS    │   │
│  │    SERVICE      │  │     CORE        │  │                 │   │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤   │
│  │ • Availability  │  │ • CRUD Ops      │  │ • Scheduled     │   │
│  │ • Conflict Det. │  │ • Status Trans. │  │   Notifications │   │
│  │ • Slot Gen.     │  │ • History       │  │ • Sent Tracking │   │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘   │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐                        │
│  │   PROVIDER      │  │   PROVIDER      │                        │
│  │  AVAILABILITY   │  │   TIME OFF      │                        │
│  ├─────────────────┤  ├─────────────────┤                        │
│  │ • Weekly Sched. │  │ • Vacation      │                        │
│  │ • Multi-Slot    │  │ • Holidays      │                        │
│  │ • Location Type │  │ • Recurring     │                        │
│  └─────────────────┘  └─────────────────┘                        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Models

### 2.1 Appointment Model
The core appointment model supporting both registered patients and provider-managed patient records.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `provider` | FK → Provider | Healthcare provider (required) |
| `patient_user` | FK → User | Patient with user account (nullable) |
| `patient_record` | FK → PatientRecord | Patient without account (nullable) |
| `service` | FK → Service | Service being provided (optional) |
| `scheduled_date` | DateField | Appointment date |
| `scheduled_time` | TimeField | Start time |
| `duration_minutes` | PositiveInteger | Duration (default: 30, min: 5) |
| `location_type` | CharField | CLINIC, HOME, or ONLINE |
| `clinic_address` | FK → Address | For clinic appointments |
| `home_address` | FK → Address | For home visits |
| `meeting_link` | URLField | For online appointments |
| `status` | CharField | Current status (see enum) |
| `reason` | TextField | Chief complaint / reason for visit |
| `notes` | TextField | Additional notes (visible to patient) |
| `provider_notes` | TextField | Private notes (provider only) |
| `cancellation_reason` | CharField | Predefined cancellation reason |
| `cancellation_notes` | TextField | Additional cancellation details |
| `cancelled_by` | FK → User | Who cancelled |
| `cancelled_at` | DateTime | When cancelled |
| `created_by` | FK → User | Who created the appointment |
| `created_by_role` | CharField | PATIENT, PROVIDER, ADMIN, or SYSTEM |
| `confirmed_at` | DateTime | Confirmation timestamp |
| `completed_at` | DateTime | Completion timestamp |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

**Database Constraints:**
```python
# At least one patient identifier required
CheckConstraint(
    condition=Q(patient_user__isnull=False) | Q(patient_record__isnull=False),
    name='appointment_has_patient'
)

# Cannot have both patient types
CheckConstraint(
    condition=~(Q(patient_user__isnull=False) & Q(patient_record__isnull=False)),
    name='appointment_single_patient_type'
)
```

**Indexes:**
- `provider, scheduled_date` - Provider schedule queries
- `patient_user, scheduled_date` - Patient appointment queries
- `patient_record, scheduled_date` - Patient record queries
- `status` - Status filtering
- `scheduled_date, status` - Combined queries

### 2.2 ProviderAvailability Model
Weekly availability schedule for providers.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `provider` | FK → Provider | The provider |
| `day_of_week` | Integer | 0=Monday through 6=Sunday |
| `start_time` | TimeField | Availability start |
| `end_time` | TimeField | Availability end |
| `is_active` | Boolean | Whether this slot is active |
| `location_type` | CharField | CLINIC, HOME, ONLINE, or ALL |
| `max_appointments` | PositiveInteger | Concurrent capacity (default: 1) |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Update timestamp |

**Constraint:** `start_time < end_time`

### 2.3 ProviderTimeOff Model
Vacation, holidays, and blocked time periods.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `provider` | FK → Provider | The provider |
| `start_datetime` | DateTime | Start of time off |
| `end_datetime` | DateTime | End of time off |
| `reason` | TextField | Reason for time off |
| `is_recurring_annual` | Boolean | Repeats annually (holidays) |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Update timestamp |

### 2.4 AppointmentReminder Model
Scheduled reminders for appointments.

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key |
| `appointment` | FK → Appointment | The appointment |
| `remind_at` | DateTime | When to send reminder |
| `sent` | Boolean | Whether sent |
| `sent_at` | DateTime | When sent (nullable) |

---

## 3. Enums & Constants

### 3.1 AppointmentStatus
```python
class AppointmentStatus(TextChoices):
    PENDING = 'PENDING', 'Pending'          # Awaiting confirmation
    CONFIRMED = 'CONFIRMED', 'Confirmed'    # Provider confirmed
    CANCELLED = 'CANCELLED', 'Cancelled'    # Cancelled by either party
    COMPLETED = 'COMPLETED', 'Completed'    # Successfully completed
    NO_SHOW = 'NO_SHOW', 'No Show'          # Patient didn't show up
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'  # Rescheduled (treated as confirmed)
```

### 3.2 AppointmentLocationType
```python
class AppointmentLocationType(TextChoices):
    CLINIC = 'CLINIC', 'At Clinic'          # In-person at clinic
    HOME = 'HOME', 'Home Visit'             # Provider visits patient
    ONLINE = 'ONLINE', 'Online/Video Call'  # Telemedicine
```

### 3.3 LocationType (Availability)
```python
class LocationType(TextChoices):
    CLINIC = 'CLINIC', 'Clinic'
    HOME = 'HOME', 'Home Visit'
    ONLINE = 'ONLINE', 'Online'
    ALL = 'ALL', 'All Locations'  # Provider available for any type
```

### 3.4 CancellationReason
```python
class CancellationReason(TextChoices):
    PATIENT_REQUEST = 'PATIENT_REQUEST', 'Patient Request'
    PROVIDER_UNAVAILABLE = 'PROVIDER_UNAVAILABLE', 'Provider Unavailable'
    EMERGENCY = 'EMERGENCY', 'Emergency'
    RESCHEDULED = 'RESCHEDULED', 'Rescheduled'
    NO_RESPONSE = 'NO_RESPONSE', 'No Response'
    OTHER = 'OTHER', 'Other'
```

### 3.5 CreatedByRole
```python
class CreatedByRole(TextChoices):
    PATIENT = 'PATIENT', 'Created by Patient'
    PROVIDER = 'PROVIDER', 'Created by Provider'
    ADMIN = 'ADMIN', 'Created by Admin'
    SYSTEM = 'SYSTEM', 'System Generated'
```

### 3.6 DayOfWeek
```python
class DayOfWeek(IntegerChoices):
    MONDAY = 0, 'Monday'
    TUESDAY = 1, 'Tuesday'
    WEDNESDAY = 2, 'Wednesday'
    THURSDAY = 3, 'Thursday'
    FRIDAY = 4, 'Friday'
    SATURDAY = 5, 'Saturday'
    SUNDAY = 6, 'Sunday'
```

---

## 4. API Endpoints

### Base URL: `/api/appointments/`

### 4.1 Appointment CRUD Operations

#### List Appointments
```
GET /appointments/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (PENDING, CONFIRMED, etc.) |
| `date_from` | date | Start date filter (YYYY-MM-DD) |
| `date_to` | date | End date filter (YYYY-MM-DD) |
| `provider` | UUID | Filter by provider ID |
| `patient` | UUID | Filter by patient user or record ID |
| `location_type` | string | Filter by location type |
| `search` | string | Search in reason/notes |

**Response:**
```json
{
  "count": 10,
  "next": "http://api/appointments/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "provider": "123e4567-e89b-12d3-a456-426614174000",
      "provider_name": "Dr. John Smith",
      "patient_name": "Jane Doe",
      "service_name": "General Consultation",
      "scheduled_date": "2025-01-15",
      "scheduled_time": "10:00:00",
      "duration_minutes": 30,
      "location_type": "CLINIC",
      "location_type_display": "At Clinic",
      "status": "CONFIRMED",
      "status_display": "Confirmed",
      "reason": "Annual checkup",
      "is_upcoming": true,
      "created_at": "2025-01-10T08:00:00Z"
    }
  ]
}
```

#### Create Appointment
```
POST /appointments/
```

**Request Body (Patient creating):**
```json
{
  "provider": "123e4567-e89b-12d3-a456-426614174000",
  "scheduled_date": "2025-01-20",
  "scheduled_time": "14:00",
  "duration_minutes": 30,
  "location_type": "CLINIC",
  "service": "uuid-of-service",
  "reason": "Follow-up consultation",
  "notes": "Bringing previous test results"
}
```

**Request Body (Provider creating for patient record):**
```json
{
  "patient_record": "uuid-of-patient-record",
  "scheduled_date": "2025-01-20",
  "scheduled_time": "14:00",
  "duration_minutes": 45,
  "location_type": "HOME",
  "home_address": "uuid-of-address",
  "reason": "Post-surgery checkup",
  "notes": "Home visit required"
}
```

**Response:** `201 Created`
```json
{
  "id": "new-appointment-uuid",
  "provider": "123e4567-e89b-12d3-a456-426614174000",
  "provider_name": "Dr. John Smith",
  "patient_name": "Jane Doe",
  "scheduled_date": "2025-01-20",
  "scheduled_time": "14:00:00",
  "status": "PENDING",
  "created_by_role": "PATIENT"
}
```

#### Get Appointment Detail
```
GET /appointments/{id}/
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "123e4567-e89b-12d3-a456-426614174000",
  "provider_name": "Dr. John Smith",
  "provider_email": "dr.smith@clinic.com",
  "provider_type": "DOCTOR",
  "patient_user": "patient-uuid",
  "patient_record": null,
  "patient_name": "Jane Doe",
  "patient_email": "jane@example.com",
  "patient_phone": "+1234567890",
  "service": "service-uuid",
  "service_name": "General Consultation",
  "service_description": "30-minute general health consultation",
  "scheduled_date": "2025-01-15",
  "scheduled_time": "10:00:00",
  "duration_minutes": 30,
  "location_type": "CLINIC",
  "location_type_display": "At Clinic",
  "clinic_address": "address-uuid",
  "home_address": null,
  "meeting_link": "",
  "status": "CONFIRMED",
  "status_display": "Confirmed",
  "reason": "Annual checkup",
  "notes": "Patient notes...",
  "cancellation_reason": "",
  "cancellation_notes": "",
  "cancelled_by": null,
  "cancelled_by_name": null,
  "cancelled_at": null,
  "created_by": "creator-uuid",
  "created_by_name": "Jane Doe",
  "confirmed_at": "2025-01-11T09:00:00Z",
  "completed_at": null,
  "is_upcoming": true,
  "is_past": false,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-11T09:00:00Z"
}
```

#### Update Appointment
```
PUT/PATCH /appointments/{id}/
```

**Updatable Fields:**
- `scheduled_date`, `scheduled_time`, `duration_minutes` (with restrictions)
- `location_type`, `clinic_address`, `home_address`, `meeting_link`
- `reason`, `notes`, `provider_notes`

**Restrictions:**
- Cannot update COMPLETED or CANCELLED appointments
- For CONFIRMED appointments, only provider/admin can change time
- Validates scheduling conflicts on time changes

**Request:**
```json
{
  "reason": "Updated reason for visit",
  "notes": "Additional notes"
}
```

#### Delete Appointment
```
DELETE /appointments/{id}/
```

**Response:** `204 No Content`

---

### 4.2 Appointment Status Actions

#### Confirm Appointment
```
POST /appointments/{id}/confirm/
```

**Permission:** Provider or Admin only

**Request:**
```json
{
  "notes": "Looking forward to seeing you"
}
```

**Response:**
```json
{
  "status": "confirmed",
  "message": "Appointment confirmed successfully",
  "data": { /* Full appointment detail */ }
}
```

#### Cancel Appointment
```
POST /appointments/{id}/cancel/
```

**Permission:** Patient, Provider, or Admin

**Request:**
```json
{
  "reason": "PATIENT_REQUEST",
  "notes": "Unable to make it due to work conflict"
}
```

**Response:**
```json
{
  "status": "cancelled",
  "message": "Appointment cancelled successfully",
  "data": { /* Full appointment detail */ }
}
```

#### Complete Appointment
```
POST /appointments/{id}/complete/
```

**Permission:** Provider or Admin only

**Request:**
```json
{
  "provider_notes": "Patient is responding well to treatment"
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Appointment marked as completed",
  "data": { /* Full appointment detail */ }
}
```

#### Mark as No-Show
```
POST /appointments/{id}/no_show/
```

**Permission:** Provider or Admin only

**Response:**
```json
{
  "status": "no_show",
  "message": "Appointment marked as no-show",
  "data": { /* Full appointment detail */ }
}
```

#### Reschedule Appointment
```
POST /appointments/{id}/reschedule/
```

**Permission:**
- PENDING appointments: Patient, Provider, or Admin
- CONFIRMED appointments: Provider or Admin only

**Request:**
```json
{
  "scheduled_date": "2025-01-25",
  "scheduled_time": "15:00",
  "notes": "Rescheduled due to conflict"
}
```

**Response:**
```json
{
  "status": "rescheduled",
  "message": "Appointment rescheduled successfully",
  "data": { /* Full appointment detail */ }
}
```

---

### 4.3 Appointment Query Endpoints

#### Get Upcoming Appointments
```
GET /appointments/upcoming/
```

Returns appointments with status PENDING or CONFIRMED and date >= today.

#### Get Past Appointments
```
GET /appointments/past/
```

Returns COMPLETED, CANCELLED, NO_SHOW appointments or past dates.

#### Get Today's Appointments
```
GET /appointments/today/
```

Returns all appointments scheduled for today.

#### Get Week's Appointments
```
GET /appointments/week/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `week_offset` | integer | 0=this week, 1=next week, -1=last week |

**Response:**
```json
{
  "week_start": "2025-01-13",
  "week_end": "2025-01-19",
  "appointments": [ /* List of appointments */ ]
}
```

#### Get Appointment Statistics
```
GET /appointments/stats/
```

**Response:**
```json
{
  "total": 150,
  "pending": 10,
  "confirmed": 25,
  "completed": 100,
  "cancelled": 10,
  "no_show": 5,
  "today": 8,
  "upcoming": 35
}
```

#### Search Appointments
```
GET /appointments/search/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (patient name, email, reason, notes, service) |
| `status` | string | Filter by status |
| `date_from` | date | Start date |
| `date_to` | date | End date |
| `location_type` | string | Filter by location |
| `created_by_role` | string | PATIENT, PROVIDER, ADMIN |

#### Get Appointment History
```
GET /appointments/history/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `include_upcoming` | boolean | Include upcoming appointments (default: false) |
| `date_from` | date | Start date filter |
| `date_to` | date | End date filter |

---

### 4.4 Provider Availability Management

#### List Provider Availability
```
GET /provider-availability/
```

Returns availability slots for the authenticated provider.

**Response:**
```json
[
  {
    "id": "availability-uuid",
    "provider": "provider-uuid",
    "day_of_week": 0,
    "day_of_week_display": "Monday",
    "start_time": "09:00:00",
    "end_time": "12:00:00",
    "is_active": true,
    "location_type": "CLINIC",
    "max_appointments": 1,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

#### Create Availability Slot
```
POST /provider-availability/
```

**Request:**
```json
{
  "day_of_week": 1,
  "start_time": "14:00",
  "end_time": "18:00",
  "is_active": true,
  "location_type": "ALL",
  "max_appointments": 2
}
```

#### Get My Schedule
```
GET /provider-availability/my_schedule/
```

Returns only active availability slots for the current provider.

#### Bulk Update Availability
```
POST /provider-availability/bulk_update/
```

Replaces all existing availability with new schedule.

**Request:**
```json
[
  {
    "day_of_week": 0,
    "start_time": "09:00",
    "end_time": "12:00",
    "location_type": "CLINIC",
    "max_appointments": 1
  },
  {
    "day_of_week": 0,
    "start_time": "14:00",
    "end_time": "17:00",
    "location_type": "ONLINE",
    "max_appointments": 3
  }
]
```

---

### 4.5 Provider Time Off Management

#### List Time Off
```
GET /provider-time-off/
```

#### Create Time Off
```
POST /provider-time-off/
```

**Request:**
```json
{
  "start_datetime": "2025-02-01T00:00:00Z",
  "end_datetime": "2025-02-07T23:59:59Z",
  "reason": "Annual vacation",
  "is_recurring_annual": false
}
```

#### Get Upcoming Time Off
```
GET /provider-time-off/upcoming/
```

Returns time off periods that haven't ended yet.

---

### 4.6 Scheduling Utilities

#### Get Available Slots
```
GET /available-slots/
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | UUID | Yes | Provider ID |
| `date` | date | Yes | Date to check (YYYY-MM-DD) |
| `duration_minutes` | integer | No | Duration (default: 30) |
| `location_type` | string | No | Location type (default: CLINIC) |

**Response:**
```json
{
  "provider": "provider-uuid",
  "date": "2025-01-20",
  "duration_minutes": 30,
  "location_type": "CLINIC",
  "available_slots": [
    {
      "start_time": "09:00",
      "end_time": "09:30",
      "duration_minutes": 30
    },
    {
      "start_time": "09:15",
      "end_time": "09:45",
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

#### Get Provider Schedule
```
GET /provider-schedule/
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | UUID | No | Provider ID (defaults to current if provider) |
| `start_date` | date | No | Start of range (defaults to week start) |
| `end_date` | date | No | End of range (defaults to week end) |

**Response:**
```json
{
  "provider": "provider-uuid",
  "start_date": "2025-01-13",
  "end_date": "2025-01-19",
  "availability": [
    {
      "day_of_week": 0,
      "start_time": "09:00:00",
      "end_time": "17:00:00",
      "location_type": "CLINIC",
      "max_appointments": 1
    }
  ],
  "time_off": [
    {
      "start_datetime": "2025-01-15T00:00:00Z",
      "end_datetime": "2025-01-15T23:59:59Z",
      "reason": "Personal day"
    }
  ],
  "appointments": [
    {
      "id": "appointment-uuid",
      "scheduled_date": "2025-01-14",
      "scheduled_time": "10:00:00",
      "duration_minutes": 30,
      "status": "CONFIRMED",
      "location_type": "CLINIC"
    }
  ]
}
```

#### Get Appointment Choices
```
GET /appointment-choices/
```

**Response:**
```json
{
  "statuses": [
    {"value": "PENDING", "label": "Pending"},
    {"value": "CONFIRMED", "label": "Confirmed"},
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

### 4.7 Appointment Reminders

#### List Reminders
```
GET /appointment-reminders/
```

#### Create Reminder
```
POST /appointment-reminders/
```

**Request:**
```json
{
  "appointment": "appointment-uuid",
  "remind_at": "2025-01-14T08:00:00Z"
}
```

---

## 5. Business Logic & Workflows

### 5.1 Appointment Lifecycle

```
                    ┌─────────┐
                    │ CREATE  │
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │ PENDING │◄──────────────────┐
                    └────┬────┘                   │
                         │                        │
            ┌────────────┼────────────┐          │
            │            │            │          │
            ▼            ▼            ▼          │
       ┌─────────┐  ┌─────────┐  ┌─────────┐    │
       │CONFIRMED│  │CANCELLED│  │RESCHEDULE├───┘
       └────┬────┘  └─────────┘  └─────────┘
            │
    ┌───────┼───────┐
    │       │       │
    ▼       ▼       ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│COMPLETED│ │ NO_SHOW │ │CANCELLED│
└─────────┘ └─────────┘ └─────────┘
```

### 5.2 Status Transition Rules

| Current Status | Allowed Transitions | Who Can Transition |
|----------------|--------------------|--------------------|
| PENDING | CONFIRMED, CANCELLED, RESCHEDULED | Provider/Admin for confirm; Any participant for cancel/reschedule |
| CONFIRMED | COMPLETED, NO_SHOW, CANCELLED, RESCHEDULED | Provider/Admin for complete/no-show; Any for cancel; Provider/Admin for reschedule |
| COMPLETED | - | No transitions allowed |
| CANCELLED | - | No transitions allowed |
| NO_SHOW | - | No transitions allowed |
| RESCHEDULED | Same as CONFIRMED | Treated like CONFIRMED status |

### 5.3 Patient Identification Logic

Appointments support two patient identification methods:

1. **Patient User (`patient_user`)**: For registered patients with accounts
2. **Patient Record (`patient_record`)**: For provider-managed patients without accounts

**Rules:**
- Exactly one must be provided (enforced by database constraint)
- Patients creating appointments automatically use their user account
- Providers can create appointments for either type

### 5.4 Location-Based Requirements

| Location Type | Required Fields | Optional Fields |
|---------------|-----------------|-----------------|
| CLINIC | - | `clinic_address` |
| HOME | `home_address` | - |
| ONLINE | - | `meeting_link` (can be added later) |

---

## 6. Permission System

### 6.1 Permission Classes

| Class | Purpose |
|-------|---------|
| `IsAppointmentParticipant` | View/edit own appointments |
| `CanCreateAppointment` | Create appointments (patients for self, providers for any) |
| `CanConfirmAppointment` | Confirm appointments (provider only) |
| `CanCancelAppointment` | Cancel appointments (any participant) |
| `CanCompleteAppointment` | Complete/mark no-show (provider only) |
| `CanRescheduleAppointment` | Reschedule with status-based rules |
| `IsProviderOrAdmin` | Provider or admin access |
| `IsOwnProviderAvailability` | Manage own availability |

### 6.2 Permission Matrix

| Action | Patient | Provider | Admin |
|--------|---------|----------|-------|
| List own appointments | ✅ | ✅ | ✅ (all) |
| Create appointment | ✅ (self) | ✅ (any) | ✅ |
| View appointment | ✅ (own) | ✅ (own) | ✅ |
| Update appointment | ✅ (own, limited) | ✅ (own) | ✅ |
| Confirm | ❌ | ✅ (own) | ✅ |
| Cancel | ✅ (own) | ✅ (own) | ✅ |
| Complete | ❌ | ✅ (own) | ✅ |
| Mark No-Show | ❌ | ✅ (own) | ✅ |
| Reschedule (PENDING) | ✅ (own) | ✅ (own) | ✅ |
| Reschedule (CONFIRMED) | ❌ | ✅ (own) | ✅ |
| Manage availability | ❌ | ✅ (own) | ✅ |
| Manage time off | ❌ | ✅ (own) | ✅ |

---

## 7. Scheduling Service

### 7.1 Availability Checking

The `SchedulingService` performs comprehensive availability validation:

1. **Date Range Check**: Cannot book more than 90 days in advance
2. **Minimum Notice**: Requires at least 1 hour booking notice
3. **Time Off Check**: Ensures no overlap with provider time off
4. **Availability Schedule**: Validates against provider's weekly schedule
5. **Conflict Detection**: Prevents double-booking

### 7.2 Conflict Detection Algorithm

```python
def check_scheduling_conflict(provider, date, time, duration, exclude_id=None):
    # Calculate appointment time range
    appointment_start = datetime.combine(date, time)
    appointment_end = appointment_start + timedelta(minutes=duration)
    
    # Get max concurrent appointments from availability
    availability = get_availability_for_slot(provider, date, time)
    max_concurrent = availability.max_appointments if availability else 1
    
    # Find overlapping appointments (excluding cancelled/completed)
    overlapping = Appointment.objects.filter(
        provider=provider,
        scheduled_date=date,
        status__in=['PENDING', 'CONFIRMED', 'RESCHEDULED']
    ).exclude(pk=exclude_id)
    
    # Count actual overlaps
    conflicts = []
    for apt in overlapping:
        if apt.start < appointment_end and apt.end > appointment_start:
            conflicts.append(apt)
    
    # Check against max concurrent
    return len(conflicts) >= max_concurrent
```

### 7.3 Available Slots Generation

The system generates available time slots by:

1. Getting provider's availability for the day
2. Generating slots at configurable intervals (default: 15 minutes)
3. Filtering out slots that fail availability checks
4. Returning formatted list of available times

---

## 8. Dashboard Integration

### 8.1 Patient Dashboard

#### Booking Flow
```
1. Select Provider
   GET /providers/ → List available providers

2. Select Date & View Available Slots
   GET /available-slots/?provider={id}&date={date}
   
3. Select Service (Optional)
   GET /services/?provider={id}
   
4. Create Appointment
   POST /appointments/
   
5. View Confirmation
   GET /appointments/{id}/
```

#### My Appointments View
```
# Today's appointments
GET /appointments/today/

# Upcoming appointments
GET /appointments/upcoming/

# Past appointments
GET /appointments/history/

# Statistics
GET /appointments/stats/
```

### 8.2 Provider Dashboard

#### Daily Schedule
```
# Today's appointments
GET /appointments/today/

# This week's schedule
GET /appointments/week/

# Full schedule view
GET /provider-schedule/?start_date={}&end_date={}
```

#### Appointment Management
```
# Pending appointments requiring action
GET /appointments/?status=PENDING

# Confirm appointment
POST /appointments/{id}/confirm/

# Complete after visit
POST /appointments/{id}/complete/

# Handle no-shows
POST /appointments/{id}/no_show/
```

#### Availability Management
```
# View current availability
GET /provider-availability/my_schedule/

# Update weekly schedule
POST /provider-availability/bulk_update/

# Add time off
POST /provider-time-off/

# View upcoming time off
GET /provider-time-off/upcoming/
```

### 8.3 Dashboard Widgets

#### Patient Widgets
| Widget | Endpoint | Data |
|--------|----------|------|
| Next Appointment | `GET /appointments/upcoming/?limit=1` | Single upcoming appointment |
| This Week | `GET /appointments/week/` | Week's appointments |
| Quick Stats | `GET /appointments/stats/` | Total, upcoming, completed counts |

#### Provider Widgets
| Widget | Endpoint | Data |
|--------|----------|------|
| Today's Schedule | `GET /appointments/today/` | Today's appointments |
| Pending Actions | `GET /appointments/?status=PENDING` | Appointments needing confirmation |
| Week Overview | `GET /appointments/week/` | Calendar view data |
| Statistics | `GET /appointments/stats/` | Performance metrics |

---

## 9. Error Codes

### 9.1 Validation Errors

| Error | Description |
|-------|-------------|
| `patient_user: Either patient_user or patient_record must be provided` | Missing patient identification |
| `patient_user: Cannot specify both patient_user and patient_record` | Both patient types provided |
| `scheduled_date: Appointment cannot be scheduled in the past` | Past date selected |
| `scheduled_time: This time slot is already booked` | Double-booking conflict |
| `scheduled_time: This time slot is outside provider's available hours` | Outside availability |
| `scheduled_time: Provider is not available (time off)` | Provider on vacation |
| `scheduled_date: Cannot book more than 90 days in advance` | Too far in future |
| `scheduled_time: Appointments require at least 1 hour notice` | Insufficient notice |
| `home_address: Home address is required for home visit appointments` | Missing home address |
| `end_time: End time must be after start time` | Invalid time range |

### 9.2 Status Transition Errors

| Error | Description |
|-------|-------------|
| `Cannot confirm appointment with status {status}` | Invalid confirm transition |
| `Cannot cancel appointment with status {status}` | Trying to cancel completed |
| `Cannot complete appointment with status {status}` | Not in CONFIRMED status |
| `Cannot reschedule appointment with status {status}` | Completed or cancelled |
| `Cannot update appointment with status {status}` | Trying to modify completed/cancelled |

### 9.3 Permission Errors

| Error | Description |
|-------|-------------|
| `Only providers can access this endpoint` | Provider-only action |
| `Patients can only reschedule pending appointments` | Patient reschedule restriction |
| `Cannot change {field} on confirmed appointment` | Patient modifying confirmed |

---

## 10. Configuration Constants

### 10.1 Scheduling Service Constants

```python
class SchedulingService:
    # Minimum booking notice in hours
    MIN_BOOKING_NOTICE_HOURS = 1
    
    # Maximum advance booking in days  
    MAX_ADVANCE_BOOKING_DAYS = 90
```

### 10.2 Default Values

| Setting | Default Value | Description |
|---------|---------------|-------------|
| `duration_minutes` | 30 | Default appointment duration |
| `min_duration` | 5 | Minimum appointment duration |
| `location_type` | CLINIC | Default location type |
| `max_appointments` | 1 | Default concurrent appointments |
| `slot_interval_minutes` | 15 | Available slots interval |

### 10.3 Database Indexes

The following indexes optimize query performance:

```python
# Appointment indexes
Index(['provider', 'scheduled_date'])      # Provider schedule queries
Index(['patient_user', 'scheduled_date'])  # Patient queries
Index(['patient_record', 'scheduled_date']) # Patient record queries
Index(['status'])                          # Status filtering
Index(['scheduled_date', 'status'])        # Combined queries

# Availability indexes
Index(['provider', 'day_of_week', 'start_time'])

# Time off indexes
Index(['provider', 'start_datetime', 'end_datetime'])
```

---

## Appendix A: Complete Endpoint Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/appointments/` | List appointments |
| POST | `/appointments/` | Create appointment |
| GET | `/appointments/{id}/` | Get appointment details |
| PUT/PATCH | `/appointments/{id}/` | Update appointment |
| DELETE | `/appointments/{id}/` | Delete appointment |
| POST | `/appointments/{id}/confirm/` | Confirm appointment |
| POST | `/appointments/{id}/cancel/` | Cancel appointment |
| POST | `/appointments/{id}/complete/` | Complete appointment |
| POST | `/appointments/{id}/no_show/` | Mark as no-show |
| POST | `/appointments/{id}/reschedule/` | Reschedule appointment |
| GET | `/appointments/upcoming/` | Get upcoming appointments |
| GET | `/appointments/past/` | Get past appointments |
| GET | `/appointments/today/` | Get today's appointments |
| GET | `/appointments/week/` | Get week's appointments |
| GET | `/appointments/stats/` | Get statistics |
| GET | `/appointments/history/` | Get appointment history |
| GET | `/appointments/search/` | Advanced search |
| GET | `/appointment-reminders/` | List reminders |
| POST | `/appointment-reminders/` | Create reminder |
| GET | `/appointment-reminders/{id}/` | Get reminder |
| PUT/PATCH | `/appointment-reminders/{id}/` | Update reminder |
| DELETE | `/appointment-reminders/{id}/` | Delete reminder |
| GET | `/provider-availability/` | List availability |
| POST | `/provider-availability/` | Create availability slot |
| GET | `/provider-availability/{id}/` | Get availability slot |
| PUT/PATCH | `/provider-availability/{id}/` | Update availability |
| DELETE | `/provider-availability/{id}/` | Delete availability |
| GET | `/provider-availability/my_schedule/` | Get my schedule |
| POST | `/provider-availability/bulk_update/` | Bulk update availability |
| GET | `/provider-time-off/` | List time off |
| POST | `/provider-time-off/` | Create time off |
| GET | `/provider-time-off/{id}/` | Get time off |
| PUT/PATCH | `/provider-time-off/{id}/` | Update time off |
| DELETE | `/provider-time-off/{id}/` | Delete time off |
| GET | `/provider-time-off/upcoming/` | Get upcoming time off |
| GET | `/appointment-choices/` | Get choices (status, location) |
| GET | `/available-slots/` | Get available time slots |
| GET | `/provider-schedule/` | Get provider's full schedule |

**Total Endpoints: 35**

---

*Document Version: 1.0*  
*Last Updated: January 2025*  
*System: MediLink Appointments Management*
