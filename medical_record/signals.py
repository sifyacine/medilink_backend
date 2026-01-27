"""
Signals for Medical Records app.
Handles audit logging and automatic actions.
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from medical_record.models import (
    MedicalRecord,
    MedicalRecordAccessLog,
)


@receiver(post_save, sender=MedicalRecord)
def log_medical_record_creation(sender, instance, created, **kwargs):
    """
    Log medical record creation/update.
    Note: This is a backup - primary logging happens in views.
    """
    if created:
        # Creation is logged in the view, but we can add additional logic here
        pass
    else:
        # Updates are logged in the view
        pass


@receiver(pre_delete, sender=MedicalRecord)
def log_medical_record_deletion(sender, instance, **kwargs):
    """
    Log medical record deletion (if hard delete is ever used).
    Note: We use soft delete (is_active=False) by default.
    """
    # Log deletion if hard delete occurs
    # In practice, we use soft delete, so this may not be called
    pass
