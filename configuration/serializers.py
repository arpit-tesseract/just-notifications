from rest_framework import serializers
from .models import *
from user.models import User
from shashan.utils.validators import get_object_by_name_or_error
from .utils import *
from django.apps import apps
from django.db import transaction, IntegrityError
from rest_framework.validators import UniqueTogetherValidator
from django.db.models import F, Max
from django.core.exceptions import ValidationError as DjangoValidationError
from simple_history.utils import update_change_reason

import json
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
            'display_name',
            'dimension',
            'parent',
            'child',
            'sort_order',
            'single_mode',
            'is_mandatory',
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
        
        new_code_digits = validated_data.get('code_digits')
        if new_code_digits is not None and new_code_digits < instance.code_digits:
            # Check if any node has a code length > new_code_digits
            if Node.objects.filter(level=instance, code__gte=10**new_code_digits).exists():
                raise serializers.ValidationError({
                    "code_digits": f"Cannot decrease code digits to {new_code_digits}. Some nodes have codes requiring more digits."
                })

        try:
            # Do not update name, only display_name and code_digits
            level_logger.info(f"Try to updating level {instance.name}'s display_name or code_digits")
            instance.code_digits = validated_data.get('code_digits', instance.code_digits)
            instance.display_name = validated_data.get('display_name', instance.display_name)
            instance.save(update_fields=['display_name', 'code_digits'])
        except Exception as e:
            level_logger.exception("Failed to update level:", e)
            raise serializers.ValidationError({"error": "Failed to update level."})
        return instance
    
    

class LevelIdNameSerializerWithCustomColumn(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    parent_display_name = serializers.SerializerMethodField()
    class Meta:
        model = Level
        fields = ['id', 'name', 'display_name', 'is_mandatory', 'single_mode',  'parent_name', 'parent_display_name', 'code_digits', 'extra_fields_schema']
    
    def get_parent_name(self, obj):
        if obj.parent:
            return obj.parent.name
    
    def get_parent_display_name(self, obj):
        if obj.parent:
            return obj.parent.display_name
        
class LevelIdNameSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()
    class Meta:
        model = Level
        fields = ['id', 'name', 'display_name', 'parent_name', 'single_mode']
    
    def get_parent_name(self, obj):
        if obj.parent:
            return obj.parent.name

class LevelDetailSerializer(serializers.ModelSerializer):
    parent = LevelIdNameSerializer()
    dimension = DimensionIdNameSerializer()
    class Meta:
        model = Level
        fields = ['id', 'name', 'display_name', 'parent', 'dimension', 'sort_order', 'is_mandatory']

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
        ('dropdown', 'Dropdown'),
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
    
    options = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Required for 'dropdown' type. List of valid options."
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

        if field_type == 'dropdown':
            options = data.get('options', [])
            if not options:
                raise serializers.ValidationError({"options": "Dropdown options cannot be empty."})

        if default_val is not None and default_val != "":
            try:
                data['default_value'] = validate_value_type(default_val, field_type, max_len, options=data.get('options'))
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
    
    options = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Updated options for 'dropdown' type."
    )
    
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
    relationships = serializers.SerializerMethodField()
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
            'relationships'
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
    
    def get_relationships(self, instance):
        node_relationships = NodeRelationship.objects.filter(territory=instance)
        output = []
        for relationship in node_relationships:
            data = NodeRelationshipOutputSerializer(relationship).data
            output.append(data)
        return output



