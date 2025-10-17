from .models import UserRole, CustomUser

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

def check_email_exists(email):
    try:
        CustomUser.objects.get(email=email)
        return True
    except CustomUser.DoesNotExist:
        return False

def check_contact_no_exists(contact_no):
    try:
        CustomUser.objects.get(contact_no=contact_no)
        return True
    except CustomUser.DoesNotExist:
        return False