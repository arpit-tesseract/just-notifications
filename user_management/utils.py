from .models import UserRole

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

def verify_user_roles(role_lst):
    for role in role_lst:
        try:
            UserRole.objects.get(id=role)
        except UserRole.DoesNotExist:
            return False
    return True

def verify_user_category(category):
    categories = ['owner', 'tenant', 'grp_tenant']
    if category not in categories:
        return False
    return True