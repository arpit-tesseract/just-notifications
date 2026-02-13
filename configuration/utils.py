from rest_framework.exceptions import ValidationError
from configuration.models import ModelAccess, ModelName, Designation
from django.db.models import Q, ForeignKey
from django.utils import timezone
import re
import datetime

# def get_two_degit(num):
#     return str(num).zfill(2)

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
    elif isinstance(val, bool):
        return val
    elif isinstance(val, str):
        if val.strip().lower() in ["TRUE", "True", "true", "1", "yes", "y",]:
            return True
        elif val.strip().lower() in ["FALSE", "False", "false", "0", "no", "n"]:
            return False
        else:
            raise ValidationError(f"Invalid boolean value: {val}, value must be either True or False.")
    elif isinstance(val, (int, float)):
        return bool(val)
    else:
        raise ValidationError(f"Invalid boolean value: {val}, value must be either True or False.")
    return False


def get_regular_query(model):
    today = timezone.now().date()
    return model.objects.filter(
        is_hidden=False,
        on_hold=False
    ).filter(
        Q(hold_date__lte=today) | Q(hold_date__isnull=True)
    )

def calculate_hidden_hold(is_hidden, on_hold, hold_date):
    if on_hold == False:
        hold_date = None
             
    if hold_date:
        if hold_date >= timezone.now().date():
            on_hold = True
        else:
            on_hold = False
            hold_date = None
    else:
        on_hold = False
    return is_hidden, on_hold, hold_date


def check_designation_category(category):
    if category in ['personal', 'professional', 'residential']:
        return True
    else:
        return False

def check_designation_name(name):
    pattern = re.compile(r'^[a-z_]+$')
    
    # re.fullmatch() checks if the *entire* string matches the pattern
    if re.fullmatch(pattern, name):
        return True
    else:
        return False


def get_designation_obj_by_name(desingation_name):
    try:
        return Designation.objects.get(name=desingation_name)
    except Designation.DoesNotExist:
        return None
    except Exception as e:
        return None


def parse_bool(v: str) -> bool:
    value = (v or "").strip().lower()
    if value in ["true", "t", "1", "yes", "y"]:
        return True
    elif value in ["false", "f", "0", "no", "n"]:
        return False
    else:
        raise ValueError(f"Invalid boolean value: {value}")


def cast_value_by_type(value:str, field_type:str):
    value = (value or "").strip()
    if value == "":
        return None
    
    if field_type in ["char", "text"]:
        return value, "icontains"
    
    if field_type in ["int", "bigint"]:
        if not value.lsstrip('-').isdigit():
            raise ValueError("The value must be an integer.")
        return int(value), "exact"
    
    if field_type == "positive_int":
        if not value.isdigit():
            raise ValueError("The value must be a positive integer.")
        val = int(value)
        if val < 0:
            raise ValueError("The value must be a positive integer.")
        return val, "exact"
    
    if field_type == ["float"]:
        try:
            val = float(value)
        except ValueError:
            raise ValueError("The value must be a float.")
        
        return val, "exact"
    
    if field_type == "date":
        # stored as string "YYYY-MM-DD" usually, but exact still works
        try:
            datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("The value must be a date.")
        
        return value, "exact"

    
    if field_type == "date_time":
        try:
            datetime.datetime.strptime(value, "%y-%m_%d %H%M%S")
        except ValueError:
            raise ValueError("The value must be a datetime.")
    
    if field_type == "boolean":
        if value in ["true", "t", "1", "yes", "y"]:
            return True, "exact"
        elif value in ["false", "f", "0", "no", "n"]:
            return False, "exact"
        else:
            raise ValueError(f"Invalid boolean value: {value}")
        
    
    return value, "exact"