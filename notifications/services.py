"""
Services for the Notifications app.

Provides:
- FCMService: Firebase Cloud Messaging for push notifications (mobile + web)
- NotificationService: Notification management with WebSocket broadcast
- WebSocketBroadcaster: Real-time WebSocket notification delivery
"""
import logging
from typing import Optional, List, Dict, Any
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class FCMService:
    """
    Firebase Cloud Messaging service for push notifications.
    """
    _initialized = False
    _firebase_app = None
    
    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK."""
        if cls._initialized:
            return True
        
        try:
            import firebase_admin
            from firebase_admin import credentials
            import os
            
            # Get credentials path from settings or environment
            creds_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            if not creds_path:
                creds_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
            
            if not creds_path:
                logger.warning(
                    'Firebase credentials path not configured. '
                    'Set FIREBASE_CREDENTIALS_PATH in settings or environment.'
                )
                return False
            
            if not os.path.exists(creds_path):
                logger.error(f'Firebase credentials file not found: {creds_path}')
                return False
            
            cred = credentials.Certificate(creds_path)
            cls._firebase_app = firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info('Firebase Admin SDK initialized successfully.')
            return True
            
        except ImportError:
            logger.warning('firebase-admin package not installed.')
            return False
        except Exception as e:
            logger.error(f'Failed to initialize Firebase: {e}')
            return False
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if FCM is available and initialized."""
        if not cls._initialized:
            cls.initialize()
        return cls._initialized
    
    @classmethod
    def send_to_token(
        cls,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        priority: str = 'high'
    ) -> Optional[str]:
        """
        Send push notification to a single device token.
        
        Returns:
            Message ID on success, None on failure
        """
        if not cls.is_available():
            logger.warning('FCM not available, skipping push notification.')
            return None
        
        try:
            from firebase_admin import messaging
            
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build Android config
            android = messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    icon='notification_icon',
                    color='#4A90A4',
                    sound='default',
                    click_action='FLUTTER_NOTIFICATION_CLICK'
                )
            )
            
            # Build APNS config for iOS
            apns = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    )
                )
            )
            
            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android,
                apns=apns,
            )
            
            # Send message
            response = messaging.send(message)
            logger.info(f'Push notification sent successfully: {response}')
            return response
            
        except Exception as e:
            logger.error(f'Failed to send push notification: {e}')
            return None
    
    @classmethod
    def send_to_tokens(
        cls,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple device tokens.
        
        Returns:
            Dict with success_count, failure_count, and failed_tokens
        """
        if not cls.is_available():
            logger.warning('FCM not available, skipping push notifications.')
            return {'success_count': 0, 'failure_count': len(tokens), 'failed_tokens': tokens}
        
        if not tokens:
            return {'success_count': 0, 'failure_count': 0, 'failed_tokens': []}
        
        try:
            from firebase_admin import messaging
            
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Build multicast message
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens,
            )
            
            # Send messages
            response = messaging.send_each_for_multicast(message)
            
            # Process results
            failed_tokens = []
            for idx, result in enumerate(response.responses):
                if not result.success:
                    failed_tokens.append(tokens[idx])
                    logger.warning(
                        f'Failed to send to token {tokens[idx][:20]}...: {result.exception}'
                    )
            
            logger.info(
                f'Multicast sent: {response.success_count} success, '
                f'{response.failure_count} failures'
            )
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'failed_tokens': failed_tokens,
            }
            
        except Exception as e:
            logger.error(f'Failed to send multicast notification: {e}')
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'failed_tokens': tokens,
            }
    
    @classmethod
    def send_to_topic(
        cls,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Send push notification to a topic."""
        if not cls.is_available():
            return None
        
        try:
            from firebase_admin import messaging
            
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                topic=topic,
            )
            
            response = messaging.send(message)
            logger.info(f'Topic notification sent to {topic}: {response}')
            return response
            
        except Exception as e:
            logger.error(f'Failed to send topic notification: {e}')
            return None
    
    @classmethod
    def send_web_push(
        cls,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        icon_url: Optional[str] = None,
        click_action: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send Web Push notification via FCM.
        
        Specifically configured for browser push notifications.
        
        Args:
            token: Browser FCM token
            title: Notification title
            body: Notification body
            data: Custom data payload
            icon_url: Notification icon URL
            click_action: URL to open when notification is clicked
        
        Returns:
            Message ID on success, None on failure
        """
        if not cls.is_available():
            return None
        
        try:
            from firebase_admin import messaging
            
            # Web-specific configuration
            webpush_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon=icon_url or '/static/icons/notification-icon.png',
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link=click_action or '/'
                )
            )
            
            message = messaging.Message(
                data=data or {},
                token=token,
                webpush=webpush_config,
            )
            
            response = messaging.send(message)
            logger.info(f'Web push notification sent: {response}')
            return response
            
        except Exception as e:
            logger.error(f'Failed to send web push: {e}')
            return None


class WebSocketBroadcaster:
    """
    Service for broadcasting messages via WebSocket using Django Channels.
    
    Provides real-time notification delivery to connected clients.
    """
    
    @classmethod
    def _get_channel_layer(cls):
        """Get the Channels layer."""
        try:
            from channels.layers import get_channel_layer
            return get_channel_layer()
        except ImportError:
            logger.warning('Django Channels not installed')
            return None
    
    @classmethod
    def send_to_user(cls, user_id, message_type: str, data: Dict[str, Any]):
        """
        Send message to a specific user via WebSocket.
        
        Args:
            user_id: User ID to send to
            message_type: Type of message (e.g., 'notification', 'appointment_updated')
            data: Message data
        """
        channel_layer = cls._get_channel_layer()
        if not channel_layer:
            return
        
        group_name = f'user_{user_id}_notifications'
        
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    **data
                }
            )
            logger.debug(f'WebSocket message sent to user {user_id}')
        except Exception as e:
            logger.error(f'Failed to send WebSocket message to user {user_id}: {e}')
    
    @classmethod
    def send_to_provider(cls, provider_id, message_type: str, data: Dict[str, Any]):
        """
        Send message to a provider (doctor/nurse) via appointment WebSocket.
        
        Args:
            provider_id: Provider ID to send to
            message_type: Type of message (e.g., 'new_appointment')
            data: Message data
        """
        channel_layer = cls._get_channel_layer()
        if not channel_layer:
            return
        
        group_name = f'provider_{provider_id}_appointments'
        
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    **data
                }
            )
            logger.debug(f'WebSocket message sent to provider {provider_id}')
        except Exception as e:
            logger.error(f'Failed to send WebSocket message to provider {provider_id}: {e}')
    
    @classmethod
    def send_to_patient(cls, user_id, message_type: str, data: Dict[str, Any]):
        """
        Send message to a patient via appointment WebSocket.
        
        Args:
            user_id: User ID of the patient
            message_type: Type of message
            data: Message data
        """
        channel_layer = cls._get_channel_layer()
        if not channel_layer:
            return
        
        group_name = f'patient_{user_id}_appointments'
        
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    **data
                }
            )
            logger.debug(f'WebSocket message sent to patient {user_id}')
        except Exception as e:
            logger.error(f'Failed to send WebSocket message to patient {user_id}: {e}')
    
    @classmethod
    def send_to_role(cls, role: str, message_type: str, data: Dict[str, Any]):
        """
        Broadcast message to all users with a specific role.
        
        Args:
            role: Role name (e.g., 'PROVIDER', 'PATIENT', 'ADMIN')
            message_type: Type of message
            data: Message data
        """
        channel_layer = cls._get_channel_layer()
        if not channel_layer:
            return
        
        group_name = f'role_{role}_notifications'
        
        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    **data
                }
            )
            logger.debug(f'WebSocket message broadcast to role {role}')
        except Exception as e:
            logger.error(f'Failed to broadcast WebSocket message to role {role}: {e}')
    
    @classmethod
    def broadcast_notification(cls, user_id, notification_data: Dict[str, Any]):
        """
        Broadcast a new notification to user's WebSocket connections.
        
        Args:
            user_id: User ID to notify
            notification_data: Serialized notification data
        """
        cls.send_to_user(user_id, 'notification', {'notification': notification_data})
    
    @classmethod
    def broadcast_appointment_event(
        cls,
        provider_id,
        patient_user_id,
        event_type: str,
        appointment_data: Dict[str, Any],
        message: str = None
    ):
        """
        Broadcast an appointment event to both provider and patient.
        
        Args:
            provider_id: Provider ID
            patient_user_id: Patient's user ID (can be None)
            event_type: Event type ('new_appointment', 'appointment_updated', etc.)
            appointment_data: Serialized appointment data
            message: Optional message to include
        """
        event_data = {
            'appointment': appointment_data,
            'message': message,
        }
        
        # Send to provider
        cls.send_to_provider(provider_id, event_type, event_data)
        
        # Send to patient if they have a user account
        if patient_user_id:
            cls.send_to_patient(patient_user_id, event_type, event_data)


class NotificationService:
    """
    Service for managing notifications with WebSocket and FCM integration.
    """
    
    @classmethod
    def create_notification(
        cls,
        recipient,
        title: str,
        message: str,
        notification_type: str = 'GENERAL',
        category: str = 'SYSTEM',
        priority: str = 'NORMAL',
        related_object=None,
        action_url: str = '',
        data: Optional[Dict] = None,
        image_url: Optional[str] = None,
        send_push: bool = True,
        send_websocket: bool = True,
        expires_at=None,
    ):
        """
        Create a notification with push and WebSocket delivery.
        
        Args:
            recipient: User to notify
            title: Notification title
            message: Notification body
            notification_type: Type from NotificationType
            category: Category from NotificationCategory
            priority: Priority from NotificationPriority
            related_object: Optional related model instance
            action_url: URL/route for navigation
            data: Additional JSON data
            image_url: Image URL for rich notification
            send_push: Whether to send FCM push notification
            send_websocket: Whether to broadcast via WebSocket
            expires_at: When notification expires
        
        Returns:
            Created Notification instance
        """
        from .models import Notification, NotificationPreference
        
        # Build notification data
        notification_data = {
            'recipient': recipient,
            'title': title,
            'message': message,
            'notification_type': notification_type,
            'category': category,
            'priority': priority,
            'action_url': action_url,
            'data': data or {},
            'image_url': image_url,
            'expires_at': expires_at,
        }
        
        # Handle related object
        if related_object:
            notification_data['related_content_type'] = ContentType.objects.get_for_model(
                related_object
            )
            notification_data['related_object_id'] = str(related_object.pk)
        
        # Create notification
        notification = Notification.objects.create(**notification_data)
        
        # Broadcast via WebSocket for real-time delivery
        if send_websocket:
            cls._broadcast_via_websocket(notification)
        
        # Send FCM push notification if enabled
        if send_push:
            cls._send_push_for_notification(notification)
        
        return notification
    
    @classmethod
    def create_for_object(
        cls,
        recipient,
        title: str,
        message: str,
        related_object,
        notification_type: str = 'GENERAL',
        priority: str = 'NORMAL',
        action_url: str = '',
        data: Optional[Dict] = None,
        send_push: bool = True,
        send_websocket: bool = True,
    ):
        """
        Create a notification linked to a specific object.
        
        Convenience method for creating notifications with related objects.
        Auto-determines category based on notification type.
        
        Args:
            recipient: User to notify
            title: Notification title
            message: Notification body
            related_object: Related model instance (Appointment, etc.)
            notification_type: Type from NotificationType
            priority: Priority from NotificationPriority
            action_url: URL/route for navigation
            data: Additional JSON data
            send_push: Whether to send FCM push notification
            send_websocket: Whether to broadcast via WebSocket
        
        Returns:
            Created Notification instance
        """
        from .models import NotificationType as NT, NotificationCategory
        
        # Auto-determine category from notification type
        type_to_category = {
            NT.APPOINTMENT_CREATED: NotificationCategory.APPOINTMENTS,
            NT.APPOINTMENT_CONFIRMED: NotificationCategory.APPOINTMENTS,
            NT.APPOINTMENT_CANCELLED: NotificationCategory.APPOINTMENTS,
            NT.APPOINTMENT_UPDATED: NotificationCategory.APPOINTMENTS,
            NT.APPOINTMENT_REMINDER: NotificationCategory.REMINDERS,
            NT.APPOINTMENT_COMPLETED: NotificationCategory.APPOINTMENTS,
            NT.ACCOUNT_VERIFIED: NotificationCategory.ACCOUNT,
            NT.ACCOUNT_SUSPENDED: NotificationCategory.ACCOUNT,
            NT.PROVIDER_APPROVED: NotificationCategory.ACCOUNT,
            NT.PROVIDER_REFUSED: NotificationCategory.ACCOUNT,
            NT.PATIENT_RECORD_CREATED: NotificationCategory.ACCOUNT,
            NT.PATIENT_ACCOUNT_LINKED: NotificationCategory.ACCOUNT,
            NT.SYSTEM_ANNOUNCEMENT: NotificationCategory.SYSTEM,
            NT.SYSTEM_MAINTENANCE: NotificationCategory.SYSTEM,
            NT.MESSAGE: NotificationCategory.MESSAGES,
            NT.GENERAL: NotificationCategory.SYSTEM,
        }
        
        category = type_to_category.get(notification_type, NotificationCategory.SYSTEM)
        
        return cls.create_notification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category,
            priority=priority,
            related_object=related_object,
            action_url=action_url,
            data=data,
            send_push=send_push,
            send_websocket=send_websocket,
        )
    
    @classmethod
    def _broadcast_via_websocket(cls, notification):
        """Broadcast notification via WebSocket for real-time delivery."""
        try:
            # Serialize notification for WebSocket
            notification_data = {
                'id': str(notification.id),
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'category': notification.category,
                'priority': notification.priority,
                'action_url': notification.action_url,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'data': notification.data,
            }
            
            if notification.image_url:
                notification_data['image_url'] = notification.image_url
            
            if notification.related_object_id:
                notification_data['related_object_id'] = notification.related_object_id
                notification_data['related_type'] = notification.related_content_type.model if notification.related_content_type else None
            
            # Broadcast to user
            WebSocketBroadcaster.broadcast_notification(
                user_id=notification.recipient_id,
                notification_data=notification_data
            )
            
        except Exception as e:
            logger.error(f'Failed to broadcast notification via WebSocket: {e}')
    
    @classmethod
    def create_bulk_notifications(
        cls,
        recipients: List,
        title: str,
        message: str,
        notification_type: str = 'GENERAL',
        category: str = 'SYSTEM',
        priority: str = 'NORMAL',
        action_url: str = '',
        data: Optional[Dict] = None,
        send_push: bool = True,
    ) -> List:
        """
        Create notifications for multiple recipients.
        
        Returns:
            List of created notifications
        """
        from .models import Notification
        
        notifications = []
        with transaction.atomic():
            for recipient in recipients:
                notification = Notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    category=category,
                    priority=priority,
                    action_url=action_url,
                    data=data or {},
                )
                notifications.append(notification)
            
            Notification.objects.bulk_create(notifications)
        
        # Send push notifications
        if send_push and notifications:
            cls._send_bulk_push(notifications, title, message, data)
        
        return notifications
    
    @classmethod
    def _send_push_for_notification(cls, notification):
        """Send push notification for a single notification."""
        from .models import DeviceToken, NotificationPreference
        
        recipient = notification.recipient
        
        # Check user preferences
        try:
            prefs = recipient.notification_preferences
            if not prefs.should_send_push(notification.category):
                logger.info(f'Push disabled for category {notification.category} for user {recipient.id}')
                return
            if prefs.is_quiet_hours():
                logger.info(f'Quiet hours active for user {recipient.id}')
                return
        except NotificationPreference.DoesNotExist:
            pass
        
        # Get active device tokens
        tokens = list(
            DeviceToken.objects.filter(
                user=recipient,
                is_active=True
            ).values_list('token', flat=True)
        )
        
        if not tokens:
            logger.info(f'No active device tokens for user {recipient.id}')
            return
        
        # Prepare push data
        push_data = {
            'notification_id': str(notification.id),
            'type': notification.notification_type,
            'category': notification.category,
        }
        if notification.action_url:
            push_data['action_url'] = notification.action_url
        if notification.data:
            push_data.update({k: str(v) for k, v in notification.data.items()})
        
        # Send push
        result = FCMService.send_to_tokens(
            tokens=tokens,
            title=notification.title,
            body=notification.message,
            data=push_data,
            image_url=notification.image_url,
        )
        
        # Update push status
        if result['success_count'] > 0:
            notification.push_sent = True
            notification.push_sent_at = timezone.now()
            notification.save(update_fields=['push_sent', 'push_sent_at', 'updated_at'])
        
        # Handle failed tokens
        if result['failed_tokens']:
            cls._handle_failed_tokens(result['failed_tokens'])
    
    @classmethod
    def _send_bulk_push(cls, notifications, title: str, message: str, data: Dict = None):
        """Send push for bulk notifications."""
        from .models import DeviceToken
        
        if not notifications:
            return
        
        # Collect all recipient tokens
        recipient_ids = [n.recipient_id for n in notifications]
        
        tokens = list(
            DeviceToken.objects.filter(
                user_id__in=recipient_ids,
                is_active=True
            ).values_list('token', flat=True)
        )
        
        if not tokens:
            return
        
        push_data = {'type': 'BULK', 'category': 'SYSTEM'}
        if data:
            push_data.update({k: str(v) for k, v in data.items()})
        
        result = FCMService.send_to_tokens(
            tokens=tokens,
            title=title,
            body=message,
            data=push_data,
        )
        
        if result['failed_tokens']:
            cls._handle_failed_tokens(result['failed_tokens'])
    
    @classmethod
    def _handle_failed_tokens(cls, failed_tokens: List[str]):
        """Handle failed device tokens by incrementing failure count."""
        from .models import DeviceToken
        
        for token in failed_tokens:
            try:
                device_token = DeviceToken.objects.get(token=token)
                device_token.increment_failure()
            except DeviceToken.DoesNotExist:
                pass
    
    @classmethod
    def mark_as_read(cls, user, notification_ids: List[str] = None) -> int:
        """
        Mark notifications as read.
        
        Args:
            user: User whose notifications to mark
            notification_ids: Optional list of notification IDs. If None, marks all.
        
        Returns:
            Number of notifications marked as read
        """
        from .models import Notification
        
        queryset = Notification.objects.filter(recipient=user, is_read=False)
        
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        
        count = queryset.update(is_read=True, read_at=timezone.now())
        return count
    
    @classmethod
    def delete_old_notifications(cls, days: int = 30) -> int:
        """Delete notifications older than specified days."""
        from .models import Notification
        
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
        return deleted
    
    @classmethod
    def get_user_stats(cls, user) -> Dict[str, Any]:
        """Get notification statistics for a user."""
        from .models import Notification, NotificationCategory, NotificationPriority
        from django.db.models import Count, Q
        
        queryset = Notification.objects.filter(recipient=user)
        
        total = queryset.count()
        unread = queryset.filter(is_read=False).count()
        
        # Count by category
        by_category = {}
        for category in NotificationCategory.values:
            by_category[category] = queryset.filter(category=category).count()
        
        # Count by priority
        by_priority = {}
        for priority in NotificationPriority.values:
            by_priority[priority] = queryset.filter(priority=priority).count()
        
        return {
            'total': total,
            'unread': unread,
            'by_category': by_category,
            'by_priority': by_priority,
        }
