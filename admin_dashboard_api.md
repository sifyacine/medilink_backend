# MediLink Admin Dashboard — API Reference

All admin endpoints require **token authentication** and the caller's user role must be `ADMIN`.

Base prefix: `/api/admin/`

---

## Table of Contents

1. [Specialties](#1-specialties)
2. [Services](#2-services)
3. [Social Media Links](#3-social-media-links)
4. [Platform Content](#4-platform-content)
5. [Products & Income](#5-products--income)
6. [Providers](#6-providers)
7. [Users](#7-users)
8. [Patients](#8-patients)
9. [Invoices](#9-invoices)
10. [Analytics](#10-analytics)
11. [Activity Logs](#11-activity-logs)

---

## 1. Specialties

Manage the global medical specialty catalog and doctor–specialty assignments.
These are the specialties shown to patients when browsing doctors and filtering by specialty.
All text fields support **English, Arabic, and French**.

### 1.1 Specialty Catalog

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/specialties/` | List all specialties |
| `POST` | `/api/admin/specialties/` | Create a specialty |
| `GET` | `/api/admin/specialties/{id}/` | Get specialty detail |
| `PATCH` | `/api/admin/specialties/{id}/` | Update specialty |
| `DELETE` | `/api/admin/specialties/{id}/` | Hard-delete specialty |
| `POST` | `/api/admin/specialties/{id}/toggle-active/` | Flip `is_active` |

#### Query Parameters (GET list)

| Param | Values | Description |
|-------|--------|-------------|
| `is_active` | `true` / `false` | Filter by active status |
| `medical_domain` | string | Filter by domain (e.g. `Surgery`) |
| `search` | string | Full-text search across all 3 language title/description fields |
| `ordering` | `title`, `created_at`, `updated_at` (prefix `-` for desc) | Sort order |

#### Create / Update Body

```json
{
  "title": "Cardiology",
  "title_en": "Cardiology",
  "title_ar": "طب القلب",
  "title_fr": "Cardiologie",
  "description": "Heart and cardiovascular system specialists.",
  "description_en": "Heart and cardiovascular system specialists.",
  "description_ar": "أطباء متخصصون في القلب والجهاز الوعائي.",
  "description_fr": "Spécialistes du cœur et du système cardiovasculaire.",
  "medical_domain": "Internal Medicine",
  "is_active": true,
  "meta_title": "Find Cardiologists in Algeria",
  "meta_description": "Book appointments with verified cardiologists on MediLink."
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Specialty ID |
| `title` | string | Primary title (EN fallback) |
| `slug` | string | URL-friendly identifier (auto-generated) |
| `title_en/ar/fr` | string | Translated titles |
| `description_en/ar/fr` | string | Translated descriptions |
| `medical_domain` | string | Grouping domain |
| `icon` | string/null | Icon image URL |
| `is_active` | bool | Whether visible to patients |
| `meta_title` | string | SEO title |
| `meta_description` | string | SEO description |
| `created_at` / `updated_at` | datetime | Timestamps |

---

### 1.2 Doctor–Specialty Assignments

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/doctor-specialties/` | List all doctor ↔ specialty links |
| `POST` | `/api/admin/doctor-specialties/` | Assign a specialty to a doctor |
| `PATCH` | `/api/admin/doctor-specialties/{id}/` | Update `is_primary` or `years_of_experience` |
| `DELETE` | `/api/admin/doctor-specialties/{id}/` | Remove assignment |

#### Query Parameters

| Param | Description |
|-------|-------------|
| `doctor` | Filter by doctor ID |
| `specialty` | Filter by specialty ID |
| `is_primary` | `true` / `false` |
| `search` | Doctor name or specialty title |

#### Create Body

```json
{
  "doctor": 12,
  "specialty_id": 3,
  "is_primary": true,
  "years_of_experience": 8
}
```

---

## 2. Services

Manage the platform's medical service catalog. Admins create/edit services; doctors and nurses then subscribe to them with optional custom pricing.

### 2.1 Service Catalog

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/services/` | List all services |
| `POST` | `/api/admin/services/` | Create a service |
| `GET` | `/api/admin/services/{id}/` | Service detail with provider assignment counts |
| `PATCH` | `/api/admin/services/{id}/` | Update service |
| `DELETE` | `/api/admin/services/{id}/` | Hard-delete service |
| `POST` | `/api/admin/services/{id}/toggle-active/` | Flip `is_active` |
| `POST` | `/api/admin/services/{id}/toggle-on-demand/` | Flip `is_on_demand` |
| `GET` | `/api/admin/services/stats/` | Catalog-wide statistics |

#### Query Parameters

| Param | Values | Description |
|-------|--------|-------------|
| `service_type` | `DOCTOR`, `NURSE`, `VTC`, `GENERAL` | Filter by type |
| `is_active` | `true` / `false` | Active status |
| `is_on_demand` | `true` / `false` | On-demand (nursing Uber-flow) |
| `is_home_service` | `true` / `false` | Home visit service |
| `specialty` | int | Filter by related specialty ID |
| `currency` | `DZD`, `USD`, `EUR` | Filter by currency |
| `search` | string | Title/description in all 3 languages |
| `ordering` | `title`, `price`, `duration_minutes`, `created_at` | Sort order |

#### Create / Update Body

```json
{
  "title": "General Consultation",
  "title_en": "General Consultation",
  "title_ar": "استشارة عامة",
  "title_fr": "Consultation Générale",
  "description_en": "Standard in-clinic doctor consultation.",
  "description_ar": "استشارة طبيب عيادة قياسية.",
  "description_fr": "Consultation médicale standard en clinique.",
  "service_type": "DOCTOR",
  "price": 2000.00,
  "currency": "DZD",
  "duration_minutes": 30,
  "is_home_service": false,
  "is_on_demand": false,
  "is_active": true,
  "specialty": 3
}
```

#### Stats Response

```json
{
  "total_services": 45,
  "active_services": 40,
  "inactive_services": 5,
  "on_demand_nurse_services": 12,
  "nurse_provider_assignments": 128,
  "doctor_provider_assignments": 95,
  "provider_custom_services": 33,
  "by_type": {
    "DOCTOR": { "total": 20, "active": 18, "on_demand": 0 },
    "NURSE":  { "total": 15, "active": 14, "on_demand": 12 }
  }
}
```

---

### 2.2 Nurse–Service Assignments

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/nurse-services/` | List nurse ↔ service links |
| `PATCH` | `/api/admin/nurse-services/{id}/` | Edit custom price or availability |
| `DELETE` | `/api/admin/nurse-services/{id}/` | Remove assignment |

Filters: `?is_available=`, `?service=`, `?service__service_type=`

---

### 2.3 Doctor–Service Assignments

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/doctor-services/` | List doctor ↔ service links |
| `PATCH` | `/api/admin/doctor-services/{id}/` | Edit custom price or availability |
| `DELETE` | `/api/admin/doctor-services/{id}/` | Remove assignment |

Filters: `?is_available=`, `?service=`, `?service__service_type=`

---

### 2.4 Provider Custom Services

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/custom-services/` | List all provider-created custom services |
| `PATCH` | `/api/admin/custom-services/{id}/` | Edit custom service |
| `POST` | `/api/admin/custom-services/{id}/toggle-active/` | Flip `is_active` |
| `DELETE` | `/api/admin/custom-services/{id}/` | Delete custom service |

Filters: `?is_active=`, `?is_home_service=`, `?is_online_available=`, `?specialty=`

---

## 3. Social Media Links

Two separate social media systems exist on the platform:

| System | Model | Purpose |
|--------|-------|---------|
| **Provider social links** | `SocialMediaLink` | Links attached to individual provider profiles (generic FK) |
| **Platform social links** | `PlatformSocialLink` | Platform footer/contact social links (Facebook page, Instagram, etc.) |

### 3.1 Provider Social Links

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/social-links/` | List all provider social links |
| `POST` | `/api/admin/social-links/` | Create a link for any entity |
| `GET` | `/api/admin/social-links/{id}/` | Link detail |
| `PATCH` | `/api/admin/social-links/{id}/` | Update link |
| `DELETE` | `/api/admin/social-links/{id}/` | Delete link |

#### Query Parameters

| Param | Description |
|-------|-------------|
| `provider_id` | Filter links for a specific provider |
| `content_type_id` + `object_id` | Filter links for any generic entity |
| `platform` | `FACEBOOK`, `INSTAGRAM`, `TWITTER`, `LINKEDIN`, `YOUTUBE`, `TIKTOK`, `OTHER` |
| `is_visible` | `true` / `false` |

#### Create Body

```json
{
  "content_type": 15,
  "object_id": 42,
  "platform": "INSTAGRAM",
  "url": "https://instagram.com/dr.example",
  "is_visible": true,
  "display_order": 1
}
```

---

### 3.2 Platform Social Links (Footer / Contact Page)

Managed under the platform content module.

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/platform/social-links/` | List platform social links |
| `POST` | `/api/admin/platform/social-links/` | Create platform social link |
| `PATCH` | `/api/admin/platform/social-links/{id}/` | Update link |
| `DELETE` | `/api/admin/platform/social-links/{id}/` | Delete link |

#### Supported Platforms

`FACEBOOK`, `INSTAGRAM`, `TWITTER`, `LINKEDIN`, `YOUTUBE`, `TIKTOK`, `OTHER`

> When `platform` is `OTHER`, `custom_label` is **required**.

#### Create Body

```json
{
  "platform": "FACEBOOK",
  "url": "https://facebook.com/medilink.dz",
  "display_order": 1,
  "is_active": true
}
```

---

## 4. Platform Content

CMS endpoints for all public-facing content. Requires `CONTENT_EDITOR` sub-role (all admins qualify).

### 4.1 Landing Page Sections

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/platform/sections/` | List all sections |
| `POST` | `/api/admin/platform/sections/` | Create section |
| `PATCH` | `/api/admin/platform/sections/{id}/` | Update section |
| `DELETE` | `/api/admin/platform/sections/{id}/` | Delete section |

Key `section_key` values used by the frontend: `hero`, `features`, `testimonials`, `stats`, `cta`.

#### Body

```json
{
  "section_key": "hero",
  "title_en": "Your Health, Connected",
  "title_ar": "صحتك، متصلة",
  "title_fr": "Votre santé, connectée",
  "subtitle_en": "Book doctors, nurses and labs in minutes.",
  "body_en": "...",
  "cta_text_en": "Get Started",
  "cta_url": "/register",
  "is_active": true,
  "display_order": 1
}
```

---

### 4.2 Announcements

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/platform/announcements/` | List all announcements |
| `POST` | `/api/admin/platform/announcements/` | Create announcement |
| `PATCH` | `/api/admin/platform/announcements/{id}/` | Update |
| `DELETE` | `/api/admin/platform/announcements/{id}/` | Delete |

#### Body

```json
{
  "title_en": "Scheduled maintenance",
  "title_ar": "صيانة مجدولة",
  "title_fr": "Maintenance planifiée",
  "body_en": "The platform will be unavailable on Sunday from 2–4 AM.",
  "announcement_type": "WARNING",
  "target_audience": "ALL",
  "is_active": true,
  "starts_at": "2026-06-01T02:00:00Z",
  "ends_at": "2026-06-01T04:00:00Z"
}
```

`announcement_type`: `INFO` | `WARNING` | `SUCCESS` | `DANGER`
`target_audience`: `ALL` | `PATIENTS` | `PROVIDERS`

---

### 4.3 FAQs

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/platform/faqs/` | List all FAQs |
| `POST` | `/api/admin/platform/faqs/` | Create FAQ |
| `PATCH` | `/api/admin/platform/faqs/{id}/` | Update FAQ |
| `DELETE` | `/api/admin/platform/faqs/{id}/` | Delete FAQ |

---

### 4.4 Blog Posts

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/platform/posts/` | List all posts |
| `POST` | `/api/admin/platform/posts/` | Create post (starts as `DRAFT`) |
| `PATCH` | `/api/admin/platform/posts/{id}/` | Update post |
| `POST` | `/api/admin/platform/posts/{id}/publish/` | Publish post |
| `POST` | `/api/admin/platform/posts/{id}/archive/` | Archive post |
| `DELETE` | `/api/admin/platform/posts/{id}/` | Delete post |

`status` values: `DRAFT` | `PUBLISHED` | `ARCHIVED`

---

### 4.5 Contact Info (Singleton)

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/platform/contact/` | Get contact info |
| `PATCH` | `/api/admin/platform/contact/` | Update contact info |

```json
{
  "phone": "+213 21 00 00 00",
  "email": "contact@medilink.dz",
  "support_email": "support@medilink.dz",
  "whatsapp": "+213 5XX XXX XXX",
  "address": "Algiers, Algeria",
  "office_hours": "Sun–Thu 8:00–17:00"
}
```

---

### 4.6 Legal Documents (Singleton per type)

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/platform/legal/{doc_type}/` | Get document |
| `PATCH` | `/api/admin/platform/legal/{doc_type}/` | Update document |

`doc_type` values: `PRIVACY_POLICY` | `TERMS_AND_CONDITIONS` | `COOKIE_POLICY`

```json
{
  "title_en": "Privacy Policy",
  "title_ar": "سياسة الخصوصية",
  "title_fr": "Politique de confidentialité",
  "content_en": "# Privacy Policy\n...",
  "content_ar": "...",
  "content_fr": "...",
  "version": "v2.0",
  "is_active": true
}
```

---

## 5. Products & Income

MediLink's own product catalog (subscriptions, medical supplies, equipment, etc.) and revenue tracking.

### 5.1 Products

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/products/` | List all products |
| `POST` | `/api/admin/products/` | Create product |
| `GET` | `/api/admin/products/{id}/` | Product detail |
| `PATCH` | `/api/admin/products/{id}/` | Update product |
| `DELETE` | `/api/admin/products/{id}/` | Delete product |
| `POST` | `/api/admin/products/{id}/toggle-active/` | Flip `is_active` |

#### Product Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Product name |
| `sku` | string | Unique SKU (optional) |
| `category` | enum | `SUBSCRIPTION`, `SOFTWARE`, `MEDICAL_SUPPLY`, `EQUIPMENT`, `DIGITAL`, `OTHER` |
| `cost_price` | decimal | Internal cost (not shown publicly) |
| `selling_price` | decimal | Price shown to buyers |
| `currency` | string | Always `DZD` (platform-standardized) |
| `discount_type` | enum | `PERCENTAGE` or `FIXED` (blank for no discount) |
| `discount_value` | decimal | Discount amount |
| `effective_price` | decimal | `selling_price` minus discount (read-only) |
| `is_for_sale` | bool | Product can be purchased outright (default `true`) |
| `is_for_rent` | bool | Product can be rented (default `false`) |
| `rental_price_per_day` | decimal/null | Daily rental price (required when `is_for_rent` is `true`) |
| `stock_quantity` | int | Current stock |
| `low_stock_threshold` | int | Alert threshold (default 5) |
| `is_low_stock` | bool | `stock_quantity <= low_stock_threshold` (read-only) |
| `rating` | decimal | 0–5 rating (read-only) |
| `is_active` | bool | Whether product appears in public catalog |

#### Acquisition Type Rules

- A product **must** be available for at least one of `is_for_sale` or `is_for_rent`.
- When `is_for_rent` is `true`, `rental_price_per_day` must be a positive value.
- When `is_for_rent` is `false`, `rental_price_per_day` is automatically cleared to `null`.

#### Create Body Example (Rentable Medical Equipment)

```json
{
  "name": "Portable ECG Monitor",
  "sku": "ECG-001",
  "category": "EQUIPMENT",
  "cost_price": 45000.00,
  "selling_price": 60000.00,
  "is_for_sale": true,
  "is_for_rent": true,
  "rental_price_per_day": 800.00,
  "stock_quantity": 10,
  "low_stock_threshold": 2,
  "is_active": true
}
```

#### Image Upload

Products support a primary image and a gallery. Use `multipart/form-data`:

```
POST /api/admin/products/
Content-Type: multipart/form-data

image=<file>          # primary image
images[]=<file>       # gallery image 1
images[]=<file>       # gallery image 2
```

To remove gallery images on update:
```
PATCH /api/admin/products/{id}/
remove_image_ids[]=5
remove_image_ids[]=7
```

---

### 5.2 Income / Sales Records

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/income/` | List all sale records |
| `POST` | `/api/admin/income/` | Record a new sale |
| `GET` | `/api/admin/income/{id}/` | Sale detail |
| `PATCH` | `/api/admin/income/{id}/` | Update sale |
| `DELETE` | `/api/admin/income/{id}/` | Delete record |

#### Create Body

```json
{
  "product": 3,
  "buyer": 88,
  "quantity": 1,
  "unit_price": 2500.00,
  "total_amount": 2500.00,
  "status": "COMPLETED",
  "notes": "Provider subscription renewal",
  "reference": "TXN-20260523-001"
}
```

`status` values: `PENDING` | `COMPLETED` | `REFUNDED` | `CANCELLED`

---

## 6. Providers

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/providers/` | List all providers with review counts |
| `GET` | `/api/admin/providers/{id}/` | Provider detail |
| `POST` | `/api/admin/providers/{id}/approve/` | Approve provider |
| `POST` | `/api/admin/providers/{id}/refuse/` | Refuse provider |
| `POST` | `/api/admin/providers/{id}/suspend/` | Suspend provider |
| `POST` | `/api/admin/providers/{id}/reactivate/` | Reactivate suspended provider |

Filters: `?provider_type=`, `?status=`, `?search=`

---

## 7. Users

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/users/` | List all users |
| `GET` | `/api/admin/users/{id}/` | User detail |
| `PATCH` | `/api/admin/users/{id}/` | Update user |
| `POST` | `/api/admin/users/{id}/suspend/` | Suspend user account |
| `POST` | `/api/admin/users/{id}/reactivate/` | Reactivate account |
| `DELETE` | `/api/admin/users/{id}/` | Delete user |

Filters: `?role=PATIENT|PROVIDER|ADMIN`, `?account_status=`, `?search=`

---

## 8. Patients

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/patients/` | List all patient records (`PatientRecord`) |
| `GET` | `/api/admin/patients/{id}/` | Patient detail |

---

## 9. Invoices

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/invoices/` | List all invoices |
| `GET` | `/api/admin/invoices/{id}/` | Invoice detail |

---

## 10. Analytics

All analytics endpoints respond with `{ "success": true, "data": { ... } }`.

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/analytics/overview/` | Platform-wide overview KPIs |
| `GET` | `/api/admin/analytics/users/` | User growth and role breakdown |
| `GET` | `/api/admin/analytics/appointments/` | Appointment trends and status counts |
| `GET` | `/api/admin/analytics/revenue/` | Revenue and sales data |
| `GET` | `/api/admin/analytics/providers/` | Provider registration and approval stats |

---

## 11. Activity Logs

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/admin/logs/` | List admin activity log entries |
| `GET` | `/api/admin/logs/{id}/` | Log entry detail |

Filters: `?action_type=`, `?performed_by=`, `?ordering=-created_at`

---

## Authentication

All admin endpoints require:

```
Authorization: Token <token>
```

Obtain token via `POST /api/auth/login/` with admin credentials.

---

## Multilingual Fields Convention

All multilingual text models follow this pattern:

| Field suffix | Language |
|-------------|----------|
| `_en` | English |
| `_ar` | Arabic (RTL) |
| `_fr` | French |

The base field (e.g., `title`) is always the English fallback. When all three are provided, the frontend uses the field matching the user's active language (`Accept-Language` header or `?lang=` query param).
