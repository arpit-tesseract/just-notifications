from rest_framework import serializers
from .models import *
from shashan.utils.validators import get_object_by_name_or_error
from user_management.models import CustomUser
from .utils import *
from django.apps import apps
from django.db import transaction, IntegrityError
from rest_framework.validators import UniqueTogetherValidator
from django.db.models import F, Max
from django.core.exceptions import ValidationError as DjangoValidationError

import logging

level_logger = logging.getLogger("Levels")

class DimensionIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dimension
        fields = ['id', 'name']


class LevelSerializer(serializers.ModelSerializer):
    child = serializers.PrimaryKeyRelatedField(
        queryset=Level.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    class Meta:
        model = Level
        fields = [
            'id',
            'name',
            'dimension',
            'parent',
            'child',
            'sort_order',
            'single_mode',
            'code_digits',
        ]
        extra_kwargs = {
            'sort_order': {'allow_null': True}
        }
        validators = [
            UniqueTogetherValidator(
                queryset=Level.objects.all(),
                fields=['dimension', 'name'],
                message="Level with this name already exists."
            )
        ]
        
    # v4
    def create(self, validated_data):
        print("Payload:", validated_data)
        single_mode = validated_data.pop('single_mode', False)
        
        # We don't need 'child' input from user. We find it automatically.
        validated_data.pop('child', None) 
        
        dimension = validated_data['dimension']
        parent = validated_data.get('parent')
        requested_order = validated_data.get('sort_order')


        print("Given Parent From Frontend:", parent)

        
        try:
            with transaction.atomic():
                print(f"Try to create level {validated_data.get('name')}")
                level_logger.info(f"Try to create level {validated_data.get('name')}: {validated_data}")
                qs = Level.objects.select_for_update().filter(
                    dimension=dimension,
                )
                
                final_order = None
                
                if single_mode:
                    print("Is single mode.")
                    print("Sort order:", requested_order)
                    if qs.exists():
                        if requested_order is None:
                            max_order = qs.aggregate(Max('sort_order'))['sort_order__max']
                            final_order = (max_order or 0) + 1
                        else:   
                            final_order = requested_order
                    else:
                        final_order = 1
                    
                    qs.filter(sort_order__gte=final_order).update(sort_order=F('sort_order') + 1)
                    validated_data['sort_order'] = final_order

                    # # Check if dimension has levels
                    # if Level.objects.filter(dimension=dimension).exists():
                    validated_data['single_mode'] = True
                    return super().create(validated_data)
                
                else:
                    child = None
                    first_parent = None
                    if parent:
                        print("Has parent:", parent.name if parent else None)
                        # final_order = parent.sort_order + 1
                        if requested_order is None:
                            max_order = qs.aggregate(Max('sort_order'))['sort_order__max']
                            final_order = (max_order or 0) + 1
                        else:
                            final_order = requested_order

                        child = qs.filter(parent=parent).first()
                        print("Child:", child.name if child else None)
                    else:
                        print("No parent.")
                        first_parent = qs.filter(single_mode=False).first()

                        if requested_order is None:
                            if qs.exists() and not first_parent:
                                max_order = qs.aggregate(Max('sort_order'))['sort_order__max']
                                final_order = (max_order or 0) + 1
                            else:
                                final_order = 1
                        else:
                            final_order = requested_order
                        
                    # SHIFT EVERYONE DOWN
                    qs.filter(sort_order__gte=final_order).update(sort_order=F('sort_order') + 1)
                    
                    # CREATE THE NEW NODE
                    validated_data['sort_order'] = final_order
                    level_obj = super().create(validated_data)
                    
                    if child:
                        child.parent = level_obj
                        child.save(update_fields=['parent'])
                    
                    if first_parent:
                        first_parent.parent = level_obj
                        first_parent.save(update_fields=['parent'])
                
                    return level_obj
                
        except Exception as e:
            level_logger.exception("Failed to create level:", e)
            raise serializers.ValidationError({"error": "Failed to create level."})
    
    def update(self, instance, validated_data):
        print("validated_data", validated_data)
        try:
            # Only update name
            level_logger.info(f"Try to updating level {instance.name} to {validated_data.get('name')}")
            instance.code_digits = validated_data.get('code_digits', instance.code_digits)
            instance.name = validated_data.get('name', instance.name)
            instance.save(update_fields=['name', 'code_digits'])
        except Exception as e:
            level_logger.exception("Failed to update level:", e)
            raise serializers.ValidationError({"error": "Failed to update level."})
        return instance
    
    # v3 Working
    # def create(self, validated_data):
    #     single_mode = validated_data.pop('single_mode', False)
    #     child = validated_data.pop('child', None)
    #     dimension = validated_data['dimension']
    #     parent = validated_data.get('parent')
    #     sort_order = validated_data.get('sort_order')

    #     try:
    #         with transaction.atomic():
    #             # Always operate on the same set of rows
    #             qs = Level.objects.select_for_update().filter(
    #                 dimension=dimension,
    #                 is_archived=False
    #             )

    #             # End position or Middle position
    #             if single_mode:
    #                 if qs.exists():
    #                     if sort_order is None:
    #                         sort_order = qs.aggregate(Max('sort_order'))['sort_order__max']
    #                     qs.filter(sort_order__gte=sort_order).update(sort_order=F('sort_order') + 1)
    #                 else:
    #                     sort_order = 1
                    
    #                 validated_data['sort_order'] = sort_order
    #                 return super().create(validated_data)
                    
    #             if parent:
    #                 sort_order = parent.sort_order + 1

    #             # Start position
    #             if parent is None:
    #                 sort_order = 1
                    
    #             qs.filter(sort_order__gte=sort_order).update(sort_order=F('sort_order') + 1)

    #             validated_data['sort_order'] = sort_order
    #             level_obj = super().create(validated_data)
                
    #             # Set parent of middle position or start position
    #             if (parent is None and child) or  (parent and child):
    #                 child.parent = level_obj
    #                 child.save(update_fields=['parent'])
                    
    #         return level_obj
        
    #     except Exception as e:
    #         raise ValidationError({"error": "Failed to create level."})
            
    # v2
    # def create(self, validated_data):
    #     child = validated_data.pop('child', None)

    #     dimension = validated_data['dimension']
    #     sort_order = validated_data.get('sort_order')

    #     with transaction.atomic():
    #         qs = Level.objects.select_for_update().filter(dimension=dimension, is_archived=False)

    #         # normalize sort_order
    #         if sort_order is None:
    #             last = qs.aggregate(m=Max('sort_order'))['m'] or 0
    #             sort_order = last + 1
    #         else:
    #             sort_order = max(1, int(sort_order))  # prevent 0/negative
    #             qs.filter(sort_order__gte=sort_order).update(sort_order=F('sort_order') + 1)

    #         validated_data['sort_order'] = sort_order
    #         level_obj = super().create(validated_data)

    #         if child:
    #             # move child right after new level
    #             child_new_order = sort_order + 1
    #             qs.exclude(pk=child.pk).filter(sort_order__gte=child_new_order).update(sort_order=F('sort_order') + 1)
    #             child.parent = level_obj
    #             child.sort_order = child_new_order
    #             child.save(update_fields=['parent', 'sort_order'])

    #         return level_obj
    
    # v1
    # def create(self, validated_data):
    #     child = validated_data.pop('child', None)
    #     parent = validated_data.get('parent')
    #     dimension = validated_data.get('dimension')
    #     sort_order = validated_data.get('sort_order')
        
    #     with transaction.atomic():
    #         if parent and parent.sort_order is not None:
    #             sort_order = parent.sort_order + 1
                
    #         if sort_order is None:
    #             # If no order provided, put it at the end
    #             last_level = Level.objects.filter(dimension=dimension).aggregate(models.Max('sort_order'))
    #             sort_order = (last_level['sort_order__max'] or 0) + 1
    #         else:
    #             Level.objects.filter(
    #                 dimension=dimension, 
    #                 sort_order__gte=sort_order
    #             ).update(sort_order=F('sort_order') + 1)
                
    #         validated_data['sort_order'] = sort_order
    #         level_obj = super().create(validated_data)
            
    #         if child:
    #             # make space right after the new level
    #             child_new_order = level_obj.sort_order + 1

    #             Level.objects.filter(
    #                 dimension=dimension,
    #                 is_archived=False,
    #                 sort_order__gte=child_new_order
    #             ).exclude(pk=child.pk).update(sort_order=F('sort_order') + 1)

    #             child.parent = level_obj
    #             child.sort_order = child_new_order
    #             child.save(update_fields=['parent', 'sort_order'])
                
    #     return level_obj


class LevelIdNameSerializerWithCustomColumn(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    class Meta:
        model = Level
        fields = ['id', 'name', 'single_mode',  'parent_name', 'code_digits', 'extra_fields_schema']
    
    def get_parent_name(self, obj):
        if obj.parent:
            return obj.parent.name
        
class LevelIdNameSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    class Meta:
        model = Level
        fields = ['id', 'name', 'parent_name', 'single_mode']
    
    def get_parent_name(self, obj):
        if obj.parent:
            return obj.parent.name

class LevelDetailSerializer(serializers.ModelSerializer):
    parent = LevelIdNameSerializer()
    dimension = DimensionIdNameSerializer()
    class Meta:
        model = Level
        fields = ['id', 'name', 'parent', 'dimension', 'sort_order']

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import datetime

class ColumnDefinitionSerializer(serializers.Serializer):
    TYPE_CHOICES = [
        ('char', 'Text (Short)'),
        ('text', 'Text (Long)'),
        ('int', 'Integer'),
        ('positive_int', 'Positive Integer'),
        # ('bigint', 'Big Integer'),
        ('float', 'Decimal/Float'),
        ('boolean', 'Boolean (Checkbox)'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
    ]

    name = serializers.CharField(
        required=True, 
        max_length=50,
        help_text="Column identifier (e.g., 'total_area', 'is_active'). Lowercase & underscores only."
    )
    
    type = serializers.ChoiceField(choices=TYPE_CHOICES, required=True)
    required = serializers.BooleanField(default=False)
    
    # 1. Add default_value field
    default_value = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True,
        help_text="Optional default value"
    )

    max_length = serializers.IntegerField(
        required=False, 
        min_value=1,
        help_text="Only applicable for 'char' type"
    )
    
    def check_name_regex(self, value):
        """
        STRICT RULE: Lowercase letters and underscores only.
        """
        if not re.match(r'^[a-z_]+$', value):
            raise serializers.ValidationError("Name must be lowercase and contain only lettersand underscores (e.g., 'total_area').")
        return value
    
    def validate_name(self, value):
        return self.check_name_regex(value)

    def validate(self, data):
        """
        1. Validate max_length constraints.
        2. Validate default_value type consistency.
        """
        field_type = data.get('type')
        max_len = data.get('max_length')
        default_val = data.get('default_value')
        is_required = data.get('required', False)  
        
        level_obj = self.context.get('level_obj')
        node_count = 0
        if level_obj:
            node_count = Node.objects.filter(level=level_obj).count()
             
        if is_required and node_count > 0 and (default_val is None or default_val == ""):
             raise serializers.ValidationError({
                 "default_value": "You cannot create a 'Required' column without a 'Default Value'."
             })

        # --- A. Validate Max Length Usage ---
        if field_type != 'char' and max_len:
            raise serializers.ValidationError({"max_length": "This field is only valid for type 'char'."})
        
        if field_type == 'char' and not max_len:
             raise serializers.ValidationError({"max_length": "This field is required for type 'char'."})

        # --- B. Validate Default Value ---
        # Only validate if a default value is actually provided

        if field_type == "boolean":
            if default_val is None or str(default_val).strip() == "":
                default_val = "false"
                data['default_value'] = "false"

        if default_val is not None and default_val != "":
            try:
                data['default_value'] = validate_value_type(default_val, field_type, max_len)
            except ValueError:
                raise serializers.ValidationError({
                    "default_value": f"The value '{default_val}' is not a valid {field_type}."
                })
            except ValidationError as e:
                raise serializers.ValidationError({"default_value": e.detail})

        return data


# serializers.py
import re
from rest_framework import serializers

class CustomDefinationUpdateSerializer(serializers.Serializer):
    # New Name (Optional - For Renaming)
    new_name = serializers.CharField(
        required=False,
        max_length=50,
        help_text="Provide ONLY if renaming."
    )
    
    # Metadata Updates
    required = serializers.BooleanField(default=False)
    
    default_value = serializers.CharField(
        required=False, 
        allow_blank=True, 
        allow_null=True
    )

    max_length = serializers.IntegerField(
        required=False, 
        min_value=1,
        help_text="Only applicable if the existing column is type 'char'"
    )

    def check_name_regex(self, value):
        """
        STRICT RULE: Lowercase letters, numbers, and underscores only.
        """
        if not re.match(r'^[a-z_]+$', value):
            raise serializers.ValidationError("Name must be lowercase and contain only letters, numbers, and underscores.")
        return value

    def validate_new_name(self, value):
        if value:
            return self.check_name_regex(value)
        return value
    
    # def validate_default_value(self, value):
    #     instance = self.instance
    #     field_type = instance.type
    #     if field_type == "boolean" and (value == "" or value is None):
    #         value = "false"

    #     return value


class NodeAliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeAlias
        fields = ['name', 'note']
    

class NodeIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ['id', 'name', 'code', 'parent']

class NodeOutputSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    alias = serializers.SerializerMethodField()
    class Meta:
        model = Node
        fields = [
            'id', 
            'name',
            'code',
            'is_hidden',
            'on_hold',
            'hold_date',
            'created_at',
            'updated_at',
            'attributes',
            'alias', 
        ]
    
    def get_code(self, obj):
        if not obj:
            return None
        
        digits = obj.level.code_digits if obj.level else 2
        parent_node = obj.parent
        
        try:
            current_code = str(obj.code).zfill(digits)
        except:
            current_code =  obj.code  
        
        #2. Get the total count from our annotation
        # We use getattr because parent_total_count only exists if we annotate it
        if obj.parent_id is None:
            return current_code
        
        total_siblings = getattr(obj, 'parent_total_count', 0)
        padded_total = str(total_siblings).zfill(parent_node.level.code_digits)

        # 3. Format as (current/total)
        return f"{current_code}/{padded_total}" 
    
    def get_alias(self, obj):
        return list(obj.aliases.values('name')) 
    
    
    def get_attributes(self, obj):
        """
        Returns a list of attribute objects with metadata:
        [
            { "name": "total_area", "value": 500, "type": "int", "label": "Total Area" },
            { "name": "is_active", "value": true, "type": "boolean", "label": "Active?" }
        ]
        """
        # 1. Get stored data (or empty dict)
        stored_data = obj.attributes or {}

        # 2. Get Schema (Columns Definition)
        # Check if level exists to avoid errors
        if not obj.level or not obj.level.extra_fields_schema:
            return []

        # 3. Build the List
        attribute_list = []
        
        for col_def in obj.level.extra_fields_schema:
            name = col_def.get('name')
            data_type = col_def.get('type')
            default_value = col_def.get('default_value')
            value = stored_data.get(name, default_value)
            
            attribute_list.append({
                "name": name,        # The database key (e.g., "total_area")
                "value": value,     # The actual data (e.g., 500 or None)
                "type": data_type,  # The type (e.g., "int")
            })

        return attribute_list



class NodeSerializer(serializers.ModelSerializer):
    alias = NodeAliasSerializer(many=True, required=False, allow_null=True)
    class Meta:
        model = Node
        exclude = ['created_at', 'updated_at']
        # validators = []
    
    def validate(self, attrs):
        instance = getattr(self, 'instance', None)
        
        # 1. Setup Variables (Get New Value or Fallback to Instance Value)
        # We need these to be sure we are checking the right combination
        dimension = attrs.get('dimension') if 'dimension' in attrs else (instance.dimension if instance else None)
        level = attrs.get('level') if 'level' in attrs else (instance.level if instance else None)
        parent = attrs.get('parent') if 'parent' in attrs else (instance.parent if instance else None)
        code = attrs.get('code') if 'code' in attrs else (instance.code if instance else None)

        code_digits = level.code_digits if level else 2
        if code and len(str(code)) > code_digits:
            raise serializers.ValidationError({
                "code": f"Code must be {code_digits} digits long."
            })
        
        attributes = attrs.get('attributes', {})
        if instance and 'attributes' not in attrs:
            attributes = instance.attributes or {}

        # ---------------------------------------------------------
        # 2. NEW LOGIC: Conditional Unique Code Check
        # ---------------------------------------------------------
        if code is not None:
            # Start with all nodes
            qs = Node.objects.all()
            
            # If updating, exclude ourselves
            if instance:
                qs = qs.exclude(pk=instance.pk)
            
            # CASE A: Child Node (Parent is NOT NULL)
            if parent is not None:
                if qs.filter(parent=parent, level=level, code=code).exists():
                    raise serializers.ValidationError({
                        "code": f"Code '{code}' is already used by another node under parent '{parent.name}'."
                    })
            
            # CASE B: Top/Global Node (Parent IS NULL)
            else:
                if qs.filter(parent__isnull=True, dimension=dimension, level=level, code=code).exists():
                    raise serializers.ValidationError({
                        "code": f"Code '{code}' is already used."
                    })

        # ---------------------------------------------------------
        # 3. EXISTING LOGIC: Parent Consistency Checks
        # ---------------------------------------------------------
        if parent:
            # We use the resolved 'dimension' variable we created at step 1
            if parent.dimension != dimension:
                raise serializers.ValidationError({"parent": "Parent must be in the same dimension."})
            
            if instance and parent.id == instance.id:
                raise serializers.ValidationError({"parent": "Parent cannot be self."})
        else:
            if level.parent:
                raise serializers.ValidationError({"parent": "Parent is required."})

        
        # ---------------------------------------------------------
        # 4. EXISTING LOGIC: Schema Validation (Attributes)
        # ---------------------------------------------------------
        if level:
            # A. Get allowed keys from Level Schema
            schema = level.extra_fields_schema or []
            
            if attributes:
                allowed_keys = {col.get('name') for col in schema}
                
                # B. Get incoming keys
                incoming_keys = set(attributes.keys())
                
                # C. Find 'Junk' keys (Incoming - Allowed)
                unknown_keys = incoming_keys - allowed_keys
                
                if unknown_keys:
                    raise serializers.ValidationError({
                        "attributes": f"Invalid custom columns detected: {list(unknown_keys)}. Allowed columns: {list(allowed_keys)}"
                    })
            
            # D. Strict Type Validation via Model Method
            # Create temp node to reuse the model's clean logic
            temp_node = Node(level=level, attributes=attributes)
            try:
                temp_node.validate_attributes()
            except DjangoValidationError as e:
                # Convert Django Error to DRF Error
                if hasattr(e, 'messages'):
                     raise serializers.ValidationError({"attributes": e.messages})
                raise serializers.ValidationError({"attributes": str(e)})
        
        # Pass the processed attributes back to attrs
        attrs['attributes'] = attributes
        return attrs

    def create(self, validated_data):
        alias_data = validated_data.pop('alias', [])
        try:
            with transaction.atomic():
                node = super().create(validated_data)
                
                # create alias
                if alias_data:
                    for alias in alias_data:
                        NodeAlias.objects.create(node=node, **alias)
        except Exception as e:
            raise ValidationError({"error": "Error creating node."})
                
        return node

    def update(self, instance, validated_data):
        alias_data = validated_data.pop('alias', [])
        print('Alias data:', alias_data)
        instance = super().update(instance, validated_data)
        
        if alias_data is None:
            NodeAlias.objects.filter(node=instance).delete()

        if alias_data:
            incoming_name = [alias['name'] for alias in alias_data]
            # delete alias where name not in incoming
            NodeAlias.objects.filter(node=instance).exclude(name__in=incoming_name).delete()
            
            # update or create alias
            for alias in alias_data:
                if not NodeAlias.objects.filter(node=instance, name__iexact=alias.get('name')).exists():
                    NodeAlias.objects.update_or_create(
                        node=instance,
                        name=alias.get('name'),
                        defaults={}
                    )
        
                
        return instance


class SplitNodeSerializer(serializers.Serializer):
    node = NodeSerializer()
    children_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[],
    )


class SplitNodeInputSerializer(serializers.Serializer):
    number_of_splits = serializers.IntegerField()
    splits = SplitNodeSerializer(many=True)

    def validate(self, attrs):
        splits = attrs.get('splits')
        number_of_splits = attrs.get('number_of_splits')

        if len(splits) < 2 or number_of_splits < 2:
        # if number_of_splits < 2:
            raise serializers.ValidationError({'number_of_splits': "Minimum number of splits must be at least 2"})
        
        if number_of_splits != len(splits):
            raise serializers.ValidationError({'error': 'Failed to split node.'})
        
        # Validate children_ids overlap between parts
        seen = set()
        overlap = set()
        for idx, p in enumerate(splits):
            ids = p.get("children_ids", [])
            for cid in ids:
                if cid in seen:
                    overlap.add(cid)
                seen.add(cid)

        if overlap:
            raise serializers.ValidationError({
                "children_ids": f"Same child ids appear in multiple parts: {sorted(list(overlap))}"
            })

        return attrs

class RemoveTimestampMixin:
    """
    Mixin to automatically exclude 'time_stamp' from the serializer fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove time_stamp if it exists in the fields
        self.fields.pop('time_stamp', None)
        

class DynamicFieldsModelSerializer(RemoveTimestampMixin, serializers.ModelSerializer):
    code = serializers.SerializerMethodField()
    
    """
    Base serializer that allows dynamic exclusion of fields
    via either context={'exclude_fields': [...]} or argument exclude_fields=[...].
    """
    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', None)
        super().__init__(*args, **kwargs)

        if exclude_fields is None:
            exclude_fields = self.context.get('exclude_fields', [])

        for field in exclude_fields:
            self.fields.pop(field, None)
            
    def get_code(self, obj):
        # 1. Priority: Check if we manually forced raw code in context (for nested parents)
        if self.context.get('use_raw_code'):
            return get_two_digit(obj.code)

        # 2. Check the View Action (List vs Detail)
        view = self.context.get('view')
        if view and hasattr(view, 'action'):
            # If we are viewing a single item (api/<id>), return RAW code
            if view.action == 'retrieve':
                return get_two_digit(obj.code)
            
            # If we are listing items (api/), return FORMATTED code
            if view.action == 'list':
                return obj.get_formatted_code()

        # Default fallback (e.g., inside other views)
        return obj.get_formatted_code()


# =================================================
# Residential 
# =================================================

# ========== Glob ==========
class GlobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Glob
        fields = '__all__'
        read_only_fields = ['id']

class GlobDetailSerializer(DynamicFieldsModelSerializer):
    code = serializers.SerializerMethodField()
    class Meta:
        model = Glob
        fields = '__all__'
        read_only_fields = ['id']

class GlobIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Glob
        fields = ["id", "name"] 


# ========== Continent ==========
class ContinentIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = ["id", "name"]

class ContinentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Continent.objects.all(),
                fields=['glob', 'name'],
                message="A continent with this name already exists in the selected glob.",
            )
        ]


class ContinentDetailSerializer(DynamicFieldsModelSerializer):
    glob = serializers.SerializerMethodField()
    class Meta:
        model = Continent
        fields = '__all__'
        read_only_fields = ['id']
    
    def get_glob(self, obj):
        serializer = GlobDetailSerializer(
            obj.glob,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== Country ==========
class CountryIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]
        
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Country.objects.all(),
                fields=['continent', 'name'],
                message="A country with this name already exists in the selected continent.",
            )
        ]

class CountryDetailSerializer(DynamicFieldsModelSerializer):
    continent = serializers.SerializerMethodField()
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = [f for f in Country._meta.fields]
    
    def get_continent(self, obj):
        serializer = ContinentDetailSerializer(
            obj.continent,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== State ==========
class StateIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name"]
        
class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=State.objects.all(),
                fields=['country', 'name'],
                message="A state with this name already exists in the selected country.",
            )
        ]


class StateDetailSerializer(DynamicFieldsModelSerializer):
    country = serializers.SerializerMethodField()  
    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = [f for f in State._meta.fields]
    
    def get_country(self, obj):
        serializer = CountryDetailSerializer(
            obj.country,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
    
    
# ========== District ==========
class DistrictIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]
        
class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=District.objects.all(),
                fields=['state', 'name'],
                message="A district with this name already exists in the selected state.",
            )
        ]


class DistrictDetailSerializer(DynamicFieldsModelSerializer):
    state = serializers.SerializerMethodField()
    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = [f for f in District._meta.fields]
    
    def get_state(self, obj):
        serializer = StateDetailSerializer(
            obj.state,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== Taluka ==========
class TalukaIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taluka
        fields = ["id", "name"]
        
class TalukaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taluka
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Taluka.objects.all(),
                fields=['district', 'name'],
                message="A taluka with this name already exists in the selected district.",
            )
        ]


class TalukaDetailSerializer(DynamicFieldsModelSerializer):
    district = serializers.SerializerMethodField()
    class Meta:
        model = Taluka
        fields = '__all__'
        read_only_fields = [f for f in Taluka._meta.fields]
    
    def get_district(self, obj):
        serializer = DistrictDetailSerializer(
            obj.district,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== CityVillage ==========
class CityVillageIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityVillage
        fields = ["id", "name"]
        
class CityVillageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityVillage
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=CityVillage.objects.all(),
                fields=['taluka', 'name'],
                message="A city/village with this name already exists in the selected taluka.",
            )
        ]

class CityVillageDetailSerializer(DynamicFieldsModelSerializer):
    taluka = serializers.SerializerMethodField()
    class Meta:
        model = CityVillage
        fields = '__all__'
        read_only_fields = [f for f in CityVillage._meta.fields]
    
    def get_taluka(self, obj):
        serializer = TalukaDetailSerializer(
            obj.taluka,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data

class SectorIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["id", "name"]

class BrandIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]

class ProductIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name"]

# ========== Ward ==========
class WardIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ["id", "name"]

class WardFlashOutputSerializer(serializers.ModelSerializer):
    brand = BrandIdNameSerializer(source='product.brand')
    product = ProductIdNameSerializer()
    sector = SectorIdNameSerializer(source='product.brand.type.subdepartment.department.subsector.sector')

    class Meta:
        model = WardFlash
        fields = ['id', 'sector', 'brand', 'product', 'value']

class WardFlashSerializer(serializers.ModelSerializer):
    existing_id = serializers.IntegerField(required=False, allow_null=True)
    class Meta:
        model = WardFlash
        fields = ['existing_id', 'product', 'value']

class WardFlashBulkInputSerializer(serializers.Serializer):
    flashes = WardFlashSerializer(many=True)
    
class WardSerializer(serializers.ModelSerializer):
    flashes = WardFlashSerializer(
        required=False, 
        allow_null=True, 
        many=True
    )
    class Meta:
        model = Ward
        fields = ['city_village', 'name', 'code', 'is_hidden', 'on_hold', 'hold_date', 'flashes']
        validators = [
            UniqueTogetherValidator(
                queryset=Ward.objects.all(),
                fields=['city_village', 'name'],
                message="A ward with this name already exists in the selected city/village.",
            )
        ]
    
    def create(self, validated_data):
        flashes = validated_data.pop("flashes", [])
        with transaction.atomic():
            ward = Ward.objects.create(**validated_data)
            for flash in flashes:
                flash.pop("existing_id", None)
                WardFlash.objects.create(ward=ward, **flash)
            return ward

    def update(self, instance, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            # update ward
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # update flashes
            if flash_data is not None:
                incoming_flash_ids = [f.get("existing_id") for f in flash_data if f.get("existing_id")]

                # Delete existing flashes which are not included in new request
                WardFlash.objects.filter(ward=instance).exclude(id__in=incoming_flash_ids).delete()

                # Process incoming flashes
                for flash in flash_data:
                    flash_id = flash.get("existing_id")

                    if flash_id:
                        # Update existing flash
                        try:
                            obj = WardFlash.objects.get(id=flash_id, ward=instance)
                        except WardFlash.DoesNotExist:
                            raise serializers.ValidationError(
                                f"Flash with id {flash_id} does not exist."
                            )
                            
                        for attr, value in flash.items():
                            if attr != "existing_id":
                                setattr(obj, attr, value)
                        obj.save()

                    else:
                        # Create new flash
                        flash.pop("existing_id", None)
                        WardFlash.objects.create(ward=instance, **flash)
            else:
                ward_flash_objs = instance.ward_flashes.all()
                if ward_flash_objs.exists():
                    ward_flash_objs.delete()

            return instance

class WardDetailSerializer(DynamicFieldsModelSerializer):
    city_village = serializers.SerializerMethodField()
    flashes = WardFlashOutputSerializer(source="ward_flashes", many=True)
    class Meta:
        model = Ward
        fields = '__all__'
        read_only_fields = [f for f in Ward._meta.fields]
    
    def get_city_village(self, obj):
        if not obj.city_village:
            return None
        serializer = CityVillageDetailSerializer(
            obj.city_village,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== Society ==========
class SocietyIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Society
        fields = ["id", "name"]

class SocietyFlashOutputSerializer(serializers.ModelSerializer):
    brand = BrandIdNameSerializer(source='product.brand')
    product = ProductIdNameSerializer()
    sector = SectorIdNameSerializer(source='product.brand.type.subdepartment.department.subsector.sector')

    class Meta:
        model = SocietyFlash
        fields = ['id', 'sector', 'brand', 'product', 'value']
        
class SocietyFlashSerializer(serializers.ModelSerializer):
    existing_id = serializers.IntegerField(required=False)
    class Meta:
        model = SocietyFlash
        fields = ['existing_id', 'product', 'value']

class SocietyFlashBulkInputSerializer(serializers.Serializer):
    flashes = SocietyFlashSerializer(many=True)

class SocietySerializer(serializers.ModelSerializer):
    flashes = SocietyFlashSerializer(
        required=True, 
        allow_null=True, 
        many=True
    )
    class Meta:
        model = Society
        fields = ['id', 'ward', 'name', 'code', 'is_hidden', 'on_hold', 'hold_date', 'flashes']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            society = Society.objects.create(**validated_data)
            for flash in flash_data:
                flash.pop("existing_id", None)
                SocietyFlash.objects.create(society=society, **flash)
            return society
    
    def update(self, instance, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            # update society
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # update flashes
            if flash_data is not None:
                incoming_flash_ids = [f.get("existing_id") for f in flash_data if f.get("existing_id")]

                # Delete existing flashes which are not included in new request
                SocietyFlash.objects.filter(society=instance).exclude(id__in=incoming_flash_ids).delete()

                # Process incoming flashes
                for flash in flash_data:
                    flash_id = flash.get("existing_id")

                    if flash_id:
                        # Update existing flash
                        obj = SocietyFlash.objects.get(id=flash_id, society=instance)
                        for attr, value in flash.items():
                            if attr != "existing_id":
                                setattr(obj, attr, value)
                        obj.save()

                    else:
                        # Create new flash
                        flash.pop("existing_id", None)
                        SocietyFlash.objects.create(society=instance, **flash)
            else:
                society_flash_objs = instance.society_flashes.all()
                if society_flash_objs.exists():
                    society_flash_objs.delete()
            
            return instance

class SocietyDetailSerializer(DynamicFieldsModelSerializer):
    ward = serializers.SerializerMethodField()
    flashes = SocietyFlashOutputSerializer(source="society_flashes", many=True)
    class Meta:
        model = Society
        fields = '__all__'
        read_only_fields = [f for f in Society._meta.fields]
    
    def get_ward(self, obj):
        if not obj.ward:
            return None
        
        serializer = WardDetailSerializer(
            obj.ward,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== Block ==========
class BlockIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["id", "name"]

class BlockFlashOutputSerializer(serializers.ModelSerializer):
    brand = BrandIdNameSerializer(source='product.brand')
    product = ProductIdNameSerializer()
    sector = SectorIdNameSerializer(source='product.brand.type.subdepartment.department.subsector.sector')

    class Meta:
        model = BlockFlash
        fields = ['id', 'sector', 'brand', 'product', 'value']
        
class BlockFlashSerializer(serializers.ModelSerializer):
    existing_id = serializers.IntegerField(required=False)
    class Meta:
        model = BlockFlash
        fields = ['existing_id', 'product', 'value']

class BlockFlashBulkInputSerializer(serializers.Serializer):
    flashes = BlockFlashSerializer(many=True)

class BlockSerializer(serializers.ModelSerializer):
    flashes = BlockFlashSerializer(
        required=True, 
        allow_null=True, 
        many=True
    )
    class Meta:
        model = Block
        fields = ['id', 'society', 'name', 'code', 'is_hidden', 'on_hold', 'hold_date', 'flashes']
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Block.objects.all(),
                fields=['society', 'name'],
                message="A block with this name already exists in the selected society.",
            )
        ]
    
    def create(self, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            block = Block.objects.create(**validated_data)
            for flash in flash_data:
                flash.pop("existing_id", None)
                BlockFlash.objects.create(block=block, **flash)
            return block
    
    def update(self, instance, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            # update block
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # update flashes
            if flash_data is not None:
                incoming_flash_ids = [f.get("existing_id") for f in flash_data if f.get("existing_id")]

                # Delete existing flashes which are not included in new request
                BlockFlash.objects.filter(block=instance).exclude(id__in=incoming_flash_ids).delete()

                # Process incoming flashes
                for flash in flash_data:
                    flash_id = flash.get("existing_id")

                    if flash_id:
                        # Update existing flash
                        obj = BlockFlash.objects.get(id=flash_id, block=instance)
                        for attr, value in flash.items():
                            if attr != "existing_id":
                                setattr(obj, attr, value)
                        obj.save()

                    else:
                        # Create new flash
                        flash.pop("existing_id", None)
                        BlockFlash.objects.create(block=instance, **flash)
            else:
                block_flash_objs = instance.block_flashes.all()
                if block_flash_objs.exists():
                    block_flash_objs.delete()
                    
            return instance
        
class BlockDetailSerializer(DynamicFieldsModelSerializer):
    society = serializers.SerializerMethodField()
    flashes = BlockFlashOutputSerializer(source="block_flashes", many=True)
    class Meta:
        model = Block
        fields = '__all__'
        read_only_fields = [f for f in Block._meta.fields]
    
    def get_society(self, obj):
        if not obj.society:
            return None
        serializer = SocietyDetailSerializer(
            obj.society,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== Floor ==========
class FloorIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = ["id", "no"]

class FloorFlashOutputSerializer(serializers.ModelSerializer):
    brand = BrandIdNameSerializer(source='product.brand')
    product = ProductIdNameSerializer()
    sector = SectorIdNameSerializer(source='product.brand.type.subdepartment.department.subsector.sector')

    class Meta:
        model = FloorFlash
        fields = ['id', 'sector', 'brand', 'product', 'value']
        
class FloorFlashSerializer(serializers.ModelSerializer):
    existing_id = serializers.IntegerField(required=False)
    class Meta:
        model = FloorFlash
        fields = ['existing_id', 'product', 'value']

class FloorFlashBulkInputSerializer(serializers.Serializer):
    flashes = FloorFlashSerializer(many=True)
        
class FloorSerializer(serializers.ModelSerializer):
    flashes = FloorFlashSerializer(
        required=True, 
        allow_null=True, 
        many=True
    )
    class Meta:
        model = Floor
        fields = ['id', 'block', 'no', 'is_hidden', 'on_hold', 'hold_date', 'flashes']
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Floor.objects.all(),
                fields=['block', 'no'],
                message="A floor with this name already exists in the selected block.",
            )
        ]
    
    def create(self, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            floor = Floor.objects.create(**validated_data)
            for flash in flash_data:
                flash.pop("existing_id", None)
                FloorFlash.objects.create(floor=floor, **flash)
            return floor
    
    def update(self, instance, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            # update floor
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # update flashes
            if flash_data is not None:
                incoming_flash_ids = [f.get("existing_id") for f in flash_data if f.get("existing_id")]

                # Delete existing flashes which are not included in new request
                FloorFlash.objects.filter(floor=instance).exclude(id__in=incoming_flash_ids).delete()

                # Process incoming flashes
                for flash in flash_data:
                    flash_id = flash.get("existing_id")

                    if flash_id:
                        # Update existing flash
                        obj = FloorFlash.objects.get(id=flash_id, floor=instance)
                        for attr, value in flash.items():
                            if attr != "existing_id":
                                setattr(obj, attr, value)
                        obj.save()

                    else:
                        # Create new flash
                        flash.pop("existing_id", None)
                        FloorFlash.objects.create(floor=instance, **flash)
            else:
                floor_flash_objs = instance.floor_flashes.all()
                if floor_flash_objs.exists():
                    floor_flash_objs.delete()
                    
            return instance


class FloorDetailSerializer(DynamicFieldsModelSerializer):
    block = serializers.SerializerMethodField()
    flashes = FloorFlashOutputSerializer(source="floor_flashes", many=True)
    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = [f for f in Floor._meta.fields]
    
    def get_block(self, obj):
        if not obj.block:
            return None
        serializer = BlockDetailSerializer(
            obj.block,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== House ==========
class HouseIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ["id", "no"]

class HouseFlashOutputSerializer(serializers.ModelSerializer):
    brand = BrandIdNameSerializer(source='product.brand')
    product = ProductIdNameSerializer()
    sector = SectorIdNameSerializer(source='product.brand.type.subdepartment.department.subsector.sector')

    class Meta:
        model = HouseFlash
        fields = ['id', 'sector', 'brand', 'product', 'value']
        
class HouseFlashSerializer(serializers.ModelSerializer):
    existing_id = serializers.IntegerField(required=False)
    class Meta:
        model = HouseFlash
        fields = ['existing_id', 'product', 'value']

class HouseFlashBulkInputSerializer(serializers.Serializer):
    flashes = HouseFlashSerializer(many=True)

class HouseSerializer(serializers.ModelSerializer):
    flashes = HouseFlashSerializer(
        required=True, 
        allow_null=True, 
        many=True
    )
    class Meta:
        model = House
        fields = ['floor', 'no', 'code', 'is_hidden', 'on_hold', 'hold_date', 'flashes']
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=House.objects.all(),
                fields=['floor', 'no'],
                message="A house with this name already exists in the selected block.",
            )
        ]
        
    def create(self, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            house = House.objects.create(**validated_data)
            for flash in flash_data:
                flash.pop("existing_id", None)
                HouseFlash.objects.create(house=house, **flash)
            return house
    
    def update(self, instance, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            # update house
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # update flashes
            if flash_data is not None:
                incoming_flash_ids = [f.get("existing_id") for f in flash_data if f.get("existing_id")]

                # Delete existing flashes which are not included in new request
                HouseFlash.objects.filter(house=instance).exclude(id__in=incoming_flash_ids).delete()

                # Process incoming flashes
                for flash in flash_data:
                    flash_id = flash.get("existing_id")

                    if flash_id:
                        # Update existing flash
                        obj = HouseFlash.objects.get(id=flash_id, house=instance)
                        for attr, value in flash.items():
                            if attr != "existing_id":
                                setattr(obj, attr, value)
                        obj.save()

                    else:
                        # Create new flash
                        flash.pop("existing_id", None)
                        HouseFlash.objects.create(house=instance, **flash)
            else:
                house_flash_objs = instance.house_flashes.all()
                if house_flash_objs.exists():
                    house_flash_objs.delete()
                    
            return instance

class HouseDetailSerializer(DynamicFieldsModelSerializer):
    floor = serializers.SerializerMethodField()
    flashes = HouseFlashOutputSerializer(source="house_flashes", many=True)
    class Meta:
        model = House
        fields = '__all__'
        read_only_fields = [f for f in House._meta.fields]
    
    def get_floor(self, obj):
        if not obj.floor:
            return None
        serializer = FloorDetailSerializer(
            obj.floor,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


# ========== Room ==========

class RoomTypeIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ['id', 'name']
        
        
class RoomIdNameSerializer(serializers.ModelSerializer):
    room_type_name = serializers.SerializerMethodField()
    class Meta:
        model = Room
        fields = ["id", "no", "room_type_name"]
    
    def get_room_type_name(self, obj):
        if not obj.room_type:
            return None
        return obj.room_type.name

class RoomFlashOutputSerializer(serializers.ModelSerializer):
    brand = BrandIdNameSerializer(source='product.brand')
    product = ProductIdNameSerializer()
    sector = SectorIdNameSerializer(source='product.brand.type.subdepartment.department.subsector.sector')

    class Meta:
        model = RoomFlash
        fields = ['id', 'sector', 'brand', 'product', 'value']
        
class RoomFlashSerializer(serializers.ModelSerializer):
    existing_id = serializers.IntegerField(required=False)
    class Meta:
        model = RoomFlash
        fields = ['existing_id', 'product', 'value']

class RoomFlashBulkInputSerializer(serializers.Serializer):
    flashes = RoomFlashSerializer(many=True)
        
class RoomSerializer(serializers.ModelSerializer):
    flashes = RoomFlashSerializer(
        required=True, 
        allow_null=True, 
        many=True
    )
    class Meta:
        model = Room
        fields = ['id', 'house', 'no', 'code', 'is_hidden', 'on_hold', 'hold_date', 'flashes']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            room = Room.objects.create(**validated_data)
            for flash in flash_data:
                flash.pop("existing_id", None)
                RoomFlash.objects.create(room=room, **flash)
            return room
    
    def update(self, instance, validated_data):
        flash_data = validated_data.pop("flashes", [])
        with transaction.atomic():
            # update room
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            # update flashes
            if flash_data is not None:
                incoming_flash_ids = [f.get("existing_id") for f in flash_data if f.get("existing_id")]

                # Delete existing flashes which are not included in new request
                RoomFlash.objects.filter(room=instance).exclude(id__in=incoming_flash_ids).delete()

                # Process incoming flashes
                for flash in flash_data:
                    flash_id = flash.get("existing_id")

                    if flash_id:
                        # Update existing flash
                        obj = RoomFlash.objects.get(id=flash_id, room=instance)
                        for attr, value in flash.items():
                            if attr != "existing_id":
                                setattr(obj, attr, value)
                        obj.save()

                    else:
                        # Create new flash
                        flash.pop("existing_id", None)
                        RoomFlash.objects.create(room=instance, **flash)
            else:
                room_flash_objs = instance.room_flashes.all()
                if room_flash_objs.exists():
                    room_flash_objs.delete()
                    
            return instance

class RoomDetailSerializer(DynamicFieldsModelSerializer):
    house = serializers.SerializerMethodField()
    room_type = RoomTypeIdNameSerializer()
    flashes = RoomFlashOutputSerializer(source="room_flashes", many=True)
    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = [f for f in Room._meta.fields]
    
    def get_house(self, obj):
        if not obj.house:
            return None
        serializer = HouseDetailSerializer(
            obj.house,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
    
# ======================================================
# Personal 
# ======================================================
class ReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Religion
        fields = '__all__'
        read_only_fields = ['id']

class ReligionDetailSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Religion
        fields = '__all__'
        
class SampradaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Sampraday
        fields = '__all__'
        read_only_fields = ['id']

class SampradayDetailSerializer(DynamicFieldsModelSerializer):
    religion = serializers.SerializerMethodField()
    class Meta:
        model = Sampraday
        fields = '__all__'
        read_only_fields = [f for f in Sampraday._meta.fields]
    
    def get_religion(self, obj):
        serializer = ReligionDetailSerializer(
            obj.religion,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class PanthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Panth
        fields = '__all__'
        read_only_fields = ['id']
        
class PanthDetailSerializer(DynamicFieldsModelSerializer):
    sampraday = serializers.SerializerMethodField()
    class Meta:
        model = Panth
        fields = '__all__'
        read_only_fields = [f for f in Panth._meta.fields]
    
    def get_sampraday(self, obj):
        serializer = SampradayDetailSerializer(
            obj.sampraday,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class AwasthaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Awastha
        fields = '__all__'
        read_only_fields = ['id']

class AwasthaDetailSerializer(DynamicFieldsModelSerializer):
    # panth = serializers.SerializerMethodField()
    class Meta:
        model = Awastha
        fields = '__all__'
        read_only_fields = [f for f in Awastha._meta.fields]
    
    # def get_panth(self, obj):
    #     serializer = PanthDetailSerializer(
    #         obj.panth,
    #         context={
            #     'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
            #     'use_raw_code': True
            # }
    #     )
    #     return serializer.data

class VarnaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Varna
        fields = '__all__'
        read_only_fields = ['id']

class VarnaDetailSerializer(DynamicFieldsModelSerializer):
    panth = serializers.SerializerMethodField()
    class Meta:
        model = Varna
        fields = '__all__'
        read_only_fields = [f for f in Varna._meta.fields]
    
    def get_panth(self, obj):
        serializer = PanthDetailSerializer(
            obj.panth,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class CasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = '__all__'
        read_only_fields = ['id']

class CasteDetailSerializer(DynamicFieldsModelSerializer):
    varna = serializers.SerializerMethodField()
    class Meta:
        model = Caste
        fields = '__all__'
        read_only_fields = [f for f in Caste._meta.fields]
    
    def get_varna(self, obj):
        serializer = VarnaDetailSerializer(
            obj.varna,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class SubCasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCaste
        fields = '__all__'
        read_only_fields = ['id']

class SubCasteDetailSerializer(DynamicFieldsModelSerializer):
    caste = serializers.SerializerMethodField()
    class Meta:
        model = SubCaste
        fields = '__all__'
        read_only_fields = [f for f in SubCaste._meta.fields]
    
    def get_caste(self, obj):
        serializer = CasteDetailSerializer(
            obj.caste,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
    
    
class GotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gotra
        fields = '__all__'
        read_only_fields = ['id']

class GotraDetailSerializer(DynamicFieldsModelSerializer):
    subcaste = serializers.SerializerMethodField()
    class Meta:
        model = Gotra
        fields = '__all__'
        read_only_fields = [f for f in Gotra._meta.fields]
    
    def get_subcaste(self, obj):
        serializer = SubCasteDetailSerializer(
            obj.subcaste,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class SubGotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGotra
        fields = '__all__'
        read_only_fields = ['id']

class SubGotraDetailSerializer(DynamicFieldsModelSerializer):
    gotra = serializers.SerializerMethodField()
    class Meta:
        model = SubGotra
        fields = '__all__'
        read_only_fields = [f for f in SubGotra._meta.fields]
    
    def get_gotra(self, obj):
        serializer = GotraDetailSerializer(
            obj.gotra,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class KulSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kul
        fields = '__all__'
        read_only_fields = ['id']

class KulDetailSerializer(DynamicFieldsModelSerializer):
    subgotra = serializers.SerializerMethodField()
    class Meta:
        model = Kul
        fields = '__all__'
        read_only_fields = [f for f in Kul._meta.fields]
    
    def get_subgotra(self, obj):
        serializer = SubGotraDetailSerializer(
            obj.subgotra,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
        

class VanshSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vansh
        fields = '__all__'
        read_only_fields = ['id']

class VanshDetailSerializer(DynamicFieldsModelSerializer):
    kul = serializers.SerializerMethodField()
    class Meta:
        model = Vansh
        fields = '__all__'
        read_only_fields = [f for f in Vansh._meta.fields]
    
    def get_kul(self, obj):
        serializer = KulDetailSerializer(
            obj.kul,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
        

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = '__all__'
        read_only_fields = ['id']

class FamilyDetailSerializer(DynamicFieldsModelSerializer):
    vansh = serializers.SerializerMethodField()
    class Meta:
        model = Family
        fields = '__all__'
        read_only_fields = [f for f in Family._meta.fields]
    
    def get_vansh(self, obj):
        serializer = VanshDetailSerializer(
            obj.vansh,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class PidhiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pidhi
        fields = '__all__'
        read_only_fields = ['id']


class PidhiDetailSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Pidhi
        fields = '__all__'
        read_only_fields = [f for f in Pidhi._meta.fields]

# class PidhiIdNameSerializer(serializers.ModelSerializer):
#     # family = serializers.SerializerMethodField()
#     class Meta:
#         model = Pidhi
#         fields = '__all__'
#         read_only_fields = [f for f in Pidhi._meta.fields]
    
    # def get_family(self, obj):
    #     serializer = FamilyIdNameSerializer(
    #         obj.family,
    #         context={
    #             'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
    #             'use_raw_code': True
    #         }
    #     )
    #     return serializer.data


class CalibrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calibration
        fields = '__all__'
        read_only_fields = ['id']

# ===================================================
# Professional 
# ===================================================
class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'
        read_only_fields = ['id']

class SectionDetailSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'
        read_only_fields = [f for f in Section._meta.fields]


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id']

class ClassDetailSerializer(DynamicFieldsModelSerializer):
    section = serializers.SerializerMethodField()
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = [f for f in Class._meta.fields]
    
    def get_section(self, obj):
        serializer = SectionDetailSerializer(
            obj.section,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class ProfCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfCategory
        fields = '__all__'
        read_only_fields = ['id']

class ProfCategoryDetailSerializer(DynamicFieldsModelSerializer):
    profclass = serializers.SerializerMethodField()
    class Meta:
        model = ProfCategory
        fields = '__all__'
        read_only_fields = [f for f in ProfCategory._meta.fields]
    
    def get_profclass(self, obj):
        serializer = ClassDetailSerializer(
            obj.profclass,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
        


class ProfSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfSubCategory
        fields = '__all__'
        read_only_fields = ['id']

class ProfSubCategoryDetailSerializer(DynamicFieldsModelSerializer):
    category = serializers.SerializerMethodField()
    class Meta:
        model = ProfSubCategory
        fields = '__all__'
        read_only_fields = [f for f in ProfSubCategory._meta.fields]
    
    def get_category(self, obj):
        serializer = ProfCategoryDetailSerializer(
            obj.category,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
    
    
class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = ['id']

class SectorDetailSerializer(DynamicFieldsModelSerializer):
    subcategory = serializers.SerializerMethodField()
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = [f for f in Sector._meta.fields]
    
    def get_subcategory(self, obj):
        serializer = ProfSubCategoryDetailSerializer(
            obj.subcategory,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class SubSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = '__all__'
        read_only_fields = ['id']

class SubSectorDetailSerializer(DynamicFieldsModelSerializer):
    sector = serializers.SerializerMethodField()
    class Meta:
        model = SubSector
        fields = '__all__'
        read_only_fields = [f for f in SubSector._meta.fields]
    
    def get_sector(self, obj):
        serializer = SectorDetailSerializer(
            obj.sector,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['id']

class DepartmentDetailSerializer(DynamicFieldsModelSerializer):
    subsector = serializers.SerializerMethodField()
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = [f for f in Department._meta.fields]
    
    def get_subsector(self, obj):
        serializer = SubSectorDetailSerializer(
            obj.subsector,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class SubDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubDepartment
        fields = '__all__'
        read_only_fields = ['id']

class SubDepartmentDetailSerializer(DynamicFieldsModelSerializer):
    department = serializers.SerializerMethodField()
    class Meta:
        model = SubDepartment
        fields = '__all__'
        read_only_fields = [f for f in SubDepartment._meta.fields]
    
    def get_department(self, obj):
        serializer = DepartmentDetailSerializer(
            obj.department,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = '__all__'
        read_only_fields = ['id']

class TypeDetailSerializer(DynamicFieldsModelSerializer):
    subdepartment = serializers.SerializerMethodField()
    class Meta:
        model = Type
        fields = '__all__'
        read_only_fields = [f for f in Type._meta.fields]
    
    def get_subdepartment(self, obj):
        serializer = SubDepartmentDetailSerializer(
            obj.subdepartment,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ['id']

class BrandDetailSerializer(DynamicFieldsModelSerializer):
    type = serializers.SerializerMethodField()
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = [f for f in Brand._meta.fields]
    
    def get_type(self, obj):
        serializer = TypeDetailSerializer(
            obj.type,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'
        read_only_fields = ['id']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id']

class ProductDetailSerializer(DynamicFieldsModelSerializer):
    brand = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = [f for f in Product._meta.fields]
    
    def get_brand(self, obj):
        serializer = BrandDetailSerializer(
            obj.brand,
            context={
                'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
                'use_raw_code': True
            }
        )
        return serializer.data
        
# class PostModelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PostModel
#         fields = '__all__'
#         read_only_fields = ['id']

# class PostModelDetailSerializer(DynamicFieldsModelSerializer):
#     brand = serializers.SerializerMethodField()
#     class Meta:
#         model = PostModel
#         fields = '__all__'
#         read_only_fields = [f.name for f in PostModel._meta.fields]
    
#     def get_brand(self, obj):
#         serializer = BrandDetailSerializer(
#             obj.brand,
#             context={
            #     'exclude_fields': ['is_hidden', 'on_hold', 'hold_date'],
            #     'use_raw_code': True
            # }
#         )
#         return serializer.data


class RoomFlashSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFlash
        fields = "__all__"
        # fields = ['id', 'name', 'code', 'is_hidden', 'on_hold', 'hold_date']
        read_only_fields = ['id', 'is_used']

class RoomFlashIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFlash
        fields = ['id', 'name']


class RoomTypeSerializer(RemoveTimestampMixin, serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = "__all__"
        # fields = ['id', 'name', 'code', 'is_hidden', 'on_hold', 'hold_date']
        read_only_fields = ['id', 'is_used']


class ModelNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelName
        fields = ['id', 'model', 'technical_name']
        read_only_fields = ['id','model', 'technical_name']
        
# class RecordRuleAccessInputSerializer(serializers.Serializer):
#     domain_filter = serializers.JSONField()
#     can_read = serializers.BooleanField(default=False)
#     can_create = serializers.BooleanField(default=False)
#     can_write = serializers.BooleanField(default=False)
#     can_delete = serializers.BooleanField(default=False)
    
        
class ModelRuleAccessInputSerializer(serializers.Serializer):
    model_id = serializers.IntegerField()
    model_name = serializers.CharField(read_only=True)
    can_read = serializers.BooleanField(default=False)
    can_create = serializers.BooleanField(default=False)
    can_update = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)
    domain_filter = serializers.JSONField(required=False)

    

class ModelAndRecordRuleAccessInputSerializer(serializers.Serializer):
    user = serializers.IntegerField()  # <-- You need this
    model_access_rule = ModelRuleAccessInputSerializer(many=True)
    

    def create(self, validated_data):
        request_user = self.context["request"].user
        user_id = validated_data.get("user")
        
        # Ensure user exists
        target_user = check_obj_exists(CustomUser, user_id)
        if not isinstance(target_user, CustomUser):
            raise serializers.ValidationError("User does not exist")
        
        # (request_user) main admin designation level = 1, admin disignation level = 0, (1>0) True
        if request_user.is_system_user and target_user.is_system_user:
            if (
                getattr(request_user.designation, "reporting_designation", None)
                and request_user.designation.level > target_user.designation.level
            ):
                raise serializers.ValidationError("You do not have permission to assign access")

        
        model_access_rules = validated_data.get("model_access_rule")
        result = []

        with transaction.atomic():
            for model_rule in model_access_rules:
                model_id = model_rule.get("model_id")
                
                # Ensure model exists
                model_obj = check_obj_exists(ModelName, model_id)
                if not isinstance(model_obj, ModelName):
                    raise serializers.ValidationError("Model does not exist")
                
                # Super Admin of system user
                if request_user.is_system_user and getattr(request_user.designation, "level", None) == 0:
                    pass
                else:
                    validate_assignable_permissions(request_user, model_id, model_rule)
                
                model_access, _ = ModelAccess.objects.update_or_create(
                    user_id=user_id,     # lookup by user + model
                    model_id=model_id,
                    defaults={
                        "can_create": model_rule.get("can_create", False),
                        "can_read": model_rule.get("can_read", False),
                        "can_update": model_rule.get("can_update", False),
                        "can_delete": model_rule.get("can_delete", False),
                    },
                )
                
                domain_filter = model_rule.get("domain_filter", None)
                
                if domain_filter is not None:
                    django_model = apps.get_model(model_obj.app_label, model_obj.model)
                    validate_domain_filter(django_model, domain_filter)
                    
                    
                    record_access, _ = RecordRule.objects.update_or_create(
                        model_id=model_id,
                        domain_filter = domain_filter,
                        defaults={
                            "user": target_user,
                            "can_read": model_rule.get("can_read", False), # default use model rule for record acess rule
                            "can_create": model_rule.get("can_create", False),
                            "can_write": model_rule.get("can_write", False),
                            "can_delete": model_rule.get("can_delete", False),
                        },
                    )
                
                result.append({
                "model_id": model_access.model_id,
                "model_name": model_access.model.technical_name,
                "can_create": model_access.can_create,
                "can_read": model_access.can_read,
                "can_update": model_access.can_update,
                "can_delete": model_access.can_delete,
                "domain_filter": domain_filter
                })
            
        return {
        "user": user_id,
        "model_access_rule": result
    }
        


# ---------------- OUTPUT SERIALIZER (GET) ----------------
class ModelRuleAccessOutputSerializer(serializers.Serializer):
    model_id = serializers.IntegerField()
    model_name = serializers.CharField()
    can_read = serializers.BooleanField()
    can_create = serializers.BooleanField()
    can_update = serializers.BooleanField()
    can_delete = serializers.BooleanField()
    domain_filter = serializers.JSONField(required=False)


class ModelAndRecordRuleAccessOutputSerializer(serializers.Serializer):
    user = serializers.IntegerField(source="id")
    model_access_rule = serializers.SerializerMethodField()

    def get_model_access_rule(self, user_obj):
        model_accesses = ModelAccess.objects.filter(user=user_obj)
        result = []

        for model_access in model_accesses:
            try:
                record_rule = RecordRule.objects.get(
                    user=user_obj, model=model_access.model
                )
            except RecordRule.DoesNotExist:
                record_rule = None

            result.append({
                "model_id": model_access.model_id,
                "model_name": model_access.model.technical_name,
                "can_read": model_access.can_read,
                "can_create": model_access.can_create,
                "can_update": model_access.can_update,
                "can_delete": model_access.can_delete,
                "domain_filter": record_rule.domain_filter if record_rule else None,
            })
        return result


class ResidentialSearchInputSerializer(serializers.Serializer):
    glob = serializers.CharField(required=False, allow_blank=True)
    continent = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    taluka = serializers.CharField(required=False, allow_blank=True)
    city_village = serializers.CharField(required=False, allow_blank=True)
    ward = serializers.CharField(required=False, allow_blank=True)
    society = serializers.CharField(required=False, allow_blank=True)
    block = serializers.CharField(required=False, allow_blank=True)
    floor = serializers.CharField(required=False, allow_blank=True)
    house = serializers.CharField(required=False, allow_blank=True)
    search_key = serializers.CharField()

    
# Residential Unified Output Serializer (always same structure)
class ResidentialOutputSerializer(serializers.Serializer):
    glob = GlobIdNameSerializer(allow_null=True)
    continent = ContinentIdNameSerializer(allow_null=True)
    country = CountryIdNameSerializer(allow_null=True)
    state = StateIdNameSerializer(allow_null=True)
    district = DistrictIdNameSerializer(allow_null=True)
    taluka = TalukaIdNameSerializer(allow_null=True)
    city_village = CityVillageIdNameSerializer(allow_null=True)
    ward = WardIdNameSerializer(allow_null=True)
    society = SocietyIdNameSerializer(allow_null=True)
    block = BlockIdNameSerializer(allow_null=True)
    floor = FloorIdNameSerializer(allow_null=True)
    house = HouseIdNameSerializer(allow_null=True)
    room = RoomIdNameSerializer(allow_null=True)

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    

class ReligionIdNameSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField()
    class Meta:
        model = Religion
        fields = ["id", "name"]
    
    # def get_code(self, obj):
    #     value = obj.code if hasattr(obj, "code") else obj.get("code")
    #     return get_two_digit(value)

class SampradayIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sampraday
        fields = ["id", "name"]

class PanthIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Panth
        fields = ["id", "name"]

class AwasthaIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Awastha
        fields = ["id", "name"]

class VarnaIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Varna
        fields = ["id", "name"]

class CasteIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = ["id", "name"]

class SubCasteIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCaste
        fields = ["id", "name"]

class GotraIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gotra
        fields = ["id", "name"]

class SubGotraIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGotra
        fields = ["id", "name"]

class KulIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kul
        fields = ["id", "name"]

class VanshIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vansh
        fields = ["id", "name"]

class FamilyIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ["id", "name"]

class PidhiIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pidhi
        fields = ["id", "name"]

class PersonalInputSerializer(serializers.Serializer):
    religion = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    sampraday = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    panth = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    awastha = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    varna = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    caste = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subcaste = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    gotra = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subgotra = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    kul = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    vansh = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    family = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    pidhi = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    search_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class PersonalOutputSerializer(serializers.Serializer):
    religion = ReligionIdNameSerializer(allow_null=True)
    sampraday = SampradayIdNameSerializer(allow_null=True)
    panth = PanthIdNameSerializer(allow_null=True)
    awastha = AwasthaIdNameSerializer(allow_null=True, many=True)
    varna = VarnaIdNameSerializer(allow_null=True)
    caste = CasteIdNameSerializer(allow_null=True)
    subcaste = SubCasteIdNameSerializer(allow_null=True)
    gotra = GotraIdNameSerializer(allow_null=True)
    subgotra = SubGotraIdNameSerializer(allow_null=True)
    kul = KulIdNameSerializer(allow_null=True)
    vansh = VanshIdNameSerializer(allow_null=True)
    family = FamilyIdNameSerializer(allow_null=True)
    pidhi = PidhiIdNameSerializer(allow_null=True, many=True)


class SectionIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name"]

class ClassIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name"]

class ProfCategoryIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfCategory
        fields = ["id", "name"]

class ProfSubCategoryIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfSubCategory
        fields = ["id", "name"]

class SectorIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["id", "name"]

class SubSectorIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = ["id", "name"]

class DepartmentIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]

class SubDepartmentIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubDepartment
        fields = ["id", "name"]

class TypeIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ["id", "name"]

class BrandIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]

        
        
# class PostModelIdNameSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PostModel
#         fields = ["id", "name"]

class ProductSearchInputSerializer(serializers.Serializer):
    sector = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    brand = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    product = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    search_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class ProductSearchOutputSerializer(serializers.Serializer):
    sector = SectorIdNameSerializer()
    brand = BrandIdNameSerializer()
    product = ProductIdNameSerializer()

class ProfessionalInputSerializer(serializers.Serializer):
    section = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    profclass = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    category = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subcategory = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    sector = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subsector = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    department = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subdepartment = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    type = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    brand = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    search_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class ProfessionalOutputSerializer(serializers.Serializer):
    section = SectionIdNameSerializer(allow_null=True)
    profclass = ClassIdNameSerializer(allow_null=True)
    category = ProfCategoryIdNameSerializer(allow_null=True)
    subcategory = ProfSubCategoryIdNameSerializer(allow_null=True)
    sector = SectorIdNameSerializer(allow_null=True)
    subsector = SubSectorIdNameSerializer(allow_null=True)
    department = DepartmentIdNameSerializer(allow_null=True)
    subdepartment = SubDepartmentIdNameSerializer(allow_null=True)
    type = TypeIdNameSerializer(allow_null=True)
    brand = BrandIdNameSerializer(allow_null=True)


class DesignationIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = ["id", "name"]


class DesignationSerializer(serializers.ModelSerializer):
    # access id in input...
    reporting_designation = serializers.PrimaryKeyRelatedField(
        queryset=Designation.objects.all(),
        required=False,
        allow_null=True
    )
    class Meta:
        model = Designation
        fields = "__all__"
        read_only_fields = ["id"]
        validators = [
            UniqueTogetherValidator(
                queryset=Designation.objects.all(),
                fields=['category', 'name'],
                message="A continent with this name already exists in the selected category.",
            )
        ]
        # extra_kwargs = {
        #     'code': {'required': False}
        # }
    
    def to_representation(self, instance):
        """
        Override output representation — show nested reporting_designation.
        """
        data = super().to_representation(instance)
        if instance.reporting_designation:
            data["reporting_designation"] = {
                "id": instance.reporting_designation.id,
                "name": instance.reporting_designation.name,
            }
        else:
            data["reporting_designation"] = None
        return data
    
    def validate_name(self, value):
        """
        Validate that name does not contain special characters.
        Allow only letters, numbers, and spaces.
        """
        if not re.match(r'^[A-Za-z ]+$', value):
            raise serializers.ValidationError(
                "Name can only contain letters and spaces."
            )
        return value
    
    def validate(self, attrs):        
        code = attrs.get('code')
        reporting_designation = attrs.get('reporting_designation')

        if code is not None:
            # Case 1: User *provided* a code.
            # We just need to validate it.
            if code == 0 and (attrs.get('name') != 'self' or attrs.get('name') != 'Self'):
                    raise serializers.ValidationError({"code": "Invalid post no. Cannot be 0."})
            # The provided code is fine, so we'll use it.
            attrs['code'] = code
        
        else:
            # Case 2: User did *not* provide a code.
            # We will set it based on your logic.
            if reporting_designation:
                # Set code = parent's code + 1
                attrs['code'] = reporting_designation.code + 1
            else:
                # Set code = 1 (for top-level designations)
                attrs['code'] = 1

        return attrs


class DesignationGetSerializer(RemoveTimestampMixin, serializers.ModelSerializer):
    reporting_designation = DesignationIdNameSerializer()
    class Meta:
        model = Designation
        fields = "__all__"


class NodeMergeSerializer(serializers.Serializer):
    target_node_id = serializers.IntegerField(
        help_text="The ID of the node to keep (the winner)."
    )
    source_node_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of IDs to merge INTO the target (these will be deleted)."
    )

    def validate(self, data):
        target_id = data['target_node_id']
        source_ids = data['source_node_ids']

        # 1. Check if Target exists
        try:
            target = Node.objects.get(id=target_id)
        except Node.DoesNotExist:
            raise serializers.ValidationError({"target_node_id": "Target node not found."})

        # 2. Validate Sources
        sources = Node.objects.filter(id__in=source_ids)
        if len(sources) != len(set(source_ids)):
            raise serializers.ValidationError({"source_node_ids": "One or more source nodes not found."})

        for source in sources:
            # Prevent merging into self
            if source.id == target.id:
                raise serializers.ValidationError("Cannot merge a node into itself.")
            
            # Prevent merging different Levels (e.g., Cannot merge State into Country)
            if source.level_id != target.level_id:
                raise serializers.ValidationError(
                    f"Level mismatch: Cannot merge '{source.level.name}' into '{target.level.name}'."
                )
                
            # Prevent merging different Dimensions
            if source.dimension_id != target.dimension_id:
                raise serializers.ValidationError("Dimension mismatch: Cannot merge nodes from different dimensions.")

        data['target_node'] = target
        data['source_nodes'] = sources
        return data


class NodeMergeCreateSerializer(serializers.Serializer):
    source_node_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    dimension = serializers.PrimaryKeyRelatedField(
        queryset=Dimension.objects.filter(is_active=True)
    )
    level = serializers.PrimaryKeyRelatedField(
        queryset=Level.objects.all()
    )
    
    name = serializers.CharField(max_length=255)
    code = serializers.IntegerField()
    
    parent = serializers.PrimaryKeyRelatedField(queryset=Node.objects.all(), required=False, allow_null=True)
    
    # 1. Add Attributes Field
    attributes = serializers.JSONField(
        required=False, 
        default=dict,
        help_text="Custom column values for the new node."
    )
    
    def validate(self, attrs):
        # Get the actual objects (DRF fetched them for us)
        target_dimension = attrs.get('dimension')
        target_level = attrs.get('level')
        code = attrs.get('code')
        parent = attrs.get('parent')
        source_ids = attrs.get('source_node_ids')
        attributes = attrs.get('attributes')

        if code is not None:
            # Start with all nodes
            qs = Node.objects.all()
            
            # CASE A: Child Node (Parent is NOT NULL)
            if parent is not None:
                if qs.filter(parent=parent, level=target_level, code=code).exists():
                    raise serializers.ValidationError({
                        "code": f"Code '{code}' is already used by another node under parent '{parent.name}'."
                    })
            
            # CASE B: Top/Global Node (Parent IS NULL)
            else:
                if qs.filter(parent__isnull=True, dimension=target_dimension, level=target_level, code=code).exists():
                    raise serializers.ValidationError({
                        "code": f"Code '{code}' is already used at the Top Level for this Dimension/Level."
                    })
        
        if parent and parent.id in source_ids:
            raise serializers.ValidationError({"parent": "The new parent cannot be one of the nodes being merged."})
    
        # --- A. Validate Parent ---
        if parent:
            if parent.dimension != target_dimension:
                raise serializers.ValidationError({"parent": "Parent must belong to the selected dimension."})
        
        if target_level.parent is not None and parent is None:
            raise serializers.ValidationError({"parent": "Parent is required."})
            

        # --- B. Validate Source Nodes (The Logic You Requested) ---
        # Fetch all unique source nodes
        source_nodes = Node.objects.filter(id__in=source_ids)
        
        # 1. Check if all IDs exist
        if source_nodes.count() != len(set(source_ids)):
            raise serializers.ValidationError({"source_node_ids": "One or more source IDs are invalid or duplicates."})

        # 2. Check Consistency
        for source in source_nodes:
            # Check Dimension
            if source.dimension != target_dimension:
                raise serializers.ValidationError({
                    "source_node_ids": f"Node '{source.name}' (ID: {source.id}) does not belong to the selected dimension."
                })
            
            # Check Level
            if source.level != target_level:
                raise serializers.ValidationError({
                    "source_node_ids": f"Node '{source.name}' (ID: {source.id}) does not belong to the selected level."
                })

        # Store the node objects in attrs so the View doesn't have to query them again
        attrs['source_nodes_objects'] = source_nodes
        
        
        if target_level:
            # 1. Get Schema
            schema = target_level.extra_fields_schema or []
            
            # 2. Check for Junk Keys (Only if attributes were actually sent)
            if attributes:
                allowed_keys = {col.get('name') for col in schema}
                incoming_keys = set(attributes.keys())
                unknown_keys = incoming_keys - allowed_keys
                
                if unknown_keys:
                    raise serializers.ValidationError({
                        "attributes": f"Invalid custom columns detected: {list(unknown_keys)}. Allowed columns: {list(allowed_keys)}"
                    })
            
            # 3. Check for REQUIRED fields and TYPES
            # We create a temporary Node instance to run the model's strict validation
            temp_node = Node(level=target_level, attributes=attributes)
            
            try:
                # This checks for missing required fields AND invalid types
                temp_node.validate_attributes()
            except ValidationError as e:
                # Convert Django Error to DRF Error
                if hasattr(e, 'messages'):
                     raise serializers.ValidationError({"attributes": e.messages})
                raise serializers.ValidationError({"attributes": str(e)})
        
        # Update attrs with the safe dictionary in case it was None
        attrs['attributes'] = attributes
        return attrs


class HistoricalLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level.history.model
        fields = '__all__'


class HistoricalNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node.history.model
        fields = '__all__'