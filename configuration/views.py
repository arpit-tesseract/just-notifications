from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
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
                )
                
                # update children
                child = qs.filter(parent=instance).first()
                if child:
                    child.parent = instance.parent
                    child.save(update_fields=['parent'])
                
                # CLOSE THE GAP (Shift everyone up)
                qs.filter(sort_order__gt=instance.sort_order).update(sort_order=F('sort_order') - 1)

                # ACTUAL DELETE
                instance.soft_delete(user=self.request.user)
                
        except Exception as e:
            level_logger.exception("Failed to delete level:", e)
            raise ValidationError({"error": "Failed to delete. Please try again."})
                
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
    
    def perform_destroy(self, instance):
        try:
            instance.soft_delete(user=self.request.user)
        except Exception as e:
            raise ValidationError({"error": "Failed to delete. Please try again."})
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
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
        ).annotate(
            # This calculates the count of nodes having the same parent_id 
            # and same level_id across the entire table
            parent_total_count=Window(
                expression=Count('id'),
                partition_by=[F('parent_id'), F('level_id')]
            )
        ).order_by('id') # Ordering is mandatory for pagination!
        
        # 2. Apply Name/Code Search
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |      # Match Name
                Q(code__icontains=search_query)       # Match Code (Optional)
            )        

        # 3. Standard Filters (Hidden / On Hold)
        is_hidden_param = request.query_params.get("is_hidden", "").strip()
        if is_hidden_param != "":
            is_hidden_bool = is_hidden_param.lower() == "true"
            queryset = queryset.filter(is_hidden=is_hidden_bool)
        
        on_hold_param = request.query_params.get("on_hold", "").strip()
        if on_hold_param != "":
            on_hold_bool = on_hold_param.lower() == "true"
            queryset = queryset.filter(on_hold=on_hold_bool)
            
        # 4. Ancestor Filtering
        ancestor_ids_param = request.query_params.get("ancestor_ids", "").strip()
        if ancestor_ids_param != "":
            try:
                # Convert "1,5" -> [1, 5]
                ancestor_ids = [int(x) for x in ancestor_ids_param.split(',') if x.strip().isdigit()]
                
                if ancestor_ids:
                    for ancestor_id in ancestor_ids:
                        # Use NodeClosure for efficient lookup
                        queryset = queryset.filter(
                            id__in=NodeClosure.objects.filter(
                                ancestor_id=ancestor_id
                            ).values('descendant_id')
                        )
            except ValueError:
                pass # Ignore invalid format
            
        # ==============================================
        # 5. Dynamic Attribute Filtering (The Fix)
        # ==============================================
        
        # A. Get Schema for this level
        level_obj = Level.objects.filter(id=level).first()
        defined_schema = level_obj.extra_fields_schema if level_obj else []
        
        # Map schema for easy lookup: {'isgenz': {'type': 'boolean', ...}}
        schema_map = {col['name']: col for col in defined_schema} 

        # B. Loop through request parameters
        # We explicitly exclude standard params to avoid collisions
        standard_params = ['dimension', 'level', 'search', 'page', 'page_size', 'is_hidden', 'on_hold', 'ancestor_ids']
        
        for param, raw_value in request.query_params.items():
            if param in standard_params:
                continue

            # Check if this param is actually in your schema
            if param in schema_map:
                column_def = schema_map[param]
                field_type = column_def.get('type', 'char')
                default_val_raw = column_def.get('default_value')
                
                try:
                    # 1. Cast the Request Value
                    typed_value, lookup = cast_value_by_type(raw_value, field_type)
                    if typed_value is None:
                        continue

                    # 2. Cast the Default Value
                    typed_default, _ =  (default_val_raw, field_type)
                    
                    # 3. Check if user is searching for the default
                    is_searching_default = (typed_default is not None) and (typed_value == typed_default)

                    if is_searching_default:
                        # LOGIC: Implicit Default (Missing Key) OR Explicit Default (Saved Value)
                        queryset = queryset.filter(
                            Q(**{f"attributes__{param}__{lookup}": typed_value}) | 
                            ~Q(attributes__has_key=param)
                        )
                    else:
                        # LOGIC: Standard search (Must exist and match)
                        queryset = queryset.filter(**{f"attributes__{param}__{lookup}": typed_value})

                except ValueError as e:
                    # Handle invalid input format (e.g. user sent "abc" for an int field)
                    print(f"Skipping filter for {param}: {e}")
                    continue

        # ==============================================
        # 6. Pagination & Response Construction
        # ==============================================
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            # Serialize ONLY the paginated nodes
            node_data_list = NodeOutputSerializer(page, many=True).data
            
            # Extract IDs for just this page
            node_map = {n['id']: n for n in node_data_list}
            target_ids = list(node_map.keys())

            # Fetch Paths (Closures) ONLY for these items
            grouped_paths = defaultdict(dict)
            
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

                for c in closures:
                    if c.ancestor.level: # Check just in case root has no level
                        level_name = c.ancestor.level.name
                        grouped_paths[c.descendant_id][level_name] = {
                            "id": c.ancestor.id,
                            "name": c.ancestor.name,
                            "code": c.ancestor.code
                        }

            # Combine & Return Paginated Response
            result = []
            # Iterate over the LIST to preserve order from node_data_list
            for node_data in node_data_list:
                nid = node_data['id']
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
        ids_param = request.query_params.get('ids', [])
        all_ids = request.query_params.get('all_ids', False)
        level_id = request.query_params.get('level_id', None)

        
        if all_ids and all_ids in ["true", "True", True]:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            nodes = Node.objects.filter(level_id=level_id)
        
        elif ids_param:
            try:
                ids = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
            except ValueError:
                return Response({"error": "Invalid ids format"}, status=status.HTTP_400_BAD_REQUEST)

            if not ids:
                return Response({"error": "No valid numeric ids provided"}, status=status.HTTP_400_BAD_REQUEST)

            nodes = Node.objects.filter(id__in=ids)

        else:
            return Response({"error": "Either 'all_ids' or 'ids' parameter is required"}, status=400)
        
        if not nodes.exists():
            return Response({"error": "No valid nodes found"}, status=status.HTTP_404_NOT_FOUND)
        

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
                "id": row['ancestor_id'],
                "name": row['ancestor__name'], 
            }
        
        return Response(
            {
                "common_parents": common_parents, 
                "total_selected": total_selected
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put'], url_path='bulk-update')
    def bulk_update(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
        all_ids = request.data.get('all_ids', False)
        level_id = request.data.get('level_id', None)

        payload = request.data.get('payload', {})
        
        if not payload:
            return Response({"error": "Payload is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if all_ids and all_ids in ["true", "True", True]:
            if not level_id:
                return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            nodes = Node.objects.filter(level_id=level_id)
        
        elif ids:
            if not isinstance(ids, list):
                return Response({"error": "Invalid 'ids' format"}, status=status.HTTP_400_BAD_REQUEST)
            
            nodes = Node.objects.filter(id__in=ids)
        else:
            return Response({"error": "Either 'all_ids' or 'ids' parameter is required"}, status=400)
        
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
        
    
    # In views.py, inside NodeViewSet class

    @action(detail=False, methods=['post'], url_path='merge-to-existing')
    def merge_nodes(self, request):
        """
        Merge multiple source nodes into one target node.
        1. Source Node names become Aliases for Target.
        2. Children of Source are moved to Target.
        3. Source Nodes are deleted.
        """
        serializer = NodeMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target = serializer.validated_data['target_node']
        sources = serializer.validated_data['source_nodes']

        # Counters for response
        moved_children_count = 0
        created_aliases_count = 0

        try:
            with transaction.atomic():
                for source in sources:
                    # A. Create Alias
                    # We save the old name so users searching for "Old Country" find "New Country"
                    if not NodeAlias.objects.filter(node=target, name=source.name).exists():
                        NodeAlias.objects.create(
                            node=target, 
                            name=source.name, 
                            note=f"Merged from Node ID {source.id}"
                        )
                        created_aliases_count += 1
                    
                    # Also move existing aliases from Source to Target
                    existing_aliases = NodeAlias.objects.filter(node=source)
                    for alias in existing_aliases:
                        alias.node = target
                        alias.save()

                    # B. Reparent Children (CRITICAL STEP)
                    # We must iterate and .save() to trigger the 'manage_node_closure' signal
                    # found in your signals.py. If we do .update(), the closure table won't fix itself.
                    children = Node.objects.filter(parent=source)
                    for child in children:
                        child.parent = target
                        child.save() # This triggers signals.py to fix ancestry
                        moved_children_count += 1

                    # C. Delete Source
                    # (Optional: You could set is_archived=True instead of deleting)
                    source.soft_delete(user=request.user)

            return Response({
                "message": "Merge successful",
                "target_node": {
                    "id": target.id,
                    "name": target.name
                },
                "summary": {
                    "merged_nodes_count": len(sources),
                    "children_moved": moved_children_count,
                    "aliases_created": created_aliases_count
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            level_logger.exception("Merge failed:", str(e))
            return Response(
                {
                    "error": "Failed to merge nodes",
                    "details": str(e)
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    
    @action(detail=False, methods=['post'], url_path='merge-to-new')
    def merge_to_new_node(self, request):
        serializer = NodeMergeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Everything is already validated and fetched!
        data = serializer.validated_data
        
        new_name = data['name']
        new_code = data.get('code')
        dimension = data['dimension'] # Actual Dimension Object
        level = data['level']         # Actual Level Object
        parent = data.get('parent')   # Actual Node Object (or None)
        attributes = data.get('attributes', {})
        sources = data['source_nodes_objects'] # The list of Node objects we stored in validate()

        try:
            with transaction.atomic():
                # 1. Create New Node
                new_node = Node.objects.create(
                    name=new_name,
                    code=new_code,
                    dimension=dimension,
                    level=level,
                    parent=parent,
                    attributes=attributes
                )

                # 2. Merge Logic (Aliases & Children)
                summary = {"children_moved": 0, "aliases_created": 0}

                for source in sources:
                    # Create Alias (History)
                    if not NodeAlias.objects.filter(node=new_node, name=source.name).exists():
                        NodeAlias.objects.create(
                            node=new_node, 
                            name=source.name, 
                            note=f"Merged from deleted Node ID {source.id}"
                        )
                        summary['aliases_created'] += 1
                    
                    # Move existing aliases
                    NodeAlias.objects.filter(node=source).update(node=new_node)

                    # Move Children
                    children = Node.objects.filter(parent=source)
                    for child in children:
                        child.parent = new_node
                        child.save() # Trigger Signal
                        summary['children_moved'] += 1

                    # Delete Source
                    source.soft_delete(user=request.user)

            return Response({
                "message": "Merge successful",
                "new_node": {
                    "id": new_node.id, 
                    "name": new_node.name,
                    "attributes": new_node.attributes
                },
                "summary": summary
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
    @action(detail=False, methods=['get'], url_path='export-selected')
    def export_selected(self, request):
        level_id = request.query_params.get('level_id')
        all_ids = request.query_params.get('all_ids', False)
        ids_param = request.query_params.get('ids')
        
        target_level = None
        nodes = []

        if all_ids and all_ids in ["true", "True", True]:
            if not level_id:
                return Response({"error": "level_id is required"}, status=400)
            
            try:
                target_level = Level.objects.get(id=level_id)
            except Level.DoesNotExist:
                return Response({"error": "Level not found"}, status=404)

            nodes = Node.objects.filter(level_id=level_id).select_related('parent', 'parent__parent', 'parent__parent__parent')

        # Case A: Export Selected Nodes by ID
        elif ids_param:
            try:
                ids = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
            except ValueError:
                return Response({"error": "Invalid ids format"}, status=400)
            
            if not ids:
                return Response({"error": "No ids provided"}, status=400)
                
            nodes = Node.objects.filter(id__in=ids).select_related('level', 'parent', 'parent__parent', 'parent__parent__parent')
            
            if not nodes.exists():
                return Response({"error": "No nodes found for the provided IDs"}, status=404)
            
            # Validation: Ensure all nodes are from the SAME level
            first_node = nodes.first()
            target_level = first_node.level
            
            if nodes.exclude(level=target_level).exists():
                return Response({
                    "error": "Export failed: All selected nodes must belong to the same Level to maintain consistent Excel columns."
                }, status=400)
        
        else:
            return Response({"error": "Either 'all_ids' or 'ids' parameter is required"}, status=400)

        # ---------------------------------------------------------
        # GENERATE EXCEL DATA (Same logic as before)
        # ---------------------------------------------------------
        
        dimension = target_level.dimension
        
        # 1. Identify Ancestor Levels (for columns like Glob | Continent | ...)
        ancestor_levels = Level.objects.filter(
            dimension=dimension,
            sort_order__lt=target_level.sort_order
        ).order_by('sort_order')
        
        ancestor_col_names = [lvl.name for lvl in ancestor_levels]

        data = []
        for node in nodes:
            row = {}
            
            # A. Fill Ancestor Columns (Walk up the parent chain)
            curr = node
            for ancestor_name in reversed(ancestor_col_names):
                if curr.parent:
                    row[ancestor_name] = curr.parent.name
                    curr = curr.parent
                else:
                    row[ancestor_name] = "" 

            # B. Fill Self Data
            row[target_level.name] = node.name
            row['Code'] = node.code
            row['Hidden'] = node.is_hidden
            row['On Hold'] = node.on_hold
            row['Hold Date'] = node.hold_date

            # C. Fill Custom Columns (Attributes)
            attributes = node.attributes or {}
            for key, value in attributes.items():
                row[key] = value
                
            data.append(row)

        if not data:
            return Response({"message": "No data to export"}, status=200)

        # 2. Build DataFrame
        df = pd.DataFrame(data)
        
        # 3. Order Columns
        custom_schema_keys = [col['name'] for col in (target_level.extra_fields_schema or [])]
        final_columns = ancestor_col_names + [target_level.name, 'Code', 'Hidden', 'On Hold'] + custom_schema_keys
        
        # Ensure all columns exist (fill missing with None)
        for col in final_columns:
            if col not in df.columns:
                df[col] = None

        df = df[final_columns]

        # 4. Return Response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"{target_level.name}_Export.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=target_level.name)
            
        return response
                    
    
    @action(detail=False, methods=['post'], url_path='upload-excel', parser_classes=[MultiPartParser])
    def upload_excel(self, request):
        """
        Uploads an Excel file formatted exactly like the 'export-selected' output.
        Required params: file, level_id
        """
        file_obj = request.FILES.get('file')
        level_id = request.query_params.get('level_id')

        if not file_obj:
            return Response({"error": "File is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not level_id:
            return Response({"error": "level_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_level = Level.objects.get(pk=level_id)
        except Level.DoesNotExist:
            return Response({"error": "Level not found."}, status=status.HTTP_404_NOT_FOUND)

        # 1. Read Excel
        try:
            df = pd.read_excel(file_obj)
            # Clean up: Replace NaN with None, strip whitespace from headers
            df = df.where(pd.notnull(df), None)
            df.columns = df.columns.str.strip()
        except Exception as e:
            return Response({"error": f"Invalid Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Identify Critical Columns
        # The main name column is the Level Name itself (e.g., "Country")
        node_name_col = target_level.name 
        
        if node_name_col not in df.columns:
            return Response({
                "error": f"Invalid format. Missing required column '{node_name_col}' (Level Name)."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Identify Parent Column (Immediate parent level name)
        # We only need the immediate parent to link the hierarchy.
        parent_level = target_level.parent
        parent_col_name = parent_level.name if parent_level else None
        
        # Identify Custom Attribute Columns
        schema = target_level.extra_fields_schema or []
        custom_keys = [col['name'] for col in schema]

        summary = {"created": 0, "updated": 0, "errors": []}

        # 3. Process Rows
        try:
            with transaction.atomic():
                for index, row in df.iterrows():
                    row_index = index + 2  # Excel row number (1-based + header)
                    row_data = row.to_dict()
                    
                    # A. Get Name
                    name = row_data.get(node_name_col)
                    if not name:
                        continue # Skip empty rows

                    # B. Resolve Parent
                    parent_node = None
                    if parent_col_name:
                        parent_name_val = row_data.get(parent_col_name)
                        if parent_name_val:
                            # Look up parent. 
                            # Note: Strictly, we should filter by the grandparent to be safe, 
                            # but usually Name+Level is unique enough in a context.
                            parent_node = Node.objects.filter(
                                name=parent_name_val,
                                level=parent_level,
                                dimension=target_level.dimension
                            ).first()
                            
                            if not parent_node:
                                summary["errors"].append(f"Row {row_index}: Parent '{parent_name_val}' ({parent_col_name}) not found.")
                                continue
                        else:
                            # If parent is required by hierarchy but missing in file
                            summary["errors"].append(f"Row {row_index}: Missing parent value for '{parent_col_name}'.")
                            continue

                    # C. Extract Standard Fields
                    # Maps Excel headers 'Code', 'Hidden', 'On Hold' to model fields
                    code_val = row_data.get('Code')
                    is_hidden_val = bool(row_data.get('Hidden', False))
                    on_hold_val = bool(row_data.get('On Hold', False))

                    if code_val is not None:
                        collision_qs = Node.objects.filter(
                            level=target_level,
                            code=code_val,
                            parent=parent_node
                        )

                        existing_node_with_code = collision_qs.first()
    
                        if existing_node_with_code and existing_node_with_code.name != name:
                            raise Exception(
                                f"Row {row_index}: Code '{code_val}' is already used by {target_level.name} '{existing_node_with_code.name}'. "
                                f"Codes must be unique within this level."
                            )
                    
                    # Handle Date format for 'Hold Date'
                    # hold_date_val = row_data.get('Hold Date')
                    # if hold_date_val and pd.isna(hold_date_val):
                    #     hold_date_val = None

                    # 1. Get the raw value
                    raw_hold_date = row_data.get('Hold Date')
                    hold_date_val = None

                    # 2. Check if it has a value (isn't None or NaN)
                    if raw_hold_date and not pd.isna(raw_hold_date):
                        try:
                            # Force conversion to datetime. 
                            # dayfirst=True ensures 19-02-2026 is read as Feb 19th, not invalid month 19.
                            dt_obj = pd.to_datetime(raw_hold_date, dayfirst=True)
                            
                            # Convert to Python date object (YYYY-MM-DD) for Django
                            hold_date_val = dt_obj.date()
                            
                        except (ValueError, TypeError):
                            # Optional: Log a warning or error if the date format is totally wrong
                            print(f"Warning: Row {row_index} has invalid date '{raw_hold_date}'")
                            hold_date_val = None
                    
                    # D. Extract Custom Attributes
                    attributes = {}
                    for key in custom_keys:
                        if key in row_data:
                            val = row_data[key]
                            attributes[key] = val

                    # E. Update or Create
                    # We identify the node by Name + Parent (or just Name if root)
                    lookup_kwargs = {
                        "name": name,
                        "level": target_level,
                        "parent": parent_node
                    }

                    print("Hold date:", hold_date_val)
                    
                    defaults = {
                        "code": code_val,
                        "is_hidden": is_hidden_val,
                        "on_hold": on_hold_val,
                        "hold_date": hold_date_val,
                        "attributes": attributes,
                        "dimension": target_level.dimension
                    }

                    node, created = Node.objects.update_or_create(
                        **lookup_kwargs,
                        defaults=defaults
                    )

                    # F. Validate Custom Attributes (Model Logic)
                    try:
                        node.validate_attributes()
                        node.save()
                    except ValidationError as e:
                        # Re-raise to trigger atomic rollback or catch to log error
                        # Here we catch to log, but since we are in atomic, 
                        # you might want to raise Exception to rollback the whole batch.
                        raise Exception(f"Row {row_index} Validation Error: {e.messages}")

                    if created:
                        summary["created"] += 1
                    else:
                        summary["updated"] += 1

        except Exception as e:
            # If any strict error occurs (like Validation), the atomic block rolls back everything.
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # If we collected specific row errors (like missing parents) without raising Exception
        if summary["errors"]:
            return Response({
                "message": "Upload completed with errors.",
                "summary": summary
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Upload successful.",
            "summary": {
                "created": summary["created"],
                "updated": summary["updated"]
            }
        }, status=status.HTTP_200_OK)
        
        


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
        input_serializer = ColumnDefinitionSerializer(data=request.data, context={"level": level})
        input_serializer.is_valid(raise_exception=True)
        
        new_col = input_serializer.validated_data
        if new_col["name"] in ["name", "code", "is_hidden", "on_hold", "hold_date", "created_at", "updated_at", "id", "level", "parent"]:
            return Response({"detail": f"Column name '{new_col['name']}' already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        current_schema = level.extra_fields_schema or []
        
        default_value = new_col.get("default_value")
        if default_value:
            pass
        
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
            default_value = validated_data['default_value']
            if existing_type == 'boolean' and (default_value == "" or default_value is None):
                default_value = "false"

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
            print("new_max_length", new_max_length)
            
        if new_required and not existing_required:
            if new_default_value in [None, ""]:
                return Response(
                    {"default_value": "Required columns must have a default value"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 5. Validate Consistency
        try:
            new_default_value = self._validate_value_type(new_default_value, existing_type, new_max_length)
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
        s_value = str(value)

        # 1. Integer Checks
        if field_type in ['int', 'bigint']:
            if not s_value.lstrip('-').isdigit():
                 raise ValueError("The value must be an integer.")
            return int(s_value) # <--- RETURN INT

        elif field_type == 'positive_int':
            if not s_value.isdigit():
                 raise ValueError
            val = int(s_value)
            if val < 0:
                raise ValueError("The value must be a positive integer.")
            return val # <--- RETURN INT

        # 2. Float Check
        elif field_type == 'float':
            try:
                val = float(s_value)
                return val # <--- RETURN FLOAT
            except ValueError:
                raise ValueError("The value must be a float.")

        # 3. Boolean Check
        elif field_type == 'boolean':
            lower_val = s_value.lower()
            if lower_val in ['true', '1', 'yes', 'on']:
                return True # <--- RETURN TRUE (bool)
            elif lower_val in ['false', '0', 'no', 'off']:
                return False # <--- RETURN FALSE (bool)
            else:
                raise ValueError("The value must be a boolean.")

        # 4. Date Checks (Keep as string for JSON, but ensure format)
        elif field_type == 'date':
            try:
                datetime.datetime.strptime(s_value, '%Y-%m-%d')
                return s_value # Return sanitized string
            except ValueError:
                raise serializers.ValidationError("Date must be in YYYY-MM-DD format.")

        elif field_type == 'datetime':
            try:
                datetime.datetime.strptime(s_value, '%Y-%m-%d %H:%M:%S')
                return s_value
            except ValueError:
                try:
                    # Allow T separator
                    datetime.datetime.strptime(s_value, '%Y-%m-%dT%H:%M:%S')
                    return s_value
                except ValueError:
                    raise serializers.ValidationError("DateTime must be in YYYY-MM-DD HH:MM:SS format.")

        # 5. Char / Text Checks
        elif field_type == 'char':
            if max_len and len(s_value) > max_len:
                raise serializers.ValidationError(f"Default value cannot exceed {max_len} characters.")
            return s_value
        
        elif field_type == 'text':
            return s_value

        return s_value