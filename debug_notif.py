
import os
import sys
import django
import logging

# Add current directory to path
sys.path.append(os.getcwd())

# Setup Django environment BEFORE imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from appointments.models import Appointment
from appointments.notifications import AppointmentNotifier
from notifications.models import DeviceToken

# Configure logging to verify output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

def run_debug():
    print("--- STARTING NOTIFICATION DEBUG ---")
    
    # 1. Fetch the doctor user (likely the one testing)
    # We'll take the first user with a provider profile
    try:
        doctor_user = User.objects.filter(provider_profile__isnull=False).first()
        if not doctor_user:
            print("❌ No doctor user found in database.")
            return
        print(f"👨‍⚕️ Doctor User: {doctor_user.email} (ID: {doctor_user.id})")
        
        # Check tokens for doctor
        tokens = DeviceToken.objects.filter(user=doctor_user, is_active=True)
        print(f"📱 Doctor Tokens: {tokens.count()}")
        for t in tokens:
            print(f"   - {t.token[:20]}... ({t.device_type})")

    except Exception as e:
        print(f"❌ Error fetching doctor: {e}")
        return

    # 2. Simulate Patient User
    # Create or get a dummy patient
    patient_email = "debug_patient@example.com"
    patient_user, created = User.objects.get_or_create(
        email=patient_email, 
        defaults={'role': 'PATIENT'}
    )
    if created:
        patient_user.set_password('password123')
        patient_user.save()
        print(f"👤 Created debug patient: {patient_email}")
    else:
        print(f"👤 Using debug patient: {patient_email} (ID: {patient_user.id})")

    # 3. Simulate Appointment Creation (WITHOUT saving to DB to avoid clutter/signals first)
    # We want to call notify_new_appointment manually to test LOGIC
    
    # We need a real appointment for the function to work because it accesses fields
    # Let's try to get the last appointment created by the doctor
    last_appt = Appointment.objects.filter(provider__user=doctor_user).last()
    
    if not last_appt:
        print("⚠️ No existing appointment found for this doctor. Cannot test with real object.")
        # Create a dummy one?
        return

    print(f"\n🧪 Testing Notification Logic with Appointment ID: {last_appt.id}")
    print(f"   - Patient User in Appt: {last_appt.patient_user}")
    print(f"   - Provider in Appt: {last_appt.provider.user}")
    
    # Scenario A: Doctor created it (Should NOT notify doctor)
    print("\n[Scenario A] Doctor creates appointment -> Should SKIP Doctor notification")
    AppointmentNotifier.notify_new_appointment(last_appt, created_by=doctor_user)
    
    # Scenario B: Patient created it (Should NOTIFY doctor)
    print("\n[Scenario B] Patient creates appointment -> Should NOTIFY Doctor")
    # Temporarily ensure appointment has a patient user so it looks real
    original_patient = last_appt.patient_user
    last_appt.patient_user = patient_user 
    # We don't save, just modify instance for the method call
    
    try:
        AppointmentNotifier.notify_new_appointment(last_appt, created_by=patient_user)
        print("✅ method executed (check logs/firebase for delivery)")
    except Exception as e:
        print(f"❌ Exception in notify_new_appointment: {e}")

    print("\n--- END DEBUG ---")

if __name__ == "__main__":
    run_debug()
