# Admin Dashboard — Backend Deployment Guide

> Applies to the **Medilink** production server running:
> **nginx → gunicorn (WSGI/HTTP)** + **daphne (ASGI/WebSocket)**

---

## 1. What Changed

| Area | Change |
|------|--------|
| `admins` app | Added `AdminProfile`, `AdminActivityLog` models; full user/patient/provider management; analytics; activity log endpoints |
| `platform_content` app | **New app** — CMS for landing page sections, announcements, FAQs, blog posts, contact info, social links |
| `common/enums.py` | Added `AdminSubRole` and `AdminActionType` |
| `admins/permissions.py` | Replaced single `IsAdmin` with sub-role permission classes |
| `core/urls.py` | Added `/api/admin/platform/` and `/api/platform/` URL groups |
| `core/settings/base.py` | Added `platform_content` to `INSTALLED_APPS` |
| DB migrations | `admins.0001_initial`, `platform_content.0001_initial`, `accounts.0003_*` |

---

## 2. Step-by-step Deployment

### 2.1 Pull the latest code

```bash
cd /path/to/medilink_backend
git pull origin main
```

### 2.2 Activate the virtual environment

```bash
source venv/bin/activate   # Linux/macOS
# or
venv\Scripts\activate      # Windows
```

### 2.3 Install / sync dependencies

```bash
pip install -r requirements.txt
```

> No new packages were added in this update. This step is a safety net.

### 2.4 Run database migrations

```bash
python manage.py migrate
```

Expected output:
```
Applying accounts.0003_user_profile_image... OK
Applying admins.0001_initial... OK
Applying platform_content.0001_initial... OK
```

### 2.5 Collect static files

```bash
python manage.py collectstatic --noinput
```

### 2.6 Create the first Super Admin (if needed)

```bash
# Upgrade an existing user to SUPER_ADMIN
python manage.py create_admin_profile admin@example.com --sub-role SUPER_ADMIN --notes "Initial super admin"

# Create a content editor
python manage.py create_admin_profile editor@example.com --sub-role CONTENT_EDITOR
```

Sub-role options: `SUPER_ADMIN`, `MODERATOR`, `SUPPORT`, `CONTENT_EDITOR`

---

## 3. Reload Application Servers

### 3.1 Reload gunicorn (handles HTTP API requests)

```bash
# If using systemd:
sudo systemctl reload gunicorn
# or send HUP signal to master process:
sudo kill -HUP $(cat /run/gunicorn/gunicorn.pid)
```

> **gunicorn reload** gracefully replaces worker processes — zero downtime.

### 3.2 Reload daphne (handles WebSocket / ASGI connections)

```bash
# If using systemd:
sudo systemctl restart daphne
```

> Daphne does **not** support graceful reload via HUP. A brief restart is required.
> Existing WebSocket clients will reconnect automatically if the frontend implements
> exponential back-off reconnection.

### 3.3 Reload nginx (only if nginx config was changed)

```bash
sudo nginx -t && sudo systemctl reload nginx
```

> Nginx config was **not** modified in this update. Skip unless you changed it manually.

---

## 4. Verification Checklist

After deployment, verify the following endpoints respond correctly:

| Method | URL | Expected |
|--------|-----|----------|
| `GET` | `/api/admin/users/` | 401 (unauthenticated) |
| `GET` | `/api/admin/analytics/overview/` | 401 (unauthenticated) |
| `GET` | `/api/admin/logs/` | 401 (unauthenticated) |
| `GET` | `/api/admin/platform/sections/` | 401 (unauthenticated) |
| `GET` | `/api/platform/sections/` | 200 (public, empty list OK) |
| `GET` | `/api/platform/faqs/` | 200 (public) |
| `GET` | `/api/platform/contact/` | 200 (public) |
| `GET` | `/admin/` | Django admin login page |

---

## 5. New API Surface

### Admin Dashboard Endpoints  (`/api/admin/...` — requires `Authorization: Token <token>`)

#### Provider Management
| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| `GET` | `/api/admin/providers/` | IsAdmin | List all providers |
| `POST` | `/api/admin/providers/{id}/approve/` | IsAdmin | Approve provider |
| `POST` | `/api/admin/providers/{id}/refuse/` | IsAdmin | Refuse provider |
| `POST` | `/api/admin/providers/{id}/suspend/` | IsModerator | Suspend provider |
| `POST` | `/api/admin/providers/{id}/restore/` | IsModerator | Restore suspended provider |

