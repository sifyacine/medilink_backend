# notifications/services.py
"""
Unified Notification Service — FCM Push + WebSocket Broadcasting.

This module provides a clean, unified interface for:
1. **FCM push notifications** via Firebase Cloud Messaging
2. **WebSocket real-time broadcasting** via Django Channels

Usage:
    from notifications.services import NotificationService, WebSocketBroadcaster
    
    # Send FCM push to a single user
    NotificationService.send_to_user(
        user=user_instance,
        title="Hello",
        body="World",
        data={'key': 'value'}
    )
    
    # Broadcast real-time WebSocket event
    WebSocketBroadcaster.send_to_patient(
        user_id=42,
        message_type='appointment_confirmed',
        data={'appointment': {...}},
    )
    
    # Create notification (stores in DB + sends FCM push)
    NotificationService.create_notification(
        user=user_instance,
        title="Hello",
        body="World",
    )
"""

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from django.contrib.auth import get_user_model
import logging

from .models import DeviceToken, Notification, NotificationType, NotificationCategory, NotificationPriority

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Centralized service for sending FCM push notifications.
    
    All notification types use this service under the hood.
    It handles:
    - Fetching user device tokens from the database
    - Sending via FCM
    - Automatic cleanup of invalid/expired tokens
    - Storing notifications in the database for in-app history
    
    For real-time WebSocket delivery, use ``WebSocketBroadcaster``.
    """
    
    # ============================================
    # CORE FCM METHODS
    # ============================================
    
    @staticmethod
    def send_to_user(user, title: str, body: str, image_url: str = None, data: dict = None) -> bool:
        """
        Send a notification to all active devices of a specific user.
        
        Args:
            user: User instance to send notification to
            title: Notification title
            body: Notification body text
            image_url: Optional image URL for rich notifications
            data: Optional data payload (must be dict with string values)
            
        Returns:
            bool: True if at least one message was sent successfully
        """
        # Always persist the in-app notification to DB first, regardless of
        # whether the user has FCM tokens or whether Firebase is configured.
        # This ensures the notification bell always reflects real activity.
        NotificationService._save_notification(
            user=user,
            title=title,
            body=body,
            data=data,
        )

        tokens = list(DeviceToken.objects.filter(
            user=user,
            is_active=True
        ).values_list('token', flat=True))

        if not tokens:
            logger.debug(f"No active tokens found for user {user.id}")
            return False

        return NotificationService._send_to_tokens(
            tokens=tokens,
            title=title,
            body=body,
            image_url=image_url,
            data=data,
        )
    
    @staticmethod
    def send_to_users(users, title: str, body: str, image_url: str = None, data: dict = None) -> bool:
        """
        Send a notification to multiple users.
        
        Args:
            users: QuerySet or list of User instances
            title: Notification title
            body: Notification body text
            image_url: Optional image URL
            data: Optional data payload
            
        Returns:
            bool: True if at least one message was sent successfully
        """
        # Save to database for history for each user regardless of FCM result
        for user in users:
            NotificationService._save_notification(
                user=user,
                title=title,
                body=body,
                data=data
            )

        # Get all tokens for the given users
        tokens = list(DeviceToken.objects.filter(
            user__in=users,
            is_active=True
        ).values_list('token', flat=True))
        
        if not tokens:
            logger.debug(f"No active tokens found for users")
            return False
        
        return NotificationService._send_to_tokens(
            tokens=tokens,
            title=title,
            body=body,
            image_url=image_url,
            data=data
        )
    
    @staticmethod
    def send_to_topic(topic: str, title: str, body: str, image_url: str = None, data: dict = None) -> bool:
        """
        Send a notification to a topic (all subscribers).
        
        Args:
            topic: Topic name (e.g., 'news', 'promotions')
            title: Notification title
            body: Notification body text
            image_url: Optional image URL
            data: Optional data payload
            
        Returns:
            bool: True if message was sent successfully
        """
        # Ensure data values are strings (FCM requirement)
        safe_data = NotificationService._prepare_data(data)
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
                image=image_url,
            ),
            data=safe_data,
            topic=topic,
        )
        
        try:
            response = messaging.send(message)
            logger.info(f"✅ Sent message to topic '{topic}': {response}")
            return True
        except FirebaseError as e:
            logger.error(f"❌ Firebase error sending to topic '{topic}': {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending to topic '{topic}': {e}")
            return False
    
    # ============================================
    # COMPATIBILITY METHODS (For other apps)
    # These provide a simple interface that other apps use
    # ============================================
    
    @staticmethod
    def create_notification(user=None, recipient=None, title: str = '', body: str = '', 
                           message: str = '', notification_type: str = None, 
                           data: dict = None, **kwargs) -> bool:
        """
        Create and send a notification to a user.
        
        This is a compatibility method for other apps that expect to create
        notification records. In FCM-only mode, this just sends the push.
        
        Args:
            user: User to notify (alias for recipient)
            recipient: User to notify
            title: Notification title
            body: Notification body (message is an alias)
            message: Alias for body
            notification_type: Type of notification (included in data)
            data: Additional data payload
            **kwargs: Additional arguments (ignored for FCM-only)
            
        Returns:
            bool: True if notification was sent successfully
        """
        target_user = user or recipient
        if not target_user:
            logger.warning("No user specified for notification")
            return False
        
        # Use body or message (whichever is provided)
        notification_body = body or message
        
        # Build data payload
        notification_data = data.copy() if data else {}
        if notification_type:
            notification_data['type'] = str(notification_type)
        
        return NotificationService.send_to_user(
            user=target_user,
            title=title,
            body=notification_body,
            data=notification_data
        )
    
    @staticmethod
    def create_for_object(recipient, title: str, message: str, related_object=None,
                         notification_type=None, priority=None, action_url: str = None,
                         data: dict = None, **kwargs) -> bool:
        """
        Create a notification related to a specific object.
        
        This is a compatibility method for apps like appointments that create
        notifications linked to specific objects.
        
        In FCM-only mode, this sends the push notification with object info in data.
        
        Args:
            recipient: User to notify
            title: Notification title
            message: Notification body
            related_object: Related Django model instance (optional)
            notification_type: Type of notification
            priority: Priority level (included in data)
            action_url: URL to navigate to (included in data)
            data: Additional data payload
            
        Returns:
            bool: True if notification was sent successfully
        """
        if not recipient:
            logger.warning("No recipient specified for notification")
            return False
        
        # Build data payload
        notification_data = data.copy() if data else {}
        
        if notification_type:
            notification_data['type'] = str(notification_type)
        
        if priority:
            notification_data['priority'] = str(priority)
        
        if action_url:
            notification_data['action_url'] = action_url
        
        # Add related object info if provided
        if related_object:
            notification_data['object_type'] = related_object.__class__.__name__
            notification_data['object_id'] = str(related_object.pk)
        
        return NotificationService.send_to_user(
            user=recipient,
            title=title,
            body=message,
            data=notification_data
        )
    
    # ============================================
    # INTERNAL METHODS
    # ============================================
    
    @staticmethod
    def _send_to_tokens(tokens: list, title: str, body: str, image_url: str = None, data: dict = None) -> bool:
        """
        Internal method to send notifications to a list of FCM tokens.
        
        Handles:
        - Batching (FCM allows max 500 tokens per request)
        - Token cleanup for failed tokens
        """
        if not tokens:
            logger.debug("No FCM tokens to send to")
            return False

        # Ensure Firebase Admin SDK is initialized (required for sending)
        try:
            import firebase_admin
            if not firebase_admin._apps:
                logger.warning("Firebase Admin SDK not initialized; cannot send FCM. Check firebase-credentials.json.")
                return False
        except Exception as e:
            logger.warning(f"Firebase check failed: {e}; cannot send FCM.")
            return False
        
        # Ensure data values are strings (FCM requirement)
        safe_data = NotificationService._prepare_data(data)
        
        # FCM limits to 500 tokens per multicast
        BATCH_SIZE = 500
        total_success = 0
        total_failure = 0
        failed_tokens = []
        
        for i in range(0, len(tokens), BATCH_SIZE):
            batch_tokens = tokens[i:i + BATCH_SIZE]
            
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url,
                ),
                data=safe_data,
                tokens=batch_tokens,
            )
            
            try:
                response = messaging.send_each_for_multicast(message)
                total_success += response.success_count
                total_failure += response.failure_count
                
                # Collect failed tokens for cleanup
                if response.failure_count > 0:
                    for idx, resp in enumerate(response.responses):
                        if not resp.success:
                            failed_tokens.append(batch_tokens[idx])
                            
            except FirebaseError as e:
                logger.error(f"❌ Firebase error in batch: {e}")
                total_failure += len(batch_tokens)
            except Exception as e:
                logger.error(f"❌ Error sending batch: {e}")
                total_failure += len(batch_tokens)
        
        # Cleanup failed tokens
        if failed_tokens:
            cleanup_count = DeviceToken.objects.filter(
                token__in=failed_tokens
            ).update(is_active=False)
            logger.info(f"🧹 Deactivated {cleanup_count} invalid tokens")
        
        logger.info(f"📬 Notification sent: {total_success} success, {total_failure} failed")
        return total_success > 0
    

    @staticmethod
    def _save_notification(user, title: str, body: str, data: dict = None) -> None:
        """
        Internal helper to save a notification to the database.
        """
        try:
            # Map notification_type if present in data
            notif_type = data.get('type') if data else None
            # Basic validation of choices
            if notif_type not in [c[0] for c in NotificationType.choices]:
                notif_type = NotificationType.GENERAL

            Notification.objects.create(
                recipient=user,
                title=title,
                body=body,
                notification_type=notif_type,
                data=data or {},
                is_read=False,
                push_sent=False,
                action_url=data.get('action_url', '') if data else '',
            )
            logger.info(f"💾 Saved notification '{title}' for user {user.id}")
        except Exception as e:
            logger.error(f"❌ Error saving notification to history: {e}", exc_info=True)

    @staticmethod
    def _prepare_data(data: dict) -> dict:
        """
        Prepare data payload for FCM.
        FCM requires all data values to be strings.
        """
        if not data:
            return {}
        
        return {str(k): str(v) for k, v in data.items() if v is not None}


# ============================================
# WEBSOCKET BROADCASTER (Channel Layer)
# Pushes real-time messages to connected WebSocket clients
# via Django Channels' channel layer (in-memory or Redis).
# ============================================

class WebSocketBroadcaster:
    """
    Broadcast messages to WebSocket consumers via the Channel Layer.

    Group naming conventions (must match the consumers):
        user_{user_id}_notifications   — general notification stream
        user_{user_id}_appointments    — appointment events for a user
        appointment_{appt_id}          — events for a single appointment
    """

    @staticmethod
    def _get_channel_layer():
        """Lazily import to avoid issues at module load time."""
        try:
            from channels.layers import get_channel_layer
            layer = get_channel_layer()
            if layer is None:
                logger.debug("Channel layer is not configured")
            return layer
        except Exception as e:
            logger.warning("Could not get channel layer: %s", e)
            return None

    @staticmethod
    def _send(group: str, message: dict) -> None:
        """
        Fire-and-forget send to a channel layer group.

        Uses ``async_to_sync`` so callers don't need to be async.
        """
        layer = WebSocketBroadcaster._get_channel_layer()
        if layer is None:
            return
        try:
            from asgiref.sync import async_to_sync
            async_to_sync(layer.group_send)(group, message)
            logger.debug("WS sent %s to group %s", message.get("type"), group)
        except Exception as e:
            logger.error("WS broadcast error (%s → %s): %s", message.get("type"), group, e)

    # ----- High-level helpers used by other apps -----

    @staticmethod
    def send_to_provider(provider_id, message_type: str, data: dict) -> None:
        """
        Send to a provider's personal groups.

        Resolves provider → user_id then pushes to both the
        notification stream and the appointments stream.
        """
        try:
            from providers.models.provider import Provider
            provider = Provider.objects.select_related("user").get(pk=provider_id)
            user_id = provider.user_id
        except Exception:
            logger.warning("send_to_provider: cannot resolve provider %s", provider_id)
            return

        WebSocketBroadcaster._send_to_user_groups(user_id, message_type, data)

    @staticmethod
    def send_to_patient(user_id, message_type: str, data: dict) -> None:
        """Send to a patient (user) groups."""
        WebSocketBroadcaster._send_to_user_groups(user_id, message_type, data)

    @staticmethod
    def send_to_user(user_id, message_type: str, data: dict) -> None:
        """Send to any user's groups (generic)."""
        WebSocketBroadcaster._send_to_user_groups(user_id, message_type, data)

    @staticmethod
    def broadcast(channel: str, message_type: str, data: dict) -> None:
        """Send to an arbitrary group name."""
        WebSocketBroadcaster._send(channel, {
            "type": message_type,
            "data": data,
        })

    @staticmethod
    def send_to_appointment(appointment_id, message_type: str, data: dict) -> None:
        """
        Send to the appointment-specific group so all subscribers
        watching that single appointment receive the event.
        """
        group = f"appointment_{appointment_id}"
        WebSocketBroadcaster._send(group, {
            "type": message_type,
            "data": data,
        })

    # ----- Internal -----

    @staticmethod
    def _send_to_user_groups(user_id, message_type: str, data: dict) -> None:
        """Push to both the notification and appointment groups of a user."""
        # Notification stream
        WebSocketBroadcaster._send(
            f"user_{user_id}_notifications",
            {"type": message_type, "data": data},
        )
        # Appointment stream (if it's an appointment event)
        if "appointment" in message_type:
            WebSocketBroadcaster._send(
                f"user_{user_id}_appointments",
                {"type": message_type, "data": data},
            )
        # Nurse-request stream
        if "nurse_request" in message_type:
            WebSocketBroadcaster._send(
                f"user_{user_id}_nurse_requests",
                {"type": message_type, "data": data},
            )


# ============================================
# Convenience functions for common notifications
# ============================================

def send_notification(user, title: str, body: str, data: dict = None, image_url: str = None) -> bool:
    """
    Convenience function to send a notification to a user.
    
    This is the main function you should use throughout the app.
    """
    return NotificationService.send_to_user(
        user=user,
        title=title,
        body=body,
        image_url=image_url,
        data=data
    )


def send_notification_to_users(users, title: str, body: str, data: dict = None, image_url: str = None) -> bool:
    """
    Convenience function to send a notification to multiple users.
    """
    return NotificationService.send_to_users(
        users=users,
        title=title,
        body=body,
        image_url=image_url,
        data=data
    )


def send_topic_notification(topic: str, title: str, body: str, data: dict = None, image_url: str = None) -> bool:
    """
    Convenience function to send a notification to a topic.
    """
    return NotificationService.send_to_topic(
        topic=topic,
        title=title,
        body=body,
        image_url=image_url,
        data=data
    )
