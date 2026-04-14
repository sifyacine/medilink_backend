# Medical Records & Nurse Request Enhancements

## Overview
This document outlines enhancements to the medical records system and nurse request workflow to improve patient record visibility, better organize medical history, and strengthen the integration between nurse services and medical records.

## 1. Medical Folder Organization Enhancement

### 1.1 Update MedicalRecord Model
Add fields to support better organization:

```python
# In medical_record/models.py - MedicalRecord model
sequence_number = models.PositiveIntegerField(
    null=True,
    blank=True,
    db_index=True,
    help_text='Sequential number for this patient\'s records'
)
folder_name = models.CharField(
    max_length=200,
    blank=True,
    help_text='Custom folder/category name (e.g., "Heart Condition", "Surgery History")'
)
severity_level = models.CharField(
    max_length=20,
    choices=[
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
        ('INFO', 'Info'),
    ],
    default='MEDIUM',
    db_index=True,
    help_text='Clinical severity level'
)
timeline_order = models.IntegerField(
    default=0,
    db_index=True,
    help_text='For ordering records in timeline view'
)
```

### 1.2 Create a MedicalRecordFolder Model (Optional)
```python
class MedicalRecordFolder(models.Model):
    """
    Organize medical records into folders/categories.
    Patients can group related records together.
    """
    patient = models.ForeignKey(User, ...)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    color_tag = models.CharField(max_length=10, default='#3498DB')
    icon = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    records = models.ManyToManyField(MedicalRecord, related_name='folders')
    
    class Meta:
        unique_together = [['patient', 'name']]
        ordering = ['order', 'name']
```

### 1.3 Create Enhanced List Serializer with Grouping

```python
class MedicalRecordDetailedListSerializer(serializers.Serializer):
    """
    Enhanced list serializer that groups records by timeline/folder/diagnosis
    """
    timeline = serializers.SerializerMethodField()
    by_diagnosis = serializers.SerializerMethodField()
    by_folder = serializers.SerializerMethodField()
    
    def get_timeline(self, data):
        """Group and order chronologically"""
        # Sort by record_date descending
        return sorted(data, key=lambda x: x['record_date'], reverse=True)
    
    def get_by_diagnosis(self, data):
        """Group by diagnosis_code and record_type"""
        grouped = {}
        for record in data:
            key = record['diagnosis_code'] or record['record_type']
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        return grouped
    
    def get_by_folder(self, data):
        """Group by assigned folder"""
        # Implementation depends on folder model
        pass
```

## 2. Enhanced Patient Health Data Endpoint

### 2.1 Enrich `/api/medical-records/my-health-data/` Response

```python
# In views.py - enhance my_health_data action
@action(detail=False, methods=['get'], url_path='my-health-data')
def my_health_data(self, request):
    """Enhanced consolidated health data with organization"""
    # Existing code...
    
    return Response({
        'generated_at': timezone.now(),
        'patient': {...},
        'summary': {...},
        
        # NEW: Organized medical records
        'medical_records': {
            'total_count': len(records_data),
            'by_timeline': organized_by_timeline,
            'by_diagnosis': organized_by_diagnosis,
            'by_severity': {
                'critical': [...],
                'high': [...],
                'medium': [...],
                'low': [...],
            },
            'recent_30_days': records_from_last_30_days,
            'all_records': records_data,
        },
        
        # Numerical folder structure
        'folders': {
            '1_Recent': [...],
            '2_Medications': [...],
            '3_Vaccinations': [...],
            '4_Lab_Results': [...],
            '5_Procedures': [...],
        },
        
        'prescriptions': {...},
        'appointments': {...},
        'nurse_requests': {...},
        'provider_access': {...},
    })
```

## 3. Provider Access Revocation & Lifecycle

### 3.1 Add Access Expiration Support

Already exists! Use the `expires_at` field on ProviderAccess model:

```python
# In ProviderAccessSerializer
# Support setting expiration when granting access:
{
    "provider_id": "uuid",
    "access_type": "READ_ONLY",
    "expires_at": "2026-06-14T00:00:00Z"  # 2 months expiration
}
```

