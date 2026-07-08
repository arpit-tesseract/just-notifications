"""E-Commerce API views."""
from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import CommonPagination
from ecommerce.pagination import DropdownPagination
from ecommerce.models import (
    Attribute, AttributeOption, Cart, CartItem, Delivery, MerchantStoreSetting, Order,
    OrderStatusLog, Product, ProductImage, ProductPromotion, ProductReview, ProductTemplate,
    ProductVariant, TemplateAttribute, Unit, UnitType, Wishlist, WishlistItem,
)
from ecommerce.permissions import (
    IsAdminIdentity, IsAuthenticatedBusinessOrAdmin, is_platform_admin, user_business_family_ids,
)
from ecommerce.serializers import (
    AddCartItemSerializer, AgentDeliverySerializer, AssignVendorSerializer,
    AttributeCreateSerializer, AttributeDetailSerializer, AttributeListSerializer,
    AttributeOptionCreateSerializer, AttributeOptionDetailSerializer, AttributeOptionListSerializer,
    AttributeOptionUpdateSerializer, AttributeUpdateSerializer, BuyerOrderListSerializer,
    BuyerOrderSerializer, CartSerializer, MerchantStoreSettingCreateSerializer,
    MerchantStoreSettingDetailSerializer, MerchantStoreSettingListSerializer,
    MerchantStoreSettingUpdateSerializer, OrderListSerializer, OrderSerializer, PlaceOrderSerializer,
    ProductCreateSerializer, ProductDetailSerializer, ProductImageCreateSerializer,
    ProductImageDetailSerializer, ProductImageListSerializer, ProductImageUpdateSerializer,
    ProductListSerializer, ProductPromotionCreateSerializer, ProductPromotionDetailSerializer,
    ProductPromotionListSerializer, ProductPromotionUpdateSerializer, ProductReviewCreateSerializer,
    ProductReviewDetailSerializer, ProductReviewListSerializer, ProductReviewUpdateSerializer,
    ProductTemplateCreateSerializer, ProductTemplateDetailSerializer, ProductTemplateListSerializer,
    ProductTemplateUpdateSerializer, ProductUpdateSerializer, ProductVariantSerializer,
    StockAdjustSerializer, StockMovementSerializer, TemplateAttributeCreateSerializer,
    TemplateAttributeDetailSerializer, TemplateAttributeListSerializer,
    TemplateAttributeUpdateSerializer, UnitCreateSerializer, UnitDetailSerializer,
    UnitListSerializer, UnitTypeCreateSerializer, UnitTypeDetailSerializer, UnitTypeListSerializer,
    UnitTypeUpdateSerializer, UnitUpdateSerializer, WishlistItemSerializer,
)
from ecommerce.services import catalog as catalog_service
from ecommerce.services import orders as order_service
from ecommerce.services import product_type as product_type_service
from ecommerce.services.inventory import apply_movement


class SoftDeleteModelViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet with soft-delete + per-operation serializers.

    Set ``serializer_action_classes`` = {'list':..., 'retrieve':..., 'create':...,
    'update':..., 'partial_update':...}; anything unset falls back to ``serializer_class``.
    """
    serializer_action_classes = {}

    def get_serializer_class(self):
        return self.serializer_action_classes.get(self.action, self.serializer_class)

    def perform_destroy(self, instance):
        if hasattr(instance, 'soft_delete'):
            instance.soft_delete(user=self.request.user)
        else:
            instance.delete()


# =====================================================================================
# A. ADMIN MASTER CONFIG
# =====================================================================================
class UnitTypeViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAdminIdentity]
    queryset = UnitType.objects.all()
    serializer_class = UnitTypeDetailSerializer
    serializer_action_classes = {
        'list': UnitTypeListSerializer, 'retrieve': UnitTypeDetailSerializer,
        'create': UnitTypeCreateSerializer, 'update': UnitTypeUpdateSerializer,
        'partial_update': UnitTypeUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']


class UnitViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAdminIdentity]
    queryset = Unit.objects.select_related('unit_type').all()
    serializer_class = UnitDetailSerializer
    serializer_action_classes = {
        'list': UnitListSerializer, 'retrieve': UnitDetailSerializer,
        'create': UnitCreateSerializer, 'update': UnitUpdateSerializer,
        'partial_update': UnitUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'symbol']
    ordering_fields = ['name', 'sort_order']

    def get_queryset(self):
        qs = super().get_queryset()
        unit_type = self.request.query_params.get('unit_type')
        return qs.filter(unit_type_id=unit_type) if unit_type else qs


class AttributeViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAdminIdentity]
    queryset = Attribute.objects.prefetch_related('options').all()
    serializer_class = AttributeDetailSerializer
    serializer_action_classes = {
        'list': AttributeListSerializer, 'retrieve': AttributeDetailSerializer,
        'create': AttributeCreateSerializer, 'update': AttributeUpdateSerializer,
        'partial_update': AttributeUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        input_type = self.request.query_params.get('input_type')
        return qs.filter(input_type=input_type) if input_type else qs


class AttributeOptionViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAdminIdentity]
    queryset = AttributeOption.objects.select_related('attribute', 'unit').all()
    serializer_class = AttributeOptionDetailSerializer
    serializer_action_classes = {
        'list': AttributeOptionListSerializer, 'retrieve': AttributeOptionDetailSerializer,
        'create': AttributeOptionCreateSerializer, 'update': AttributeOptionUpdateSerializer,
        'partial_update': AttributeOptionUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['value', 'display_value']
    ordering_fields = ['sort_order', 'value']

    def get_queryset(self):
        qs = super().get_queryset()
        attribute = self.request.query_params.get('attribute')
        unit = self.request.query_params.get('unit')
        if attribute:
            qs = qs.filter(attribute_id=attribute)
        if unit:
            qs = qs.filter(Q(unit_id=unit) | Q(unit__isnull=True))
        return qs


class ProductTemplateViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAdminIdentity]
    queryset = ProductTemplate.objects.prefetch_related('template_attributes__attribute').all()
    serializer_class = ProductTemplateDetailSerializer
    serializer_action_classes = {
        'list': ProductTemplateListSerializer, 'retrieve': ProductTemplateDetailSerializer,
        'create': ProductTemplateCreateSerializer, 'update': ProductTemplateUpdateSerializer,
        'partial_update': ProductTemplateUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']

    @action(detail=True, methods=['get'], url_path='form-schema',
            permission_classes=[IsAuthenticated])
    def form_schema(self, request, pk=None):
        template = self.get_object()
        return Response(catalog_service.build_form_schema(template))

    @action(detail=True, methods=['get', 'post'], url_path='attributes')
    def attributes(self, request, pk=None):
        template = self.get_object()
        if request.method == 'GET':
            qs = template.template_attributes.filter(is_deleted=False)
            return Response(TemplateAttributeDetailSerializer(qs, many=True).data)
        serializer = TemplateAttributeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(template=template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TemplateAttributeViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAdminIdentity]
    queryset = TemplateAttribute.objects.select_related('attribute', 'template').all()
    serializer_class = TemplateAttributeDetailSerializer
    serializer_action_classes = {
        'list': TemplateAttributeListSerializer, 'retrieve': TemplateAttributeDetailSerializer,
        'create': TemplateAttributeCreateSerializer, 'update': TemplateAttributeUpdateSerializer,
        'partial_update': TemplateAttributeUpdateSerializer,
    }
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['sort_order']

    def get_queryset(self):
        qs = super().get_queryset()
        template = self.request.query_params.get('template')
        return qs.filter(template_id=template) if template else qs


class BaseDropdownView(APIView):
    """Searchable dropdown returning 10-per-chunk {id, name} results."""
    permission_classes = [IsAuthenticated]
    model = None
    search_fields = ['name']
    base_filter = {'is_active': True}

    def get_queryset(self):
        return self.model.objects.filter(**self.base_filter)

    def label(self, obj):
        return obj.name

    def get(self, request):
        qs = self.get_queryset()
        search = request.query_params.get('search', '').strip()
        if search:
            q = Q()
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(q)
        paginator = DropdownPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        data = [{'id': obj.id, 'name': self.label(obj)} for obj in page]
        return paginator.get_paginated_response(data)


class UnitTypeDropdownView(BaseDropdownView):
    model = UnitType
    search_fields = ['name', 'code']


class UnitDropdownView(BaseDropdownView):
    model = Unit
    search_fields = ['name', 'symbol']

    def get_queryset(self):
        qs = Unit.objects.filter(is_active=True)
        unit_type = self.request.query_params.get('unit_type')
        return qs.filter(unit_type_id=unit_type) if unit_type else qs

    def label(self, obj):
        return f"{obj.name} ({obj.unit_type.name})"


class AttributeDropdownView(BaseDropdownView):
    model = Attribute
    search_fields = ['name', 'code']


class ProductTemplateDropdownView(BaseDropdownView):
    model = ProductTemplate
    search_fields = ['name', 'code']


class ProductTypeView(APIView):
    """
    Single-call 'Create Product Type' upsert (business logic -> APIView).

    GET  /product-types/            -> paginated, searchable lightweight list
    GET  /product-types/<id>/       -> full nested detail (same shape as POST body)
    POST /product-types/            -> create or update (id in body) template + attributes +
                                       unit types + units + options in one request
    DELETE /product-types/<id>/     -> soft delete the template
    """
    permission_classes = [IsAdminIdentity]

    def get(self, request, pk=None):
        if pk:
            template = get_object_or_404(ProductTemplate, pk=pk)
            return Response(product_type_service.serialize_product_type(template))

        qs = ProductTemplate.objects.all()
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
        paginator = CommonPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        data = ProductTemplateListSerializer(page, many=True).data
        return paginator.get_paginated_response(data)

    def post(self, request):
        try:
            template = product_type_service.upsert_product_type(request.data, request.user)
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(product_type_service.serialize_product_type(template),
                        status=status.HTTP_200_OK if request.data.get('id') else status.HTTP_201_CREATED)

    def delete(self, request, pk=None):
        template = get_object_or_404(ProductTemplate, pk=pk)
        template.soft_delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


# =====================================================================================
# B. MERCHANT CATALOG
# =====================================================================================
class ProductViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAuthenticatedBusinessOrAdmin]
    queryset = Product.objects.select_related('template', 'business_family').all()
    serializer_class = ProductDetailSerializer
    serializer_action_classes = {
        'list': ProductListSerializer, 'retrieve': ProductDetailSerializer,
        'create': ProductCreateSerializer, 'update': ProductUpdateSerializer,
        'partial_update': ProductUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'base_price', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Merchants see only their own catalog; admins may scope by ?business_family.
        if is_platform_admin(user):
            business = self.request.query_params.get('business_family')
            if business:
                qs = qs.filter(business_family_id=business)
        else:
            qs = qs.filter(business_family_id__in=user_business_family_ids(user))
        for field in ('status', 'template', 'category'):
            value = self.request.query_params.get(field)
            if value:
                qs = qs.filter(**{f"{field}_id" if field in ('template', 'category') else field: value})
        return qs

    def perform_create(self, serializer):
        business_family = serializer.validated_data.get('business_family')
        user = self.request.user
        if not is_platform_admin(user):
            if not business_family or business_family.id not in user_business_family_ids(user):
                raise PermissionDenied("You can only add products to your own business.")
        serializer.save()

    @action(detail=True, methods=['get'], url_path='form-schema',
            permission_classes=[IsAuthenticated])
    def form_schema(self, request, pk=None):
        product = self.get_object()
        return Response(catalog_service.build_form_schema(product.template))

    @action(detail=True, methods=['get'], url_path='variants',
            permission_classes=[IsAuthenticated])
    def variants(self, request, pk=None):
        product = self.get_object()
        qs = product.variants.filter(is_deleted=False).prefetch_related('attribute_values__attribute')
        return Response(ProductVariantSerializer(qs, many=True).data)


class ProductImageViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAuthenticatedBusinessOrAdmin]
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageDetailSerializer
    serializer_action_classes = {
        'list': ProductImageListSerializer, 'retrieve': ProductImageDetailSerializer,
        'create': ProductImageCreateSerializer, 'update': ProductImageUpdateSerializer,
        'partial_update': ProductImageUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['sort_order']

    def get_queryset(self):
        qs = super().get_queryset()
        product = self.request.query_params.get('product')
        variant_group = self.request.query_params.get('variant_group')
        if product:
            qs = qs.filter(product_id=product)
        if variant_group:
            qs = qs.filter(variant_group_id=variant_group)
        return qs


class VariantStockView(APIView):
    permission_classes = [IsAuthenticatedBusinessOrAdmin]

    def post(self, request, pk=None):
        variant = get_object_or_404(ProductVariant, pk=pk)
        serializer = StockAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            movement = apply_movement(
                variant,
                serializer.validated_data['movement_type'],
                serializer.validated_data['quantity_delta'],
                reason=serializer.validated_data.get('reason'),
                user=request.user,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)

    def get(self, request, pk=None):
        variant = get_object_or_404(ProductVariant, pk=pk)
        qs = variant.stock_movements.all()
        return Response(StockMovementSerializer(qs, many=True).data)


# =====================================================================================
# C. STOREFRONT & DISCOVERY
# =====================================================================================
class MerchantStoreSettingViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAuthenticatedBusinessOrAdmin]
    queryset = MerchantStoreSetting.objects.select_related('business_family').all()
    serializer_class = MerchantStoreSettingDetailSerializer
    serializer_action_classes = {
        'list': MerchantStoreSettingListSerializer, 'retrieve': MerchantStoreSettingDetailSerializer,
        'create': MerchantStoreSettingCreateSerializer, 'update': MerchantStoreSettingUpdateSerializer,
        'partial_update': MerchantStoreSettingUpdateSerializer,
    }
    pagination_class = CommonPagination

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_platform_admin(user):
            return qs
        return qs.filter(business_family_id__in=user_business_family_ids(user))


class ProductPromotionViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAdminIdentity]
    queryset = ProductPromotion.objects.all()
    serializer_class = ProductPromotionDetailSerializer
    serializer_action_classes = {
        'list': ProductPromotionListSerializer, 'retrieve': ProductPromotionDetailSerializer,
        'create': ProductPromotionCreateSerializer, 'update': ProductPromotionUpdateSerializer,
        'partial_update': ProductPromotionUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['priority_boost', 'start_at']

    def get_queryset(self):
        qs = super().get_queryset()
        for field in ('product', 'business_family', 'promotion_type', 'is_active'):
            value = self.request.query_params.get(field)
            if value is not None and value != '':
                qs = qs.filter(**{field: value})
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProductReviewViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = ProductReview.objects.select_related('user', 'product').all()
    serializer_class = ProductReviewDetailSerializer
    serializer_action_classes = {
        'list': ProductReviewListSerializer, 'retrieve': ProductReviewDetailSerializer,
        'create': ProductReviewCreateSerializer, 'update': ProductReviewUpdateSerializer,
        'partial_update': ProductReviewUpdateSerializer,
    }
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'comment']
    ordering_fields = ['rating', 'created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        for field in ('product', 'rating'):
            value = self.request.query_params.get(field)
            if value:
                qs = qs.filter(**{field: value})
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FeedView(APIView):
    """Area-based, vendor-hidden feed: same-area products grouped with a price range."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        area_code = request.query_params.get('area_code')
        if not area_code:
            rd = getattr(request.user, 'current_residential_details', None)
            area_code = rd.residential_code if rd else None

        products = (
            Product.objects.filter(status=Product.STATUS_ACTIVE)
            .select_related('template')
            .prefetch_related('variants', 'images')
            .exclude(business_family__store_setting__is_online=False)
        )
        if area_code:
            prefix = catalog_service.area_prefix(area_code)
            products = products.filter(area_code__startswith=prefix)

        category = request.query_params.get('category')
        if category:
            products = products.filter(category_id=category)
        search = request.query_params.get('search')
        if search:
            products = products.filter(name__icontains=search)

        cards = {}
        for product in products:
            template = product.template
            prices = []
            for variant in product.variants.all():
                if variant.is_deleted or variant.status != ProductVariant.STATUS_ACTIVE:
                    continue
                final = Decimal(variant.price) + template.commission_for(variant.price)
                prices.append(final)
            if not prices:
                continue
            key = product.grouping_key or f"product:{product.id}"
            card = cards.setdefault(key, {
                'grouping_key': key,
                'name': product.name,
                'template_id': template.id,
                'template_name': template.name,
                'category': product.category_id,
                'min_price': min(prices),
                'max_price': max(prices),
                'vendor_count': 0,
                'product_ids': [],
                'image_url': None,
            })
            card['min_price'] = min(card['min_price'], min(prices))
            card['max_price'] = max(card['max_price'], max(prices))
            card['vendor_count'] += 1
            card['product_ids'].append(product.id)
            if not card['image_url']:
                img = product.images.filter(is_primary=True).first() or product.images.first()
                if img:
                    card['image_url'] = img.image.url

        results = []
        for card in cards.values():
            card['min_price'] = str(card['min_price'].quantize(Decimal('0.01')))
            card['max_price'] = str(card['max_price'].quantize(Decimal('0.01')))
            results.append(card)
        results.sort(key=lambda c: float(c['min_price']))
        return Response({'area_code': area_code, 'count': len(results), 'results': results})


