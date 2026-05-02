# Nurse Authentication API Documentation

> **For:** Flutter Mobile Developer  
> **Backend:** Django REST Framework  
> **Auth scheme:** Token Authentication (DRF `rest_framework.authtoken`)

---

## Base URL

```
https://your-api-domain.com
```

Replace with the actual server URL for dev / staging / production.

---

## Table of Contents

1. [Create Nurse Account (Register)](#1-create-nurse-account-register)
2. [Login](#2-login)
3. [Logout](#3-logout)
4. [Error Reference](#4-error-reference)
5. [Flutter Implementation Checklist](#5-flutter-implementation-checklist)

---

## 1. Create Nurse Account (Register)

```
POST /api/auth/provider/register/
```

> **Content-Type: `multipart/form-data`** — mandatory because document files are uploaded.  
> Do **not** use `application/json` for this endpoint.

### Request Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | **yes** | Lowercased automatically by the server |
| `password` | string | **yes** | Django password validation applies (min 8 chars, not too common, not all numeric) |
| `password_confirm` | string | **yes** | Must match `password` exactly |
| `provider_type` | string | **yes** | Must be exactly `"NURSE"` |
| `first_name` | string | **yes** | |
| `last_name` | string | **yes** | |
| `phone_number` | string | **yes** | Min 8 digits after stripping spaces and dashes |
| `degree_document` | file | **yes** | Diploma / degree scan (image or PDF) |
| `entrepreneur_card_front` | file | **yes** | Entrepreneur card — front side |
| `entrepreneur_card_back` | file | **yes** | Entrepreneur card — back side |
| `entrepreneur_card_pdf` | file | no | Optional combined PDF version of the entrepreneur card |
| `license_number` | string | no | Optional — omit or send empty string if unknown |

---

### Success Response — `201 Created`

Returned when a **new** nurse account is created.

```json
{
  "user": {
    "id": 42,
    "email": "nurse@example.com",
    "role": "PROVIDER",
    "first_name": "Amina",
    "last_name": "Benali",
    "profile_image": null,
    "full_name": "Amina Benali",
    "phone_number": "+213555000000",
    "is_active": true,
    "email_verified": false,
    "profile_completed": false,
    "profile_completion_percentage": 0,
    "created_at": "2026-05-02T10:00:00Z"
  },
  "provider": {
    "status": "PENDING",
    "refusal_reason": null,
    "approved_at": null,
    "verified_at": null,
    "provider_type": "NURSE",
    "provider_type_display": "Nurse"
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

> **Important:** `provider.status` will always be `"PENDING"` after registration.  
> The nurse **cannot log in** until an administrator approves the account.  
> The token returned here is valid but access to protected endpoints will be blocked until approval.

---

### Idempotent Re-registration — `200 OK`

If the same email is submitted again with `provider_type: "NURSE"`, the server returns `200` with the **existing** account data instead of creating a duplicate. The response shape is identical to `201`.

> Handle both `200` and `201` as success on this endpoint.

---

### Error Responses — Registration

#### `400 Bad Request` — Validation errors

The response body is a JSON object where each key is the **failing field name** and the value is an array of error strings. Multiple field errors can appear in the same response.

```json
{
  "email": ["A user with this email already exists."],
  "password": ["This password is too short. It must contain at least 8 characters."],
  "password_confirm": ["Passwords do not match."],
  "first_name": ["This field is required for nurse signup."],
  "last_name": ["This field is required for nurse signup."],
  "phone_number": ["Phone number is too short."],
  "degree_document": ["This field is required for nurse signup."],
  "entrepreneur_card_front": ["This field is required for nurse signup."],
  "entrepreneur_card_back": ["This field is required for nurse signup."]
}
```

> Always iterate over all keys — do not assume only one field fails at a time.

#### `400 Bad Request` — Email already used with a different role

```json
{
  "email": [
    "User with this email already exists with role PATIENT. Cannot create provider account."
  ]
}
```

#### `400 Bad Request` — Service-level error (rare)

```json
{
  "error": "Description of the problem."
}
```

---

## 2. Login

```
POST /api/auth/login/
```

> **Content-Type: `application/json`**

### Request Body

```json
{
  "email": "nurse@example.com",
  "password": "securepassword123"
}
```

---

### Success Response — `200 OK`

```json
{
  "user": {
    "id": 42,
    "email": "nurse@example.com",
    "role": "PROVIDER",
    "first_name": "Amina",
    "last_name": "Benali",
    "profile_image": null,
    "full_name": "Amina Benali",
    "phone_number": "+213555000000",
    "is_active": true,
    "email_verified": false,
    "profile_completed": false,
    "profile_completion_percentage": 60,
    "created_at": "2026-05-02T10:00:00Z",
    "provider_type": "NURSE",
    "provider_type_display": "Nurse"
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

> **Save the `token` in secure storage** (e.g. `flutter_secure_storage`).  
> Send it in every authenticated request as an HTTP header:
>
> ```
> Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
> ```

---

### Error Responses — Login

#### `400 Bad Request` — Missing fields

```json
{
  "error": "Email and password are required."
}
```

#### `401 Unauthorized` — Wrong credentials

```json
{
  "error": "Invalid email or password."
}
```

#### `403 Forbidden` — Account inactive

```json
{
  "error": "Account is inactive."
}
```

#### `403 Forbidden` — Account blocked at user level

```json
{
  "error": "Account is suspended. Access denied.",
  "account_status": "SUSPENDED"
}
```

Possible `account_status` values: `"ACTIVE"`, `"SUSPENDED"`, `"BANNED"`, `"DELETED"`.

#### `403 Forbidden` — Awaiting admin approval (most common after registration)

```json
{
  "error": "Account verification in progress.",
  "provider_status": "PENDING",
  "message": "Your account is currently being reviewed by our medical board. You will receive an email once your professional documents are verified."
}
```

#### `403 Forbidden` — Registration refused by admin

```json
{
  "error": "Account registration refused.",
  "provider_status": "REFUSED",
  "refusal_reason": "Degree document is unreadable.",
  "message": "Your account registration was refused for the following reason: Degree document is unreadable. Please contact support or re-upload your documents."
}
```

> Always display `refusal_reason` to the user so they know what to fix.

#### `403 Forbidden` — Account suspended by admin

```json
{
  "error": "Account suspended.",
  "provider_status": "SUSPENDED",
  "message": "Your account has been temporarily suspended for administrative reasons. Please contact support."
}
```

#### `423 Locked` — Brute-force protection triggered

```json
{
  "error": "Account temporarily locked due to multiple failed login attempts.",
  "message": "Please try again later or contact support."
}
```

> `423` is a non-standard HTTP status. Ensure your HTTP client handles it gracefully and does not throw an unhandled exception.

---

### Login Error Summary Table

| HTTP Status | `error` field | Extra fields | Trigger |
|---|---|---|---|
| `400` | `"Email and password are required."` | — | Empty body |
| `401` | `"Invalid email or password."` | — | Wrong credentials |
| `403` | `"Account is inactive."` | — | Admin disabled the user |
| `403` | `"Account is <status>. Access denied."` | `account_status` | User-level block |
| `403` | `"Account verification in progress."` | `provider_status: "PENDING"` | Awaiting admin approval |
| `403` | `"Account registration refused."` | `provider_status: "REFUSED"`, `refusal_reason` | Admin refused documents |
| `403` | `"Account suspended."` | `provider_status: "SUSPENDED"` | Admin suspension |
| `423` | `"Account temporarily locked…"` | `message` | Too many failed attempts |

---

## 3. Logout

```
POST /api/auth/logout/
```

> Requires `Authorization: Token <token>` header.

### Response — `200 OK`

```json
{
  "message": "Successfully logged out."
}
```

> The token is deleted server-side after logout. Clear it from local storage immediately.

---

## 4. Error Reference

### Password Validation Rules (Django default)

The server rejects passwords that:
- Are shorter than 8 characters → `"This password is too short. It must contain at least 8 characters."`
- Are entirely numeric → `"This password is entirely numeric."`
- Are too common (e.g. `"password123"`) → `"This password is too common."`
- Are too similar to the email address → `"The password is too similar to the email address."`

### Phone Number Rules

- Spaces and dashes are stripped automatically before validation.
- The cleaned number must be at least 8 digits long.
- Invalid: `"error"` → `"Phone number is too short."`

### Provider Status Values

| Value | Meaning |
|---|---|
| `"PENDING"` | Submitted, awaiting admin review |
| `"APPROVED"` | Approved — nurse can log in and use the app |
| `"REFUSED"` | Documents rejected — see `refusal_reason` |
| `"SUSPENDED"` | Suspended by admin |

---

## 5. Flutter Implementation Checklist

- [ ] Use `multipart/form-data` for registration (`http.MultipartRequest` or `dio` with `FormData`) — **not** JSON
- [ ] Attach all three required files (`degree_document`, `entrepreneur_card_front`, `entrepreneur_card_back`) before submitting
- [ ] Handle both `200` and `201` as success on the register endpoint
- [ ] After registration, show the nurse a "pending approval" screen — the account is not usable yet
- [ ] On login `403`, check whether the body contains `provider_status` or `account_status` to show the right message
- [ ] When `provider_status == "REFUSED"`, display `refusal_reason` to the user
- [ ] Handle HTTP `423` explicitly — most Flutter HTTP clients will not map it to a named exception by default
- [ ] Store the `token` in `flutter_secure_storage` (not `SharedPreferences`)
- [ ] Send `Authorization: Token <token>` in the headers of every authenticated request
- [ ] On logout, delete the token from secure storage and navigate back to the login screen
- [ ] On any `401` response from a protected endpoint (token expired / deleted), redirect to login
