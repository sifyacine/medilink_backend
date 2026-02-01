"""
WebSocket URL routing for notifications.
"""
from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    # General notifications WebSocket
    # Connect to receive all notifications for the authenticated user
    re_path(
        r'ws/notifications/$',
        consumers.NotificationConsumer.as_asgi()
    ),
    
    # Appointment-specific WebSocket
    # Connect to receive real-time appointment updates (for doctors dashboard)
    re_path(
        r'ws/appointments/$',
        consumers.AppointmentConsumer.as_asgi()
    ),
]
