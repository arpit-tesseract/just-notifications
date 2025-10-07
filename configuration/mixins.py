from django.utils import timezone
from django.db.models import Q, ForeignKey
from django.core.exceptions import FieldError
from rest_framework.exceptions import ValidationError

class BaseQueryMixin:
    """
    Base mixin to ensure super().get_queryset() can always be called safely.
    All other mixins should inherit this first.
    """
    
    def get_queryset(self):
        # Use self.queryset if defined
        # Use model if defined
        if hasattr(self, "model") and self.model is not None:
            return self.model.objects.all()
        if hasattr(self, "get_base_queryset") and self.get_base_queryset is not None:
            return self.get_base_queryset()
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
        'update': 'write',
        'partial_update': 'write',
        'destroy': 'delete',
        # fallback HTTP methods
        'get': 'read',
        'post': 'create',
        'put': 'write',
        'patch': 'write',
        'delete': 'delete',
    }
    
    def get_queryset(self):
        # Always start with parent queryset
        qs = super().get_queryset()
        # Then Apply record rules
        return self.apply_record_rules(qs)
    
    # Return only foreign key fields of this model
    def suggest_foreign_keys(self, model):
        return [f.name for f in model._meta.get_fields() if isinstance(f, ForeignKey)]

    # Return direct fields of this model (including fks)
    def suggest_model_fields(self, model):
        return [f.name for f in model._meta.fields]
    
    # Generic field suggester (used in error handling)
    def suggest_fields(self, model):
        return self.suggest_model_fields(model) + self.suggest_foreign_keys(model)
    
    # Validate domain key like 'continent__namee'.
    def validate_domain_key(self, model, key):
        parts = key.split("__")
        current_model = model

        # idx = id, part = contient,name when {"contient__name": "Europe"}
        # idx = 0, part = contient
        # idx = 1, part = name
        for idx, part in enumerate(parts):
            fields = {f.name: f for f in current_model._meta.get_fields()}

            if part not in fields:
                if idx == 0:
                    # Wrong foreign key in current model
                    return (
                        False,
                        self.suggest_foreign_keys(current_model),
                        part
                    )
                else:
                    # Wrong field in related model
                    return (
                        False,
                        self.suggest_model_fields(current_model),
                        part
                    )

            field = fields[part]
            if field.is_relation and field.related_model:
                current_model = field.related_model
            else:
                if idx < len(parts) - 1:
                    # Not a relation but more parts given
                    return (
                        False,
                        self.suggest_model_fields(current_model),
                        part
                    )

        return (True, None, None)


    def apply_record_rules(self, qs):
        user = self.request.user
        model = qs.model
        model_name = qs.model._meta.label # e.g. "app_label.ModelName"

        # Determine action
        action = getattr(self, "action", None)
        if not action:
            action = self.request.method.lower()  # fallback for APIView

        perm_field = f"can_{self.action_map.get(action, 'read')}"
        
        #  Bypass if system user AND designation level = 0
        if user.check_is_super_admin():
            return qs

        # Fetch all record rules for this user and model
        rules = user.record_rules.filter(
            model__technical_name=model_name,
            **{perm_field: True}        # e.g can_create = True
        )
        
        if not rules.exists():
            return qs

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
                if isinstance(v, list):
                    domain_filter[f"{k}__in"] = v
                else:
                    domain_filter[k] = v
            combined_q |= Q(**domain_filter)

        try:
            return qs.filter(combined_q)
        except FieldError as e:
            raise ValidationError({
                "error": str(e),
                "suggestions": self.suggest_fields(model)
            })



    
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
        base_qs = super().get_queryset()

        if user.check_is_system_admin() or user.check_is_super_admin() and user.is_verified:
            qs = self._model.objects.all()
            is_hidden = self.request.query_params.get("is_hidden")
            on_hold = self.request.query_params.get("on_hold")

            # Apply filters if provided
            if is_hidden is not None:
                if is_hidden.lower() == 'true':
                    qs = qs.filter(is_hidden=True)
                elif is_hidden.lower() == 'false':
                    qs = qs.filter(is_hidden=False)
            
            if on_hold is not None:
                if on_hold.lower() == 'true':
                    qs = qs.filter(on_hold=True)
                elif on_hold.lower() == 'false':
                    qs = qs.filter(on_hold=False)
            
            for param, field in self.FILTER_FIELDS.items():
                value = self.request.query_params.get(param)
                if value is not None and value is not '':
                    qs = qs.filter(**{field: value})

            final_qs = qs
        else:
            final_qs = base_qs
        
        # Apply record rules if RecordRuleMixin is used
        # if hasattr(self, "apply_record_rules"):
        #     return self.apply_record_rules(final_qs)
        return final_qs  


class SearchMixin(BaseQueryMixin):
    search_param = "search"
    search_limit = 10          # configurable limit

    def get_result_queryset(self):
        qs = super().get_queryset()
        search_value = self.request.query_params.get(self.search_param)
        if search_value:
            qs = qs.filter(name__icontains=search_value)[: self.search_limit]
        return qs