### 3.2 Add Cleanup Task (Celery or Management Command)

```python
# management/commands/cleanup_expired_access.py
from django.core.management.base import BaseCommand
from medical_record.models import ProviderAccess
from django.utils import timezone

class Command(BaseCommand):
    def handle(self, *args, **options):
        expired = ProviderAccess.objects.filter(
            is_active=True,
            expires_at__lt=timezone.now()
        )
        count = expired.update(is_active=False)
        self.stdout.write(f"Deactivated {count} expired access grants")
```

### 3.3 Add Access Audit Endpoint

```python
# In ProviderAccessViewSet
@action(detail=True, methods=['get'], url_path='audit-trail')
def audit_trail(self, request, pk=None):
    """Get audit trail of who accessed this grant"""
    access = self.get_object()
    logs = MedicalRecordAccessLog.objects.filter(
        medical_record__patient=access.patient,
        accessed_by=access.provider.user
    ).order_by('-accessed_at')
    
    return Response({
        'grant': ProviderAccessSerializer(access).data,
        'access_logs': MedicalRecordAccessLogSerializer(logs, many=True).data
    })
```

## 4. Nurse Request Medical Records Integration

### 4.1 Enhanced Nurse Request Creation
Link to existing medical records:

```python
# In CreateNurseServiceRequestSerializer
reason_for_visit = serializers.CharField(required=False)
related_medical_records = serializers.PrimaryKeyRelatedField(
    many=True,
    queryset=MedicalRecord.objects.all(),
    required=False
)

def validate_related_medical_records(self, value):
    """Ensure records belong to patient"""
    patient_user = self.context['request'].user
    for record in value:
        if record.patient != patient_user and \
           record.patient_record.linked_user != patient_user:
            raise ValidationError("Record doesn't belong to you")
    return value
```

### 4.2 Link Access to Service Request

```python
# In signals.py - enhance access granting
def _grant_medical_access_for_accepted_request(request_obj, nurse_provider):
    """Grant medical access with service request context"""
    # ... existing code ...
    
    # Set expiration based on service duration
    service_duration_days = request_obj.service.estimated_hours / 24
    expires_at = timezone.now() + timedelta(days=service_duration_days + 7)
    
    ProviderAccess.objects.update_or_create(
        provider=nurse_provider,
        patient=patient_user,
        defaults={
            'access_type': 'READ_ONLY',  # Restrict to read-only
            'is_active': True,
            'expires_at': expires_at,
            'reason': f'Medical access for nurse request #{request_obj.id} - {request_obj.service.title}',
        },
    )
```

### 4.3 Show Medical Context in Nurse Request

```python
# In NurseServiceRequestDetailSerializer
class NurseServiceRequestDetailSerializer(serializers.ModelSerializer):
    # ... existing fields ...
    
    patient_medical_summary = serializers.SerializerMethodField()
    critical_allergies = serializers.SerializerMethodField()
    active_medications = serializers.SerializerMethodField()
    recent_visits = serializers.SerializerMethodField()
    
    def get_patient_medical_summary(self, obj):
        """Show concise medical summary for nurses"""
        patient_user = obj.get_patient_user()
        if not patient_user:
            return None
        
        records = MedicalRecord.objects.filter(
            patient=patient_user,
            is_active=True
        ).order_by('-record_date')[:5]
        
        return [{
            'id': r.id,
            'title': r.title,
            'record_type': r.record_type,
            'record_date': r.record_date,
            'diagnosis_code': r.diagnosis_code,
        } for r in records]
    
    def get_critical_allergies(self, obj):
        """Show critical and severe allergies"""
        patient_user = obj.get_patient_user()
        if not patient_user:
            return []
        
        return list(MedicalRecord.objects.filter(
            patient=patient_user,
            record_type='ALLERGY',
            allergy__severity__in=['SEVERE', 'LIFE_THREATENING'],
            is_active=True
        ).values('allergy__allergen', 'allergy__severity', 'allergy__reaction'))
    
    def get_active_medications(self, obj):
        """Show current medications"""
        patient_user = obj.get_patient_user()
        if not patient_user:
            return []
        
        records = MedicalRecord.objects.filter(
            patient=patient_user,
            record_type='PRESCRIPTION',
            is_active=True
        ).prefetch_related('prescription')
        
        return [{
            'medication': r.prescription.medication_name,
            'dosage': r.prescription.dosage,
            'frequency': r.prescription.frequency,
        } for r in records if hasattr(r, 'prescription')]
    
    def get_recent_visits(self, obj):
        """Show recent medical visits"""
        patient_user = obj.get_patient_user()
        if not patient_user:
            return []
        
        from appointments.models import Appointment
        visits = Appointment.objects.filter(
            patient_user=patient_user,
            status='COMPLETED'
        ).order_by('-appointment_date')[:3]
        
        return [{
            'id': v.id,
            'date': v.appointment_date,
            'provider': v.provider.name if v.provider else None,
        } for v in visits]
```

