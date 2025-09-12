from rest_framework.exceptions import ValidationError
from configuration.models import ModelAccess, ModelName

def check_id_exists(model, id):
    try:
        model.objects.get(id=id)
        return True
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
        if requested_perms.get(perm) != getattr(current_user_access, perm): # getattr(current_user_access, "can_update") → True/False.
            print(getattr(current_user_access, perm))
            raise ValidationError(
                f"You cannot assign {perm.split("_")[1]} for {model_name.model} "
                f"because you don’t have it yourself."
            )