#### User Management
| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| `GET` | `/api/admin/users/` | IsSupport | List all users |
| `GET` | `/api/admin/users/{id}/` | IsSupport | User detail |
| `PATCH` | `/api/admin/users/{id}/` | IsModerator | Update user info |
| `POST` | `/api/admin/users/{id}/suspend/` | IsModerator | Suspend user |
| `POST` | `/api/admin/users/{id}/activate/` | IsModerator | Activate user |
| `POST` | `/api/admin/users/{id}/deactivate/` | IsModerator | Deactivate user |
| `POST` | `/api/admin/users/{id}/reset-password/` | IsModerator | Force password reset email |
| `GET` | `/api/admin/users/{id}/activity/` | IsSupport | User's activity logs |

#### Patient Management
| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| `GET` | `/api/admin/patients/` | IsSupport | List all patients |
| `GET` | `/api/admin/patients/{id}/` | IsSupport | Patient detail |
| `POST` | `/api/admin/patients/{id}/suspend/` | IsModerator | Suspend patient's linked user |

#### Analytics
| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| `GET` | `/api/admin/analytics/overview/` | IsSupport | Overview stats |
| `GET` | `/api/admin/analytics/users/?period=daily` | IsSupport | User registration trends |
| `GET` | `/api/admin/analytics/appointments/` | IsSupport | Appointment stats |
| `GET` | `/api/admin/analytics/revenue/` | IsSupport | Revenue breakdown |
| `GET` | `/api/admin/analytics/providers/` | IsSupport | Provider stats |

#### Activity Log
| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| `GET` | `/api/admin/logs/` | IsSupport | All admin activity logs |
| `GET` | `/api/admin/logs/?action=SUSPEND_USER` | IsSupport | Filter by action type |

#### Platform Content (Admin Write)
| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| `GET/POST` | `/api/admin/platform/sections/` | IsContentEditor | Manage landing page sections |
| `GET/POST` | `/api/admin/platform/announcements/` | IsContentEditor | Manage announcements |
| `GET/POST` | `/api/admin/platform/faqs/` | IsContentEditor | Manage FAQs |
| `GET/POST` | `/api/admin/platform/posts/` | IsContentEditor | Manage blog posts |
| `POST` | `/api/admin/platform/posts/{id}/publish/` | IsContentEditor | Publish a draft post |
| `POST` | `/api/admin/platform/posts/{id}/archive/` | IsContentEditor | Archive a post |
| `GET/PATCH` | `/api/admin/platform/contact/` | IsContentEditor | Update contact info |
| `GET/POST` | `/api/admin/platform/social-links/` | IsContentEditor | Manage social links |

### Public Endpoints  (`/api/platform/...` — no authentication required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/platform/sections/` | Active landing page sections |
| `GET` | `/api/platform/sections/{section_key}/` | Single section by key |
| `GET` | `/api/platform/announcements/` | Active announcements |
| `GET` | `/api/platform/faqs/` | Active FAQs (filter by `?category=`) |
| `GET` | `/api/platform/posts/` | Published blog posts |
| `GET` | `/api/platform/posts/{slug}/` | Single post by slug |
| `GET` | `/api/platform/contact/` | Contact information |
| `GET` | `/api/platform/social-links/` | Active social links |

---

## 6. Permission Matrix

| Sub-role | User Mgmt Read | User Mgmt Write | Provider Mgmt | Analytics | Log Access | Content Edit |
|----------|---------------|-----------------|---------------|-----------|------------|-------------|
| SUPER_ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| MODERATOR | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| SUPPORT | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| CONTENT_EDITOR | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

> Note: All sub-roles inherit `IsAdmin` (user.role == ADMIN). Legacy `IsAdmin` permission on
> existing provider endpoints still applies.

---

## 7. Rollback Plan

If something goes wrong after deployment:

```bash
# 1. Revert to previous commit
git revert HEAD --no-edit
git push origin main

# 2. On the server, pull the reverted code
git pull origin main

# 3. Roll back migrations
python manage.py migrate admins zero
python manage.py migrate platform_content zero

# 4. Reload servers
sudo systemctl reload gunicorn
sudo systemctl restart daphne
```

---

## 8. Environment Variables

No new environment variables were introduced. All existing variables remain unchanged.
