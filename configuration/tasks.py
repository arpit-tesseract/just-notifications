from celery import shared_task
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from .models import Level, Node
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import IntegrityError
import time
from .utils import cast_value_by_type, check_bool_value, validate_value_type
from simple_history.utils import update_change_reason


level_logger = logging.getLogger("Levels")
User = get_user_model()

@shared_task
def process_level_deletion(level_id, user_id):
    channel_layer = get_channel_layer()
    group_name = f'user_notifications_{user_id}'
    try:
        time.sleep(2)
        # Fetch the instances from the database using the IDs
        user = User.objects.get(id=user_id)
        
        with transaction.atomic():
            level = Level.objects.get(id=level_id, is_deleted=False)
            level_logger.info(f"Background Task: Starting deletion of level {level.name}")
            
            # ==========================================
            # 1. FIX THE DATA NODES FIRST
            # ==========================================
            nodes_in_level = Node.objects.filter(level=level, is_deleted=False)
            
            for node in nodes_in_level:
                children = Node.objects.select_for_update().filter(parent=node, is_deleted=False)
                
                for child in children:
                    child.parent = node.parent
                    child.save() # Safely triggers hierarchy_path & NodeClosure rebuilds
                
                node.soft_delete(user=user)

            # ==========================================
            # 2. FIX THE LEVEL HIERARCHY
            # ==========================================
            qs = Level.objects.select_for_update().filter(
                dimension=level.dimension,
                is_deleted=False
            )
            
            child_level = qs.filter(parent=level).first()
            if child_level:
                child_level.parent = level.parent
                child_level.save(update_fields=['parent'])
            
            qs.filter(sort_order__gt=level.sort_order).update(sort_order=F('sort_order') - 1)

            # ==========================================
            # 3. ACTUAL DELETE
            # ==========================================
            level.soft_delete(user=user)
            
            level_logger.info(f"Background Task: Successfully deleted level {level.name}")
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification', # MUST match the function name in Consumer
                'type_status': 'success',
                'event_type': 'level_delete',
                'message': f"{level.display_name} table deleted successfully."
            }
        )
    except IntegrityError as e:
        level_logger.exception(f"Background Task Failed for level ID {level_id}: {e}")
        # Optional: You could create a Notification model here to alert the user that the job failed

        level_obj = Level.objects.get(id=level_id)
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification', 
                'type_status': 'error',
                'event_type': 'level_delete',
                'message': f"Failed to delete {level_obj.display_name} table."
            }
        )

    except Exception as e:
        level_logger.exception(f"Background Task Failed for level ID {level_id}: {e}")
        # Optional: You could create a Notification model here to alert the user that the job failed
        level_obj = Level.objects.get(id=level_id)
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification', 
                'type_status': 'error',
                'event_type': 'level_delete',
                'message': f"Failed to delete {level_obj.name} table."
            }
        )



import pandas as pd
import json
from celery import shared_task
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from asgiref.sync import async_to_sync          
from channels.layers import get_channel_layer

from .models import Level, Node # Adjust imports based on your app

