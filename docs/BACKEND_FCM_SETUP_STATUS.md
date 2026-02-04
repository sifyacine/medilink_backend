# Backend FCM Setup Status

## Summary

**Your Django backend does NOT use `fcm-django` package.** Instead, it uses **Firebase Admin SDK directly**, which is a more flexible and modern approach.

---

## 1. FCM Package Status

### ❌ `fcm-django` is NOT installed
- **Package:** `fcm-django` is **not** in `requirements.txt`
- **INSTALLED_APPS:** `fcm_django` is **not** in `INSTALLED_APPS`
- **FCM_DJANGO_SETTINGS:** This setting does **not exist** in your project

### ✅ Firebase Admin SDK IS installed
- **Package:** `firebase-admin==7.1.0` ✅ (in `requirements.txt`)
- **Initialization:** Firebase Admin SDK is initialized in `notifications/apps.py` ✅
- **Credentials:** Uses `firebase-credentials.json` file ✅

---

## 2. Current FCM Configuration

### INSTALLED_APPS (from `core/settings/base.py`)

```python
INSTALLED_APPS = [
    # ... other apps ...
    'notifications',  # ✅ Line 81 - Your notifications app is installed
    # ... other apps ...
]
```

### Firebase Configuration (Environment Variables)

Your backend reads Firebase config from **environment variables** (not `FCM_DJANGO_SETTINGS`):

**Required in `.env`:**
```bash
# Firebase Web Config (for frontend)
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
FIREBASE_STORAGE_BUCKET=...
FIREBASE_MESSAGING_SENDER_ID=...
FIREBASE_APP_ID=...
FIREBASE_MEASUREMENT_ID=...
FIREBASE_VAPID_KEY=...

# Firebase Admin SDK (for backend sending)
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

**Location:** These are read in `notifications/views.py` → `get_firebase_config()` function.

### Firebase Admin SDK Initialization

**File:** `notifications/apps.py`

```python
class NotificationsConfig(AppConfig):
    def ready(self):
        """Initialize Firebase Admin SDK when Django starts"""
        import firebase_admin
        from firebase_admin import credentials
        
        # Reads FIREBASE_CREDENTIALS_PATH from settings/env
        # Initializes Firebase Admin SDK for sending push notifications
```

**Status:** ✅ Configured and working (if `firebase-credentials.json` exists)

---

## 3. Database Migrations Status

### Migration Files Present

```
notifications/migrations/
├── __init__.py
├── 0001_initial.py                    ✅ Creates DeviceToken model
├── 0002_remove_devicetoken_token_unique.py  ✅ Removes unique constraint
└── 0003_devicetoken_uuid_id_state.py  ✅ Syncs UUID state
```

### To Check Migration Status

Run on your server:
```bash
python manage.py showmigrations notifications
```

**Expected Output:**
```
notifications
 [X] 0001_initial
 [X] 0002_remove_devicetoken_token_unique
 [X] 0003_devicetoken_uuid_id_state
