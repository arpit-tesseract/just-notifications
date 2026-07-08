"""
E-Commerce serializers.

Per-operation split (matching the existing codebase style): every CRUD resource exposes
distinct ``<Model>ListSerializer`` / ``<Model>DetailSerializer`` / ``<Model>CreateSerializer``
/ ``<Model>UpdateSerializer`` classes, selected by the viewset's ``get_serializer_class``.
Update subclasses Create so it can diverge later without touching create. List is the
lightweight table view; Detail is the full record.
"""
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from ecommerce.models import (
    Attribute, AttributeOption, Cart, CartItem, Delivery, MerchantStoreSetting, Order,
    OrderItem, OrderStatusLog, OrderVendorAssignment, Product, ProductImage,
    ProductPromotion, ProductReview, ProductTemplate, ProductVariant, ProductVariantGroup,
    ProductVariantGroupValue, StockMovement, TemplateAttribute, Unit, UnitType,
    VariantAttributeValue, Wishlist, WishlistItem,
)
from ecommerce.services import catalog as catalog_service
from ecommerce.services.inventory import apply_movement
from user.models import BusinessFamily, ResidentialDetails


class IdNameSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


# =====================================================================================
# A. ADMIN CONFIG
# =====================================================================================
# ---- UnitType ----
class UnitTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ['id', 'name', 'code', 'is_active']


class UnitTypeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ['id', 'name', 'code', 'description', 'is_active', 'created_at', 'updated_at']


class UnitTypeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitType
        fields = ['id', 'name', 'code', 'description', 'is_active']


class UnitTypeUpdateSerializer(UnitTypeCreateSerializer):
    pass


# ---- Unit ----
class UnitListSerializer(serializers.ModelSerializer):
    unit_type_name = serializers.CharField(source='unit_type.name', read_only=True)

    class Meta:
        model = Unit
        fields = ['id', 'unit_type', 'unit_type_name', 'name', 'symbol', 'is_base', 'is_active']


class UnitDetailSerializer(serializers.ModelSerializer):
    unit_type_name = serializers.CharField(source='unit_type.name', read_only=True)

    class Meta:
        model = Unit
        fields = ['id', 'unit_type', 'unit_type_name', 'name', 'symbol', 'is_base',
                  'conversion_factor', 'sort_order', 'is_active', 'created_at', 'updated_at']


class UnitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ['id', 'unit_type', 'name', 'symbol', 'is_base', 'conversion_factor',
                  'sort_order', 'is_active']
        validators = [
            UniqueTogetherValidator(
                queryset=Unit.objects.all(), fields=['unit_type', 'name'],
                message="A unit with this name already exists for this unit type.")
        ]


class UnitUpdateSerializer(UnitCreateSerializer):
    pass


# ---- AttributeOption ----
class AttributeOptionListSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='unit.name', read_only=True)

    class Meta:
        model = AttributeOption
        fields = ['id', 'attribute', 'unit', 'unit_name', 'value', 'display_value', 'is_active']


class AttributeOptionDetailSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='unit.name', read_only=True)

    class Meta:
        model = AttributeOption
        fields = ['id', 'attribute', 'unit', 'unit_name', 'value', 'display_value', 'color_hex',
                  'sort_order', 'is_active']


class AttributeOptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeOption
        fields = ['id', 'attribute', 'unit', 'value', 'display_value', 'color_hex',
                  'sort_order', 'is_active']


class AttributeOptionUpdateSerializer(AttributeOptionCreateSerializer):
    pass


class _AttributeOptionNestedSerializer(serializers.ModelSerializer):
    """Options embedded in an Attribute payload (attribute set by the parent)."""
    class Meta:
        model = AttributeOption
        fields = ['id', 'unit', 'value', 'display_value', 'color_hex', 'sort_order', 'is_active']


# ---- Attribute ----
class AttributeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ['id', 'name', 'code', 'input_type', 'is_active']


class AttributeDetailSerializer(serializers.ModelSerializer):
    options = AttributeOptionDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'code', 'input_type', 'unit_type', 'help_text', 'is_active',
                  'options', 'created_at', 'updated_at']


