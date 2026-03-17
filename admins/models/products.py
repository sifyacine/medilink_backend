"""
MediLink platform products and income tracking.

MediLinkProduct  – products/services sold by MediLink itself
MediLinkSale     – each sale event, recording platform revenue
"""
from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from accounts.models import User


class DiscountType(models.TextChoices):
    PERCENTAGE = 'PERCENTAGE', 'Percentage'
    FIXED = 'FIXED', 'Fixed Amount'


class ProductCategory(models.TextChoices):
    SUBSCRIPTION = 'SUBSCRIPTION', 'Provider Subscription'
    SOFTWARE = 'SOFTWARE', 'Software / SaaS'
    MEDICAL_SUPPLY = 'MEDICAL_SUPPLY', 'Medical Supply'
    EQUIPMENT = 'EQUIPMENT', 'Equipment'
    DIGITAL = 'DIGITAL', 'Digital Product'
    OTHER = 'OTHER', 'Other'


class SaleStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    REFUNDED = 'REFUNDED', 'Refunded'
    CANCELLED = 'CANCELLED', 'Cancelled'


class MediLinkProduct(models.Model):
    """
    A product or service sold by MediLink (not by providers).
    Examples: provider subscription plans, medical supplies, digital products.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=30,
        choices=ProductCategory.choices,
        default=ProductCategory.OTHER,
    )

    # Pricing
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='How much MediLink paid / cost price',
    )
    selling_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Price shown to buyers',
    )

    # Discount
    discount_type = models.CharField(
        max_length=15,
        choices=DiscountType.choices,
        blank=True,
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
    )

    # Ratings (0–5, can be set manually or computed from sales)
    rating = models.DecimalField(
        max_digits=3, decimal_places=2,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))],
    )
    rating_count = models.PositiveIntegerField(default=0)

    # Meta
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medilink_products',
        help_text='Admin who created this product (shown as MediLink in UI)',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'MediLink Product'
        verbose_name_plural = 'MediLink Products'

    def __str__(self):
        return self.name

    @property
    def effective_price(self):
        """Selling price after discount."""
        if not self.discount_type or self.discount_value <= 0:
            return self.selling_price
        if self.discount_type == DiscountType.PERCENTAGE:
            discount = self.selling_price * (self.discount_value / Decimal('100'))
        else:
            discount = self.discount_value
        return max(self.selling_price - discount, Decimal('0'))

    @property
    def profit_margin(self):
        ep = self.effective_price
        if ep <= 0:
            return Decimal('0')
        return ((ep - self.cost_price) / ep * 100).quantize(Decimal('0.01'))


class MediLinkSale(models.Model):
    """
    Records a single income event for MediLink.
    Can be linked to a product (for product sales) or standalone
    (e.g., manual subscription fee entry, provider subscription charge).
    """
    product = models.ForeignKey(
        MediLinkProduct,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sales',
    )
    # Optional: the buyer (provider or patient user)
    buyer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='medilink_purchases',
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    status = models.CharField(
        max_length=15,
        choices=SaleStatus.choices,
        default=SaleStatus.COMPLETED,
    )
    notes = models.TextField(blank=True)
    reference = models.CharField(
        max_length=100, blank=True,
        help_text='External reference / transaction ID',
    )
    sale_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recorded_sales',
    )

    class Meta:
        ordering = ['-sale_date']
        verbose_name = 'MediLink Sale'
        verbose_name_plural = 'MediLink Sales'

    def __str__(self):
        product_name = self.product.name if self.product else 'Manual Entry'
        return f'{product_name} – {self.total_amount}'
