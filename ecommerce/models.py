"""
E-Commerce module models.

Layered design:
  A. Admin master config (global reusable library)  -> UnitType, Unit, Attribute,
     AttributeOption, ProductTemplate, TemplateAttribute
  B. Merchant catalog                               -> Product, ProductVariantGroup,
     ProductVariantGroupValue, ProductImage, ProductVariant, VariantAttributeValue
  C. Inventory                                      -> StockMovement, LowStockAlert
  D. Storefront & discovery                         -> MerchantStoreSetting,
     ProductPromotion, ProductReview, Wishlist, WishlistItem
  E. Cart & Orders (admin-brokered area routing)    -> Cart, CartItem, Order,
     OrderVendorAssignment, OrderItem, OrderStatusLog, Delivery, ReturnRequest

Merchant / Vendor == user.BusinessFamily. Discovery reuses the residential code from the
residence configuration. Wallet is out of scope; the money-flow breakdown is modelled on
the order so a future wallet can settle it.
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from simple_history.models import HistoricalRecords

from common.models import AuditMixin, SoftDeleteMixin


# =====================================================================================
# A. ADMIN MASTER CONFIG (global reusable library)
# =====================================================================================
class UnitType(AuditMixin, SoftDeleteMixin):
    """A family of units, e.g. 'Shoe Size System', 'Weight'."""
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Unit(AuditMixin, SoftDeleteMixin):
    """A member of a UnitType, e.g. US / UK / EU under 'Shoe Size System'."""
    unit_type = models.ForeignKey(UnitType, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20, null=True, blank=True)
    is_base = models.BooleanField(default=False, help_text="Reference unit of the family.")
    conversion_factor = models.DecimalField(max_digits=14, decimal_places=6, default=Decimal('1'))
    sort_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['unit_type', 'sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['unit_type', 'name'],
                condition=models.Q(is_deleted=False),
                name='uq_unit_name_per_type',
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.unit_type.name})"


class Attribute(AuditMixin, SoftDeleteMixin):
    """Global attribute definition, e.g. 'Color' (text), 'Size' (dropdown)."""
    INPUT_TEXT = 'text'
    INPUT_NUMBER = 'number'
    INPUT_DROPDOWN = 'dropdown'
    INPUT_BOOLEAN = 'boolean'
    INPUT_DATE = 'date'
    INPUT_COLOR = 'color'
    INPUT_TYPE_CHOICES = [
        (INPUT_TEXT, 'Text'),
        (INPUT_NUMBER, 'Number'),
        (INPUT_DROPDOWN, 'Dropdown'),
        (INPUT_BOOLEAN, 'Boolean'),
        (INPUT_DATE, 'Date'),
        (INPUT_COLOR, 'Color'),
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)
    input_type = models.CharField(max_length=20, choices=INPUT_TYPE_CHOICES, default=INPUT_TEXT)
    unit_type = models.ForeignKey(
        UnitType, on_delete=models.SET_NULL, null=True, blank=True, related_name='attributes'
    )
    help_text = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['name']

    @property
    def has_options(self):
        return self.input_type in (self.INPUT_DROPDOWN, self.INPUT_COLOR)

    def __str__(self):
        return self.name


class AttributeOption(AuditMixin, SoftDeleteMixin):
    """
    Choices for dropdown attributes, e.g. Size -> 7, 8, 9.

    Values may be scoped to a Unit: e.g. UK sizes 7/8/9/10 vs US sizes 8/9/10.
    ``unit = NULL`` means the value applies to all units (e.g. Color = Black/White/Red).
    When a merchant selects a unit, only that unit's options (+ all-unit options) show.
    """
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='options')
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, null=True, blank=True, related_name='options',
        help_text="Null = applies to all units.",
    )
    value = models.CharField(max_length=100)
    display_value = models.CharField(max_length=100, null=True, blank=True)
    color_hex = models.CharField(max_length=7, null=True, blank=True, help_text="e.g. #1E63FF for swatches")
    sort_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['attribute', 'sort_order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['attribute', 'unit', 'value'],
                condition=models.Q(is_deleted=False),
                name='uq_option_value_per_attribute_unit',
            )
        ]

    def __str__(self):
        unit = f" {self.unit.name}" if self.unit_id else ""
        return f"{self.attribute.name}: {self.display_value or self.value}{unit}"


class ProductTemplate(AuditMixin, SoftDeleteMixin):
    """Admin-defined product blueprint, e.g. 'Shoes'. Holds commission config."""
    COMMISSION_PERCENT = 'percent'
    COMMISSION_FLAT = 'flat'
    COMMISSION_TYPE_CHOICES = [
        (COMMISSION_PERCENT, 'Percent'),
        (COMMISSION_FLAT, 'Flat'),
    ]

    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=100, unique=True)
    category = models.ForeignKey(
        'configuration.Node', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='product_templates',
    )
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='ecommerce/templates/', null=True, blank=True)
    commission_type = models.CharField(
        max_length=10, choices=COMMISSION_TYPE_CHOICES, default=COMMISSION_PERCENT
    )
    commission_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Percent (e.g. 5.00 = 5%) or flat amount per unit.",
    )
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['name']

    def commission_for(self, vendor_unit_price):
        """Commission amount for one unit at a given vendor price."""
        price = Decimal(vendor_unit_price or 0)
        if self.commission_type == self.COMMISSION_PERCENT:
            return (price * self.commission_value / Decimal('100')).quantize(Decimal('0.01'))
        return Decimal(self.commission_value).quantize(Decimal('0.01'))

    def __str__(self):
        return self.name


class TemplateAttribute(AuditMixin, SoftDeleteMixin):
    """Which attributes a template uses + how they behave in the form."""
    template = models.ForeignKey(
        ProductTemplate, on_delete=models.CASCADE, related_name='template_attributes'
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT, related_name='template_links')
    is_required = models.BooleanField(default=False)
    is_variant_defining = models.BooleanField(
        default=False, help_text="Value creates separate sellable variants (Color, Size)."
    )
    is_image_defining = models.BooleanField(
        default=False, help_text="Value forms the image-sharing group (Color=True)."
    )
    default_unit = models.ForeignKey(
        Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='template_attributes'
    )
    sort_order = models.PositiveIntegerField(default=1)

    history = HistoricalRecords()

    class Meta:
        ordering = ['template', 'sort_order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['template', 'attribute'],
                condition=models.Q(is_deleted=False),
                name='uq_attribute_per_template',
            )
        ]

    def __str__(self):
        return f"{self.template.name} / {self.attribute.name}"


# =====================================================================================
# B. MERCHANT CATALOG
# =====================================================================================
class Product(AuditMixin, SoftDeleteMixin):
    """A merchant's product instance of an admin template."""
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_OUT_OF_STOCK = 'out_of_stock'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_OUT_OF_STOCK, 'Out of Stock'),
    ]

    business_family = models.ForeignKey(
        'user.BusinessFamily', on_delete=models.CASCADE, related_name='products'
    )
    template = models.ForeignKey(ProductTemplate, on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(
        'configuration.Node', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products',
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100)
    slug = models.SlugField(max_length=220, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    base_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))]
    )
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    hsn_code = models.CharField(max_length=20, null=True, blank=True)
    min_order_qty = models.PositiveIntegerField(default=1)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    preparation_time_minutes = models.PositiveIntegerField(default=0)
    # Delivery time for THIS product (0 = fall back to the store's default_delivery_time_minutes).
    delivery_time_minutes = models.PositiveIntegerField(default=0)
    # Cached from the merchant's business residential_code -> fast same-area feed filter.
    area_code = models.CharField(max_length=120, null=True, blank=True, db_index=True)
    # template + variant-defining attribute values -> groups identical products for price range.
    grouping_key = models.CharField(max_length=180, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_products'
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['business_family', 'sku'],
                condition=models.Q(is_deleted=False),
                name='uq_product_sku_per_business',
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductVariantGroup(AuditMixin):
    """Image/color-sharing level. All sizes of one color share this group's images."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variant_groups')
    label = models.CharField(max_length=150)
    sort_order = models.PositiveIntegerField(default=1)

    history = HistoricalRecords()

    class Meta:
        ordering = ['product', 'sort_order', 'id']

    def __str__(self):
        return f"{self.product.name} / {self.label}"


class ProductVariantGroupValue(AuditMixin):
    """The image-defining attribute value(s) defining a group, e.g. color=Blue."""
    variant_group = models.ForeignKey(
        ProductVariantGroup, on_delete=models.CASCADE, related_name='values'
    )
    template_attribute = models.ForeignKey(TemplateAttribute, on_delete=models.PROTECT)
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT)
    option = models.ForeignKey(
        AttributeOption, on_delete=models.SET_NULL, null=True, blank=True
    )
    value_text = models.CharField(max_length=255, null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.variant_group.label}: {self.attribute.name}"


class ProductImage(AuditMixin):
    """Variant-group-wise images. variant_group NULL => product-level generic image."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant_group = models.ForeignKey(
        ProductVariantGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='images'
    )
    image = models.ImageField(upload_to='ecommerce/products/')
    alt_text = models.CharField(max_length=150, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=1)

    history = HistoricalRecords()

    class Meta:
        ordering = ['product', 'sort_order', 'id']

    def __str__(self):
        return f"Image #{self.id} of {self.product.name}"


