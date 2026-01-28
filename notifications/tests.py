"""
Tests for the Notifications app.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from accounts.models import User
from .models import (
    Notification,
    DeviceToken,
    NotificationPreference,
    NotificationType,
    NotificationCategory,
    NotificationPriority,
)
from .services import NotificationService, FCMService


class NotificationModelTest(TestCase):
    """Tests for Notification model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
    
    def test_create_notification(self):
        """Test creating a notification."""
        notification = Notification.objects.create(
            recipient=self.user,
            title='Test Notification',
            message='This is a test message.',
            notification_type=NotificationType.GENERAL,
            category=NotificationCategory.SYSTEM,
        )
        
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
    
    def test_mark_as_read(self):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            recipient=self.user,
            title='Test',
            message='Test message',
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)
    
    def test_mark_as_unread(self):
        """Test marking notification as unread."""
        notification = Notification.objects.create(
            recipient=self.user,
            title='Test',
            message='Test message',
            is_read=True,
            read_at=timezone.now(),
        )
        
        notification.mark_as_unread()
        
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.read_at)
    
    def test_get_unread_count(self):
        """Test getting unread count."""
        # Create 3 notifications, 1 read
        for i in range(3):
            Notification.objects.create(
                recipient=self.user,
                title=f'Test {i}',
                message='Message',
                is_read=(i == 0),
            )
        
        count = Notification.get_unread_count(self.user)
        self.assertEqual(count, 2)
    
    def test_is_expired(self):
        """Test expiration check."""
        # Not expired
        notification1 = Notification.objects.create(
            recipient=self.user,
            title='Future',
            message='Message',
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )
        self.assertFalse(notification1.is_expired)
        
        # Expired
        notification2 = Notification.objects.create(
            recipient=self.user,
            title='Past',
            message='Message',
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        self.assertTrue(notification2.is_expired)


class DeviceTokenModelTest(TestCase):
    """Tests for DeviceToken model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
    
    def test_create_device_token(self):
        """Test creating a device token."""
        token = DeviceToken.objects.create(
            user=self.user,
            token='fcm-token-123',
            device_type='android',
        )
        
        self.assertIsNotNone(token.id)
        self.assertTrue(token.is_active)
        self.assertEqual(token.failure_count, 0)
    
    def test_increment_failure(self):
        """Test failure count increment."""
        token = DeviceToken.objects.create(
            user=self.user,
            token='fcm-token-123',
            device_type='android',
        )
        
        # First two failures
        token.increment_failure()
        token.increment_failure()
        
        token.refresh_from_db()
        self.assertEqual(token.failure_count, 2)
        self.assertTrue(token.is_active)
        
        # Third failure deactivates
        token.increment_failure()
        
        token.refresh_from_db()
        self.assertEqual(token.failure_count, 3)
        self.assertFalse(token.is_active)
    
    def test_reset_failures(self):
        """Test resetting failure count."""
        token = DeviceToken.objects.create(
            user=self.user,
            token='fcm-token-123',
            device_type='android',
            failure_count=2,
        )
        
        token.reset_failures()
        
        token.refresh_from_db()
        self.assertEqual(token.failure_count, 0)
        self.assertIsNotNone(token.last_used_at)


class NotificationPreferenceModelTest(TestCase):
    """Tests for NotificationPreference model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.prefs = NotificationPreference.objects.create(user=self.user)
    
    def test_should_send_push_enabled(self):
        """Test push check when enabled."""
        self.assertTrue(self.prefs.should_send_push(NotificationCategory.APPOINTMENTS))
        self.assertTrue(self.prefs.should_send_push(NotificationCategory.SYSTEM))
    
    def test_should_send_push_disabled(self):
        """Test push check when disabled."""
        self.prefs.push_enabled = False
        self.prefs.save()
        
        self.assertFalse(self.prefs.should_send_push(NotificationCategory.APPOINTMENTS))
    
    def test_should_send_push_category_disabled(self):
        """Test push check for disabled category."""
        self.prefs.push_promotions = False
        self.prefs.save()
        
        self.assertFalse(self.prefs.should_send_push(NotificationCategory.PROMOTIONS))


class NotificationServiceTest(TestCase):
    """Tests for NotificationService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
    
    @patch.object(FCMService, 'send_to_tokens')
    def test_create_notification(self, mock_send):
        """Test creating notification via service."""
        mock_send.return_value = {'success_count': 1, 'failure_count': 0, 'failed_tokens': []}
        
        notification = NotificationService.create_notification(
            recipient=self.user,
            title='Test Title',
            message='Test message',
            notification_type=NotificationType.GENERAL,
            send_push=False,
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, 'Test Title')
        self.assertEqual(notification.recipient, self.user)
    
    def test_mark_as_read(self):
        """Test marking notifications as read via service."""
        # Create notifications
        for i in range(3):
            Notification.objects.create(
                recipient=self.user,
                title=f'Test {i}',
                message='Message',
            )
        
        count = NotificationService.mark_as_read(self.user)
        self.assertEqual(count, 3)
        
        # Verify all are read
        unread = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread, 0)
    
    def test_get_user_stats(self):
        """Test getting user stats."""
        # Create notifications with different categories
        Notification.objects.create(
            recipient=self.user,
            title='Appointment',
            message='Message',
            category=NotificationCategory.APPOINTMENTS,
        )
        Notification.objects.create(
            recipient=self.user,
            title='System',
            message='Message',
            category=NotificationCategory.SYSTEM,
            is_read=True,
        )
        
        stats = NotificationService.get_user_stats(self.user)
        
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['unread'], 1)
        self.assertEqual(stats['by_category'][NotificationCategory.APPOINTMENTS], 1)


class NotificationAPITest(APITestCase):
    """API tests for notifications."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
        
        # Create some notifications
        for i in range(5):
            Notification.objects.create(
                recipient=self.user,
                title=f'Notification {i}',
                message=f'Message {i}',
                is_read=(i < 2),
            )
    
    def test_list_notifications(self):
        """Test listing notifications."""
        response = self.client.get('/api/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unread_count(self):
        """Test getting unread count."""
        response = self.client.get('/api/notifications/unread_count/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 3)
    
    def test_mark_all_read(self):
        """Test marking all as read."""
        response = self.client.post('/api/notifications/mark_all_read/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify
        unread = Notification.objects.filter(recipient=self.user, is_read=False).count()
        self.assertEqual(unread, 0)
    
    def test_stats(self):
        """Test getting stats."""
        response = self.client.get('/api/notifications/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('unread', response.data)


class DeviceTokenAPITest(APITestCase):
    """API tests for device tokens."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
    
    def test_register_device(self):
        """Test registering a device token."""
        response = self.client.post('/api/device-tokens/register/', {
            'token': 'fcm-token-123456',
            'device_type': 'android',
            'device_name': 'Pixel 7',
        })
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        
        # Verify token created
        self.assertTrue(
            DeviceToken.objects.filter(token='fcm-token-123456', user=self.user).exists()
        )
    
    def test_unregister_device(self):
        """Test unregistering a device token."""
        DeviceToken.objects.create(
            user=self.user,
            token='fcm-token-to-remove',
            device_type='android',
        )
        
        response = self.client.post('/api/device-tokens/unregister/', {
            'token': 'fcm-token-to-remove',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            DeviceToken.objects.filter(token='fcm-token-to-remove').exists()
        )


class NotificationPreferenceAPITest(APITestCase):
    """API tests for notification preferences."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_preferences(self):
        """Test getting preferences."""
        response = self.client.get('/api/preferences/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('push_enabled', response.data)
    
    def test_update_preferences(self):
        """Test updating preferences."""
        response = self.client.post('/api/preferences/', {
            'push_promotions': False,
            'quiet_hours_enabled': True,
            'quiet_hours_start': '22:00:00',
            'quiet_hours_end': '08:00:00',
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify
        prefs = NotificationPreference.objects.get(user=self.user)
        self.assertFalse(prefs.push_promotions)
        self.assertTrue(prefs.quiet_hours_enabled)
