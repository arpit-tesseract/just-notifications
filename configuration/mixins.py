from django.utils import timezone
from django.db.models import Q

# Only work for Model View Set
# class RecordRuleMixin:
#     action_map = {
#         'list': 'read',
#         'retrieve': 'read',
#         'create': 'create',
#         'update': 'write',
#         'partial_update': 'write',
#         'destroy': 'delete',
#     }
#     def apply_record_rules(self, qs):
#         user = self.request.user
#         model_name = qs.model._meta.label

#         # Fetch all record rules for this user and model
#         rules = user.record_rules.filter(
#             model__technical_name=model_name,
#             **{f"perm_{self.action_map.get(self.action, 'read')}": True}
#         )
        
#         # Combine all domain filters
#         if not rules.exists():
#             return qs
        
#         combined_q = Q()
#         for rule in rules:
#             domain_filter = {}
#             for k, v in rule.domain_filter.items():
#                 if isinstance(v, list):  
#                     # Convert to __in lookup
#                     domain_filter[f"{k}__in"] = v
#                 else:
#                     domain_filter[k] = v
#             combined_q |= Q(**domain_filter)

#         return qs.filter(combined_q)

# Working for APIView & Model ViewSet
class RecordRuleMixin:
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

    def apply_record_rules(self, qs):
        user = self.request.user
        model_name = qs.model._meta.label

        # Determine action
        action = getattr(self, "action", None)
        if not action:
            action = self.request.method.lower()  # fallback for APIView

        perm_field = f"perm_{self.action_map.get(action, 'read')}"

        # Fetch all record rules for this user and model
        rules = user.record_rules.filter(
            model__technical_name=model_name,
            **{perm_field: True}
        )

        # Combine all domain filters
        if not rules.exists():
            return qs

        combined_q = Q()
        for rule in rules:
            domain_filter = {}
            for k, v in rule.domain_filter.items():
                if isinstance(v, list):
                    domain_filter[f"{k}__in"] = v
                else:
                    domain_filter[k] = v
            combined_q |= Q(**domain_filter)

        return qs.filter(combined_q)



    
class FilteredQuerysetMixin(RecordRuleMixin):
    """
    Provides a reusable get_queryset with common filters.
    Automatically infers `model` from queryset if not defined.
    """

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

    def get_base_queryset(self):
        today = timezone.now().date()
        return self._model.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__gte=today) | Q(hold_date__isnull=True)
        )

    def get_queryset(self):
        user = self.request.user
        base_qs = self.get_base_queryset()

        if user.is_system_user:
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

            return self.apply_record_rules(base_qs) if not (is_hidden or on_hold) else self.apply_record_rules(qs)

        return self.apply_record_rules(base_qs)  


# from django.db.models import Q

# class RecordRuleFilteredMixin:
#     action_map = {
#         'list': 'read',
#         'retrieve': 'read',
#         'create': 'create',
#         'update': 'write',
#         'partial_update': 'write',
#         'destroy': 'delete',
#     }

#     def get_queryset(self):
#         qs = super().get_queryset()
#         user = self.request.user
#         model_name = qs.model._meta.label

#         rules = user.record_rules.filter(
#             model__technical_name=model_name,
#             **{f"perm_{self.action_map.get(self.action, 'read')}": True}
#         )

#         if not rules.exists():
#             return qs.none()  # no rules = no access

#         filters = Q()
#         first = True
#         for rule in rules:
#             rule_q = Q(**rule.domain_filter)
#             if first:
#                 filters = rule_q
#                 first = False
#             else:
#                 filters &= rule_q   # <-- AND instead of OR

#         return qs.filter(filters)
