from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import logging
import os

from .models import DeviceToken, Notification
from .services import NotificationService

logger = logging.getLogger(__name__)


def get_firebase_config():
    """Get Firebase configuration from environment variables"""
    return {
        'apiKey': os.environ.get('FIREBASE_API_KEY', ''),
        'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
        'projectId': os.environ.get('FIREBASE_PROJECT_ID', ''),
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
        'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
        'appId': os.environ.get('FIREBASE_APP_ID', ''),
        'measurementId': os.environ.get('FIREBASE_MEASUREMENT_ID', ''),
        'vapidKey': os.environ.get('FIREBASE_VAPID_KEY', ''),
    }


# ============================================
# REST API VIEWS (Use these in production)
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_firebase_config_api(request):
    """
    Get Firebase configuration for client-side initialization.
    
    This endpoint returns the Firebase config needed for web push notifications.
    The config is read from environment variables to keep secrets in .env file.
    
    GET /api/notifications/config/
    """
    config = get_firebase_config()
    return Response({
        'firebase_config': {
            'apiKey': config['apiKey'],
            'authDomain': config['authDomain'],
            'projectId': config['projectId'],
            'storageBucket': config['storageBucket'],
            'messagingSenderId': config['messagingSenderId'],
            'appId': config['appId'],
            'measurementId': config['measurementId'],
        },
        'vapid_key': config['vapidKey'],
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_api(request):
    """
    Register a device token for push notifications.
    
    POST /notifications/api/register/
    {
        "token": "fcm_device_token_here",
        "device_type": "android" | "ios" | "web"
    }
    """
    token = (request.data.get('token') or '').strip()
    device_type = (request.data.get('device_type') or 'web').strip().lower()
    
    if not token:
        return Response(
            {'error': 'Token is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if device_type not in ['android', 'ios', 'web']:
        return Response(
            {'error': 'device_type must be android, ios, or web'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check if token exists for this user
        device_token = DeviceToken.objects.filter(user=request.user, token=token).first()
        
        if device_token:
            # Update existing token for this user
            device_token.device_type = device_type
            device_token.is_active = True
            device_token.save()
            created = False
        else:
            # Check if token exists for a different user
            existing_token = DeviceToken.objects.filter(token=token).first()
            
            if existing_token:
                # Reassign token to current user
                existing_token.user = request.user
                existing_token.device_type = device_type
                existing_token.is_active = True
                existing_token.save()
                device_token = existing_token
                created = False
            else:
                # Create new token
                device_token = DeviceToken.objects.create(
                    user=request.user,
                    token=token,
                    device_type=device_type,
                    is_active=True
                )
                created = True
        
        logger.info(f"✅ Device token {'created' if created else 'updated'} for user {request.user.id}")
        
        return Response({
            'success': True,
            'message': f'Token {"registered" if created else "updated"} successfully',
            'device_id': str(device_token.id),
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error registering device token: {e}", exc_info=True)
        return Response(
            {'error': f'Failed to register token: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unregister_device_api(request):
    """
    Unregister a device token (logout or disable notifications).
    
    POST /notifications/api/unregister/
    {
        "token": "fcm_device_token_here"
    }
    """
    token = request.data.get('token')
    
    if not token:
        return Response(
            {'error': 'Token is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        deleted_count, _ = DeviceToken.objects.filter(
            user=request.user,
            token=token
        ).delete()
        
        if deleted_count > 0:
            logger.info(f"✅ Device token removed for user {request.user.id}")
            return Response({
                'success': True,
                'message': 'Token unregistered successfully'
            })
        else:
            return Response(
                {'error': 'Token not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        logger.error(f"❌ Error unregistering device token: {e}")
        return Response(
            {'error': 'Failed to unregister token'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unregister_all_devices_api(request):
    """
    Unregister all device tokens for the current user (full logout).
    
    DELETE /notifications/api/unregister-all/
    """
    try:
        deleted_count, _ = DeviceToken.objects.filter(user=request.user).delete()
        
        logger.info(f"✅ Removed {deleted_count} device tokens for user {request.user.id}")
        
        return Response({
            'success': True,
            'message': f'Removed {deleted_count} device(s)',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"❌ Error unregistering all devices: {e}")
        return Response(
            {'error': 'Failed to unregister devices'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_devices_api(request):
    """
    List all registered devices for the current user.
    
    GET /notifications/api/devices/
    """
    devices_qs = DeviceToken.objects.filter(
        user=request.user,
        is_active=True
    ).values('id', 'device_type', 'created_at', 'updated_at')
    
    devices = [
        {**d, 'id': str(d['id'])}
        for d in devices_qs
    ]
    return Response({
        'devices': devices,
        'count': len(devices)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification_api(request):
    """
    Send a test FCM notification to the current user's registered devices.
    Use this to verify the backend is actually sending notifications.
    
    POST /api/notifications/test/
    Optional body: { "title": "Custom title", "body": "Custom body" }
    """
    title = (request.data.get('title') or 'MediLink Test').strip() or 'MediLink Test'
    body = (request.data.get('body') or 'If you see this, backend FCM is working.').strip() or 'Test notification.'
    
    sent = NotificationService.send_to_user(
        user=request.user,
        title=title,
        body=body,
        data={'type': 'TEST', 'source': 'backend_test_endpoint'}
    )
    
    if sent:
        logger.info(f"Test notification sent to user {request.user.id}")
        return Response({
            'success': True,
            'message': 'Test notification sent to your registered device(s).',
        })
    
    return Response(
        {
            'success': False,
            'message': 'No notification sent. Register a device token first (POST /api/notifications/register/) and ensure Firebase Admin SDK is initialized (firebase-credentials.json).',
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_to_user_api(request):
    """
    Send a test FCM notification to a specific user's registered devices.
    Highly useful for debugging cross-user notification flows.
    
    POST /api/notifications/test-user/
    Body: { "user_id": "uuid/int", "provider_id": "uuid (optional legacy)", "title": "?", "body": "?" }
    """
    from django.contrib.auth import get_user_model
    from providers.models import Provider
    from patients.models import PatientRecord
    
    User = get_user_model()
    
    user_id = request.data.get('user_id')
    provider_id = request.data.get('provider_id')
    patient_id = request.data.get('patient_id')
    title = (request.data.get('title') or 'MediLink Notification Test').strip()
    body = (request.data.get('body') or f'Test message from {request.user.email}').strip()
    
    target_user = None
    
    if user_id:
        try:
            target_user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError):
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    elif provider_id:
        try:
            provider = Provider.objects.get(id=provider_id)
            target_user = provider.user
        except (Provider.DoesNotExist, ValueError):
            return Response({'error': 'Provider not found'}, status=status.HTTP_404_NOT_FOUND)
    elif patient_id:
        try:
            patient = PatientRecord.objects.get(id=patient_id)
            if not patient.linked_user:
                return Response({'error': 'Patient record is not linked to a user account'}, status=status.HTTP_400_BAD_REQUEST)
            target_user = patient.linked_user
        except (PatientRecord.DoesNotExist, ValueError):
            return Response({'error': 'Patient record not found'}, status=status.HTTP_404_NOT_FOUND)
            
    if not target_user:
        return Response({'error': 'user_id, provider_id, or patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        sent = NotificationService.send_to_user(
            user=target_user,
            title=title,
            body=body,
            data={
                'type': 'TEST_DIRECT', 
                'sender_email': request.user.email,
                'source': 'manual_test_trigger'
            }
        )
        
        if sent:
            logger.info(f"✅ Test notification sent from user {request.user.id} to target user {target_user.id}")
            return Response({
                'success': True,
                'message': f'Test notification sent to {target_user.email}.',
            })
        
        return Response(
            {
                'success': False,
                'message': f'Could not send notification. Target user {target_user.email} may not have any active device tokens.',
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        
        return Response({'error': 'Provider not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"❌ Error in send_test_to_provider_api: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications_api(request):
    """
    List all notifications for the current user.
    
    GET /api/notifications/
    """
    notifications_qs = Notification.objects.filter(
        recipient=request.user
    ).values('id', 'title', 'body', 'notification_type', 'data', 'is_read', 'created_at')
    
    notifications = [
        {**n, 'id': str(n['id']), 'timestamp': n['created_at']}
        for n in notifications_qs
    ]
    return Response({
        'notifications': notifications,
        'count': len(notifications),
        'unread_count': Notification.objects.filter(recipient=request.user, is_read=False).count()
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_notification_read_api(request, notification_id):
    """
    Mark a specific notification as read.
    
    PATCH /api/notifications/<id>/read/
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return Response({'success': True, 'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read_api(request):
    """
    Mark all notifications for the current user as read.
    
    POST /api/notifications/mark-all-read/
    """
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response({'success': True, 'message': 'All notifications marked as read'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification_api(request, notification_id):
    """
    Delete a specific notification.
    
    DELETE /api/notifications/<id>/
    """
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.delete()
        return Response({'success': True, 'message': 'Notification deleted'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_all_notifications_api(request):
    """
    Delete all notifications for the current user.
    
    DELETE /api/notifications/clear-all/
    """
    count, _ = Notification.objects.filter(recipient=request.user).delete()
    return Response({'success': True, 'message': f'Cleared {count} notifications'})


# ============================================
# DASHBOARD / ACTIVITY FEED
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_feed_api(request):
    """
    Get the recent activity feed for the authenticated provider.

    Returns a combined list of recent appointments, invoices, and reviews
    sorted by timestamp descending.

    GET /api/notifications/activity-feed/
    Query params:
        - limit: int (default 20, max 50) — number of items to return
    """
    from common.enums import UserRole

    user = request.user
    if user.role != UserRole.PROVIDER:
        return Response(
            {'error': 'Only providers can access the activity feed.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        provider = user.provider_profile
    except Exception:
        return Response(
            {'error': 'Provider profile not found.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        limit = min(int(request.query_params.get('limit', 20)), 50)
    except (TypeError, ValueError):
        limit = 20

    from .dashboard_services import DashboardStatsService

    items = DashboardStatsService.get_recent_activity(provider, limit=limit)
    return Response({'count': len(items), 'results': items})


# ============================================
# SERVICE WORKER (For web push)
# ============================================

@require_http_methods(["GET"])
def service_worker(request):
    """
    Serve the Firebase messaging service worker with config from environment variables.
    
    This MUST be served from the root of your domain for web push to work.
    The service worker handles background notifications when the browser tab is closed.
    
    Firebase config is read from environment variables to keep secrets safe.
    """
    # Get Firebase config from environment variables
    api_key = os.environ.get('FIREBASE_API_KEY', '')
    auth_domain = os.environ.get('FIREBASE_AUTH_DOMAIN', '')
    project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', '')
    messaging_sender_id = os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '')
    app_id = os.environ.get('FIREBASE_APP_ID', '')
    measurement_id = os.environ.get('FIREBASE_MEASUREMENT_ID', '')
    
    # Build the service worker JavaScript
    # Using string formatting to avoid f-string issues with JavaScript template literals
    js_code = '''
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Firebase configuration (injected from Django environment variables)
firebase.initializeApp({
    apiKey: "''' + api_key + '''",
    authDomain: "''' + auth_domain + '''",
    projectId: "''' + project_id + '''",
    storageBucket: "''' + storage_bucket + '''",
    messagingSenderId: "''' + messaging_sender_id + '''",
    appId: "''' + app_id + '''",
    measurementId: "''' + measurement_id + '''"
});

const messaging = firebase.messaging();

// Handle background messages (when browser tab is closed or in background)
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Background message received:', payload);
    
    const notificationTitle = payload.notification?.title || 'MediLink';
    const notificationOptions = {
        body: payload.notification?.body || '',
        icon: '/static/notifications/icon-192.png',
        badge: '/static/notifications/badge-72.png',
        image: payload.notification?.image,
        data: payload.data,
        vibrate: [100, 50, 100],
        actions: [
            { action: 'open', title: 'Open' },
            { action: 'dismiss', title: 'Dismiss' }
        ]
    };
    
    self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    console.log('[firebase-messaging-sw.js] Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'dismiss') {
        return;
    }
    
    // Get the action URL from data payload or default to home
    const actionUrl = event.notification.data?.action_url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // If a window is already open, focus it
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.focus();
                        client.navigate(actionUrl);
                        return;
                    }
                }
                // Otherwise, open a new window
                if (clients.openWindow) {
                    return clients.openWindow(actionUrl);
                }
            })
    );
});
'''
    response = HttpResponse(js_code, content_type='application/javascript')
    # Allow service worker to be cached but revalidated
    response['Cache-Control'] = 'public, max-age=0, must-revalidate'
    response['Service-Worker-Allowed'] = '/'
    return response