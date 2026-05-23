"""
Admin views for managing medical specialties and doctor-specialty assignments.

Endpoints:
  GET    /api/admin/specialties/                   List all specialties
  POST   /api/admin/specialties/                   Create specialty
  GET    /api/admin/specialties/{id}/              Specialty detail
  PATCH  /api/admin/specialties/{id}/              Update specialty (any field, all 3 languages)
  DELETE /api/admin/specialties/{id}/              Hard-delete specialty
  POST   /api/admin/specialties/{id}/toggle-active/ Flip is_active

  GET    /api/admin/doctor-specialties/            List all doctor ↔ specialty assignments
  POST   /api/admin/doctor-specialties/            Create assignment
  PATCH  /api/admin/doctor-specialties/{id}/       Update (is_primary, years_of_experience)
  DELETE /api/admin/doctor-specialties/{id}/       Remove assignment
"""
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admins.permissions import IsAdmin
from specialties.models import DoctorSpecialty, Specialty
from specialties.serializers import DoctorSpecialtySerializer, SpecialtyAdminSerializer


class AdminSpecialtyViewSet(viewsets.ModelViewSet):
    """
    Full CRUD management for Medical Specialties (admin only).

    Filters
    -------
    ?is_active=true|false
    ?medical_domain=<text>
    ?search=<text>  — searches title/description in all three languages
    ?ordering=title|created_at|updated_at|-title|-created_at|-updated_at
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = SpecialtyAdminSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'medical_domain']
    search_fields = [
        'title', 'title_en', 'title_ar', 'title_fr',
        'description', 'description_en', 'description_ar', 'description_fr',
        'medical_domain',
    ]
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['title']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return Specialty.objects.annotate(
            doctors_count=Count('specialty_doctors', distinct=True),
        ).order_by('title')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        title = instance.title
        instance.delete()
        return Response(
            {'success': True, 'message': f'Specialty "{title}" deleted.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        """Flip is_active on a specialty."""
        specialty = self.get_object()
        specialty.is_active = not specialty.is_active
        specialty.save(update_fields=['is_active', 'updated_at'])
        state = 'activated' if specialty.is_active else 'deactivated'
        return Response({
            'success': True,
            'is_active': specialty.is_active,
            'message': f'Specialty "{specialty.title}" {state}.',
        })


class AdminDoctorSpecialtyViewSet(viewsets.ModelViewSet):
    """
    Admin management of Doctor ↔ Specialty assignments.

    Filters
    -------
    ?doctor=<id>
    ?specialty=<id>
    ?is_primary=true|false
    ?search=<text>  — searches doctor name and specialty title
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = DoctorSpecialtySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_primary', 'specialty', 'doctor']
    search_fields = ['doctor__first_name', 'doctor__last_name', 'specialty__title']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return DoctorSpecialty.objects.select_related(
            'doctor__provider', 'specialty'
        ).order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        label = f'{instance.doctor.full_name} / {instance.specialty.title}'
        instance.delete()
        return Response(
            {'success': True, 'message': f'Assignment "{label}" removed.'},
            status=status.HTTP_200_OK,
        )