class NodeSerializer(serializers.ModelSerializer):
    alias = NodeAliasSerializer(many=True, required=False, allow_null=True)
    parent_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="Provide multiple parent IDs to create parallel nodes across branches."
    )

    # NEW: Accept relationships in the same payload
    relationships = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
        help_text="List of relationship objects to create/update/delete along with the node."
    )
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
        parent_ids = attrs.get('parent_ids', [])
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
        # 2. Build the list of parents to validate
        # ---------------------------------------------------------
        parents_to_check = []
        if not instance and parent_ids:
            parents_to_check = list(Node.objects.filter(id__in=parent_ids))
            if len(parents_to_check) != len(set(parent_ids)):
                raise serializers.ValidationError({"parent_ids": "One or more parent IDs are invalid."})
        elif parent:
            parents_to_check = [parent]
        else:
            parents_to_check = [None] # Top-level/Global Node

        # ---------------------------------------------------------
        # 3. Validation Logic (Uniqueness & Consistency)
        # ---------------------------------------------------------
        for p in parents_to_check:
            # A. Parent Consistency
            if p:
                if p.dimension != dimension:
                    raise serializers.ValidationError({"parent": f"Parent '{p.name}' must be in the same dimension."})
                if instance and p.id == instance.id:
                    raise serializers.ValidationError({"parent": "Parent cannot be self."})

            # B. Conditional Unique Code Check (Looping through all parents)
            if code is not None:
                qs = Node.objects.all()
                if instance:
                    qs = qs.exclude(pk=instance.pk)

                if p is not None:
                    if qs.filter(parent=p, level=level, code=code).exists():
                        raise serializers.ValidationError({
                            "code": f"Code '{code}' is already used under '{p.name}'."
                        })
                else:
                    if qs.filter(parent__isnull=True, dimension=dimension, level=level, code=code).exists():
                        raise serializers.ValidationError({
                            "code": f"Code '{code}' is already used at the Top Level."
                        })

        # C. Check if Parent is strictly required
        if not parents_to_check[0] and level and level.parent:
            raise serializers.ValidationError({"parent": "This field is required."})
        
        # ---------------------------------------------------------
        # 4. Schema Validation (Attributes)
        # ---------------------------------------------------------
        if level:
            schema = level.extra_fields_schema or []
            if attributes:
                allowed_keys = {col.get('name') for col in schema}
                incoming_keys = set(attributes.keys())
                unknown_keys = incoming_keys - allowed_keys
                
                if unknown_keys:
                    raise serializers.ValidationError({
                        "attributes": f"Invalid custom columns detected: {list(unknown_keys)}. Allowed columns: {list(allowed_keys)}"
                    })
            
            temp_node = Node(level=level, attributes=attributes)
            try:
                temp_node.validate_attributes()
            except DjangoValidationError as e:
                if hasattr(e, 'messages'):
                     raise serializers.ValidationError({"attributes": e.messages})
                raise serializers.ValidationError({"attributes": str(e)})
        
        attrs['attributes'] = attributes
        attrs['validated_parents'] = parents_to_check # Pass these to create()
        return attrs

    def create(self, validated_data):
        alias_data = validated_data.pop('alias', [])
        validated_data.pop('parent_ids', None) # Remove it so super() doesn't break
        parents_to_create = validated_data.pop('validated_parents', [None])

        # NEW: Extract relationships data
        relationships_data = validated_data.pop('relationships', [])

        created_nodes = []

        try:
            with transaction.atomic():
                for p in parents_to_create:
                    node_data = validated_data.copy()
                    node_data['parent'] = p
                    
                    # Create the individual node
                    node = super().create(node_data)
                    
                    # Apply Aliases
                    if alias_data:
                        alias_names = []
                        for alias in alias_data:
                            NodeAlias.objects.create(node=node, **alias)
                            alias_names.append(alias.get('name'))
                        
                        alias_diff = {"before": [], "after": alias_names}
                        update_change_reason(node, f"aliases:{json.dumps(alias_diff)}")

                    # NEW: Process Relationships
                    if relationships_data:
                        self._process_relationships(node, relationships_data)
                        
                    created_nodes.append(node)
        except serializers.ValidationError as e:
            raise e # Re-raise validation errors so they format properly
        except Exception as e:
            raise serializers.ValidationError({"error": "Error creating node(s)."})
            
        # DRF expects a single instance back. We return the first one, 
        # but attach the full list so our ViewSet can grab it.
        first_node = created_nodes[0]
        first_node._created_nodes_list = created_nodes
        return first_node

    def update(self, instance, validated_data):
        has_alias_field = 'alias' in validated_data
        alias_data = validated_data.pop('alias',[])

        # NEW: Extract relationships data
        relationships_data = validated_data.pop('relationships', None)

        if alias_data is None:
            alias_data = []
            
        # instance = super().update(instance, validated_data)
        print('Alias data:', alias_data)

        reason_parts = []

        if has_alias_field:
            old_aliases_set = set(NodeAlias.objects.filter(node=instance).values_list('name', flat=True))
            incoming_names_set = set(alias.get('name') for alias in alias_data if alias.get('name'))

            added_aliases = incoming_names_set - old_aliases_set
            removed_aliases = old_aliases_set - incoming_names_set

            if added_aliases or removed_aliases:
                if removed_aliases:
                    NodeAlias.objects.filter(node=instance, name__in=removed_aliases).delete()
                for name in added_aliases:
                    NodeAlias.objects.create(node=instance, name=name)
                
                # 2. Inject the Universal JSON string
                # We simply convert the sets back to lists for JSON serialization
                alias_diff = {
                    "before": list(old_aliases_set),
                    "after": list(incoming_names_set)
                }
                reason_parts.append(f"aliases:{json.dumps(alias_diff)}")

        # NEW: Process Relationships during update
        if relationships_data is not None:
            self._process_relationships(instance, relationships_data)
        
        # 2. Inject the change reason into the instance 
        if reason_parts:
            instance._change_reason = " | ".join(reason_parts)
            
            # CRITICAL: If ONLY aliases changed (and no other fields like 'name' or 'code'), 
            # super().update() will NOT trigger a save. We must force a save to generate history!
            if not validated_data: 
                instance.updated_at = timezone.now()
                instance.save(update_fields=['updated_at'])
                return instance

        # 3. Update standard fields 
        # (If standard fields changed, simple-history will automatically grab the _change_reason we set above)
        instance = super().update(instance, validated_data)
            
        return instance
    

    # NEW: Helper method to handle the heavy lifting
    def _process_relationships(self, node, relationships_data):
        """
        Mimics the bulk_manage logic, but auto-injects the current Node's ID.
        """
        # Grab the request user for soft-delete history logging
        request = self.context.get('request')
        user = request.user if request else None

        for index, item_data in enumerate(relationships_data):
            
            # --- AUTO-INJECT NODE ID ---
            # If the frontend passes 'controller' but no 'territory', assume the new Node IS the territory!
            # if 'territory' not in item_data and 'controller' in item_data:
            #     item_data['territory'] = node.id
            # elif 'controller' not in item_data and 'territory' in item_data:
            #     item_data['controller'] = node.id
            # elif 'territory' not in item_data and 'controller' not in item_data:
            #      raise serializers.ValidationError({"relationships": f"Row {index}: Must specify at least one side of the relationship ('territory' or 'controller')."})

            item_data['territory'] = node.id

            item_id = item_data.get('id')
            is_deleted_flag = item_data.get('delete', False)

            # --- SCENARIO 1: DELETE ---
            if item_id and is_deleted_flag:
                try:
                    rel = NodeRelationship.objects.get(id=item_id)
                    rel.soft_delete(user=user)
                    update_change_reason(rel, f"Deleted via Node '{node.name}' update")
                except NodeRelationship.DoesNotExist:
                    raise serializers.ValidationError({"relationships": f"Row {index}: ID {item_id} not found for deletion."})
                continue

            # --- SCENARIO 2: UPDATE ---
            if item_id and not is_deleted_flag:
                try:
                    rel = NodeRelationship.objects.get(id=item_id)
                    rel_serializer = NodeRelationshipInputSerializer(rel, data=item_data, partial=True)
                    if rel_serializer.is_valid():
                        try:
                            with transaction.atomic():
                                updated_rel = rel_serializer.save()
                                update_change_reason(updated_rel, f"Updated via Node '{node.name}' update")
                        except IntegrityError:
                            raise serializers.ValidationError({"relationships": f"Row {index}: This relationship already exists."})
                    else:
                        raise serializers.ValidationError({"relationships": rel_serializer.errors})
                except NodeRelationship.DoesNotExist:
                    raise serializers.ValidationError({"relationships": f"Row {index}: ID {item_id} not found for update."})
                continue

            # --- SCENARIO 3: CREATE ---
            if not item_id:
                rel_serializer = NodeRelationshipInputSerializer(data=item_data)
                if rel_serializer.is_valid():
                    try:
                        with transaction.atomic():
                            new_rel = rel_serializer.save()
                            update_change_reason(new_rel, f"Created via Node '{node.name}'")
                    except IntegrityError:
                        raise serializers.ValidationError({"relationships": f"Row {index}: This relationship already exists."})
                else:
                    raise serializers.ValidationError({"relationships": rel_serializer.errors})


