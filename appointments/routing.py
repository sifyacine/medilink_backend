"""
WebSocket URL routing for the appointments app.

Patterns:
    ws/appointments/                       — all appointment events for the user
    ws/appointments/<uuid:appointment_id>/ — single appointment events
"""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # All appointments for the authenticated user
    re_path(
        r"ws/appointments/$",
        consumers.AppointmentConsumer.as_asgi(),
    ),
    # Single appointment subscription
    re_path(
        r"ws/appointments/(?P<appointment_id>[0-9a-f-]+)/$",
        consumers.AppointmentConsumer.as_asgi(),
    ),
]
