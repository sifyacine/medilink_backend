# MediLink FCM Push Notifications Integration Guide

This guide explains how to integrate Firebase Cloud Messaging (FCM) push notifications with the MediLink backend for your **website**, **Android**, and **iOS** apps.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Backend API Endpoints](#backend-api-endpoints)
3. [Firebase Setup](#firebase-setup)
4. [Web Integration](#web-integration)
5. [Android Integration (Flutter)](#android-integration-flutter)
6. [iOS Integration (Flutter)](#ios-integration-flutter)
7. [Testing Notifications](#testing-notifications)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         MEDILINK FCM FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐        ┌──────────────┐        ┌─────────────┐   │
│   │  Client  │───────▶│   Backend    │───────▶│   Firebase  │   │
│   │  (App/   │  POST  │   Django     │  FCM   │   Cloud     │   │
│   │   Web)   │ /register│             │  Send  │  Messaging  │   │
│   └──────────┘        └──────────────┘        └─────────────┘   │
│        ▲                                             │          │
│        │                                             │          │
│        └─────────────── Push Notification ───────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- **FCM Only**: No WebSockets. All notifications go through Firebase Cloud Messaging
- **Device Tokens**: Each device (web, Android, iOS) gets a unique FCM token
- **Multi-device**: Users can have multiple devices receiving notifications
- **Token Cleanup**: Invalid tokens are automatically deactivated

---

## Backend API Endpoints

Base URL: `https://your-backend-domain.com/api/notifications/`

### 1. Get Firebase Config (Public)

```http
GET /api/notifications/config/
```

**Response:**
```json
{
  "firebase_config": {
    "apiKey": "AIza...",
    "authDomain": "medilink-3cb2d.firebaseapp.com",
    "projectId": "medilink-3cb2d",
    "storageBucket": "medilink-3cb2d.appspot.com",
    "messagingSenderId": "123456789",
    "appId": "1:123456789:web:abc123",
    "measurementId": "G-XXXXXXX"
  },
  "vapid_key": "BLxxxxxxxx..."
}
```

### 2. Register Device Token (Authenticated)

```http
POST /api/notifications/register/
Authorization: Token <auth_token>
Content-Type: application/json

{
  "token": "fcm_device_token_here",
  "device_type": "android" | "ios" | "web"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Token registered successfully",
  "device_id": 123
}
```

### 3. Unregister Device Token (Authenticated)

```http
POST /api/notifications/unregister/
Authorization: Token <auth_token>
Content-Type: application/json

{
  "token": "fcm_device_token_here"
}
```

### 4. Unregister All Devices (Full Logout)

```http
DELETE /api/notifications/unregister-all/
Authorization: Token <auth_token>
```

### 5. List Registered Devices (Authenticated)

```http
GET /api/notifications/devices/
Authorization: Token <auth_token>
```

**Response:**
```json
{
  "devices": [
    {"id": 1, "device_type": "android", "created_at": "2026-02-04T10:00:00Z"},
    {"id": 2, "device_type": "web", "created_at": "2026-02-04T11:00:00Z"}
  ],
  "count": 2
}
```

---

## Firebase Setup

### 1. Firebase Console Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: **medilink-3cb2d**
3. Go to **Project Settings** → **Cloud Messaging**
4. Note your **Server Key** and **Sender ID**
5. Generate a **VAPID Key** (for web push):
   - Click "Generate Key Pair" under Web Push Certificates

### 2. Backend Environment Variables

Add to your `.env.prod`:

```bash
# Firebase Configuration
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=medilink-3cb2d.firebaseapp.com
FIREBASE_PROJECT_ID=medilink-3cb2d
FIREBASE_STORAGE_BUCKET=medilink-3cb2d.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abc123
FIREBASE_MEASUREMENT_ID=G-XXXXXXX
FIREBASE_VAPID_KEY=BLxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Path to Firebase Admin SDK credentials file
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

### 3. Firebase Admin SDK Credentials

1. Go to **Project Settings** → **Service Accounts**
2. Click "Generate new private key"
3. Save as `firebase-credentials.json` in your project root
4. **NEVER commit this file to git** (it's in `.gitignore`)

---

## Web Integration

### Step 1: Register Service Worker

The service worker is served dynamically from your backend:

```javascript
// In your web app initialization
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/firebase-messaging-sw.js')
    .then((registration) => {
      console.log('Service Worker registered:', registration);
    })
    .catch((error) => {
      console.error('Service Worker registration failed:', error);
    });
}
```

### Step 2: Initialize Firebase & Get Token

```javascript
// notification-service.js

import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

class NotificationService {
  constructor() {
    this.messaging = null;
    this.currentToken = null;
  }

  // Fetch config from backend and initialize
  async init() {
    try {
      // Fetch Firebase config from backend
      const response = await fetch('https://your-backend.com/api/notifications/config/');
      const { firebase_config, vapid_key } = await response.json();
      
      // Initialize Firebase
      const app = initializeApp(firebase_config);
      this.messaging = getMessaging(app);
      this.vapidKey = vapid_key;
      
      console.log('Firebase initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize Firebase:', error);
      return false;
    }
  }

  // Request permission and get token
  async requestPermissionAndGetToken() {
    try {
      const permission = await Notification.requestPermission();
      
      if (permission !== 'granted') {
        console.warn('Notification permission denied');
        return null;
      }

      // Get FCM token
      this.currentToken = await getToken(this.messaging, {
        vapidKey: this.vapidKey
      });
      
      console.log('FCM Token:', this.currentToken);
      return this.currentToken;
    } catch (error) {
      console.error('Failed to get FCM token:', error);
      return null;
    }
  }

  // Register token with backend
  async registerWithBackend(authToken) {
    if (!this.currentToken) {
      await this.requestPermissionAndGetToken();
    }

    try {
      const response = await fetch('https://your-backend.com/api/notifications/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`
        },
        body: JSON.stringify({
          token: this.currentToken,
          device_type: 'web'
        })
      });

      const data = await response.json();
      console.log('Token registered:', data);
      return data.success;
    } catch (error) {
      console.error('Failed to register token:', error);
      return false;
    }
  }

  // Unregister token (on logout)
  async unregisterFromBackend(authToken) {
    try {
      const response = await fetch('https://your-backend.com/api/notifications/unregister/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`
        },
        body: JSON.stringify({
          token: this.currentToken
        })
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to unregister token:', error);
      return false;
    }
  }

  // Listen for foreground messages
  onForegroundMessage(callback) {
    onMessage(this.messaging, (payload) => {
      console.log('Foreground message received:', payload);
      callback(payload);
    });
  }
}

export const notificationService = new NotificationService();
```

### Step 3: Usage in Your App

```javascript
// On app initialization / user login
import { notificationService } from './notification-service';

async function setupNotifications(userAuthToken) {
  // 1. Initialize Firebase
  await notificationService.init();
  
  // 2. Request permission & get token
  const token = await notificationService.requestPermissionAndGetToken();
  
  if (token) {
    // 3. Register with backend
    await notificationService.registerWithBackend(userAuthToken);
    
    // 4. Listen for foreground messages
    notificationService.onForegroundMessage((payload) => {
      // Show in-app notification UI
      showToast(payload.notification.title, payload.notification.body);
    });
  }
}

// On user logout
async function handleLogout(userAuthToken) {
  await notificationService.unregisterFromBackend(userAuthToken);
  // ... rest of logout logic
}
```

---

## Android Integration (Flutter)

### Step 1: Add Firebase to Android

1. In Firebase Console, add Android app with package name
2. Download `google-services.json`
3. Place in `android/app/google-services.json`

### Step 2: Add Dependencies

```yaml
# pubspec.yaml
dependencies:
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
  flutter_local_notifications: ^16.3.0
```

### Step 3: Android Configuration

```groovy
// android/build.gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}

// android/app/build.gradle
apply plugin: 'com.google.gms.google-services'
```

### Step 4: Flutter Service

```dart
// lib/services/notification_service.dart

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

// Background message handler (must be top-level)
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('Background message: ${message.messageId}');
}

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();
  
  String? _fcmToken;
  String get fcmToken => _fcmToken ?? '';

  Future<void> initialize() async {
    // Initialize Firebase
    await Firebase.initializeApp();
    
    // Set background handler
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
    
    // Request permission
    NotificationSettings settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      // Get FCM token
      _fcmToken = await _messaging.getToken();
      print('FCM Token: $_fcmToken');
      
      // Listen for token refresh
      _messaging.onTokenRefresh.listen((newToken) {
        _fcmToken = newToken;
        // Re-register with backend
        // _registerWithBackend(authToken);
      });
      
      // Initialize local notifications
      await _initLocalNotifications();
      
      // Handle foreground messages
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      
      // Handle notification tap when app is in background
      FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
    }
  }

  Future<void> _initLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings();
    
    await _localNotifications.initialize(
      const InitializationSettings(
        android: androidSettings,
        iOS: iosSettings,
      ),
      onDidReceiveNotificationResponse: (response) {
        // Handle notification tap
        print('Notification tapped: ${response.payload}');
      },
    );
  }

  void _handleForegroundMessage(RemoteMessage message) {
    print('Foreground message: ${message.notification?.title}');
    
    // Show local notification
    _localNotifications.show(
      message.hashCode,
      message.notification?.title,
      message.notification?.body,
      const NotificationDetails(
        android: AndroidNotificationDetails(
          'medilink_notifications',
          'MediLink Notifications',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(),
      ),
      payload: jsonEncode(message.data),
    );
  }

  void _handleNotificationTap(RemoteMessage message) {
    print('Notification tapped: ${message.data}');
    // Navigate based on message.data['action_url'] or message.data['type']
  }

  // Register token with backend
  Future<bool> registerWithBackend(String authToken) async {
    if (_fcmToken == null) return false;
    
    try {
      final response = await http.post(
        Uri.parse('https://your-backend.com/api/notifications/register/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $authToken',
        },
        body: jsonEncode({
          'token': _fcmToken,
          'device_type': 'android',  // or 'ios' based on Platform.isIOS
        }),
      );
      
      return response.statusCode == 200 || response.statusCode == 201;
    } catch (e) {
      print('Failed to register token: $e');
      return false;
    }
  }

  // Unregister token (on logout)
  Future<bool> unregisterFromBackend(String authToken) async {
    if (_fcmToken == null) return false;
    
    try {
      final response = await http.post(
        Uri.parse('https://your-backend.com/api/notifications/unregister/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $authToken',
        },
        body: jsonEncode({'token': _fcmToken}),
      );
      
      return response.statusCode == 200;
    } catch (e) {
      print('Failed to unregister token: $e');
      return false;
    }
  }
}
```

### Step 5: Usage in Flutter App

```dart
// main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService().initialize();
  runApp(MyApp());
}

