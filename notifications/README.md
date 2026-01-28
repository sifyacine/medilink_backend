# Notifications App API Documentation

## Overview

The Notifications app provides a comprehensive notification system for the Medilink platform, including:

- **In-app notifications** with read/unread status
- **Push notifications** via Firebase Cloud Messaging (FCM)
- **User preferences** for notification settings
- **Device token management** for mobile/web push

## Base URL

```
/api/notifications/
```

---

## Models

### Notification

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `recipient` | FK(User) | User receiving the notification |
| `title` | String | Notification title |
| `message` | Text | Notification body |
| `image_url` | URL | Optional image for rich notifications |
| `notification_type` | Choice | Type of notification (see types below) |
| `category` | Choice | Category for grouping |
| `priority` | Choice | LOW, NORMAL, HIGH, URGENT |
| `is_read` | Boolean | Whether notification has been read |
| `read_at` | DateTime | When notification was read |
| `push_sent` | Boolean | Whether push was sent |
| `action_url` | String | URL/route for navigation |
| `data` | JSON | Additional metadata |
| `expires_at` | DateTime | Optional expiration time |
| `created_at` | DateTime | Creation timestamp |

### Notification Types

- `APPOINTMENT_CREATED` - New appointment created
- `APPOINTMENT_CONFIRMED` - Appointment confirmed
- `APPOINTMENT_CANCELLED` - Appointment cancelled
- `APPOINTMENT_UPDATED` - Appointment updated
- `APPOINTMENT_REMINDER` - Reminder for upcoming appointment
- `APPOINTMENT_COMPLETED` - Appointment completed
- `ACCOUNT_VERIFIED` - Account has been verified
- `ACCOUNT_SUSPENDED` - Account has been suspended
- `PROVIDER_APPROVED` - Provider application approved
- `PROVIDER_REFUSED` - Provider application refused
- `PATIENT_RECORD_CREATED` - Patient record created
- `PATIENT_ACCOUNT_LINKED` - Patient account linked
- `SYSTEM_ANNOUNCEMENT` - System-wide announcement
- `SYSTEM_MAINTENANCE` - Maintenance notification
- `MESSAGE` - Direct message
- `GENERAL` - General notification

### Notification Categories

- `APPOINTMENTS` - Appointment-related
- `ACCOUNT` - Account-related
- `MESSAGES` - Messages
- `SYSTEM` - System notifications
- `PROMOTIONS` - Promotional content
- `REMINDERS` - Reminders