## 5. Implementation Checklist

- [ ] Add migration for MedicalRecord fields
- [ ] Create MedicalRecordFolder model (optional)
- [ ] Add enhanced timeline/folder serializers
- [ ] Enhance `/my-health-data/` endpoint response
- [ ] Test ProviderAccess revocation workflow
- [ ] Create cleanup management command
- [ ] Add access audit trail endpoint
- [ ] Link medical records to nurse requests
- [ ] Update nurse request detail serializer with medical context
- [ ] Test end-to-end nurse workflow with medical data
- [ ] Add proper error handling and validation
- [ ] Create E2E test scenarios

## 6. API Endpoints Summary

### Patient Endpoints
- GET `/api/medical-records/my-records/` - List patient's records
- GET `/api/medical-records/my-records/?record_type=DIAGNOSIS` - Filter by type
- GET `/api/medical-records/my-health-data/` - Consolidated health data (enhanced)
- GET `/api/medical-records/my-records/export-summary/` - Export all records as PDF
- GET `/api/medical-records/{id}/export-pdf/` - Export single record
- GET `/api/medical-records/provider-access/my-providers/` - See who has access
- POST `/api/medical-records/provider-access/revoke/` - Revoke provider access
- POST `/api/medical-records/provider-access/renew/` - Renew access

### Nurse Request Endpoints (with medical context)
- GET `/api/nurse-requests/patient/my-requests/` - Patient's requests with medical summary
- POST `/api/nurse-requests/patient/my-requests/` - Create request (with optional medical context)
- POST `/api/nurse-requests/nurse/available-requests/{id}/accept/` - Accept with medical visibility

## 7. Security Considerations

✅ Already implemented:
- RBAC permission checks in place
- Audit logging of all access
- Expiration support for temporary access

🔒 Additional measures:
- Restrict READ_ONLY access for temporary nurse assignments
- Log all revocation events
- Implement rate limiting on access requests
- Add compliance audit reports

## 8. Testing Scenarios

### Scenario 1: Patient Views All Health Data
```
1. Patient logs in
2. GET /api/medical-records/my-health-data/
3. Verify response includes organized records by timeline, diagnosis, severity
4. Verify 30-day recent records are included
5. Verify sensitive data (allergies, medications) is visible
```

### Scenario 2: Provider Access Revocation
```
1. Patient grants READ_ONLY access to nurse
2. Nurse accepts request - access auto-granted with expiration
3. Patient views provider access list
4. Patient revokes access (POST /revoke/)
5. Verify nurse can't access records anymore
6. Verify access log shows revocation
```

### Scenario 3: Nurse Request with Medical Context
```
1. Patient creates nurse request
2. System auto-links to patient's medical records
3. Nurse accepts request
4. Nurse can see medical summary (allergies, medications, recent visits)
5. Service complete → Access automatically expires
6. Verify nurse can't access records post-expiration
```

### Scenario 4: Uber-Like Workflow
```
1. Patient requests nurse service (like requesting Uber)
2. Multiple nurses respond with offers
3. Patient sees nurse profiles + medical qualifications
4. Patient accepts nurse offer
5. Nurse gets temporary medical record access
6. Service starts and completes
7. Access expires, both parties can leave feedback
```
