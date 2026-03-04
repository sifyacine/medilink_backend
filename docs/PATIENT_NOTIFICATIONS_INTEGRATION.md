# Medilink — Patient Notifications Integration Guide

> **Last updated:** 2026-03-04  
> **Audience:** Mobile / Web frontend developers building the patient-facing app

This guide covers **everything** needed to:
1. Register the patient's device for FCM push notifications
2. Display the notification bell (history list with `is_read`, timestamp)
3. Mark notifications as read / delete them
4. Receive real-time updates via WebSocket
5. Verify the backend is actually sending notifications to your device

---

## Table of Contents

1. [How It Works — End-to-End Flow](#1-how-it-works--end-to-end-flow)
2. [Authentication](#2-authentication)
3. [Step 1 — Register Device for FCM Push](#3-step-1--register-device-for-fcm-push)
4. [Step 2 — Display Notification History](#4-step-2--display-notification-history)
5. [Step 3 — Mark as Read / Delete](#5-step-3--mark-as-read--delete)
6. [Step 4 — Real-Time WebSocket Connection](#6-step-4--real-time-websocket-connection)
7. [FCM Push Background Messages](#7-fcm-push-background-messages)
8. [Notification Data Reference](#8-notification-data-reference)
9. [What Triggers a Patient Notification](#9-what-triggers-a-patient-notification)
10. [Testing & Verification Checklist](#10-testing--verification-checklist)
11. [Error Handling & Edge Cases](#11-error-handling--edge-cases)

---

## 1. How It Works — End-to-End Flow

```
Patient Action / Provider Action
        │
        ▼
  Django Backend (signal / view)
        │
        ├──► NotificationService.create_for_object()
        │         ├── Saves row to `notifications` table (DB)   ← shows in bell
        │         └── Sends FCM push via firebase_admin         ← wakes up phone
        │
        └──► WebSocketBroadcaster.send_to_patient()
                  └── Pushes JSON to ws/notifications/           ← live update
```

Every important event fires **all three** at once:
| Channel | Works Offline? | Persistent? | Purpose |
|---------|---------------|-------------|---------|
| **FCM Push** | ✅ Yes (OS delivers it) | ❌ No | Wakes up the app / shows banner |
| **DB (in-app)** | ✅ Yes (read later) | ✅ Yes | Notification bell history |
| **WebSocket** | ❌ No (missed if offline) | ❌ No | Instant UI update while app is open |

---

## 2. Authentication

All REST endpoints require a `Token` header. The WebSocket requires a query-string token.

```
Authorization: Token <patient_auth_token>
```

Obtain the token from the login endpoint (`POST /api/auth/login/`).

---

## 3. Step 1 — Register Device for FCM Push

This is the **most important step**. Without this, the patient will never receive push notifications.

### When to call it
- Immediately after the patient logs in
- Whenever the Firebase SDK gives you a **new** token (`onTokenRefresh`)
- Once per app session is fine; the backend deduplicates tokens

### Endpoint

```
POST /api/notifications/register/
Authorization: Token <patient_auth_token>
Content-Type: application/json
```

### Request Body

```json
{
  "token": "<FCM_DEVICE_TOKEN>",
  "device_type": "android"
}
```

| Field | Required | Values |
|-------|----------|--------|
| `token` | ✅ Yes | The FCM registration token from Firebase SDK |
| `device_type` | ✅ Yes | `"android"` \| `"ios"` \| `"web"` |

### Success Response — `201 Created` (new token) or `200 OK` (updated)

```json
{
  "success": true,
  "message": "Token registered successfully",
  "device_id": "uuid-of-stored-token"
}
```

### Flutter/Dart Example

```dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> registerFcmToken(String authToken) async {
  final fcmToken = await FirebaseMessaging.instance.getToken();
  if (fcmToken == null) return;

  final response = await http.post(
    Uri.parse('https://your-api.com/api/notifications/register/'),
    headers: {
      'Authorization': 'Token $authToken',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'token': fcmToken,
      'device_type': 'android', // or 'ios'
    }),
  );

  if (response.statusCode == 200 || response.statusCode == 201) {
    print('✅ FCM token registered');
  } else {
    print('❌ Failed to register FCM token: ${response.body}');
  }
}

// Also handle token refresh
FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
  registerFcmToken(authToken); // re-register whenever token changes
});
```

### React Native / JavaScript Example

```javascript
import messaging from '@react-native-firebase/messaging';

async function registerFcmToken(authToken) {
  const fcmToken = await messaging().getToken();

  const res = await fetch('https://your-api.com/api/notifications/register/', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${authToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      token: fcmToken,
      device_type: 'android', // or 'ios'
    }),
  });

  const data = await res.json();
  console.log('FCM registration:', data);
}

// Handle token refresh
messaging().onTokenRefresh(token => {
  registerFcmToken(authToken);
});
```

---

### Unregister on Logout

Call this when the patient logs out so they stop receiving notifications:

```
POST /api/notifications/unregister/
Authorization: Token <patient_auth_token>
Content-Type: application/json

{ "token": "<FCM_DEVICE_TOKEN>" }
```

Or to remove **all** devices at once (full logout):

```
DELETE /api/notifications/unregister-all/
Authorization: Token <patient_auth_token>
```

---

## 4. Step 2 — Display Notification History

### Endpoint

```
GET /api/notifications/
Authorization: Token <patient_auth_token>
```

### Response

```json
{
  "notifications": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "title": "✅ Appointment Confirmed",
      "body": "Your appointment with Dr. Ahmed Benali on March 10, 2026 at 02:30 PM has been confirmed.",
      "notification_type": "APPOINTMENT_CONFIRMED",
      "data": {
        "type": "APPOINTMENT_CONFIRMED",
        "priority": "HIGH",
        "action_url": "/appointments/abc-123",
        "object_type": "Appointment",
        "object_id": "abc-123"
      },
      "is_read": false,
      "timestamp": "2026-03-04T10:30:00Z",
      "created_at": "2026-03-04T10:30:00Z"
    },
    {
      "id": "b2c3d4e5-...",
      "title": "🩺 Nurse Responded",
      "body": "Fatima Boudiaf accepted your request for IV Drip Administration at 5500.00 DZD.",
      "notification_type": "NURSE_REQUEST_OFFER",
      "data": {
        "type": "NURSE_REQUEST_OFFER",
        "priority": "HIGH",
        "action_url": "/nurse-requests/42",
        "object_type": "NurseServiceRequest",
        "object_id": "42",
        "request_id": "42",
        "offer_id": "1"
      },
      "is_read": true,
      "timestamp": "2026-03-03T10:45:00Z",
      "created_at": "2026-03-03T10:45:00Z"
    }
  ],
  "count": 2,
  "unread_count": 1
}
```

### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID string | Unique notification ID — use this for mark-read/delete |
| `title` | string | Short notification title (shown in bell dropdown) |
| `body` | string | Full notification message text |
| `notification_type` | string | Category code — see [Section 8](#8-notification-data-reference) |
| `data` | object | Extra payload with `action_url`, `object_id`, etc. |
| `is_read` | boolean | `false` = unread (show badge), `true` = already seen |
| `timestamp` / `created_at` | ISO 8601 string | When the notification was created — use for display |
| `unread_count` | integer | (top-level) Total number of unread notifications |

### Flutter/Dart Example

```dart
class NotificationItem {
  final String id;
  final String title;
  final String body;
  final String notificationType;
  final Map<String, dynamic> data;
  final bool isRead;
  final DateTime timestamp;

  NotificationItem({
    required this.id,
    required this.title,
    required this.body,
    required this.notificationType,
    required this.data,
    required this.isRead,
    required this.timestamp,
  });

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    return NotificationItem(
      id: json['id'],
      title: json['title'],
      body: json['body'],
      notificationType: json['notification_type'],
      data: Map<String, dynamic>.from(json['data'] ?? {}),
      isRead: json['is_read'] ?? false,
      timestamp: DateTime.parse(json['timestamp'] ?? json['created_at']),
    );
  }
}

Future<Map<String, dynamic>> fetchNotifications(String authToken) async {
  final response = await http.get(
    Uri.parse('https://your-api.com/api/notifications/'),
    headers: {'Authorization': 'Token $authToken'},
  );

  if (response.statusCode == 200) {
    final json = jsonDecode(response.body);
    return {
      'notifications': (json['notifications'] as List)
          .map((n) => NotificationItem.fromJson(n))
          .toList(),
      'unread_count': json['unread_count'],
    };
  }
  throw Exception('Failed to load notifications');
}
```

---

## 5. Step 3 — Mark as Read / Delete

### Mark one notification as read

```
PATCH /api/notifications/<notification_id>/read/
Authorization: Token <patient_auth_token>
```

Response:
```json
{ "success": true, "message": "Notification marked as read" }
```

### Mark all as read

```
POST /api/notifications/mark-all-read/
Authorization: Token <patient_auth_token>
```

Response:
```json
{ "success": true, "message": "All notifications marked as read" }
```

### Delete one notification

```
DELETE /api/notifications/<notification_id>/
Authorization: Token <patient_auth_token>
```

### Delete all notifications

```
DELETE /api/notifications/clear-all/
Authorization: Token <patient_auth_token>
```

### Flutter/Dart Example — Mark as Read

```dart
Future<void> markAsRead(String authToken, String notificationId) async {
  await http.patch(
    Uri.parse('https://your-api.com/api/notifications/$notificationId/read/'),
    headers: {'Authorization': 'Token $authToken'},
  );
}

Future<void> markAllAsRead(String authToken) async {
  await http.post(
    Uri.parse('https://your-api.com/api/notifications/mark-all-read/'),
    headers: {'Authorization': 'Token $authToken'},
  );
}
```

---

## 6. Step 4 — Real-Time WebSocket Connection

The WebSocket pushes live events so the notification bell and screens update **instantly without polling**.

### Connection URL

```
ws://<host>/ws/notifications/?token=<patient_auth_token>
```

> **Note:** Use `wss://` in production.

### Groups the patient joins after connecting

| Group | Purpose |
|-------|---------|
| `user_<id>_notifications` | All notification types |

### Incoming message on connect

Right after connecting the server sends the current unread count:

```json
{ "type": "unread_count", "count": 3 }
```

### Sending messages TO the server

```json
{ "type": "ping" }                                       → { "type": "pong" }
{ "type": "mark_read", "id": "<notification-uuid>" }    → { "type": "unread_count", "count": N }
{ "type": "mark_all_read" }                             → { "type": "unread_count", "count": 0 }
```

### Flutter/Dart WebSocket Example

```dart
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:async';

class NotificationWebSocketService {
  WebSocketChannel? _channel;
  Timer? _pingTimer;
  final String authToken;
  final String host;

  // Callbacks the UI can listen to
  Function(int)? onUnreadCountChanged;
  Function(Map<String, dynamic>)? onNewNotification;
  Function(Map<String, dynamic>)? onAppointmentEvent;
  Function(Map<String, dynamic>)? onNurseRequestEvent;

  NotificationWebSocketService({required this.authToken, required this.host});

  void connect() {
    final uri = Uri.parse('wss://$host/ws/notifications/?token=$authToken');
    _channel = WebSocketChannel.connect(uri);

    _channel!.stream.listen(
      _onMessage,
      onError: (error) => print('WS error: $error'),
      onDone: () {
        print('WS disconnected — reconnecting in 3s');
        Future.delayed(const Duration(seconds: 3), connect);
      },
    );

    // Keep-alive ping every 30 seconds
    _pingTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _send({'type': 'ping'});
    });
  }

  void _onMessage(dynamic raw) {
    final msg = jsonDecode(raw as String) as Map<String, dynamic>;
    final type = msg['type'] as String? ?? '';

    switch (type) {
      case 'unread_count':
        onUnreadCountChanged?.call(msg['count'] as int);
        break;

      case 'notification':
        onNewNotification?.call(msg['data'] as Map<String, dynamic>);
        break;

      // ── Appointment events ──────────────────────
      case 'new_appointment':
      case 'appointment_confirmed':
      case 'appointment_rejected':
      case 'appointment_cancelled':
      case 'appointment_rescheduled':
      case 'appointment_completed':
      case 'appointment_no_show':
      case 'appointment_updated':
      case 'appointment_reminder':
        onAppointmentEvent?.call(msg);
        break;

      // ── Nurse request events ────────────────────
      case 'nurse_request_new':
      case 'nurse_request_offer':
      case 'nurse_request_accepted':
      case 'nurse_request_in_progress':
      case 'nurse_request_completed':
      case 'nurse_request_cancelled':
        onNurseRequestEvent?.call(msg);
        break;

      case 'pong':
        // Keep-alive OK
        break;
    }
  }

  void markRead(String notificationId) {
    _send({'type': 'mark_read', 'id': notificationId});
  }

  void markAllRead() {
    _send({'type': 'mark_all_read'});
  }

  void _send(Map<String, dynamic> message) {
    _channel?.sink.add(jsonEncode(message));
  }

  void disconnect() {
    _pingTimer?.cancel();
    _channel?.sink.close();
  }
}
```

### Usage in a widget

```dart
final wsService = NotificationWebSocketService(
  authToken: 'patient_token_here',
  host: 'your-api.com',
);

wsService.onUnreadCountChanged = (count) {
  setState(() => unreadCount = count);
};

wsService.onNewNotification = (data) {
  // data has the full notification object (same fields as REST list)
  setState(() => notifications.insert(0, NotificationItem.fromJson(data)));
  showToast(data['title']);
};

wsService.onAppointmentEvent = (msg) {
  // msg['data']['appointment'] = full appointment object
  // msg['data']['message'] = human-readable string
  final type = msg['type'];
  final appointment = msg['data']['appointment'];
  updateAppointmentInState(appointment);
  showToast(msg['data']['message']);
};

wsService.onNurseRequestEvent = (msg) {
  final type = msg['type'];
  final request = msg['data']['request'];
  updateNurseRequestInState(request);
  if (type == 'nurse_request_offer') {
    final offer = msg['data']['offer'];
    showOfferSheet(offer);
  }
};

wsService.connect();
```

---

## 7. FCM Push Background Messages

When the patient's app is **closed or in the background**, FCM delivers a native OS notification. The Firebase SDK handles this automatically — you handle the tap.

### Android — `AndroidManifest.xml`

Make sure the `INTERNET` permission and the `google-services.json` file are in place. No extra setup needed beyond the standard Firebase setup.

### Handle Notification Tap (deep link)

The backend always includes `data.action_url` in the FCM payload:

| Notification Type | `action_url` | Where to navigate |
|---|---|---|
| `APPOINTMENT_CONFIRMED` | `/appointments/<id>` | Appointment detail screen |
| `APPOINTMENT_CANCELLED` | `/appointments/<id>` | Appointment detail screen |
| `APPOINTMENT_RESCHEDULED` | `/appointments/<id>` | Appointment detail screen |
| `APPOINTMENT_COMPLETED` | `/appointments/<id>` | Appointment detail screen |
| `APPOINTMENT_REMINDER` | `/appointments/<id>` | Appointment detail screen |
| `NURSE_REQUEST_OFFER` | `/nurse-requests/<id>` | Nurse request detail screen |
| `NURSE_REQUEST_ACCEPTED` | `/nurse-requests/<id>` | Nurse request detail screen |
| `NURSE_REQUEST_IN_PROGRESS` | `/nurse-requests/<id>` | Nurse request detail screen |
| `NURSE_REQUEST_COMPLETED` | `/nurse-requests/<id>` | Nurse request detail screen |
| `NURSE_REQUEST_CANCELLED` | `/nurse-requests/<id>` | Nurse request detail screen |
| `INVOICE_CREATED` | `/invoices/<id>` | Invoice detail screen |
| `INVOICE_OVERDUE` | `/invoices/<id>` | Invoice detail screen |
| `PRESCRIPTION_ISSUED` | `/prescriptions/<id>` | Prescription detail screen |

### Flutter — Handle background tap

```dart
// In main() before runApp()
FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // Minimal work here — app is not running
  print('Background FCM: ${message.messageId}');
}

// In your widget (after app starts)
FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
  final actionUrl = message.data['action_url'];
  if (actionUrl != null) {
    navigateTo(actionUrl); // your router logic
  }
});

// Also check if app was opened FROM a terminated state via a notification
final initialMessage = await FirebaseMessaging.instance.getInitialMessage();
if (initialMessage != null) {
  final actionUrl = initialMessage.data['action_url'];
  if (actionUrl != null) navigateTo(actionUrl);
}

// Foreground notifications (app is open)
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  // Show in-app banner / update bell badge
  final title = message.notification?.title ?? '';
  final body  = message.notification?.body ?? '';
  showInAppBanner(title, body);
  refreshNotificationBell(); // re-fetch unread count
});
```

---

## 8. Notification Data Reference

### `notification_type` values a patient will receive

| `notification_type` | Trigger | Action URL |
|---|---|---|
| `APPOINTMENT_CREATED` | Provider booked an appointment for the patient | `/appointments/<id>` |
| `APPOINTMENT_CONFIRMED` | Provider confirmed the patient's appointment | `/appointments/<id>` |
| `APPOINTMENT_CANCELLED` | Provider or system cancelled the appointment | `/appointments/<id>` |
| `APPOINTMENT_UPDATED` | Appointment rescheduled | `/appointments/<id>` |
| `APPOINTMENT_REMINDER` | Scheduled reminder before appointment | `/appointments/<id>` |
| `APPOINTMENT_COMPLETED` | Provider marked appointment as completed | `/appointments/<id>` |
| `NURSE_REQUEST_OFFER` | Nurse accepted at patient's offered price | `/nurse-requests/<id>` |
| `NURSE_REQUEST_COUNTER_OFFER` | Nurse sent a counter-offer | `/nurse-requests/<id>` |
| `NURSE_REQUEST_ACCEPTED` | Patient accepted offer (confirmation back to patient) | `/nurse-requests/<id>` |
| `NURSE_REQUEST_IN_PROGRESS` | Nurse started the service | `/nurse-requests/<id>` |
| `NURSE_REQUEST_COMPLETED` | Nurse completed the service | `/nurse-requests/<id>` |
| `NURSE_REQUEST_CANCELLED` | Nurse or system cancelled the request | `/nurse-requests/<id>` |
| `PRESCRIPTION_ISSUED` | Doctor issued a new prescription | `/prescriptions/<id>` |
| `INVOICE_CREATED` | New invoice sent to patient | `/invoices/<id>` |
| `INVOICE_OVERDUE` | Invoice is overdue / reminder | `/invoices/<id>` |
| `PAYMENT_RECEIVED` | Payment confirmation | `/invoices/<id>` |

### `data` object fields (always present in notification)

```json
{
  "type": "APPOINTMENT_CONFIRMED",
  "priority": "HIGH",
  "action_url": "/appointments/abc-123",
  "object_type": "Appointment",
  "object_id": "abc-123"
}
```

For nurse request notifications, these extra fields are also present:
```json
{
  "request_id": "42",
  "offer_id": "1"
}
```

---

## 9. What Triggers a Patient Notification

### Appointment Events

| What happened | Channels | `notification_type` |
|---|---|---|
| Patient books appointment | ❌ Nothing (patient is the actor) | — |
| Provider creates appointment for patient | In-app + FCM + WS | `APPOINTMENT_CREATED` |
| Provider **confirms** appointment | In-app + FCM + WS | `APPOINTMENT_CONFIRMED` |
| Provider **rejects** appointment | In-app + FCM + WS | `APPOINTMENT_CANCELLED` |
| Patient cancels | ❌ Nothing (patient is the actor) | — |
| Provider cancels | In-app + FCM + WS | `APPOINTMENT_CANCELLED` |
| System auto-cancels | In-app + FCM + WS | `APPOINTMENT_CANCELLED` |
| Either side reschedules | In-app + FCM + WS | `APPOINTMENT_UPDATED` |
| Provider completes | In-app + FCM + WS | `APPOINTMENT_COMPLETED` |
| Provider marks no-show | In-app + FCM + WS | `APPOINTMENT_CANCELLED` |
| Reminder (scheduled) | In-app + FCM + WS | `APPOINTMENT_REMINDER` |
| Non-status field updated | WS only | `appointment_updated` |

### Nurse Request Events

| What happened | Channels | `notification_type` |
|---|---|---|
| Patient creates request | WS only (confirmation) | No in-app |
| Nurse responds (offer) | In-app + FCM + WS | `NURSE_REQUEST_OFFER` |
| Nurse counter-offers | In-app + FCM + WS | `NURSE_REQUEST_COUNTER_OFFER` |
| Patient accepts offer | In-app + FCM + WS (confirmation) | `NURSE_REQUEST_ACCEPTED` |
| Nurse starts service | In-app + FCM + WS | `NURSE_REQUEST_IN_PROGRESS` |
| Service completed | In-app + FCM + WS | `NURSE_REQUEST_COMPLETED` |
| Patient cancels | ❌ Nothing (patient is the actor) | — |
| Nurse/system cancels | In-app + FCM + WS | `NURSE_REQUEST_CANCELLED` |

### Other

| What happened | Channels | `notification_type` |
|---|---|---|
| Doctor issues prescription | In-app + FCM | `PRESCRIPTION_ISSUED` |
| Invoice sent | In-app + FCM | `INVOICE_CREATED` |
| Invoice overdue / reminder | In-app + FCM | `INVOICE_OVERDUE` |
| Payment received | In-app + FCM | `PAYMENT_RECEIVED` |

---

## 10. Testing & Verification Checklist

### 10.1 Verify backend is sending FCM to your device

Use this endpoint to send a **manual test push** to yourself:

```
POST /api/notifications/test/
Authorization: Token <patient_auth_token>
Content-Type: application/json

{
  "title": "Test from backend",
  "body": "If you see this, FCM is working!"
}
```

Expected response if working:
```json
{ "success": true, "message": "Test notification sent to your registered device(s)." }
```

Expected response if NOT working (no token registered):
```json
{ "success": false, "message": "No notification sent. Register a device token first..." }
```

### 10.2 Full integration test sequence

1. **Login** → get `authToken`
2. **Get FCM token** from Firebase SDK
3. **Register token** → `POST /api/notifications/register/`
4. **Send test push** → `POST /api/notifications/test/` → phone should buzz
5. **List notifications** → `GET /api/notifications/` → verify the test appears with `is_read: false`
6. **Mark as read** → `PATCH /api/notifications/<id>/read/`
7. **Verify** → `GET /api/notifications/` → `is_read` should now be `true`, `unread_count` decremented
8. **Connect WebSocket** → `ws://<host>/ws/notifications/?token=<authToken>`
9. **Trigger an appointment** from provider side → verify WS event received instantly

### 10.3 Verify FCM credentials on backend

SSH into the server and check:

```bash
# Verify firebase-credentials.json exists
ls -la /path/to/backend/firebase-credentials.json

# Check backend logs for Firebase initialization
grep "Firebase Admin SDK" /var/log/medilink/django.log
# Should show: ✅ Firebase Admin SDK initialized successfully
```

If you see `⚠️ Firebase credentials file not found`, the backend cannot send any FCM messages. Contact your backend admin to ensure `firebase-credentials.json` is in the project root.

---

## 11. Error Handling & Edge Cases

### Token expired or replaced

Firebase sometimes invalidates tokens (new device, app reinstall, etc.). The backend auto-deactivates invalid tokens. Always call `registerFcmToken()` on login AND on `onTokenRefresh`.

### WebSocket disconnected

Implement auto-reconnect with exponential backoff:

```dart
int _reconnectSeconds = 3;

void _onWsDone() {
  print('WS closed — reconnecting in $_reconnectSeconds s');
  Future.delayed(Duration(seconds: _reconnectSeconds), () {
    _reconnectSeconds = (_reconnectSeconds * 2).clamp(3, 60);
    connect();
  });
}
```

Reset `_reconnectSeconds` back to 3 after a successful connection.

### Notification already read

The `is_read` field is safe to call `PATCH` on multiple times — the endpoint is idempotent.

### App in foreground receiving FCM

When the app is **open**, FCM delivers the push to `FirebaseMessaging.onMessage` (not as a system notification). You should show an **in-app banner** and refresh the notification bell. The WebSocket will also deliver the same event simultaneously — debounce if needed.

```dart
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  // Option A: Show a SnackBar / overlay banner
  showInAppBanner(
    message.notification?.title ?? '',
    message.notification?.body ?? '',
  );
  // Option B: Let the WebSocket handle UI update (it arrives at the same time)
  // Just refresh the unread badge
  unreadCount++;
  setState(() {});
});
```

### Pagination (large notification lists)

The current `GET /api/notifications/` endpoint returns **all** notifications. For large lists, display them in a `ListView` and let the user scroll. Consider limiting client-side to the latest 50–100 after fetching.

---

## Quick Reference Card

| Task | Method | Endpoint |
|------|--------|----------|
| Register device | `POST` | `/api/notifications/register/` |
| Unregister device | `POST` | `/api/notifications/unregister/` |
| Logout (remove all) | `DELETE` | `/api/notifications/unregister-all/` |
| List notifications + unread count | `GET` | `/api/notifications/` |
| Mark one read | `PATCH` | `/api/notifications/<id>/read/` |
| Mark all read | `POST` | `/api/notifications/mark-all-read/` |
| Delete one | `DELETE` | `/api/notifications/<id>/` |
| Delete all | `DELETE` | `/api/notifications/clear-all/` |
| Test push to yourself | `POST` | `/api/notifications/test/` |
| Real-time stream | `WebSocket` | `ws://<host>/ws/notifications/?token=<token>` |
