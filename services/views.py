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
from common.permissions import IsAdmin, IsDoctor, IsNurse, IsDoctorOrClinic, IsDoctorOrClinicOrAdmin
from common.enums import ProviderType
from rest_framework import serializers


class ServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Services (Global Catalog).
    
    Services are a global catalog. Providers do not own services directly.
    Provider ↔ Service relationships are handled via linking tables (DoctorService, NurseService).
    
    Permissions:
    - Clinics: Can create services (global catalog)
    - Doctors: Can create services (auto-attached via DoctorService)
    - Nurses: Cannot create services
    - Admins: Full access
    - Public: Read-only access to active services
    
    GET /api/services/ - List all active services (public)
    GET /api/services/{id}/ - Get service details (public)
    POST /api/services/ - Create service (doctor/clinic/admin only)
    PUT /api/services/{id}/ - Update service (admin only)
    DELETE /api/services/{id}/ - Delete service (admin only)
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]  # Public read, restricted write
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_home_service', 'is_active', 'specialty', 'service_type']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price', 'created_at']
    ordering = ['title']
    
    def get_permissions(self):
        """
        Permissions based on action:
        - create: Doctor, Clinic, or Admin
        - update/partial_update/destroy: Admin only
        - read: Public
        """
        if self.action == 'create':
            return [IsAuthenticated(), IsDoctorOrClinicOrAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        """Return active services for public, all for admin."""
        if self.request.user.is_authenticated and self.request.user.role == 'ADMIN':
            return Service.objects.all()
        return Service.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        """
        Create a service with role-based auto-attach behavior:
        - Doctor creates: Create Service + auto-create DoctorService
        - Clinic creates: Create Service only (global catalog, no attachment)
        - Admin creates: Create Service only
        """
        try:
            service = serializer.save()
        except Exception as e:
            raise serializers.ValidationError({'detail': f'Error creating service: {str(e)}'})
        
        # Check if creator is a doctor - auto-attach the service
        user = self.request.user
        if user.role == 'PROVIDER':
            try:
                provider = user.provider_profile
                if provider.provider_type == ProviderType.DOCTOR:
                    doctor = provider.doctor_profile
                    # Auto-create DoctorService relationship
                    DoctorService.objects.get_or_create(
                        doctor=doctor,
                        service=service,
                        defaults={'is_available': True}
                    )
            except Exception:
                pass  # If doctor profile doesn't exist, just create the service
        
        return service


class DoctorServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Doctor Services.
    
    Allows doctors to manage which services they offer.
    
    GET /api/services/doctor-services/ - List doctor's services
    POST /api/services/doctor-services/ - Assign service to doctor
    PUT /api/services/doctor-services/{id}/ - Update doctor service (custom price, availability)
    DELETE /api/services/doctor-services/{id}/ - Remove service from doctor
    
    Permissions: Only authenticated doctors can access.
    """
    serializer_class = DoctorServiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return services for the authenticated doctor."""
        user = self.request.user
        if not user.is_authenticated:
            return DoctorService.objects.none()
        
        try:
            if hasattr(user, 'provider_profile'):
                provider = user.provider_profile
                if hasattr(provider, 'doctor_profile'):
                    doctor = provider.doctor_profile
                    return DoctorService.objects.filter(doctor=doctor).select_related('service')
        except Exception:
            pass
        
        return DoctorService.objects.none()
    
    def perform_create(self, serializer):
        """Assign service to the authenticated doctor."""
        user = self.request.user
        
        try:
            if not hasattr(user, 'provider_profile'):
                raise serializers.ValidationError({'detail': 'Provider profile not found.'})
            
            provider = user.provider_profile
            if not hasattr(provider, 'doctor_profile'):
                raise serializers.ValidationError({'detail': 'Doctor profile not found.'})
            
            doctor = provider.doctor_profile
            service = serializer.validated_data['service']
            
            # Check if already assigned
            if DoctorService.objects.filter(doctor=doctor, service=service).exists():
                raise serializers.ValidationError({'service': 'Service already assigned to this doctor.'})
            
            serializer.save(doctor=doctor)
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError({'detail': f'Error assigning service: {str(e)}'})


class NurseServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Nurse Services.
    
    Allows nurses to manage which services they offer.
    
    GET /api/services/nurse-services/ - List nurse's services
    POST /api/services/nurse-services/ - Assign service to nurse
    PUT /api/services/nurse-services/{id}/ - Update nurse service (custom price, availability)
    DELETE /api/services/nurse-services/{id}/ - Remove service from nurse
    
    Permissions: Only authenticated nurses can access.
    """
    serializer_class = NurseServiceSerializer
    permission_classes = [IsAuthenticated, IsNurse]
    
    def get_queryset(self):
        """Return services for the authenticated nurse."""
        try:
            nurse = self.request.user.provider_profile.nurse_profile
            return NurseService.objects.filter(nurse=nurse).select_related('service')
        except Exception:
            return NurseService.objects.none()
    
    def perform_create(self, serializer):
        """Assign service to the authenticated nurse."""
        try:
            nurse = self.request.user.provider_profile.nurse_profile
            service = serializer.validated_data['service']
            
            # Check if already assigned
            if NurseService.objects.filter(nurse=nurse, service=service).exists():
                raise serializers.ValidationError({'service': 'Service already assigned to this nurse.'})
            
            serializer.save(nurse=nurse)
        except AttributeError:
            raise serializers.ValidationError({'detail': 'Nurse profile not found.'})
        except AttributeError:
            raise serializers.ValidationError('Nurse profile not found.')
        except Exception as e:
            raise serializers.ValidationError(f'Error assigning service: {str(e)}')