class ProductVariant(AuditMixin, SoftDeleteMixin):
    """The actual sellable SKU, e.g. Blue / US-8."""
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_OUT_OF_STOCK = 'out_of_stock'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
        (STATUS_OUT_OF_STOCK, 'Out of Stock'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_group = models.ForeignKey(
        ProductVariantGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='variants'
    )
    # Identifies "the same variant across vendors": template + sorted variant-defining values.
    # Lets the admin find every vendor who stocks this exact variant when routing an order.
    concept_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    sku = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0'))]
    )
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_qty = models.IntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=0)
    weight_grams = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    is_default = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        ordering = ['product', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'sku'],
                condition=models.Q(is_deleted=False),
                name='uq_variant_sku_per_product',
            )
        ]

    def __str__(self):
        return f"{self.product.name} / {self.sku}"


class VariantAttributeValue(AuditMixin):
    """Relational value store: one row per attribute per variant (color=Blue, size=8 US)."""
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='attribute_values'
    )
    template_attribute = models.ForeignKey(TemplateAttribute, on_delete=models.PROTECT)
    attribute = models.ForeignKey(Attribute, on_delete=models.PROTECT)
    option = models.ForeignKey(AttributeOption, on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    value_text = models.CharField(max_length=255, null=True, blank=True)
    value_number = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    value_bool = models.BooleanField(null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['variant', 'template_attribute'],
                name='uq_value_per_variant_attribute',
            )
        ]

    @property
    def display(self):
        if self.option_id:
            label = self.option.display_value or self.option.value
        elif self.value_text is not None:
            label = self.value_text
        elif self.value_number is not None:
            label = str(self.value_number)
        elif self.value_bool is not None:
            label = 'Yes' if self.value_bool else 'No'
        elif self.value_date is not None:
            label = str(self.value_date)
        else:
            label = ''
        if self.unit_id:
            label = f"{self.unit.name} {label}".strip()
        return label

    def __str__(self):
        return f"{self.attribute.name}: {self.display}"


