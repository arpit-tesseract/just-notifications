from rest_framework import serializers
from .models import AttributeTemplate, Unit, AttributeOption

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


class AttributeTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeTemplate
        fields = ['id', 'name', 'display_name']


class AttributeTemplateDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeTemplate
        fields = ['id', 'name', 'display_name']
