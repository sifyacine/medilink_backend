from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # ===========================================
    # REST API Endpoints (Use these in apps/websites)
    # ===========================================
    
    # Get Firebase config for client-side (public endpoint)
    # GET /api/notifications/config/
    path('notifications/config/', views.get_firebase_config_api, name='get_firebase_config'),
    
    # Register device token (requires authentication)
    # POST /api/notifications/register/
    path('notifications/register/', views.register_device_api, name='register_device_api'),
    
    # Unregister single device token
    # POST /api/notifications/unregister/
    path('notifications/unregister/', views.unregister_device_api, name='unregister_device_api'),
    
    # Unregister all devices (full logout)
    # DELETE /api/notifications/unregister-all/
    path('notifications/unregister-all/', views.unregister_all_devices_api, name='unregister_all_devices'),
    
    # List registered devices
    # GET /api/notifications/devices/
    path('notifications/devices/', views.list_devices_api, name='list_devices'),
    
    # Send test notification to current user (verify backend sends FCM)
    # POST /api/notifications/test/
    path('notifications/test/', views.send_test_notification_api, name='send_test_notification'),
]