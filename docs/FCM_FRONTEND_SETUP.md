# FCM Push Notifications - Frontend Setup Guide

## Task: Complete FCM Push Notifications Setup for Web Frontend

### Current Status:
- Backend is Django REST Framework at `https://dzmedilink.duckdns.org`
- Firebase Admin SDK is configured with `firebase-credentials.json` (project: `medilink-3cb2d`)
- Backend `.env` has all Firebase web config variables set
- `DeviceToken` model exists for storing FCM tokens
- Notification signals are working (triggered on appointment create/update)

---

## What's Already Working (Backend):

1. Backend can send FCM push notifications via `NotificationService.send_to_user()`
2. API endpoints exist:
   - `GET /api/notifications/config/` - returns Firebase config for frontend
   - `POST /api/notifications/register/` - register device token (requires auth)
   - `POST /api/notifications/unregister/` - unregister token
   - `GET /api/notifications/devices/` - list registered devices

---

## What Needs to Be Done on Frontend:

### 1. Initialize Firebase
Initialize Firebase in the web app using config from `/api/notifications/config/` or use the env variables directly.

### 2. Request Notification Permission
Ask user for permission to show notifications.

### 3. Get FCM Token
Use `getToken()` from Firebase Messaging to get the device token.

### 4. Register the Token with Backend
Call `POST /api/notifications/register/` with:
```json
{
  "token": "fcm_token_here",
  "device_type": "web"
}
```

### 5. Create Service Worker
Create `firebase-messaging-sw.js` at the root of your public folder for background notifications.

### 6. Handle Foreground Messages
Use `onMessage()` to show notifications when the app is open/focused.

---

## Firebase Config (already in frontend .env):

```env
VITE_FIREBASE_API_KEY=AIzaSyCR7_dE8URlspMMlQh1JvD_Ta-aawlQ8ww
VITE_FIREBASE_AUTH_DOMAIN=medilink-3cb2d.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=medilink-3cb2d
VITE_FIREBASE_STORAGE_BUCKET=medilink-3cb2d.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=881642188727
VITE_FIREBASE_APP_ID=1:881642188727:web:f879ca8300cde65e34c232
VITE_FIREBASE_MEASUREMENT_ID=G-EMJKZ8X2GK
VITE_FIREBASE_VAPID_KEY=BKvwwF97ZD9F47OxT5ZSPfGI8-bl2xB0P3XjIciYnDz9Cf5urqFXXS95cbLA4cYoIVnunL3CERXjRHop5C2ZPKA
```

---

## Expected Notification Payload from Backend:

```json
{
  "title": "🗓️ New Appointment Request",
  "body": "John Doe has requested an appointment on February 5, 2026 at 10:00 AM.",
  "data": {
    "type": "APPOINTMENT_CREATED",
    "appointment_id": "123",
    "action_url": "/appointments/123"
  }
}
```

---

## Implementation Example:

### 1. Firebase Config File (`src/lib/firebase.ts`)

```typescript
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

const app = initializeApp(firebaseConfig);
export const messaging = getMessaging(app);

export { getToken, onMessage };
```

### 2. Notification Service (`src/services/notificationService.ts`)

```typescript
import { messaging, getToken, onMessage } from '@/lib/firebase';
import { apiClient } from '@/lib/api'; // Your API client

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY;

export const notificationService = {
  /**
   * Request permission and register FCM token with backend
   */
  async requestPermissionAndRegister(): Promise<boolean> {
    try {
      // Check if notifications are supported
      if (!('Notification' in window)) {
        console.warn('This browser does not support notifications');
        return false;
      }

      // Request permission
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        console.warn('Notification permission denied');
        return false;
      }

      // Get FCM token
      const token = await getToken(messaging, { vapidKey: VAPID_KEY });
      if (!token) {
        console.warn('Failed to get FCM token');
        return false;
      }

      // Register token with backend
      await apiClient.post('/api/notifications/register/', {
        token: token,
        device_type: 'web',
      });

      console.log('✅ FCM token registered successfully');
      return true;
    } catch (error) {
      console.error('❌ Error registering FCM token:', error);
      return false;
    }
  },

  /**
   * Listen for foreground messages
   */
  onForegroundMessage(callback: (payload: any) => void): void {
    onMessage(messaging, (payload) => {
      console.log('📬 Foreground message received:', payload);
      callback(payload);
    });
  },

  /**
   * Unregister device token (call on logout)
   */
  async unregister(token: string): Promise<void> {
    try {
      await apiClient.post('/api/notifications/unregister/', { token });
    } catch (error) {
      console.error('Error unregistering token:', error);
    }
  },
};
```

