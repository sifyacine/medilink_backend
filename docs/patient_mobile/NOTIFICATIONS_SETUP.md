# Patient Mobile App - Notifications Setup

## Overview

This guide helps you integrate **real-time notifications** into your patient mobile app (React Native / Flutter / native iOS/Android), ensuring patients receive **instant updates** about their appointments without needing to pull-to-refresh.

## Why Real-Time Notifications Matter for Patients

### Before Real-Time

❌ Patient must manually refresh to see appointment status  
❌ Missed doctor confirmation notifications  
❌ Uncertain whether appointment was received  
❌ Poor user experience

### After Real-Time

✅ Instant confirmation when doctor accepts appointment  
✅ Real-time updates when doctor reschedules  
✅ Push notifications even when app is closed  
✅ Professional, modern app experience

## Quick Start (React Native)

### Step 1: Install Dependencies

```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
```

### Step 2: Configure Firebase

Follow [Firebase setup for React Native](https://rnfirebase.io/)

### Step 3: Register Device Token

```javascript
// src/services/NotificationService.js
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const NotificationService = {
  async requestPermission() {
    const authStatus = await messaging().requestPermission();
    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (enabled) {
      console.log('✅ Notification permission granted');
      await this.registerDeviceToken();
    }
  },

  async registerDeviceToken() {
    try {
      // Get FCM token
      const fcmToken = await messaging().getToken();
      
      // Send to backend
      const authToken = await AsyncStorage.getItem('authToken');
      const response = await fetch('https://dzmedilink.duckdns.org/api/notifications/devices/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify({
          token: fcmToken,
          device_type: 'MOBILE',
          device_name: Platform.OS,
        }),
      });

      if (response.ok) {
        console.log('✅ Device registered for notifications');
      }
    } catch (error) {
      console.error('❌ Error registering device:', error);
    }
  },

  setupForegroundNotifications() {
    // Handle notifications when app is in foreground
    messaging().onMessage(async (remoteMessage) => {
      console.log('📩 Foreground notification:', remoteMessage);
      
      // Show in-app notification
      this.showInAppNotification(remoteMessage);
    });
  },

  setupBackgroundNotifications() {
    // Handle notifications when app is in background
    messaging().setBackgroundMessageHandler(async (remoteMessage) => {
      console.log('📩 Background notification:', remoteMessage);
    });
  },

  showInAppNotification(remoteMessage) {
    const { title, body } = remoteMessage.notification;
    
    // Example: Show toast or modal
    // Using react-native-toast-message:
    Toast.show({
      type: 'info',
      text1: title,
      text2: body,
      onPress: () => {
        // Navigate to relevant screen
        if (remoteMessage.data.appointment_id) {
          Navigation.navigate('AppointmentDetails', {
            id: remoteMessage.data.appointment_id
          });
        }
      }
    });
  },
};
```

### Step 4: Initialize in App.js

```javascript
// App.js
import { NotificationService } from './services/NotificationService';
import { useEffect } from 'react';

function App() {
  useEffect(() => {
    // Request notification permission
    NotificationService.requestPermission();
    
    // Setup notification handlers
    NotificationService.setupForegroundNotifications();
    NotificationService.setupBackgroundNotifications();
    
    // Handle notification tap when app is opened
    messaging().onNotificationOpenedApp((remoteMessage) => {
      console.log('Notification opened app:', remoteMessage);
      
      if (remoteMessage.data.appointment_id) {
        // Navigate to appointment details
        Navigation.navigate('AppointmentDetails', {
          id: remoteMessage.data.appointment_id
        });
      }
    });

    // Check if app was opened by notification
    messaging()
      .getInitialNotification()
      .then((remoteMessage) => {
        if (remoteMessage) {
          console.log('App opened by notification:', remoteMessage);
          // Handle initial notification
        }
      });
  }, []);

  return <NavigationContainer>{/* Your app */}</NavigationContainer>;
}
```

## WebSocket for Real-Time In-App Updates

While FCM handles push notifications, WebSocket provides **instant in-app updates** when the app is active.

### React Native WebSocket Integration

```javascript
// src/services/WebSocketService.js
export class WebSocketService {
  constructor() {
    this.ws = null;
    this.callbacks = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(authToken) {
    const wsUrl = `wss://dzmedilink.duckdns.org/ws/notifications/?token=${authToken}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.reconnect(authToken);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'connection_established':
        console.log(`Connected. Unread notifications: ${data.unread_count}`);
        this.emit('unreadCountUpdate', data.unread_count);
        break;

      case 'notification':
        console.log('📩 New notification:', data.notification);
        this.emit('newNotification', data.notification);
        this.emit('unreadCountUpdate', data.unread_count);
        break;

      case 'appointment_update':
        console.log('📅 Appointment updated:', data.appointment);
        this.emit('appointmentUpdate', data.appointment);
        break;
    }
  }

  on(event, callback) {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, []);
    }
    this.callbacks.get(event).push(callback);
  }

  emit(event, data) {
    if (this.callbacks.has(event)) {
      this.callbacks.get(event).forEach(callback => callback(data));
    }
  }

  reconnect(authToken) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`Reconnecting in ${delay}ms...`);
      setTimeout(() => this.connect(authToken), delay);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default new WebSocketService();