### DeviceToken

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user` | FK(User) | Token owner |
| `token` | String | FCM device token |
| `device_type` | Choice | android, ios, web |
| `device_name` | String | Device name/model |
| `device_id` | String | Unique device identifier |
| `app_version` | String | App version |
| `is_active` | Boolean | Whether token is active |
| `failure_count` | Integer | Consecutive push failures |

### NotificationPreference

| Field | Type | Description |
|-------|------|-------------|
| `user` | OneToOne(User) | User |
| `push_enabled` | Boolean | Master push toggle |
| `push_appointments` | Boolean | Push for appointments |
| `push_messages` | Boolean | Push for messages |
| `push_reminders` | Boolean | Push for reminders |
| `push_promotions` | Boolean | Push for promotions |
| `push_system` | Boolean | Push for system |
| `email_enabled` | Boolean | Master email toggle |
| `quiet_hours_enabled` | Boolean | Enable quiet hours |
| `quiet_hours_start` | Time | Start of quiet hours |
| `quiet_hours_end` | Time | End of quiet hours |

---

## API Endpoints

### Notifications

#### List Notifications

```http
GET /api/notifications/
```

**Query Parameters:**
- `is_read` - Filter by read status (true/false)
- `category` - Filter by category
- `priority` - Filter by priority
- `notification_type` - Filter by type
- `ordering` - Order by field (-created_at, priority)

**Response:**
```json
{
  "count": 25,
  "next": "http://api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Appointment Confirmed",
      "message": "Your appointment with Dr. Smith has been confirmed.",
      "image_url": null,
      "notification_type": "APPOINTMENT_CONFIRMED",
      "notification_type_display": "Appointment Confirmed",
      "category": "APPOINTMENTS",
      "category_display": "Appointments",
      "priority": "NORMAL",
      "priority_display": "Normal",
      "is_read": false,
      "read_at": null,
      "action_url": "/appointments/uuid",
      "created_at": "2024-01-15T10:30:00Z",
      "time_ago": "2h ago"
    }
  ]
}
```

#### Get Single Notification

```http
GET /api/notifications/{id}/
```

**Note:** Automatically marks the notification as read.

#### Get Unread Notifications

```http
GET /api/notifications/unread/
```

#### Get Unread Count

```http
GET /api/notifications/unread_count/
```

**Response:**
```json
{
  "unread_count": 5
}
```

#### Get Statistics

```http
GET /api/notifications/stats/
```

**Response:**
```json
{
  "total": 50,
  "unread": 12,
  "by_category": {
    "APPOINTMENTS": 20,
    "SYSTEM": 15,
    "MESSAGES": 10,
    "REMINDERS": 5
  },
  "by_priority": {
    "LOW": 5,
    "NORMAL": 40,
    "HIGH": 4,
    "URGENT": 1
  }
}
```

#### Get Notifications by Category

```http
GET /api/notifications/by_category/
```

**Response:**
```json
{
  "APPOINTMENTS": {
    "count": 20,
    "unread": 5,
    "recent": [...]
  },
  "SYSTEM": {
    "count": 15,
    "unread": 2,
    "recent": [...]
  }
}
```

#### Mark Notifications as Read

```http
POST /api/notifications/mark_read/
```

**Request Body:**
```json
{
  "notification_ids": ["uuid1", "uuid2", "uuid3"]
}
```

If `notification_ids` is empty or omitted, marks all as read.

**Response:**
```json
{
  "message": "3 notification(s) marked as read.",
  "count": 3
}
```

#### Mark All as Read

```http
POST /api/notifications/mark_all_read/
```

#### Mark as Unread

```http
POST /api/notifications/{id}/mark_unread/
```

#### Delete Notification

```http
DELETE /api/notifications/{id}/
```

#### Clear All Notifications

```http
DELETE /api/notifications/clear_all/
```

#### Clear Read Notifications

```http
DELETE /api/notifications/clear_read/
```

---

### Device Tokens

#### List User's Device Tokens

```http
GET /api/device-tokens/
```

#### Register Device Token

```http
POST /api/device-tokens/register/
```

**Request Body:**
```json
{
  "token": "fcm-device-token-string",
  "device_type": "android",
  "device_name": "Pixel 7 Pro",
  "device_id": "unique-device-identifier",
  "app_version": "1.2.0"
}
```

**Response:**
```json
{
  "id": "uuid",
  "message": "Device registered successfully.",
  "created": true
}
```

#### Unregister Device Token

```http
POST /api/device-tokens/unregister/
```

**Request Body:**
```json
{
  "token": "fcm-device-token-string"
}
```

#### Delete Device Token

```http
DELETE /api/device-tokens/{id}/
```

---

### Notification Preferences

#### Get Preferences

```http
GET /api/preferences/
```

**Response:**
```json
{
  "push_enabled": true,
  "push_appointments": true,
  "push_messages": true,
  "push_reminders": true,
  "push_promotions": false,
  "push_system": true,
  "email_enabled": true,
  "email_appointments": true,
  "email_reminders": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Update Preferences

```http
POST /api/preferences/
```

**Request Body (partial update supported):**
```json
{
  "push_promotions": false,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "23:00:00",
  "quiet_hours_end": "07:00:00"
}
```

#### Reset Preferences to Defaults

```http
POST /api/preferences/reset/
```

---

## Firebase Cloud Messaging (FCM) Setup

### 1. Get Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select or create a project
3. Go to Project Settings > Service Accounts
4. Generate a new private key
5. Save the JSON file

### 2. Configure Django

Add to your settings or environment:

```python
# settings.py
FIREBASE_CREDENTIALS_PATH = '/path/to/firebase-credentials.json'

# Or use environment variable
import os
FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH')
```

### 3. Install Dependencies

```bash
pip install firebase-admin
```

### 4. Test Push Notifications

```python
from notifications.services import FCMService

# Send to single device
FCMService.send_to_token(
    token='device-token',
    title='Test Notification',
    body='This is a test message',
    data={'action': 'open_app'}
)

# Send to multiple devices
FCMService.send_to_tokens(
    tokens=['token1', 'token2'],
    title='Broadcast',
    body='Message to all devices'
)
```

---

## Using the NotificationService

### Creating Notifications

```python
from notifications.services import NotificationService
from notifications.models import NotificationType, NotificationCategory

# Simple notification
NotificationService.create_notification(
    recipient=user,
    title='Welcome!',
    message='Thanks for joining Medilink.',
    notification_type=NotificationType.GENERAL,
    category=NotificationCategory.SYSTEM,
)

# With related object
NotificationService.create_notification(
    recipient=patient_user,
    title='Appointment Confirmed',
    message='Your appointment with Dr. Smith is confirmed.',
    notification_type=NotificationType.APPOINTMENT_CONFIRMED,
    category=NotificationCategory.APPOINTMENTS,
    related_object=appointment,
    action_url=f'/appointments/{appointment.id}',
    send_push=True,
)

# Bulk notifications
NotificationService.create_bulk_notifications(
    recipients=[user1, user2, user3],
    title='System Maintenance',
    message='Scheduled maintenance tomorrow at 2 AM.',
    notification_type=NotificationType.SYSTEM_MAINTENANCE,
    category=NotificationCategory.SYSTEM,
)
```

---

## Integration with Appointments

The notifications app integrates with the appointments app via signals. When appointments are created, confirmed, cancelled, etc., notifications are automatically sent to the relevant users.

Example signals (in `appointments/signals.py`):

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from appointments.models import Appointment
from notifications.services import NotificationService
from notifications.models import NotificationType, NotificationCategory

@receiver(post_save, sender=Appointment)
def notify_appointment_created(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_notification(
            recipient=instance.provider.user,
            title='New Appointment Request',
            message=f'New appointment request for {instance.scheduled_date}',
            notification_type=NotificationType.APPOINTMENT_CREATED,
            category=NotificationCategory.APPOINTMENTS,
            related_object=instance,
            action_url=f'/appointments/{instance.id}',
        )
```

---

## Error Handling

### Token Failure Management

- Device tokens that fail 3 consecutive times are automatically deactivated
- Failure count resets on successful push delivery
- Inactive tokens are excluded from future push sends

### Quiet Hours

- When quiet hours are enabled, push notifications are suppressed during specified times
- In-app notifications are still created and visible
- Push notifications are not queued for later delivery

---

## Best Practices

1. **Register tokens early** - Register FCM tokens as soon as the user logs in
2. **Handle token refresh** - Update tokens when FCM refreshes them
3. **Clean up on logout** - Unregister device tokens when user logs out
4. **Use categories** - Categorize notifications for better filtering
5. **Set expiration** - Use `expires_at` for time-sensitive notifications
6. **Include action URLs** - Help users navigate directly to relevant content
