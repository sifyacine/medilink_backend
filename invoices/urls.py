"""
Invoice URLs for the Medilink platform.

Routes:
- /api/invoices/ - Invoice CRUD and actions
- /api/invoices/payments/ - Payment management
- /api/invoices/my/ - Patient's invoices
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import InvoiceViewSet, PaymentViewSet, PatientInvoiceListView


router = DefaultRouter()
router.register(r'', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    # Patient's invoices (simplified view)
    path('my/', PatientInvoiceListView.as_view(), name='my-invoices'),
    
    # Router URLs
    path('', include(router.urls)),
]
