"""
Serializers for MediLink platform products and income tracking.
"""
from decimal import Decimal

from rest_framework import serializers

from admins.models.products import MediLinkProduct, MediLinkSale


class MediLinkProductSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for MediLink products."""

    added_by_display = serializers.SerializerMethodField()
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    profit_margin = serializers.DecimalField(
        max_digits=6, decimal_places=2, read_only=True
    )
    rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)

    class Meta:
        model = MediLinkProduct
        fields = [
            'id',
            'name',
            'sku',
            'description',
            'brand',
            'manufacturer',
            'category',
            'cost_price',
            'selling_price',
            'currency',
            'discount_type',
            'discount_value',
            'stock_quantity',
            'low_stock_threshold',
            'effective_price',
            'profit_margin',
            'rating',
            'rating_count',
            'is_active',
            'added_by',
            'added_by_display',
            'updated_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['currency', 'rating', 'rating_count', 'added_by', 'added_by_display', 'updated_by', 'effective_price', 'profit_margin', 'created_at', 'updated_at']

    def get_added_by_display(self, obj):
        """Show MediLink for admin-created products, seller info otherwise."""
        if obj.added_by is None or getattr(obj.added_by, 'role', None) == 'ADMIN':
            return 'MediLink'
        return obj.added_by.get_full_name() or obj.added_by.email

    def validate(self, data):
        """Ensure discount_value is set when discount_type is provided."""
        discount_type = data.get('discount_type', getattr(self.instance, 'discount_type', ''))
        discount_value = data.get('discount_value', getattr(self.instance, 'discount_value', Decimal('0')))
        if discount_type and (discount_value is None or discount_value <= 0):
            raise serializers.ValidationError(
                {'discount_value': 'A positive discount value is required when a discount type is set.'}
            )
        if discount_type == 'PERCENTAGE' and discount_value > 100:
            raise serializers.ValidationError({'discount_value': 'Percentage discount cannot exceed 100.'})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['added_by'] = request.user
            validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class MediLinkProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listing."""

    added_by_display = serializers.SerializerMethodField()
    effective_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = MediLinkProduct
        fields = [
            'id',
            'name',
            'sku',
            'category',
            'currency',
            'selling_price',
            'discount_type',
            'discount_value',
            'effective_price',
            'stock_quantity',
            'low_stock_threshold',
            'is_low_stock',
            'rating',
            'rating_count',
            'is_active',
            'added_by_display',
            'created_at',
        ]

    def get_added_by_display(self, obj):
        if obj.added_by is None or getattr(obj.added_by, 'role', None) == 'ADMIN':
            return 'MediLink'
        return obj.added_by.get_full_name() or obj.added_by.email


class MediLinkSaleSerializer(serializers.ModelSerializer):
    """Serializer for income/sale records."""

    product_name = serializers.SerializerMethodField()
    buyer_email = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()
    recorded_by_display = serializers.SerializerMethodField()

    class Meta:
        model = MediLinkSale
        fields = [
            'id',
            'product',
            'product_name',
            'buyer',
            'buyer_email',
            'buyer_name',
            'quantity',
            'unit_price',
            'total_amount',
            'status',
            'notes',
            'reference',
            'sale_date',
            'recorded_by',
            'recorded_by_display',
        ]
        read_only_fields = ['sale_date', 'recorded_by', 'recorded_by_display']

    def get_product_name(self, obj):
        return obj.product.name if obj.product else 'Manual Entry'

    def get_buyer_email(self, obj):
        return obj.buyer.email if obj.buyer else None

    def get_buyer_name(self, obj):
        if not obj.buyer:
            return None
        return obj.buyer.get_full_name() or obj.buyer.email

    def get_recorded_by_display(self, obj):
        if obj.recorded_by:
            return obj.recorded_by.get_full_name() or obj.recorded_by.email
        return 'MediLink'

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['recorded_by'] = request.user
        return super().create(validated_data)
