"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.

Supports:
- HTTP requests (Django)
- WebSocket connections with Token authentication for:
  - Notifications (per-user real-time stream)
  - Appointments (real-time status updates)
  - Nurse Requests (on-demand nursing flow)

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.development')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

# Import Channels components after Django is initialized
from channels.routing import ProtocolTypeRouter, URLRouter

# Import WebSocket routing from each app
from nurse_requests.routing import websocket_urlpatterns as nurse_request_patterns
from notifications.routing import websocket_urlpatterns as notification_patterns
from appointments.routing import websocket_urlpatterns as appointment_patterns
from notifications.middleware import WebSocketAuthMiddlewareStack

# Combine all WebSocket URL patterns
all_websocket_patterns = (
    nurse_request_patterns
    + notification_patterns
    + appointment_patterns
)

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": WebSocketAuthMiddlewareStack(
        URLRouter(
            all_websocket_patterns
        )
    ),
})
