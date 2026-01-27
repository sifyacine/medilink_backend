"""
Services views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from services.models import Service, DoctorService, NurseService
from services.serializers import (
    ServiceSerializer,
    DoctorServiceSerializer,
    NurseServiceSerializer,
)
from common.permissions import IsAdmin, IsVerifiedProvider
from rest_framework import serializers


class ServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Services.
    
    GET /api/services/ - List all active services
    GET /api/services/{id}/ - Get service details
    POST /api/services/ - Create service (admin only)
    PUT /api/services/{id}/ - Update service (admin only)
    DELETE /api/services/{id}/ - Delete service (admin only)
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]  # Public read, admin write
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_home_service', 'is_active', 'specialty']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price', 'created_at']
    ordering = ['title']
    
    def get_permissions(self):
        """Admin required for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        """Return active services for public, all for admin."""
        if self.request.user.is_authenticated and self.request.user.role == 'ADMIN':
            return Service.objects.all()
        return Service.objects.filter(is_active=True)


class DoctorServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Doctor Services.
    
    GET /api/doctor-services/ - List doctor's services
    POST /api/doctor-services/ - Assign service to doctor
    PUT /api/doctor-services/{id}/ - Update doctor service
    DELETE /api/doctor-services/{id}/ - Remove service from doctor
    """
    serializer_class = DoctorServiceSerializer
    permission_classes = [IsAuthenticated, IsVerifiedProvider]
    
    def get_queryset(self):
        """Return services for the authenticated doctor."""
        try:
            doctor = self.request.user.provider_profile.doctor_profile
            return DoctorService.objects.filter(doctor=doctor)
        except Exception:
            return DoctorService.objects.none()
    
    def perform_create(self, serializer):
        """Assign service to the authenticated doctor."""
        try:
            doctor = self.request.user.provider_profile.doctor_profile
            service = serializer.validated_data['service']
            
            # Check if already assigned
            if DoctorService.objects.filter(doctor=doctor, service=service).exists():
                raise serializers.ValidationError('Service already assigned to this doctor.')
            
            serializer.save(doctor=doctor)
        except AttributeError:
            raise serializers.ValidationError('Doctor profile not found.')
        except Exception as e:
            raise serializers.ValidationError(f'Error assigning service: {str(e)}')


class NurseServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Nurse Services.
    
    GET /api/nurse-services/ - List nurse's services
    POST /api/nurse-services/ - Assign service to nurse
    PUT /api/nurse-services/{id}/ - Update nurse service
    DELETE /api/nurse-services/{id}/ - Remove service from nurse
    """
    serializer_class = NurseServiceSerializer
    permission_classes = [IsAuthenticated, IsVerifiedProvider]
    
    def get_queryset(self):
        """Return services for the authenticated nurse."""
        try:
            nurse = self.request.user.provider_profile.nurse_profile
            return NurseService.objects.filter(nurse=nurse)
        except Exception:
            return NurseService.objects.none()
    
    def perform_create(self, serializer):
        """Assign service to the authenticated nurse."""
        try:
            nurse = self.request.user.provider_profile.nurse_profile
            service = serializer.validated_data['service']
            
            # Check if already assigned
            if NurseService.objects.filter(nurse=nurse, service=service).exists():
                raise serializers.ValidationError('Service already assigned to this nurse.')
            
            serializer.save(nurse=nurse)
        except AttributeError:
            raise serializers.ValidationError('Nurse profile not found.')
        except Exception as e:
            raise serializers.ValidationError(f'Error assigning service: {str(e)}')
