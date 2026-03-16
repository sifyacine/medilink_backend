# Patient Backend Revisions - 2026-03-14

## Summary
Quick patient-side backend revisions applied while preparing integration documentation.

## Changes Applied
1. Added patient profile image support on user model.
2. Exposed profile image in user/profile serializers used by auth flows.
3. Enabled patient update of `profile_image` via `PATCH /api/auth/me/`.
4. Fixed medical record string rendering fallback to avoid crashes when records are linked through `patient_record` and not direct `patient`.

## Files Updated
1. `accounts/models/user.py`
2. `accounts/serializers/user.py`
3. `accounts/serializers/profile.py`
4. `medical_record/models.py`
5. `accounts/migrations/0003_user_profile_image.py`

## Notes
1. Run migrations before using profile image upload endpoint.
2. Media serving is already enabled in debug mode through `core/urls.py`.
3. In production, ensure media storage and URL serving are correctly configured.
