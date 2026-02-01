"""
WebSocket consumers for real-time notifications.

Provides:
- NotificationConsumer: Real-time notification delivery
- AppointmentConsumer: Real-time appointment updates for all providers (doctors, nurses, clinics, etc.)
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notification delivery.
    
    Channels/Groups:
    - user_{user_id}_notifications: Personal notifications for a user
    - role_{role}_notifications: Broadcast to all users with a role
    - all_notifications: System-wide broadcasts
    
    Messages sent to client:
    - notification: New notification received
    - notification_read: Notification marked as read
    - notification_count: Updated unread count
    - ping/pong: Connection keep-alive
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthenticated WebSocket connection attempt")
            await self.close(code=4001)
            return
        
        # Create user-specific notification group
        self.user_group = f'user_{self.user.id}_notifications'
        
        # Add to user's personal notification group
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        # Add to role-based group
        if hasattr(self.user, 'role') and self.user.role:
            self.role_group = f'role_{self.user.role}_notifications'
            await self.channel_layer.group_add(
                self.role_group,
                self.channel_name
            )
        
        # Accept the connection
        await self.accept()
        
        # Send initial unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'unread_count': unread_count,
        }))
        
        logger.info(f"WebSocket connected for user {self.user.id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave all groups
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        
        if hasattr(self, 'role_group'):
            await self.channel_layer.group_discard(
                self.role_group,
                self.channel_name
            )
        
        logger.info(f"WebSocket disconnected for user {getattr(self.user, 'id', 'unknown')}")
    
    async def receive(self, text_data):
        """Handle incoming messages from the client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                # Keep-alive ping
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'mark_read':
                # Mark notification(s) as read
                notification_ids = data.get('notification_ids', [])
                await self.mark_notifications_read(notification_ids)
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notification_count',
                    'unread_count': unread_count,
                }))
            
            elif message_type == 'mark_all_read':
                # Mark all notifications as read
                await self.mark_all_notifications_read()
                await self.send(text_data=json.dumps({
                    'type': 'notification_count',
                    'unread_count': 0,
                }))
            
            elif message_type == 'get_count':
                # Get current unread count
                unread_count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'notification_count',
                    'unread_count': unread_count,
                }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Server error'
            }))
    
    # Event handlers - called by channel layer
    async def notification(self, event):
        """Send a new notification to the client."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification'],
        }))
    
    async def notification_read(self, event):
        """Notify client that notification was read (from another device)."""
        await self.send(text_data=json.dumps({
            'type': 'notification_read',
            'notification_id': event['notification_id'],
        }))
    
    async def notification_count(self, event):
        """Send updated unread count to client."""
        await self.send(text_data=json.dumps({
            'type': 'notification_count',
            'unread_count': event['unread_count'],
        }))
    
    async def system_broadcast(self, event):
        """Handle system-wide broadcast messages."""
        await self.send(text_data=json.dumps({
            'type': 'system_broadcast',
            'message': event['message'],
            'data': event.get('data', {}),
        }))
    
    # Database helpers
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread notification count for current user."""
        from notifications.models import Notification
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notifications_read(self, notification_ids):
        """Mark specific notifications as read."""
        from notifications.models import Notification
        from django.utils import timezone
        
        if notification_ids:
            Notification.objects.filter(
                recipient=self.user,
                id__in=notification_ids,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Mark all notifications as read for current user."""
        from notifications.models import Notification
        from django.utils import timezone
        
        Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())


class AppointmentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time appointment updates.
    
    Designed for ALL providers (doctors, nurses, clinics, laboratories, VTC)
    to receive instant appointment notifications without needing to refresh.
    
    Channels/Groups:
    - provider_{provider_id}_appointments: Provider's appointment updates (any provider type)
    - patient_{user_id}_appointments: Patient's appointment updates
    
    Messages sent to client:
    - new_appointment: New appointment request received
    - appointment_updated: Appointment status changed
    - appointment_cancelled: Appointment was cancelled
    - appointment_reminder: Upcoming appointment reminder
    - appointment_confirmed: Appointment was confirmed
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope.get('user')
        
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        self.groups = []
        
        # Determine user type and create appropriate groups
        provider = await self.get_provider()
        
        if provider:
            # Provider (doctor/nurse/etc) - subscribe to their appointment updates
            self.provider_group = f'provider_{provider.id}_appointments'
            self.groups.append(self.provider_group)
            await self.channel_layer.group_add(
                self.provider_group,
                self.channel_name
            )
        
        # Also subscribe to patient appointments (all users can be patients)
        self.patient_group = f'patient_{self.user.id}_appointments'
        self.groups.append(self.patient_group)
        await self.channel_layer.group_add(
            self.patient_group,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation with provider details
        provider_info = None
        if provider:
            provider_info = {
                'id': str(provider.id),
                'type': provider.provider_type if hasattr(provider, 'provider_type') else None,
            }
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': str(self.user.id),
            'is_provider': provider is not None,
            'provider': provider_info,
            'groups': self.groups,
        }))
        
        logger.info(f"Appointment WebSocket connected for user {self.user.id} (provider: {provider_info})")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        for group in getattr(self, 'groups', []):
            await self.channel_layer.group_discard(
                group,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            
            elif message_type == 'get_pending':
                # Get pending appointments count
                pending_count = await self.get_pending_appointments_count()
                await self.send(text_data=json.dumps({
                    'type': 'pending_count',
                    'count': pending_count,
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    # Event handlers
    async def new_appointment(self, event):
        """Notify about new appointment request."""
        await self.send(text_data=json.dumps({
            'type': 'new_appointment',
            'appointment': event['appointment'],
            'message': event.get('message', 'New appointment request received'),
        }))
    
    async def appointment_updated(self, event):
        """Notify about appointment status change."""
        await self.send(text_data=json.dumps({
            'type': 'appointment_updated',
            'appointment': event['appointment'],
            'old_status': event.get('old_status'),
            'new_status': event.get('new_status'),
            'message': event.get('message'),
        }))
    
    async def appointment_cancelled(self, event):
        """Notify about appointment cancellation."""
        await self.send(text_data=json.dumps({
            'type': 'appointment_cancelled',
            'appointment_id': event['appointment_id'],
            'cancelled_by': event.get('cancelled_by'),
            'reason': event.get('reason'),
            'message': event.get('message', 'Appointment was cancelled'),
        }))
    
    async def appointment_reminder(self, event):
        """Send appointment reminder."""
        await self.send(text_data=json.dumps({
            'type': 'appointment_reminder',
            'appointment': event['appointment'],
            'minutes_until': event.get('minutes_until'),
            'message': event.get('message'),
        }))
    
    async def appointment_confirmed(self, event):
        """Notify that appointment was confirmed."""
        await self.send(text_data=json.dumps({
            'type': 'appointment_confirmed',
            'appointment': event['appointment'],
            'message': event.get('message', 'Appointment confirmed'),
        }))
    
    # Database helpers
    @database_sync_to_async
    def get_provider(self):
        """Get provider profile if user is a provider."""
        try:
            if hasattr(self.user, 'provider_profile'):
                return self.user.provider_profile
        except Exception:
            pass
        return None
    
    @database_sync_to_async
    def get_pending_appointments_count(self):
        """Get count of pending appointments for provider."""
        from appointments.models import Appointment, AppointmentStatus
        
        try:
            provider = self.user.provider_profile
            return Appointment.objects.filter(
                provider=provider,
                status=AppointmentStatus.PENDING
            ).count()
        except Exception:
            return 0
