# Patients System - AI/Automation Documentation

## System Architecture Overview

This document provides technical documentation for AI agents, automation scripts, and LLM-based systems integrating with the Medilink Patients API.

---

## Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│      User       │     │    PatientRecord    │     │    Provider     │
│  (accounts)     │     │    (patients)       │     │  (providers)    │
├─────────────────┤     ├─────────────────────┤     ├─────────────────┤
│ id              │     │ id                  │     │ id              │
│ email           │     │ patient_unique_id   │     │ user_id (FK)    │
│ role            │◄────│ linked_user (FK)    │     │ provider_type   │
│ is_active       │     │ linking_token       │     │ is_approved     │
│ can_login       │     │ token_used          │────►│                 │
└─────────────────┘     │ first_name          │     └─────────────────┘
                        │ last_name           │             │
                        │ date_of_birth       │             │
                        │ gender              │             │
                        │ blood_type          │             │
                        │ created_by_provider │◄────────────┘
                        │ is_deleted          │
                        │ is_active           │
                        └─────────────────────┘
                                 │
                                 │ 1:N
                                 ▼
              ┌──────────────────────────────────────┐
              │      ProviderPatientAccess           │
              │      (patients)                      │
              ├──────────────────────────────────────┤
              │ id                                   │
              │ provider_id (FK)                     │
              │ patient_record_id (FK)               │
              │ access_level (FULL/READ_ONLY/LIMITED)│
              │ granted_by (FK)                      │
              └──────────────────────────────────────┘

              ┌──────────────────────────────────────┐
              │      MedicalRecordShareToken         │
              │      (patients)                      │
              ├──────────────────────────────────────┤
              │ id                                   │
              │ token (unique)                       │
              │ patient_record_id (FK)               │
              │ access_level                         │
              │ expires_at                           │
              │ max_uses                             │
              │ use_count                            │
              │ is_active                            │
              │ is_revoked                           │
              │ target_provider_id (FK, optional)    │
              └──────────────────────────────────────┘
                                 │
                                 │ 1:N
                                 ▼
              ┌──────────────────────────────────────┐
              │      ShareTokenAccessLog             │
              │      (patients)                      │
              ├──────────────────────────────────────┤
              │ id                                   │
              │ share_token_id (FK)                  │
              │ accessed_by_provider_id (FK)         │
              │ accessed_at                          │
              │ ip_address                           │
              └──────────────────────────────────────┘

              ┌──────────────────────────────────────┐
              │         MedicalRecord                │
              │         (medical_record)             │
              ├──────────────────────────────────────┤
              │ id                                   │
              │ patient_id (FK to User, nullable)    │
              │ patient_record_id (FK, nullable)     │
              │ title                                │
              │ record_type                          │
              │ description                          │
              │ record_date                          │
              │ created_by (FK)                      │
              │ is_active                            │
              │ is_confidential                      │
              └──────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Flow 1: Patient Record Creation

```
Provider               API                    Database
   │                    │                        │
   │  POST /patients/   │                        │
   │ ─────────────────► │                        │
   │                    │  Create PatientRecord  │
   │                    │ ─────────────────────► │
   │                    │                        │
   │                    │  Generate:             │
   │                    │  - patient_unique_id   │
   │                    │  - linking_token       │
   │                    │                        │
   │                    │  Create Provider       │
   │                    │  PatientAccess (FULL)  │
   │                    │ ─────────────────────► │
   │                    │                        │
   │  201 + record      │                        │
   │ ◄───────────────── │                        │
```

### Flow 2: Account Linking

```
Patient                API                    Database
   │                    │                        │
   │  POST /link-       │                        │
   │  account/          │                        │
   │  {linking_token}   │                        │
   │ ─────────────────► │                        │
   │                    │  Validate token        │
   │                    │ ─────────────────────► │
   │                    │                        │
   │                    │  Check: token_used?    │
   │                    │  Check: already linked?│
   │                    │  Check: user.role?     │
   │                    │                        │
   │                    │  Update PatientRecord: │
   │                    │  - linked_user = user  │
   │                    │  - token_used = True   │
   │                    │ ─────────────────────► │
   │                    │                        │
   │  200 + record      │                        │
   │ ◄───────────────── │                        │
```

### Flow 3: Share Token Creation and Usage

