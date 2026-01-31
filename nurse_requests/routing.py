from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Patient WebSocket - subscribe to specific request updates
    re_path(
        r'ws/nurse-requests/(?P<request_id>\d+)/$',
        consumers.NurseRequestConsumer.as_asgi()
    ),
    
    # Nurse WebSocket - subscribe to available requests in their area
    re_path(
        r'ws/nurse-requests/available/$',
        consumers.NurseRequestConsumer.as_asgi()
    ),
]