# =====================================================================================
# C. INVENTORY
# =====================================================================================
class StockMovement(AuditMixin):
    """Every stock change with running balance (SRS 7.2.2)."""
    PURCHASE = 'purchase'
    SALE = 'sale'
    ADJUSTMENT = 'adjustment'
    RETURN = 'return'
    WRITE_OFF = 'write_off'
    DAMAGED = 'damaged'
    EXPIRED = 'expired'
    MOVEMENT_TYPE_CHOICES = [
        (PURCHASE, 'Purchase / Restock'),
        (SALE, 'Sale'),
        (ADJUSTMENT, 'Manual Adjustment'),
        (RETURN, 'Return'),
        (WRITE_OFF, 'Write Off'),
        (DAMAGED, 'Damaged'),
        (EXPIRED, 'Expired'),
    ]

    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='stock_movements'
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity_delta = models.IntegerField(help_text="+in / -out")
    balance_after = models.IntegerField()
    reason = models.CharField(max_length=255, null=True, blank=True)
    reference_type = models.CharField(max_length=30, null=True, blank=True)
    reference_id = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements'
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.variant.sku} {self.quantity_delta:+d} ({self.movement_type})"


class LowStockAlert(AuditMixin):
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='low_stock_alerts'
    )
    threshold = models.PositiveIntegerField()
    stock_at_alert = models.IntegerField()
    is_resolved = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Low stock: {self.variant.sku} ({self.stock_at_alert})"