```
Patient                API                    Provider
   │                    │                        │
   │  POST /share-      │                        │
   │  tokens/           │                        │
   │ ─────────────────► │                        │
   │                    │                        │
   │  201 + token       │                        │
   │  + qr_code_data    │                        │
   │ ◄───────────────── │                        │
   │                    │                        │
   │     [Patient shows QR code to Provider]     │
   │                    │                        │
   │                    │  GET /records/share/   │
   │                    │  {token}/              │
   │                    │ ◄───────────────────── │
   │                    │                        │
   │                    │  Validate:             │
   │                    │  - is_usable?          │
   │                    │  - target_provider?    │
   │                    │                        │
   │                    │  record_use()          │
   │                    │  Create AccessLog      │
   │                    │                        │
   │                    │  200 + patient_data    │
   │                    │  + medical_records     │
   │                    │ ─────────────────────► │
```

---

## State Machines

### PatientRecord States

```
                    ┌─────────────┐
                    │   CREATED   │
                    │  (is_active │
                    │   = True)   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐
   │  LINKED   │    │ DEACTIVA- │    │  SOFT     │
   │(linked_   │    │    TED    │    │ DELETED   │
   │ user set) │    │(is_active │    │(is_deleted│
   └───────────┘    │ = False)  │    │ = True)   │
         │          └───────────┘    └─────┬─────┘
         │                                 │
         │          ┌───────────┐          │
         └─────────►│ RESTORED  │◄─────────┘
                    │(is_active │
                    │ = True,   │
                    │is_deleted │
                    │ = False)  │
                    └───────────┘
```

### ShareToken States

```
   ┌─────────────┐
   │   ACTIVE    │
   │ (is_usable  │
   │  = True)    │
   └──────┬──────┘
          │
    ┌─────┼─────┬──────────────┐
    │     │     │              │
    ▼     ▼     ▼              ▼
┌──────┐┌──────┐┌──────┐  ┌──────────┐
│USED  ││EXPI- ││REVOK-│  │ TARGETED │
│(use_ ││RED   ││ED    │  │ (target_ │
│count ││(now >││(is_  │  │ provider │
│>= max││expir-││revok-│  │ set)     │
│_uses)││es_at)││ed)   │  └──────────┘
└──────┘└──────┘└──────┘
```

---

## Role-Based Access Control Matrix

### User Roles

| Action | PATIENT | PROVIDER | ADMIN |
|--------|---------|----------|-------|
| Create PatientRecord | ❌ | ✅ (verified) | ✅ |
| Read Own PatientRecord | ✅ | N/A | ✅ |
| Read Any PatientRecord | ❌ | ✅ (with access) | ✅ |
| Update PatientRecord | ❌ | ✅ (FULL access) | ✅ |
| Delete PatientRecord | ❌ | ✅ (creator only) | ✅ |
| Get Linking Token | ❌ | ✅ (FULL access) | ✅ |
| Regenerate Token | ❌ | ✅ (creator only) | ✅ |
| Grant Access | ❌ | ✅ (FULL access) | ✅ |
| Link Account | ✅ | ❌ | ❌ |
| Create ShareToken | ✅ (linked) | ❌ | ❌ |
| Use ShareToken | ❌ | ✅ | ❌ |
| Revoke ShareToken | ✅ (owner) | ❌ | ✅ |
| View Medical Records | ✅ (own) | ✅ (with access) | ✅ |

### Provider Access Levels

| Capability | FULL | READ_ONLY | LIMITED |
|------------|------|-----------|---------|
| View patient info | ✅ | ✅ | ✅ |
| View medical records | ✅ | ✅ | ✅ (non-confidential) |
| View confidential records | ✅ | ✅ | ❌ |
| Update patient record | ✅ | ❌ | ❌ |
| Grant access to others | ✅ | ❌ | ❌ |
| Get linking token | ✅ | ❌ | ❌ |

---

## API Endpoint Decision Tree

