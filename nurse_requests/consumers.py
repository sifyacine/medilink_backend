import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from common.enums import ProviderType

logger = logging.getLogger(__name__)
User = get_user_model()


class NurseRequestConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time nurse request updates.

    URL patterns:
    - ws/nurse-requests/<request_id>/   → patient subscribes to a specific request
    - ws/nurse-requests/available/      → nurse subscribes to their city + personal stream

    Channel groups joined per connection:
    - user_<id>_nurse_requests          personal stream (always joined)
    - request_<id>_updates              specific-request updates (when request_id in URL)
    - city_<city>_requests              city broadcast for nurses (when user is a nurse with
                                        a known city address)

    Authentication:
    - Token passed via Authorization header (standard DRF token middleware handles this).
    - Unauthenticated connections are closed immediately with code 4001.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.groups_joined: list[str] = []

        # Personal stream — every authenticated user gets this
        personal_group = f"user_{self.user.id}_nurse_requests"
        await self.channel_layer.group_add(personal_group, self.channel_name)
        self.groups_joined.append(personal_group)

        # Request-specific group (patient subscribing to one request's updates)
        request_id = self.scope["url_route"]["kwargs"].get("request_id")
        if request_id:
            request_group = f"request_{request_id}_updates"
            await self.channel_layer.group_add(request_group, self.channel_name)
            self.groups_joined.append(request_group)

        # City channel for nurses (so they receive new-request broadcasts)
        if await self._is_nurse():
            city = await self._get_nurse_city()
            if city:
                city_group = f"city_{city.lower().replace(' ', '_')}_requests"
                await self.channel_layer.group_add(city_group, self.channel_name)
                self.groups_joined.append(city_group)

        await self.accept()
        logger.debug(
            "WS connected: user=%s groups=%s",
            self.user.id,
            self.groups_joined,
        )

    async def disconnect(self, close_code):
        for group in getattr(self, "groups_joined", []):
            try:
                await self.channel_layer.group_discard(group, self.channel_name)
            except Exception:
                pass
        logger.debug("WS disconnected: user=%s code=%s", getattr(self, "user", "?"), close_code)

    # ------------------------------------------------------------------
    # Incoming from client
    # ------------------------------------------------------------------

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type", "")
        if msg_type == "ping":
            await self.send_json({"type": "pong"})

    # ------------------------------------------------------------------
    # Handlers — messages pushed FROM backend via channel layer
    #
    # Django Channels dispatches channel-layer messages to methods whose
    # name equals the message "type" with dots replaced by underscores.
    # Every handler below receives {"type": "...", "data": {...}} and
    # forwards it to the connected client.
    # ------------------------------------------------------------------

    async def nurse_request_new(self, event):
        """New request broadcast (city-wide and/or personal)."""
        await self.send_json({"type": "nurse_request_new", "data": event.get("data", {})})

    async def nurse_request_offer(self, event):
        """A nurse submitted an offer or accepted at patient price."""
        await self.send_json({"type": "nurse_request_offer", "data": event.get("data", {})})

    async def nurse_request_accepted(self, event):
        """Patient accepted a nurse offer — sent to both parties."""
        await self.send_json({"type": "nurse_request_accepted", "data": event.get("data", {})})

    async def nurse_request_in_progress(self, event):
        """Service started — sent to patient and nurse."""
        await self.send_json({"type": "nurse_request_in_progress", "data": event.get("data", {})})

    async def nurse_request_completed(self, event):
        """Service completed — sent to patient."""
        await self.send_json({"type": "nurse_request_completed", "data": event.get("data", {})})

    async def nurse_request_cancelled(self, event):
        """Request cancelled — sent to the affected party."""
        await self.send_json({"type": "nurse_request_cancelled", "data": event.get("data", {})})

    async def nurse_offer_declined(self, event):
        """Patient declined the nurse's offer — sent to nurse."""
        await self.send_json({"type": "nurse_offer_declined", "data": event.get("data", {})})

    async def nurse_review_received(self, event):
        """Nurse received a review from a patient."""
        await self.send_json({"type": "nurse_review_received", "data": event.get("data", {})})

    async def nurse_rating_updated(self, event):
        """Nurse's aggregate rating changed after a new review."""
        await self.send_json({"type": "nurse_rating_updated", "data": event.get("data", {})})

    async def nurse_request_updated(self, event):
        """Generic catch-all update — sent when no more specific type applies."""
        await self.send_json({"type": "nurse_request_updated", "data": event.get("data", {})})

    # ------------------------------------------------------------------
    # Database helpers (run in thread pool via database_sync_to_async)
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _is_nurse(self) -> bool:
        """Return True if the connected user is a nurse provider."""
        try:
            return (
                hasattr(self.user, "provider_profile")
                and self.user.provider_profile.provider_type == ProviderType.NURSE
            )
        except Exception:
            return False

    @database_sync_to_async
    def _get_nurse_city(self) -> str | None:
        """
        Return the city used for the nurse's city broadcast group.

        Uses the same address lookup as the available-requests view:
        address is linked to the *user* (not the provider) with
        address_type in ['WORK', 'CLINIC'] and is_primary=True.
        Falls back to any user address if the primary work/clinic
        address is not found.
        """
        try:
            from address.models import Address
            from django.contrib.contenttypes.models import ContentType

            user_ct = ContentType.objects.get_for_model(self.user)

            # Prefer primary WORK/CLINIC address (matches the view's filter)
            addr = (
                Address.objects.filter(
                    content_type=user_ct,
                    object_id=self.user.pk,
                    address_type__in=["WORK", "CLINIC"],
                    is_primary=True,
                )
                .first()
            )

            # Fallback: any primary address for this user
            if not addr:
                addr = (
                    Address.objects.filter(
                        content_type=user_ct,
                        object_id=self.user.pk,
                        is_primary=True,
                    )
                    .first()
                )

            # Last resort: any address at all
            if not addr:
                addr = (
                    Address.objects.filter(
                        content_type=user_ct,
                        object_id=self.user.pk,
                    )
                    .order_by("-updated_at")
                    .first()
                )

            return addr.city if addr and addr.city else None
        except Exception:
            return None
