"""
Social media views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend

from social_media.models import SocialMediaLink
from social_media.serializers import SocialMediaLinkSerializer
from common.permissions import IsOwnerOrAdmin


class SocialMediaLinkViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Social Media Links.
    
    Supports Generic Foreign Key - can be attached to User, Provider, Doctor, Nurse, etc.
    
    GET /api/social-links/ - List social links for authenticated user/provider
    POST /api/social-links/ - Create social link
    PUT /api/social-links/{id}/ - Update social link
    DELETE /api/social-links/{id}/ - Delete social link
    """
    serializer_class = SocialMediaLinkSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['platform', 'is_visible']
    ordering_fields = ['display_order', 'platform']
    ordering = ['display_order', 'platform']
    
    def get_queryset(self):
        """Return social links for the authenticated user/provider."""
        user = self.request.user
        
        # Get ContentType for User
        user_content_type = ContentType.objects.get_for_model(user.__class__)
        
        # Get links for user
        user_links = SocialMediaLink.objects.filter(
            content_type=user_content_type,
            object_id=user.id
        )
        
        # If user is a provider, also get provider links
        if hasattr(user, 'provider_profile'):
            try:
                provider = user.provider_profile
                provider_content_type = ContentType.objects.get_for_model(provider.__class__)
                provider_links = SocialMediaLink.objects.filter(
                    content_type=provider_content_type,
                    object_id=provider.id
                )
                
                # Get doctor/nurse links if applicable
                doctor_links = SocialMediaLink.objects.none()
                nurse_links = SocialMediaLink.objects.none()
                
                if hasattr(provider, 'doctor_profile'):
                    doctor = provider.doctor_profile
                    doctor_content_type = ContentType.objects.get_for_model(doctor.__class__)
                    doctor_links = SocialMediaLink.objects.filter(
                        content_type=doctor_content_type,
                        object_id=doctor.id
                    )
                
                if hasattr(provider, 'nurse_profile'):
                    nurse = provider.nurse_profile
                    nurse_content_type = ContentType.objects.get_for_model(nurse.__class__)
                    nurse_links = SocialMediaLink.objects.filter(
                        content_type=nurse_content_type,
                        object_id=nurse.id
                    )
                
                return (user_links | provider_links | doctor_links | nurse_links).distinct()
            except Exception:
                pass
        
        return user_links
    
    def perform_create(self, serializer):
        """Create social link and attach to user/provider."""
        user = self.request.user
        
        # Determine target object (user, provider, doctor, nurse)
        target_object = user
        if hasattr(user, 'provider_profile'):
            try:
                provider = user.provider_profile
                # For providers, attach to provider by default
                # Can be changed via content_type and object_id in request
                if 'content_type' not in serializer.validated_data:
                    target_object = provider
            except Exception:
                pass
        
        # Set content_type and object_id
        content_type = ContentType.objects.get_for_model(target_object.__class__)
        serializer.save(
            content_type=content_type,
            object_id=target_object.id
        )
    
    def get_permissions(self):
        """Use IsOwnerOrAdmin for object-level permissions."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        # Allow public read for visible links
        if self.action == 'list' and self.request.query_params.get('public'):
            return [AllowAny()]
        return [IsAuthenticated()]
