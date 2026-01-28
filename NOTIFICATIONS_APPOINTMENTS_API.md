# Notifications & Appointments API Documentation

This document provides comprehensive API documentation for the **Notifications** and **Appointments** modules of the Medilink healthcare platform.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Notifications API](#notifications-api)
   - [List Notifications](#list-notifications)
   - [Get Notification](#get-notification)
   - [Create Notification](#create-notification-admin-only)
   - [Mark as Read](#mark-as-read)
   - [Mark as Unread](#mark-as-unread)
   - [Bulk Mark Read/Unread](#bulk-mark-readunread)
   - [Mark All as Read](#mark-all-as-read)
   - [Get Unread Count](#get-unread-count)
   - [Delete All Read](#delete-all-read)
   - [Delete Notification](#delete-notification)
   - [Get Notification Choices](#get-notification-choices)
4. [Device Tokens API](#device-tokens-api)
   - [Register Device Token](#register-device-token)
   - [List Device Tokens](#list-device-tokens)
   - [Deactivate Device Token](#deactivate-device-token)
5. [Appointments API](#appointments-api)
   - [List Appointments](#list-appointments)
   - [Create Appointment](#create-appointment)
   - [Get Appointment Details](#get-appointment-details)
   - [Update Appointment](#update-appointment)
   - [Confirm Appointment](#confirm-appointment)
   - [Cancel Appointment](#cancel-appointment)
   - [Complete Appointment](#complete-appointment)
   - [Mark as No-Show](#mark-as-no-show)
   - [Reschedule Appointment](#reschedule-appointment) *(NEW)*
   - [Get Appointment History](#get-appointment-history) *(NEW)*
   - [Search Appointments](#search-appointments) *(NEW)*
   - [Get Upcoming Appointments](#get-upcoming-appointments)
   - [Get Past Appointments](#get-past-appointments)
   - [Get Today's Appointments](#get-todays-appointments)
   - [Get Week's Appointments](#get-weeks-appointments) *(NEW)*
   - [Get Appointment Statistics](#get-appointment-statistics)
   - [Get Appointment Choices](#get-appointment-choices)
6. [Provider Availability API](#provider-availability-api) *(NEW)*
   - [List Availability](#list-availability)
   - [Create Availability Slot](#create-availability-slot)
   - [Update Availability Slot](#update-availability-slot)
   - [Delete Availability Slot](#delete-availability-slot)
   - [Get My Schedule](#get-my-schedule)
   - [Bulk Update Availability](#bulk-update-availability)
7. [Provider Time Off API](#provider-time-off-api) *(NEW)*
   - [List Time Off](#list-time-off)
   - [Create Time Off](#create-time-off)
   - [Update Time Off](#update-time-off)
   - [Delete Time Off](#delete-time-off)
   - [Get Upcoming Time Off](#get-upcoming-time-off)
8. [Scheduling API](#scheduling-api) *(NEW)*
   - [Get Available Slots](#get-available-slots)
   - [Get Provider Schedule](#get-provider-schedule)
9. [Enumerations](#enumerations)
10. [Notification Triggers](#notification-triggers)
11. [Error Responses](#error-responses)

---

## Overview

### Base URL
```
https://your-domain.com/api/
```

### Endpoints Summary

| Module | Endpoint | Description |
|--------|----------|-------------|
| Notifications | `/api/notifications/` | User notification management |
| Device Tokens | `/api/device-tokens/` | Push notification tokens |
| Appointments | `/api/appointments/` | Appointment scheduling |
| Provider Availability | `/api/provider-availability/` | Provider weekly schedule |
| Provider Time Off | `/api/provider-time-off/` | Vacation/holiday blocking |
| Scheduling | `/api/available-slots/` | Available time slots |

---

## Authentication

All endpoints require authentication. Include the token in the Authorization header:

```http
Authorization: Token <your-token>
```

---

## Notifications API

### List Notifications

Get all notifications for the authenticated user.

**Endpoint:** `GET /api/notifications/`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `is_read` | boolean | Filter by read status (`true` or `false`) |
| `type` | string | Filter by notification type |
| `priority` | string | Filter by priority level |
| `search` | string | Search in title and message |

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Appointment Confirmed",
      "message": "Your appointment with Dr. Smith on January 15, 2025 at 10:00 AM has been confirmed.",
      "notification_type": "APPOINTMENT_CONFIRMED",
      "notification_type_display": "Appointment Confirmed",
      "priority": "HIGH",
      "is_read": false,
      "action_url": "/appointments/abc123",
      "created_at": "2025-01-10T14:30:00Z"
    }
  ]
}
```

---

### Get Notification

Get details of a specific notification.

**Endpoint:** `GET /api/notifications/{id}/`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `auto_read` | boolean | Automatically mark as read when viewed |

**Response (200 OK):**
```json
{
  "id": 1,
  "recipient": 5,
  "recipient_email": "patient@example.com",
  "title": "Appointment Confirmed",
  "message": "Your appointment has been confirmed.",
  "notification_type": "APPOINTMENT_CONFIRMED",
  "notification_type_display": "Appointment Confirmed",
  "priority": "HIGH",
  "priority_display": "High",
  "related_object_type": "appointment",
  "related_object_id": "abc123-uuid",
  "is_read": false,
  "read_at": null,
  "action_url": "/appointments/abc123",
  "data": {},
  "created_at": "2025-01-10T14:30:00Z",
  "updated_at": "2025-01-10T14:30:00Z"
}
```

---

### Create Notification (Admin Only)

Create a new notification for a user.

**Endpoint:** `POST /api/notifications/`

**Request Body:**
```json
{
  "recipient": 5,
  "title": "System Announcement",
  "message": "Scheduled maintenance on Sunday.",
  "notification_type": "SYSTEM_ANNOUNCEMENT",
  "priority": "NORMAL",
  "action_url": "/announcements"
}
```

**Response (201 Created):**
```json
{
  "id": 10,
  "recipient": 5,
  "title": "System Announcement",
  "message": "Scheduled maintenance on Sunday.",
  "notification_type": "SYSTEM_ANNOUNCEMENT",
  "priority": "NORMAL",
  "action_url": "/announcements",
  "data": {},
  "created_at": "2025-01-10T15:00:00Z"
}
```

---

### Mark as Read

Mark a single notification as read.

**Endpoint:** `POST /api/notifications/{id}/mark_read/`

**Response (200 OK):**
```json
{
  "status": "marked as read"
}
```

---

### Mark as Unread

Mark a single notification as unread.

**Endpoint:** `POST /api/notifications/{id}/mark_unread/`

**Response (200 OK):**
```json
{
  "status": "marked as unread"
}
```

---

### Bulk Mark Read/Unread

Mark multiple notifications as read or unread.

**Endpoint:** `POST /api/notifications/mark_bulk/`

**Request Body:**
```json
{
  "notification_ids": [1, 2, 3],
  "is_read": true
}
```

If `notification_ids` is empty or omitted, all notifications will be affected.

**Response (200 OK):**
```json
{
  "status": "success",
  "updated_count": 3,
  "is_read": true
}
```

---

### Mark All as Read

Mark all unread notifications as read.

**Endpoint:** `POST /api/notifications/mark_all_read/`

**Response (200 OK):**
```json
{
  "status": "success",
  "marked_count": 15
}
```

---

### Get Unread Count

Get the count of unread and total notifications.

**Endpoint:** `GET /api/notifications/unread_count/`

**Response (200 OK):**
```json
{
  "unread_count": 5,
  "total_count": 25
}
```

---

### Delete All Read

Delete all read notifications.

**Endpoint:** `DELETE /api/notifications/delete_all_read/`

**Response (200 OK):**
```json
{
  "status": "success",
  "deleted_count": 20
}
```

---

### Delete Notification

Delete a specific notification.

**Endpoint:** `DELETE /api/notifications/{id}/`

**Response (204 No Content)**

---

### Get Notification Choices

Get available notification types and priorities.

**Endpoint:** `GET /api/notification-choices/`

**Response (200 OK):**
```json
{
  "notification_types": [
    {"value": "APPOINTMENT_CREATED", "label": "Appointment Created"},
    {"value": "APPOINTMENT_CONFIRMED", "label": "Appointment Confirmed"},
    {"value": "APPOINTMENT_CANCELLED", "label": "Appointment Cancelled"},
    {"value": "APPOINTMENT_UPDATED", "label": "Appointment Updated"},
    {"value": "APPOINTMENT_REMINDER", "label": "Appointment Reminder"},
    {"value": "APPOINTMENT_COMPLETED", "label": "Appointment Completed"},
    {"value": "ACCOUNT_VERIFIED", "label": "Account Verified"},
    {"value": "PROVIDER_APPROVED", "label": "Provider Approved"},
    {"value": "SYSTEM_ANNOUNCEMENT", "label": "System Announcement"},
    {"value": "GENERAL", "label": "General Notification"}
  ],
  "priorities": [
    {"value": "LOW", "label": "Low"},
    {"value": "NORMAL", "label": "Normal"},
    {"value": "HIGH", "label": "High"},
    {"value": "URGENT", "label": "Urgent"}
  ]
}
```

---

## Device Tokens API

### Register Device Token

Register a device token for push notifications.

**Endpoint:** `POST /api/device-tokens/`

**Request Body:**
```json
{
  "token": "fcm-device-token-string",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "token": "fcm-device-token-string",
  "device_type": "android",
  "device_name": "Samsung Galaxy S21",
  "is_active": true,
  "created_at": "2025-01-10T14:00:00Z",
  "last_used_at": null
}
```

---

### List Device Tokens

List all device tokens for the authenticated user.

**Endpoint:** `GET /api/device-tokens/`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "token": "fcm-token-1",
    "device_type": "android",
    "device_name": "Samsung Galaxy S21",
    "is_active": true,
    "created_at": "2025-01-10T14:00:00Z",
    "last_used_at": "2025-01-10T16:00:00Z"
  }
]
```

---

### Deactivate Device Token

Deactivate a device token (e.g., on logout).

**Endpoint:** `POST /api/device-tokens/deactivate/`

**Request Body:**
```json
{
  "token": "fcm-device-token-to-deactivate"
}
```

**Response (200 OK):**
```json
{
  "status": "token deactivated"
}
```

---

## Appointments API

### List Appointments

Get appointments based on user role.

**Endpoint:** `GET /api/appointments/`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (PENDING, CONFIRMED, etc.) |
| `date_from` | date | Filter appointments from this date |
| `date_to` | date | Filter appointments until this date |
| `provider` | integer | Filter by provider ID |
| `patient` | integer/uuid | Filter by patient user or record ID |
| `location_type` | string | Filter by location type |
| `search` | string | Search in reason and notes |

**Response (200 OK):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "abc123-uuid",
      "provider": 5,
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
      "created_at": "2025-01-10T14:00:00Z"
    }
  ]
}
```

---

### Create Appointment

Create a new appointment.

**Endpoint:** `POST /api/appointments/`

**For Patients:**
```json
{
  "provider": 5,
  "scheduled_date": "2025-01-20",
  "scheduled_time": "14:00:00",
  "duration_minutes": 30,
  "location_type": "CLINIC",
  "service": 1,
  "reason": "Follow-up consultation"
}
```

**For Providers (with existing patient record):**
```json
{
  "patient_record": 10,
  "scheduled_date": "2025-01-20",
  "scheduled_time": "14:00:00",
  "duration_minutes": 45,
  "location_type": "HOME",
  "home_address": 5,
  "reason": "Home visit for physical therapy"
}
```

**For Providers (with registered patient):**
```json
{
  "patient_user": 15,
  "scheduled_date": "2025-01-20",
  "scheduled_time": "16:00:00",
  "duration_minutes": 30,
  "location_type": "ONLINE",
  "reason": "Telehealth consultation"
}
```

**Response (201 Created):**
```json
{
  "id": "new-appointment-uuid",
  "provider": 5,
  "provider_name": "Dr. John Smith",
  "patient_user": 15,
  "patient_record": null,
  "patient_name": "Jane Doe",
  "scheduled_date": "2025-01-20",
  "scheduled_time": "14:00:00",
  "duration_minutes": 30,
  "location_type": "CLINIC",
  "status": "PENDING",
  "reason": "Follow-up consultation",
  "created_at": "2025-01-10T14:30:00Z"
}
```

---

### Get Appointment Details

Get detailed information about an appointment.

**Endpoint:** `GET /api/appointments/{id}/`

**Response (200 OK):**
```json
{
  "id": "abc123-uuid",
  "provider": 5,
  "provider_name": "Dr. John Smith",
  "provider_email": "doctor@example.com",
  "provider_type": "DOCTOR",
  "patient_user": 15,
  "patient_record": null,
  "patient_name": "Jane Doe",
  "patient_email": "jane@example.com",
  "patient_phone": "+1234567890",
  "service": 1,
  "service_name": "General Consultation",
  "service_description": "Standard medical consultation",
  "scheduled_date": "2025-01-20",
  "scheduled_time": "14:00:00",
  "duration_minutes": 30,
  "location_type": "CLINIC",
  "location_type_display": "At Clinic",
  "clinic_address": 10,
  "home_address": null,
  "meeting_link": "",
  "status": "CONFIRMED",
  "status_display": "Confirmed",
  "reason": "Follow-up consultation",
  "notes": "Patient prefers afternoon appointments",
  "cancellation_reason": "",
  "cancellation_notes": "",
  "cancelled_by": null,
  "cancelled_by_name": null,
  "cancelled_at": null,
  "created_by": 15,
  "created_by_name": "Jane Doe",
  "confirmed_at": "2025-01-11T09:00:00Z",
  "completed_at": null,
  "is_upcoming": true,
  "is_past": false,
  "created_at": "2025-01-10T14:30:00Z",
  "updated_at": "2025-01-11T09:00:00Z"
}
```

---

### Update Appointment

Update appointment details (before completion/cancellation).

**Endpoint:** `PUT /api/appointments/{id}/` or `PATCH /api/appointments/{id}/`

**Request Body:**
```json
{
  "scheduled_date": "2025-01-22",
  "scheduled_time": "15:00:00",
  "notes": "Rescheduled per patient request"
}
```

**Response (200 OK):** Returns updated appointment details.

---

### Confirm Appointment

Confirm a pending appointment (provider only).

**Endpoint:** `POST /api/appointments/{id}/confirm/`

**Request Body (optional):**
```json
{
  "notes": "Confirmed. Please arrive 10 minutes early."
}
```

**Response (200 OK):**
```json
{
  "status": "confirmed",
  "message": "Appointment confirmed successfully",
  "data": { /* full appointment details */ }
}
```

---

### Cancel Appointment

Cancel an appointment (patient or provider).

**Endpoint:** `POST /api/appointments/{id}/cancel/`

**Request Body:**
```json
{
  "reason": "PATIENT_REQUEST",
  "notes": "Unexpected schedule conflict"
}
```

**Cancellation Reasons:**
- `PATIENT_REQUEST` - Patient requested cancellation
- `PROVIDER_UNAVAILABLE` - Provider not available
- `EMERGENCY` - Emergency situation
- `RESCHEDULED` - Being rescheduled
- `NO_RESPONSE` - No response from other party
- `OTHER` - Other reason

**Response (200 OK):**
```json
{
  "status": "cancelled",
  "message": "Appointment cancelled successfully",
  "data": { /* full appointment details */ }
}
```

---

### Complete Appointment

Mark an appointment as completed (provider only).

**Endpoint:** `POST /api/appointments/{id}/complete/`

**Request Body (optional):**
```json
{
  "provider_notes": "Patient in good health. Recommended annual checkup."
}
```

**Response (200 OK):**
```json
{
  "status": "completed",
  "message": "Appointment marked as completed",
  "data": { /* full appointment details */ }
}
```

---

### Mark as No-Show

Mark an appointment as no-show (provider only).

**Endpoint:** `POST /api/appointments/{id}/no_show/`

**Response (200 OK):**
```json
{
  "status": "no_show",
  "message": "Appointment marked as no-show",
  "data": { /* full appointment details */ }
}
```

---

### Get Upcoming Appointments

Get all upcoming appointments.

**Endpoint:** `GET /api/appointments/upcoming/`

Returns appointments with status PENDING or CONFIRMED scheduled for today or later.

---

### Get Past Appointments

Get past/historical appointments.

**Endpoint:** `GET /api/appointments/past/`

Returns completed, cancelled, or no-show appointments, and past-dated appointments.

---

### Get Today's Appointments

Get appointments scheduled for today.

**Endpoint:** `GET /api/appointments/today/`

---

### Get Appointment Statistics

Get summary statistics for appointments.

**Endpoint:** `GET /api/appointments/stats/`

**Response (200 OK):**
```json
{
  "total": 50,
  "pending": 5,
  "confirmed": 10,
  "completed": 30,
  "cancelled": 3,
  "no_show": 2,
  "today": 4,
  "upcoming": 15
}
```

---

### Get Appointment Choices

Get available status and location type options.

**Endpoint:** `GET /api/appointment-choices/`

**Response (200 OK):**
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

### Reschedule Appointment

Reschedule an existing appointment to a new date/time.

**Endpoint:** `POST /api/appointments/{id}/reschedule/`

**Permissions:**
- PENDING appointments: Patient or Provider can reschedule
- CONFIRMED appointments: Only Provider or Admin can reschedule
- COMPLETED/CANCELLED: Cannot be rescheduled

**Request Body:**
```json
{
  "scheduled_date": "2025-01-25",
  "scheduled_time": "15:00:00",
  "notes": "Rescheduled due to conflict"
}
```

**Response (200 OK):**
```json
{
  "status": "rescheduled",
  "message": "Appointment rescheduled successfully",
  "data": {
    "id": "abc123-uuid",
    "scheduled_date": "2025-01-25",
    "scheduled_time": "15:00:00",
    "status": "RESCHEDULED"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "scheduled_time": ["This time slot is already booked."]
}
```

---

### Get Appointment History

Get appointment history for the current user (past/completed/cancelled).

**Endpoint:** `GET /api/appointments/history/`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `include_upcoming` | boolean | Include upcoming appointments (default: false) |
| `date_from` | date | Filter from this date |
| `date_to` | date | Filter until this date |

**Response (200 OK):**
```json
{
  "count": 15,
  "results": [
    {
      "id": "abc123-uuid",
      "provider_name": "Dr. John Smith",
      "patient_name": "Jane Doe",
      "service_name": "General Consultation",
      "scheduled_date": "2025-01-10",
      "scheduled_time": "10:00:00",
      "status": "COMPLETED",
      "status_display": "Completed",
      "created_by_role": "PATIENT",
      "created_by_role_display": "Created by Patient",
      "completed_at": "2025-01-10T11:00:00Z"
    }
  ]
}
```

---

### Search Appointments

Advanced search for appointments with multiple filters.

**Endpoint:** `GET /api/appointments/search/`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (patient name, email, reason, notes, service) |
| `status` | string | Filter by status |
| `date_from` | date | Start date |
| `date_to` | date | End date |
| `location_type` | string | Filter by location type |
| `created_by_role` | string | Filter by who created (PATIENT, PROVIDER, ADMIN) |

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "abc123-uuid",
      "provider_name": "Dr. Smith",
      "patient_name": "John Doe",
      "scheduled_date": "2025-01-20",
      "status": "CONFIRMED"
    }
  ]
}
```

---

### Get Week's Appointments

Get appointments for a specific week.

**Endpoint:** `GET /api/appointments/week/`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `week_offset` | integer | Weeks from current (0=this week, 1=next, -1=last) |

**Response (200 OK):**
```json
{
  "week_start": "2025-01-20",
  "week_end": "2025-01-26",
  "appointments": [
    {
      "id": "abc123-uuid",
      "scheduled_date": "2025-01-21",
      "scheduled_time": "09:00:00",
      "status": "CONFIRMED"
    }
  ]
}
```

---

## Provider Availability API

Manage provider weekly availability schedules. Providers can define recurring time slots when they're available for appointments.

### List Availability

Get availability slots for the current provider.

**Endpoint:** `GET /api/provider-availability/`

**Response (200 OK):**
```json
[
  {
    "id": "slot-uuid",
    "provider": 5,
    "day_of_week": 0,
    "day_of_week_display": "Monday",
    "start_time": "09:00:00",
    "end_time": "12:00:00",
    "is_active": true,
    "location_type": "CLINIC",
    "max_appointments": 1,
    "created_at": "2025-01-01T00:00:00Z"
  },
  {
    "id": "slot-uuid-2",
    "provider": 5,
    "day_of_week": 0,
    "day_of_week_display": "Monday",
    "start_time": "14:00:00",
    "end_time": "17:00:00",
    "is_active": true,
    "location_type": "ALL",
    "max_appointments": 2,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### Create Availability Slot

Add a new availability slot.

**Endpoint:** `POST /api/provider-availability/`

**Request Body:**
```json
{
  "day_of_week": 1,
  "start_time": "09:00:00",
  "end_time": "12:00:00",
  "location_type": "CLINIC",
  "max_appointments": 1,
  "is_active": true
}
```

**Day of Week Values:**
| Value | Day |
|-------|-----|
| 0 | Monday |
| 1 | Tuesday |
| 2 | Wednesday |
| 3 | Thursday |
| 4 | Friday |
| 5 | Saturday |
| 6 | Sunday |

---

### Get My Schedule

Get the current provider's complete weekly schedule.

**Endpoint:** `GET /api/provider-availability/my_schedule/`

**Response (200 OK):**
```json
[
  {
    "day_of_week": 0,
    "day_of_week_display": "Monday",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "location_type": "ALL"
  }
]
```

---

### Bulk Update Availability

Replace all availability with a new schedule.

**Endpoint:** `POST /api/provider-availability/bulk_update/`

**Request Body:**
```json
[
  {
    "day_of_week": 0,
    "start_time": "09:00:00",
    "end_time": "12:00:00",
    "location_type": "CLINIC"
  },
  {
    "day_of_week": 0,
    "start_time": "14:00:00",
    "end_time": "17:00:00",
    "location_type": "ALL"
  },
  {
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "location_type": "ALL"
  }
]
```

---

## Provider Time Off API

Manage provider time off periods for vacations, holidays, and blocked times.

### List Time Off

Get time off periods for the current provider.

**Endpoint:** `GET /api/provider-time-off/`

**Response (200 OK):**
```json
[
  {
    "id": "timeoff-uuid",
    "provider": 5,
    "start_datetime": "2025-02-01T00:00:00Z",
    "end_datetime": "2025-02-07T23:59:59Z",
    "reason": "Annual vacation",
    "is_recurring_annual": false
  }
]
```

---

### Create Time Off

Block out a time period.

**Endpoint:** `POST /api/provider-time-off/`

**Request Body:**
```json
{
  "start_datetime": "2025-02-01T00:00:00Z",
  "end_datetime": "2025-02-07T23:59:59Z",
  "reason": "Annual vacation",
  "is_recurring_annual": false
}
```

---

### Get Upcoming Time Off

Get upcoming time off periods only.

**Endpoint:** `GET /api/provider-time-off/upcoming/`

---

## Scheduling API

Endpoints for checking availability and finding open appointment slots.

### Get Available Slots

Get available time slots for a provider on a specific date.

**Endpoint:** `GET /api/available-slots/`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | uuid | Yes | Provider ID |
| `date` | date | Yes | Date to check (YYYY-MM-DD) |
| `duration_minutes` | integer | No | Appointment duration (default: 30) |
| `location_type` | string | No | Location type (default: CLINIC) |

**Response (200 OK):**
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
      "start_time": "09:30",
      "end_time": "10:00",
      "duration_minutes": 30
    },
    {
      "start_time": "14:00",
      "end_time": "14:30",
      "duration_minutes": 30
    }
  ]
}
```

---

### Get Provider Schedule

Get a provider's complete schedule including availability, time off, and appointments.

**Endpoint:** `GET /api/provider-schedule/`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | uuid | No | Provider ID (optional if user is provider) |
| `start_date` | date | No | Start of date range (default: current week start) |
| `end_date` | date | No | End of date range (default: current week end) |

**Response (200 OK):**
```json
{
  "provider": "provider-uuid",
  "start_date": "2025-01-20",
  "end_date": "2025-01-26",
  "availability": [
    {
      "day_of_week": 0,
      "start_time": "09:00:00",
      "end_time": "17:00:00",
      "location_type": "ALL",
      "max_appointments": 1
    }
  ],
  "time_off": [
    {
      "start_datetime": "2025-01-22T00:00:00Z",
      "end_datetime": "2025-01-22T23:59:59Z",
      "reason": "Personal day"
    }
  ],
  "appointments": [
    {
      "id": "appt-uuid",
      "scheduled_date": "2025-01-21",
      "scheduled_time": "10:00:00",
      "duration_minutes": 30,
      "status": "CONFIRMED",
      "location_type": "CLINIC"
    }
  ]
}
```

---

## Enumerations

### Notification Types
| Value | Description |
|-------|-------------|
| `APPOINTMENT_CREATED` | New appointment scheduled |
| `APPOINTMENT_CONFIRMED` | Appointment confirmed by provider |
| `APPOINTMENT_CANCELLED` | Appointment cancelled |
| `APPOINTMENT_UPDATED` | Appointment details updated |
| `APPOINTMENT_REMINDER` | Upcoming appointment reminder |
| `APPOINTMENT_COMPLETED` | Appointment completed |
| `ACCOUNT_VERIFIED` | User account verified |
| `ACCOUNT_SUSPENDED` | User account suspended |
| `PROVIDER_APPROVED` | Provider application approved |
| `PROVIDER_REFUSED` | Provider application refused |
| `PATIENT_RECORD_CREATED` | Patient record created |
| `PATIENT_ACCOUNT_LINKED` | Patient account linked |
| `SYSTEM_ANNOUNCEMENT` | System-wide announcement |
| `SYSTEM_MAINTENANCE` | Scheduled maintenance notice |
| `MESSAGE` | Direct message |
| `GENERAL` | General notification |

### Notification Priorities
| Value | Description |
|-------|-------------|
| `LOW` | Low priority |
| `NORMAL` | Normal priority (default) |
| `HIGH` | High priority |
| `URGENT` | Urgent/critical |

### Appointment Statuses
| Value | Description |
|-------|-------------|
| `PENDING` | Awaiting confirmation |
| `CONFIRMED` | Confirmed by provider |
| `CANCELLED` | Cancelled by either party |
| `COMPLETED` | Successfully completed |
| `NO_SHOW` | Patient did not show up |
| `RESCHEDULED` | Rescheduled to new date/time |

### Created By Role
| Value | Description |
|-------|-------------|
| `PATIENT` | Appointment created by patient |
| `PROVIDER` | Appointment created by provider |
| `ADMIN` | Appointment created by admin |
| `SYSTEM` | System-generated appointment |

### Location Types
| Value | Description |
|-------|-------------|
| `CLINIC` | In-person at clinic |
| `HOME` | Home visit by provider |
| `ONLINE` | Video/telehealth call |

### Day of Week
| Value | Day |
|-------|-----|
| `0` | Monday |
| `1` | Tuesday |
| `2` | Wednesday |
| `3` | Thursday |
| `4` | Friday |
| `5` | Saturday |
| `6` | Sunday |

### Device Types
| Value | Description |
|-------|-------------|
| `android` | Android device |
| `ios` | iOS device |
| `web` | Web browser |

---

## Notification Triggers

Notifications are automatically created for the following events:

### Appointment Created
- **When:** New appointment is created
- **Recipients:**
  - Provider receives notification when patient creates appointment
  - Patient receives notification when provider creates appointment for them
- **Type:** `APPOINTMENT_CREATED`
- **Priority:** `HIGH`

### Appointment Confirmed
- **When:** Provider confirms a pending appointment
- **Recipients:** Patient
- **Type:** `APPOINTMENT_CONFIRMED`
- **Priority:** `HIGH`

### Appointment Cancelled
- **When:** Either party cancels the appointment
- **Recipients:**
  - Provider receives notification if patient cancels
  - Patient receives notification if provider cancels
- **Type:** `APPOINTMENT_CANCELLED`
- **Priority:** `HIGH`

### Appointment Completed
- **When:** Provider marks appointment as completed
- **Recipients:** Patient
- **Type:** `APPOINTMENT_COMPLETED`
- **Priority:** `NORMAL`

### Appointment Rescheduled
- **When:** Appointment date/time is changed
- **Recipients:** Both patient and provider
- **Type:** `APPOINTMENT_UPDATED`
- **Priority:** `HIGH`

---

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"],
  "non_field_errors": ["General error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "detail": "An unexpected error occurred."
}
```

---

## Usage Examples

### Patient Books Appointment (JavaScript/Fetch)

```javascript
const response = await fetch('/api/appointments/', {
  method: 'POST',
  headers: {
    'Authorization': 'Token YOUR_TOKEN',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    provider: 5,
    scheduled_date: '2025-01-20',
    scheduled_time: '14:00:00',
    location_type: 'CLINIC',
    service: 1,
    reason: 'Annual checkup'
  })
});

const appointment = await response.json();
```

### Provider Confirms Appointment

```javascript
const response = await fetch(`/api/appointments/${appointmentId}/confirm/`, {
  method: 'POST',
  headers: {
    'Authorization': 'Token PROVIDER_TOKEN',
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    notes: 'Please arrive 10 minutes early'
  })
});
```

### Fetch Unread Notifications

```javascript
const response = await fetch('/api/notifications/?is_read=false', {
  headers: {
    'Authorization': 'Token YOUR_TOKEN',
  }
});

const { results } = await response.json();
```

### Mark All Notifications as Read

```javascript
const response = await fetch('/api/notifications/mark_all_read/', {
  method: 'POST',
  headers: {
    'Authorization': 'Token YOUR_TOKEN',
  }
});
```

---

## Frontend Integration Guide

### Notification Badge

Poll the unread count endpoint periodically:

```javascript
// Poll every 30 seconds
setInterval(async () => {
  const response = await fetch('/api/notifications/unread_count/', {
    headers: { 'Authorization': `Token ${token}` }
  });
  const { unread_count } = await response.json();
  updateBadge(unread_count);
}, 30000);
```

### Appointment Status Flow

```
PENDING → CONFIRMED → COMPLETED
    ↓         ↓          
CANCELLED  NO_SHOW    
```

### Push Notifications

1. Register FCM token on app launch:
```javascript
const token = await firebase.messaging().getToken();
await fetch('/api/device-tokens/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${authToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    token: token,
    device_type: 'android',
    device_name: 'User Device'
  })
});
```

2. Deactivate token on logout:
```javascript
await fetch('/api/device-tokens/deactivate/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${authToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ token: fcmToken })
});
```
