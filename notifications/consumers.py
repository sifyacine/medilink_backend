"""
WebSocket consumer for general user notifications.

Every authenticated user can open a single WebSocket connection to receive
real-time notifications (appointments, prescriptions, invoices, etc.).

Connection URL:
    ws://<host>/ws/notifications/?token=<auth-token>

Outgoing message types sent TO the client:
    - notification         : new in-app notification
    - appointment_update   : any appointment status change
    - unread_count         : updated unread notification count

Incoming message types FROM the client:
    - ping                 : keep-alive (server replies with pong)
    - mark_read            : mark a notification as read  { id: <uuid> }
    - mark_all_read        : mark all notifications read
"""
import json
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    Per-user notification channel.

    Each user is added to a personal group ``user_<id>_notifications``
    so that any server-side code can push messages through the
    Channel Layer.
    """

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.user_group = f"user_{self.user.id}_notifications"

        # Join personal notification group
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        await self.accept()

        # Send initial unread count on connect
        unread = await self._get_unread_count()
        await self.send_json({
            "type": "unread_count",
            "count": unread,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(
                self.user_group, self.channel_name
            )

    # ------------------------------------------------------------------
    # Incoming messages from client
    # ------------------------------------------------------------------

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type", "")

        if msg_type == "ping":
            await self.send_json({"type": "pong"})

        elif msg_type == "mark_read":
            notif_id = content.get("id")
            if notif_id:
                await self._mark_notification_read(notif_id)
                unread = await self._get_unread_count()
                await self.send_json({"type": "unread_count", "count": unread})

        elif msg_type == "mark_all_read":
            await self._mark_all_read()
            await self.send_json({"type": "unread_count", "count": 0})

    # ------------------------------------------------------------------
    # Handlers for messages pushed FROM the server via channel layer
    # ------------------------------------------------------------------

    async def notification(self, event):
        """New notification pushed from backend."""
        await self.send_json({
            "type": "notification",
            "data": event.get("data", {}),
        })

    async def appointment_update(self, event):
        """Appointment status change pushed from backend."""
        await self.send_json({
            "type": "appointment_update",
            "data": event.get("data", {}),
        })

    async def unread_count(self, event):
        """Unread count update."""
        await self.send_json({
            "type": "unread_count",
            "count": event.get("count", 0),
        })

    # Appointment event handlers — forward all to the client as-is
    # so the browser notification bell and toast system receive them.
    async def new_appointment(self, event):
        await self.send_json({"type": "new_appointment", "data": event.get("data", {})})

    async def appointment_confirmed(self, event):
        await self.send_json({"type": "appointment_confirmed", "data": event.get("data", {})})

    async def appointment_rejected(self, event):
        await self.send_json({"type": "appointment_rejected", "data": event.get("data", {})})

    async def appointment_cancelled(self, event):
        await self.send_json({"type": "appointment_cancelled", "data": event.get("data", {})})

    async def appointment_rescheduled(self, event):
        await self.send_json({"type": "appointment_rescheduled", "data": event.get("data", {})})

    async def appointment_completed(self, event):
        await self.send_json({"type": "appointment_completed", "data": event.get("data", {})})

    async def appointment_no_show(self, event):
        await self.send_json({"type": "appointment_no_show", "data": event.get("data", {})})

    async def appointment_reminder(self, event):
        await self.send_json({"type": "appointment_reminder", "data": event.get("data", {})})

    async def appointment_deleted(self, event):
        await self.send_json({"type": "appointment_deleted", "data": event.get("data", {})})

    async def appointment_updated(self, event):
        await self.send_json({"type": "appointment_updated", "data": event.get("data", {})})

    # Nurse request event handlers — forward to client
    async def nurse_request_new(self, event):
        await self.send_json({"type": "nurse_request_new", "data": event.get("data", {})})

    async def nurse_request_offer(self, event):
        await self.send_json({"type": "nurse_request_offer", "data": event.get("data", {})})

    async def nurse_request_accepted(self, event):
        await self.send_json({"type": "nurse_request_accepted", "data": event.get("data", {})})

    async def nurse_request_in_progress(self, event):
        await self.send_json({"type": "nurse_request_in_progress", "data": event.get("data", {})})

    async def nurse_request_completed(self, event):
        await self.send_json({"type": "nurse_request_completed", "data": event.get("data", {})})

    async def nurse_request_cancelled(self, event):
        await self.send_json({"type": "nurse_request_cancelled", "data": event.get("data", {})})

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _get_unread_count(self) -> int:
        from notifications.models import Notification
        return Notification.objects.filter(
            recipient=self.user, is_read=False
        ).count()

    @database_sync_to_async
    def _mark_notification_read(self, notif_id: str):
        from notifications.models import Notification
        Notification.objects.filter(
            id=notif_id, recipient=self.user
        ).update(is_read=True)

    @database_sync_to_async
    def _mark_all_read(self):
        from notifications.models import Notification
        Notification.objects.filter(
            recipient=self.user, is_read=False
        ).update(is_read=True)
