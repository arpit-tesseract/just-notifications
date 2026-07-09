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


import uuid
from django.core.files.storage import default_storage
from django.core.cache import cache

@shared_task(bind=True)
def task_validate_excel(self, file_path, level_id, mapping_dict, user_id):
    """
    Background job to process Step 1 (Preview & Validate) and push progress via WebSocket.
    """
    channel_layer = get_channel_layer()
    group_name = f'user_notifications_{user_id}' if user_id else None

    try:
        from configuration.import_service import ImportService
        target_level = Level.objects.get(pk=level_id)

        with default_storage.open(file_path, 'rb') as file_obj:
            df = ImportService.validate_import_file(file_obj)

        def progress_callback(current, total):
            if group_name and channel_layer:
                progress_percent = int((current / total) * 100)
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'send_notification',
                        'type_status': 'info',
                        'event_type': 'node_file_import',
                        'message': {
                            'action': 'progress',
                            'percent': progress_percent,
                            'text': f"Validating {current} of {total}..."
                        }
                    }
                )

        valid_rows, invalid_rows, summary = ImportService.build_preview(
            df, target_level, mapping_dict, progress_callback=progress_callback
        )

        # Option B logic: If ANY row is invalid, block import.
        if invalid_rows:
            if group_name and channel_layer:
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        'type': 'send_notification',
                        'type_status': 'error',
                        'event_type': 'node_file_import',
                        'message': {
                            'action': 'validation_failed',
                            'message': "File contains errors. Import is blocked.",
                            'summary': summary,
                            'invalid_rows': invalid_rows
                        }
                    }
                )
            return summary

        # If all valid, cache and return session id
        import_session_id = f"import_{uuid.uuid4().hex}"
        cache.set(import_session_id, valid_rows, timeout=1800) # 30 mins

        if group_name and channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'type_status': 'success',
                    'event_type': 'node_file_import',
                    'message': {
                        'action': 'preview_ready',
                        'message': "File validated successfully. Ready to commit.",
                        'import_session_id': import_session_id,
                        'summary': summary,
                        'valid_rows': valid_rows
                    }
                }
            )

    except Exception as e:
        if group_name and channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'type_status': 'error',
                    'event_type': 'node_file_import',
                    'message': {
                        'action': 'error',
                        'message': f"Critical Error: {str(e)}"
                    }
                }
            )
    finally:
        if default_storage.exists(file_path):
            default_storage.delete(file_path)

@shared_task(bind=True)
def task_commit_excel(self, import_session_id, user_id):
    """
    Background job to process Step 2 (Database Commit) and push progress via WebSocket.
    """
    channel_layer = get_channel_layer()
    group_name = f'user_notifications_{user_id}' if user_id else None

    valid_rows = cache.get(import_session_id)
    if not valid_rows:
        if group_name and channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'type_status': 'error',
                    'event_type': 'node_file_import',
                    'message': {
                        'action': 'error',
                        'message': "Import session expired or invalid. Please re-upload."
                    }
                }
            )
        return

    summary = {"created": 0, "updated": 0, "errors": []}
    total = len(valid_rows)

    try:
        with transaction.atomic():
            for i, row in enumerate(valid_rows):
                current = i + 1
                
                # Send progress every 5 rows or on the last row
                if current % 5 == 0 or current == total:
                    if group_name and channel_layer:
                        progress_percent = int((current / total) * 100)
                        async_to_sync(channel_layer.group_send)(
                            group_name,
                            {
                                'type': 'send_notification',
                                'type_status': 'info',
                                'event_type': 'node_file_import',
                                'message': {
                                    'action': 'progress',
                                    'percent': progress_percent,
                                    'text': f"Committing {current} of {total}..."
                                }
                            }
                        )

                node_id = row.get("id")
                is_update = row.get("is_update", False)
                
                if node_id and is_update:
                    node = Node.objects.get(id=node_id)
                    node.name = row["name"]
                    node.code = row["code"]
                    node.is_hidden = row["is_hidden"]
                    node.on_hold = row["on_hold"]
                    node.hold_date = row["hold_date"]
                    node.parent_id = row["parent_id"]
                    node.attributes = row["attributes"]
                    node.save()
                    update_change_reason(node, "Updated via Excel Import")
                    summary["updated"] += 1
                else:
                    create_kwargs = {
                        "name": row["name"],
                        "code": row["code"],
                        "is_hidden": row["is_hidden"],
                        "on_hold": row["on_hold"],
                        "hold_date": row["hold_date"],
                        "parent_id": row["parent_id"],
                        "level_id": row["level_id"],
                        "dimension_id": row["dimension_id"],
                        "attributes": row["attributes"]
                    }
                    if node_id:
                        create_kwargs["id"] = node_id
                        
                    node = Node.objects.create(**create_kwargs)
                    update_change_reason(node, "Created via Excel Import")
                    summary["created"] += 1
                    
        # Clean up cache
        cache.delete(import_session_id)
        
        if group_name and channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'type_status': 'success',
                    'event_type': 'node_file_import',
                    'message': {
                        'action': 'commit_ready',
                        'message': "Import committed successfully.",
                        'summary': summary
                    }
                }
            )
            
    except Exception as e:
        if group_name and channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'send_notification',
                    'type_status': 'error',
                    'event_type': 'node_file_import',
                    'message': {
                        'action': 'error',
                        'message': f"Commit Error: {str(e)}"
                    }
                }
            )