```

### Using WebSocket in Screens

```javascript
// src/screens/AppointmentsScreen.js
import WebSocketService from '../services/WebSocketService';
import { useEffect, useState } from 'react';

function AppointmentsScreen() {
  const [appointments, setAppointments] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const authToken = await AsyncStorage.getItem('authToken');
    
    // Connect to WebSocket
    WebSocketService.connect(authToken);
    
    // Listen for new notifications
    WebSocketService.on('newNotification', (notification) => {
      if (notification.notification_type.startsWith('APPOINTMENT_')) {
        // Show toast
        Toast.show({
          type: 'success',
          text1: notification.title,
          text2: notification.message,
        });
        
        // Refresh appointments
        fetchAppointments();
      }
    });
    
    // Listen for appointment updates
    WebSocketService.on('appointmentUpdate', (updatedAppointment) => {
      // Update appointment in list without full refresh
      setAppointments(prev =>
        prev.map(apt =>
          apt.id === updatedAppointment.id ? updatedAppointment : apt
        )
      );
    });
    
    // Listen for unread count
    WebSocketService.on('unreadCountUpdate', (count) => {
      setUnreadCount(count);
    });
    
    // Load initial data
    fetchAppointments();
    
    // Cleanup
    return () => {
      WebSocketService.disconnect();
    };
  }, []);

  return (
    <View>
      <AppointmentList appointments={appointments} />
      {unreadCount > 0 && <Badge count={unreadCount} />}
    </View>
  );
}
```

## Notification Types for Patients

| Type | When You Get It | What It Means |
|------|----------------|---------------|
| `APPOINTMENT_CONFIRMED` | Doctor confirms your appointment | ✅ Your appointment is confirmed! |
| `APPOINTMENT_CANCELLED` | Doctor cancels appointment | ❌ Appointment was cancelled |
| `APPOINTMENT_UPDATED` | Appointment details changed | 📝 Time or details changed |
| `APPOINTMENT_REMINDER` | 24 hours before appointment | ⏰ Don't forget your appointment tomorrow! |
| `PRESCRIPTION_CREATED` | Doctor creates prescription | 💊 New prescription available |

## User Experience Best Practices

### 1. Appointment Status Updates

When doctor confirms appointment:

```javascript
// Show success animation
Animated.sequence([
  Animated.timing(scaleAnim, { toValue: 1.2, duration: 200 }),
  Animated.timing(scaleAnim, { toValue: 1, duration: 200 }),
]).start();

// Update appointment status
setAppointment(prev => ({
  ...prev,
  status: 'CONFIRMED',
  confirmed_at: new Date().toISOString(),
}));

