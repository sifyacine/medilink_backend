# Provider Dashboard - Notifications Setup

## Overview

This guide helps you integrate **real-time notifications** into your provider dashboard, ensuring you see new appointments and updates **instantly without refreshing the page**.

## Why Real-Time Notifications Matter

### Before Real-Time

❌ Doctor has to manually refresh page to see new appointments  
❌ Missed appointment requests  
❌ Delayed response to patients  
❌ Poor user experience

### After Real-Time

✅ New appointments appear instantly  
✅ Immediate notification of patient requests  
✅ Real-time status updates (confirmed, cancelled, etc.)  
✅ Professional, responsive dashboard

## Quick Start (5 Minutes)

### Step 1: Connect to WebSocket

```javascript
// src/services/NotificationWebSocket.js
class NotificationWebSocket {
  constructor(authToken) {
    this.authToken = authToken;
    this.ws = null;
    this.callbacks = {
      onNotification: null,
      onAppointmentUpdate: null,
      onUnreadCountUpdate: null,
    };
  }

  connect() {
    const wsUrl = `wss://dzmedilink.duckdns.org/ws/notifications/?token=${this.authToken}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('✅ Connected to notification service');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Disconnected. Reconnecting in 5 seconds...');
      setTimeout(() => this.connect(), 5000);
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'connection_established':
        console.log(`Connected as provider`);
        if (this.callbacks.onUnreadCountUpdate) {
          this.callbacks.onUnreadCountUpdate(data.unread_count);
        }
        break;

      case 'notification':
        // New notification (e.g., patient booked appointment)
        if (this.callbacks.onNotification) {
          this.callbacks.onNotification(data.notification);
        }
        if (this.callbacks.onUnreadCountUpdate) {
          this.callbacks.onUnreadCountUpdate(data.unread_count);
        }
        break;

      case 'appointment_update':
        // Appointment status changed
        if (this.callbacks.onAppointmentUpdate) {
          this.callbacks.onAppointmentUpdate(data.appointment);
        }
        break;
    }
  }

  on(event, callback) {
    this.callbacks[event] = callback;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

export default NotificationWebSocket;
```

### Step 2: Initialize in Your Dashboard

```javascript
// src/App.js or src/Dashboard.js
import NotificationWebSocket from './services/NotificationWebSocket';
import { useState, useEffect } from 'react';

function ProviderDashboard() {
  const [appointments, setAppointments] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [wsClient, setWsClient] = useState(null);

  useEffect(() => {
    const authToken = localStorage.getItem('authToken');
    
    // Initialize WebSocket
    const ws = new NotificationWebSocket(authToken);
    
    // Listen for new notifications
    ws.on('onNotification', (notification) => {
      // Show toast notification
      showToast(notification.title, notification.message);
      
      // If it's an appointment notification, refresh list
      if (notification.notification_type.startsWith('APPOINTMENT_')) {
        refreshAppointments();
      }
    });
    
    // Listen for appointment updates
    ws.on('onAppointmentUpdate', (appointment) => {
      // Update appointment in the list without full refresh
      setAppointments(prev => 
        prev.map(apt => 
          apt.id === appointment.id ? appointment : apt
        )
      );
    });
    
    // Listen for unread count updates
    ws.on('onUnreadCountUpdate', (count) => {
      setUnreadCount(count);
    });
    
    // Connect
    ws.connect();
    setWsClient(ws);
    
    // Cleanup on unmount
    return () => {
      ws.disconnect();
    };
  }, []);

  const refreshAppointments = async () => {
    const response = await fetch('https://dzmedilink.duckdns.org/api/appointments/', {
      headers: {
        'Authorization': `Token ${localStorage.getItem('authToken')}`
      }
    });
    const data = await response.json();
    setAppointments(data.results);
  };

  const showToast = (title, message) => {
    // Your toast notification implementation
    // Example with react-toastify:
    toast.info(message, {
      title: title,
      autoClose: 5000,
    });
  };

  return (
    <div className="dashboard">
      <NotificationBell count={unreadCount} />
      <AppointmentList appointments={appointments} />
    </div>
  );
}
```

### Step 3: Show Notification Badge

```javascript
// src/components/NotificationBell.js
function NotificationBell({ count }) {
  return (
    <div className="notification-bell">
      <i className="fas fa-bell"></i>
      {count > 0 && (
        <span className="badge">{count}</span>
      )}
    </div>
  );
}
```

## Common Use Cases

### Use Case 1: New Appointment Request

**What Happens:**
1. Patient books appointment via mobile app
2. Your WebSocket receives `notification` message
3. Toast notification appears: "New Appointment Request from Ahmed"
4. Appointment list refreshes automatically
5. Notification badge updates

**Implementation:**
```javascript
ws.on('onNotification', (notification) => {
  if (notification.notification_type === 'APPOINTMENT_CREATED') {
    // Play notification sound
    playNotificationSound();
    
    // Show toast
    toast.info(`New appointment request from ${notification.data.patient_name}`, {
      onClick: () => {
        // Navigate to appointment details
        window.location.href = `/appointments/${notification.data.appointment_id}`;
      }
    });
    
    // Refresh appointment list
    refreshAppointments();
  }
});
```

### Use Case 2: Patient Cancels Appointment

**What Happens:**
1. Patient cancels appointment
2. Your WebSocket receives `notification` message
3. Toast: "Appointment Cancelled by Ahmed Ben Ali"
4. Appointment removed from confirmed list
5. Moves to cancelled list automatically

**Implementation:**
```javascript
ws.on('onNotification', (notification) => {
  if (notification.notification_type === 'APPOINTMENT_CANCELLED') {
    toast.warning(`Appointment cancelled: ${notification.message}`, {
      autoClose: 7000,
    });
    
    // Update appointment status in state
    setAppointments(prev => 
      prev.map(apt => 
        apt.id === notification.data.appointment_id 
          ? { ...apt, status: 'CANCELLED' }
          : apt
      )
    );
  }
});
```

### Use Case 3: Real-Time Dashboard Updates

Update your dashboard sections in real-time:

```javascript
// Separate appointments by status
const pendingAppointments = appointments.filter(apt => apt.status === 'PENDING');
const confirmedAppointments = appointments.filter(apt => apt.status === 'CONFIRMED');
const todayAppointments = appointments.filter(apt => 
  apt.scheduled_date === new Date().toISOString().split('T')[0] &&
  apt.status === 'CONFIRMED'
);

return (
  <div className="dashboard">
    <DashboardStats>
      <StatCard 
        title="Pending Requests" 
        count={pendingAppointments.length}
        icon="clock"
      />
      <StatCard 
        title="Today's Appointments" 
        count={todayAppointments.length}
        icon="calendar"
      />
    </DashboardStats>
    
    <AppointmentTabs>
      <Tab label={`Pending (${pendingAppointments.length})`}>
        <AppointmentList appointments={pendingAppointments} />
      </Tab>
      <Tab label={`Confirmed (${confirmedAppointments.length})`}>
        <AppointmentList appointments={confirmedAppointments} />
      </Tab>
    </AppointmentTabs>
  </div>
);
```

## Notification Types for Providers

| Type | When You Get It | Recommended Action |
|------|----------------|-------------------|
| `APPOINTMENT_CREATED` | Patient books new appointment | Review details and confirm/reject |
| `APPOINTMENT_CANCELLED` | Patient cancels appointment | Update schedule, note the cancellation |
| `APPOINTMENT_UPDATED` | Patient reschedules | Check new time fits your schedule |

## Testing Your Integration

### Test 1: WebSocket Connection

Open browser console and run:

```javascript
const ws = new WebSocket('wss://dzmedilink.duckdns.org/ws/notifications/?token=YOUR_TOKEN');
ws.onopen = () => console.log('✅ Connected');
ws.onmessage = (e) => console.log('📩 Message:', JSON.parse(e.data));
```

Expected output:
```
✅ Connected
📩 Message: {type: "connection_established", user_id: "...", unread_count: 3}
```

### Test 2: Simulate New Appointment

1. Open your dashboard in one browser tab
2. Create a test appointment using API/another account
3. Verify:
   - ✅ Toast notification appears
   - ✅ Appointment list updates
   - ✅ Notification badge increments

### Test 3: Network Resilience

1. Disconnect WiFi
2. Wait 10 seconds
3. Reconnect WiFi
4. Verify WebSocket reconnects automatically

## Common Issues & Solutions

### Issue 1: WebSocket Not Connecting

**Error:** `WebSocket connection failed`

**Solutions:**
1. Check auth token is valid: `console.log(authToken)`
2. Verify WebSocket URL uses `wss://` (not `ws://`) for production
3. Check CORS settings in backend
4. Ensure Redis is running on server

### Issue 2: Notifications Not Appearing

**Error:** Connected but no messages received

**Solutions:**
1. Check `onmessage` handler is registered
2. Verify user has correct permissions
3. Check browser console for JavaScript errors
4. Test with curl: 
   ```bash
   wscat -c "wss://dzmedilink.duckdns.org/ws/notifications/?token=YOUR_TOKEN"
   ```

### Issue 3: Page Performance Issues

**Error:** Dashboard becomes slow after some time

**Solutions:**
1. Limit notification history display (show last 50 only)
2. Implement pagination for appointment list
3. Clear old notifications:
   ```javascript
   // Keep only last 100 notifications in state
   setNotifications(prev => prev.slice(0, 100));
   ```

## Production Checklist

Before deploying to production:

- [ ] WebSocket uses secure connection (`wss://`)
- [ ] Auth token stored securely (not in localStorage for sensitive apps)
- [ ] WebSocket reconnects automatically on disconnect
- [ ] Notification sounds are user-configurable
- [ ] Unread count updates correctly
- [ ] Toast notifications don't overlap
- [ ] WebSocket connection closes on logout
- [ ] Error handling for network issues
- [ ] Loading states for appointment list
- [ ] Notification preferences respected

## Advanced Features

### Feature 1: Desktop Notifications

Request permission and show browser notifications:

```javascript
// Request permission on app load
if (Notification.permission === 'default') {
  Notification.requestPermission();
}

// Show desktop notification
ws.on('onNotification', (notification) => {
  if (Notification.permission === 'granted') {
    new Notification(notification.title, {
      body: notification.message,
      icon: '/logo.png',
      badge: '/badge.png',
      tag: notification.id,  // Prevents duplicates
    });
  }
});
```

### Feature 2: Notification Sounds

```javascript
const notificationSound = new Audio('/sounds/notification.mp3');

ws.on('onNotification', (notification) => {
  if (notification.priority === 'HIGH' || notification.priority === 'URGENT') {
    notificationSound.play();
  }
});
```

### Feature 3: In-App Notification Center

```javascript
function NotificationCenter({ notifications }) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="notification-center">
      <button onClick={() => setIsOpen(!isOpen)}>
        <i className="fas fa-bell"></i>
        {unreadCount > 0 && <Badge count={unreadCount} />}
      </button>
      
      {isOpen && (
        <div className="notification-dropdown">
          {notifications.map(notification => (
            <NotificationItem 
              key={notification.id}
              notification={notification}
              onRead={() => markAsRead(notification.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

## Next Steps

✅ You now have real-time notifications working!

**Recommended:**
1. Add notification preferences (allow users to mute certain types)
2. Implement notification grouping (group similar notifications)
3. Add notification archive/history
4. Set up push notifications for mobile (FCM)

**Resources:**
- [Complete Notifications Setup](../NOTIFICATIONS_SETUP.md)
- [Appointments API Documentation](APPOINTMENTS_API.md)
- [WebSocket API Reference](../websocket/WEBSOCKET_API.md)

---

**Need Help?** Check the [troubleshooting section](../NOTIFICATIONS_SETUP.md#troubleshooting) in the main notifications setup guide.