class AttributeCreateSerializer(serializers.ModelSerializer):
    options = _AttributeOptionNestedSerializer(many=True, required=False)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'code', 'input_type', 'unit_type', 'help_text', 'is_active', 'options']

    @transaction.atomic
    def create(self, validated_data):
        options = validated_data.pop('options', [])
        attribute = Attribute.objects.create(**validated_data)
        for opt in options:
            AttributeOption.objects.create(attribute=attribute, **opt)
        return attribute

    @transaction.atomic
    def update(self, instance, validated_data):
        options = validated_data.pop('options', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if options is not None:
            instance.options.all().delete()
            for opt in options:
                AttributeOption.objects.create(attribute=instance, **opt)
        return instance


class AttributeUpdateSerializer(AttributeCreateSerializer):
    pass


# ---- TemplateAttribute ----
class TemplateAttributeListSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    input_type = serializers.CharField(source='attribute.input_type', read_only=True)

    class Meta:
        model = TemplateAttribute
        fields = ['id', 'template', 'attribute', 'attribute_name', 'input_type', 'is_required',
                  'is_variant_defining', 'is_image_defining', 'sort_order']


class TemplateAttributeDetailSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    input_type = serializers.CharField(source='attribute.input_type', read_only=True)

    class Meta:
        model = TemplateAttribute
        fields = ['id', 'template', 'attribute', 'attribute_name', 'input_type', 'is_required',
                  'is_variant_defining', 'is_image_defining', 'default_unit', 'sort_order']


class TemplateAttributeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateAttribute
        fields = ['id', 'template', 'attribute', 'is_required', 'is_variant_defining',
                  'is_image_defining', 'default_unit', 'sort_order']
        extra_kwargs = {'template': {'required': False}}


class TemplateAttributeUpdateSerializer(TemplateAttributeCreateSerializer):
    pass


# ---- ProductTemplate ----
class ProductTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight row for table/list views."""
    attribute_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductTemplate
        fields = ['id', 'name', 'code', 'commission_type', 'commission_value', 'is_active',
                  'attribute_count']

    def get_attribute_count(self, obj):
        return obj.template_attributes.filter(is_deleted=False).count()


class ProductTemplateDetailSerializer(serializers.ModelSerializer):
    template_attributes = TemplateAttributeDetailSerializer(many=True, read_only=True)

    class Meta:
        model = ProductTemplate
        fields = ['id', 'name', 'code', 'category', 'description', 'image', 'commission_type',
                  'commission_value', 'is_active', 'template_attributes']


class ProductTemplateCreateSerializer(serializers.ModelSerializer):
    """Supports nested template_attributes on create/update."""
    template_attributes = TemplateAttributeCreateSerializer(many=True, required=False)

    class Meta:
        model = ProductTemplate
        fields = ['id', 'name', 'code', 'category', 'description', 'image', 'commission_type',
                  'commission_value', 'is_active', 'template_attributes']

    @transaction.atomic
    def create(self, validated_data):
        attrs = validated_data.pop('template_attributes', [])
        template = ProductTemplate.objects.create(**validated_data)
        for ta in attrs:
            TemplateAttribute.objects.create(template=template, **ta)
        return template

    @transaction.atomic
    def update(self, instance, validated_data):
        attrs = validated_data.pop('template_attributes', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if attrs is not None:
            instance.template_attributes.all().delete()
            for ta in attrs:
                TemplateAttribute.objects.create(template=instance, **ta)
        return instance


class ProductTemplateUpdateSerializer(ProductTemplateCreateSerializer):
    pass


# =====================================================================================
# B. CATALOG — read serializers + nested product creation
# =====================================================================================
class ProductVariantValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    display = serializers.CharField(read_only=True)

    class Meta:
        model = VariantAttributeValue
        fields = ['id', 'attribute', 'attribute_name', 'option', 'unit', 'value_text',
                  'value_number', 'value_bool', 'value_date', 'display']


class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values = ProductVariantValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'variant_group', 'sku', 'price', 'compare_at_price', 'stock_qty',
                  'low_stock_threshold', 'weight_grams', 'status', 'is_default', 'concept_key',
                  'attribute_values']


# ---- ProductImage ----
class ProductImageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'variant_group', 'image', 'is_primary', 'sort_order']


class ProductImageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'variant_group', 'image', 'alt_text', 'is_primary', 'sort_order']


class ProductImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'variant_group', 'image', 'alt_text', 'is_primary', 'sort_order']


class ProductImageUpdateSerializer(ProductImageCreateSerializer):
    pass


class ProductVariantGroupSerializer(serializers.ModelSerializer):
    images = ProductImageDetailSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariantGroup
        fields = ['id', 'label', 'sort_order', 'images', 'variants']


# ---- Product ----
class ProductListSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'template', 'template_name', 'category', 'base_price',
                  'status', 'delivery_fee', 'delivery_time_minutes', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    variant_groups = ProductVariantGroupSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'business_family', 'template', 'template_name', 'category', 'name', 'sku',
                  'slug', 'description', 'base_price', 'tax_rate', 'hsn_code', 'min_order_qty',
                  'delivery_fee', 'preparation_time_minutes', 'delivery_time_minutes', 'status',
                  'variant_groups', 'images']

    def get_images(self, obj):
        # Product-level (generic) images only; group images live under each variant_group.
        qs = obj.images.filter(variant_group__isnull=True)
        return ProductImageDetailSerializer(qs, many=True).data


# Nested input serializers for product create.
class VariantAttributeValueInputSerializer(serializers.Serializer):
    template_attribute = serializers.PrimaryKeyRelatedField(queryset=TemplateAttribute.objects.all())
    option = serializers.PrimaryKeyRelatedField(
        queryset=AttributeOption.objects.all(), required=False, allow_null=True)
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.all(), required=False, allow_null=True)
    value_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    value_number = serializers.DecimalField(max_digits=14, decimal_places=4, required=False, allow_null=True)
    value_bool = serializers.BooleanField(required=False, allow_null=True)
    value_date = serializers.DateField(required=False, allow_null=True)


class VariantInputSerializer(serializers.Serializer):
    sku = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    stock_qty = serializers.IntegerField(required=False, default=0)
    low_stock_threshold = serializers.IntegerField(required=False, default=0)
    weight_grams = serializers.IntegerField(required=False, allow_null=True)
    is_default = serializers.BooleanField(required=False, default=False)
    attribute_values = VariantAttributeValueInputSerializer(many=True)


class VariantGroupValueInputSerializer(serializers.Serializer):
    template_attribute = serializers.PrimaryKeyRelatedField(queryset=TemplateAttribute.objects.all())
    option = serializers.PrimaryKeyRelatedField(
        queryset=AttributeOption.objects.all(), required=False, allow_null=True)
    value_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class VariantGroupInputSerializer(serializers.Serializer):
    label = serializers.CharField()
    sort_order = serializers.IntegerField(required=False, default=1)
    values = VariantGroupValueInputSerializer(many=True, required=False)
    variants = VariantInputSerializer(many=True)


class ProductCreateSerializer(serializers.ModelSerializer):
    variant_groups = VariantGroupInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Product
        fields = ['id', 'business_family', 'template', 'category', 'name', 'sku', 'slug',
                  'description', 'base_price', 'tax_rate', 'hsn_code', 'min_order_qty',
                  'delivery_fee', 'preparation_time_minutes', 'delivery_time_minutes', 'status',
                  'variant_groups']

    def _validate_sku_unique(self, attrs):
        business = attrs.get('business_family') or getattr(self.instance, 'business_family', None)
        sku = attrs.get('sku') or getattr(self.instance, 'sku', None)
        if business and sku:
            clash = Product.objects.filter(business_family=business, sku=sku)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError({'sku': "You already have a product with this SKU."})

    def validate(self, attrs):
        self._validate_sku_unique(attrs)
        template = attrs.get('template') or getattr(self.instance, 'template', None)
        groups = attrs.get('variant_groups', [])
        valid_ta_ids = set(
            TemplateAttribute.objects.filter(template=template, is_deleted=False)
            .values_list('id', flat=True)
        ) if template else set()
        for group in groups:
            for variant in group['variants']:
                for av in variant['attribute_values']:
                    ta = av['template_attribute']
                    if template and ta.id not in valid_ta_ids:
                        raise serializers.ValidationError(
                            f"TemplateAttribute {ta.id} does not belong to template '{template}'.")
                    if ta.attribute.has_options and not av.get('option'):
                        raise serializers.ValidationError(
                            f"Attribute '{ta.attribute.name}' requires an option.")
        return attrs

    def _build_value(self, av, template_attribute):
        return {
            'attribute': template_attribute.attribute,
            'template_attribute': template_attribute,
            'option': av.get('option'),
            'unit': av.get('unit'),
            'value_text': av.get('value_text'),
            'value_number': av.get('value_number'),
            'value_bool': av.get('value_bool'),
            'value_date': av.get('value_date'),
        }

    @transaction.atomic
    def create(self, validated_data):
        groups = validated_data.pop('variant_groups', [])
        business_family = validated_data['business_family']
        user = self.context['request'].user if 'request' in self.context else None

        validated_data['area_code'] = catalog_service.resolve_business_area_code(business_family)
        validated_data['grouping_key'] = catalog_service.build_grouping_key(
            validated_data['template'].id, validated_data['name'])
        validated_data['created_by'] = user

        product = Product.objects.create(**validated_data)

        for group in groups:
            vg = ProductVariantGroup.objects.create(
                product=product, label=group['label'], sort_order=group.get('sort_order', 1))
            for val in group.get('values', []):
                ta = val['template_attribute']
                ProductVariantGroupValue.objects.create(
                    variant_group=vg, template_attribute=ta, attribute=ta.attribute,
                    option=val.get('option'), value_text=val.get('value_text'))
            for v in group['variants']:
                initial_stock = v.get('stock_qty', 0) or 0
                variant = ProductVariant.objects.create(
                    product=product, variant_group=vg, sku=v['sku'], price=v['price'],
                    compare_at_price=v.get('compare_at_price'), stock_qty=0,
                    low_stock_threshold=v.get('low_stock_threshold', 0) or 0,
                    weight_grams=v.get('weight_grams'), is_default=v.get('is_default', False))
                concept_parts = []
                for av in v['attribute_values']:
                    ta = av['template_attribute']
                    VariantAttributeValue.objects.create(variant=variant, **self._build_value(av, ta))
                    if ta.is_variant_defining:
                        opt = av.get('option')
                        unit = av.get('unit')
                        value = opt.value if opt else av.get('value_text')
                        concept_parts.append((ta.attribute.code, value, unit.name if unit else None))
                variant.concept_key = catalog_service.build_variant_concept_key(
                    product.template_id, concept_parts)
                variant.save(update_fields=['concept_key', 'updated_at'])
                if initial_stock:
                    apply_movement(variant, StockMovement.PURCHASE, initial_stock,
                                   reason="Initial stock", user=user)
        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Scalar-field update only; variants/images are managed via their own endpoints."""
    class Meta:
        model = Product
        fields = ['id', 'category', 'name', 'sku', 'slug', 'description', 'base_price', 'tax_rate',
                  'hsn_code', 'min_order_qty', 'delivery_fee', 'preparation_time_minutes',
                  'delivery_time_minutes', 'status']

    def validate(self, attrs):
        sku = attrs.get('sku') or getattr(self.instance, 'sku', None)
        business = getattr(self.instance, 'business_family', None)
        if business and sku:
            clash = Product.objects.filter(business_family=business, sku=sku).exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError({'sku': "You already have a product with this SKU."})
        return attrs


# ---- Inventory ----
class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ['id', 'variant', 'movement_type', 'quantity_delta', 'balance_after',
                  'reason', 'reference_type', 'reference_id', 'created_at']


class StockAdjustSerializer(serializers.Serializer):
    movement_type = serializers.ChoiceField(choices=[c[0] for c in StockMovement.MOVEMENT_TYPE_CHOICES])
    quantity_delta = serializers.IntegerField()
    reason = serializers.CharField(required=False, allow_blank=True)


# =====================================================================================
# D. STOREFRONT
# =====================================================================================
# ---- MerchantStoreSetting ----
class MerchantStoreSettingListSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business_family.name', read_only=True)

    class Meta:
        model = MerchantStoreSetting
        fields = ['id', 'business_family', 'business_name', 'is_online', 'is_open',
                  'default_delivery_time_minutes']


class MerchantStoreSettingDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantStoreSetting
        fields = ['id', 'business_family', 'is_online', 'is_open', 'min_order_value',
                  'default_delivery_time_minutes', 'return_policy']


class MerchantStoreSettingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantStoreSetting
        fields = ['id', 'business_family', 'is_online', 'is_open', 'min_order_value',
                  'default_delivery_time_minutes', 'return_policy']


class MerchantStoreSettingUpdateSerializer(MerchantStoreSettingCreateSerializer):
    pass


# ---- ProductPromotion ----
class ProductPromotionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPromotion
        fields = ['id', 'product', 'business_family', 'promotion_type', 'priority_boost', 'is_active']


class ProductPromotionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPromotion
        fields = ['id', 'product', 'business_family', 'promotion_type', 'priority_boost',
                  'start_at', 'end_at', 'is_active', 'created_at']


class ProductPromotionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPromotion
        fields = ['id', 'product', 'business_family', 'promotion_type', 'priority_boost',
                  'start_at', 'end_at', 'is_active']


class ProductPromotionUpdateSerializer(ProductPromotionCreateSerializer):
    pass


# ---- ProductReview ----
class ProductReviewListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_name', 'rating', 'title', 'is_approved', 'created_at']


class ProductReviewDetailSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'user', 'user_name', 'order_item', 'rating', 'title',
                  'comment', 'is_approved', 'created_at']


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'order_item', 'rating', 'title', 'comment']