// Show success message
Alert.alert(
  'Appointment Confirmed! ✅',
  `Dr. ${doctorName} has confirmed your appointment for ${appointmentDate}.`,
  [{ text: 'OK', style: 'default' }]
);
```

### 2. Real-Time Appointment List

```javascript
function AppointmentCard({ appointment }) {
  const [status, setStatus] = useState(appointment.status);
  
  useEffect(() => {
    // Listen for this appointment's updates
    const listener = (updatedAppointment) => {
      if (updatedAppointment.id === appointment.id) {
        setStatus(updatedAppointment.status);
      }
    };
    
    WebSocketService.on('appointmentUpdate', listener);
    
    return () => {
      // Cleanup
    };
  }, [appointment.id]);
  
  return (
    <Card>
      <StatusBadge status={status} />
      {status === 'CONFIRMED' && <ConfettiAnimation />}
    </Card>
  );
}
```

### 3. Notification Badge

```javascript
function NotificationBell({ count }) {
  return (
    <TouchableOpacity onPress={() => navigation.navigate('Notifications')}>
      <Icon name="bell" size={24} color="#333" />
      {count > 0 && (
        <Badge
          value={count > 99 ? '99+' : count}
          status="error"
          containerStyle={{ position: 'absolute', top: -4, right: -4 }}
        />
      )}
    </TouchableOpacity>
  );
}
```

## Flutter Integration

### Setup Firebase Messaging (Flutter)

```dart
// pubspec.yaml
dependencies:
  firebase_messaging: ^14.0.0
  flutter_local_notifications: ^16.0.0

// lib/services/notification_service.dart
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = 
      FlutterLocalNotificationsPlugin();

  Future<void> initialize() async {
    // Request permission
    NotificationSettings settings = await _fcm.requestPermission();
    
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      print('✅ Notification permission granted');
      await _registerDeviceToken();
    }

    // Configure foreground notifications
    await _configureForegroundNotifications();
    
    // Handle notification taps
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
  }

  Future<void> _registerDeviceToken() async {
    String? token = await _fcm.getToken();
    
    if (token != null) {
      // Send to backend
      final authToken = await storage.read(key: 'authToken');
      
      await http.post(
        Uri.parse('https://dzmedilink.duckdns.org/api/notifications/devices/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Token $authToken',
        },
        body: jsonEncode({
          'token': token,
          'device_type': 'MOBILE',
          'device_name': Platform.operatingSystem,
        }),
      );
      
      print('✅ Device registered');
    }
  }

  Future<void> _configureForegroundNotifications() async {
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('📩 Foreground notification: ${message.notification?.title}');
      
      // Show local notification
      _showLocalNotification(message);
    });
  }

  void _showLocalNotification(RemoteMessage message) {
    _localNotifications.show(
      message.hashCode,
      message.notification?.title,
      message.notification?.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          'medilink_channel',
          'Medilink Notifications',
          importance: Importance.high,
        ),
        iOS: DarwinNotificationDetails(),
      ),
      payload: message.data['appointment_id'],
    );
  }

  void _handleNotificationTap(RemoteMessage message) {
    if (message.data['appointment_id'] != null) {
      // Navigate to appointment details
      navigatorKey.currentState?.pushNamed(
        '/appointment-details',
        arguments: message.data['appointment_id'],
      );
    }
  }
}
```

## Testing Your Integration

### Test 1: Device Registration

```javascript
// Check if device is registered
const response = await fetch(
  'https://dzmedilink.duckdns.org/api/notifications/devices/',
  {
    headers: {
      'Authorization': `Token ${authToken}`,
    },
  }
);

