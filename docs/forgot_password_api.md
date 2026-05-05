# Forgot Password API

Base URL: `https://dzmedilink.duckdns.org`  
Frontend: `https://dzmedilink.netlify.app`

---

## Overview

The forgot-password flow has two steps:

1. **Request a reset link** — the user submits their email and receives a reset link by email.
2. **Confirm the reset** — the frontend sends the token from the link along with the new password.

Both endpoints are public (no authentication required).

---

## 1. Request Password Reset

Sends a password-reset email to the user. Always returns HTTP 200 to prevent email enumeration.

**Endpoint**

```
POST /api/auth/password/reset/
```

**Request headers**

```
Content-Type: application/json
```

**Request body**

```json
{
  "email": "user@example.com"
}
```

| Field   | Type   | Required | Description            |
|---------|--------|----------|------------------------|
| `email` | string | yes      | Registered email address |

**Success response — 200 OK**

```json
{
  "message": "If an account with that email exists, a reset link has been sent."
}
```

> The same message is returned whether or not the email exists in the system.

**Error response — 400 Bad Request**

```json
{
  "error": "Email is required."
}
```

**What happens**

- Django generates a secure, one-time token tied to the user and their current password hash.
- The token expires in **24 hours**.
- An HTML email is sent to the address with a reset link of the form:

  ```
  https://dzmedilink.netlify.app/reset-password/<uid>/<token>/
  ```

  where `<uid>` is the base64-encoded user ID.

---

## 2. Confirm Password Reset

Validates the token and sets the new password. Revokes all existing auth tokens on success.

**Endpoint**

```
POST /api/auth/password/reset/confirm/
```

**Request headers**

```
Content-Type: application/json
```

**Request body**

```json
{
  "uid": "MQ==",
  "token": "c3ab8f-abc123...",
  "new_password": "MyNewSecurePass1!",
  "new_password_confirm": "MyNewSecurePass1!"
}
```

| Field                  | Type   | Required | Description                              |
|------------------------|--------|----------|------------------------------------------|
| `uid`                  | string | yes      | Base64-encoded user ID (from reset link) |
| `token`                | string | yes      | Reset token (from reset link)            |
| `new_password`         | string | yes      | New password                             |
| `new_password_confirm` | string | yes      | Must match `new_password`                |

**Success response — 200 OK**

```json
{
  "message": "Password reset successfully."
}
```

**Error responses — 400 Bad Request**

```json
{ "error": "All fields are required." }
```

```json
{ "error": "Passwords do not match." }
```

```json
{ "error": "Invalid or expired reset token." }
```

```json
{ "error": "Invalid reset token." }
```

---

## Frontend Integration Guide

### Step 1 — Forgot Password page

```js
// POST /api/auth/password/reset/
const response = await fetch('https://dzmedilink.duckdns.org/api/auth/password/reset/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email }),
});
const data = await response.json();
// Always show data.message to the user regardless of status
```

### Step 2 — Reset Password page

The frontend receives the URL:

```
https://dzmedilink.netlify.app/reset-password/<uid>/<token>/
```

Extract `uid` and `token` from the path and call:

```js
// POST /api/auth/password/reset/confirm/
const response = await fetch('https://dzmedilink.duckdns.org/api/auth/password/reset/confirm/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ uid, token, new_password, new_password_confirm }),
});

if (response.ok) {
  // Redirect to login
} else {
  const { error } = await response.json();
  // Show error to user
}
```

---

## Server Configuration

### Required environment variables (`.env.prod` on the server)

| Variable              | Description                              | Example                          |
|-----------------------|------------------------------------------|----------------------------------|
| `FRONTEND_URL`        | Base URL of the frontend                 | `https://dzmedilink.netlify.app` |
| `EMAIL_BACKEND`       | Django email backend class               | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST`          | SMTP server hostname                     | `smtp.gmail.com`                 |
| `EMAIL_PORT`          | SMTP port                                | `587`                            |
| `EMAIL_USE_TLS`       | Enable STARTTLS                          | `True`                           |
| `EMAIL_HOST_USER`     | SMTP login / sender address              | `your-account@gmail.com`         |
| `EMAIL_HOST_PASSWORD` | SMTP password or app password            | `xxxx xxxx xxxx xxxx`            |
| `DEFAULT_FROM_EMAIL`  | Display name + address in From header    | `MediLink <no-reply@medilink.dz>` |

### Gmail setup (recommended for small scale)

1. Enable 2-Step Verification on the Gmail account.
2. Go to **Google Account → Security → App Passwords**.
3. Generate an App Password for "Mail".
4. Use that 16-character password as `EMAIL_HOST_PASSWORD`.
5. Set `EMAIL_HOST_USER` to the full Gmail address.

### Reload after changing `.env.prod`

```bash
sudo systemctl restart gunicorn   # or your process manager
```

---

## Security Notes

- The reset token is generated by Django's `default_token_generator` (HMAC-SHA256 over the user's PK, last login, and current password hash).
- The token is **single-use** — it becomes invalid the moment the password changes because the password hash changes.
- The token expires after **24 hours** (Django default: `PASSWORD_RESET_TIMEOUT = 259200` seconds / 3 days; overridden to 24 h by the token generator checking `last_login`).
- On success, **all existing auth tokens are revoked** — the user must log in again.
- The request endpoint always returns the same response whether or not the email exists, preventing user enumeration attacks.
