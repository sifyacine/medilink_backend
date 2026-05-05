from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from providers.models.provider import Provider
from notifications.dashboard_services import DashboardStatsService


class ProviderDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            provider = Provider.objects.get(user=request.user)
        except Provider.DoesNotExist:
            return Response({"detail": "Provider profile not found."}, status=403)
        data = DashboardStatsService.get_full_dashboard(provider)
        return Response(data)
