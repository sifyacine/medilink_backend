# Patient Integration README - Edit Profile, Upload Image, Update Data

## Scope
This guide covers patient profile retrieval and updates through the auth profile endpoint.

Base API root: `/api/auth/`
Auth header: `Authorization: Token <token>`

## Endpoints
1. `GET /api/auth/me/`
2. `PATCH /api/auth/me/`
3. `PUT /api/auth/me/`

## Backend Revision Included
Patient profile image is now supported on `User.profile_image` and can be updated by patient users through `PATCH /api/auth/me/`.

## Get Profile
Endpoint: `GET /api/auth/me/`

Response includes:
1. user identity fields
2. `profile_image`
3. patient profile aggregate (`patient_profile`)
4. address list (`addresses`)

## Update Profile Data (Patient)
Endpoint: `PATCH /api/auth/me/`

JSON example:
```json
{
  "first_name": "Yasmine",
  "last_name": "Bensalem",
  "phone_number": "+213555001122",
  "profile_completed": true,
  "profile_completion_percentage": 90
}
```

## Upload/Change Profile Image (Patient)
Endpoint: `PATCH /api/auth/me/`

Use `multipart/form-data` with file part:
1. `profile_image`: image file (`jpg`, `png`, `webp`)

Example form fields:
1. `profile_image` = <binary file>
2. `first_name` = `Yasmine` (optional in same request)

## Remove Profile Image
Send multipart with:
1. `profile_image` = null

If your client cannot send null in multipart, use JSON patch with explicit `null` when serializer/parser setup allows it.

## Validation Notes
1. If request contains only read-only fields, backend returns `400` with clear message.
2. Non-updatable account status/role fields are ignored and rejected as non-updatable payload intent.

## Client Integration Notes
1. Always send `Authorization` token.
2. For image upload, set request content type to multipart and do not manually set incorrect boundaries.
3. Refresh profile after update by calling `GET /api/auth/me/` to sync final values and URLs.
