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
    
    # Send test notification to a specific provider (for debugging cross-user flows)
    # POST /api/notifications/test-provider/ (Legacy, maps to test-user)
    path('notifications/test-provider/', views.send_test_to_user_api, name='send_test_to_provider'),
    
    # Send test notification to any specific user
    # POST /api/notifications/test-user/
    path('notifications/test-user/', views.send_test_to_user_api, name='send_test_to_user'),
    
    # -------------------------------------------
    # History & Management
    # -------------------------------------------
    
    # List notifications
    # GET /api/notifications/
    path('notifications/', views.list_notifications_api, name='list_notifications'),
    
    # Mark as read
    # PATCH /api/notifications/<id>/read/
    path('notifications/<uuid:notification_id>/read/', views.mark_notification_read_api, name='mark_notification_read'),

    # Mark all read
    # POST /api/notifications/mark-all-read/
    path('notifications/mark-all-read/', views.mark_all_notifications_read_api, name='mark_all_read'),

    # Delete single notification
    # DELETE /api/notifications/<id>/
    path('notifications/<uuid:notification_id>/', views.delete_notification_api, name='delete_notification'),
    
    # Clear all notifications
    # DELETE /api/notifications/clear-all/
    path('notifications/clear-all/', views.clear_all_notifications_api, name='clear_all_notifications'),

    # Activity feed (provider dashboard)
    # GET /api/notifications/activity-feed/
    path('notifications/activity-feed/', views.activity_feed_api, name='activity_feed'),
]