from configuration.serializers import *

def get_object_by_name_or_error(model, name, field=None):
    if field is None:
        field = "name"
    try:
        return model.objects.get(**{f"{field}__iexact": name.strip()})
    except model.DoesNotExist:
        raise serializers.ValidationError(f"{model.__name__} with {field}='{name}' not found.")
