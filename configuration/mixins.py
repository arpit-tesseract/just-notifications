from django.utils import timezone
from django.db.models import Q, ForeignKey
from django.core.exceptions import FieldError
from rest_framework.exceptions import ValidationError
from django.db.models.fields.related import ForeignObjectRel
from rest_framework import status
from rest_framework.response import Response

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


# Working for APIView & Model ViewSet
class RecordRuleMixin(BaseQueryMixin):
    action_map = {
        'list': 'read',
        'retrieve': 'read',
        'create': 'create',
        'update': 'update',
        'partial_update': 'update',
        'destroy': 'delete',
        # fallback HTTP methods
        'get': 'read',
        'post': 'create',
        'put': 'update',
        'patch': 'update',
        'delete': 'delete',
    }
    
    def get_queryset(self):
        qs = super().get_queryset()
        return self.apply_record_rules(qs)
    
    def suggest_foreign_keys(self, model):
        # This logic is better, it gets all relation fields
        return [
            f.name for f in model._meta.get_fields() 
            if isinstance(f, (ForeignKey, ForeignObjectRel))
        ]

    def suggest_model_fields(self, model):
        return [f.name for f in model._meta.fields]
    
    def suggest_fields(self, model):
        return self.suggest_model_fields(model) + self.suggest_foreign_keys(model)
    
    # 
    # ======================================================================
    # FIX #1: validate_domain_key
    # The logic is moved *outside* the loop and iterates over the
    # correct `field_parts` list.
    # ======================================================================
    #
    def validate_domain_key(self, model, key):
        parts = key.split("__")
        current_model = model

        lookup_suffixes = {
            "exact", "iexact", "contains", "icontains",
            "in", "gt", "gte", "lt", "lte",
            "startswith", "istartswith", "endswith", "iendswith",
            "range", "year", "month", "day", "isnull"
        }
        
        # 1. Determine the actual field path, separating it from the lookup
        field_parts = parts
        if parts[-1] in lookup_suffixes:
            field_parts = parts[:-1] # This is the path we need to validate (e.g., ['id'])
        
        if not field_parts:
             raise ValidationError({"error": f"Invalid filter key '{key}'. Cannot be empty."})

        # 2. Now, loop over the *corrected* field_parts list
        for idx, part in enumerate(field_parts):
            
            # Get all fields, including reverse relations
            fields = {f.name: f for f in current_model._meta.get_fields()}

            if part not in fields:
                if idx == 0:
                    return (
                        False,
                        self.suggest_foreign_keys(current_model),
                        part
                    )
                else:
                    return (
                        False,
                        self.suggest_model_fields(current_model),
                        part
                    )

            field = fields[part]
            
            # Check if this field is a relation that we can traverse
            if field.is_relation and field.related_model:
                current_model = field.related_model
            else:
                # 3. Check against the length of field_parts, not parts
                if idx < len(field_parts) - 1:
                    # This is not a relation, but there are more parts left.
                    # e.g., "name__startswith" - "name" is not a relation.
                    return (
                        False,
                        self.suggest_model_fields(current_model),
                        part
                    )

        return (True, None, None)

    # 
    # ======================================================================
    # FIX #2: apply_record_rules
    # This now trusts the key 'k' from the database and fixes the
    # 'id__in__in' bug. It also fixes the 'qs.none' typo.
    # ======================================================================
    #
    def apply_record_rules(self, qs):
        user = self.request.user
        model = qs.model
        model_name = qs.model._meta.label # e.g. "app_label.ModelName"

        action = getattr(self, "action", None)
        if not action:
            action = self.request.method.lower()

        perm_field = f"can_{self.action_map.get(action, 'read')}"
        
        if user.check_is_super_admin():
            return qs

        all_rules_for_model = user.record_rules.filter(
            model__technical_name=model_name
        )

        if not all_rules_for_model.exists():
            return qs
        
        rules = all_rules_for_model.filter(
            **{perm_field: True}
        )
        
        if not rules.exists():
            # Typo fix: qs.none is a function
            return qs.none() 

        combined_q = Q()
        for rule in rules:
            domain_filter = {}
            for k, v in rule.domain_filter.items():
                is_valid, suggestions, bad_field = self.validate_domain_key(model, k)
                if not is_valid:
                    raise ValidationError({
                        "error": f"Invalid field '{bad_field}' in filter key '{k}'",
                        "suggestions": suggestions,
                    })
                
                # --- THIS IS THE FIX ---
                # We trust the key 'k' and value 'v' directly from the rule.
                # This correctly handles "id__in": [1, 2, 3]
                # and avoids creating "id__in__in".
                domain_filter[k] = v
                # --- END FIX ---
                
            combined_q |= Q(**domain_filter)
        
        if not combined_q:
            # No valid filters were built (e.g., rules had empty domain_filters)
            return qs.none()

        try:
            return qs.filter(combined_q)
        except FieldError as e:
            raise ValidationError({
                "error": str(e),
                "suggestions": self.suggest_fields(model)
            })

# Working for APIView & Model ViewSet
# class RecordRuleMixin(BaseQueryMixin):
#     action_map = {
#         'list': 'read',
#         'retrieve': 'read',
#         'create': 'create',
#         'update': 'update',
#         'partial_update': 'update',
#         'destroy': 'delete',
#         # fallback HTTP methods
#         'get': 'read',
#         'post': 'create',
#         'put': 'update',
#         'patch': 'write',
#         'delete': 'delete',
#     }
    
