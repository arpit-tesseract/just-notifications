from .models import UserRole, CustomUser
from configuration.models import Brand
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import ResidentialDetail, PersonalDetail, ProfessionalDetail, Relation
from configuration.models import ModelName, ModelAccess

def get_obj_by_modle_and_id(model, id_):
    try:
        return model.objects.get(id=id_)
    except model.DoesNotExist:
        return None

def get_role_obj_by_ids(role_id_lst):
    roles = UserRole.objects.filter(id__in=role_id_lst)
    if roles.count() != len(role_id_lst):
        return None
    return roles

def get_role_obj_by_name(role_name):
    try:
        role = UserRole.objects.get(name=role_name)
        return role
    except UserRole.DoesNotExist:
        return None
    except Exception as e:
        return None

def verify_user_category_for_residential(category):
    categories = ['owner', 'tenant', 'grp_tenant']
    if category not in categories:
        return False
    return True

def verify_user_relation_category(category):
    categories = ['current', 'owner', 'permanent', 'native', 'inlaws', 'maternal', 'business']
    if category not in categories:
        return False
    return True

def get_obj_by_modle_and_id(model, id):
    try:
        return model.objects.get(id=id)
    except model.DoesNotExist:
        return None
    except Exception as e:
        return None

def check_email_exists_in_CustomUser(email):
    try:
        CustomUser.objects.get(email=email)
        return True
    except CustomUser.DoesNotExist:
        return False

def check_contact_no_exists_in_CustomUser(contact_no):
    try:
        CustomUser.objects.get(contact_no=contact_no)
        return True
    except CustomUser.DoesNotExist:
        return False

def verify_shashan_brand_by_id(id):
    try:
        brand_obj = Brand.objects.get(id=id)
        if brand_obj.name != "Shashan":
            return False
        return True
    except Brand.DoesNotExist:
        return False
    except Exception as e:
        return False

def assign_system_admin_role_if_brand_is_shashan(user_obj, brand_id):
    if brand_id is not None:
        
        if isinstance(brand_id, Brand):
            brand_id = brand_id.id
            
        if verify_shashan_brand_by_id(brand_id):
            system_admin_role = get_role_obj_by_name("system_admin")
            if system_admin_role is None:
                ValidationError("System admin role not found.")
            user_obj.user_role.add(system_admin_role)

def clean_str(value):
    # print("Clean str fun is called")
    if value is None:
        return None
    
    # Ensure it's a string
    if not isinstance(value, str):
        value = str(value)
    
    # Normalize line breaks and tabs
    value = value.replace('\r', '').replace('\n', ' ').replace('\t', ' ')
    
    # Strip extra spaces
    value = value.strip()
    if value == "":
        return None
    
    return value


def get_from_user_and_to_users(higher_designation, relations):
    for index, relation in enumerate(relations):
        user_obj = relation.get("user_obj")
        designation = relation.get("designation")
        
        print(designation.id, "===", higher_designation.id, "and", user_obj.expired_date)
        if designation.id == higher_designation.id and user_obj.expired_date is None:
            relation_obj = relations.pop(relations.index(relation))
            from_user_obj = relation_obj.get("user_obj")
            from_user_designation = designation
            # print("Higher designation user:", relation_obj.get("user_obj"), relations)
    return from_user_obj, from_user_designation, relations


def get_or_create_residential_details(**residential_details):
    residential_details_obj, created = ResidentialDetail.objects.get_or_create(
        **residential_details
    )
    return residential_details_obj


def allocate_rooms_for_from_user(user_obj):
    # get residential details
    residential_obj = user_obj.residential_details
    print("residential_obj to allocate room", residential_obj)
    print("room details:", residential_obj.room_details)
    room_details = residential_obj.room_details
    
    # if user_obj.allocated_rooms is None:
    #     print("pending rooms to allocate (1):",residential_obj.pending_rooms_to_allocate)
    #     user_obj.allocated_rooms = residential_obj.pending_rooms_to_allocate.copy()
    #     user_obj.save()


    print("pending rooms to allocate (1):",residential_obj.pending_rooms_to_allocate)
    user_obj.allocated_rooms = residential_obj.pending_rooms_to_allocate.copy()
    user_obj.save()
            
        
    for room_type, value in room_details.items():
        # user_obj.allocated_rooms[room_type] = 1
        if residential_obj.pending_rooms_to_allocate[room_type]["count"] == value["count"]:
            # residential_obj.pending_rooms_to_allocate[room_type] = total_rooms
            print("Pending room stay as it is:", residential_obj.pending_rooms_to_allocate)
            pass
        else:
            residential_obj.pending_rooms_to_allocate[room_type]["count"] += 1
            print("Pending room to allocate:", residential_obj.pending_rooms_to_allocate)
    
    print("user allocate rooms:", user_obj.allocated_rooms)
    residential_obj.save()

