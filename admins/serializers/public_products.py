"""
Public serializers for MediLink products.

These serializers are intentionally read-only and expose only
customer-facing fields for the public product catalog.
"""
from rest_framework import serializers

from admins.models.products import MediLinkProduct, MediLinkProductImage


class PublicProductImageSerializer(serializers.ModelSerializer):
    """Public serializer for product gallery images."""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = MediLinkProductImage
        fields = ['id', 'image_url', 'alt_text', 'display_order']

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class PublicProductListSerializer(serializers.ModelSerializer):
    """Public lightweight product serializer for catalog listings."""
    image_url = serializers.SerializerMethodField()
    gallery_images = PublicProductImageSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = MediLinkProduct
        fields = [
            'id',
            'name',
            'sku',
            'image_url',
            'gallery_images',
            'description',
            'brand',
            'manufacturer',
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
            'is_for_sale',
            'is_for_rent',
            'rental_price_per_day',
            'created_at',
        ]

    def get_image_url(self, obj):
        if not obj.image:
            first_gallery = obj.gallery_images.first()
            if not first_gallery or not first_gallery.image:
                return None
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_gallery.image.url)
            return first_gallery.image.url
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


class PublicProductDetailSerializer(serializers.ModelSerializer):
    """Public detailed product serializer for product detail pages."""
    image_url = serializers.SerializerMethodField()
    gallery_images = PublicProductImageSerializer(many=True, read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = MediLinkProduct
        fields = [
            'id',
            'name',
            'sku',
            'image_url',
            'gallery_images',
            'description',
            'brand',
            'manufacturer',
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
            'is_for_sale',
            'is_for_rent',
            'rental_price_per_day',
            'created_at',
            'updated_at',
        ]

    def get_image_url(self, obj):
        if not obj.image:
            first_gallery = obj.gallery_images.first()
            if not first_gallery or not first_gallery.image:
                return None
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_gallery.image.url)
            return first_gallery.image.url
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url