class ProductReviewUpdateSerializer(ProductReviewCreateSerializer):
    pass


class WishlistItemSerializer(serializers.ModelSerializer):
    variant_sku = serializers.CharField(source='variant.sku', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'variant', 'variant_sku', 'created_at']


# =====================================================================================
# E. CART & ORDERS (service-driven; read serializers + small input serializers)
# =====================================================================================
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    variant_sku = serializers.CharField(source='variant.sku', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'variant', 'variant_sku', 'product_name', 'quantity', 'unit_price', 'line_total']

    def get_line_total(self, obj):
        return str((obj.unit_price * obj.quantity).quantize(Decimal('0.01')))


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'status', 'items']


class AddCartItemSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity = serializers.IntegerField(min_value=1, default=1)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'template', 'concept_key', 'product_name', 'variant_sku',
                  'attributes_snapshot', 'image_url', 'quantity',
                  'estimated_min_price', 'estimated_max_price',
                  'vendor_unit_price', 'commission_unit_amount', 'final_unit_price', 'line_total']


class OrderStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusLog
        fields = ['id', 'status', 'note', 'actor_context', 'created_at']


class OrderVendorAssignmentSerializer(serializers.ModelSerializer):
    business_family_name = serializers.CharField(source='business_family.name', read_only=True)

    class Meta:
        model = OrderVendorAssignment
        fields = ['id', 'business_family', 'business_family_name', 'status', 'responded_at',
                  'note', 'created_at']


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['id', 'agent', 'status', 'tracking_note', 'assigned_at', 'accepted_at',
                  'picked_up_at', 'delivered_at', 'proof_image', 'otp_verified']