# =====================================================================================
# D. STOREFRONT & DISCOVERY
# =====================================================================================
class MerchantStoreSetting(AuditMixin):
    business_family = models.OneToOneField(
        'user.BusinessFamily', on_delete=models.CASCADE, related_name='store_setting'
    )
    is_online = models.BooleanField(default=True, help_text="Vendor's products eligible for area listings.")
    is_open = models.BooleanField(default=True, help_text="Accepting orders now.")
    min_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    # Store-wide default delivery time; a product's own delivery_time_minutes overrides it.
    default_delivery_time_minutes = models.PositiveIntegerField(default=0)
    return_policy = models.TextField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Store settings: {self.business_family.name}"


class ProductPromotion(AuditMixin):
    SPONSORED = 'sponsored'
    FEATURED = 'featured'
    PROMOTION_TYPE_CHOICES = [
        (SPONSORED, 'Sponsored'),
        (FEATURED, 'Featured'),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name='promotions'
    )
    business_family = models.ForeignKey(
        'user.BusinessFamily', on_delete=models.CASCADE, null=True, blank=True,
        related_name='promotions',
    )
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPE_CHOICES, default=SPONSORED)
    priority_boost = models.IntegerField(default=0)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_promotions'
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ['-priority_boost', '-start_at']

    def __str__(self):
        return f"{self.get_promotion_type_display()} #{self.id}"


class ProductReview(AuditMixin, SoftDeleteMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='product_reviews')
    order_item = models.ForeignKey(
        'OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    title = models.CharField(max_length=150, null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user', 'order_item'],
                condition=models.Q(is_deleted=False),
                name='uq_review_per_user_orderitem',
            )
        ]

    def __str__(self):
        return f"{self.rating}* {self.product.name}"


class Wishlist(AuditMixin):
    user = models.OneToOneField('user.User', on_delete=models.CASCADE, related_name='wishlist')

    def __str__(self):
        return f"Wishlist of {self.user.full_name}"


class WishlistItem(AuditMixin):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='wishlist_items')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['wishlist', 'variant'], name='uq_wishlist_variant')
        ]

    def __str__(self):
        return f"{self.wishlist.user.full_name} loves {self.variant.sku}"


# =====================================================================================
# E. CART & ORDERS (admin-brokered area routing)
# =====================================================================================
class Cart(AuditMixin):
    STATUS_ACTIVE = 'active'
    STATUS_ORDERED = 'ordered'
    STATUS_ABANDONED = 'abandoned'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ORDERED, 'Ordered'),
        (STATUS_ABANDONED, 'Abandoned'),
    ]

    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='carts')
    # Vendor-agnostic: the buyer shops product concepts (vendor is chosen later by the admin).
    business_family = models.ForeignKey(
        'user.BusinessFamily', on_delete=models.SET_NULL, null=True, blank=True, related_name='carts'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status='active'),
                name='uq_active_cart_per_user',
            )
        ]

    def __str__(self):
        return f"Cart #{self.id} of {self.user.full_name}"


class CartItem(AuditMixin):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'variant'], name='uq_cartitem_variant')
        ]

    def __str__(self):
        return f"{self.quantity} x {self.variant.sku}"


class Order(AuditMixin, SoftDeleteMixin):
    STATUS_PLACED = 'placed'
    STATUS_PENDING_ASSIGNMENT = 'pending_assignment'
    STATUS_ASSIGNED = 'assigned'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_AGENT_ASSIGNED = 'agent_assigned'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_RETURN_REQUESTED = 'return_requested'
    STATUS_RETURNED = 'returned'
    STATUS_COMPLETED = 'completed'
    STATUS_CHOICES = [
        (STATUS_PLACED, 'Placed'),
        (STATUS_PENDING_ASSIGNMENT, 'Pending Assignment'),
        (STATUS_ASSIGNED, 'Assigned to Vendor'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_AGENT_ASSIGNED, 'Agent Assigned'),
        (STATUS_PICKED_UP, 'Picked Up'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_RETURN_REQUESTED, 'Return Requested'),
        (STATUS_RETURNED, 'Returned'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    PAYMENT_PENDING = 'pending'
    PAYMENT_PAID = 'paid'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_PENDING, 'Pending'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_REFUNDED, 'Refunded'),
    ]

    order_no = models.CharField(max_length=30, unique=True)
    buyer = models.ForeignKey('user.User', on_delete=models.PROTECT, related_name='orders')
    area_node = models.ForeignKey(
        'configuration.Node', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='area_orders',
    )
    # Vendor who listed the ordered product (reference only, hidden from buyer).
    listing_business_family = models.ForeignKey(
        'user.BusinessFamily', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='listed_orders',
    )
    # Fulfilling vendor -- assigned by the area admin (null until a vendor accepts).
    business_family = models.ForeignKey(
        'user.BusinessFamily', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='received_orders',
    )
    assigned_admin = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='routed_orders'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    delivery_address = models.ForeignKey(
        'user.ResidentialDetails', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders',
    )
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)

    # Price is a RANGE at placement (many vendors, different prices); finalized on assignment.
    estimated_min_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    estimated_max_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    is_price_final = models.BooleanField(default=False)

    # Money-flow breakdown (filled when a vendor is assigned; no wallet yet, but fully modelled).
    vendor_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLACED)
    payment_status = models.CharField(
        max_length=15, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING
    )
    placed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_no