### 3. Service Worker (`public/firebase-messaging-sw.js`)

```javascript
// Give the service worker access to Firebase Messaging.
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

// Initialize the Firebase app in the service worker
firebase.initializeApp({
  apiKey: 'AIzaSyCR7_dE8URlspMMlQh1JvD_Ta-aawlQ8ww',
  authDomain: 'medilink-3cb2d.firebaseapp.com',
  projectId: 'medilink-3cb2d',
  storageBucket: 'medilink-3cb2d.firebasestorage.app',
  messagingSenderId: '881642188727',
  appId: '1:881642188727:web:f879ca8300cde65e34c232',
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('📬 Background message received:', payload);

  const notificationTitle = payload.notification?.title || 'MediLink';
  const notificationOptions = {
    body: payload.notification?.body || '',
    icon: '/logo.png', // Your app icon
    badge: '/badge.png',
    data: payload.data,
    tag: payload.data?.type || 'default',
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const actionUrl = event.notification.data?.action_url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // If a window is already open, focus it
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.focus();
          client.navigate(actionUrl);
          return;
        }
      }
      // Otherwise open a new window
      if (clients.openWindow) {
        return clients.openWindow(actionUrl);
      }
    })
  );
});
```

### 4. Usage in App (`src/App.tsx` or main component)

```typescript
import { useEffect } from 'react';
import { notificationService } from '@/services/notificationService';
import { useAuth } from '@/hooks/useAuth'; // Your auth hook
import { toast } from 'sonner'; // Or your toast library

function App() {
  const { isAuthenticated, user } = useAuth();

  useEffect(() => {
    if (isAuthenticated && user) {
      // Register for push notifications after login
      notificationService.requestPermissionAndRegister();

      // Listen for foreground messages
      notificationService.onForegroundMessage((payload) => {
        // Show toast notification when app is focused
        toast(payload.notification?.title, {
          description: payload.notification?.body,
          action: payload.data?.action_url ? {
            label: 'View',
            onClick: () => window.location.href = payload.data.action_url,
          } : undefined,
        });
      });
    }
  }, [isAuthenticated, user]);

  return (
    // Your app content
  );
}
```

---

## API Endpoints Reference:

### Register Device Token
```http
POST /api/notifications/register/
Authorization: Token <user_auth_token>
Content-Type: application/json

{
  "token": "fcm_device_token_here",
  "device_type": "web"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Token registered successfully",
  "device_id": 123
}
```

### Unregister Device Token (on logout)
```http
POST /api/notifications/unregister/
Authorization: Token <user_auth_token>
Content-Type: application/json

{
  "token": "fcm_device_token_here"
}
```

### List Registered Devices
```http
GET /api/notifications/devices/
Authorization: Token <user_auth_token>
```

---

## Goal:
When a patient books an appointment from mobile app, the doctor's web dashboard should receive a push notification instantly.

---

## Troubleshooting:

1. **No notifications appearing?**
   - Check browser notification permissions
   - Verify the FCM token is being registered (check `DeviceToken` table in database)
   - Check browser console for errors

2. **Token registration failing?**
   - Ensure user is authenticated before registering token
   - Check that VAPID key is correct

3. **Background notifications not working?**
   - Verify `firebase-messaging-sw.js` is at the root of your public folder
   - Check that the service worker is registered (Chrome DevTools > Application > Service Workers)

4. **Testing notifications:**
   - Use Firebase Console > Cloud Messaging > Send test message
   - Or create an appointment from mobile app and verify web receives notification