// After user login
Future<void> onUserLogin(String authToken) async {
  await NotificationService().registerWithBackend(authToken);
}

// On user logout
Future<void> onUserLogout(String authToken) async {
  await NotificationService().unregisterFromBackend(authToken);
}
```

---

## iOS Integration (Flutter)

### Step 1: Add Firebase to iOS

1. In Firebase Console, add iOS app with bundle ID
2. Download `GoogleService-Info.plist`
3. Place in `ios/Runner/GoogleService-Info.plist`

### Step 2: iOS Configuration

Add to `ios/Runner/Info.plist`:

```xml
<key>UIBackgroundModes</key>
<array>
  <string>fetch</string>
  <string>remote-notification</string>
</array>
<key>FirebaseAppDelegateProxyEnabled</key>
<false/>
```

### Step 3: AppDelegate Setup

```swift
// ios/Runner/AppDelegate.swift
import UIKit
import Flutter
import FirebaseCore
import FirebaseMessaging

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    FirebaseApp.configure()
    
    // Request notification authorization
    UNUserNotificationCenter.current().delegate = self
    
    let authOptions: UNAuthorizationOptions = [.alert, .badge, .sound]
    UNUserNotificationCenter.current().requestAuthorization(options: authOptions) { _, _ in }
    
    application.registerForRemoteNotifications()
    
    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
  
  override func application(_ application: UIApplication,
                   didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
    Messaging.messaging().apnsToken = deviceToken
  }
}
```

The Flutter code from the Android section works for iOS as well - just change `device_type` to `'ios'`.

---

## Testing Notifications

### 1. Test from Django Shell

```python
python manage.py shell