class SplitNodeSerializer(serializers.Serializer):
    node = serializers.DictField()
    children_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[],
    )


class SplitNodeInputSerializer(serializers.Serializer):
    split_date = serializers.DateField()
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
    

class NodeRelationshipInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeRelationship
        fields = [
            'territory',
            'controller',
            'relationship_type',
            'start_date',
            'end_date',
            'notes'
        ]
    
    def validate(self, attrs):
        # 1. Get the incoming data (or fallback to the existing instance if updating)
        rel_type = attrs.get('relationship_type', getattr(self.instance, 'relationship_type', None))
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))

        errors = {}

        # 2. General Date Logic: Start Date cannot be after End Date
        if start_date and end_date and start_date > end_date:
            errors['start_date'] = "Start date cannot be after the end date."

        # 3. specific rules based on relationship_type
        if rel_type == 'leased_to':
            if not start_date:
                errors['start_date'] = "Start date is required for leased territories."
            if not end_date:
                errors['end_date'] = "End date is required for leased territories."

        elif rel_type == 'historical':
            if not end_date:
                errors['end_date'] = "End date is required for historical relationships."

        elif rel_type in ['administered_by', 'claimed_by']:
            if end_date:
                # Force end_date to None, or throw an error. Throwing an error is safer so the user knows.
                errors['end_date'] = f"An active '{rel_type}' relationship cannot have an end date."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class NodeRelationshipOutputSerializer(serializers.ModelSerializer):
    territory = serializers.SerializerMethodField()
    controller = serializers.SerializerMethodField()

    class Meta:
        model = NodeRelationship
        fields = [
            'id',
            'territory',
            'controller',
            'relationship_type',
            'start_date',
            'end_date',
            'notes'
        ]

    def get_territory(self, obj):
        return {
            "id": obj.territory.id,
            "name": obj.territory.name
        }

    def get_controller(self, obj):
        return {
            "id": obj.controller.id,
            "name": obj.controller.name
        }



