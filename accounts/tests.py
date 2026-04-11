"""
Critical tests for authentication and account management.

These tests cover the security-critical paths identified in the architecture review.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import User
from common.enums import UserRole, UserAccountStatus
from providers.models import Provider
from providers.models.nurse import Nurse
from common.enums import ProviderStatus

User = get_user_model()


class AuthenticationTests(TestCase):
    """Tests for authentication endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.patient_data = {
            'email': 'patient@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Patient',
            'last_name': 'One',
            'phone_number': '+213555123450',
        }
        self.provider_data = {
            'email': 'doctor@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'provider_type': 'DOCTOR',
            'first_name': 'Ali',
            'last_name': 'Brahimi',
            'phone_number': '+213555123451',
            'license_number': 'DOC-1001',
            'degree_document': SimpleUploadedFile(
                'degree.pdf',
                b'%PDF-1.4 fake doctor degree document',
                content_type='application/pdf',
            ),
        }
        self.nurse_data = {
            'email': 'nurse@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'provider_type': 'NURSE',
            'first_name': 'Nadia',
            'last_name': 'Khelifi',
            'phone_number': '+213555123456',
            'degree_document': SimpleUploadedFile(
                'degree.pdf',
                b'%PDF-1.4 fake degree document',
                content_type='application/pdf',
            ),
            'entrepreneur_card_front': SimpleUploadedFile(
                'card-front.jpg',
                b'fake image front',
                content_type='image/jpeg',
            ),
            'entrepreneur_card_back': SimpleUploadedFile(
                'card-back.jpg',
                b'fake image back',
                content_type='image/jpeg',
            ),
        }
    
    def test_patient_registration(self):
        """Test patient can register successfully."""
        response = self.client.post('/api/auth/patient/register/', self.patient_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['role'], UserRole.PATIENT)
    
    def test_provider_registration_creates_pending(self):
        """Test provider registration creates PENDING status."""
        response = self.client.post('/api/auth/provider/register/', self.provider_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['provider']['status'], ProviderStatus.PENDING)

    def test_nurse_registration_requires_documents_and_creates_profile(self):
        """Test nurse registration accepts multipart document uploads."""
        response = self.client.post(
            '/api/auth/provider/register/',
            self.nurse_data,
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], UserRole.PROVIDER)

        user = User.objects.get(email='nurse@test.com')
        provider = user.provider_profile
        self.assertEqual(provider.provider_type, 'NURSE')
        nurse = provider.nurse_profile
        self.assertIsInstance(nurse, Nurse)
        self.assertEqual(nurse.first_name, 'Nadia')
        self.assertEqual(nurse.last_name, 'Khelifi')
        self.assertEqual(nurse.phone_number, '+213555123456')
        self.assertTrue(nurse.degree_document.name.endswith('.pdf'))
        self.assertTrue(nurse.entrepreneur_card_front.name.endswith('.jpg'))
        self.assertTrue(nurse.entrepreneur_card_back.name.endswith('.jpg'))

    def test_nurse_registration_rejects_missing_documents(self):
        """Test nurse registration fails if required documents are missing."""
        response = self.client.post('/api/auth/provider/register/', {
            'email': 'nurse-missing@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'provider_type': 'NURSE',
            'first_name': 'Nadia',
            'last_name': 'Khelifi',
            'phone_number': '+213555123456',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('degree_document', response.data)
        self.assertIn('entrepreneur_card_front', response.data)
        self.assertIn('entrepreneur_card_back', response.data)
    
    def test_suspended_user_cannot_login(self):
        """Test suspended user cannot login."""
        user = User.objects.create_user(
            email='suspended@test.com',
            password='testpass123',
            role=UserRole.PATIENT,
        )
        user.suspend()
        
        response = self.client.post('/api/auth/login/', {
            'email': 'suspended@test.com',
            'password': 'testpass123',
        })
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        self.assertIn('error', response.data)


class ProviderAccessTests(TestCase):
    """Tests for provider access control."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create pending provider
        self.pending_user = User.objects.create_user(
            email='pending@test.com',
            password='testpass123',
            role=UserRole.PROVIDER,
        )
        self.pending_provider = Provider.objects.create(
            user=self.pending_user,
            provider_type='DOCTOR',
            status=ProviderStatus.PENDING,
        )
        
        # Create verified provider
        self.verified_user = User.objects.create_user(
            email='verified@test.com',
            password='testpass123',
            role=UserRole.PROVIDER,
        )
        self.verified_provider = Provider.objects.create(
            user=self.verified_user,
            provider_type='DOCTOR',
            status=ProviderStatus.VERIFIED,
        )
        
        # Create refused provider
        self.refused_user = User.objects.create_user(
            email='refused@test.com',
            password='testpass123',
            role=UserRole.PROVIDER,
        )
        self.refused_provider = Provider.objects.create(
            user=self.refused_user,
            provider_type='DOCTOR',
            status=ProviderStatus.REFUSED,
            refusal_reason='Test refusal',
        )
    
    def test_pending_provider_can_check_status(self):
        """Test pending provider can check their status."""
        self.client.force_authenticate(user=self.pending_user)
        response = self.client.get('/api/provider/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], ProviderStatus.PENDING)
    
    def test_refused_provider_sees_refusal_reason(self):
        """Test refused provider sees refusal reason."""
        self.client.force_authenticate(user=self.refused_user)
        response = self.client.get('/api/provider/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], ProviderStatus.REFUSED)
        self.assertIn('refusal_reason', response.data)
        self.assertEqual(response.data['refusal_reason'], 'Test refusal')


class PermissionTests(TestCase):
    """Tests for role-based permissions."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.patient = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            role=UserRole.PATIENT,
        )
        self.provider = User.objects.create_user(
            email='provider@test.com',
            password='testpass123',
            role=UserRole.PROVIDER,
        )
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=UserRole.ADMIN,
        )
        
        # Create provider profile
        Provider.objects.create(
            user=self.provider,
            provider_type='DOCTOR',
            status=ProviderStatus.VERIFIED,
        )
    
    def test_patient_cannot_access_admin_endpoints(self):
        """Test patient cannot access admin endpoints."""
        self.client.force_authenticate(user=self.patient)
        response = self.client.get('/api/admin/providers/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_provider_cannot_access_admin_endpoints(self):
        """Test provider cannot access admin endpoints."""
        self.client.force_authenticate(user=self.provider)
        response = self.client.get('/api/admin/providers/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_access_admin_endpoints(self):
        """Test admin can access admin endpoints."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/providers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminVerificationTests(TestCase):
    """Tests for admin verification workflow."""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create admin
        self.admin = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=UserRole.ADMIN,
        )
        
        # Create pending provider
        self.provider_user = User.objects.create_user(
            email='doctor@test.com',
            password='testpass123',
            role=UserRole.PROVIDER,
        )
        self.provider = Provider.objects.create(
            user=self.provider_user,
            provider_type='DOCTOR',
            status=ProviderStatus.PENDING,
        )
    
    def test_admin_can_verify_provider(self):
        """Test admin can verify a provider."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/admin/providers/{self.provider.id}/verify/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.status, ProviderStatus.VERIFIED)
    
    def test_admin_can_refuse_provider(self):
        """Test admin can refuse a provider with reason."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f'/api/admin/providers/{self.provider.id}/refuse/',
            {'reason': 'Incomplete documentation'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.status, ProviderStatus.REFUSED)
        self.assertEqual(self.provider.refusal_reason, 'Incomplete documentation')
    
    def test_refuse_requires_reason(self):
        """Test refusing provider requires a reason."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f'/api/admin/providers/{self.provider.id}/refuse/',
            {'reason': ''}  # Empty reason
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class IdempotencyTests(TestCase):
    """Tests for idempotent provider registration."""
    
    def setUp(self):
        self.client = APIClient()
        self.provider_data = {
            'email': 'doctor@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'provider_type': 'DOCTOR',
        }
    
    def test_provider_re_registration_idempotent(self):
        """Test provider can re-register (idempotent behavior)."""
        # First registration
        response1 = self.client.post('/api/auth/provider/register/', self.provider_data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Re-registration should return existing provider
        response2 = self.client.post('/api/auth/provider/register/', self.provider_data)
        # Should return 200 or 201 (idempotent)
        self.assertIn(response2.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(response1.data['user']['id'], response2.data['user']['id'])
    
    def test_cannot_register_provider_with_existing_patient_email(self):
        """Test cannot create provider if email exists as patient."""
        # Create patient
        User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role=UserRole.PATIENT,
        )
        
        # Try to register as provider
        response = self.client.post('/api/auth/provider/register/', {
            'email': 'user@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'provider_type': 'DOCTOR',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', str(response.data).lower())