const devices = await response.json();
console.log('Registered devices:', devices);
```

Expected: You should see your device in the list.

### Test 2: Receive Test Notification

Have someone (doctor/admin) create a test appointment for your account. You should:

1. ✅ Receive push notification (even if app is closed)
2. ✅ See in-app toast if app is open
3. ✅ See appointment appear in appointment list
4. ✅ Notification badge increments

### Test 3: Real-Time Updates

1. Book an appointment
2. Have doctor confirm it from their dashboard
3. Verify:
   - ✅ Notification appears instantly
   - ✅ Appointment status updates to "CONFIRMED"
   - ✅ No manual refresh needed

## Common Issues & Solutions

### Issue 1: Not Receiving Notifications

**Symptoms:** No notifications appear

**Solutions:**
1. Check notification permissions: Settings → App → Notifications → Enabled
2. Verify device token is registered:
   ```javascript
   const token = await messaging().getToken();
   console.log('FCM Token:', token);
   ```
3. Check backend logs for FCM errors
4. Test with Firebase Console → Cloud Messaging → Send test message

### Issue 2: WebSocket Disconnects Frequently

**Symptoms:** Connection drops often

**Solutions:**
1. Implement automatic reconnection (already in code above)
2. Send periodic ping messages (keep-alive)
3. Handle app state changes:
   ```javascript
   AppState.addEventListener('change', (state) => {
     if (state === 'active') {
       WebSocketService.connect(authToken);
     } else {
       WebSocketService.disconnect();
     }
   });
   ```

### Issue 3: Duplicate Notifications

**Symptoms:** Same notification shown twice

**Solutions:**
1. Use notification `tag` to prevent duplicates:
   ```javascript
   messaging().onMessage(async (message) => {
     // Check if already shown
     const lastNotificationId = await AsyncStorage.getItem('lastNotificationId');
     if (lastNotificationId === message.messageId) {
       return; // Skip duplicate
     }
     
     await AsyncStorage.setItem('lastNotificationId', message.messageId);
     showNotification(message);
   });
   ```

## Production Checklist

- [ ] Firebase project configured correctly
- [ ] FCM server key added to backend
- [ ] Device token registration working
- [ ] Foreground notifications displayed
- [ ] Background notifications working
- [ ] Notification tap navigation working
- [ ] WebSocket reconnection implemented
- [ ] Notification permissions requested gracefully
- [ ] Badge count updates correctly
- [ ] Notification sounds are appropriate
- [ ] Deep linking to appointment details works
- [ ] Unread count displayed in UI

## Advanced Features

### Feature 1: Notification Preferences

Let users control what notifications they receive:

```javascript
function NotificationPreferences() {
  const [preferences, setPreferences] = useState({
    appointment_confirmed: true,
    appointment_reminder: true,
    appointment_cancelled: true,
    prescription_created: true,
  });

  const updatePreference = async (key, value) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    
    // Save to backend
    await fetch('https://dzmedilink.duckdns.org/api/notifications/preferences/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${authToken}`,
      },
      body: JSON.stringify({
        [`${key}_push`]: value,
      }),
    });
  };

  return (
    <View>
      <Switch
        label="Appointment Confirmations"
        value={preferences.appointment_confirmed}
        onValueChange={(value) => updatePreference('appointment_confirmed', value)}
      />
      <Switch
        label="Appointment Reminders"
        value={preferences.appointment_reminder}
        onValueChange={(value) => updatePreference('appointment_reminder', value)}
      />
    </View>
  );
}
```

### Feature 2: Rich Notifications with Actions

```javascript
// iOS/Android notification with actions
messaging().onMessage(async (message) => {
  if (message.notification.title.includes('Appointment Confirmed')) {
    _localNotifications.show(
      message.hashCode,
      message.notification.title,
      message.notification.body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          'medilink_channel',
          'Medilink Notifications',
          actions: [
            AndroidNotificationAction(
              'view',
              'View Details',
            ),
            AndroidNotificationAction(
              'remind',
              'Remind Me Later',
            ),
          ],
        ),
      ),
    );
  }
});
```

## Next Steps

✅ You now have real-time notifications working in your mobile app!

**Recommended:**
1. Implement notification history screen
2. Add notification filtering (read/unread)
3. Set up notification grouping by type
4. Implement quiet hours (don't disturb)

**Resources:**
- [Complete Notifications Setup](../NOTIFICATIONS_SETUP.md)
- [Appointments API Documentation](APPOINTMENTS_API.md)
- [React Native Firebase Docs](https://rnfirebase.io/)
- [Flutter Firebase Messaging](https://firebase.flutter.dev/docs/messaging/overview)

---

**Need Help?** Check the [troubleshooting section](../NOTIFICATIONS_SETUP.md#troubleshooting) in the main notifications setup guide.
