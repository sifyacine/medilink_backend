# Provider Dashboard — Real-Time Integration Guide

This document describes how to integrate the **provider dashboard** on the frontend. The dashboard exposes:

1. A **WebSocket endpoint** (`ws/dashboard/`) that pushes computed stats in real time.
2. Two **REST endpoints** for initial data loading (activity feed, patient stats).
3. **Event types** and payload schemas for every dashboard section.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [WebSocket Connection](#websocket-connection)
3. [WebSocket Event Types & Payloads](#websocket-event-types--payloads)
4. [REST Endpoints](#rest-endpoints)
5. [Dashboard Sections & Data Sources](#dashboard-sections--data-sources)
6. [Frontend Integration Examples](#frontend-integration-examples)
7. [Error Handling & Reconnection](#error-handling--reconnection)

---

## Architecture Overview

```
┌──────────────────┐         ┌─────────────────────────────┐
│  Provider Client  │◄──WS──►│  DashboardConsumer           │
│  (React / Mobile) │         │  ws/dashboard/?token=<jwt>   │
└──────────────────┘         └────────────┬──────────────────┘
                                          │
                       ┌──────────────────┴──────────────────┐
                       │        DashboardStatsService         │
                       │  (computes all dashboard numbers)    │
                       └──────────────────┬──────────────────┘
                                          │
        ┌──────────┬──────────┬───────────┼───────────┐
        ▼          ▼          ▼           ▼           ▼
   Appointments  Invoices  Patients    Reviews   Activity Feed
```

### How Updates Flow

1. A data change occurs (appointment saved, invoice created, review posted, patient linked).
2. A Django **signal** fires and — inside `transaction.on_commit()` — calls `DashboardStatsService` to re-compute the relevant stats.
3. The computed payload is pushed to the `user_{provider.user_id}_dashboard` channel group via `WebSocketBroadcaster.send_to_dashboard()`.
4. `DashboardConsumer` receives the event and forwards it to the connected client **as pre-computed JSON** — no additional REST fetch is required.

---

## WebSocket Connection

### URL

```
ws://<host>/ws/dashboard/?token=<auth-token>
```

- Requires valid JWT authentication token.
- **Only providers** can connect — non-provider users receive close code `4003`.

### Connection Flow

1. Client opens WebSocket with the token query parameter.
2. Server authenticates → verifies user has a `provider_profile`.
3. Server accepts the connection.
4. Server immediately pushes a full `dashboard_snapshot` event with all computed stats.

### Client → Server Messages

| Type      | Description                         | Payload      |
|-----------|-------------------------------------|--------------|
| `ping`    | Keep-alive heartbeat                | `{}`         |
| `refresh` | Request a fresh full dashboard push | `{}`         |

Example:

```json
{ "type": "ping" }
```

```json
{ "type": "refresh" }
```

---

## WebSocket Event Types & Payloads

All server-to-client messages follow this envelope:

```json
{
  "type": "<event_type>",
  "data": { ... }
}
```

### 1. `dashboard_snapshot`

Sent on initial connect and when the client sends `refresh`.

```json
{
  "type": "dashboard_snapshot",
  "data": {
    "appointments": {
      "total": 42,
      "pending": 5,
      "confirmed": 10,
      "completed": 20,
      "cancelled": 3,
      "no_show": 1,
      "rescheduled": 2,
      "rejected": 1,
      "today_count": 4,
      "upcoming_count": 15
    },
    "today_appointments": [
      {
        "id": "uuid",
        "patient_name": "John Doe",
        "scheduled_date": "2025-01-15",
        "scheduled_time": "09:00:00",
        "status": "CONFIRMED",
        "service_name": "General Checkup"
      }
    ],
    "invoices": {
      "total_revenue": "12500.00",
      "total_outstanding": "3200.00",
      "total_overdue": "800.00",
      "counts": {
        "draft": 2,
        "sent": 5,
        "viewed": 3,
        "partially_paid": 1,
        "paid": 15,
        "overdue": 2,
        "cancelled": 0,
        "refunded": 1,
        "partially_refunded": 0
      }
    },
    "patients": {
      "total_patients": 120,
      "gender_breakdown": {
        "male": 55,
        "female": 50,
        "other": 5,
        "prefer_not_to_say": 10
      }
    },
    "reviews": {
      "average_rating": 4.35,
      "total_reviews": 28,
      "rating_distribution": {
        "1": 1,
        "2": 2,
        "3": 5,
        "4": 10,
        "5": 10
      },
      "recent_reviews": [
        {
          "id": "uuid",
          "reviewer_name": "Jane Smith",
          "rating": 5,
          "title": "Great doctor!",
          "comment": "Very professional and kind.",
          "created_at": "2025-01-15T10:30:00Z"
        }
      ]
    },
    "recent_activity": [
      {
        "type": "appointment",
        "id": "uuid",
        "description": "Confirmed appointment with John Doe",
        "status": "CONFIRMED",
        "timestamp": "2025-01-15T10:00:00Z"
      },
      {
        "type": "invoice",
        "id": "uuid",
        "description": "Invoice INV-0042 — Paid (Jane Smith)",
        "status": "PAID",
        "amount": "250.00",
        "timestamp": "2025-01-15T09:30:00Z"
      },
      {
        "type": "review",
        "id": "uuid",
        "description": "Jane Smith left a 5★ review",
        "rating": 5,
        "timestamp": "2025-01-15T09:00:00Z"
      }
    ]
  }
}
```

### 2. `dashboard_appointments_updated`

Pushed when any appointment for this provider is created, updated, or deleted.

```json
{
  "type": "dashboard_appointments_updated",
  "data": {
    "appointments": {
      "total": 43,
      "pending": 6,
      "confirmed": 10,
      "completed": 20,
      "cancelled": 3,
      "no_show": 1,
      "rescheduled": 2,
      "rejected": 1,
      "today_count": 5,
      "upcoming_count": 16
    },
    "today_appointments": [ ... ]
  }
}
```

### 3. `dashboard_invoices_updated`

Pushed when any invoice for this provider is created or its status changes.

```json
{
  "type": "dashboard_invoices_updated",
  "data": {
    "invoices": {
      "total_revenue": "12750.00",
      "total_outstanding": "2950.00",
      "total_overdue": "800.00",
      "counts": { ... }
    }
  }
}
```

### 4. `dashboard_patients_updated`

Pushed when a patient is linked to or unlinked from this provider.

```json
{
  "type": "dashboard_patients_updated",
  "data": {
    "patients": {
      "total_patients": 121,
      "gender_breakdown": {
        "male": 56,
        "female": 50,
        "other": 5,
        "prefer_not_to_say": 10
      }
    }
  }
}
```

### 5. `dashboard_reviews_updated`

Pushed when a review for this provider is created, updated, or deleted.

```json
{
  "type": "dashboard_reviews_updated",
  "data": {
    "reviews": {
      "average_rating": 4.40,
      "total_reviews": 29,
      "rating_distribution": { ... },
      "recent_reviews": [ ... ]
    }
  }
}
```

### 6. `dashboard_activity`

Pushed as a lightweight notification when a notable activity occurs (currently bundled with the section-specific event above).

---

## REST Endpoints

These endpoints provide initial data loading. After the WebSocket connects and pushes the snapshot, the frontend does **not** need to poll these — the WS pushes pre-computed stats automatically.

### GET `/api/patients/provider-stats/`

Returns patient count + gender breakdown for the authenticated provider.

**Auth:** Bearer token (provider only)

**Response:**

```json
{
  "total_patients": 120,
  "gender_breakdown": {
    "male": 55,
    "female": 50,
    "other": 5,
    "prefer_not_to_say": 10
  }
}
```

### GET `/api/notifications/activity-feed/`

Returns the combined recent activity feed.

**Auth:** Bearer token (provider only)

**Query params:**

| Param   | Type | Default | Max | Description                  |
|---------|------|---------|-----|------------------------------|
| `limit` | int  | 20      | 50  | Number of activity items     |

**Response:**

```json
{
  "count": 15,
  "results": [
    {
      "type": "appointment",
      "id": "uuid",
      "description": "Confirmed appointment with John Doe",
      "status": "CONFIRMED",
      "timestamp": "2025-01-15T10:00:00Z"
    },
    {
      "type": "invoice",
      "id": "uuid",
      "description": "Invoice INV-0042 — Paid (Jane Smith)",
      "status": "PAID",
      "amount": "250.00",
      "timestamp": "2025-01-15T09:30:00Z"
    },
    {
      "type": "review",
      "id": "uuid",
      "description": "Jane Smith left a 5★ review",
      "rating": 5,
      "timestamp": "2025-01-15T09:00:00Z"
    }
  ]
}
```

---

## Dashboard Sections & Data Sources

| Dashboard Section         | WS Event                        | REST Fallback                        | Signal Sources                                 |
|---------------------------|---------------------------------|--------------------------------------|-------------------------------------------------|
| Appointment Stats         | `dashboard_appointments_updated`| N/A (use snapshot)                   | `appointments.signals` (save, delete)           |
| Today's Appointments      | `dashboard_appointments_updated`| N/A (use snapshot)                   | `appointments.signals` (save, delete)           |
| Invoice Summary           | `dashboard_invoices_updated`    | N/A (use snapshot)                   | `invoices.signals` (save)                       |
| Patient Count & Gender    | `dashboard_patients_updated`    | `GET /api/patients/provider-stats/`  | `patients.signals` (ProviderPatientAccess save/delete) |
| Review Stats & Recent     | `dashboard_reviews_updated`     | N/A (use snapshot)                   | `reviews.signals` (save, delete)                |
| Activity Feed             | (bundled in section events)     | `GET /api/notifications/activity-feed/` | All of the above                             |

---

## Frontend Integration Examples

### React / Next.js

```javascript
import { useEffect, useRef, useState } from 'react';

function useDashboardSocket(authToken) {
  const [dashboard, setDashboard] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!authToken) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(
      `${protocol}://${window.location.host}/ws/dashboard/?token=${authToken}`
    );
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case 'dashboard_snapshot':
          setDashboard(msg.data);
          break;

        case 'dashboard_appointments_updated':
          setDashboard(prev => ({
            ...prev,
            appointments: msg.data.appointments,
            today_appointments: msg.data.today_appointments,
          }));
          break;

        case 'dashboard_invoices_updated':
          setDashboard(prev => ({
            ...prev,
            invoices: msg.data.invoices,
          }));
          break;

        case 'dashboard_patients_updated':
          setDashboard(prev => ({
            ...prev,
            patients: msg.data.patients,
          }));
          break;

        case 'dashboard_reviews_updated':
          setDashboard(prev => ({
            ...prev,
            reviews: msg.data.reviews,
          }));
          break;

        default:
          break;
      }
    };

    // Keep-alive ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    ws.onclose = () => clearInterval(pingInterval);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [authToken]);

  const refresh = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'refresh' }));
    }
  };

  return { dashboard, refresh };
}
```

Usage in a component:

```jsx
function ProviderDashboard() {
  const { dashboard, refresh } = useDashboardSocket(authToken);

  if (!dashboard) return <LoadingSpinner />;

  return (
    <div>
      <AppointmentStatsCard data={dashboard.appointments} />
      <TodayAppointmentsList items={dashboard.today_appointments} />
      <InvoiceSummaryCard data={dashboard.invoices} />
      <PatientGenderChart data={dashboard.patients} />
      <ReviewStatsCard data={dashboard.reviews} />
      <ActivityFeed items={dashboard.recent_activity} />
      <button onClick={refresh}>Refresh</button>
    </div>
  );
}
```

### React Native / Expo

```javascript
import { useEffect, useRef, useState } from 'react';

