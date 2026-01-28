"""
Views for the Notifications app.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q

from .models import (
    Notification,
    DeviceToken,
    NotificationPreference,
    NotificationCategory,
    NotificationPriority,
)
from .serializers import (
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationCreateSerializer,
    BulkNotificationSerializer,
    MarkReadSerializer,
    DeviceTokenSerializer,
    DeviceTokenRegisterSerializer,
    NotificationPreferenceSerializer,
    NotificationStatsSerializer,
)
from .services import NotificationService


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    
    list:
        Get all notifications for the current user.
        Supports filtering by is_read, category, priority, and notification_type.
    
    retrieve:
        Get a single notification and mark it as read.
    
    destroy:
        Delete a notification.
    
    mark_read:
        Mark one or more notifications as read.
    
    mark_all_read:
        Mark all notifications as read.
    
    unread:
        Get only unread notifications.
    
    stats:
        Get notification statistics.
    
    by_category:
        Get notifications grouped by category.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'category', 'priority', 'notification_type']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter to only the current user's notifications."""
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('related_content_type')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        elif self.action == 'mark_read':
            return MarkReadSerializer
        elif self.action == 'stats':
            return NotificationStatsSerializer
        return NotificationDetailSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """Get notification and auto-mark as read."""
        instance = self.get_object()
        instance.mark_as_read()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create notification (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only staff can create notifications directly.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """
        Mark specific notifications as read.
        
        Request body:
            notification_ids: List of notification UUIDs (optional)
            
        If notification_ids is empty or not provided, marks all as read.
        """
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data.get('notification_ids', [])
        count = NotificationService.mark_as_read(request.user, notification_ids or None)
        
        return Response({
            'message': f'{count} notification(s) marked as read.',
            'count': count
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        count = NotificationService.mark_as_read(request.user)
        return Response({
            'message': f'{count} notification(s) marked as read.',
            'count': count
        })
    
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Mark a notification as unread."""
        notification = self.get_object()
        notification.mark_as_unread()
        return Response({'message': 'Notification marked as unread.'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get only unread notifications."""
        queryset = self.get_queryset().filter(is_read=False)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = NotificationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = Notification.get_unread_count(request.user)
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics."""
        stats = NotificationService.get_user_stats(request.user)
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get notifications grouped by category."""
        queryset = self.get_queryset()
        
        result = {}
        for category in NotificationCategory.values:
            notifications = queryset.filter(category=category)[:10]
            result[category] = {
                'count': queryset.filter(category=category).count(),
                'unread': queryset.filter(category=category, is_read=False).count(),
                'recent': NotificationListSerializer(notifications, many=True).data
            }
        
        return Response(result)
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all notifications for the user."""
        count, _ = self.get_queryset().delete()
        return Response({
            'message': f'{count} notification(s) deleted.',
            'count': count
        })
    
    @action(detail=False, methods=['delete'])
    def clear_read(self, request):
        """Delete all read notifications."""
        count, _ = self.get_queryset().filter(is_read=True).delete()
        return Response({
            'message': f'{count} read notification(s) deleted.',
            'count': count
        })


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing device tokens for push notifications.
    
    list:
        Get all device tokens for the current user.
    
    create:
        Register a new device token.
    
    destroy:
        Unregister a device token.
    
    register:
        Simplified endpoint to register a device token.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DeviceTokenSerializer
    
    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a device token for push notifications.
        
        Request body:
            token: FCM device token (required)
            device_type: 'android', 'ios', or 'web' (required)
            device_name: Device name (optional)
            device_id: Unique device identifier (optional)
            app_version: App version (optional)
        """
        serializer = DeviceTokenRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        # Update or create device token
        device_token, created = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                'user': request.user,
                'device_type': serializer.validated_data['device_type'],
                'device_name': serializer.validated_data.get('device_name', ''),
                'device_id': serializer.validated_data.get('device_id', ''),
                'app_version': serializer.validated_data.get('app_version', ''),
                'is_active': True,
                'failure_count': 0,
            }
        )
        
        return Response({
            'id': str(device_token.id),
            'message': 'Device registered successfully.' if created else 'Device token updated.',
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def unregister(self, request):
        """
        Unregister a device token.
        
        Request body:
            token: FCM device token to unregister
        """
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted, _ = DeviceToken.objects.filter(
            user=request.user,
            token=token
        ).delete()
        
        if deleted:
            return Response({'message': 'Device unregistered successfully.'})
        return Response(
            {'error': 'Token not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for managing notification preferences.
    
    retrieve:
        Get current user's notification preferences.
    
    update:
        Update notification preferences.
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get notification preferences."""
        prefs, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)
    
    def create(self, request):
        """Update notification preferences."""
        prefs, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def reset(self, request):
        """Reset preferences to defaults."""
        NotificationPreference.objects.filter(user=request.user).delete()
        prefs = NotificationPreference.objects.create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return Response({
            'message': 'Preferences reset to defaults.',
            'preferences': serializer.data
        })
