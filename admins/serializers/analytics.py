"""
Admin serializers for analytics responses.
"""
from rest_framework import serializers


class OverviewStatsSerializer(serializers.Serializer):
    """Platform overview statistics."""
    total_users = serializers.IntegerField()
    total_providers = serializers.IntegerField()
    total_patients = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    pending_providers = serializers.IntegerField()
    active_users = serializers.IntegerField()
    suspended_users = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    new_users_this_month = serializers.IntegerField()
    new_providers_this_month = serializers.IntegerField()


class TimeSeriesPointSerializer(serializers.Serializer):
    """Single data point for a time-series chart."""
    date = serializers.DateField()
    count = serializers.IntegerField()


class ProviderTypeStatSerializer(serializers.Serializer):
    """Provider count broken down by type with approval breakdown."""
    provider_type = serializers.CharField()
    provider_type_display = serializers.CharField()
    total = serializers.IntegerField()
    approved = serializers.IntegerField()
    pending = serializers.IntegerField()
    refused = serializers.IntegerField()
    suspended = serializers.IntegerField()


class AppointmentStatusStatSerializer(serializers.Serializer):
    """Appointment count broken down by status."""
    status = serializers.CharField()
    count = serializers.IntegerField()


class RevenueByMonthSerializer(serializers.Serializer):
    """Monthly revenue data point."""
    month = serializers.DateField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    count = serializers.IntegerField()


class PaymentMethodStatSerializer(serializers.Serializer):
    """Revenue broken down by payment method."""
    payment_method = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    count = serializers.IntegerField()
