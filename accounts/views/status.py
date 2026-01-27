"""Public endpoint to check account/provider status by email.

This is intended for frontend apps to check whether a provider is
PENDING, APPROVED, REFUSED (with reason), or SUSPENDED before allowing
login or showing next steps.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.contrib.auth import get_user_model

from providers.models import Provider
from providers.serializers.status import ProviderStatusSerializer


User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def check_account_status(request):
    """Return account + provider status for a given email.

    Request body:
    {
        "email": "provider@example.com"
    }

    Response (200):
    {
        "email": "provider@example.com",
        "exists": true,
        "role": "PROVIDER",              // or PATIENT/ADMIN
        "account_status": "ACTIVE",      // ACTIVE/SUSPENDED/DEACTIVATED
        "can_login": true,                // based on account_status & is_active
        "provider": {
            "status": "PENDING",         // PENDING/APPROVED/REFUSED/SUSPENDED
            "refusal_reason": null,
            "approved_at": null,
            "verified_at": null
        }
    }

    If the user does not exist, returns:
    {
        "email": "unknown@example.com",
        "exists": false
    }
    """
    email = (request.data.get("email") or "").strip().lower()

    if not email:
        return Response(
            {"email": ["This field is required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response(
            {"email": email, "exists": False},
            status=status.HTTP_200_OK,
        )

    data = {
        "email": user.email,
        "exists": True,
        "role": user.role,
        "account_status": user.account_status,
        "can_login": bool(user.can_login),
    }

    # If this is a provider, include provider status details
    try:
        provider = user.provider_profile
    except Provider.DoesNotExist:
        provider = None
    except Exception:
        provider = None

    if provider is not None:
        data["provider"] = ProviderStatusSerializer(provider).data
    else:
        data["provider"] = None

    return Response(data, status=status.HTTP_200_OK)
