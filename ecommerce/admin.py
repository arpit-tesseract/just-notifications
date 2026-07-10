from django.contrib import admin
from .models import (
    TaxCategory, Tax,
    AttributeTemplate, Unit, AttributeOption,
    ProductTemplate, ProductTemplateAttribute, ProductTemplateNodeMapping,
    Product, ProductVariants, ProductImage, ProductVariantAttributeValue
)

@admin.register(TaxCategory)
class TaxCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('is_active',)

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ('name', 'tax_category', 'percentage', 'created_at')
    search_fields = ('name', 'tax_category__name')
    list_filter = ('tax_category',)

@admin.register(AttributeTemplate)
class AttributeTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'input_type', 'is_active', 'created_at')
    search_fields = ('name', 'display_name')
    list_filter = ('input_type', 'is_active')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'attribute_template', 'is_active', 'created_at')
    search_fields = ('name', 'attribute_template__name')
    list_filter = ('is_active', 'attribute_template')

@admin.register(AttributeOption)
class AttributeOptionAdmin(admin.ModelAdmin):
    list_display = ('value', 'attribute_template', 'unit', 'display_order', 'is_active')
    search_fields = ('value', 'attribute_template__name')
    list_filter = ('is_active', 'attribute_template')

@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'commission_type', 'commission_value', 'is_active')
    search_fields = ('name', 'display_name')
    list_filter = ('commission_type', 'is_active')

@admin.register(ProductTemplateAttribute)
class ProductTemplateAttributeAdmin(admin.ModelAdmin):
    list_display = ('product_template', 'attribute_template', 'is_required', 'display_order', 'is_active')
    search_fields = ('product_template__name', 'attribute_template__name')
    list_filter = ('is_required', 'is_active')

@admin.register(ProductTemplateNodeMapping)
class ProductTemplateNodeMappingAdmin(admin.ModelAdmin):
    list_display = ('product_template', 'level', 'node')
    search_fields = ('product_template__name', 'node__name')
    list_filter = ('level',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'product_template', 'status', 'is_visible')
    search_fields = ('name', 'slug', 'business__name')
    list_filter = ('status', 'is_visible', 'product_template')

@admin.register(ProductVariants)
class ProductVariantsAdmin(admin.ModelAdmin):
    list_display = ('sku_code', 'product', 'price', 'is_visible')
    search_fields = ('sku_code', 'product__name')
    list_filter = ('is_visible',)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'product_variant', 'created_at')
    search_fields = ('product__name',)

@admin.register(ProductVariantAttributeValue)
class ProductVariantAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product_variant', 'attribute_template', 'text_value', 'attribute_option')
    search_fields = ('product_variant__sku_code', 'attribute_template__name')
    list_filter = ('attribute_template',)
