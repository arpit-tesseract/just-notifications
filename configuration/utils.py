from rest_framework.exceptions import ValidationError
from configuration.models import ModelAccess, ModelName
from django.db.models import Q, ForeignKey

def check_id_exists(model, id):
    try:
        model.objects.get(id=id)
        return True
    except model.DoesNotExist:
        return False

def check_obj_exists(model, id):
    try:
        obj = model.objects.get(id=id)
        return obj
    except model.DoesNotExist:
        return False

    
def validate_assignable_permissions(request_user, model_id, requested_perms: dict):
    """
    Ensure that the logged-in user can only assign permissions 
    that they themselves already have for the given model.
    
    Args:
        request_user (CustomUser): logged-in user
        model_id (int): model being assigned
        requested_perms (dict): dict of permissions, e.g.
            {"can_read": True, "can_create": False, "can_update": True, "can_delete": False}
    """
    try:
        model_name = ModelName.objects.get(id=model_id)
    except ModelName.DoesNotExist:
        pass
    
    try:
        current_user_access = ModelAccess.objects.get(user=request_user, model=model_id)
    except ModelAccess.DoesNotExist:
        raise ValidationError(f"You do not have any access to {model_name.model} yet.")

    for perm in ["can_read", "can_create", "can_update", "can_delete"]:
        # can_read = True & current_user_access.can_read = False, then raise error
        if requested_perms.get(perm) and not getattr(current_user_access, perm): # getattr(current_user_access, "can_update") → True/False.
            print(getattr(current_user_access, perm))
            raise ValidationError(
                f"You cannot assign {perm.split("_")[1]} for {model_name.model} "
                f"because you don’t have it yourself."
            )
            
            
# Return only foreign key fields of this model
def suggest_foreign_keys(model):
        return [f.name for f in model._meta.get_fields() if isinstance(f, ForeignKey)]

# Return direct fields of this model (including fks)
def suggest_model_fields(model):
    return [f.name for f in model._meta.fields]


def validate_domain_filter(model, domain_filter):
    for key, val in domain_filter.items():

        parts = key.split("__")
        if len(parts) > 2:
            raise ValidationError({"error": "Only one level of nested fields is allowed."})
        
        current_model = model

        # idx = id, part = contient,name when {"contient__name": "Europe"}
        # idx = 0, part = contient
        # idx = 1, part = name
        for idx, part in enumerate(parts):
            fields = {f.name: f for f in current_model._meta.get_fields()}
            
            if part not in fields:
                # Wrong foreign key in current model
                raise ValidationError({
                    "error":f"{part} is not a valid field for {current_model.__name__}.",
                    "suggetions": suggest_foreign_keys(current_model) if idx == 0 else suggest_model_fields(current_model),
                    }
                )
        
        # ---- Value Existence Check ----
        # {key: val}        # → {"continent__name": "Asia"}
        # Q(**{key: val})   # → Q(continent__name="Asia")
        if isinstance(val, list):
            q = Q(**{f"{key}__in": val})
        else:
            q = Q(**{key: val})

        if not current_model.objects.filter(q).exists():
            raise ValidationError({
                "error": f"Value {val} not found for filter {key} in {current_model.__name__}."
            })
       
            
# Find first ForeignKey/OneToOneField in model_cls that points to target_model.
def get_related_field_name(model_cls, target_model):
    for field in model_cls._meta.get_fields():
        if field.is_relation and field.related_model == target_model:
            return field.name
    return None

import pandas as pd
from django.core.exceptions import ValidationError

def read_file(file, required_columns):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file, encoding="utf-8")
    elif file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file)
    else:
        raise ValidationError("Unsupported file format.")

    # Normalize headers
    df.columns = df.columns.str.strip()
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required columns: {', '.join(missing_cols)}")
        
    return df

def normalize_bool(val):
    """Safely convert Excel/CSV boolean values to Python bool."""
    if pd.isna(val):
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        return val.strip().lower() in ["true", "1", "yes", "y"]
    return False