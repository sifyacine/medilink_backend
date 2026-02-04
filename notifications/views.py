from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import logging
import os

from .models import DeviceToken

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
    devices = DeviceToken.objects.filter(
        user=request.user,
        is_active=True
    ).values('id', 'device_type', 'created_at', 'updated_at')
    
    return Response({
        'devices': list(devices),
        'count': len(devices)
    })


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