class OrderVendorAssignment(AuditMixin):
    """Admin routing history -- an order can be offered to multiple vendors over time."""
    OFFERED = 'offered'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    REASSIGNED = 'reassigned'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (OFFERED, 'Offered'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (REASSIGNED, 'Reassigned'),
        (CANCELLED, 'Cancelled'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='vendor_assignments')
    business_family = models.ForeignKey(
        'user.BusinessFamily', on_delete=models.PROTECT, related_name='order_assignments'
    )
    area_node = models.ForeignKey(
        'configuration.Node', on_delete=models.SET_NULL, null=True, blank=True
    )
    assigned_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_assignments_made'
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=OFFERED)
    responded_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order.order_no} -> {self.business_family.name} ({self.status})"


class OrderItem(AuditMixin):
    """Line items with historical snapshots + per-line commission breakdown."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    # Bound to the actual fulfilling vendor's variant on assignment (null until then).
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.PROTECT, null=True, blank=True, related_name='order_items')
    template = models.ForeignKey(
        ProductTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    concept_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    product_name = models.CharField(max_length=200)
    variant_sku = models.CharField(max_length=100, null=True, blank=True)
    attributes_snapshot = models.JSONField(default=dict, blank=True)
    image_url = models.CharField(max_length=300, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    # Estimated range at placement (per line, incl. commission).
    estimated_min_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    estimated_max_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    # Finalized on assignment.
    vendor_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    commission_type = models.CharField(max_length=10, null=True, blank=True)
    commission_value = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    commission_unit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    final_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.order.order_no})"


class OrderStatusLog(AuditMixin):
    ACTOR_BUYER = 'buyer'
    ACTOR_MERCHANT = 'merchant'
    ACTOR_AGENT = 'agent'
    ACTOR_ADMIN = 'admin'
    ACTOR_SYSTEM = 'system'
    ACTOR_CHOICES = [
        (ACTOR_BUYER, 'Buyer'),
        (ACTOR_MERCHANT, 'Merchant'),
        (ACTOR_AGENT, 'Agent'),
        (ACTOR_ADMIN, 'Admin'),
        (ACTOR_SYSTEM, 'System'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(max_length=20)
    note = models.TextField(null=True, blank=True)
    changed_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_status_changes'
    )
    actor_context = models.CharField(max_length=10, choices=ACTOR_CHOICES, default=ACTOR_SYSTEM)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.order.order_no}: {self.status}"


class Delivery(AuditMixin):
    STATUS_ASSIGNED = 'assigned'
    STATUS_ACCEPTED = 'accepted'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_PICKED_UP, 'Picked Up'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_FAILED, 'Failed'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    agent = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries'
    )
    # Status-based tracking only (updated by the delivery agent).
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_ASSIGNED)
    tracking_note = models.CharField(max_length=255, null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    # Delivery confirmation: proof image is REQUIRED to mark 'delivered'.
    proof_image = models.ImageField(upload_to='ecommerce/delivery_proofs/', null=True, blank=True)
    otp_code = models.CharField(max_length=6, null=True, blank=True)
    otp_verified = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Delivery for {self.order.order_no}"


class ReturnRequest(AuditMixin):
    REQUESTED = 'requested'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    REFUNDED = 'refunded'
    STATUS_CHOICES = [
        (REQUESTED, 'Requested'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
        (REFUNDED, 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    order_item = models.ForeignKey(
        OrderItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns'
    )
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=REQUESTED)
    reviewed_by = models.ForeignKey(
        'user.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_returns'
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return for {self.order.order_no} ({self.status})"
