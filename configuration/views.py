from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from rest_framework.decorators import action
from django.db.models import Count, Window, F
from .pagination import ConfigurationPagination
from .utils import cast_value_by_type

import logging
level_logger = logging.getLogger("Levels")

class DimensionListView(APIView):
    def get(self, request):
        dimensions = Dimension.objects.filter(is_active=True)
        serializer = DimensionIdNameSerializer(dimensions, many=True)
        return Response(serializer.data)

class LevelViewSet(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LevelSerializer
        return LevelDetailSerializer

    def perform_destroy(self, instance):
        try:
            with transaction.atomic():
                level_logger.info(f"Try to delete(archived) level {instance.name}")
                qs = Level.objects.select_for_update().filter(
                    dimension=instance.dimension,
                    is_archived=False
                )
                
                # update children
                child = qs.filter(parent=instance).first()
                if child:
                    child.parent = instance.parent
                    child.save(update_fields=['parent'])
                
                # CLOSE THE GAP (Shift everyone up)
                qs.filter(sort_order__gt=instance.sort_order).update(sort_order=F('sort_order') - 1)

                # ACTUAL DELETE
                instance.is_archived = True
                instance.save(update_fields=['is_archived'])
                
        except Exception as e:
            level_logger.exception("Failed to delete level:", e)
            raise ValidationError({"error": "Failed to delete level. Please try again."})
                
        # return super().perform_destroy(instance)

class LevelListView(APIView):
    def get(self, request):
        dimension_id = request.query_params.get('dimension_id', "").strip()
        if not dimension_id:
            return Response({"error": "Query paramter 'dimension_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if not dimension_id.isdigit():
            return Response({"error": "Query paramter 'dimension_id' must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        
        levels = Level.objects.filter(
            dimension_id=dimension_id,
            is_archived=False
        )
        serializer = LevelIdNameSerializerWithCustomColumn(levels, many=True)
        return Response(serializer.data)

from collections import defaultdict
from django.db.models import F

class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.select_related("dimension", "level", "parent")
    serializer_class = NodeSerializer
    pagination_class = ConfigurationPagination
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return NodeSerializer
        return NodeIdNameSerializer
    
    
    def list(self, request, *args, **kwargs):
        dimension = request.query_params.get("dimension", "").strip()
        level = request.query_params.get("level", "").strip()
        search_query = request.query_params.get("search", "").strip()

        if not dimension or not dimension.isdigit():
             return Response({"error": "Valid 'dimension' ID is required."}, status=status.HTTP_400_BAD_REQUEST)
         
        if not level or not level.isdigit():
             return Response({"error": "Valid 'level' ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Filter Target Nodes (Base Queryset)
        queryset = Node.objects.filter(
            dimension_id=int(dimension),
            level_id=int(level),
            level__is_archived=False
        ).annotate(
            # This calculates the count of nodes having the same parent_id 
            # and same level_id across the entire table
            parent_total_count=Window(
                expression=Count('id'),
                partition_by=[F('parent_id'), F('level_id')]
            )
        ).order_by('id') # Ordering is mandatory for pagination!
        
        # 4. Apply Name Search
        # if search_query:
        #     queryset = queryset.filter(
        #         Q(name__icontains=search_query) |      # Match Name
        #         Q(code__icontains=search_query) |      # Match Code (Optional)
        #         Q(attributes__icontains=search_query)  # Match ANY text inside attributes JSON
        #     )

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |      # Match Name
                Q(code__icontains=search_query)       # Match Code (Optional)
            )        
        # ==============================================
        # Filteration logic
        # ==============================================
        is_hidden_param = request.query_params.get("is_hidden", "").strip()
        if is_hidden_param != "":
            is_hidden_bool = is_hidden_param.lower() == "true"
            queryset = queryset.filter(is_hidden=is_hidden_bool)
        
        on_hold_param = request.query_params.get("on_hold", "").strip()
        if on_hold_param != "":
            on_hold_bool = on_hold_param.lower() == "true"
            queryset = queryset.filter(on_hold=on_hold_bool)
            
        ancestor_ids_param = request.query_params.get("ancestor_ids", "").strip()
        if ancestor_ids_param != "":
            try:
                # Convert "1,5" -> [1, 5]
                ancestor_ids_param = [int(x) for x in ancestor_ids_param.split(',') if x.strip().isdigit()]
                
                if ancestor_ids_param:
                    # Logic: We need nodes that descend from ALL selected ancestors.
                    # Since it's a hierarchy, usually filtering by the 'deepest' ancestor (last one) 
                    # is sufficient, but looping through all ensures 100% data integrity.
                    for ancestor_id in ancestor_ids_param:
                        # Use NodeClosure for efficient lookup (no recursive DB queries)
                        queryset = queryset.filter(
                            id__in=NodeClosure.objects.filter(
                                ancestor_id=ancestor_id
                            ).values('descendant_id')
                        )
            except ValueError:
                pass # Ignore invalid format
            
        level_obj = Level.objects.filter(id=level).first()
        allowed_custom_keys = []
        if level_obj and level_obj.extra_fields_schema:
            allowed_custom_keys = [col['name'] for col in level_obj.extra_fields_schema]
        
        # 2. Iterate over all query params
        skip_keys = {"page", "dimension", "level", "search", "is_hidden", "on_hold", "ancestor_ids"}
        for param, value in request.query_params.items():
            if param in skip_keys: 
                continue
            
            if param == "alias":
                alias_value = value.strip()
                if alias_value:
                    queryset = queryset.filter(aliases__name__icontains=alias_value)
            
            print("param:", param, "value:", value)
            value = value.strip()
            if not value: continue
            
            # If the param matches a custom column name (e.g., 'color')
            if param in allowed_custom_keys:
                # Construct the JSON lookup: attributes -> color
                # Use 'icontains' for text, 'exact' for booleans/numbers if preferred
                filter_key = f"attributes__{param}__exact" 
                
                # Apply filter
                queryset = queryset.filter(**{filter_key: value})
        
        print("queryset:", queryset)

        # 2. Apply Pagination (Get only 10 records)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            # Serialize ONLY the paginated nodes
            node_data_list = NodeOutputSerializer(page, many=True).data
            
            # Extract IDs for just this page
            node_map = {n['id']: n for n in node_data_list}
            target_ids = node_map.keys()

            # 3. Fetch Paths (Closures) ONLY for these 10 items
            if target_ids:
                closures = NodeClosure.objects.filter(
                    descendant_id__in=target_ids
                ).select_related(
                    'ancestor', 
                    'ancestor__level'
                ).order_by(
                    'descendant_id', 
                    '-depth' 
                )

                # 4. Build Path Dictionary
                grouped_paths = defaultdict(dict)
                for c in closures:
                    level_name = c.ancestor.level.name
                    grouped_paths[c.descendant_id][level_name] = {
                        "name": c.ancestor.name,
                        "code": c.ancestor.code
                    }

            # 5. Combine & Return Paginated Response
            result = []
            for nid, node_data in node_map.items():
                result.append({
                    "node": node_data,
                    "path": grouped_paths.get(nid, {})
                })
            
            return self.get_paginated_response(result)

        # Fallback if pagination is disabled
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='bulk-edit-details')
    def get_bulk_edit_details(self, request):
        ids_param = request.query_params.get('ids', "")
        
        if not ids_param:
             return Response({"error": "ids parameter is required (e.g. ?ids=1,2)"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Convert "1,2,3" string to list of integers [1, 2, 3]
        try:
            ids = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
        except ValueError:
            return Response({"error": "Invalid ids format"}, status=status.HTTP_400_BAD_REQUEST)

        if not ids:
            return Response({"error": "No valid numeric ids provided"}, status=status.HTTP_400_BAD_REQUEST)
         
        nodes = Node.objects.filter(id__in=ids)
        total_selected = nodes.count()
        
        if total_selected == 0:
            return Response({"error": "No valid nodes found"}, status=status.HTTP_404_NOT_FOUND)
        
        common_ancestors_qs = NodeClosure.objects.filter(
            descendant_id__in=ids
        ).values(
            'ancestor_id', 
            'ancestor__name', 
            'ancestor__level__name'
        ).annotate(
            link_count=Count('descendant_id')
        ).filter(
            link_count=total_selected  # MUST match the number of selected items
        )
        
        # Format: {"Glob": 1, "Continent": 5}
        common_parents = {}
        for row in common_ancestors_qs:
            # We exclude 'Self' (depth=0) usually, but for dropdowns it's fine to keep all
            level_name = row['ancestor__level__name']
            common_parents[level_name] = {
                "name": row['ancestor__name'], 
                "id": row['ancestor_id']
            }
        
        return Response(
            {
                "common_parents": common_parents, 
                "total_selected": total_selected
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put'], url_path='bulk-update')
    def bulk_update(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        all_ids = request.data.get('all_ids', [])
        payload = request.data.get('payload', {})
        
        if not payload:
            return Response({"error": "Payload is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if all_ids not in ['true', 'True']:
            if ids and not isinstance(ids, list):
                return Response({"error": "Invalid 'ids' format"}, status=status.HTTP_400_BAD_REQUEST)
            nodes = Node.objects.filter(id__in=ids)
        else:
            nodes = Node.objects.all()   
        
        if not nodes.exists():
            return Response({"error": "No valid nodes found"}, status=status.HTTP_404_NOT_FOUND)
                
        results = []
        errors = []
        payload_attributes = payload.pop('attributes', None)
        
        
        try:
            with transaction.atomic():
                for node in nodes:
                    node_data = payload.copy()
                    
                    if payload_attributes:
                        current_attributes = node.attributes.copy() if node.attributes else {}
                        current_attributes.update(payload_attributes)
                        node_data['attributes'] = current_attributes
                    
                    input_serializer = NodeSerializer(node, data=node_data, partial=True)
                    if input_serializer.is_valid():
                        print(input_serializer.validated_data)
                        input_serializer.save()
                        results.append({"id": node.id, "node": input_serializer.data})
                    else:
                        errors.append({"id": node.id, "errors": input_serializer.errors})
                        raise ValidationError(input_serializer.errors)
        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
        return Response(
            {
                "message": f"Successfully updated {len(results)} nodes",
                "updated_ids": [r['id'] for r in results],
            }, status=status.HTTP_200_OK
        )
                        
                    
            
        
        


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from collections import defaultdict

class NodeSearchAPIView(APIView):
    """
    POST /api/search/nodes/?dimension=1
    Body:
    {
        "Glob": "Earth",
        "Continent": "Asia",
        "Country": "In",
        "search_key": "Country"
    }
    """
    def post(self, request):
        # 1. Get Params
        dimension_id = request.query_params.get('dimension')
        if not dimension_id:
            return Response({"error": "Dimension ID is required"}, status=400)
        
        print(request.data)
        
        search_data = request.data.copy()
        target_level_name = search_data.pop('search_key', "").strip() # e.g., "Country"
        
        if not target_level_name:
            return Response({"error": "search_key is required in body"}, status=400)

        # 2. Get the Search Value (e.g., "In" for Country)
        raw_value = search_data.get(target_level_name)
        search_value = str(raw_value).strip() if raw_value else ""

        # 3. Step A: Find CANDIDATE Nodes first
        # We search for ANY node at Level="Country" that contains "In"
        nodes = Node.objects.filter(
            dimension_id=dimension_id,
            level__name__iexact=target_level_name,
            is_hidden=False,
            on_hold=False
        ).distinct()
        
        # CONDITIONAL: Filter by Name OR Alias
        if search_value:
            nodes = nodes.filter(                   # Match Current ID
                Q(name__icontains=search_value) |             # Match Current Name
                Q(aliases__name__icontains=search_value)      # Match Alias Name
            )
        
        # IMPORTANT: Order matching to ensure "First 10" is consistent
        nodes = nodes.prefetch_related('aliases').order_by('name')

        if not nodes.exists():
            return Response([])

        # 4. Step B: Validate Hierarchy (The "Parent Check")
        # We need to verify that each candidate belongs to "Earth" -> "Asia"
        
        # Prepare filters from body (exclude the target itself)
        # parent_filters = {"Glob": "Earth", "Continent": "Asia"}
        parent_filters = {k: v for k, v in search_data.items() if k != target_level_name}
        
        # Prefetch ancestors for all nodes to avoid N+1 queries
        # We use NodeClosure to get the full path
        node_ids = nodes.values_list('id', flat=True)
        
        closures = NodeClosure.objects.filter(
            descendant_id__in=node_ids
        ).select_related('ancestor', 'ancestor__level').order_by('descendant_id', '-depth')

        # Group ancestors by Node ID
        # node_paths = { 101: { "Glob": <NodeObj>, "Continent": <NodeObj> }, ... }
        node_paths = defaultdict(dict)
        for c in closures:
            node_paths[c.descendant_id][c.ancestor.level.name] = c.ancestor

        final_results = []

        for node in nodes:
            # STOPPING CONDITION
            if len(final_results) >= 10:
                break
            
            # Get ancestors
            my_path = node_paths.get(node.id, {})
            
            # --- HIERARCHY VALIDATION ---
            is_valid = True
            # for req_level, req_name in parent_filters.items():
            #     if req_level not in my_path:
            #         # Special case: If the user filters by "Country" and we ARE the Country, check self.
            #         # But usually parent filters are strictly ancestors.
            #         is_valid = False 
            #         continue
                
            #     ancestor_node = my_path[req_level]
            #     if ancestor_node.name.lower() != req_name.lower():
            #         is_valid = False
            #         break
            for req_level, req_name in parent_filters.items():
                req_name = str(req_name).strip()
                if not req_name:
                    continue  # ignore empty filters

                ancestor_node = my_path.get(req_level)

                if not ancestor_node:
                    # allow missing Zone for old data
                    if req_level.lower() == "zone":
                        continue
                    is_valid = False
                    break

                if ancestor_node.name.lower() != req_name.lower():
                    is_valid = False
                    break
            
            if is_valid:
                # --- MATCH TYPE LOGIC (Current vs Alias) ---
                match_type = "Current Name"
                matched_word = node.name
                
                # Check if we matched via Alias
                # We use 'search_value' from the outer scope
                if search_value and search_value.lower() not in node.name.lower():
                    for alias in node.aliases.all():
                        if search_value.lower() in alias.name.lower():
                            match_type = "Alias"
                            matched_word = alias.name
                            break
                
                # --- BUILD RESPONSE ---
                formatted_item = {}
                
                # 1. Add Metadata
                formatted_item['meta'] = {
                    "match_type": match_type,
                    "matched_word": matched_word
                }
                
                # 2. Add Ancestors (Glob, Continent, etc.)
                for level_name, node_obj in my_path.items():
                    formatted_item[level_name] = {
                        "id": node_obj.id,
                        "name": node_obj.name,
                        "code": node_obj.code
                    }

                # 3. [FIX] EXPLICITLY ADD THE TARGET NODE ITSELF
                # We use 'target_level_name' (e.g., "Country") as the key
                formatted_item[target_level_name] = {
                    "id": node.id,
                    "name": node.name,
                    "code": node.code
                }
                
                final_results.append(formatted_item)

        return Response(final_results)

class CustomColumnView(APIView):
    
    def get(self, request, pk):
        existing_col_name = request.query_params.get('col_name', "").strip()
        level = get_object_or_404(Level, pk=pk)
        if existing_col_name == "":
            return Response(level.extra_fields_schema or [], status=status.HTTP_200_OK)
        
        for extra_col in level.extra_fields_schema or []:
            if extra_col['name'] == existing_col_name:
                return Response(extra_col, status=status.HTTP_200_OK)
        
        return Response({"detail": "Column not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, pk):
        level = get_object_or_404(Level, pk=pk)
        input_serializer = ColumnDefinitionSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        
        new_col = input_serializer.validated_data
        if new_col["name"] in ["name", "code", "is_hidden", "on_hold", "hold_date", "created_at", "updated_at", "id", "level", "parent"]:
            return Response({"detail": f"Column name '{new_col['name']}' already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        current_schema = level.extra_fields_schema or []
        
        
        if any([col['name'] == new_col['name'] for col in current_schema]):
            return Response({"detail": f"Column with name '{new_col['name']}' already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        current_schema.append(new_col)
        level.extra_fields_schema = current_schema
        level.save()
        
        return Response(new_col, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        level = get_object_or_404(Level, pk=pk)
        
        current_name = request.query_params.get('col_name', "").strip()
        if current_name == "":
            return Response(
                {"detail": "Column name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 1. Validate Input
        # Note: Ensure you are using the Update Serializer we defined earlier
        input_serializer = CustomDefinationUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data
        
        new_name = validated_data.get('new_name')
        if new_name in ["name", "code", "is_hidden", "on_hold", "hold_date", "created_at", "updated_at", "id", "level", "parent"]:
            return Response({"detail": f"Column name '{new_name}' already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        # 2. Find existing column
        current_schema = level.extra_fields_schema or []
        target_index = -1
        existing_col = None
        
        for i, col in enumerate(current_schema):
            if col['name'] == current_name:
                target_index = i
                existing_col = col
                break
        
        if target_index == -1:
            return Response(
                {"detail": f"Column '{current_name}' not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 3. Handle Renaming (Only if new_name is provided AND different)
        final_name = current_name
        if new_name and new_name != current_name:
            # Check for duplicates in OTHER columns
            if any(col['name'] == new_name for col in current_schema):
                return Response(
                    {"detail": f"Column with name '{new_name}' already exists"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            final_name = new_name
            
            # OPTIONAL: If renaming, you might want to update key/label too?
            # existing_col['key'] = new_name
            # existing_col['label'] = new_name.replace('_', ' ').title()

        # 4. Prepare Values
        existing_type = existing_col.get('type')
        
        # Use new default if provided, otherwise keep existing
        # checking "if key in validated_data" allows clearing the default (setting to None)
        if 'default_value' in validated_data:
            new_default_value = validated_data['default_value']
        else:
            new_default_value = existing_col.get('default_value')
            
        # B. Required Status Logic
        existing_required = existing_col.get('required', False)
        # If 'required' is sent in body, use it; otherwise keep existing
        new_required = validated_data.get('required', existing_required)
        
        # Handle Max Length (Only for char)
        new_max_length = None
        if existing_type == 'char':
            existing_max = existing_col.get('max_length')
            new_max_length = validated_data.get('max_length', existing_max)
            
        if new_required and not existing_required:
            if new_default_value in [None, ""]:
                return Response(
                    {"default_value": "Required columns must have a default value"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 5. Validate Consistency
        try:
            self._validate_value_type(new_default_value, existing_type, new_max_length)
        except (ValidationError, ValueError) as e: # FIX: Catch both error types
            # Unwrap the error message safely
            msg = e.detail[0] if isinstance(e, ValidationError) and isinstance(e.detail, list) else str(e)
            return Response({"default_value": msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # 6. Apply Updates
        existing_col['name'] = final_name
        existing_col['default_value'] = new_default_value
        existing_col['max_length'] = new_max_length
        existing_col['required'] = new_required
        
        # 7. Save
        level.extra_fields_schema[target_index] = existing_col
        level.save()
        
        return Response(existing_col, status=status.HTTP_200_OK)
    
    
    def delete(self, request, pk):
        try:
            level = get_object_or_404(Level, pk=pk)
            col_name = request.query_params.get('col_name', "").strip()
            if col_name == "":
                return Response(
                    {"detail": "Column name is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            current_schema = level.extra_fields_schema or []
            target_index = -1
            
            for i, col in enumerate(current_schema):
                if col['name'] == col_name:
                    target_index = i
                    break
            
            if target_index == -1:
                return Response(
                    {"detail": f"Column '{col_name}' not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            del current_schema[target_index]
            level.extra_fields_schema = current_schema
            level.save()
        except Exception as e:
            return Response({"Error": "Error on deleting column"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _validate_value_type(self, value, field_type, max_len=None):
        """
        Helper method to check if 'value' matches 'field_type'
        """
        if value in [None, ""]:
            return
        
        # 1. Integer Checks
        if field_type in ['int', 'bigint']:
            if not str(value).lstrip('-').isdigit():
                 raise ValueError("The value must be an integer.")

        elif field_type == 'positive_int':
            if not str(value).isdigit(): 
                 raise ValueError("The value must be a positive integer.")
            if int(value) < 0:
                raise ValueError("The value must be a positive integer.")

        # 2. Float Check
        elif field_type == 'float':
            try:
                float(value)
            except ValueError:
                raise ValueError("The value must be a float.")

        # 3. Boolean Check
        elif field_type == 'boolean':
            if str(value).lower() not in ['true', '1', 'yes', 'on', 'false', '0', 'no', 'off']:
                raise ValueError("The value must be a boolean.")

        # 4. Date Checks
        elif field_type == 'date':
            try:
                datetime.datetime.strptime(str(value), '%Y-%m-%d')
            except ValueError:
                raise serializers.ValidationError("Date must be in YYYY-MM-DD format.")

        elif field_type == 'datetime':
            try:
                datetime.datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    datetime.datetime.strptime(str(value), '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    raise serializers.ValidationError("DateTime must be in YYYY-MM-DD HH:MM:SS format.")

        # 5. Char Check
        elif field_type == 'char':
            if max_len and len(str(value)) > max_len:
                raise serializers.ValidationError(f"Default value cannot exceed {max_len} characters.")
        
        
        