```
START
  │
  ├─ Is user authenticated?
  │   ├─ NO → Return 401 Unauthorized
  │   └─ YES → Continue
  │
  ├─ What is user.role?
  │   │
  │   ├─ PATIENT
  │   │   ├─ Allowed endpoints:
  │   │   │   • GET /api/patients/me/
  │   │   │   • POST /api/patients/link-account/
  │   │   │   • GET/POST /api/patients/share-tokens/
  │   │   │   • POST /api/patients/share-tokens/{id}/revoke/
  │   │   │   • GET /api/patients/my-records/
  │   │   └─ All others → 403 Forbidden
  │   │
  │   ├─ PROVIDER
  │   │   ├─ Is provider.is_approved?
  │   │   │   ├─ NO → Return 403 Forbidden
  │   │   │   └─ YES → Continue
  │   │   ├─ Allowed endpoints:
  │   │   │   • GET/POST /api/patients/
  │   │   │   • GET/PUT/DELETE /api/patients/{id}/
  │   │   │   • GET /api/patients/{id}/token/
  │   │   │   • POST /api/patients/{id}/regenerate-token/
  │   │   │   • POST /api/patients/{id}/grant-access/
  │   │   │   • GET /api/patients/{id}/history/
  │   │   │   • GET /api/patients/records/share/{token}/
  │   │   └─ Object-level checks apply
  │   │
  │   └─ ADMIN
  │       └─ All endpoints allowed
```

---

## Data Validation Rules

### PatientRecord

| Field | Type | Constraints |
|-------|------|-------------|
| patient_unique_id | string | Auto-generated, unique, format: MED-XXXXXXXX |
| linking_token | string | Auto-generated, unique, 256-bit secure |
| first_name | string | Required, max 100 chars |
| last_name | string | Required, max 100 chars |
| date_of_birth | date | Required |
| gender | enum | MALE, FEMALE, OTHER, PREFER_NOT_TO_SAY |
| phone_number | string | Max 20 chars |
| email | email | Optional, validated format |
| blood_type | enum | A+, A-, B+, B-, AB+, AB-, O+, O-, UNKNOWN |
| national_id | string | Unique if provided |

### MedicalRecordShareToken

| Field | Type | Constraints |
|-------|------|-------------|
| token | string | Auto-generated, unique, 192-bit secure |
| access_level | enum | READ_ONLY, FULL, LIMITED |
| expires_in_hours | int | 1-720 (30 days max) |
| max_uses | int | 0-100 (0 = unlimited) |
| target_provider_id | int | Optional, must exist |

---

## Edge Cases and Error Handling

### Account Linking Edge Cases

```python
# Case 1: Token already used
{
    "token_used": True
}
# Result: 400 Bad Request
# Message: "This linking token has already been used."

# Case 2: Record already linked
{
    "linked_user": not None
}
# Result: 400 Bad Request
# Message: "This patient record is already linked to an account."

# Case 3: User already has linked record
user.patient_record exists
# Result: 400 Bad Request
# Message: "Your account is already linked to a patient record."

# Case 4: User is not a patient
user.role != PATIENT
# Result: 400 Bad Request
# Message: "User must have PATIENT role to link patient records."
```

### Share Token Edge Cases

```python
# Case 1: Token expired
timezone.now() > token.expires_at
# Result: 400 Bad Request
# Message: "This share token has expired."

# Case 2: Token revoked
token.is_revoked == True
# Result: 400 Bad Request
# Message: "This share token has been revoked."

# Case 3: Max uses exceeded
token.use_count >= token.max_uses and token.max_uses > 0
# Result: 400 Bad Request
# Message: "This share token has reached maximum uses."

# Case 4: Wrong target provider
token.target_provider != requesting_provider
# Result: 403 Forbidden
# Message: "This share token is for a different provider."
```

### Soft Delete Edge Cases

```python
# Soft deleted records are excluded by default
PatientRecord.objects.filter(is_active=True)  # Excludes soft deleted

# To include soft deleted (admin only):
PatientRecord.objects.filter(is_deleted=True)

# Restore soft deleted:
patient_record.restore()  # Sets is_deleted=False, is_active=True
```

---

## Automation Script Examples

### Example 1: Batch Patient Import

```python
import requests

API_BASE = "https://api.medilink.com"
headers = {"Authorization": f"Bearer {access_token}"}

patients_to_import = [
    {
        "first_name": "Ahmed",
        "last_name": "Benali",
        "date_of_birth": "1985-03-15",
        "gender": "MALE",
        "phone_number": "+213555123456",
    },
    # ... more patients
]

created_records = []
for patient_data in patients_to_import:
    response = requests.post(
        f"{API_BASE}/api/patients/",
        headers=headers,
        json=patient_data
    )
    if response.status_code == 201:
        record = response.json()
        created_records.append({
            "patient_unique_id": record["patient_unique_id"],
            "full_name": record["full_name"],
            "linking_token_masked": record["linking_token_masked"]
        })
    else:
        print(f"Failed to create: {patient_data['first_name']} - {response.json()}")

print(f"Created {len(created_records)} patient records")
```