@shared_task(bind=True)
def process_excel_import(self, file_path, level_id, mapping_dict, user_id=None):
    """
    Background job to process the Excel file.
    """
    summary = {"requested": 0, "created": 0, "updated": 0, "errors": []}

    channel_layer = get_channel_layer()

    # ✅ FIX: Create the group name that matches NotificationConsumer
    group_name = f'user_notifications_{user_id}' if user_id else None

    # Helper function to log errors and fire them off to the WebSocket immediately
    def log_and_send_error(error_data):
        summary["errors"].append(error_data)
        if group_name and channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification', # MUST match the method in NotificationConsumer
                    'event_type': 'node_file_import',
                    'message': error_data,
                    'type_status': 'error'       # Matches the kwargs in NotificationConsumer
                }
            )

    try:
        # 1. Fetch Target Level
        target_level = Level.objects.get(pk=level_id)

        # 2. Open the file from the storage path
        with default_storage.open(file_path, 'rb') as file_obj:
            file_name = file_path.lower()
            
            if file_name.endswith(".csv"):
                df = pd.read_csv(file_obj, encoding="utf-8")
            elif file_name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file_obj)
            else:
                summary["errors"].append({"message": "Invalid file format.", "color": "red"})
                return summary
            
            df = df.astype(object).where(pd.notnull(df), None)
            df.columns = df.columns.str.strip()

        # 3. Identify Key Columns from Mapping
        target_level_name_key = target_level.name
        col_target_name = mapping_dict.get(target_level_name_key)
        
        parent_level = target_level.parent
        col_parent_name = mapping_dict.get(parent_level.name) if parent_level else None

        valid_attr_keys = {col['name']: col['type'] for col in (target_level.extra_fields_schema or [])}

        # ✅ 1. Get the total number of rows
        total_rows = len(df)

        # 4. Process Rows
        for index, row in df.iterrows():
            row_index = index + 2
            row_data = row.to_dict()

            # ✅ 2. Calculate progress percentage
            current_row_number = index + 1

            # Update the frontend every 5 rows, or on the very last row
            if current_row_number % 5 == 0 or current_row_number == total_rows:
                progress_percent = int((current_row_number / total_rows) * 100)
                
                if group_name and channel_layer:
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            'type': 'send_notification',
                            'type_status': 'info',
                            'event_type': 'node_file_import',
                            'message': {
                                'action': 'progress', # Custom flag so the frontend knows what this is
                                'percent': progress_percent,
                                'text': f"Processing {current_row_number} of {total_rows}..."
                            }
                        }
                    )

            id_val = row_data.get("ID")
            if id_val in ["", None]:
                id_val = None
            else:    
                if isinstance(id_val, str) and id_val.isdigit():
                    id_val = int(id_val)
                elif isinstance(id_val, float):
                    id_val = int(id_val)
                elif not isinstance(id_val, int):
                    id_val = None

            name_val = row_data.get(col_target_name)
            if not name_val:
                continue

            summary["requested"] += 1

            try:
                 with transaction.atomic():
                        # --- Step 2: Resolve Parent Node ---
                        # parent_node = None
                        # if parent_level:
                        #     parent_name_val = row_data.get(col_parent_name)
                            
                        #     if not parent_name_val:
                        #         summary["errors"].append(f"Row {row_index}: Missing parent '{parent_level.name}'.")
                        #         continue
                        #     print("Parent Name:", parent_name_val)
                        #     # Find the parent node
                        #     # We search for a Node with the Parent's Name + Parent's Level + Same Dimension
                        #     parent_node = Node.objects.filter(
                        #         name=parent_name_val,
                        #         level=parent_level,
                        #         dimension=target_level.dimension
                        #     ).first()

                        #     if not parent_node:
                        #         # summary["errors"].append(f"Row {row_index}: Parent '{parent_level.name}' named '{parent_name_val}' not found.")
                        #         raise Exception(f"Parent '{parent_level.name}' named '{parent_name_val}' not found. Cannot create row.")


                        # --- Step 2: Resolve Parent Node (Full Hierarchy Lookup) ---
                        parent_node = None
                        if parent_level:
                            parent_name_val = row_data.get(col_parent_name)
                            
                            if not parent_name_val:
                                log_and_send_error({
                                    "message": f"Row {row_index}: Missing parent '{parent_level.name}'.",
                                    "color": "red"
                                })
                                continue
                            
                            # 1. Start building our dynamic query dictionary
                            lookup_kwargs = {
                                'dimension': target_level.dimension
                            }
                            
                            # 2. Traverse UP the level hierarchy
                            current_ancestor_level = parent_level
                            prefix = "" # Starts as "", then becomes "parent__", then "parent__parent__", etc.
                            missing_ancestor_data = False
                            
                            while current_ancestor_level:
                                level_name = current_ancestor_level.name
                                
                                # If this ancestor level is mapped in our JSON (e.g., "Country")
                                if level_name in mapping_dict:
                                    col_name = mapping_dict[level_name]
                                    ancestor_val = row_data.get(col_name)
                                    
                                    if not ancestor_val:
                                        log_and_send_error({
                                            "message": f"Row {row_index}: Missing value for '{level_name}' in column '{col_name}'.",
                                            "color": "red"
                                        })
                                        missing_ancestor_data = True
                                        break
                                    
                                    # Add to our query: e.g., parent__name="China", parent__level=<Country Level>
                                    lookup_kwargs[f"{prefix}name"] = ancestor_val
                                    lookup_kwargs[f"{prefix}level"] = current_ancestor_level
                                
                                # Move up to the next parent level for the next loop iteration
                                current_ancestor_level = current_ancestor_level.parent
                                prefix += "parent__"

                            if missing_ancestor_data:
                                raise Exception(f"Row {row_index}: Missing required hierarchy data.")

                            # 3. Execute the exact hierarchy query
                            # E.g., Node.objects.filter(name="Gujrat", parent__name="China", parent__parent__name="Asia")
                            # 3. Execute the exact hierarchy query
                            parent_node = Node.objects.filter(**lookup_kwargs).first()

                            if not parent_node:
                                # UX UPGRADE: Build a visual path string to show the user exactly what failed
                                attempted_path = []
                                p_prefix = ""
                                c_level = parent_level
                                
                                while c_level:
                                    val = lookup_kwargs.get(f"{p_prefix}name")
                                    if val:
                                        attempted_path.insert(0, str(val))
                                    c_level = c_level.parent
                                    p_prefix += "parent__"
                                
                                path_str = " -> ".join(attempted_path)
                                
                                raise Exception(f"Hierarchy '{path_str}' not found in database. Please check your Excel file for typos!")
                                
                        # --- NEW Step 3: Find Existing Node (Determine Create vs Update) ---
                        node = None
                        # print("Id:", id_val)
                        if id_val is not None:
                            node = Node.objects.filter(id=id_val, level=target_level).first()
                            # print("Node in condition: ", node)
                            if not node:
                                # raise Exception(f"Row {row_index}: Provided ID '{id_val}' does not exist.")
                                # print(f"Row {row_index}: Provided ID '{id_val}' does not exist, so a new row will be created.")
                                log_and_send_error({
                                    "message": f"Row {row_index}: Provided ID '{id_val}' does not exist so a new row will be created.",
                                    "color": "blue"
                                })
                        # print("Node: ", node)

                        # --- Step 3: Extract Standard Fields ---
                        # Helper to safely get value based on mapping key
                        def get_mapped_val(key, default=None):
                            if key in mapping_dict and mapping_dict[key] in row_data:
                                return row_data[mapping_dict[key]]
                            return default

                        code_val = get_mapped_val('code')
                        # print(f"Code: {code_val}, Type: {type(code_val)}")

                        if code_val in ["", None]:
                            raise Exception(f"Row {row_index}: Missing Code.")
                        
                        if type(code_val) not in [str, int]:
                            raise Exception(f"Row {row_index}: Code '{code_val}' is not numeric.")

                        
                        if isinstance(code_val, str) and code_val.isdigit():
                            code_val = int(code_val)

                        if len(str(code_val)) > target_level.code_digits:
                            raise Exception(f"Row {row_index}: Code '{code_val}' too long for level '{target_level.name}'.")
                        
                        # Validate Code
                        if code_val <= 0:
                            raise Exception(f"Row {row_index}: Code '{code_val}' is not positive.")
                        
                        collision_qs = Node.objects.filter(
                            level=target_level,
                            code=code_val,
                            parent=parent_node
                        ).exclude(name=name_val) # Exclude self if this is an update to existing node

                        # Exclude self based on ID if updating, otherwise exclude by name
                        if node:
                            collision_qs = collision_qs.exclude(id=node.id)
                        
                        if collision_qs.exists():
                            raise Exception(f"Row {row_index}: Code '{code_val}' already used by '{collision_qs.first().name}'.")
                        

                        is_hidden_raw = get_mapped_val('is_hidden', None)
                        if is_hidden_raw is None:
                            is_hidden = False
                        else:
                            is_hidden = check_bool_value(is_hidden_raw)
                            if is_hidden is None:
                                raise Exception(f"Row {row_index}: Invalid value for is_hidden: {is_hidden_raw}")
                            
                        on_hold_raw = get_mapped_val('on_hold', None)
                        if on_hold_raw is None:
                            on_hold = False
                        else:
                            on_hold = check_bool_value(on_hold_raw)
                            if on_hold is None:
                                raise Exception(f"Row {row_index}: Invalid value for on_hold: {on_hold_raw}")
                            

                    
                        # Date parsing
                        hold_date_raw = get_mapped_val('hold_date')
                        hold_date_val = None
                        if hold_date_raw:
                            try:
                                dt = pd.to_datetime(hold_date_raw, dayfirst=True)
                                hold_date_val = dt.date()
                            except:
                                log_and_send_error({
                                    "message": f"Row {row_index}: Invalid date format for Hold Date.",
                                    "color": "red"
                                })
                                # summary["errors"].append(f"Row {row_index}: Invalid date format for Hold Date.")
                                continue

                        # --- Step 4: Extract Attributes ---
                        node_attributes = {}
                        if 'attributes' in mapping_dict and isinstance(mapping_dict['attributes'], dict):
                            for sys_attr, excel_header in mapping_dict['attributes'].items():
                                # Only process if this attribute is defined in the Level Schema
                                if sys_attr in valid_attr_keys:
                                    val = row_data.get(excel_header)
                                    if val is not None:
                                        node_attributes[sys_attr] = val


                        # --- Step 6: Update or Create ---
                        # node, created = Node.objects.update_or_create(
                        #     name=name_val,
                        #     level=target_level,
                        #     parent=parent_node,
                        #     defaults={
                        #         "code": code_val,
                        #         "is_hidden": is_hidden,
                        #         "on_hold": on_hold,
                        #         "hold_date": hold_date_val,
                        #         "attributes": node_attributes,
                        #         "dimension": target_level.dimension
                        #     }
                        # )

                        # We avoid update_or_create so we can validate BEFORE hitting the DB
                        # node = Node.objects.filter(
                        #     name=name_val,
                        #     level=target_level,
                        #     parent=parent_node,
                        #     dimension=target_level.dimension
                        # ).first()

                        # if id_val is not None:
                        #     node = Node.objects.filter(id=id_val).first()
                        # else:
                        #     node = None

                        created = False
                        if not node:
                            node = Node(
                                name=name_val,
                                code=code_val,
                                is_hidden=is_hidden,
                                on_hold=on_hold,
                                hold_date=hold_date_val,
                                level=target_level,
                                parent=parent_node,
                                dimension=target_level.dimension,
                                attributes=node_attributes
                            )
                            created = True
                        else:
                            # FIX 2: Apply the updates to the existing node!
                            node.name = name_val
                            node.code = code_val
                            node.is_hidden = is_hidden
                            node.on_hold = on_hold
                            node.hold_date = hold_date_val
                            node.parent = parent_node
                            node.attributes = node_attributes

                        # --- Step 7: Validate (Model Logic) ---
                        try:
                            node.validate_attributes() 
                            node.save()

                        except ValidationError as e:
                            clean_error_text = " ".join(e.messages)
                            # Raise an exception so the transaction rolls back for this row
                            # The outer except block will catch this and log it in summary["errors"]
                            raise Exception(clean_error_text)
                        
                        # Track this in your history API!
                        reason = "Created via Excel Import" if created else "Updated via Excel Import"
                        update_change_reason(node, reason)

                
                        if created: 
                            summary["created"] += 1
                        else: 
                            summary["updated"] += 1


            # USE THE HELPER IN THE EXCEPT BLOCKS
            except IntegrityError as e:
                log_and_send_error({"message": f"Row {row_index}: This data already exists.", "color": "red"})
            except ValidationError as e:
                log_and_send_error({"message": f"Row {row_index}: {' '.join(e.messages)}", "color": "red"})
            except Exception as e:
                log_and_send_error({"message": f"Row {row_index}: {str(e)}", "color": "red"})

    except Exception as e:
        log_and_send_error({"message": f"Critical Error: {str(e)}", "color": "red"})

    finally:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)

        # ✅ FIX: Send final success message to the user's notification group
        if group_name and channel_layer:
             async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'event_type': 'node_file_import',
                    'message': {
                        "status": "completed", 
                        "final_summary": summary
                    },
                    'type_status': 'info'
                }
            )

    return summary