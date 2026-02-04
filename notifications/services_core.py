from firebase_admin import messaging
from .models import DeviceToken
import logging

logger = logging.getLogger(__name__)

class FCMService:
    @staticmethod
    def send_notification(user, title, body, image_url=None, data=None):
        """Send notification to all user's devices"""
        tokens = DeviceToken.objects.filter(
            user=user,
            is_active=True
        ).values_list('token', flat=True)

        if not tokens:
            logger.warning(f"No active tokens found for user {user.id}")
            return None

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
                image=image_url,  # ✅ image support
            ),
            data=data or {},
            tokens=list(tokens),
        )

        try:
            #! Legacy
            # response = messaging.send_multicast(message)
            #! New 
            response = messaging.send_each_for_multicast(message)
            
            logger.info(f"Successfully sent {response.success_count} messages")

            # Handle failed tokens
            if response.failure_count > 0:
                failed_tokens = []
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        failed_tokens.append(list(tokens)[idx])
                        logger.error(f"Failed token: {resp.exception}")

                DeviceToken.objects.filter(
                    token__in=failed_tokens
                ).update(is_active=False)

            return response

        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return None

    @staticmethod
    def send_to_topic(topic, title, body, image_url=None, data=None):
        """Send notification to a topic"""
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
                image=image_url,  # ✅ image support
            ),
            data=data or {},
            topic=topic,
        )

        try:
            response = messaging.send(message)
            logger.info(f"Successfully sent message to topic {topic}: {response}")
            return response
        except Exception as e:
            logger.error(f"Error sending to topic: {str(e)}")
            return None