```

If any show `[ ]` (unchecked), run:
```bash
python manage.py migrate notifications
```

---

## 4. Why Not `fcm-django`?

Your project uses **Firebase Admin SDK directly** because:

1. ✅ **More Control:** Direct access to Firebase Admin SDK features
2. ✅ **Custom Implementation:** Your `DeviceToken` model and registration logic are custom
3. ✅ **Flexibility:** You can send notifications via `NotificationService` without package limitations
4. ✅ **Modern Approach:** Firebase Admin SDK is the official Google library

**You don't need `fcm-django`** - your current setup is correct!

---

## 5. What You Actually Need

### ✅ Already Configured:
- [x] `notifications` app in `INSTALLED_APPS`
- [x] `firebase-admin` package installed
- [x] Firebase Admin SDK initialization in `apps.py`
- [x] `DeviceToken` model with migrations
- [x] API endpoints (`/api/notifications/register/`, etc.)

### ⚠️ Check These:

1. **Environment Variables:**
   ```bash
   # Verify these exist in your .env file:
   FIREBASE_API_KEY=...
   FIREBASE_VAPID_KEY=...
   FIREBASE_CREDENTIALS_PATH=...
   ```

2. **Firebase Credentials File:**
   ```bash
   # Check if file exists:
   ls firebase-credentials.json
   # Or check path from env:
   echo $FIREBASE_CREDENTIALS_PATH
   ```

3. **Migrations Applied:**
   ```bash
   python manage.py showmigrations notifications
   python manage.py migrate notifications  # If needed
   ```

---

## 6. Troubleshooting 500 Error on `/api/notifications/register/`

If you're getting 500 errors, check:

1. **Migrations:** Are all migrations applied?
   ```bash
   python manage.py migrate notifications
   ```

2. **Database Schema:** Does `DeviceToken` table exist?
   ```bash
   python manage.py dbshell
   # Then: \d notifications_devicetoken
   ```

3. **Backend Logs:** Check Django logs for the actual error:
   ```bash
   # Look for: "❌ Error registering device token: ..."
   tail -f /path/to/django.log
   ```

4. **Firebase Admin SDK:** Is it initialized?
   - Check Django startup logs for: `"✅ Firebase Admin SDK initialized successfully"`
   - If you see warnings, ensure `firebase-credentials.json` exists

---

## 7. Backend Triggers – When Does the Backend Send Notifications?

The backend **does send FCM notifications** when these events happen. All go through `NotificationService.send_to_user()` (which uses `DeviceToken` and Firebase Admin SDK).

### Appointments (`appointments/signals.py` + `appointments/notifications.py`)

| Event | Who gets notified | Trigger |
|-------|-------------------|--------|
| New appointment created (by patient) | Provider | `AppointmentNotifier.notify_new_appointment` |
| New appointment created (by provider) | Patient | Same |
| Appointment confirmed | Patient | `notify_appointment_confirmed` |
| Appointment cancelled | Patient + Provider | `notify_appointment_cancelled` |
| Appointment completed | Patient | `notify_appointment_completed` |
| Appointment rescheduled | Patient | `notify_appointment_rescheduled` |
| Appointment rejected | Patient | `_notify_appointment_rejected` |

Signals are connected in `appointments/apps.py` → `ready()` imports `appointments.signals`.

### Prescriptions (`prescriptions/signals.py`)

- Notification sent when a prescription is issued (recipient gets FCM).

### Invoices (`invoices/services.py`)

- Notifications sent on invoice/payment events (create, paid, overdue, etc.) via `NotificationService.create_notification`.

### How to verify the backend is sending

1. **Test endpoint (recommended)**  
   Send a test notification to your own devices:
   ```http
   POST /api/notifications/test/
   Authorization: Token <your_token>
   Content-Type: application/json
   {}
   ```
   Optional body: `{"title": "My title", "body": "My body"}`.  
   - If you have at least one registered device token and Firebase Admin SDK is initialized, you should receive the notification.  
   - If you get `"No notification sent"`, register a device first with `POST /api/notifications/register/` (e.g. from the web app), then call test again.

2. **Trigger a real event**  
   Create or confirm an appointment (as patient or provider); the other party should get an FCM notification if they have a registered token.

3. **Logs**  
   On send, the backend logs:  
   `📬 Notification sent: X success, Y failed`  
   If Firebase is not initialized you’ll see:  
   `Firebase Admin SDK not initialized; cannot send FCM. Check firebase-credentials.json.`

---

## Summary

| Item | Status | Notes |
|------|--------|-------|
| `fcm-django` package | ❌ Not installed | **Not needed** - using Firebase Admin SDK directly |
| `firebase-admin` package | ✅ Installed | Version 7.1.0 |
| `notifications` in INSTALLED_APPS | ✅ Yes | Line 81 in `base.py` |
| Firebase Admin SDK initialized | ✅ Yes | In `notifications/apps.py` |
| Migrations created | ✅ Yes | 0001, 0002, 0003 exist |
| Migrations applied | ⚠️ Check | Run `showmigrations` to verify |
| Backend triggers (appointments, etc.) | ✅ Yes | See §7 above |
| Test endpoint | ✅ Yes | `POST /api/notifications/test/` |

**Your backend setup is correct!** The 500 error is likely due to:
- Migrations not applied on production
- Database schema mismatch (UUID vs bigint issue we fixed)
- Missing environment variables

Run `python manage.py migrate notifications` on production and check server logs for the exact error.