class NodeMergeSerializer(serializers.Serializer):
    target_node_id = serializers.IntegerField(
        help_text="The ID of the node to keep (the winner)."
    )
    source_node_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of IDs to merge INTO the target (these will be deleted)."
    )
    merge_date = serializers.DateField()

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

    merge_date = serializers.DateField()
    
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
                        "code": f"Code '{code}' is already used under '{parent.name}'."
                    })
            
            # CASE B: Top/Global Node (Parent IS NULL)
            else:
                if qs.filter(parent__isnull=True, dimension=target_dimension, level=target_level, code=code).exists():
                    raise serializers.ValidationError({
                        "code": f"Code '{code}' is already used."
                    })
        
        if parent and parent.id in source_ids:
            raise serializers.ValidationError({"parent": "The new parent cannot be one of the nodes being merged."})
    
        # Fetch all unique source nodes FIRST so we can infer the parent if needed
        source_nodes = Node.objects.filter(id__in=source_ids)
        
        # 1. Check if all IDs exist
        if source_nodes.count() != len(set(source_ids)):
            raise serializers.ValidationError({"source_node_ids": "One or more source IDs are invalid or duplicates."})

        # --- A. Validate & Infer Parent ---
        if target_level.parent is not None and parent is None:
            first_source = source_nodes.first()
            if first_source and first_source.parent:
                parent = first_source.parent
                attrs['parent'] = parent
            else:
                raise serializers.ValidationError({"parent": "Parent is required and could not be inferred from source nodes."})

        if parent:
            if parent.dimension != target_dimension:
                raise serializers.ValidationError({"parent": "Parent must belong to the selected dimension."})
        
        # --- B. Validate Source Nodes (The Logic You Requested) ---

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



class HistoricalNodeRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeRelationship.history.model
        fields = '__all__'




# =========================================
# Model Access & Record Rule Serializers
# =========================================

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
        target_user = check_obj_exists(User, user_id)
        if not isinstance(target_user, User):
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


      