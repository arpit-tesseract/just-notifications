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


import datetime

def cast_value_by_type(value, field_type):
    """
    Parses the string value from the request into the correct Python type
    and returns the appropriate Django lookup (e.g., 'exact', 'icontains').
    """
    if value is None:
        return None, "exact"
        
    value = str(value).strip()
    
    # Empty string handling depends on your needs. 
    # Usually for filters, empty string might be ignored or treated as None.
    if value == "":
        return None, "exact"
    
    # 1. Text Fields
    if field_type in ["char", "text"]:
        return value, "icontains"  # Use partial match for text
    
    # 2. Integers
    if field_type in ["int", "bigint"]:
        # Fix: lstrip (not lsstrip)
        if not value.lstrip('-').isdigit():
            raise ValueError(f"Value '{value}' must be an integer.")
        return int(value), "exact"
    
    # 3. Positive Integer
    if field_type == "positive_int":
        if not value.isdigit():
            raise ValueError(f"Value '{value}' must be a positive integer.")
        return int(value), "exact"
    
    # 4. Float
    # Fix: compare to string "float", not list ["float"]
    if field_type == "float":
        try:
            val = float(value)
        except ValueError:
            raise ValueError(f"Value '{value}' must be a float.")
        return val, "exact"
    
    # 5. Date
    if field_type == "date":
        try:
            # Validate format, but return string for Django to handle
            datetime.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Value '{value}' must be a YYYY-MM-DD date.")
        return value, "exact"

    # 6. DateTime
    if field_type == "datetime":
        try:
            # Standard ISO format is safer
            datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Try ISO with T
            try:
                datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                raise ValueError(f"Value '{value}' must be a YYYY-MM-DD HH:MM:SS datetime.")
        return value, "exact"
    
    # 7. Boolean
    if field_type == "boolean":
        lower_val = value.lower()
        if lower_val in ["true", "t", "1", "yes", "y", "on"]:
            return True, "exact"
        elif lower_val in ["false", "f", "0", "no", "n", "off"]:
            return False, "exact"
        else:
            raise ValueError(f"Invalid boolean value: {value}")
            
    # 8. Dropdown
    if field_type == "dropdown":
        return value, "exact"

    # Default fallback
    return value, "exact"

# def cast_value_by_type(value:str, field_type:str):
#     value = (value or "").strip()
#     if value == "":
#         return None
    
#     if field_type in ["char", "text"]:
#         return value, "icontains"
    
#     if field_type in ["int", "bigint"]:
#         if not value.lsstrip('-').isdigit():
#             raise ValueError("The value must be an integer.")
#         return int(value), "exact"
    
#     if field_type == "positive_int":
#         if not value.isdigit():
#             raise ValueError("The value must be a positive integer.")
#         val = int(value)
#         if val < 0:
#             raise ValueError("The value must be a positive integer.")
#         return val, "exact"
    
#     if field_type == ["float"]:
#         try:
#             val = float(value)
#         except ValueError:
#             raise ValueError("The value must be a float.")
        
#         return val, "exact"
    
#     if field_type == "date":
#         # stored as string "YYYY-MM-DD" usually, but exact still works
#         try:
#             datetime.datetime.strptime(value, "%Y-%m-%d")
#         except ValueError:
#             raise ValueError("The value must be a date.")
        
#         return value, "exact"

    
#     if field_type == "date_time":
#         try:
#             datetime.datetime.strptime(value, "%y-%m_%d %H%M%S")
#         except ValueError:
#             raise ValueError("The value must be a datetime.")
    
#     if field_type == "boolean":
#         if value in ["true", "t", "1", "yes", "y"]:
#             return True, "exact"
#         elif value in ["false", "f", "0", "no", "n"]:
#             return False, "exact"
#         else:
#             raise ValueError(f"Invalid boolean value: {value}")
        
    
#     return value, "exact"

def parse_boolean_strict(val):
    """Safely parses Excel strings, numbers, and bools into a strict Python boolean."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        # Handle textual booleans from Excel
        return val.strip().lower() in ['true', '1', 'yes', 'y', 'on']
    return False

def check_bool_value(val):
    if isinstance(val, bool):
        return val
    
    if isinstance(val, str):
        if val.strip().lower() in ['true', '1', 'yes', 'y', 'on']:
            return True
        elif val.strip().lower() in ['false', '0', 'no', 'n', 'off']:
            return False
    
    return None


def get_type_label(type_val):
    if type_val == "int":
        return "Number"
    elif type_val == "float":
        return "Decimal"
    elif type_val == "date":
        return "Date"
    elif type_val == "datetime":
        return "Date Time"
    elif type_val == "boolean":
        return "Boolean"
    elif type_val == "dropdown":
        return "Dropdown"
    else:
        return "Text"
    

def validate_value_type(value, field_type, max_len=None, options=None):
        """
        Helper method to check if 'value' matches 'field_type'
        """
        s_value = str(value).strip()

        if s_value in ["", None]:
            return None

        # 1. Integer Checks
        if field_type in ['int', 'bigint']:
            if not s_value.lstrip('-').isdigit():
                 raise ValueError("The value must be an numeric.")
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
                raise ValidationError("Date must be in YYYY-MM-DD format.")

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
                    raise ValidationError("DateTime must be in YYYY-MM-DD HH:MM:SS format.")

        # 5. Char / Text Checks
        elif field_type == 'char':
            if max_len and len(s_value) > max_len:
                raise ValidationError(f"Default value cannot exceed {max_len} characters.")
            return s_value
        
        # 6. Dropdown Check
        elif field_type == 'dropdown':
            if options is not None and s_value not in options:
                raise ValidationError(f"Value '{s_value}' is not a valid option.")
            return s_value
        
        elif field_type == 'text':
            return s_value

        return s_value

def get_level_ancestors(level):
    """
    Returns ancestors in order: Root -> ... -> Parent
    Based on Level.parent chain (NOT sort_order).
    """
    ancestors = []
    curr = level.parent
    while curr:
        ancestors.append(curr)
        curr = curr.parent
    return list(reversed(ancestors))

def parse_positive_int(value):
    if value in ["", None]:
        return None
    
    if isinstance(value, str):
        if value.isdigit():
            value = int(value)
        else:
            raise ValueError("The value must be a positive integer.")
    elif not isinstance(value, int):
        raise ValueError("The value must be a positive integer.")

    if value < 0:
        raise ValueError("The value must be a positive integer.")

    return value


def default_in_bounds(default_val, start_val, end_val):
    if default_val is None:
        return False
    if start_val is not None and default_val < start_val:
        return False
    if end_val is not None and default_val > end_val:
        return False
    return True