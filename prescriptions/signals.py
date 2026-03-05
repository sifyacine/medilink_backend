"""
Signals for the prescriptions app.

Automatically creates a medical record when a prescription is issued.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Prescription, PrescriptionStatus


@receiver(pre_save, sender=Prescription)
def track_status_change(sender, instance, **kwargs):
    """Track status changes for post_save processing."""
    if instance.pk:
        try:
            old_instance = Prescription.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Prescription.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Prescription)
def handle_prescription_issued(sender, instance, created, **kwargs):
    """
    When a prescription is issued, create a corresponding medical record.
    
    This ensures prescriptions are part of the patient's medical history.
    """
    previous_status = getattr(instance, '_previous_status', None)
    
    # Only proceed if status changed to ISSUED
    if instance.status == PrescriptionStatus.ISSUED and previous_status != PrescriptionStatus.ISSUED:
        _create_medical_record_for_prescription(instance)


def _create_medical_record_for_prescription(prescription):
    """
    Create a medical record entry for an issued prescription.
    
    Args:
        prescription: The Prescription instance that was issued
    """
    from medical_record.models import MedicalRecord
    
    # Build medication summary for description
    medications = prescription.items.all()
    medication_list = []
    for item in medications:
        med_str = f"- {item.medication_name}"
        if item.dosage:
            med_str += f" ({item.dosage})"
        if item.frequency:
            med_str += f" - {item.get_frequency_display()}"
        if item.duration_text:
            med_str += f" for {item.duration_text}"
        elif item.duration_days:
            med_str += f" for {item.duration_days} days"
        medication_list.append(med_str)
    
    medications_text = "\n".join(medication_list) if medication_list else "No medications listed"
    
    # Build description
    description_parts = [f"Prescription Reference: {prescription.reference_number}"]
    
    if prescription.diagnosis:
        description_parts.append(f"\nDiagnosis: {prescription.diagnosis}")
    
    description_parts.append(f"\nMedications:\n{medications_text}")
    
    if prescription.instructions:
        description_parts.append(f"\nInstructions: {prescription.instructions}")
    
    if prescription.notes:
        description_parts.append(f"\nNotes: {prescription.notes}")
    
    if prescription.valid_until:
        description_parts.append(f"\nValid until: {prescription.valid_until}")
    
    description = "".join(description_parts)
    
    # Get the doctor's user for created_by
    created_by = prescription.doctor.user if prescription.doctor else None
    
    # Create medical record
    try:
        medical_record = MedicalRecord.objects.create(
            # Patient identification
            patient=prescription.patient,
            patient_record=prescription.patient_record,
            
            # Record type
            record_type='PRESCRIPTION',
            
            # Content
            description=description,
            
            # Link to appointment if available
            appointment=prescription.appointment,
            
            # Provider information
            provider=prescription.doctor.provider if prescription.doctor and hasattr(prescription.doctor, 'provider') else None,
            created_by=created_by,
            
            # Record date
            record_date=prescription.issued_at or timezone.now(),
        )
        
        # Copy PDF file reference if available
        if prescription.pdf_file:
            # Note: In production, you might want to copy the file or create a reference
            pass
        
        return medical_record
        
    except Exception as e:
        # Log error but don't break the prescription flow
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create medical record for prescription {prescription.id}: {e}")
        return None


@receiver(post_save, sender=Prescription)
def notify_patient_of_prescription(sender, instance, created, **kwargs):
    """
    Send notification to patient when a prescription is issued.
    """
    previous_status = getattr(instance, '_previous_status', None)
    
    # Only notify when status changes to ISSUED
    if instance.status == PrescriptionStatus.ISSUED and previous_status != PrescriptionStatus.ISSUED:
        _send_prescription_notification(instance)


def _send_prescription_notification(prescription):
    """
    Send notification to patient about new prescription.
    
    Args:
        prescription: The Prescription instance that was issued
    """
    try:
        from notifications.services import NotificationService
        
        # Get patient user
        recipient = prescription.patient
        if not recipient:
            # Can't send notification to patient without account
            return
        
        # Build notification message
        doctor_name = prescription.doctor.user.get_full_name() if prescription.doctor else None
        if not doctor_name or not doctor_name.strip():
            doctor_name = "Your doctor"
        
        NotificationService.create_notification(
            recipient=recipient,
            notification_type='PRESCRIPTION_ISSUED',
            title='New Prescription Issued',
            message=f'{doctor_name} has issued a new prescription for you. Reference: {prescription.reference_number}',
            related_object=prescription,
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send prescription notification for {prescription.id}: {e}")