from django.contrib.auth import get_user_model
from notifications.services import NotificationService

User = get_user_model()
user = User.objects.get(email='test@example.com')

# Send test notification
NotificationService.send_to_user(
    user=user,
    title='Test Notification',
    body='This is a test message from MediLink',
    data={'type': 'TEST', 'action_url': '/dashboard'}
)
```

### 2. Test from Firebase Console

1. Go to Firebase Console → Cloud Messaging
2. Click "Send your first message"
3. Enter title/body
4. Target: Single device → Paste FCM token
5. Send test message

### 3. Check Registered Tokens

```python
from notifications.models import DeviceToken

# List all tokens
DeviceToken.objects.all().values('user__email', 'device_type', 'is_active')

# Tokens for specific user
DeviceToken.objects.filter(user__email='test@example.com')
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `Firebase not initialized` | Check `firebase-credentials.json` path in `.env.prod` |
| `No tokens found for user` | User hasn't registered device token yet |
| `Invalid token` | Token expired or app reinstalled - re-register |
| `Service worker not registering` | Must be served from root domain (HTTPS) |
| `Permission denied (web)` | User blocked notifications in browser |

### Debug Logging

Enable detailed logging in Django:

```python
# settings/base.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'notifications': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Verify Firebase Initialization

```python
python manage.py shell

