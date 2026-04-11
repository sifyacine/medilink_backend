from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User
from common.enums import UserRole
from common.enums import ProviderStatus
from providers.models import Provider
from providers.models.nurse import Nurse
from services.models import Service, NurseService, ServiceType

# Create your tests here.


class NurseServiceManagementTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			email='nurse-services@test.com',
			password='testpass123',
			role=UserRole.PROVIDER,
			first_name='Samia',
			last_name='Bendimerad',
			phone_number='+213555123457',
		)
		self.provider = Provider.objects.create(
			user=self.user,
			provider_type='NURSE',
			status=ProviderStatus.APPROVED,
		)
		self.nurse = Nurse.objects.create(
			provider=self.provider,
			first_name='Samia',
			last_name='Bendimerad',
			phone_number='+213555123457',
		)
		self.service = Service.objects.create(
			title='Home Nursing Visit',
			slug='home-nursing-visit',
			description='Home visit nursing support',
			service_type=ServiceType.NURSE,
			price=2500,
			duration_minutes=60,
			is_on_demand=True,
			is_home_service=True,
		)

	def test_nurse_can_attach_and_remove_service(self):
		self.client.force_authenticate(user=self.user)

		create_response = self.client.post(
			'/api/services/nurse-services/',
			{'service_id': self.service.id, 'is_available': True},
			format='json',
		)
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(NurseService.objects.filter(nurse=self.nurse, service=self.service).count(), 1)

		nurse_service = NurseService.objects.get(nurse=self.nurse, service=self.service)
		delete_response = self.client.delete(f'/api/services/nurse-services/{nurse_service.id}/')
		self.assertIn(delete_response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
		self.assertFalse(NurseService.objects.filter(nurse=self.nurse, service=self.service).exists())