class AgentDeliverySerializer(serializers.ModelSerializer):
    order_no = serializers.CharField(source='order.order_no', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    buyer_name = serializers.CharField(source='order.buyer.full_name', read_only=True)
    total_amount = serializers.DecimalField(source='order.total_amount', max_digits=12,
                                            decimal_places=2, read_only=True)

    class Meta:
        model = Delivery
        fields = ['id', 'order', 'order_no', 'order_status', 'buyer_name', 'total_amount',
                  'status', 'tracking_note', 'assigned_at', 'accepted_at', 'picked_up_at',
                  'delivered_at', 'proof_image', 'otp_verified']


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight order row for admin/vendor tables."""
    class Meta:
        model = Order
        fields = ['id', 'order_no', 'buyer', 'business_family', 'status', 'payment_status',
                  'is_price_final', 'estimated_min_total', 'estimated_max_total', 'total_amount',
                  'placed_at']


class OrderSerializer(serializers.ModelSerializer):
    """Full order view (admin/vendor). Buyer-facing view hides the vendor via the view layer."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    vendor_assignments = OrderVendorAssignmentSerializer(many=True, read_only=True)
    delivery = DeliverySerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'buyer', 'area_node', 'listing_business_family',
                  'business_family', 'assigned_admin', 'assigned_at', 'delivery_address',
                  'estimated_min_total', 'estimated_max_total', 'is_price_final',
                  'vendor_subtotal', 'commission_amount', 'subtotal', 'tax_amount',
                  'delivery_fee', 'discount_amount', 'total_amount', 'status', 'payment_status',
                  'placed_at', 'note', 'items', 'status_logs', 'vendor_assignments', 'delivery']


class BuyerOrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_no', 'status', 'payment_status', 'is_price_final',
                  'estimated_min_total', 'estimated_max_total', 'total_amount', 'placed_at']


class BuyerOrderSerializer(serializers.ModelSerializer):
    """Buyer-facing order: vendor identity hidden."""
    items = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'delivery_address', 'estimated_min_total', 'estimated_max_total',
                  'is_price_final', 'subtotal', 'tax_amount', 'delivery_fee', 'discount_amount',
                  'total_amount', 'status', 'payment_status', 'placed_at', 'note', 'items',
                  'status_logs']


class PlaceOrderSerializer(serializers.Serializer):
    cart = serializers.PrimaryKeyRelatedField(queryset=Cart.objects.all())
    delivery_address = serializers.PrimaryKeyRelatedField(
        queryset=ResidentialDetails.objects.all(), required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)


class AssignVendorSerializer(serializers.Serializer):
    business_family = serializers.PrimaryKeyRelatedField(queryset=BusinessFamily.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)
