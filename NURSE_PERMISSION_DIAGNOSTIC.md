# Nurse Permission Issue - Diagnostic Report

## Issue Summary
Frontend showing error: **"Only nurse providers can perform this action"** when nurse tries to access `/api/nurse-requests/nurse/available-requests/`

## Root Cause Analysis

### What's Happening
1. **User registered as CLINIC provider instead of NURSE**
   - Email: `sifyacine2003@gmail.com`
   - Current Provider Type: `CLINIC`
   - Expected Provider Type: `NURSE`

2. **Permission Check**
   The `IsNurse` permission class in `nurse_requests/permissions.py` checks:
   ```python
   if provider.provider_type != 'NURSE':
       return False  # Access denied
   ```

### Current Database State
```
User: sifyacine2003@gmail.com (ID: 4)
Role: PROVIDER ✓
Provider ID: 3
Provider Type: CLINIC ✗ (should be NURSE)
Status: APPROVED
```

## Solution Options

### Option 1: Fix the Account (Recommended)
Use the provided management command to change provider type:

```bash
python manage.py fix_provider_type "sifyacine2003@gmail.com" NURSE
```

This will:
- Delete the old CLINIC profile
- Change provider_type to NURSE
- Create a new NURSE profile

### Option 2: Diagnostic Commands Available

1. **Check all accounts:**
   ```bash
   python manage.py check_accounts
   ```
   Shows all users and their provider types

2. **Diagnose and auto-fix nurse profiles:**
   ```bash
   python manage.py fix_nurse_profiles
   python manage.py fix_nurse_profiles --fix  # Auto-fix issues
   ```

3. **Change any provider type:**
   ```bash
   python manage.py fix_provider_type "<email>" "<new_type>"
   # new_type: DOCTOR, NURSE, CLINIC, LABORATORY, VTC, SELLER
   ```

## Improved Error Messages

The permission class now provides better error messages:
- "User is a CLINIC provider, not a nurse provider" (specific)
- Instead of generic "Only nurse providers can perform this action"

This helps identify the exact problem more quickly.

## Prevention

To prevent this in the future:

1. **Frontend validation** - Ensure the app clearly shows which provider type is selected during registration
2. **Pre-registration confirmation** - Show a confirmation screen before submitting provider type
3. **Better error messages** - Return specific error messages explaining what went wrong

## Files Modified

1. `nurse_requests/permissions.py` - Improved error messages
2. `accounts/management/commands/check_accounts.py` - Diagnostic tool
3. `accounts/management/commands/fix_nurse_profiles.py` - Auto-fix tool
4. `accounts/management/commands/fix_provider_type.py` - Change provider type tool
