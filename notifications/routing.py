"""
WebSocket URL routing for the notifications app.

Patterns:
    ws/notifications/  — per-user notification stream
"""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
]
