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
from common.permissions import IsAdmin, IsVerifiedProvider
from rest_framework import serializers


class SpecialtyViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Specialties.
    
    GET /api/specialties/ - List all active specialties
    GET /api/specialties/{id}/ - Get specialty details
    POST /api/specialties/ - Create specialty (admin only)
    PUT /api/specialties/{id}/ - Update specialty (admin only)
    DELETE /api/specialties/{id}/ - Delete specialty (admin only)
    """
    queryset = Specialty.objects.filter(is_active=True)
    serializer_class = SpecialtySerializer
    permission_classes = [AllowAny]  # Public read, admin write
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['medical_domain', 'is_active']
    search_fields = ['title', 'title_ar', 'title_fr', 'title_en', 'description', 'description_ar', 'description_fr', 'description_en']
    ordering_fields = ['title', 'created_at']
    ordering = ['title']
    
    def get_permissions(self):
        """Admin required for write operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]
    
    def get_queryset(self):
        """Return active specialties for public, all for admin."""
        if self.request.user.is_authenticated and self.request.user.role == 'ADMIN':
            return Specialty.objects.all()
        return Specialty.objects.filter(is_active=True)


class DoctorSpecialtyViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Doctor Specialties.
    
    GET /api/doctor-specialties/ - List doctor specialties
    POST /api/doctor-specialties/ - Assign specialty to doctor
    DELETE /api/doctor-specialties/{id}/ - Remove specialty from doctor
    """
    serializer_class = DoctorSpecialtySerializer
    permission_classes = [IsAuthenticated, IsVerifiedProvider]
    
    def get_queryset(self):
        """Return specialties for the authenticated doctor."""
        try:
            doctor = self.request.user.provider_profile.doctor_profile
            return DoctorSpecialty.objects.filter(doctor=doctor)
        except Exception:
            return DoctorSpecialty.objects.none()
    
    def perform_create(self, serializer):
        """Assign specialty to the authenticated doctor."""
        try:
            doctor = self.request.user.provider_profile.doctor_profile
            specialty = serializer.validated_data['specialty']
            
            # Check if already assigned
            if DoctorSpecialty.objects.filter(doctor=doctor, specialty=specialty).exists():
                raise serializers.ValidationError('Specialty already assigned to this doctor.')
            
            serializer.save(doctor=doctor)
        except AttributeError:
            raise serializers.ValidationError('Doctor profile not found.')
        except Exception as e:
            raise serializers.ValidationError(f'Error assigning specialty: {str(e)}')
    
    @action(detail=False, methods=['post'])
    def assign(self, request):
        """
        Assign specialty to doctor.
        
        POST /api/doctor-specialties/assign/
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
                        {'error': 'Specialty already assigned to this doctor.'},
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
            except Exception as e:
                return Response(
                    {'error': f'Error assigning specialty: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
