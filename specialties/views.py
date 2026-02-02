"""
Specialties views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from specialties.models import Specialty, DoctorSpecialty
from specialties.serializers import (
    SpecialtySerializer,
    DoctorSpecialtySerializer,
    DoctorSpecialtyCreateSerializer,
)
from common.permissions import IsAdmin, IsDoctor, IsDoctorOrClinic
from common.enums import ProviderType
from rest_framework import serializers


class SpecialtyViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Specialties (Global Catalog).
    
    Specialties are a global catalog. Doctor ↔ Specialty relationships
    are handled via DoctorSpecialty linking table.
    
    Permissions:
    - Clinics: Can create specialties (global catalog)
    - Doctors: Can create specialties (auto-attached via DoctorSpecialty)
    - Nurses: Cannot create specialties
    - Admins: Full access
    - Public: Read-only access to active specialties
    
    GET /api/specialties/ - List all active specialties (public)
    GET /api/specialties/{id}/ - Get specialty details (public)
    POST /api/specialties/ - Create specialty (doctor/clinic/admin only)
    PUT /api/specialties/{id}/ - Update specialty (admin only)
    DELETE /api/specialties/{id}/ - Delete specialty (admin only)
    """
    queryset = Specialty.objects.filter(is_active=True)
    serializer_class = SpecialtySerializer
    permission_classes = [AllowAny]  # Public read, restricted write
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['medical_domain', 'is_active']
    search_fields = ['title', 'title_ar', 'title_fr', 'title_en', 'description', 'description_ar', 'description_fr', 'description_en']
    ordering_fields = ['title', 'created_at']
    ordering = ['title']
    
    def get_permissions(self):
        """
        Permissions based on action:
        - create: Doctor, Clinic, or Admin
        - update/partial_update/destroy: Admin only
        - read: Public
        """
        if self.action == 'create':
            return [IsAuthenticated(), IsDoctorOrClinic() | IsAdmin()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        """Return active specialties for public, all for admin."""
        if self.request.user.is_authenticated and self.request.user.role == 'ADMIN':
            return Specialty.objects.all()
        return Specialty.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        """
        Create a specialty with role-based auto-attach behavior:
        - Doctor creates: Create Specialty + auto-create DoctorSpecialty
        - Clinic creates: Create Specialty only (global catalog, no attachment)
        - Admin creates: Create Specialty only
        """
        specialty = serializer.save()
        
        # Check if creator is a doctor - auto-attach the specialty
        user = self.request.user
        if user.role == 'PROVIDER':
            try:
                provider = user.provider_profile
                if provider.provider_type == ProviderType.DOCTOR:
                    doctor = provider.doctor_profile
                    # Auto-create DoctorSpecialty relationship
                    DoctorSpecialty.objects.get_or_create(
                        doctor=doctor,
                        specialty=specialty,
                        defaults={'is_primary': False}
                    )
            except Exception:
                pass  # If doctor profile doesn't exist, just create the specialty
        
        return specialty


class DoctorSpecialtyViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Doctor Specialties.
    
    Allows doctors to manage their specialties.
    
    GET /api/specialties/doctor-specialties/ - List doctor's specialties
    POST /api/specialties/doctor-specialties/ - Assign specialty to doctor
    PUT /api/specialties/doctor-specialties/{id}/ - Update specialty (is_primary, years_of_experience)
    DELETE /api/specialties/doctor-specialties/{id}/ - Remove specialty from doctor
    
    Permissions: Only authenticated doctors can access.
    """
    serializer_class = DoctorSpecialtySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return specialties for the authenticated doctor."""
        user = self.request.user
        if not user.is_authenticated:
            return DoctorSpecialty.objects.none()
        
        try:
            if hasattr(user, 'provider_profile'):
                provider = user.provider_profile
                if hasattr(provider, 'doctor_profile'):
                    doctor = provider.doctor_profile
                    return DoctorSpecialty.objects.filter(doctor=doctor).select_related('specialty')
        except Exception:
            pass
        
        return DoctorSpecialty.objects.none()
    
    def perform_create(self, serializer):
        """Assign specialty to the authenticated doctor."""
        user = self.request.user
        
        try:
            if not hasattr(user, 'provider_profile'):
                raise serializers.ValidationError({'detail': 'Provider profile not found.'})
            
            provider = user.provider_profile
            if not hasattr(provider, 'doctor_profile'):
                raise serializers.ValidationError({'detail': 'Doctor profile not found.'})
            
            doctor = provider.doctor_profile
            specialty = serializer.validated_data['specialty']
            
            # Check if already assigned
            if DoctorSpecialty.objects.filter(doctor=doctor, specialty=specialty).exists():
                raise serializers.ValidationError({'specialty': 'Specialty already assigned to this doctor.'})
            
            # If setting as primary, unset other primaries
            is_primary = serializer.validated_data.get('is_primary', False)
            if is_primary:
                DoctorSpecialty.objects.filter(doctor=doctor, is_primary=True).update(is_primary=False)
            
            serializer.save(doctor=doctor)
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError({'detail': f'Error assigning specialty: {str(e)}'})
    
    @action(detail=False, methods=['post'])
    def assign(self, request):
        """
        Assign specialty to doctor (alternative endpoint).
        
        POST /api/specialties/doctor-specialties/assign/
        Body: {
            "specialty_id": 1,
            "is_primary": false,
            "years_of_experience": 5
        }
        """
        serializer = DoctorSpecialtyCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                doctor = request.user.provider_profile.doctor_profile
                specialty = serializer.validated_data['specialty_id']
                
                # Check if already assigned
                if DoctorSpecialty.objects.filter(doctor=doctor, specialty=specialty).exists():
                    return Response(
                        {'specialty': 'Specialty already assigned to this doctor.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # If setting as primary, unset other primaries
                if serializer.validated_data.get('is_primary'):
                    DoctorSpecialty.objects.filter(doctor=doctor, is_primary=True).update(is_primary=False)
                
                doctor_specialty = DoctorSpecialty.objects.create(
                    doctor=doctor,
                    specialty=specialty,
                    is_primary=serializer.validated_data.get('is_primary', False),
                    years_of_experience=serializer.validated_data.get('years_of_experience'),
                )
                
                return Response(
                    DoctorSpecialtySerializer(doctor_specialty).data,
                    status=status.HTTP_201_CREATED
                )
            except AttributeError:
                return Response(
                    {'detail': 'Doctor profile not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
