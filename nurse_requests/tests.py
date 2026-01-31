from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import timedelta

from .models import (
    NurseServiceRequest,
    NurseOffer,
    RequestStatus,
    OfferStatus
)
from .services import NurseRequestService
from services.models import Service, ServiceType
from common.enums import UserRole

User = get_user_model()


def create_nursing_service(name, base_price, duration_minutes=30, is_active=True, description=''):
    """Helper function to create a nursing service for tests"""
    return Service.objects.create(
        title=name,
        slug=name.lower().replace(' ', '-'),
        description=description or f'Professional {name} service',
        price=base_price,
        duration_minutes=duration_minutes,
        service_type=ServiceType.NURSE,
        is_on_demand=True,
        is_active=is_active
    )


class NursingServiceModelTests(TestCase):
    """Tests for Nursing Service (using services.Service)"""
    
    def test_create_nursing_service(self):
        """Test creating a nursing service"""
        service = create_nursing_service(
            name='Wound Dressing',
            description='Professional wound care and dressing change',
            base_price=Decimal('50.00'),
            duration_minutes=30,
            is_active=True
        )
        
        self.assertEqual(service.title, 'Wound Dressing')
        self.assertEqual(service.price, Decimal('50.00'))
        self.assertTrue(service.is_active)
        self.assertEqual(service.service_type, ServiceType.NURSE)
        self.assertTrue(service.is_on_demand)
    
    def test_nursing_service_str(self):
        """Test nursing service string representation"""
        service = create_nursing_service(
            name='IV Therapy',
            description='IV drip administration',
            base_price=Decimal('100.00'),
            duration_minutes=60
        )
        
        self.assertIn('IV Therapy', str(service))


class NurseServiceRequestModelTests(TestCase):
    """Tests for NurseServiceRequest model"""
    
    def setUp(self):
        """Set up test data"""
        # Create patient user
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            role=UserRole.PATIENT
        )
        
        # Create service
        self.service = create_nursing_service(
            name='Wound Dressing',
            description='Professional wound care',
            base_price=Decimal('50.00'),
            duration_minutes=30
        )
    
    def test_create_request_with_valid_price(self):
        """Test creating request with valid offered price"""
        request = NurseServiceRequest.objects.create(
            patient_user=self.patient_user,
            service=self.service,
            base_price=self.service.price,
            patient_offered_price=Decimal('75.00'),
            latitude=Decimal('36.7525'),
            longitude=Decimal('3.0420'),
            city='Algiers'
        )
        
        self.assertEqual(request.status, RequestStatus.CREATED)
        self.assertEqual(request.patient_offered_price, Decimal('75.00'))
    
    def test_create_request_with_invalid_price(self):
        """Test that request with price below base fails"""
        with self.assertRaises(ValueError):
            NurseServiceRequest.objects.create(
                patient_user=self.patient_user,
                service=self.service,
                base_price=self.service.price,
                patient_offered_price=Decimal('30.00'),  # Below base price
                latitude=Decimal('36.7525'),
                longitude=Decimal('3.0420'),
                city='Algiers'
            )


class NurseOfferModelTests(TestCase):
    """Tests for NurseOffer model"""
    
    def setUp(self):
        """Set up test data"""
        from providers.models import Provider
        
        # Create patient
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            role=UserRole.PATIENT
        )
        
        # Create nurse
        self.nurse_user = User.objects.create_user(
            email='nurse@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Nurse',
            role=UserRole.PROVIDER
        )
        self.nurse = Provider.objects.create(
            user=self.nurse_user,
            provider_type='NURSE'
        )
        
        # Create service and request
        self.service = create_nursing_service(
            name='Wound Dressing',
            description='Professional wound care',
            base_price=Decimal('50.00'),
            duration_minutes=30
        )
        self.request = NurseServiceRequest.objects.create(
            patient_user=self.patient_user,
            service=self.service,
            base_price=self.service.price,
            patient_offered_price=Decimal('75.00'),
            latitude=Decimal('36.7525'),
            longitude=Decimal('3.0420'),
            city='Algiers'
        )
    
    def test_create_offer_at_patient_price(self):
        """Test nurse can accept at patient's price"""
        offer = NurseOffer.objects.create(
            request=self.request,
            nurse=self.nurse,
            offered_price=Decimal('75.00')
        )
        
        self.assertEqual(offer.status, OfferStatus.PENDING)
        self.assertEqual(offer.offered_price, Decimal('75.00'))
    
    def test_create_counter_offer(self):
        """Test nurse can make counter offer above patient's price"""
        offer = NurseOffer.objects.create(
            request=self.request,
            nurse=self.nurse,
            offered_price=Decimal('100.00'),
            status=OfferStatus.COUNTER_OFFERED
        )
        
        self.assertEqual(offer.offered_price, Decimal('100.00'))
    
    def test_offer_below_patient_price_fails(self):
        """Test that offer below patient's price fails"""
        with self.assertRaises(ValueError):
            NurseOffer.objects.create(
                request=self.request,
                nurse=self.nurse,
                offered_price=Decimal('50.00')  # Below patient's offer
            )