def allocate_rooms_for_to_user(user_obj):
    # get residential details
    residential_obj = user_obj.residential_details
    pending_rooms = residential_obj.pending_rooms_to_allocate
    
    if user_obj.allocated_rooms is None:
        user_obj.allocated_rooms = {}
        
    for room_type, value in pending_rooms.items():
        if residential_obj.room_details[room_type]["count"] == value["count"]:
            user_obj.allocated_rooms[room_type]["count"] = value["count"]
        else:
            user_obj.allocated_rooms[room_type]["count"] += 1
            residential_obj.pending_rooms_to_allocate[room_type]["count"] -= 1
            
    user_obj.save()
    residential_obj.save()
              
    
# def allocate_rooms(index, room_details, user_obj):
#     allocated_room_dict = {}
    
#     for room_type, total_rooms in room_details.items():
#         # If room count not exceeded, assign sequentially
#         if (index + 1) <= total_rooms:
#             allocated_room_dict[room_type] = index + 1
#         else:
#             # If rooms exhausted, share last one
#             allocated_room_dict[room_type] = total_rooms
            
#     return allocated_room_dict

def get_parent_user_obj(user_obj, relation_category):
    try:
        relation_obj = Relation.objects.get(relation_category=relation_category, to_user = user_obj)
        return relation_obj.from_user
    except Relation.DoesNotExist:
        raise ValidationError(f"No parent relation found for user {user_obj.email}.")
    except Relation.MultipleObjectsReturned:
        raise ValidationError(f"Multiple parent relations found for user {user_obj.email}.")

def allocate_room_same_as_parent(user_obj, relation_category):
    try:
        print("allocate_room_same_as_parent", user_obj.email)
        parent_user_obj = get_parent_user_obj(user_obj, relation_category)
        user_obj.allocated_rooms = parent_user_obj.allocated_rooms
        user_obj.save()
        
    except Exception as e:
        raise ValidationError(f"Room allocation failed for {user_obj.email}: {str(e)}")


def mark_as_verify_or_unverify_user(user_obj, relation_category):
    try:
        parent_user_obj = get_parent_user_obj(user_obj, relation_category)
    except ValidationError:
        # This user has no parent (is a from_user), so just return.
        # The 'from_user' verification logic is different.
        # Let's assume the from_user is verified by default if not expired.
        if user_obj.expired_date is None:
            user_obj.is_verified = True
            user_obj.save()
        else:
            user_obj.is_verified = False
            user_obj.save()
        return
    
    if user_obj.expired_date is None:
        if (user_obj.marital_status == "single" and parent_user_obj.marital_status != "single") or (user_obj.marital_status == "married"):
            user_obj.is_verified = True
            user_obj.save()
        else:
            user_obj.is_verified = False
            user_obj.save()
    else:
        user_obj.is_verified = False
        user_obj.save()


def is_to_user(user_obj):
    try:
        Relation.objects.get(to_user = user_obj)
        return True
    except Exception as e:
        return False
    

def get_model_access_rights_of_super_admin():
    model_access_rights = []
    model_name_obj_lst = ModelName.objects.all()
 
    for model_name_obj in model_name_obj_lst:
        model_access_rights.append(
            {
                "model": model_name_obj.model,
                "can_read": True,
                "can_create": True,
                "can_update": True,
                "can_delete": True, 
            }
        )
    return model_access_rights


def get_default_model_access_rights():
    model_access_rights = []
    model_name_obj_lst = ModelName.objects.all()
    
    for model_name_obj in model_name_obj_lst:
        model_access_rights.append(
            {
                "model": model_name_obj.model,
                "can_read": False,
                "can_create": False,
                "can_update": False,
                "can_delete": False, 
            }
        )
    return model_access_rights
            

   
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


def get_ModelName_obj_by_name(model_name):
    try:
        model_obj = ModelName.objects.get(model=model_name)
        return model_obj
    except ModelName.DoesNotExist:
        return None