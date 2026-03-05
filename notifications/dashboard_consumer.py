"""
WebSocket consumer for provider dashboard real-time updates.

Connection URL:
    ws://<host>/ws/dashboard/?token=<auth-token>

Only users with a ``provider_profile`` may connect.

Outgoing message types sent TO the client:
    - dashboard_snapshot               : full dashboard data on connect / refresh
    - dashboard_appointments_updated   : appointment stats + today's list changed
    - dashboard_invoices_updated       : invoice summary changed
    - dashboard_patients_updated       : patient stats changed
    - dashboard_reviews_updated        : review stats changed
    - dashboard_activity               : single new activity item

Incoming message types FROM the client:
    - ping      : keep-alive → pong
    - refresh   : re-push full dashboard snapshot
"""
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncJsonWebsocketConsumer):
    """Real-time provider dashboard updates."""

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Only providers may connect
        self.provider = await self._get_provider()
        if self.provider is None:
            await self.close(code=4003)
            return

        self.dashboard_group = f"user_{self.user.id}_dashboard"
        await self.channel_layer.group_add(self.dashboard_group, self.channel_name)
        await self.accept()

        # Push initial full snapshot
        snapshot = await self._compute_full_dashboard()
        await self.send_json({
            "type": "dashboard_snapshot",
            "data": snapshot,
        })

        logger.debug(
            "DashboardConsumer connected: user=%s provider=%s",
            self.user.id,
            self.provider.id,
        )

    async def disconnect(self, close_code):
        if hasattr(self, "dashboard_group"):
            await self.channel_layer.group_discard(
                self.dashboard_group, self.channel_name
            )

    # ------------------------------------------------------------------
    # Incoming from client
    # ------------------------------------------------------------------

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type", "")

        if msg_type == "ping":
            await self.send_json({"type": "pong"})

        elif msg_type == "refresh":
            snapshot = await self._compute_full_dashboard()
            await self.send_json({
                "type": "dashboard_snapshot",
                "data": snapshot,
            })

    # ------------------------------------------------------------------
    # Handlers for messages pushed via channel layer
    # ------------------------------------------------------------------

    async def dashboard_snapshot(self, event):
        await self.send_json({
            "type": "dashboard_snapshot",
            "data": event.get("data", {}),
        })

    async def dashboard_appointments_updated(self, event):
        await self.send_json({
            "type": "dashboard_appointments_updated",
            "data": event.get("data", {}),
        })

    async def dashboard_invoices_updated(self, event):
        await self.send_json({
            "type": "dashboard_invoices_updated",
            "data": event.get("data", {}),
        })

    async def dashboard_patients_updated(self, event):
        await self.send_json({
            "type": "dashboard_patients_updated",
            "data": event.get("data", {}),
        })

    async def dashboard_reviews_updated(self, event):
        await self.send_json({
            "type": "dashboard_reviews_updated",
            "data": event.get("data", {}),
        })

    async def dashboard_activity(self, event):
        await self.send_json({
            "type": "dashboard_activity",
            "data": event.get("data", {}),
        })

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _get_provider(self):
        from providers.models.provider import Provider

        try:
            return Provider.objects.get(user=self.user)
        except Provider.DoesNotExist:
            return None

    @database_sync_to_async
    def _compute_full_dashboard(self):
        from notifications.dashboard_services import DashboardStatsService

        return DashboardStatsService.get_full_dashboard(self.provider)
