from .models import UserRole, CustomUser
from configuration.models import Brand
from rest_framework.response import Response
from rest_framework import status

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
                return Response(
                    {"error": "Something went wrong."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
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


def get_higher_designation_user(higher_designation, relations):
    for relation in relations:
        if relation.get("designation") == higher_designation:
            relation_obj = relations.pop(relations.index(relation))
            print(higher_designation)
            print(relation_obj)
            return relation_obj.get("user_obj"), relations
