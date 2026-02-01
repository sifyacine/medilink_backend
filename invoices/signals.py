"""
Invoice signals for automatic invoice creation.

Integrates with the appointment and nurse request workflows
to automatically create invoices when appropriate.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Invoice, InvoiceActivity, InvoiceStatus


@receiver(post_save, sender='appointments.Appointment')
def handle_appointment_completion(sender, instance, created, **kwargs):
    """
    Optionally create invoice when appointment is completed.
    
    This is disabled by default. Enable with:
    MEDILINK_AUTO_INVOICE_APPOINTMENTS = True
    """
    if created:
        return
    
    # Check if auto-invoice is enabled
    auto_invoice = getattr(settings, 'MEDILINK_AUTO_INVOICE_APPOINTMENTS', False)
    if not auto_invoice:
        return
    
    from appointments.models import AppointmentStatus
    
    # Only trigger on completion
    if instance.status != AppointmentStatus.COMPLETED:
        return
    
    # Check if invoice already exists
    if Invoice.objects.filter(appointment=instance).exists():
        return
    
    # Import here to avoid circular imports
    from .services import InvoiceService, InvoiceConfig
    
    try:
        config = InvoiceConfig(
            auto_send=getattr(settings, 'MEDILINK_AUTO_SEND_INVOICES', False),
        )
        InvoiceService.create_from_appointment(
            appointment=instance,
            config=config,
            include_services=True,
        )
    except Exception as e:
        # Log error but don't fail the appointment completion
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to auto-create invoice for appointment {instance.id}: {e}")


@receiver(post_save, sender='nurse_requests.NurseServiceRequest')
def handle_nurse_request_completion(sender, instance, created, **kwargs):
    """
    Optionally create invoice when nurse request is completed.
    
    This is disabled by default. Enable with:
    MEDILINK_AUTO_INVOICE_NURSE_REQUESTS = True
    """
    if created:
        return
    
    # Check if auto-invoice is enabled
    auto_invoice = getattr(settings, 'MEDILINK_AUTO_INVOICE_NURSE_REQUESTS', False)
    if not auto_invoice:
        return
    
    try:
        from nurse_requests.models import RequestStatus
        
        # Only trigger on completion
        if instance.status != RequestStatus.COMPLETED:
            return
    except ImportError:
        return
    
    # Check if invoice already exists
    if Invoice.objects.filter(nurse_request=instance).exists():
        return
    
    from .services import InvoiceService, InvoiceConfig
    
    try:
        config = InvoiceConfig(
            auto_send=getattr(settings, 'MEDILINK_AUTO_SEND_INVOICES', False),
        )
        InvoiceService.create_from_nurse_request(
            nurse_request=instance,
            config=config,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to auto-create invoice for nurse request {instance.id}: {e}")


@receiver(post_save, sender=Invoice)
def log_invoice_status_change(sender, instance, created, **kwargs):
    """
    Log status changes for invoices.
    """
    if created:
        return
    
    # Get the update_fields if available
    update_fields = kwargs.get('update_fields')
    
    # Only log if status was explicitly updated
    if update_fields and 'status' not in update_fields:
        return
    
    # This is handled by the views/services, so we don't duplicate
    # unless it's a system change (like overdue check)
