"""
Admin serializers for invoice viewing.
"""
from rest_framework import serializers


class AdminInvoiceListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    invoice_number = serializers.CharField()
    status = serializers.CharField()
    invoice_type = serializers.CharField()
    provider_email = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField()
    due_date = serializers.DateField(allow_null=True)
    paid_at = serializers.DateTimeField(allow_null=True)
    created_at = serializers.DateTimeField()

    def get_provider_email(self, obj):
        try:
            return obj.provider.user.email
        except Exception:
            return None

    def get_provider_name(self, obj):
        try:
            u = obj.provider.user
            name = f"{u.first_name} {u.last_name}".strip()
            return name or u.email
        except Exception:
            return None

    def get_patient_email(self, obj):
        try:
            return obj.patient.email if obj.patient else None
        except Exception:
            return None

    def get_patient_name(self, obj):
        try:
            if obj.patient:
                name = f"{obj.patient.first_name} {obj.patient.last_name}".strip()
                return name or obj.patient.email
        except Exception:
            pass
        return None


class AdminInvoiceDetailSerializer(AdminInvoiceListSerializer):
    payment_method = serializers.CharField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
    updated_at = serializers.DateTimeField()
