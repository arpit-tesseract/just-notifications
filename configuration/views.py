from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_date
from .models import *
from .serializers import *
from rest_framework.decorators import action
from django.db.models import Count, Window, F, Q
from .pagination import ConfigurationPagination
from .utils import cast_value_by_type, check_bool_value, validate_value_type
from .services import reassign_user_node_references, count_user_node_references

from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
import threading
from .tasks import process_level_deletion
from .mixins import BaseHistoryDiffAPIViewMixin
from simple_history.utils import update_change_reason
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import uuid
import json
import logging
level_logger = logging.getLogger("Levels")

class DimensionListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        dimensions = Dimension.objects.filter(is_active=True)
        serializer = DimensionIdNameSerializer(dimensions, many=True)
        return Response(serializer.data)
    
from django.db import connection
def level_deletion(level_id, user_id):
    """
    A wrapper function to run the heavy task and safely clean up 
    the Django database connection afterward.
    """
    try:
        # Call the function directly (DO NOT use .delay() here)
        process_level_deletion(level_id, user_id)
    finally:
        # CRITICAL: You must manually close the connection in a custom thread
        connection.close()

class LevelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LevelSerializer
        return LevelDetailSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Trigger Celery task
        # process_level_deletion.delay(instance.id, request.user.id)
        # Spawn the background thread
        thread = threading.Thread(
            target=level_deletion, 
            args=(instance.id, request.user.id)
        )
        thread.start() # Starts the background work
        return Response(
            {"message": f"Deletion of '{instance.display_name}' table is processing in background."},
            status=status.HTTP_202_ACCEPTED
        )      

    # def perform_destroy(self, instance):
    #     try:
    #         with transaction.atomic():
    #             # Assuming you have a node_logger defined
    #             # node_logger.info(f"Try to delete(archived) node {instance.name}")
                
    #             # 1. FIND ALL IMMEDIATE CHILDREN
    #             # We select_for_update() to lock these rows while we modify their parent
    #             nodes_in_level = Node.objects.select_for_update().filter(level=instance)
                
    #             # 2. BRIDGE THE GAP (Re-link to the deleted node's parent)
    #             for node in nodes_in_level:
    #                 Node.objects.filter(parent=node).update(parent=node.parent)

    #                 node.soft_delete(user=self.request.user)
    #             # 3. ACTUAL DELETE (Soft delete)
    #             # Assuming `soft_delete` is provided by your SoftDeleteMixin
    #             instance.soft_delete(user=self.request.user)
                
    #     except Exception as e:
    #         print(e)
    #         # node_logger.exception("Failed to delete node:", e)
    #         raise ValidationError({"error": "Failed to delete node. Please try again."})

    # def perform_destroy(self, instance):
    #     try:
    #         with transaction.atomic():
    #             level_logger.info(f"Try to delete(archived) level {instance.name}")
    #             qs = Level.objects.select_for_update().filter(
    #                 dimension=instance.dimension,
    #             )
                
    #             # update children
    #             child = qs.filter(parent=instance).first()
    #             if child:
    #                 child.parent = instance.parent
    #                 child.save(update_fields=['parent'])
                
    #             # CLOSE THE GAP (Shift everyone up)
    #             qs.filter(sort_order__gt=instance.sort_order).update(sort_order=F('sort_order') - 1)

    #             # ACTUAL DELETE
    #             instance.soft_delete(user=self.request.user)
                
    #     except Exception as e:
    #         level_logger.exception("Failed to delete level:", e)
    #         raise ValidationError({"error": "Failed to delete. Please try again."})
                
    #     # return super().perform_destroy(instance)

class LevelListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        dimension_id = request.query_params.get('dimension_id', "").strip()
        if not dimension_id:
            return Response({"dimension_id": "Dimension cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if not dimension_id.isdigit():
            return Response({"dimension_id": "Dimension must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        
        levels = Level.objects.filter(
            dimension_id=dimension_id,
        )
        serializer = LevelIdNameSerializerWithCustomColumn(levels, many=True)
        return Response(serializer.data)

from collections import defaultdict
from django.db.models import F

class NodeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = Node.objects.select_related("dimension", "level", "parent")
    serializer_class = NodeSerializer
    pagination_class = ConfigurationPagination
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return NodeSerializer
        return NodeIdNameSerializer
    
    def perform_destroy(self, instance):
        # 1. Check for Dependencies (Only count active, non-deleted items)
        child_nodes_count = Node.objects.filter(parent=instance, is_deleted=False).count()
        user_nodes_count = count_user_node_references(instance.id)

        dependencies = []
        if child_nodes_count > 0:
            dependencies.append(f"{child_nodes_count} child node(s)")
        if user_nodes_count > 0:
            dependencies.append(f"{user_nodes_count} user record(s)")

        # 2. Block Deletion if dependencies exist
        if dependencies:
            dependency_str = " and ".join(dependencies)
            raise DRFValidationError({
                "error": f"Cannot delete '{instance.name}'. It is currently referenced by {dependency_str}. Please delete or reassign them first.",
                "requires_resolution": True,
            })

        # 3. If safe, execute the database soft deletion
        try:
            with transaction.atomic():
                instance.soft_delete(user=self.request.user)
                
                # Optional: Log the deletion reason in history
                update_change_reason(instance, "Deleted via API")
                
        except DRFValidationError as e:
            # Safely pass our custom validation errors straight to the frontend
            raise e 
            
        except Exception as e:
            # Log unexpected system crashes and return a generic error
            level_logger.exception(f"Failed to delete node: {e}")
            raise DRFValidationError({"error": "Failed to delete. Please try again."})
        
    @action(detail=True, methods=['get'], url_path='delete-preview')
    def delete_preview(self, request, pk=None):
        instance = self.get_object()
        child_nodes_count = Node.objects.filter(parent=instance, is_deleted=False).count()
        user_nodes_count = count_user_node_references(instance.id)
        return Response({
            "node_id": instance.id,
            "node_name": instance.name,
            "child_nodes_count": child_nodes_count,
            "user_references_count": user_nodes_count,
            "total_dependencies": child_nodes_count + user_nodes_count
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='delete-with-reassignment')
    def delete_with_reassignment(self, request, pk=None):
        instance = self.get_object()
        replacement_node_id = request.data.get('replacement_node_id')

        if not replacement_node_id:
            return Response({"error": "replacement_node_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            replacement_node = Node.objects.get(id=replacement_node_id, is_deleted=False)
        except Node.DoesNotExist:
            return Response({"error": "Replacement node not found."}, status=status.HTTP_404_NOT_FOUND)

        if replacement_node.level_id != instance.level_id:
            return Response({"error": "Replacement node must be at the same level."}, status=status.HTTP_400_BAD_REQUEST)

        if replacement_node.parent_id != instance.parent_id:
            return Response({"error": "Replacement node must have the same parent."}, status=status.HTTP_400_BAD_REQUEST)

        if replacement_node.id == instance.id:
            return Response({"error": "Replacement node cannot be the same as the node being deleted."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. Reparent children
                children = Node.objects.filter(parent=instance, is_deleted=False)
                for child in children:
                    child.parent = replacement_node
                    child.save() # Triggers closure table update

                # 2. Reassign users
                reassign_user_node_references([instance], replacement_node)

                # 3. Log event
                NodeEventLog.objects.create(
                    event_type='MERGE', # Conceptually a merge since it's reassigned
                    source_node=instance,
                    target_node=replacement_node,
                    performed_by=request.user,
                    details=f"Deleted and reassigned dependencies to node {replacement_node.id}"
                )

                # 4. Soft delete
                instance._change_reason = f"Deleted and reassigned to '{replacement_node.name}'"
                instance.soft_delete(user=request.user)

            return Response({
                "message": f"Successfully deleted '{instance.name}' and reassigned all dependencies to '{replacement_node.name}'."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            level_logger.exception(f"Failed to delete with reassignment: {e}")
            return Response({"error": "Failed to reassign and delete. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # NEW: Check if the serializer generated multiple parallel nodes
        instance = serializer.instance
        if hasattr(instance, '_created_nodes_list'):
            # It created multiple nodes! Serialize all of them into an array.
            output_serializer = self.get_serializer(instance._created_nodes_list, many=True)
            headers = self.get_success_headers(output_serializer.data)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        # Fallback to standard single response
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def list(self, request, *args, **kwargs):
        dimension = request.query_params.get("dimension", "").strip()
        level = request.query_params.get("level", "").strip()
        search_query = request.query_params.get("search", "").strip()

        if not dimension or not dimension.isdigit():
            print("Dimension:", dimension) 
            return Response({"dimension": "Valid dimension is required."}, status=status.HTTP_400_BAD_REQUEST)
         
        if not level or not level.isdigit():
             return Response({"level": "Valid level is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Step A: Get all explicitly deleted node IDs (bypassing the SoftDeleteManager)
        deleted_node_ids = Node.all_objects.filter(is_deleted=True).values_list('id', flat=True)
        
        # Step B: Get ALL descendants of those deleted nodes using the Closure table
        # This catches children, grandchildren (Countries), etc.
        hidden_branch_ids = NodeClosure.objects.filter(
            ancestor_id__in=deleted_node_ids
        ).values('descendant_id')

        # 1. Filter Target Nodes (Base Queryset)
        queryset = Node.objects.filter(
            dimension_id=int(dimension),
            level_id=int(level),
        ).exclude(
            id__in=hidden_branch_ids
        ).annotate(
            # This calculates the count of nodes having the same parent_id 
            # and same level_id across the entire table
            parent_total_count=Window(
                expression=Count('id'),
                partition_by=[F('parent_id'), F('level_id')]
            )
        ) # Ordering is mandatory for pagination!
        
        # 2. Apply Name/Code Search
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |      # Match Name
                Q(code__icontains=search_query)       # Match Code (Optional)
            )        
        
        code_start_param = request.query_params.get("code_start", "").strip()
        code_end_param = request.query_params.get("code_end", "").strip()

        try:
            code_start = parse_positive_int(code_start_param)
        except ValueError:
            return Response({"code_start": "Code start must be an integer."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            code_end = parse_positive_int(code_end_param)
        except ValueError:
            return Response({"code_end": "Code end must be an integer."}, status=status.HTTP_400_BAD_REQUEST)

        if code_start is not None and code_end is not None and code_end < code_start:
            return Response({"code_end": "Code end must be greater than code start."}, status=status.HTTP_400_BAD_REQUEST)

        # apply filters
        if code_start is not None:
            queryset = queryset.filter(code__gte=code_start)
        if code_end is not None:
            queryset = queryset.filter(code__lte=code_end)


        # 3. Standard Filters (Hidden / On Hold)
        is_hidden_param = request.query_params.get("is_hidden", "").strip()
        if is_hidden_param != "":
            is_hidden_bool = is_hidden_param.lower() == "true"
            queryset = queryset.filter(is_hidden=is_hidden_bool)
        
        on_hold_param = request.query_params.get("on_hold", "").strip()
        if on_hold_param != "":
            on_hold_bool = on_hold_param.lower() == "true"
            queryset = queryset.filter(on_hold=on_hold_bool)
        
        hold_date_start_param = request.query_params.get("hold_date_start", "").strip()
        hold_date_end_param = request.query_params.get("hold_date_end", "").strip()

        if hold_date_start_param != "":
            hold_date_start = parse_date(hold_date_start_param)
            if hold_date_start is None:
                return Response({"hold_date_start": "On hold start date must be a valid date."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(hold_date__gte=hold_date_start)

        if hold_date_end_param != "":
            hold_date_end = parse_date(hold_date_end_param)
            if hold_date_end is None:
                return Response({"hold_date_end": "On hold end date must be a valid date."}, status=status.HTTP_400_BAD_REQUEST)
            
            if hold_date_end > hold_date_start:
                return Response({"hold_date_end": "On hold end date must be greater than on hold start date."}, status=status.HTTP_400_BAD_REQUEST)
            queryset = queryset.filter(hold_date__lte=hold_date_end)

            
        # # 4. Ancestor Filtering
        # ancestor_ids_param = request.query_params.get("ancestor_ids", "").strip()
        # if ancestor_ids_param != "":
        #     try:
        #         # Convert "1,5" -> [1, 5]
        #         ancestor_ids = [int(x) for x in ancestor_ids_param.split(',') if x.strip().isdigit()]
        #         print("Ancestor IDs:", ancestor_ids)                
        #         if ancestor_ids:
        #             for ancestor_id in ancestor_ids:
        #                 # Use NodeClosure for efficient lookup
        #                 queryset = queryset.filter(
        #                     id__in=NodeClosure.objects.filter(
        #                         ancestor_id=ancestor_id,
        #                     ).values('descendant_id')
        #                 )
        #     except ValueError:
        #         pass # Ignore invalid format

        # 4. Ancestor Filtering
        ancestor_ids_param = request.query_params.get("ancestor_ids", "").strip()
        if ancestor_ids_param != "":
            try:
                # Convert "170,171" -> [170, 171]
                ancestor_ids = [int(x) for x in ancestor_ids_param.split(',') if x.strip().isdigit()]
                print("Ancestor IDs:", ancestor_ids)                
                
                if ancestor_ids:
                    # FIX: Use ancestor_id__in to apply an "OR" condition across all provided IDs
                    # This means: "Get descendants of 170 OR 171"
                    queryset = queryset.filter(
                        id__in=NodeClosure.objects.filter(
                            ancestor_id__in=ancestor_ids
                        ).values('descendant_id')
                    )
            except ValueError:
                pass
            
        # ==============================================
        # 5. Dynamic Attribute Filtering (The Fix)
        # ==============================================
        
        # A. Get Schema for this level
        level_obj = Level.objects.filter(id=level).first()
        defined_schema = level_obj.extra_fields_schema if level_obj else []
        
        import json
        if isinstance(defined_schema, str):
            try:
                defined_schema = json.loads(defined_schema)
            except:
                defined_schema = []
        if not isinstance(defined_schema, list):
            defined_schema = []
            
        # Map schema for easy lookup: {'isgenz': {'type': 'boolean', ...}}
        schema_map = {col['name']: col for col in defined_schema if isinstance(col, dict) and 'name' in col}

        # B. Loop through request parameters
        # We explicitly exclude standard params to avoid collisions
        standard_params = ['dimension', 'level', 'search', 'page', 'page_size', 'is_hidden', 'on_hold', 'ancestor_ids']
        
        for param, raw_value in request.query_params.items():
            if param in standard_params:
                # print("Skipping standard param:", param)
                continue

            # ==========================================
            # 1. Handle Range Filters
            # ==========================================
            processed_ranges = set()

            if param.endswith('_start') or param.endswith('_end'):
                base_param = param[:-6] if param.endswith('_start') else param[:-4]

                # prevent double-processing when both start & end are present
                if base_param in processed_ranges:
                    continue
                processed_ranges.add(base_param)

                if base_param in schema_map:
                    column_def = schema_map[base_param]
                    field_type = column_def.get('type', 'char')
                    default_val_raw = column_def.get('default_value')

                    if field_type in ['int', 'positive_int', 'float', 'date']:
                        start_param = f"{base_param}_start"
                        end_param = f"{base_param}_end"

                        start_raw = request.query_params.get(start_param, "").strip()
                        end_raw = request.query_params.get(end_param, "").strip()

                        try:
                            start_val, _ = cast_value_by_type(start_raw, field_type)  # ✅ from start_raw
                            end_val, _ = cast_value_by_type(end_raw, field_type)      # ✅ from end_raw

                            if start_val is None and end_val is None:
                                continue

                            if start_val is not None and end_val is not None and end_val < start_val:
                                return Response(
                                    {end_param: f"Value for '{end_param}' must be >= '{start_param}'."},
                                    status=status.HTTP_400_BAD_REQUEST
                                )

                            typed_default = None
                            print("Default Value:", default_val_raw)
                            if default_val_raw is not None:
                                typed_default, _ = cast_value_by_type(default_val_raw, field_type)

                            default_in_range = default_in_bounds(typed_default, start_val, end_val)

                            print("Default in range:", default_in_range)

                            range_kwargs = {}
                            if start_val is not None:
                                range_kwargs[f"attributes__{base_param}__gte"] = start_val
                            if end_val is not None:
                                range_kwargs[f"attributes__{base_param}__lte"] = end_val

                            range_q = Q(**range_kwargs)

                            # Updated Query logic to handle missing keys OR explicitly null values
                            if default_in_range:
                                queryset = queryset.filter(
                                    range_q | 
                                    ~Q(attributes__has_key=base_param) | 
                                    Q(**{f"attributes__{base_param}__isnull": True})
                                )
                            else:
                                queryset = queryset.filter(range_q)

                        except ValueError as e:
                            print(f"Skipping range filter for {base_param}: {e}")

                continue
            # # ==========================================
            # # 1. Handle Range Filters (_start)
            # # ==========================================
            # if param.endswith('_start'):
            #     # Extract base param name (e.g., 'area_start' -> 'area')
            #     base_param = param[:-6] 
            #     print("Base Param:", base_param)
                
            #     if base_param in schema_map:
            #         column_def = schema_map[base_param]
            #         field_type = column_def.get('type', 'char')
            #         default_val_raw = column_def.get('default_value') # <-- Get default value
                    
            #         # Ensure it's a numeric/date type
            #         if field_type in ['int', 'positive_int', 'float', 'date']:
            #             end_param = f"{base_param}_end"
            #             end_raw_value = request.query_params.get(end_param, "").strip()
                        
            #             # if not end_raw_value:
            #             #     return Response({"error": f"Query parameter '{end_param}' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
                        
            #             try:
            #                 start_val, _ = cast_value_by_type(raw_value, field_type)
            #                 end_val, _ = cast_value_by_type(end_raw_value, field_type)

            #                 print("Range Filter:", base_param, start_val, end_val)
                            
            #                 if start_val is not None and end_val is not None:
                                
            #                     # --- NEW: Default Value Logic for Ranges ---
            #                     typed_default = None
            #                     if default_val_raw is not None:
            #                         typed_default, _ = cast_value_by_type(default_val_raw, field_type)

            #                     # Check if the default value sits inside the requested bounds
            #                     default_in_range = False
            #                     if typed_default is not None:
            #                         if start_val <= typed_default <= end_val:
            #                             default_in_range = True
            #                     # -------------------------------------------

            #                     if default_in_range:
            #                         # If the default is within the range, include nodes that are missing the key entirely
            #                         queryset = queryset.filter(
            #                             Q(**{
            #                                 f"attributes__{base_param}__gte": start_val,
            #                                 f"attributes__{base_param}__lte": end_val
            #                             }) | 
            #                             ~Q(attributes__has_key=base_param)
            #                         )
            #                     else:
            #                         # Standard strict range search
            #                         queryset = queryset.filter(**{
            #                             f"attributes__{base_param}__gte": start_val,
            #                             f"attributes__{base_param}__lte": end_val
            #                         })
                                    
            #             except ValueError as e:
            #                 print(f"Skipping range filter for {base_param}: {e}")
                
            #     # Move to next parameter in the loop
            #     continue
                
            # ==========================================
            # 3. Handle Exact Match (Your Existing Logic)
            # ==========================================
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
                    descendant_id__in=target_ids,
                    ancestor__level__is_deleted=False
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
                            "code": str(c.ancestor.code).zfill(c.ancestor.level.code_digits if c.ancestor.level else 2),
                            "sort_order": c.ancestor.level.sort_order
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
                return Response({"level_id": "Level is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            nodes = Node.objects.filter(level_id=level_id)
        
        elif ids_param:
            try:
                ids = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
            except ValueError:
                return Response({"ids": "Invalid format"}, status=status.HTTP_400_BAD_REQUEST)

            if not ids:
                return Response({"ids": "No valid numeric ids provided"}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({"payload": "Payload is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if all_ids and all_ids in ["true", "True", True]:
            if not level_id:
                return Response({"level_id": "Level is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            nodes = Node.objects.filter(level_id=level_id)
        
        elif ids:
            if not isinstance(ids, list):
                return Response({"ids": "Invalid format"}, status=status.HTTP_400_BAD_REQUEST)
            
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
                    node_data['is_deleted'] = node.is_deleted
                    
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
                        print(input_serializer.errors)
                        errors.append({"id": node.id, "errors": input_serializer.errors})
                        raise ValidationError(input_serializer.errors)
        except ValidationError as e:
            print(e.messages)
            # return Response({"error": str(e.messages[0] if e.messages and isinstance(e.messages, list) else e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)
        
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

        target = serializer.validated_data.get('target_node')
        sources = serializer.validated_data.get('source_nodes')
        merge_date = serializer.validated_data.get('merge_date')

        # Counters for response
        moved_children_count = 0
        created_aliases_count = 0

        try:
            with transaction.atomic():
                
                # NEW: Log the merge on the TARGET node
                source_names = ", ".join([s.name for s in sources])
                target._change_reason = f"Merged with: {source_names}, Merge Date: {merge_date}"
                target.merge_date = merge_date
                target.save(update_fields=['updated_at', 'merge_date']) # Touch the node to create a history record

                # Reassign user node references
                reassign_user_node_references(sources, target)

                for source in sources:
                    # A. Create Alias
                    # We save the old name so users searching for "Old Country" find "New Country"
                    # ensure we don't create duplicate aliases
                    if not NodeAlias.objects.filter(node=target, name__iexact=source.name).exists():
                        NodeAlias.objects.create(
                            node=target, 
                            name=source.name, 
                            note=f"Merged from Node ID {source.id}"
                        )
                        created_aliases_count += 1
                    
                    # Also move existing aliases from Source to Target
                    existing_aliases = NodeAlias.objects.filter(node=source)
                    for alias in existing_aliases:
                        if not NodeAlias.objects.filter(node=target, name__iexact=alias.name).exists():
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
                    source._change_reason = f"Merged into '{target.name}' (ID: {target.id})"
                    NodeEventLog.objects.create(
                        event_type='MERGE',
                        source_node=source,
                        target_node=target,
                        effective_date=merge_date,
                        performed_by=request.user,
                        details=f"Merged into existing node {target.id}"
                    )
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
                    "error": "Failed to merge nodes (existing)",
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
        
        new_name = data.get('name')
        new_code = data.get('code')
        dimension = data.get('dimension') # Actual Dimension Object
        level = data.get('level')         # Actual Level Object
        parent = data.get('parent')   # Actual Node Object (or None)
        attributes = data.get('attributes', {})
        sources = data.get('source_nodes_objects') # The list of Node objects we stored in validate()
        merge_date = data.get('merge_date')

        try:
            with transaction.atomic():
                # 1. Create New Node
                new_node = Node.objects.create(
                    name=new_name,
                    code=new_code,
                    dimension=dimension,
                    level=level,
                    parent=parent,
                    attributes=attributes,
                    merge_date=merge_date
                )

                # NEW: Document the creation reason
                source_names = ", ".join([s.name for s in sources])
                update_change_reason(new_node, f"Created by merging: {source_names}, Merge Date: {merge_date}")

                # Reassign user node references
                reassign_user_node_references(sources, new_node)

                # 2. Merge Logic (Aliases & Children)
                summary = {"children_moved": 0, "aliases_created": 0}

                for source in sources:
                    # A. Create Alias (History)
                    if not NodeAlias.objects.filter(node=new_node, name__iexact=source.name).exists():
                        NodeAlias.objects.create(
                            node=new_node, 
                            name=source.name, 
                            note=f"Merged from deleted ID {source.id}"
                        )
                        summary['aliases_created'] += 1
                    
                    # B. Move existing aliases SAFELY (Replaced the .update() line)
                    existing_aliases = NodeAlias.objects.filter(node=source)
                    for alias in existing_aliases:
                        if not NodeAlias.objects.filter(node=new_node, name__iexact=alias.name).exists():
                            alias.node = new_node
                            alias.save()
                       

                    # Move Children
                    children = Node.objects.filter(parent=source)
                    for child in children:
                        child.parent = new_node
                        child.save() # Trigger Signal
                        summary['children_moved'] += 1

                    # Delete Source
                    # NEW: Document the deletion reason
                    source._change_reason = f"Merged into new '{new_node.name}' (ID: {new_node.id})"
                    NodeEventLog.objects.create(
                        event_type='MERGE',
                        source_node=source,
                        target_node=new_node,
                        effective_date=merge_date,
                        performed_by=request.user,
                        details=f"Merged into newly created node {new_node.id}"
                    )
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
        
        except ValidationError as e:
            return Response(e.message_dict, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    
    # @action(detail=False, methods=['get'], url_path='export-selected')
    # def export_selected(self, request):
    #     level_id = request.query_params.get('level_id')
    #     all_ids = request.query_params.get('all_ids', False)
    #     ids_param = request.query_params.get('ids')
        
    #     target_level = None
    #     nodes = []

    #     if all_ids and all_ids in ["true", "True", True]:
    #         if not level_id:
    #             return Response({"error": "level_id is required"}, status=400)
            
    #         try:
    #             target_level = Level.objects.get(id=level_id)
    #         except Level.DoesNotExist:
    #             return Response({"error": "Level not found"}, status=404)

    #         nodes = Node.objects.filter(level_id=level_id).select_related('parent', 'parent__parent', 'parent__parent__parent')

    #     # Case A: Export Selected Nodes by ID
    #     elif ids_param:
    #         try:
    #             ids = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
    #         except ValueError:
    #             return Response({"error": "Invalid ids format"}, status=400)
            
    #         if not ids:
    #             return Response({"error": "No ids provided"}, status=400)
                
    #         nodes = Node.objects.filter(id__in=ids).select_related('level', 'parent', 'parent__parent', 'parent__parent__parent')
            
    #         if not nodes.exists():
    #             return Response({"error": "No nodes found for the provided IDs"}, status=404)
            
    #         # Validation: Ensure all nodes are from the SAME level
    #         first_node = nodes.first()
    #         target_level = first_node.level
            
    #         if nodes.exclude(level=target_level).exists():
    #             return Response({
    #                 "error": "Export failed: All selected nodes must belong to the same Level to maintain consistent Excel columns."
    #             }, status=400)
        
    #     else:
    #         return Response({"error": "Either 'all_ids' or 'ids' parameter is required"}, status=400)

    #     # ---------------------------------------------------------
    #     # GENERATE EXCEL DATA (Same logic as before)
    #     # ---------------------------------------------------------
        
    #     dimension = target_level.dimension
        
    #     # 1. Identify Ancestor Levels (for columns like Glob | Continent | ...)
    #     ancestor_levels = Level.objects.filter(
    #         dimension=dimension,
    #         sort_order__lt=target_level.sort_order
    #     ).order_by('sort_order')
        
    #     ancestor_col_names = [lvl.name for lvl in ancestor_levels]

    #     data = []
    #     for node in nodes:
    #         row = {}
            
    #         # A. Fill Ancestor Columns (Walk up the parent chain)
    #         curr = node
    #         for ancestor_name in reversed(ancestor_col_names):
    #             if curr.parent:
    #                 row[ancestor_name] = curr.parent.name
    #                 curr = curr.parent
    #             else:
    #                 row[ancestor_name] = "" 

    #         # B. Fill Self Data
    #         row[target_level.name] = node.name
    #         row['Code'] = node.code
    #         row['Hidden'] = node.is_hidden
    #         row['On Hold'] = node.on_hold
    #         row['Hold Date'] = node.hold_date

    #         # C. Fill Custom Columns (Attributes)
    #         attributes = node.attributes or {}
    #         for key, value in attributes.items():
    #             row[key] = value
                
    #         data.append(row)

    #     if not data:
    #         return Response({"message": "No data to export"}, status=200)

    #     # 2. Build DataFrame
    #     df = pd.DataFrame(data)
        
    #     # 3. Order Columns
    #     custom_schema_keys = [col['name'] for col in (target_level.extra_fields_schema or [])]
    #     final_columns = ancestor_col_names + [target_level.name, 'Code', 'Hidden', 'On Hold'] + custom_schema_keys
        
    #     # Ensure all columns exist (fill missing with None)
    #     for col in final_columns:
    #         if col not in df.columns:
    #             df[col] = None

    #     df = df[final_columns]

    #     # 4. Return Response
    #     response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    #     filename = f"{target_level.name}_Export.xlsx"
    #     response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
    #     with pd.ExcelWriter(response, engine='openpyxl') as writer:
    #         df.to_excel(writer, index=False, sheet_name=target_level.name)
            
    #     return response

    @action(detail=False, methods=['get'], url_path='export-selected')
    def export_selected(self, request):
        level_id = request.query_params.get('level_id')
        all_ids = request.query_params.get('all_ids', False)
        ids_param = request.query_params.get('ids')

        target_level = None
        nodes_qs = None

        # -----------------------------
        # Pick nodes + target_level
        # -----------------------------
        if all_ids and all_ids in ["true", "True", True]:
            if not level_id:
                return Response({"error": "level_id is required"}, status=400)

            try:
                target_level = Level.objects.select_related("dimension", "parent").get(id=level_id)
            except Level.DoesNotExist:
                return Response({"error": "Level not found"}, status=404)

            # no fixed-depth select_related anymore
            nodes_qs = Node.objects.filter(level_id=level_id).select_related("level")

        elif ids_param:
            ids = [int(x) for x in ids_param.split(",") if x.strip().isdigit()]
            if not ids:
                return Response({"error": "No ids provided"}, status=400)

            nodes_qs = Node.objects.filter(id__in=ids).select_related("level")

            if not nodes_qs.exists():
                return Response({"error": "No nodes found for the provided IDs"}, status=404)

            first_node = nodes_qs.first()
            target_level = first_node.level

            if nodes_qs.exclude(level=target_level).exists():
                return Response(
                    {"error": "Export failed: All selected nodes must belong to the same Level to maintain consistent Excel columns."},
                    status=400
                )
        else:
            return Response({"error": "Either 'all_ids' or 'ids' parameter is required"}, status=400)

        # evaluate once (we’ll need ids multiple times)
        nodes = list(nodes_qs)
        if not nodes:
            return Response({"message": "No data to export"}, status=200)

        # -----------------------------
        # FIX: Exclude Hidden Branches (Descendants of Deleted Ancestors)
        # -----------------------------
        deleted_node_ids = Node.all_objects.filter(
            is_deleted=True, 
            dimension=target_level.dimension
        ).values_list('id', flat=True)
        
        hidden_branch_ids = NodeClosure.objects.filter(
            ancestor_id__in=deleted_node_ids
        ).values('descendant_id')

        nodes_qs = nodes_qs.exclude(id__in=hidden_branch_ids)
        # -----------------------------

        # evaluate once (we’ll need ids multiple times)
        nodes = list(nodes_qs)
        if not nodes:
            return Response({"message": "No data to export"}, status=200)

        # -----------------------------
        # Build ancestor columns (dynamic)
        # -----------------------------
        ancestor_levels = get_level_ancestors(target_level)  # Root -> Parent
        ancestor_col_names = [lvl.name for lvl in ancestor_levels]

        # -----------------------------
        # Fetch ancestors for all nodes using NodeClosure (dynamic depth)
        # We only need ancestors whose level is in ancestor_col_names
        # -----------------------------
        node_ids = [n.id for n in nodes]

        closures = (
            NodeClosure.objects
            .filter(descendant_id__in=node_ids, ancestor__level__in=ancestor_levels)
            .select_related("ancestor", "ancestor__level")
        )

        # node_ancestors[node_id][level_name] = ancestor_node
        node_ancestors = defaultdict(dict)
        for c in closures:
            node_ancestors[c.descendant_id][c.ancestor.level.name] = c.ancestor

        # -----------------------------
        # Build rows
        # -----------------------------
        custom_schema_keys = [col.get("name") for col in (target_level.extra_fields_schema or []) if col.get("name")]

        data = []
        for node in nodes:
            row = {}

            # --- NEW: Inject ID here ---
            row["ID"] = node.id

            # A) ancestor columns in correct order
            path = node_ancestors.get(node.id, {})
            for col in ancestor_col_names:
                row[col] = getattr(path.get(col), "name", "")  # empty if missing

            # B) self columns
            row[target_level.name] = node.name
            row["Code"] = node.code
            row["Hidden"] = node.is_hidden
            row["On Hold"] = node.on_hold
            row["Hold Date"] = node.hold_date  # keep it!

            # C) attributes
            attrs = node.attributes or {}
            for k, v in attrs.items():
                row[k] = v

            data.append(row)

        if not data:
            return Response({"message": "No data to export"}, status=200)

        df = pd.DataFrame(data)

        # -----------------------------
        # Column ordering (include Hold Date)
        # -----------------------------
        final_columns = ["ID"] + ancestor_col_names + [
            target_level.name, "Code", "Hidden", "On Hold", "Hold Date"
        ] + custom_schema_keys

        for col in final_columns:
            if col not in df.columns:
                df[col] = None

        df = df[final_columns]

        # -----------------------------
        # Export
        # -----------------------------
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"{target_level.name}_Export.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=target_level.name[:31])  # Excel sheet name limit

        return response                
    
    # @action(detail=False, methods=['post'], url_path='upload-excel', parser_classes=[MultiPartParser, FormParser])
    # def upload_excel(self, request):
    #     """
    #     Uploads Excel with dynamic full-hierarchy mapping.
        
    #     Payload:
    #     - file: (Binary Excel)
    #     - level_id: (ID of the level we are importing items INTO, e.g., Country Level ID)
    #     - mapping: JSON String. Example for Country Import:
    #         {
    #             "Glob": "Glob Column Name",       <-- Ancestor (Context)
    #             "Continent": "Continent Column",  <-- Parent (Required for lookup)
    #             "Country": "Country Name Column", <-- Target Item (Matches Target Level Name)
    #             "code": "Code",
    #             "is_hidden": "Hidden?",
    #             "attributes": { "area": "Area Column" }
    #         }
    #     """
    #     file_obj = request.FILES.get('file')
    #     level_id = request.data.get('level_id')
    #     mapping_str = request.data.get('mapping')

    #     print("File:", file_obj)
    #     print("Level ID:", level_id)
    #     print("Mapping:", mapping_str)

    #     if not file_obj:
    #         print("Missing file")
    #         return Response({"file": "File is required."}, status=status.HTTP_400_BAD_REQUEST)

    #     if not level_id:
    #         print("Missing level_id")
    #         return Response({"level_id": "Level is required."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     if not mapping_str:
    #         print("Missing mapping")
    #         return Response({"mapping": "Mapping is required."}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         mapping = json.loads(mapping_str)
    #     except json.JSONDecodeError:
    #         return Response({"mapping": "Invalid JSON format."}, status=status.HTTP_400_BAD_REQUEST)

    #     # 1. Fetch Target Level
    #     try:
    #         target_level = Level.objects.get(pk=level_id)
    #     except Level.DoesNotExist:
    #         return Response({"level_id": "Level not found."}, status=status.HTTP_404_NOT_FOUND)

    #     # 2. Read Excel
    #     try:
    #         file_name = file_obj.name.lower()
    #         if file_name.endswith(".csv"):
    #             df = pd.read_csv(file_obj, encoding="utf-8")
    #         elif file_name.endswith(".xlsx"):
    #             df = pd.read_excel(file_obj)
    #         elif file_name.endswith(".xls"):
    #             df = pd.read_excel(file_obj)
    #         else:
    #             return Response({"file": "Invalid file format."}, status=status.HTTP_400_BAD_REQUEST)
            
    #         # FIX: Cast to 'object' dtype so Pandas actually allows 'None' 
    #         # instead of reverting it back to 'NaN' for numeric columns.
    #         df = df.astype(object).where(pd.notnull(df), None) 
            
    #         df.columns = df.columns.str.strip() # Strip whitespace from headers
    #         print("Excel headers:", list(df.columns))
    #     except Exception as e:
    #         return Response({"file": f"Invalid Excel file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    #     # 3. Identify Key Columns from Mapping
    #     # We assume the mapping keys match the Level Names (e.g., "Country")
        
    #     # A. Target Name Column
    #     target_level_name_key = target_level.name # e.g., "Country"
        
    #     if target_level_name_key in mapping:
    #         col_target_name = mapping[target_level_name_key]
    #     else:
    #          # If the mapping doesn't contain the Level Name, we can't find the new item's name
    #          return Response({
    #              "mapping": f"Mapping missing key for '{target_level_name_key}'."
    #          }, status=status.HTTP_400_BAD_REQUEST)

    #     if col_target_name not in df.columns:
    #         return Response({"file": f"Excel file missing column '{col_target_name}'"}, status=status.HTTP_400_BAD_REQUEST)

    #     # B. Parent Resolution Columns
    #     # We resolve the immediate parent to attach the new node correctly.
    #     parent_level = target_level.parent
    #     col_parent_name = None
        
    #     if parent_level:
    #         parent_key = parent_level.name # e.g., "Continent"
    #         if parent_key in mapping:
    #             col_parent_name = mapping[parent_key]
    #             if col_parent_name not in df.columns:
    #                  return Response({"file": f"Excel file missing column '{col_parent_name}' (required for Parent {parent_key})"}, status=status.HTTP_400_BAD_REQUEST)
    #         else:
    #             return Response({"file": f"Mapping missing key for '{parent_key}'."}, status=status.HTTP_400_BAD_REQUEST)

    #     # 4. Prepare Schema for Attributes (Validation Setup)
    #     schema = target_level.extra_fields_schema or []
    #     valid_attr_keys = {col['name']: col['type'] for col in schema} # dict for fast lookup

    #     summary = {"requested":0, "created": 0, "updated": 0, "errors": []}

    #     if mapping.get("id") in ["", None]:
    #         return Response({"mapping": "Missing 'ID' key in mapping."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     if mapping.get(target_level.name) in ["", None]:
    #         return Response({"mapping": f"Missing '{target_level.name}' key in mapping."}, status=status.HTTP_400_BAD_REQUEST)

    #     if mapping.get("code") in ["", None]:
    #         return Response({"mapping": "Missing 'code' key in mapping."}, status=status.HTTP_400_BAD_REQUEST)
        
        
    #     if mapping.get("is_hidden") in ["", None]:
    #         return Response({"mapping": "Missing 'is_hidden' key in mapping."}, status=status.HTTP_400_BAD_REQUEST)
        
    #     if mapping.get("on_hold") not in ["", None]:
    #     #     return Response({"error": "Missing 'on_hold' key in mapping."}, status=status.HTTP_400_BAD_REQUEST)
    #     # else:
    #         if mapping.get("hold_date") in ["", None]:
    #             return Response({"mapping": "Missing 'hold_date' key in mapping."}, status=status.HTTP_400_BAD_REQUEST)
        

    #     # 5. Process Rows
    #     try:
    #         for index, row in df.iterrows():
    #             row_index = index + 2
    #             row_data = row.to_dict()

    #             # Get Node ID
    #             # print("Row Data:", row_data)
    #             id_val = row_data.get("ID")
    #             if id_val in ["", None]:
    #                 id_val = None
    #             else:    
    #                 if isinstance(id_val, str) and id_val.isdigit():
    #                     id_val = int(id_val)
    #                 elif isinstance(id_val, float):
    #                     id_val = int(id_val)
    #                 elif not isinstance(id_val, int):
    #                     id_val = None

    #             # --- Step 1: Get Target Name ---
    #             name_val = row_data.get(col_target_name)
    #             if not name_val:
    #                 continue # Skip empty 
                
    #             summary["requested"] += 1 # Track total number of item
                
    #             try:
    #                 with transaction.atomic():
    #                     # --- Step 2: Resolve Parent Node ---
    #                     # parent_node = None
    #                     # if parent_level:
    #                     #     parent_name_val = row_data.get(col_parent_name)
                            
    #                     #     if not parent_name_val:
    #                     #         summary["errors"].append(f"Row {row_index}: Missing parent '{parent_level.name}'.")
    #                     #         continue
    #                     #     print("Parent Name:", parent_name_val)
    #                     #     # Find the parent node
    #                     #     # We search for a Node with the Parent's Name + Parent's Level + Same Dimension
    #                     #     parent_node = Node.objects.filter(
    #                     #         name=parent_name_val,
    #                     #         level=parent_level,
    #                     #         dimension=target_level.dimension
    #                     #     ).first()

    #                     #     if not parent_node:
    #                     #         # summary["errors"].append(f"Row {row_index}: Parent '{parent_level.name}' named '{parent_name_val}' not found.")
    #                     #         raise Exception(f"Parent '{parent_level.name}' named '{parent_name_val}' not found. Cannot create row.")


    #                     # --- Step 2: Resolve Parent Node (Full Hierarchy Lookup) ---
    #                     parent_node = None
    #                     if parent_level:
    #                         parent_name_val = row_data.get(col_parent_name)
                            
    #                         if not parent_name_val:
    #                             error_data = {
    #                                 "message": f"Row {row_index}: Missing parent '{parent_level.name}'.",
    #                                 "color": "red"
    #                             }
    #                             summary["errors"].append(error_data)
    #                             continue
                            
    #                         # 1. Start building our dynamic query dictionary
    #                         lookup_kwargs = {
    #                             'dimension': target_level.dimension
    #                         }
                            
    #                         # 2. Traverse UP the level hierarchy
    #                         current_ancestor_level = parent_level
    #                         prefix = "" # Starts as "", then becomes "parent__", then "parent__parent__", etc.
    #                         missing_ancestor_data = False
                            
    #                         while current_ancestor_level:
    #                             level_name = current_ancestor_level.name
                                
    #                             # If this ancestor level is mapped in our JSON (e.g., "Country")
    #                             if level_name in mapping:
    #                                 col_name = mapping[level_name]
    #                                 ancestor_val = row_data.get(col_name)
                                    
    #                                 if not ancestor_val:
    #                                     error_data = {
    #                                         "message": f"Row {row_index}: Missing value for '{level_name}' in column '{col_name}'.",
    #                                         "color": "red"
    #                                     }
    #                                     summary["errors"].append(error_data)
    #                                     missing_ancestor_data = True
    #                                     break
                                    
    #                                 # Add to our query: e.g., parent__name="China", parent__level=<Country Level>
    #                                 lookup_kwargs[f"{prefix}name"] = ancestor_val
    #                                 lookup_kwargs[f"{prefix}level"] = current_ancestor_level
                                
    #                             # Move up to the next parent level for the next loop iteration
    #                             current_ancestor_level = current_ancestor_level.parent
    #                             prefix += "parent__"

    #                         if missing_ancestor_data:
    #                             raise Exception(f"Row {row_index}: Missing required hierarchy data.")

    #                         # 3. Execute the exact hierarchy query
    #                         # E.g., Node.objects.filter(name="Gujrat", parent__name="China", parent__parent__name="Asia")
    #                         # 3. Execute the exact hierarchy query
    #                         parent_node = Node.objects.filter(**lookup_kwargs).first()

    #                         if not parent_node:
    #                             # UX UPGRADE: Build a visual path string to show the user exactly what failed
    #                             attempted_path = []
    #                             p_prefix = ""
    #                             c_level = parent_level
                                
    #                             while c_level:
    #                                 val = lookup_kwargs.get(f"{p_prefix}name")
    #                                 if val:
    #                                     attempted_path.insert(0, str(val))
    #                                 c_level = c_level.parent
    #                                 p_prefix += "parent__"
                                
    #                             path_str = " -> ".join(attempted_path)
                                
    #                             raise Exception(f"Hierarchy '{path_str}' not found in database. Please check your Excel file for typos!")
                                
    #                     # --- NEW Step 3: Find Existing Node (Determine Create vs Update) ---
    #                     node = None
    #                     # print("Id:", id_val)
    #                     if id_val is not None:
    #                         node = Node.objects.filter(id=id_val, level=target_level).first()
    #                         # print("Node in condition: ", node)
    #                         if not node:
    #                             # raise Exception(f"Row {row_index}: Provided ID '{id_val}' does not exist.")
    #                             # print(f"Row {row_index}: Provided ID '{id_val}' does not exist, so a new row will be created.")
    #                             error_data = {
    #                                 "message": f"Row {row_index}: Provided ID '{id_val}' does not exist so a new row will be created.",
    #                                 "color": "blue"
    #                             }
    #                             summary["errors"].append(f"Row {row_index}: Provided ID '{id_val}' does not exist so a new row will be created.")
                            
    #                     # print("Node: ", node)

    #                     # --- Step 3: Extract Standard Fields ---
    #                     # Helper to safely get value based on mapping key
    #                     def get_mapped_val(key, default=None):
    #                         if key in mapping and mapping[key] in row_data:
    #                             return row_data[mapping[key]]
    #                         return default

    #                     code_val = get_mapped_val('code')
    #                     # print(f"Code: {code_val}, Type: {type(code_val)}")

    #                     if code_val in ["", None]:
    #                         raise Exception(f"Row {row_index}: Missing Code.")
                        
    #                     if type(code_val) not in [str, int]:
    #                         raise Exception(f"Row {row_index}: Code '{code_val}' is not numeric.")

                        
    #                     if isinstance(code_val, str) and code_val.isdigit():
    #                         code_val = int(code_val)

    #                     if len(str(code_val)) > target_level.code_digits:
    #                         raise Exception(f"Row {row_index}: Code '{code_val}' too long for level '{target_level.name}'.")
                        
    #                     # Validate Code
    #                     if code_val <= 0:
    #                         raise Exception(f"Row {row_index}: Code '{code_val}' is not positive.")
                        
    #                     collision_qs = Node.objects.filter(
    #                         level=target_level,
    #                         code=code_val,
    #                         parent=parent_node
    #                     ).exclude(name=name_val) # Exclude self if this is an update to existing node

    #                     # Exclude self based on ID if updating, otherwise exclude by name
    #                     if node:
    #                         collision_qs = collision_qs.exclude(id=node.id)
                        
    #                     if collision_qs.exists():
    #                         raise Exception(f"Row {row_index}: Code '{code_val}' already used by '{collision_qs.first().name}'.")
                        

    #                     is_hidden_raw = get_mapped_val('is_hidden', None)
    #                     if is_hidden_raw is None:
    #                         is_hidden = False
    #                     else:
    #                         is_hidden = check_bool_value(is_hidden_raw)
    #                         if is_hidden is None:
    #                             raise Exception(f"Row {row_index}: Invalid value for is_hidden: {is_hidden_raw}")
                            
    #                     on_hold_raw = get_mapped_val('on_hold', None)
    #                     if on_hold_raw is None:
    #                         on_hold = False
    #                     else:
    #                         on_hold = check_bool_value(on_hold_raw)
    #                         if on_hold is None:
    #                             raise Exception(f"Row {row_index}: Invalid value for on_hold: {on_hold_raw}")
                            

                    
    #                     # Date parsing
    #                     hold_date_raw = get_mapped_val('hold_date')
    #                     hold_date_val = None
    #                     if hold_date_raw:
    #                         try:
    #                             dt = pd.to_datetime(hold_date_raw, dayfirst=True)
    #                             hold_date_val = dt.date()
    #                         except:
    #                             summary["errors"].append(f"Row {row_index}: Invalid date format for Hold Date.")
    #                             continue

    #                     # --- Step 4: Extract Attributes ---
    #                     node_attributes = {}
    #                     if 'attributes' in mapping and isinstance(mapping['attributes'], dict):
    #                         for sys_attr, excel_header in mapping['attributes'].items():
    #                             # Only process if this attribute is defined in the Level Schema
    #                             if sys_attr in valid_attr_keys:
    #                                 val = row_data.get(excel_header)
    #                                 if val is not None:
    #                                     node_attributes[sys_attr] = val


    #                     # --- Step 6: Update or Create ---
    #                     # node, created = Node.objects.update_or_create(
    #                     #     name=name_val,
    #                     #     level=target_level,
    #                     #     parent=parent_node,
    #                     #     defaults={
    #                     #         "code": code_val,
    #                     #         "is_hidden": is_hidden,
    #                     #         "on_hold": on_hold,
    #                     #         "hold_date": hold_date_val,
    #                     #         "attributes": node_attributes,
    #                     #         "dimension": target_level.dimension
    #                     #     }
    #                     # )

    #                     # We avoid update_or_create so we can validate BEFORE hitting the DB
    #                     # node = Node.objects.filter(
    #                     #     name=name_val,
    #                     #     level=target_level,
    #                     #     parent=parent_node,
    #                     #     dimension=target_level.dimension
    #                     # ).first()

    #                     # if id_val is not None:
    #                     #     node = Node.objects.filter(id=id_val).first()
    #                     # else:
    #                     #     node = None

    #                     created = False
    #                     if not node:
    #                         node = Node(
    #                             name=name_val,
    #                             code=code_val,
    #                             is_hidden=is_hidden,
    #                             on_hold=on_hold,
    #                             hold_date=hold_date_val,
    #                             level=target_level,
    #                             parent=parent_node,
    #                             dimension=target_level.dimension,
    #                             attributes=node_attributes
    #                         )
    #                         created = True
    #                     else:
    #                         # FIX 2: Apply the updates to the existing node!
    #                         node.name = name_val
    #                         node.code = code_val
    #                         node.is_hidden = is_hidden
    #                         node.on_hold = on_hold
    #                         node.hold_date = hold_date_val
    #                         node.parent = parent_node
    #                         node.attributes = node_attributes

    #                     # --- Step 7: Validate (Model Logic) ---
    #                     try:
    #                         node.validate_attributes() 
    #                         node.save()

    #                     except ValidationError as e:
    #                         # Since we are in atomic transaction, this exception will rollback the batch
    #                         # If you prefer to skip rows instead of rollback, change this to `continue` 
    #                         # and append to summary["errors"]
    #                         # print("e.messages", e)
    #                         clean_error_text = " ".join(e.messages)
                            
    #                         # Raise the exception with just the clean text
    #                         # raise Exception(f"Row {row_index}: {clean_error_text}")
    #                         return Response({"error": f"Row {row_index}: {clean_error_text}"}, status=status.HTTP_400_BAD_REQUEST)

    #                     # Track this in your history API!
    #                     reason = "Created via Excel Import" if created else "Updated via Excel Import"
    #                     update_change_reason(node, reason)

                
    #                     if created: 
    #                         summary["created"] += 1
    #                     else: 
    #                         summary["updated"] += 1

    #             except IntegrityError as e:
    #                 error_data = {
    #                     "message": f"Row {row_index}: This data already exists.",
    #                     "color": "red"
    #                 }
    #                 summary["errors"].append(error_data)
    #             except ValidationError as e:
    #                 clean_error_text = " ".join(e.messages)
    #                 error_data = {
    #                     "message": f"Row {row_index}: {clean_error_text}",
    #                     "color": "red"
    #                 }
    #                 summary["errors"].append(error_data)
    #             except Exception as e:
    #                 error_data = {
    #                     "message": f"Row {row_index}: {str(e)}",
    #                     "color": "red"
    #                 }
    #                 summary["errors"].append(error_data)

    #     except Exception as e:
    #         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #     if summary["errors"]:
    #         return Response({"message": "Completed with errors", "summary": summary}, status=status.HTTP_200_OK)

    #     return Response({"message": "Success", "summary": summary}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='upload-excel', parser_classes=[MultiPartParser, FormParser])
    def upload_excel(self, request):
        file_obj = request.FILES.get('file')
        level_id = request.data.get('level_id')
        mapping_str = request.data.get('mapping')

        # 1. Basic Validation
        if not file_obj:
            return Response({"file": "File is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not level_id:
            return Response({"level_id": "Level is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not mapping_str:
            return Response({"mapping": "Mapping is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            mapping_dict = json.loads(mapping_str)
        except json.JSONDecodeError:
            return Response({"mapping": "Invalid JSON format."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the file temporarily
        # Generate a unique filename so concurrent uploads don't overwrite each other
        file_extension = file_obj.name.split('.')[-1]
        temp_file_name = f"tmp_imports/{uuid.uuid4().hex}.{file_extension}"
        
        saved_path = default_storage.save(temp_file_name, ContentFile(file_obj.read()))

        from configuration.tasks import task_validate_excel
        
        # Trigger the validation Celery Task
        task = task_validate_excel.delay(
            file_path=saved_path, 
            level_id=level_id, 
            mapping_dict=mapping_dict,
            user_id=request.user.id
        )

        return Response({
            "message": "Validation started successfully. This will process in the background.",
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'], url_path='commit-excel-import')
    def commit_excel_import(self, request):
        import_session_id = request.data.get('import_session_id')
        if not import_session_id:
            return Response({"error": "import_session_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        from configuration.tasks import task_commit_excel
        
        # Trigger the commit Celery Task
        task = task_commit_excel.delay(
            import_session_id=import_session_id,
            user_id=request.user.id
        )
        
        return Response({
            "message": "Commit started successfully. This will process in the background.",
            "task_id": task.id
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], url_path='download-template')
    def download_template(self, request):
        level_id = request.query_params.get('level_id')
        if not level_id:
            return Response({"error": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_level = Level.objects.get(id=level_id)
            
            # Gather ancestor levels
            from configuration.utils import get_level_ancestors
            ancestors = get_level_ancestors(target_level)
            
            headers = ["ID"]
            for ancestor in ancestors:
                headers.append(ancestor.name)
            
            headers.append(target_level.name)
            headers.extend(["Code", "Is Hidden", "On Hold", "Hold Date"])
            
            if target_level.extra_fields_schema:
                for col in target_level.extra_fields_schema:
                    headers.append(col['name'])
                    
            import pandas as pd
            from django.http import HttpResponse
            import io
            
            df = pd.DataFrame(columns=headers)
            
            # Add a hint row
            hint_row = ["(Leave blank for new)"]
            for ancestor in ancestors:
                hint_row.append("Exact Parent Name")
            hint_row.append("Node Name")
            hint_row.extend(["Positive Number", "TRUE/FALSE", "TRUE/FALSE", "YYYY-MM-DD"])
            
            if target_level.extra_fields_schema:
                for col in target_level.extra_fields_schema:
                    hint_row.append(f"{col['type']}")
                    
            df.loc[0] = hint_row
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=target_level.name)
                
            output.seek(0)
            response = HttpResponse(
                output.read(), 
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename={target_level.name}_template.xlsx'
            return response
            
        except Level.DoesNotExist:
            return Response({"error": "Level not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["POST"], url_path="split")
    def split_node(self, request, pk):
        # Lock the source node
        source_node = Node.all_objects.select_for_update().filter(id=pk).first()
        if not source_node:
            return Response({"error": "Node not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if source_node.is_deleted:
            return Response({"error": "Cannot split a deleted node."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = SplitNodeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        splits = serializer.validated_data.get('splits')
        split_date = serializer.validated_data.get('split_date')

        source_node_childrens = list(Node.objects.filter(parent=source_node).values_list('id', flat=True))
        source_children_set = set(source_node_childrens)

        requested_children_set = set()
        for node in splits:
            requested_children_set |= set(node.get("children_ids", []))

        invalid = sorted(list(requested_children_set - source_children_set))
        if invalid:
            return Response(
                {"error": "Some children_ids are not children of the source node.", "invalid_child_ids": invalid},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Anything not mentioned
        unassigned_childrens = sorted(list(source_children_set - requested_children_set))
        if unassigned_childrens:
            return Response(
                {"error": "Some children_ids are not mentioned in the splits.", "unassigned_child_ids": unassigned_childrens},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            created_nodes = []

            # 1. Create New Nodes
            for split in splits:
                
                # Use .copy() to avoid mutating the original validated data
                node_data = split.get('node', {}).copy()

                # Safely convert ANY loaded Django model back to its raw primary key
                for key, value in node_data.items():
                    if isinstance(value, models.Model):
                        node_data[key] = value.pk

                # node_data = split.get('node', {})
                # parent_id = node_data.get('parent_id')

                # Ensure the new node inherits the exact parent/level/dimension of the source
                # node_data['parent'] = source_node.parent_id
                # node_data['level'] = parent_id if parent_id else source_node.level_id
                # node_data['dimension'] = source_node.dimension_id

                existing_node_qs = Node.objects.filter(
                    dimension=node_data.get('dimension'),
                    level=node_data.get('level'),
                    name__iexact=node_data.get('name'),
                    code=node_data.get('code'),
                )
                
                source_node_level_parent = source_node.level.parent
                if source_node_level_parent is not None:
                    existing_node_obj = existing_node_qs.filter(level__parent=source_node_level_parent).first()
                else:
                    existing_node_obj = existing_node_qs.first()
                
                print("existing_node_obj", existing_node_obj)
                print("source_node:", source_node)

                if existing_node_obj:
                    node_serializer = NodeSerializer(existing_node_obj, data=node_data)
                else:
                    node_serializer = NodeSerializer(data=node_data)

                node_serializer.is_valid(raise_exception=True)
                node_serializer.validated_data['split_date'] = split_date
                new_node = node_serializer.save()

                # NEW: Log why this node was created
                if not existing_node_obj:
                    update_change_reason(new_node, f"Created by splitting '{source_node.name}', Split Date: {split_date}")

                created_nodes.append(new_node)

            # 2. Assign Aliases
            source_node_alias_lst = list(NodeAlias.objects.filter(node=source_node).values_list('name', flat=True))
            source_node_alias_lst.append(source_node.name)

            for new_node in created_nodes:
                for alias_name in set(source_node_alias_lst):
                    if alias_name.lower() == new_node.name.lower(): continue
                    if not NodeAlias.objects.filter(node=new_node, name__iexact=alias_name).exists():
                        NodeAlias.objects.create(
                            node=new_node, 
                            name=alias_name
                        )
            
            # 3. Assign Children & Trigger NodeClosure Logic
            for index, split in enumerate(splits):
                new_parent_node = created_nodes[index]
                child_ids = split.get("children_ids", [])
                
                if child_ids:
                    # Fetch the children that belong to this specific split
                    children_to_move = Node.objects.filter(id__in=child_ids, parent=source_node)
                    
                    for child in children_to_move:
                        child.parent = new_parent_node
                        # CRITICAL: Calling .save() triggers `manage_node_closure` in signals.py
                        # This automatically deletes old paths and creates the new hierarchy paths!
                        child.save() 

            # 4. Soft delete the original source node

            # Reassign user node references to the first created node as default target
            if created_nodes:
                reassign_user_node_references([source_node], created_nodes[0])

            # Check if the source_node was updated/reused in any of the splits
            source_node_reused = any(n.id == source_node.id for n in created_nodes)

            # NEW: Log why this node is being deleted
            new_node_names = ", ".join([n.name for n in created_nodes])
            source_node._change_reason = f"Split into {len(created_nodes)} nodes: {new_node_names}"

            for target in created_nodes:
                NodeEventLog.objects.create(
                    event_type='SPLIT',
                    source_node=source_node,
                    target_node=target,
                    effective_date=split_date,
                    performed_by=request.user,
                    details=f"Split from original node {source_node.id}"
                )

            if not source_node_reused:
                # It was not reused, so we safely delete it
                source_node.soft_delete(user=request.user)
            else:
                # It WAS reused! We don't delete it, but we force a save 
                # to ensure the `_change_reason` we just set gets logged in history.
                source_node.save(update_fields=['updated_at'])

        return Response({
            "message": f"Successfully split {source_node.name}",
            "new_nodes": [{"id": n.id, "name": n.name} for n in created_nodes]
        }, status=status.HTTP_201_CREATED)


    # @action(detail=False, methods=['POST'], url_path='multiple-delete')
    # def multiple_delete(self, request):
    #     print("request.data", request.data)
    #     level_id = request.data.get('level_id')
    #     all_ids = request.data.get('all_ids', False)
    #     ids = request.data.get('ids')

    #     # -----------------------------
    #     # Pick nodes + target_level
    #     # -----------------------------
    #     if all_ids and all_ids in ["true", "True", True]:
    #         if not level_id:
    #             return Response({"level_id": "level_id is required"}, status=400)

    #         try:
    #             target_level = Level.objects.select_related("dimension", "parent").get(id=level_id)
    #         except Level.DoesNotExist:
    #             return Response({"level_id": "Level not found"}, status=404)

    #         # no fixed-depth select_related anymore
    #         node_qs = Node.objects.filter(level=target_level)

    #         if not node_qs.exists():
    #             return Response({"level_id": "No nodes found."}, status=404)
    #         # node_qs.update(is_deleted=True, deleted_at=timezone.now(), deleted_by=request.user)

    #     elif ids:
    #         if not ids:
    #             return Response({"ids": "No ids provided"}, status=400)
            
    #         if not isinstance(ids, list):
    #             return Response({"ids": "ids must be a list"}, status=400)

    #         node_qs = Node.objects.filter(id__in=ids)

    #         if not node_qs.exists():
    #             return Response({"ids": "No nodes found."}, status=404)

    #         # nodes_qs.update(is_deleted=True, deleted_at=timezone.now(), deleted_by=request.user)

    #     # Soft delete all provided nodes
    #     if node_qs:
    #         for node in node_qs:
    #             node.soft_delete(user=request.user)

    #     return Response({"message": "Nodes deleted successfully"}, status=200)

    @action(detail=False, methods=['POST'], url_path='multiple-delete')
    def multiple_delete(self, request):
        level_id = request.data.get('level_id')
        all_ids = request.data.get('all_ids', False)
        ids = request.data.get('ids')

        # -----------------------------
        # 1. Pick nodes to delete
        # -----------------------------
        if all_ids and all_ids in ["true", "True", True]:
            if not level_id:
                return Response({"level_id": "level_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                target_level = Level.objects.get(id=level_id)
                node_qs = Node.objects.filter(level=target_level, is_deleted=False)
            except Level.DoesNotExist:
                return Response({"level_id": "Level not found"}, status=status.HTTP_404_NOT_FOUND)
        elif ids:
            if not ids or not isinstance(ids, list):
                return Response({"ids": "ids must be a valid list"}, status=status.HTTP_400_BAD_REQUEST)
            node_qs = Node.objects.filter(id__in=ids, is_deleted=False)
        else:
            return Response({"error": "Either 'all_ids' or 'ids' parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not node_qs.exists():
            return Response({"error": "No active rows found to delete."}, status=status.HTTP_404_NOT_FOUND)

        # -------------------------------------------------------------
        # 2. Dependency Check (Node by Node)
        # -------------------------------------------------------------
        try:
            with transaction.atomic():
                # Get a flat list of all IDs we are deleting
                node_ids = list(node_qs.values_list('id', flat=True))
                node_errors = []
                dependent_nodes = []
                for node in node_qs:
                    # 1. Check for Dependencies
                    # IMPORTANT: .exclude(id__in=node_ids) prevents blocking if the child is ALSO being deleted right now!
                    child_nodes_count = Node.objects.filter(parent=node, is_deleted=False).exclude(id__in=node_ids).count()

                    if child_nodes_count > 0:
                        dependent_nodes.append(node.id)
                        node_errors.append(f"'{node.name}' is referenced by {child_nodes_count} child row(s).")

                # 2. Block Deletion if dependencies exist ANYWHERE in the selection
                if node_errors:
                    combined_error_msg = "Cannot delete the selected items, Please delete or reassign them first."
                    
                    raise DRFValidationError({
                        "error": combined_error_msg,
                        "node_ids": dependent_nodes,
                        "details": node_errors, # Send array for the frontend to show a clean bulleted list
                        "requires_resolution": True
                    })

                # -------------------------------------------------------------
                # 3. Execute Soft Deletion
                # -------------------------------------------------------------
                for node in node_qs:
                    node.soft_delete(user=request.user)
                    # Optional: Log the deletion reason in history
                    update_change_reason(node, "Deleted via bulk multiple-delete API")

        except DRFValidationError as e:
            # Safely pass our custom validation errors straight to the frontend
            raise e
            
        except Exception as e:
            # Log unexpected system crashes and return a generic error
            level_logger.exception(f"Failed to bulk delete nodes: {e}")
            raise DRFValidationError({"error": "Failed to delete. Please try again."})

        return Response({"message": "Items deleted successfully"}, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from collections import defaultdict

class NodeSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]
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
            return Response({"dimension": "Dimension is required"}, status=400)
        
        try:
            dimension_obj = Dimension.objects.get(id=dimension_id)
        except Dimension.DoesNotExist:
            return Response({"dimension": "Dimension does not exist"}, status=400)
        
        print(request.data)
        
        search_data = request.data.copy()
        target_level_name = search_data.pop('search_key', "").strip() # e.g., "Country"

        if not target_level_name:
            return Response({"search_key": "search_key is required."}, status=400)
        
        target_level_obj = Level.objects.filter(name=target_level_name, dimension=dimension_obj).first()
        print("Target Level:", target_level_obj)
        if not target_level_obj:
            return Response({"error": f"'{target_level_name}' does not exist"}, status=400)
        

        # 2. Get the Search Value (e.g., "In" for Country)
        raw_value = search_data.get(target_level_name)
        search_value = str(raw_value).strip() if raw_value else ""

        # 1. Get raw IDs of explicitly deleted nodes
        deleted_node_ids = Node.all_objects.filter(is_deleted=True, dimension=dimension_obj).values_list('id', flat=True)
        
        # 2. Get all descendants (children, grandchildren, etc.) of those deleted nodes
        hidden_branch_ids = NodeClosure.objects.filter(
            ancestor_id__in=deleted_node_ids
        ).values('descendant_id')

        # 3. Step A: Find CANDIDATE Nodes first
        # We search for ANY node at Level="Country" that contains "In"
        nodes = Node.objects.filter(
            dimension_id=dimension_obj,
            # level__name__iexact=target_level_name,
            # level__name__iexact=target_level_obj.name,
            level=target_level_obj,
            is_hidden=False,
            on_hold=False
        ).exclude(
            id__in=hidden_branch_ids
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        existing_col_name = request.query_params.get('col_name', "").strip()
        level = get_object_or_404(Level, pk=pk)
        if existing_col_name == "":
            return Response(level.extra_fields_schema or [], status=status.HTTP_200_OK)
        
        for extra_col in level.extra_fields_schema or []:
            if extra_col['name'] == existing_col_name:
                return Response(extra_col, status=status.HTTP_200_OK)
        
        return Response({"col_name": "Column not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, pk):
        level = get_object_or_404(Level, pk=pk)
        input_serializer = ColumnDefinitionSerializer(data=request.data, context={"level_obj": level})
        input_serializer.is_valid(raise_exception=True)
        
        new_col = input_serializer.validated_data
        print("New col:", new_col['name'])
        print("Level:", level.name)
        if new_col["name"] in [level.name.lower(), "name", "code", "is_hidden", "on_hold", "hold_date", "created_at", "updated_at", "id", "level", "parent"]:
            return Response({"error": f"Column name '{new_col['name']}' already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        current_schema = level.extra_fields_schema or []
        
        default_value = new_col.get("default_value")
        if default_value:
            pass
        
        if any([col['name'] == new_col['name'] for col in current_schema]):
            return Response({"error": f"Column with name '{new_col['name']}' already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        current_schema.append(new_col)
        level.extra_fields_schema = current_schema
        level.save()
        
        return Response(new_col, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        level = get_object_or_404(Level, pk=pk)
        
        current_name = request.query_params.get('col_name', "").strip()
        if current_name == "":
            return Response(
                {"col_name": "Column name is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 1. Validate Input
        # Note: Ensure you are using the Update Serializer we defined earlier
        input_serializer = CustomDefinationUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data
        
        new_name = validated_data.get('new_name')
        if new_name in [level.name.lower(), "name", "code", "is_hidden", "on_hold", "hold_date", "created_at", "updated_at", "id", "level", "parent"]:
            return Response({"error": f"Column name '{new_name}' already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        
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
                {"error": f"Column '{current_name}' not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 3. Handle Renaming (Only if new_name is provided AND different)
        final_name = current_name
        if new_name and new_name != current_name:
            # Check for duplicates in OTHER columns
            if any(col['name'] == new_name for col in current_schema):
                return Response(
                    {"error": f"Column with name '{new_name}' already exists"}, 
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
            
        if new_required:
            node_count = Node.objects.filter(level=level).count()
            if node_count > 0 and new_default_value in [None, ""]:
                return Response(
                    {"default_value": "You cannot mark a column as 'Required' without a 'Default Value' because data already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 5. Validate Consistency
        try:
            options = validated_data.get('options', existing_col.get('options'))
            
            # Check if any removed dropdown options are currently in use
            if existing_type == 'dropdown' and 'options' in validated_data:
                existing_options = set(existing_col.get('options', []))
                new_options = set(validated_data['options'])
                removed_options = existing_options - new_options
                
                if removed_options:
                    query = Q()
                    for opt in removed_options:
                        query |= Q(**{f"attributes__{current_name}": opt})
                    
                    if Node.objects.filter(level=level).filter(query).exists():
                        return Response(
                            {"options": f"Cannot remove options {list(removed_options)} because they are currently used by one or more nodes."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            new_default_value = validate_value_type(new_default_value, existing_type, new_max_length, options=options)
            print(f"New Default Value: {new_default_value}, Type: {type(new_default_value)}")
        except (ValidationError, ValueError, DRFValidationError) as e: 
            # Unwrap the error message safely
            if hasattr(e, 'detail'):
                msg = e.detail[0] if isinstance(e.detail, list) else str(e.detail)
            elif hasattr(e, 'messages'):
                msg = e.messages[0] if isinstance(e.messages, list) else str(e.messages)
            else:
                msg = str(e)
            return Response({"default_value": msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # 6. Apply Updates
        existing_col['name'] = final_name
        existing_col['default_value'] = new_default_value
        existing_col['max_length'] = new_max_length
        existing_col['required'] = new_required
        if existing_type == 'dropdown':
            existing_col['options'] = options
        
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
                    {"col_name": "Column name is required"},
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
                    {"error": f"Column '{col_name}' not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            del current_schema[target_index]
            level.extra_fields_schema = current_schema
            level.save()
        except Exception as e:
            return Response({"Error": "Error on deleting column"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class NodeHistoryDiffView(BaseHistoryDiffAPIViewMixin):
    model_class = Node


class LevelHistoryDiffView(BaseHistoryDiffAPIViewMixin):
    model_class = Level


class NodeRelationshipViewset(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NodeRelationshipInputSerializer
    queryset = NodeRelationship.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return NodeRelationshipInputSerializer
        return NodeRelationshipOutputSerializer
    
    def list(self, request, *args, **kwargs):
        node_params = request.query_params.get('node', "").strip()
        territory_params = request.query_params.get('territory', "").strip()
        controller_params = request.query_params.get('controller', "").strip()

        if not node_params:
            return Response({"error": "Node is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        query_set = NodeRelationship.objects.filter(
            Q(territory=node_params) | Q(controller=node_params)
        )

        if territory_params:
            query_set = query_set.filter(territory=territory_params)
        if controller_params:
            query_set = query_set.filter(controller=controller_params)

        serializer = self.get_serializer(query_set, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def perform_destroy(self, instance):
        print("instance", instance)
        """
        Intercepts the DELETE request to perform a soft delete 
        instead of a hard database deletion.
        """
        try:
            # 1. Update the SoftDeleteMixin fields
            instance.soft_delete(user=self.request.user)
        except Exception as e:
            raise DRFValidationError({"error": str(e)})


    @action(detail=False, methods=['post'], url_path='bulk-manage')
    def bulk_manage(self, request):
        """
        Handles Create, Update, and Delete in a single request.
        Expects a JSON list of objects from the frontend grid.
        """
        payload = request.data
        
        if not isinstance(payload, list):
            return Response({"error": "Payload must be an array of relationship objects."}, status=status.HTTP_400_BAD_REQUEST)

        summary = {"created": 0, "updated": 0, "deleted": 0}
        errors = []

        try:
            with transaction.atomic():
                for index, item_data in enumerate(payload):
                    item_id = item_data.get('id')
                    
                    # Look for your exact JSON key: "delete"
                    is_deleted_flag = item_data.get('delete', False)

                    # --- SCENARIO 1: DELETE (Has ID and delete is True) ---
                    if item_id and is_deleted_flag:
                        try:
                            rel = NodeRelationship.objects.get(id=item_id)
                            rel.soft_delete(user=request.user)
                            update_change_reason(rel, "Deleted via bulk manage")
                            summary["deleted"] += 1
                        except NodeRelationship.DoesNotExist:
                            errors.append({"index": index, "error": f"ID {item_id} not found for deletion."})
                        continue

                    # --- SCENARIO 2: UPDATE (Has ID and delete is False/Missing) ---
                    if item_id and not is_deleted_flag:
                        try:
                            rel = NodeRelationship.objects.get(id=item_id)
                            # partial=True so they don't have to send every field
                            serializer = NodeRelationshipInputSerializer(rel, data=item_data, partial=True)
                            if serializer.is_valid():
                                try:
                                    updated_rel = serializer.save()
                                    update_change_reason(updated_rel, "Updated via bulk manage")
                                    summary["updated"] += 1
                                except IntegrityError:
                                    # errors.append({
                                    #     "row": index, 
                                    #     "id": item_id, 
                                    #     "error": "This relationship already exists. You cannot create duplicate active relationships between the same territory and controller."
                                    # })
                                    return Response({
                                    "index": index, 
                                    "error": "This relationship already exists."
                                }, status=status.HTTP_400_BAD_REQUEST)
                            else:
                                errors.append({"index": index, "id": item_id, "errors": serializer.errors})
                        except NodeRelationship.DoesNotExist:
                            errors.append({"index": index, "error": f"ID {item_id} not found for update."})
                        continue

                    # --- SCENARIO 3: CREATE (No ID provided) ---
                    if not item_id:
                        serializer = NodeRelationshipInputSerializer(data=item_data)
                        if serializer.is_valid():
                            try:
                                new_rel = serializer.save()
                                update_change_reason(new_rel, "Created via bulk manage")
                                summary["created"] += 1
                            except IntegrityError:
                                # errors.append({
                                #     "row": index, 
                                #     "error": "This relationship already exists. You cannot create duplicate active relationships between the same territory and controller."
                                # })
                                return Response({
                                    "index": index, 
                                    "error": "This relationship already exists."
                                }, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            errors.append({"index": index, "errors": serializer.errors})
                            # raise DRFValidationError({"message": "Validation failed for some items.", "details": serializer.errors})

                # If any index failed, rollback the whole transaction
                if errors:
                    raise DRFValidationError({"message": "Validation failed for some items.", "details": errors})

        except DRFValidationError as e:
            raise e
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Relationships updated successfully.",
            "summary": summary
        }, status=status.HTTP_200_OK)

        
class NodeRelationshipHistoryDiffView(BaseHistoryDiffAPIViewMixin):
    model_class = NodeRelationship
