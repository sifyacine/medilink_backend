"""
WebSocket consumer for real-time appointment updates.

Connection URLs:
    ws://<host>/ws/appointments/?token=<auth-token>
        → Authenticated user receives ALL their appointment updates
          (patient sees their own, provider sees their own).

    ws://<host>/ws/appointments/<appointment_id>/?token=<auth-token>
        → Subscribe to a SINGLE appointment (must be a participant).

Outgoing message types sent TO the client:
    - new_appointment           : a brand-new appointment was created
    - appointment_confirmed     : appointment confirmed by provider
    - appointment_rejected      : appointment rejected by provider
    - appointment_cancelled     : appointment cancelled (by either side)
    - appointment_rescheduled   : appointment rescheduled
    - appointment_completed     : appointment completed
    - appointment_no_show       : patient marked as no-show
    - appointment_reminder      : upcoming appointment reminder
    - appointment_updated       : generic status change catch-all

Incoming client messages:
    - ping                      : keep-alive → pong
"""
import json
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class AppointmentConsumer(AsyncJsonWebsocketConsumer):
    """
    Real-time appointment updates for patients and providers.

    Group naming convention:
        user_{user_id}_appointments    — all appointment events for a user
        appointment_{appt_id}          — events for a single appointment
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.groups_joined = []

        # Always join the personal appointments group
        self.user_group = f"user_{self.user.id}_appointments"
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        self.groups_joined.append(self.user_group)

        # Optionally subscribe to a specific appointment
        self.appointment_id = self.scope["url_route"]["kwargs"].get("appointment_id")
        if self.appointment_id:
            has_access = await self._user_is_participant(self.appointment_id)
            if has_access:
                appt_group = f"appointment_{self.appointment_id}"
                await self.channel_layer.group_add(appt_group, self.channel_name)
                self.groups_joined.append(appt_group)
            else:
                # Not a participant — close with 4003 Forbidden
                await self.close(code=4003)
                return

        await self.accept()
        logger.debug(
            "AppointmentConsumer connected: user=%s groups=%s",
            self.user.id,
            self.groups_joined,
        )

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
    # Each handler name maps to the ``type`` field in the channel message.
    # ------------------------------------------------------------------

    async def new_appointment(self, event):
        await self.send_json({
            "type": "new_appointment",
            "data": event.get("data", {}),
        })

    async def appointment_confirmed(self, event):
        await self.send_json({
            "type": "appointment_confirmed",
            "data": event.get("data", {}),
        })

    async def appointment_rejected(self, event):
        await self.send_json({
            "type": "appointment_rejected",
            "data": event.get("data", {}),
        })

    async def appointment_cancelled(self, event):
        await self.send_json({
            "type": "appointment_cancelled",
            "data": event.get("data", {}),
        })

    async def appointment_rescheduled(self, event):
        await self.send_json({
            "type": "appointment_rescheduled",
            "data": event.get("data", {}),
        })

    async def appointment_completed(self, event):
        await self.send_json({
            "type": "appointment_completed",
            "data": event.get("data", {}),
        })

    async def appointment_no_show(self, event):
        await self.send_json({
            "type": "appointment_no_show",
            "data": event.get("data", {}),
        })

    async def appointment_reminder(self, event):
        await self.send_json({
            "type": "appointment_reminder",
            "data": event.get("data", {}),
        })

    async def appointment_updated(self, event):
        """Generic catch-all for any appointment update."""
        await self.send_json({
            "type": "appointment_updated",
            "data": event.get("data", {}),
        })

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    @database_sync_to_async
    def _user_is_participant(self, appointment_id) -> bool:
        """Check if the current user is a patient or provider on the appointment."""
        from appointments.models import Appointment

        try:
            appt = Appointment.objects.select_related(
                "provider__user", "patient_user"
            ).get(pk=appointment_id)
        except Appointment.DoesNotExist:
            return False

        user_id = self.user.id
        if appt.patient_user_id == user_id:
            return True
        if appt.provider and appt.provider.user_id == user_id:
            return True
        if self.user.is_staff or self.user.is_superuser:
            return True
        return False
