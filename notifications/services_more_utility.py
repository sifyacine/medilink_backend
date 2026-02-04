# serviceApp/notifications.py
from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Centralized service for sending FCM notifications
    """
    
    @staticmethod
    def send_to_user(user, title, body, data=None):
        """
        Send notification to a specific user
        Args:
            user: User object
            title: Notification title
            body: Notification body
            data: Additional data payload (dict)
        """
        try:
            # Get FCM token from user profile or device model
            # Assuming you have a DeviceToken model or field in Profile
            from profileApp.models import Profile
            profile = Profile.objects.get(user=user)
            
            # You need to have FCM tokens stored somewhere
            # This could be in Profile model or a separate DeviceToken model
            if not hasattr(profile, 'fcm_token') or not profile.fcm_token:
                logger.warning(f"No FCM token found for user {user.id}")
                return False
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=profile.fcm_token,
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent notification to user {user.id}: {response}")
            return True
            
        except Profile.DoesNotExist:
            logger.error(f"Profile not found for user {user.id}")
            return False
        except FirebaseError as e:
            logger.error(f"Firebase error sending notification: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
    
    @staticmethod
    def send_to_multiple_users(users, title, body, data=None):
        """
        Send notification to multiple users
        Args:
            users: QuerySet or list of User objects
            title: Notification title
            body: Notification body
            data: Additional data payload (dict)
        """
        from profileApp.models import Profile
        
        # Get all valid FCM tokens
        profiles = Profile.objects.filter(
            user__in=users,
            fcm_token__isnull=False
        ).exclude(fcm_token='')
        
        tokens = [profile.fcm_token for profile in profiles]
        
        if not tokens:
            logger.warning("No valid FCM tokens found for users")
            return False
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                tokens=tokens,
            )
            
            response = messaging.send_multicast(message)
            logger.info(f"Successfully sent {response.success_count} notifications")
            
            if response.failure_count > 0:
                logger.warning(f"Failed to send {response.failure_count} notifications")
            
            return True
            
        except FirebaseError as e:
            logger.error(f"Firebase error sending multicast: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error sending multicast notification: {str(e)}")
            return False


# Specific notification functions for service requests

def notify_nearby_nurses_new_request(service_request, nurses):
    """
    Notify nearby nurses about a new service request
    """
    users = [nurse.profile.user for nurse in nurses if nurse.profile]
    
    NotificationService.send_to_multiple_users(
        users=users,
        title="New Service Request Nearby",
        body=f"New {service_request.service.name} request in your area",
        data={
            'type': 'new_service_request',
            'service_request_id': str(service_request.service_request_id),
            'service_name': service_request.service.name,
            'distance': str(service_request.distance_price or 0),
            'action': 'refresh_pending_requests'
        }
    )


def notify_patient_request_accepted(service_request):
    """
    Notify patient that their request was accepted
    """
    NotificationService.send_to_user(
        user=service_request.patient.profile.user,
        title="Request Accepted!",
        body=f"Nurse {service_request.nurse.full_name} accepted your request",
        data={
            'type': 'request_accepted',
            'service_request_id': str(service_request.service_request_id),
            'nurse_name': service_request.nurse.full_name,
            'action': 'refresh_request_details'
        }
    )


def notify_nurse_price_proposed_by_patient(service_request):
    """
    Notify nurse that patient proposed a price
    """
    if not service_request.nurse:
        return
    
    NotificationService.send_to_user(
        user=service_request.nurse.profile.user,
        title="Price Proposal Received",
        body=f"Patient proposed {service_request.patient_proposed_price} for the service",
        data={
            'type': 'price_proposed_patient',
            'service_request_id': str(service_request.service_request_id),
            'proposed_price': str(service_request.patient_proposed_price),
            'action': 'refresh_request_details'
        }
    )


def notify_patient_price_proposed_by_nurse(service_request):
    """
    Notify patient that nurse proposed a price
    """
    NotificationService.send_to_user(
        user=service_request.patient.profile.user,
        title="Price Proposal Received",
        body=f"Nurse proposed {service_request.nurse_proposed_price} for the service",
        data={
            'type': 'price_proposed_nurse',
            'service_request_id': str(service_request.service_request_id),
            'proposed_price': str(service_request.nurse_proposed_price),
            'action': 'refresh_request_details'
        }
    )


def notify_price_accepted(service_request, accepted_by):
    """
    Notify the other party that price was accepted
    accepted_by: 'patient' or 'nurse'
    """
    if accepted_by == 'patient':
        # Notify nurse
        if service_request.nurse:
            NotificationService.send_to_user(
                user=service_request.nurse.profile.user,
                title="Price Accepted!",
                body=f"Patient accepted your price of {service_request.negotiated_price}",
                data={
                    'type': 'price_accepted',
                    'service_request_id': str(service_request.service_request_id),
                    'negotiated_price': str(service_request.negotiated_price),
                    'action': 'refresh_request_details'
                }
            )
    else:
        # Notify patient
        NotificationService.send_to_user(
            user=service_request.patient.profile.user,
            title="Price Accepted!",
            body=f"Nurse accepted your price of {service_request.negotiated_price}",
            data={
                'type': 'price_accepted',
                'service_request_id': str(service_request.service_request_id),
                'negotiated_price': str(service_request.negotiated_price),
                'action': 'refresh_request_details'
            }
        )


def notify_price_rejected(service_request, rejected_by):
    """
    Notify the other party that price was rejected
    rejected_by: 'patient' or 'nurse'
    """
    if rejected_by == 'patient':
        # Notify nurse
        if service_request.nurse:
            NotificationService.send_to_user(
                user=service_request.nurse.profile.user,
                title="Price Rejected",
                body="Patient rejected your price proposal",
                data={
                    'type': 'price_rejected',
                    'service_request_id': str(service_request.service_request_id),
                    'action': 'refresh_request_details'
                }
            )
    else:
        # Notify patient
        NotificationService.send_to_user(
            user=service_request.patient.profile.user,
            title="Price Rejected",
            body="Nurse rejected your price proposal",
            data={
                'type': 'price_rejected',
                'service_request_id': str(service_request.service_request_id),
                'action': 'refresh_request_details'
            }
        )


def notify_patient_service_started(service_request):
    """
    Notify patient that nurse started the service
    """
    NotificationService.send_to_user(
        user=service_request.patient.profile.user,
        title="Service Started",
        body=f"Nurse {service_request.nurse.full_name} has arrived and started the service",
        data={
            'type': 'service_started',
            'service_request_id': str(service_request.service_request_id),
            'action': 'refresh_request_details'
        }
    )


def notify_patient_service_completed(service_request):
    """
    Notify patient that service was completed
    """
    NotificationService.send_to_user(
        user=service_request.patient.profile.user,
        title="Service Completed",
        body="Your service has been completed. Please rate your experience!",
        data={
            'type': 'service_completed',
            'service_request_id': str(service_request.service_request_id),
            'action': 'show_feedback_form'
        }
    )


def notify_nurse_request_cancelled(service_request):
    """
    Notify nurse that patient cancelled the request
    """
    if not service_request.nurse:
        return
    
    NotificationService.send_to_user(
        user=service_request.nurse.profile.user,
        title="Request Cancelled",
        body=f"Patient cancelled the service request",
        data={
            'type': 'request_cancelled',
            'service_request_id': str(service_request.service_request_id),
            'cancellation_reason': service_request.cancellation_reason or '',
            'action': 'refresh_assigned_requests'
        }
    )


def notify_patient_request_refused(service_request):
    """
    Notify patient that nurse refused the request
    """
    NotificationService.send_to_user(
        user=service_request.patient.profile.user,
        title="Request Refused",
        body=f"Nurse {service_request.nurse.full_name} refused your request",
        data={
            'type': 'request_refused',
            'service_request_id': str(service_request.service_request_id),
            'action': 'refresh_request_details'
        }
    )