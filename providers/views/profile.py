"""
Provider profile management views.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from providers.models import Provider
from common.permissions import IsProvider
from common.enums import ProviderType


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsProvider])
def provider_profile(request):
    """
    Get or update provider profile based on provider type.
    
    GET /api/provider/profile/ - Get provider profile
    PUT /api/provider/profile/ - Update provider profile
    PATCH /api/provider/profile/ - Partial update provider profile
    """
    try:
        provider = request.user.provider_profile
    except Provider.DoesNotExist:
        return Response(
            {'error': 'Provider profile not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Route to appropriate serializer based on provider type
    provider_type = provider.provider_type
    
    if request.method == 'GET':
        if provider_type == ProviderType.DOCTOR:
            from providers.serializers.doctor import DoctorSerializer
            try:
                doctor = provider.doctor_profile
                serializer = DoctorSerializer(doctor, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception:
                return Response(
                    {'error': 'Doctor profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif provider_type == ProviderType.NURSE:
            from providers.serializers.nurse import NurseSerializer
            try:
                nurse = provider.nurse_profile
                serializer = NurseSerializer(nurse, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception:
                return Response(
                    {'error': 'Nurse profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif provider_type == ProviderType.CLINIC:
            from providers.serializers.clinic import ClinicSerializer
            try:
                clinic = provider.clinic_profile
                serializer = ClinicSerializer(clinic, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception:
                return Response(
                    {'error': 'Clinic profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif provider_type == ProviderType.LABORATORY:
            from providers.serializers.laboratory import LaboratorySerializer
            try:
                laboratory = provider.laboratory_profile
                serializer = LaboratorySerializer(laboratory, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception:
                return Response(
                    {'error': 'Laboratory profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif provider_type == ProviderType.SELLER:
            from providers.serializers.seller import SellerSerializer
            try:
                seller = provider.seller_profile
                serializer = SellerSerializer(seller, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception:
                return Response(
                    {'error': 'Seller profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif provider_type == ProviderType.VTC:
            from providers.serializers.vtc import VTCSerializer
            try:
                vtc = provider.vtc_profile
                serializer = VTCSerializer(vtc, context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception:
                return Response(
                    {'error': 'VTC profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(
            {'error': f'Unsupported provider type: {provider_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    elif request.method in ['PUT', 'PATCH']:
        # Update profile based on provider type
        if provider_type == ProviderType.DOCTOR:
            from providers.serializers.doctor import DoctorSerializer
            try:
                doctor = provider.doctor_profile
                serializer = DoctorSerializer(
                    doctor,
                    data=request.data,
                    partial=(request.method == 'PATCH'),
                    context={"request": request},
                )
                if serializer.is_valid():
                    serializer.save()
                    # Recalculate profile completion after successful update
                    try:
                        request.user.recalculate_profile_completion()
                    except Exception:
                        pass
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'error': f'Error updating doctor profile: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif provider_type == ProviderType.NURSE:
            from providers.serializers.nurse import NurseSerializer
            try:
                nurse = provider.nurse_profile
                serializer = NurseSerializer(
                    nurse,
                    data=request.data,
                    partial=(request.method == 'PATCH'),
                    context={"request": request},
                )
                if serializer.is_valid():
                    serializer.save()
                    try:
                        request.user.recalculate_profile_completion()
                    except Exception:
                        pass
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'error': f'Error updating nurse profile: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif provider_type == ProviderType.CLINIC:
            from providers.serializers.clinic import ClinicSerializer
            try:
                clinic = provider.clinic_profile
                serializer = ClinicSerializer(
                    clinic,
                    data=request.data,
                    partial=(request.method == 'PATCH'),
                    context={"request": request},
                )
                if serializer.is_valid():
                    serializer.save()
                    try:
                        request.user.recalculate_profile_completion()
                    except Exception:
                        pass
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'error': f'Error updating clinic profile: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif provider_type == ProviderType.LABORATORY:
            from providers.serializers.laboratory import LaboratorySerializer
            try:
                laboratory = provider.laboratory_profile
                serializer = LaboratorySerializer(
                    laboratory,
                    data=request.data,
                    partial=(request.method == 'PATCH'),
                    context={"request": request},
                )
                if serializer.is_valid():
                    serializer.save()
                    try:
                        request.user.recalculate_profile_completion()
                    except Exception:
                        pass
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'error': f'Error updating laboratory profile: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif provider_type == ProviderType.SELLER:
            from providers.serializers.seller import SellerSerializer
            try:
                seller = provider.seller_profile
                serializer = SellerSerializer(
                    seller,
                    data=request.data,
                    partial=(request.method == 'PATCH'),
                    context={"request": request},
                )
                if serializer.is_valid():
                    serializer.save()
                    try:
                        request.user.recalculate_profile_completion()
                    except Exception:
                        pass
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'error': f'Error updating seller profile: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif provider_type == ProviderType.VTC:
            from providers.serializers.vtc import VTCSerializer
            try:
                vtc = provider.vtc_profile
                serializer = VTCSerializer(
                    vtc,
                    data=request.data,
                    partial=(request.method == 'PATCH'),
                    context={"request": request},
                )
                if serializer.is_valid():
                    serializer.save()
                    try:
                        request.user.recalculate_profile_completion()
                    except Exception:
                        pass
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response(
                    {'error': f'Error updating VTC profile: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': f'Unsupported provider type: {provider_type}'},
            status=status.HTTP_400_BAD_REQUEST
        )