### Example 2: Scheduled Token Cleanup

```python
from django.utils import timezone
from patients.models import MedicalRecordShareToken

def cleanup_expired_tokens():
    """Deactivate expired share tokens."""
    expired_tokens = MedicalRecordShareToken.objects.filter(
        is_active=True,
        expires_at__lt=timezone.now()
    )
    
    count = expired_tokens.update(is_active=False)
    print(f"Deactivated {count} expired tokens")
    return count

# Run as management command or celery task
```

### Example 3: Provider Access Audit

```python
import requests
from datetime import datetime, timedelta

def audit_provider_access(provider_id, days=30):
    """Audit which patients a provider accessed."""
    
    # Get all access logs for provider
    access_logs = ShareTokenAccessLog.objects.filter(
        accessed_by_provider_id=provider_id,
        accessed_at__gte=datetime.now() - timedelta(days=days)
    ).select_related('share_token__patient_record')
    
    audit_report = {
        "provider_id": provider_id,
        "period_days": days,
        "total_accesses": access_logs.count(),
        "patients_accessed": [],
    }
    
    patient_ids = set()
    for log in access_logs:
        patient = log.share_token.patient_record
        if patient.id not in patient_ids:
            patient_ids.add(patient.id)
            audit_report["patients_accessed"].append({
                "patient_unique_id": patient.patient_unique_id,
                "patient_name": patient.full_name,
                "first_access": log.accessed_at.isoformat(),
                "access_method": "share_token"
            })
    
    return audit_report
```

---

## Webhook Events (Future)

The following events could trigger webhooks for external integrations:

| Event | Payload |
|-------|---------|
| `patient.created` | patient_unique_id, created_by_provider |
| `patient.linked` | patient_unique_id, user_id |
| `patient.deleted` | patient_unique_id, deleted_by |
| `share_token.created` | token_id, patient_unique_id, expires_at |
| `share_token.used` | token_id, accessed_by_provider |
| `share_token.revoked` | token_id, patient_unique_id |
| `access.granted` | patient_unique_id, provider_id, access_level |

---

## Performance Considerations

### Database Indexes

The following indexes are defined for optimal query performance:

```python
# PatientRecord indexes
- patient_unique_id (unique)
- first_name, last_name
- phone_number
- email
- national_id
- linking_token (unique)
- linked_user
- is_active, is_deleted
- created_by_provider

# MedicalRecordShareToken indexes
- token (unique)
- patient_record, is_active
- expires_at, is_active

# ShareTokenAccessLog indexes
- accessed_at
```

### Query Optimization

```python
# Bad - N+1 queries
for record in PatientRecord.objects.all():
    print(record.created_by_provider.user.email)

# Good - eager loading
records = PatientRecord.objects.select_related(
    'created_by_provider__user',
    'linked_user'
).prefetch_related(
    'medical_records'
)
```

### Pagination

All list endpoints support pagination:

```
GET /api/patients/?page=1&page_size=20
```

Default page size: 20
Max page size: 100

---

## Security Considerations

### Token Security

1. **Linking Tokens**: 256-bit cryptographically secure, one-time use
2. **Share Tokens**: 192-bit cryptographically secure, configurable expiry/usage

### Access Control

1. All endpoints require authentication
2. Object-level permissions enforced
3. Provider approval status checked
4. Soft delete preserves audit trail

### Data Privacy

1. Linking tokens masked in responses (except explicit token endpoint)
2. Confidential medical records filtered for LIMITED access
3. Access logging for audit compliance

---

## Testing Checklist

### Unit Tests

- [ ] PatientRecord model validation
- [ ] Token generation uniqueness
- [ ] Soft delete/restore functionality
- [ ] ShareToken expiry/usage tracking
- [ ] Access level filtering

### Integration Tests

- [ ] Provider creates patient record
- [ ] Patient links account
- [ ] Share token creation and usage
- [ ] Provider access control
- [ ] Medical history retrieval

### Edge Case Tests

- [ ] Duplicate token handling
- [ ] Concurrent token usage
- [ ] Expired token rejection
- [ ] Wrong provider for targeted token
- [ ] Soft deleted record access

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Initial | Basic patient records, linking tokens |
| 2.0 | Current | Added patient_unique_id, share tokens, soft delete, access logging |

---

## Contact

For API issues or integration support:
- Technical: dev@medilink.dz
- Documentation: docs@medilink.dz
