"""
URL configuration for the appointments app.

Endpoints:
- /appointments/ - Appointment CRUD
- /appointment-reminders/ - Reminder management
- /provider-availability/ - Provider availability schedules
- /provider-time-off/ - Provider time off periods
- /appointment-choices/ - Get status/location type choices
- /available-slots/ - Get available appointment slots
- /provider-schedule/ - Get provider's complete schedule
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentViewSet,
    AppointmentReminderViewSet,
    AppointmentChoicesView,
    ProviderAvailabilityViewSet,
    ProviderTimeOffViewSet,
    AvailableSlotsView,
    ProviderScheduleView,
)

router = DefaultRouter()
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'appointment-reminders', AppointmentReminderViewSet, basename='appointment-reminder')
router.register(r'provider-availability', ProviderAvailabilityViewSet, basename='provider-availability')
router.register(r'provider-time-off', ProviderTimeOffViewSet, basename='provider-time-off')

urlpatterns = [
    path('', include(router.urls)),
    path('appointment-choices/', AppointmentChoicesView.as_view(), name='appointment-choices'),
    path('available-slots/', AvailableSlotsView.as_view(), name='available-slots'),
    path('provider-schedule/', ProviderScheduleView.as_view(), name='provider-schedule'),
]
