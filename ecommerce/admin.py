from django.contrib import admin

from ecommerce.models import (
    Attribute, AttributeOption, Cart, CartItem, Delivery, LowStockAlert, MerchantStoreSetting,
    Order, OrderItem, OrderStatusLog, OrderVendorAssignment, Product, ProductImage,
    ProductPromotion, ProductReview, ProductTemplate, ProductVariant, ProductVariantGroup,
    ProductVariantGroupValue, ReturnRequest, StockMovement, TemplateAttribute, Unit, UnitType,
    VariantAttributeValue, Wishlist, WishlistItem,
)


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 1


class TemplateAttributeInline(admin.TabularInline):
    model = TemplateAttribute
    extra = 1


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'input_type', 'unit_type', 'is_active')
    inlines = [AttributeOptionInline]


@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'commission_type', 'commission_value', 'is_active')
    inlines = [TemplateAttributeInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'business_family', 'template', 'status', 'area_code')
    search_fields = ('name', 'sku')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_no', 'buyer', 'business_family', 'status', 'payment_status',
                    'total_amount', 'commission_amount')
    search_fields = ('order_no',)


for model in (
    UnitType, Unit, AttributeOption, TemplateAttribute, ProductVariantGroup,
    ProductVariantGroupValue, ProductImage, ProductVariant, VariantAttributeValue,
    StockMovement, LowStockAlert, MerchantStoreSetting, ProductPromotion, ProductReview,
    Wishlist, WishlistItem, Cart, CartItem, OrderItem, OrderVendorAssignment, OrderStatusLog,
    Delivery, ReturnRequest,
):
    admin.site.register(model)
