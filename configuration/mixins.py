from django.utils import timezone
from django.db.models import Q, ForeignKey
from django.core.exceptions import FieldError
from rest_framework.exceptions import ValidationError
from django.db.models.fields.related import ForeignObjectRel
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ImproperlyConfigured

import json
import re

class BaseHistoryDiffAPIViewMixin(APIView):
    """
    Universal Base View to get before/after history diffs for ANY model 
    using django-simple-history.
    """
    permission_classes = [IsAuthenticated]
    model_class = None
    lookup_url_kwarg = 'id'  # Default URL kwarg to look for

    def get(self, request, *args, **kwargs):
        if self.model_class is None:
            raise ImproperlyConfigured("You must define 'model_class' on the child view.")

        object_id = self.kwargs.get(self.lookup_url_kwarg)
        
        # Dynamically use the history of whichever model is provided
        history_records = list(
            self.model_class.history.filter(id=object_id)
            .select_related('history_user')
            .order_by('-history_date')
        )
        
        result_data = []
        ignored_fields = ['hierarchy_path', 'updated_at', 'history_id', 'history_date', 'history_type', 'history_user', 'history_change_reason']

        for index, record in enumerate(history_records):
            if record.history_type == '+':
                action = 'Created'
            elif record.history_type == '~':
                action = 'Changed'
            else:
                action = 'Deleted'
                
            changed_by = record.history_user.email if record.history_user else 'System'
            changes = []
            
            # Compare current record with the previous one chronologically
            if action == 'Changed' and index + 1 < len(history_records):
                prev_record = history_records[index + 1]
                delta = record.diff_against(prev_record)
                
                for change in delta.changes:
                    if change.field not in ignored_fields:
                        # field_display_name = change.field.replace('_', ' ').capitalize()
                        changes.append({
                            "field": change.field,
                            "before": change.old,
                            "after": change.new
                        })
            
            # --- NEW: Intercept and Extract Aliases ---
            raw_reason = record.history_change_reason or ""
            clean_reason_parts = []
            
            # Split by " | " in case there are multiple changes or text reasons
            for part in raw_reason.split(" | "):
                part = part.strip()
                
                # Regex looks for: Any text (except colon), followed by a colon, followed by {JSON}
                # Example match: "aliases:{"before": [], "after": ["New"]}"
                match = re.match(r'^([^:]+):(\{.*\})$', part)
                
                if match:
                    raw_field_name = match.group(1).strip() # e.g., "aliases" or "tags"
                    json_str = match.group(2).strip()       # e.g., '{"before": [], "after": ["New"]}'
                    
                    try:
                        parsed_data = json.loads(json_str)
                        
                        # Verify it has our expected diff structure
                        if isinstance(parsed_data, dict) and ("before" in parsed_data or "after" in parsed_data):
                            # Format field name nicely (e.g., "node_aliases" -> "Node Aliases")
                            display_name = raw_field_name.replace('_', ' ').title()
                            
                            changes.append({
                                "field": display_name,
                                "before": parsed_data.get("before", []),
                                "after": parsed_data.get("after", [])
                            })
                        else:
                            # Valid JSON, but not a diff format -> keep as normal text
                            clean_reason_parts.append(part)
                            
                    except json.JSONDecodeError:
                        # Parsing failed -> keep as normal text
                        clean_reason_parts.append(part)
                elif part:
                    # Normal text reason (e.g., "Created via Excel Import")
                    clean_reason_parts.append(part)
            
            final_change_reason = " | ".join(clean_reason_parts) if clean_reason_parts else "None"

            # 3. Append to Results
            if final_change_reason is not None  or len(changes) > 0 :
                result_data.append({
                    "date_time": record.history_date,
                    "action": action,
                    "changed_by": changed_by,
                    "change_reason": final_change_reason,
                    "changes": changes if len(changes) > 0 else "None" 
                })
            
        return Response(result_data)

class BaseQueryMixin:
    """
    Base mixin to ensure super().get_queryset() can always be called safely.
    All other mixins should inherit this first.
    """
    
    def get_queryset(self):
        # Use self.queryset if defined
        # Use model if defined
        if hasattr(self, "get_base_queryset") and self.get_base_queryset is not None:
            return self.get_base_queryset()
        if hasattr(self, "model") and self.model is not None:
            return self.model.objects.all()
        if hasattr(self, "queryset") and self.queryset is not None:
            return self.queryset
        
        raise NotImplementedError(
            f"{self.__class__.__name__} must define `queryset` or `model`"
        )


class AssignedNodeFilterMixin(BaseQueryMixin):
    """
    Mixin to filter the queryset so that users only see the nodes 
    (or objects related to nodes) that are assigned to them via AdminResidentialNodeAssignment.
    """
    # Override this in your view if the model is related to Node instead of being the Node itself.
    # For example: node_filter_field = "node_id__in" or "node__id__in"
    node_filter_field = "id__in"
    
    # Set to False in your view if even super admins should be restricted by specific node assignments
    bypass_for_super_admins = True

    def get_queryset(self):
        print("AssignedNodeFilterMixin.get_queryset()")
        qs = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return qs.none()

        # Only super_admin can view all nodes. Regular admins are restricted.
        if self.bypass_for_super_admins and hasattr(user, 'is_super_admin') and user.is_super_admin():
            return qs
            
        from user.models import AdminResidentialNodeAssignment
        assigned_node_ids = AdminResidentialNodeAssignment.objects.filter(
            user=user
        ).values_list('node_id', flat=True)
        
        filter_kwargs = {self.node_filter_field: assigned_node_ids}
        return qs.filter(**filter_kwargs).distinct()
