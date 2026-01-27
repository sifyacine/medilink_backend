"""
Address views and viewsets.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend

from address.models import Address
from address.serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Addresses.
    
    Supports Generic Foreign Key - can be attached to User, Provider, Doctor, Nurse, etc.
    
    GET /api/addresses/ - List addresses for authenticated user/provider
    POST /api/addresses/ - Create address
    PUT /api/addresses/{id}/ - Update address
    DELETE /api/addresses/{id}/ - Delete address
    """
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_primary', 'address_type', 'city', 'country']
    
    def get_queryset(self):
        """Return addresses for the authenticated user/provider."""
        user = self.request.user
        
        # Get ContentType for User
        user_content_type = ContentType.objects.get_for_model(user.__class__)
        
        # Get addresses for user
        user_addresses = Address.objects.filter(
            content_type=user_content_type,
            object_id=user.id
        )
        
        # If user is a provider, also get provider addresses
        if hasattr(user, 'provider_profile'):
            try:
                provider = user.provider_profile
                provider_content_type = ContentType.objects.get_for_model(provider.__class__)
                provider_addresses = Address.objects.filter(
                    content_type=provider_content_type,
                    object_id=provider.id
                )
                
                # Get doctor/nurse addresses if applicable
                doctor_addresses = Address.objects.none()
                nurse_addresses = Address.objects.none()
                
                if hasattr(provider, 'doctor_profile'):
                    doctor = provider.doctor_profile
                    doctor_content_type = ContentType.objects.get_for_model(doctor.__class__)
                    doctor_addresses = Address.objects.filter(
                        content_type=doctor_content_type,
                        object_id=doctor.id
                    )
                
                if hasattr(provider, 'nurse_profile'):
                    nurse = provider.nurse_profile
                    nurse_content_type = ContentType.objects.get_for_model(nurse.__class__)
                    nurse_addresses = Address.objects.filter(
                        content_type=nurse_content_type,
                        object_id=nurse.id
                    )
                
                return (user_addresses | provider_addresses | doctor_addresses | nurse_addresses).distinct()
            except Exception:
                pass
        
        return user_addresses
    
    def perform_create(self, serializer):
        """Create address and attach to a target object.

        Default behavior:
        - If client does NOT send content_type/object_id:
          attach the address to the current user account.
        - If client DOES send content_type/object_id and they are valid,
          keep them as-is so addresses can be attached to providers,
          doctor/nurse profiles, or other models.
        """
        user = self.request.user

        content_type = serializer.validated_data.get('content_type')
        object_id = serializer.validated_data.get('object_id')

        # If no explicit target was provided, attach to the current user
        if not content_type or not object_id:
            content_type = ContentType.objects.get_for_model(user.__class__)
            object_id = user.id

        serializer.save(content_type=content_type, object_id=object_id)
    
    def get_permissions(self):
        """Ensure user is authenticated; queryset already scopes to owner.

        Because get_queryset() only returns addresses linked to the current
        user/provider, additional object-level permission checks are not
        necessary here.
        """
        return [IsAuthenticated()]
