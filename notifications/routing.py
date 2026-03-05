"""
WebSocket URL routing for the notifications app.

Patterns:
    ws/notifications/  — per-user notification stream
"""
from django.urls import re_path

from . import consumers
from .dashboard_consumer import DashboardConsumer

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    re_path(r"ws/dashboard/$", DashboardConsumer.as_asgi()),
]
