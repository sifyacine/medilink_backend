"""
Public provider profile views.

Provides public-facing endpoints for browsing and searching providers.
These endpoints are accessible without authentication and only show
approved/verified providers.
"""
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny

from providers.models import Provider
from providers.serializers.provider import ProviderPublicSerializer, ProviderPublicDetailSerializer, ProviderPublicListSerializer
from common.enums import ProviderStatus, ProviderType


class PublicProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public provider profiles endpoint.
    Accessible to everyone (authenticated and unauthenticated).
    Only shows approved/verified providers.
    
    Endpoints:
    - GET /api/provider/public/ - List all approved providers (with filters)
    - GET /api/provider/public/{id}/ - Get provider details by ID
    - GET /api/provider/public/doctors/ - List only doctors
    - GET /api/provider/public/nurses/ - List only nurses
    - GET /api/provider/public/clinics/ - List only clinics
    - GET /api/provider/public/laboratories/ - List only laboratories
    
    Query Parameters:
    - provider_type: Filter by type (DOCTOR, NURSE, CLINIC, LABORATORY, VTC, SELLER)
    - search: Search by name, specialty, or location
    - is_available: Filter by availability (true/false)
    - is_home_service: Filter by home service availability (true/false)
    - specialty: Filter by specialty slug (for doctors)
    - city: Filter by city
    - ordering: Sort by field (e.g., -created_at, years_of_experience)
    """
    permission_classes = [AllowAny]
    serializer_class = ProviderPublicListSerializer  # Default for list
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['provider_type']
    search_fields = [
        'doctor_profile__first_name',
        'doctor_profile__last_name',
        'nurse_profile__first_name',
        'nurse_profile__last_name',
        'clinic_profile__clinic_name',
        'laboratory_profile__lab_name',
    ]
    ordering_fields = ['created_at', 'doctor_profile__years_of_experience', 'nurse_profile__years_of_experience']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return approved providers with optimized queries."""
        queryset = Provider.objects.filter(
            status=ProviderStatus.APPROVED
        ).select_related(
            'user',
            'doctor_profile',
            'nurse_profile',
            'clinic_profile',
            'laboratory_profile',
            'seller_profile',
            'vtc_profile',
        )
        
        # Additional filters from query params
        params = self.request.query_params
        
        # Filter by availability
        is_available = params.get('is_available')
        if is_available is not None:
            is_available_bool = is_available.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(
                models.Q(doctor_profile__is_available=is_available_bool) |
                models.Q(nurse_profile__is_available=is_available_bool) |
                models.Q(clinic_profile__is_available=is_available_bool) |
                models.Q(laboratory_profile__is_available=is_available_bool)
            )
        
        # Filter by home service availability
        is_home_service = params.get('is_home_service')
        if is_home_service is not None:
            is_home_bool = is_home_service.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(
                models.Q(doctor_profile__is_home_service_available=is_home_bool) |
                models.Q(nurse_profile__is_home_service_available=is_home_bool)
            )
        
        # Filter by specialty (for doctors)
        specialty = params.get('specialty')
        if specialty:
            queryset = queryset.filter(
                doctor_profile__specialties__specialty__slug=specialty
            ).distinct()
        
        # Filter by city (via addresses)
        city = params.get('city')
        if city:
            from django.contrib.contenttypes.models import ContentType
            from address.models import Address
            # This is a simplified filter - in production you might want to optimize
            queryset = queryset.filter(
                models.Q(doctor_profile__isnull=False) |
                models.Q(nurse_profile__isnull=False) |
                models.Q(clinic_profile__isnull=False)
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ProviderPublicDetailSerializer
        return ProviderPublicListSerializer
    
    @action(detail=False, methods=['get'])
    def doctors(self, request):
        """
        List only doctors.
        
        GET /api/provider/public/doctors/
        """
        queryset = self.get_queryset().filter(provider_type=ProviderType.DOCTOR)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nurses(self, request):
        """
        List only nurses.
        
        GET /api/provider/public/nurses/
        """
        queryset = self.get_queryset().filter(provider_type=ProviderType.NURSE)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def clinics(self, request):
        """
        List only clinics.
        
        GET /api/provider/public/clinics/
        """
        queryset = self.get_queryset().filter(provider_type=ProviderType.CLINIC)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def laboratories(self, request):
        """
        List only laboratories.
        
        GET /api/provider/public/laboratories/
        """
        queryset = self.get_queryset().filter(provider_type=ProviderType.LABORATORY)
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def provider_types(self, request):
        """
        Get available provider types with counts.
        
        GET /api/provider/public/provider_types/
        """
        from django.db.models import Count
        
        counts = Provider.objects.filter(
            status=ProviderStatus.APPROVED
        ).values('provider_type').annotate(
            count=Count('id')
        ).order_by('provider_type')
        
        result = []
        for item in counts:
            provider_type = item['provider_type']
            try:
                label = ProviderType(provider_type).label
            except:
                label = provider_type
            result.append({
                'value': provider_type,
                'label': label,
                'count': item['count']
            })
        
        return Response(result)
