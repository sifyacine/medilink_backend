import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class NurseRequestConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time nurse request updates.

    Groups a client is joined to (depending on role):
    - ``user_<id>_nurse_requests``  — personal stream (both roles)
    - ``request_<id>_updates``      — specific request (patient & accepted nurse)
    - ``city_<city>_requests``      — city-wide broadcast for nurses
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.groups_joined: list[str] = []

        # Personal nurse-request stream for every authenticated user
        personal_group = f"user_{self.user.id}_nurse_requests"
        await self.channel_layer.group_add(personal_group, self.channel_name)
        self.groups_joined.append(personal_group)

        # If the URL contains a request_id, also join that request group
        request_id = self.scope["url_route"]["kwargs"].get("request_id")
        if request_id:
            request_group = f"request_{request_id}_updates"
            await self.channel_layer.group_add(request_group, self.channel_name)
            self.groups_joined.append(request_group)

        # If user is a nurse, also join their city channel
        if await self.is_nurse():
            city = await self.get_nurse_city()
            if city:
                city_group = f"city_{city.lower().replace(' ', '_')}_requests"
                await self.channel_layer.group_add(city_group, self.channel_name)
                self.groups_joined.append(city_group)

        await self.accept()

    async def disconnect(self, close_code):
        for group in getattr(self, "groups_joined", []):
            await self.channel_layer.group_discard(group, self.channel_name)

    # ------------------------------------------------------------------
    # Incoming from client
    # ------------------------------------------------------------------

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type", "")
        if msg_type == "ping":
            await self.send_json({"type": "pong"})

    # ------------------------------------------------------------------
    # Handlers for messages pushed FROM backend via channel layer
    # ------------------------------------------------------------------

    async def nurse_request_new(self, event):
        """New request broadcast (city-wide or personal)."""
        await self.send_json({"type": "nurse_request_new", "data": event.get("data", {})})

    async def nurse_request_offer(self, event):
        """A nurse submitted an offer."""
        await self.send_json({"type": "nurse_request_offer", "data": event.get("data", {})})

    async def nurse_request_accepted(self, event):
        """Offer was accepted."""
        await self.send_json({"type": "nurse_request_accepted", "data": event.get("data", {})})

    async def nurse_request_in_progress(self, event):
        """Service started."""
        await self.send_json({"type": "nurse_request_in_progress", "data": event.get("data", {})})

    async def nurse_request_completed(self, event):
        """Service completed."""
        await self.send_json({"type": "nurse_request_completed", "data": event.get("data", {})})

    async def nurse_request_cancelled(self, event):
        """Request cancelled."""
        await self.send_json({"type": "nurse_request_cancelled", "data": event.get("data", {})})

    # Generic catch-all
    async def nurse_request_updated(self, event):
        await self.send_json({"type": "nurse_request_updated", "data": event.get("data", {})})

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def is_nurse(self):
        try:
            return (
                hasattr(self.user, "provider_profile")
                and self.user.provider_profile.provider_type == "NURSE"
            )
        except Exception:
            return False

    @database_sync_to_async
    def get_nurse_city(self):
        """Return the city from the nurse's primary address (or None)."""
        try:
            from address.models import Address
            from django.contrib.contenttypes.models import ContentType

            provider = self.user.provider_profile
            ct = ContentType.objects.get_for_model(provider)
            addr = (
                Address.objects.filter(content_type=ct, object_id=provider.pk)
                .order_by("-is_primary")
                .first()
            )
            return addr.city if addr else None
        except Exception:
            return None