class PublicProductDetailView(APIView):
    """Product detail for buyers (vendor hidden, final price incl. commission)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        product = get_object_or_404(
            Product.objects.select_related('template'), pk=pk, status=Product.STATUS_ACTIVE)
        data = ProductDetailSerializer(product).data
        data.pop('business_family', None)
        template = product.template
        for group in data.get('variant_groups', []):
            for variant in group.get('variants', []):
                price = Decimal(variant['price'])
                variant['final_price'] = str(
                    (price + template.commission_for(price)).quantize(Decimal('0.01')))
        return Response(data)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        return Response(WishlistItemSerializer(wishlist.items.all(), many=True).data)

    def post(self, request):
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        variant = get_object_or_404(ProductVariant, pk=request.data.get('variant'))
        item, _ = WishlistItem.objects.get_or_create(wishlist=wishlist, variant=variant)
        return Response(WishlistItemSerializer(item).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        wishlist = get_object_or_404(Wishlist, user=request.user)
        WishlistItem.objects.filter(wishlist=wishlist, variant_id=request.data.get('variant')).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =====================================================================================
# D. CART
# =====================================================================================
class CartView(APIView):
    """One active, vendor-agnostic cart per buyer (the vendor is chosen later by the admin)."""
    permission_classes = [IsAuthenticated]

    def _active_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user, status=Cart.STATUS_ACTIVE)
        return cart

    def get(self, request):
        cart = self._active_cart(request.user)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = serializer.validated_data['variant']
        quantity = serializer.validated_data['quantity']
        cart = self._active_cart(request.user)
        item, created = CartItem.objects.get_or_create(
            cart=cart, variant=variant,
            defaults={'quantity': quantity, 'unit_price': variant.price})
        if not created:
            item.quantity += quantity
            item.save(update_fields=['quantity', 'updated_at'])
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        variant_id = request.data.get('variant')
        CartItem.objects.filter(cart__user=request.user, cart__status=Cart.STATUS_ACTIVE,
                                variant_id=variant_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =====================================================================================
# E. ORDERS & ROUTING
# =====================================================================================
class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = serializer.validated_data['cart']
        if cart.user_id != request.user.id:
            return Response({'detail': 'Not your cart.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            order = order_service.place_order_from_cart(
                request.user, cart,
                delivery_address=serializer.validated_data.get('delivery_address'),
                note=serializer.validated_data.get('note'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BuyerOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class BuyerOrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BuyerOrderSerializer
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_no']
    ordering_fields = ['placed_at', 'created_at']

    def get_serializer_class(self):
        return BuyerOrderListSerializer if self.action == 'list' else BuyerOrderSerializer

    def get_queryset(self):
        qs = Order.objects.filter(buyer=self.request.user).prefetch_related('items', 'status_logs')
        status_filter = self.request.query_params.get('status')
        return qs.filter(status=status_filter) if status_filter else qs

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            order_service.cancel_order(order, user=request.user, actor=OrderStatusLog.ACTOR_BUYER,
                                       note=request.data.get('note'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(BuyerOrderSerializer(order).data)


class AdminOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Area admin queue + routing."""
    permission_classes = [IsAdminIdentity]
    serializer_class = OrderSerializer
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_no']
    ordering_fields = ['placed_at', 'created_at']

    def get_serializer_class(self):
        return OrderListSerializer if self.action == 'list' else OrderSerializer

    def get_queryset(self):
        qs = Order.objects.prefetch_related('items', 'status_logs', 'vendor_assignments')
        for field in ('status', 'business_family', 'area_node'):
            value = self.request.query_params.get(field)
            if value:
                qs = qs.filter(**{field: value})
        return qs

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        qs = self.get_queryset().filter(
            status__in=[Order.STATUS_PLACED, Order.STATUS_PENDING_ASSIGNMENT])
        page = self.paginate_queryset(qs)
        serializer = OrderListSerializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='candidate-vendors')
    def candidate_vendors(self, request, pk=None):
        """Vendors who stock every line of this order, with price / delivery-time / priority."""
        order = self.get_object()
        return Response(order_service.candidate_vendors(order))

    @action(detail=True, methods=['post'], url_path='assign-vendor')
    def assign_vendor(self, request, pk=None):
        order = self.get_object()
        serializer = AssignVendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order_service.assign_to_vendor(
                order, serializer.validated_data['business_family'], request.user,
                note=serializer.validated_data.get('note'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data)


class VendorOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Vendor-facing: orders offered to / fulfilled by the caller's business."""
    permission_classes = [IsAuthenticatedBusinessOrAdmin]
    serializer_class = OrderSerializer
    pagination_class = CommonPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_no']
    ordering_fields = ['placed_at', 'created_at']

    def get_serializer_class(self):
        return OrderListSerializer if self.action == 'list' else OrderSerializer

    def get_queryset(self):
        business_ids = user_business_family_ids(self.request.user)
        qs = (
            Order.objects
            .filter(vendor_assignments__business_family_id__in=business_ids)
            .distinct()
            .prefetch_related('items', 'status_logs', 'vendor_assignments')
        )
        status_filter = self.request.query_params.get('status')
        return qs.filter(status=status_filter) if status_filter else qs

    def _resolve_business(self, request):
        from user.models import BusinessFamily
        ids = user_business_family_ids(request.user)
        requested = request.data.get('business_family')
        if requested and int(requested) in ids:
            return BusinessFamily.objects.get(pk=requested)
        if ids:
            return BusinessFamily.objects.get(pk=ids[0])
        return None

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        business = self._resolve_business(request)
        try:
            order_service.vendor_accept(order, business, user=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        business = self._resolve_business(request)
        try:
            order_service.vendor_reject(order, business, user=request.user,
                                        note=request.data.get('note'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'], url_path='assign-agent')
    def assign_agent(self, request, pk=None):
        from user.models import User
        order = get_object_or_404(Order, pk=pk)
        agent = get_object_or_404(User, pk=request.data.get('agent'))
        try:
            order_service.assign_agent(order, agent, user=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=['post'], url_path='delivery-status')
    def delivery_status(self, request, pk=None):
        order = get_object_or_404(Order, pk=pk)
        try:
            order_service.update_delivery_status(
                order, request.data.get('status'), user=request.user,
                actor=OrderStatusLog.ACTOR_MERCHANT,
                proof_image=request.FILES.get('proof_image'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data)


# =====================================================================================
# F. DELIVERY AGENT (employee of the fulfilling vendor)
# =====================================================================================
class AgentDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent-facing: the deliveries assigned to the logged-in agent + status/location updates."""
    permission_classes = [IsAuthenticated]
    serializer_class = AgentDeliverySerializer
    pagination_class = CommonPagination

    def get_queryset(self):
        qs = Delivery.objects.select_related('order', 'order__buyer').filter(agent=self.request.user)
        status_filter = self.request.query_params.get('status')
        return qs.filter(status=status_filter) if status_filter else qs

    def _order(self, pk):
        delivery = get_object_or_404(Delivery, pk=pk, agent=self.request.user)
        return delivery.order

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        order = self._order(pk)
        delivery = order_service.agent_accept_delivery(order, user=request.user)
        return Response(AgentDeliverySerializer(delivery).data)

    @action(detail=True, methods=['post'], url_path='status')
    def update_status(self, request, pk=None):
        order = self._order(pk)
        try:
            delivery = order_service.update_delivery_status(
                order, request.data.get('status'), user=request.user,
                actor=OrderStatusLog.ACTOR_AGENT, otp_code=request.data.get('otp_code'),
                proof_image=request.FILES.get('proof_image'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AgentDeliverySerializer(delivery).data)
