from django.db import models
from simple_history.models import HistoricalRecords
from common.models import AuditMixin, SoftDeleteMixin
from django.utils.text import slugify

# --- Tax Models ---

class TaxCategory(AuditMixin):
    name = models.CharField(max_length=100)
    country_level = models.ForeignKey('configuration.Level', on_delete=models.SET_NULL, null=True, blank=True)
    country_node = models.ForeignKey('configuration.Node', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class Tax(AuditMixin):
    tax_category = models.ForeignKey(TaxCategory, on_delete=models.CASCADE, related_name='taxes')
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.tax_category.name} - {self.name}"

# --- Attribute System ---

class AttributeTemplate(AuditMixin):
    INPUT_CHOICES = [
        ('raw_input', 'Raw Input'),
        ('dropdown', 'Dropdown'),
    ]
    VALUE_DATA_TYPE_CHOICES = [
        ('text', 'Text'),
        ('int', 'Integer'),
        ('float', 'Decimal'),
        ('boolean', 'Boolean'),
        ('date', 'Date'),
        ('datetime', 'Date Time'),
    ]
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    input_type = models.CharField(max_length=50, choices=INPUT_CHOICES)
    value_data_type = models.CharField(max_length=50, choices=VALUE_DATA_TYPE_CHOICES, blank=True, null=True)
    config = models.JSONField(default=dict, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.display_name

class Unit(AuditMixin):
    attribute_template = models.ForeignKey(AttributeTemplate, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.name} ({self.attribute_template.display_name})"

class AttributeOption(AuditMixin):
    attribute_template = models.ForeignKey(AttributeTemplate, on_delete=models.CASCADE, related_name='options')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='attribute_options')
    value = models.CharField(max_length=255)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.attribute_template.name}: {self.value}"

class ProductTemplate(AuditMixin):
    COMMISSION_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    commission_type = models.CharField(max_length=50, choices=COMMISSION_TYPE_CHOICES, blank=True, null=True)
    commission_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return self.display_name

class ProductTemplateAttribute(AuditMixin):
    product_template = models.ForeignKey(ProductTemplate, on_delete=models.CASCADE, related_name='attribute_templates')
    attribute_template = models.ForeignKey(AttributeTemplate, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['display_order']
        unique_together = ('product_template', 'attribute_template')

    def __str__(self):
        return f"{self.product_template.name} - {self.attribute_template.name}"

# --- Product Catalog ---

class Product(AuditMixin, SoftDeleteMixin):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]
    business = models.ForeignKey('user.BusinessFamily', on_delete=models.CASCADE, related_name='products')
    product_template = models.ForeignKey(ProductTemplate, on_delete=models.PROTECT, related_name='products')
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    tax_json = models.JSONField(default=dict, blank=True, null=True)
    
    unit_of_measurement = models.CharField(max_length=50, blank=True, null=True)
    
    is_visible = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    min_order_qty = models.PositiveIntegerField(default=1)
    
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductNodeMapping(AuditMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='node_mappings')
    level = models.ForeignKey('configuration.Level', on_delete=models.CASCADE)
    node = models.ForeignKey('configuration.Node', on_delete=models.PROTECT)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ('product', 'level')

    def __str__(self):
        return f"{self.product.name} - {self.node.name}"


class ProductVariants(AuditMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku_code = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    is_visible = models.BooleanField(default=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.product.name} - {self.sku_code}"

class ProductImage(AuditMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    product_variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField(upload_to='products/')
    
    history = HistoricalRecords()

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductVariantAttributeValue(AuditMixin):
    product_variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE, related_name='attribute_values')
    attribute_template = models.ForeignKey(AttributeTemplate, on_delete=models.CASCADE)
    attribute_option = models.ForeignKey(AttributeOption, on_delete=models.SET_NULL, null=True, blank=True)
    text_value = models.CharField(max_length=255, blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    sub_field_name = models.CharField(max_length=100, blank=True, null=True)
    
    history = HistoricalRecords()

    class Meta:
        unique_together = ('product_variant', 'attribute_template')

    def __str__(self):
        val = self.attribute_option.value if self.attribute_option else self.text_value
        return f"{self.product_variant.sku_code} - {self.attribute_template.name}: {val}"