#     def get_queryset(self):
#         # Always start with parent queryset
#         qs = super().get_queryset()
#         # Then Apply record rules
#         return self.apply_record_rules(qs)
    
#     # Return only foreign key fields of this model
#     def suggest_foreign_keys(self, model):
#         return [f.name for f in model._meta.get_fields() if isinstance(f, ForeignKey)]

#     # Return direct fields of this model (including fks)
#     def suggest_model_fields(self, model):
#         return [f.name for f in model._meta.fields]
    
#     # Generic field suggester (used in error handling)
#     def suggest_fields(self, model):
#         return self.suggest_model_fields(model) + self.suggest_foreign_keys(model)
    
#     # Validate domain key like 'continent__namee'.
#     def validate_domain_key(self, model, key):
#         parts = key.split("__")
#         current_model = model

#         # idx = id, part = contient,name when {"contient__name": "Europe"}
#         # idx = 0, part = contient
#         # idx = 1, part = name
#         for idx, part in enumerate(parts):
#             fields = {f.name: f for f in current_model._meta.get_fields()}

#             if part not in fields:
#                 if idx == 0:
#                     # Wrong foreign key in current model
#                     return (
#                         False,
#                         self.suggest_foreign_keys(current_model),
#                         part
#                     )
#                 else:
#                     # Wrong field in related model
#                     return (
#                         False,
#                         self.suggest_model_fields(current_model),
#                         part
#                     )

#             field = fields[part]
#             if field.is_relation and field.related_model:
#                 current_model = field.related_model
#             else:
#                 if idx < len(parts) - 1:
#                     # Not a relation but more parts given
#                     return (
#                         False,
#                         self.suggest_model_fields(current_model),
#                         part
#                     )

#         return (True, None, None)


#     def apply_record_rules(self, qs):
#         user = self.request.user
#         model = qs.model
#         model_name = qs.model._meta.label # e.g. "app_label.ModelName"

#         # Determine action
#         action = getattr(self, "action", None)
#         if not action:
#             action = self.request.method.lower()  # fallback for APIView

#         perm_field = f"can_{self.action_map.get(action, 'read')}"
        
#         #  Bypass if system user AND designation level = 0
#         if user.check_is_super_admin():
#             return qs

#         # Fetch all record rules for this user and model
#         rules = user.record_rules.filter(
#             model__technical_name=model_name,
#             **{perm_field: True}        # e.g can_create = True
#         )
        
#         if not rules.exists():
#             return qs

#         combined_q = Q()
#         for rule in rules:
#             domain_filter = {}
#             for k, v in rule.domain_filter.items():
#                 is_valid, suggestions, bad_field = self.validate_domain_key(model, k)
#                 if not is_valid:
#                     raise ValidationError({
#                         "error": f"Invalid field '{bad_field}' in filter key '{k}'",
#                         "suggestions": suggestions,
#                     })
#                 if isinstance(v, list):
#                     domain_filter[f"{k}__in"] = v
#                 else:
#                     domain_filter[k] = v
#             combined_q |= Q(**domain_filter)

#         try:
#             return qs.filter(combined_q)
#         except FieldError as e:
#             raise ValidationError({
#                 "error": str(e),
#                 "suggestions": self.suggest_fields(model)
#             })



    
class FilteredQuerysetMixin(BaseQueryMixin):
    """
    Provides a reusable get_queryset with common filters.
    Automatically infers `model` from queryset if not defined.
    """

    FILTER_FIELDS = {}

    @property
    def _model(self):
        # Prefer `self.model`, fallback to queryset.model
        if hasattr(self, "model") and self.model:
            return self.model
        if hasattr(self, "queryset") and self.queryset is not None:
            return self.queryset.model
        raise AttributeError(
            f"{self.__class__.__name__} must define either `model` or `queryset`."
        )

    def get_queryset(self):
        user = self.request.user
        # basw_qs = self.get_safe_queryset()
        # if user.check_is_system_admin() or user.check_is_super_admin() and user.is_verified:
        #     base_qs = self._model.objects.all()
        # else:
        base_qs = super().get_queryset()

        # if user.check_is_system_admin() or user.check_is_super_admin() and user.is_verified:
        #     base_qs = self._model.objects.all()
            
        for param, field in self.FILTER_FIELDS.items():
            
            value = self.request.query_params.get(param)
            if value in ["true", "True", "1"]:
                value = True
            if value in ["false", "False", "0"]:
                value = False
                
            if isinstance(value, bool):
                if user.check_is_system_admin() or user.check_is_super_admin() and user.is_verified:
                    base_qs = base_qs.filter(**{field: value})
                    
            elif value is not None and value is not '':
                try: 
                    if param == "search":
                        base_qs = base_qs.filter(name__icontains=value)
                    else:
                        base_qs = base_qs.filter(**{field: value})
                except Exception as e:
                    # if not a valid field, ignore
                    continue
        
        # Apply record rules if RecordRuleMixin is used
        # if hasattr(self, "apply_record_rules"):
        #     return self.apply_record_rules(final_qs)
        return base_qs  