function useDashboardSocket(authToken, baseUrl) {
  const [dashboard, setDashboard] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!authToken) return;

    const ws = new WebSocket(`ws://${baseUrl}/ws/dashboard/?token=${authToken}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === 'dashboard_snapshot') {
        setDashboard(msg.data);
      } else if (msg.type.startsWith('dashboard_')) {
        // Merge partial update into existing dashboard state
        setDashboard(prev => ({ ...prev, ...msg.data }));
      }
    };

    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    ws.onclose = () => clearInterval(pingInterval);

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [authToken, baseUrl]);

  return { dashboard };
}
```

### Activity Feed — Initial Load via REST

```javascript
// Load initial activity feed (before WS is ready, or for pagination)
async function loadActivityFeed(token, limit = 20) {
  const response = await fetch(
    `/api/notifications/activity-feed/?limit=${limit}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.json(); // { count, results: [...] }
}
```

---

## Error Handling & Reconnection

| Close Code | Meaning             | Action                                      |
|------------|---------------------|---------------------------------------------|
| `1000`     | Normal close        | No action                                   |
| `4003`     | Not a provider      | Do not reconnect — user lacks provider role  |
| Other      | Unexpected          | Reconnect with exponential backoff           |

### Recommended Reconnection Logic

```javascript
function connectWithRetry(url, maxRetries = 5) {
  let retries = 0;

  function connect() {
    const ws = new WebSocket(url);

    ws.onopen = () => { retries = 0; };

    ws.onclose = (event) => {
      if (event.code === 4003) return; // Not a provider — stop

      if (retries < maxRetries) {
        const delay = Math.min(1000 * 2 ** retries, 30000);
        retries++;
        setTimeout(connect, delay);
      }
    };

    return ws;
  }

  return connect();
}
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `notifications/dashboard_services.py` | `DashboardStatsService` — all stats computation |
| `notifications/dashboard_consumer.py` | `DashboardConsumer` — WebSocket consumer |
| `notifications/routing.py` | WebSocket URL routing (`ws/dashboard/`) |
| `notifications/services.py` | `WebSocketBroadcaster.send_to_dashboard()` |
| `appointments/signals.py` | Pushes `dashboard_appointments_updated` |
| `invoices/signals.py` | Pushes `dashboard_invoices_updated` |
| `reviews/signals.py` | Pushes `dashboard_reviews_updated` |
| `patients/signals.py` | Pushes `dashboard_patients_updated` |
| `patients/views.py` | `provider_patient_stats` REST endpoint |
| `notifications/views.py` | `activity_feed_api` REST endpoint |