class NurseRequestServiceTests(TestCase):
    """Tests for NurseRequestService business logic"""
    
    def setUp(self):
        """Set up test data"""
        from providers.models import Provider
        
        # Create patient
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            role=UserRole.PATIENT
        )
        
        # Create nurses
        self.nurse_user = User.objects.create_user(
            email='nurse@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Nurse',
            role=UserRole.PROVIDER
        )
        self.nurse = Provider.objects.create(
            user=self.nurse_user,
            provider_type='NURSE'
        )
        
        # Create service
        self.service = create_nursing_service(
            name='Wound Dressing',
            description='Professional wound care',
            base_price=Decimal('50.00'),
            duration_minutes=30
        )
    
    def test_create_request_flow(self):
        """Test complete request creation flow"""
        request = NurseRequestService.create_request(
            patient_user=self.patient_user,
            validated_data={
                'service': self.service,
                'patient_offered_price': Decimal('75.00'),
                'latitude': Decimal('36.7525'),
                'longitude': Decimal('3.0420'),
                'city': 'Algiers',
                'address_line': '',
                'notes': '',
                'base_price': self.service.price
            }
        )
        
        self.assertEqual(request.status, RequestStatus.SEARCHING)
        self.assertTrue(request.history.exists())
    
    def test_nurse_accept_request(self):
        """Test nurse accepting request at patient's price"""
        request = NurseServiceRequest.objects.create(
            patient_user=self.patient_user,
            service=self.service,
            base_price=self.service.price,
            patient_offered_price=Decimal('75.00'),
            status=RequestStatus.SEARCHING,
            latitude=Decimal('36.7525'),
            longitude=Decimal('3.0420'),
            city='Algiers'
        )
        
        offer = NurseRequestService.nurse_accept_request(
            request_obj=request,
            nurse=self.nurse
        )
        
        self.assertEqual(offer.offered_price, Decimal('75.00'))
        request.refresh_from_db()
        self.assertEqual(request.status, RequestStatus.NURSE_RESPONDED)
    
    def test_patient_accept_offer(self):
        """Test patient accepting a nurse offer"""
        request = NurseServiceRequest.objects.create(
            patient_user=self.patient_user,
            service=self.service,
            base_price=self.service.price,
            patient_offered_price=Decimal('75.00'),
            status=RequestStatus.NURSE_RESPONDED,
            latitude=Decimal('36.7525'),
            longitude=Decimal('3.0420'),
            city='Algiers'
        )
        
        offer = NurseOffer.objects.create(
            request=request,
            nurse=self.nurse,
            offered_price=Decimal('75.00'),
            status=OfferStatus.PENDING
        )
        
        updated_request = NurseRequestService.patient_accept_offer(
            request_obj=request,
            offer_id=offer.id
        )
        
        self.assertEqual(updated_request.status, RequestStatus.ACCEPTED)
        self.assertEqual(updated_request.accepted_nurse, self.nurse)
        self.assertEqual(updated_request.final_price, Decimal('75.00'))
        
        offer.refresh_from_db()
        self.assertEqual(offer.status, OfferStatus.ACCEPTED)


class PatientNurseRequestAPITests(APITestCase):
    """API tests for patient endpoints"""
    
    def setUp(self):
        """Set up test data and client"""
        self.patient_user = User.objects.create_user(
            email='patient@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Patient',
            role=UserRole.PATIENT
        )
        
        self.service = create_nursing_service(
            name='Wound Dressing',
            description='Professional wound care',
            base_price=Decimal('50.00'),
            duration_minutes=30
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient_user)
    
    def test_list_services(self):
        """Test listing available services"""
        response = self.client.get('/api/nurse-requests/services/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_request(self):
        """Test creating a new request"""
        data = {
            'service': self.service.id,
            'patient_offered_price': '75.00',
            'latitude': '36.7525',
            'longitude': '3.0420',
            'city': 'Algiers',
            'address_line': '123 Test Street',
            'notes': 'Test notes'
        }
        
        response = self.client.post(
            '/api/nurse-requests/patient/nurse-requests/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], RequestStatus.SEARCHING)
    
    def test_create_request_below_base_price_fails(self):
        """Test that request below base price fails"""
        data = {
            'service': self.service.id,
            'patient_offered_price': '30.00',  # Below base price
            'latitude': '36.7525',
            'longitude': '3.0420',
            'city': 'Algiers'
        }
        
        response = self.client.post(
            '/api/nurse-requests/patient/nurse-requests/',
            data
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