import firebase_admin
print(f"Firebase apps: {firebase_admin._apps}")
# Should show: {'[DEFAULT]': <firebase_admin.App object>}
```

---

## Notification Data Payload Structure

When sending notifications, use this data structure:

```python
NotificationService.send_to_user(
    user=user,
    title="Appointment Confirmed",
    body="Your appointment with Dr. Smith is confirmed for tomorrow at 10:00 AM",
    image_url="https://example.com/doctor-avatar.jpg",  # Optional rich notification
    data={
        'type': 'APPOINTMENT_CONFIRMED',  # For routing in app
        'priority': 'HIGH',
        'action_url': '/appointments/123',
        'appointment_id': '123',
        'object_type': 'Appointment',
        'object_id': '123',
    }
)
```

Your app should handle `data.type` to navigate to the appropriate screen.

---

## Quick Reference

| Platform | Token Registration | Device Type |
|----------|-------------------|-------------|
| Web | After user login | `'web'` |
| Android | On app start | `'android'` |
| iOS | On app start | `'ios'` |

| Endpoint | Method | Auth Required |
|----------|--------|---------------|
| `/api/notifications/config/` | GET | No |
| `/api/notifications/register/` | POST | Yes |
| `/api/notifications/unregister/` | POST | Yes |
| `/api/notifications/unregister-all/` | DELETE | Yes |
| `/api/notifications/devices/` | GET | Yes |

---

## Files Reference

| File | Purpose |
|------|---------|
| `notifications/models.py` | DeviceToken model, notification enums |
| `notifications/services.py` | NotificationService class (main service) |
| `notifications/services_core.py` | FCMService (legacy, still works) |
| `notifications/views.py` | API endpoints + service worker |
| `notifications/apps.py` | Firebase Admin SDK initialization |
| `core/urls.py` | Service worker route at root |
