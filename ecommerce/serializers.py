from rest_framework import serializers
from .models import AttributeTemplate, Unit, AttributeOption, ProductTemplate, ProductTemplateAttribute
from user.utils import validate_dimension_nodes, get_level_node_mapping
from configuration.models import Dimension


# =====================================
# Attribute Template Serializers
# =====================================

class UnitSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Unit
        fields = ['id', 'name', 'is_active']

class AttributeOptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    unit_id = serializers.IntegerField(required=False, allow_null=True)
    unit_name = serializers.CharField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = AttributeOption
        fields = ['id', 'unit_id', 'unit_name', 'value', 'display_order', 'is_active']

class AttributeTemplateSerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, required=False)
    options = AttributeOptionSerializer(many=True, required=False)

    class Meta:
        model = AttributeTemplate
        fields = ['id', 'name', 'display_name', 'input_type', 'value_data_type', 'config', 'is_active', 'units', 'options']

    def validate_units(self, value):
        if not value:
            return value
        seen_names = set()
        for unit in value:
            name = unit.get('name')
            if name:
                name_lower = name.lower().strip()
                if name_lower in seen_names:
                    raise serializers.ValidationError(f"Duplicate unit name '{name}' found in the payload.")
                seen_names.add(name_lower)
        return value

    def validate_options(self, value):
        if not value:
            return value
        seen_options = set()
        for option in value:
            val = option.get('value', '').strip()
            unit_id = option.get('unit_id')
            unit_name = option.get('unit_name', '')
            if unit_name:
                unit_name = unit_name.strip().lower()
                
            key = (val.lower(), unit_id, unit_name)
            if key in seen_options:
                raise serializers.ValidationError(f"Duplicate option '{val}' for the same unit found in the payload.")
            seen_options.add(key)
        return value


class AttributeTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeTemplate
        fields = ['id', 'name', 'display_name']


class AttributeTemplateDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeTemplate
        fields = ['id', 'name', 'display_name']


# =====================================
# Product Template Serializers
# =====================================

class ProductTemplateAttributeInputSerializer(serializers.ModelSerializer):
    attribute_template_id = serializers.IntegerField(required=True)

    class Meta:
        model = ProductTemplateAttribute
        fields = ['attribute_template_id', 'is_required', 'display_order', 'is_active']
        
    def validate_attribute_template_id(self, value):
        if not AttributeTemplate.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Attribute Template with ID {value} does not exist.")
        return value

class ProductTemplateInputSerializer(serializers.ModelSerializer):
    attributes = ProductTemplateAttributeInputSerializer(many=True, required=False)
    professional_details = serializers.JSONField(required=True, allow_null=True)

    class Meta:
        model = ProductTemplate
        fields = ['id', 'name', 'display_name', 'commission_type', 'commission_value', 'description', 'is_active', 'attributes', 'professional_details']

    def validate_professional_details(self, value):
        if value:
            dimension_obj, _ = Dimension.objects.get_or_create(name="Professional")
            return validate_dimension_nodes(value, dimension_obj)
        return value

    def validate_attributes(self, value):
        seen_ids = set()
        for attr in value:
            attr_id = attr.get('attribute_template_id')
            if attr_id in seen_ids:
                raise serializers.ValidationError(f"Duplicate attribute_template_id '{attr_id}' found in the payload. A template can only be mapped once.")
            seen_ids.add(attr_id)
        return value


class ProductTemplateAttributeListSerializer(serializers.ModelSerializer):
    attribute_template = AttributeTemplateListSerializer(read_only=True)

    class Meta:
        model = ProductTemplateAttribute
        fields = ['attribute_template', 'is_required', 'display_order', 'is_active']

class ProductTemplateOutputSerializer(serializers.ModelSerializer):
    attributes = ProductTemplateAttributeListSerializer(source='attribute_templates', many=True, read_only=True)
    professional_details = serializers.SerializerMethodField()

    class Meta:
        model = ProductTemplate
        fields = ['id', 'name', 'display_name', 'commission_type', 'commission_value', 'description', 'is_active', 'attributes', 'professional_details']

    def get_professional_details(self, obj):
        if hasattr(obj, 'node_mappings'):
            return get_level_node_mapping(obj.node_mappings.all())
        return {}
        


class ProductTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTemplate
        fields = ['id', 'name', 'display_name', 'commission_type', 'commission_value', 'is_active']


class ProductTemplateDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTemplate
        fields = ['id', 'name', 'display_name']
