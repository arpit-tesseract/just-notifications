from configuration.serializers import *
from rest_framework.response import Response
from rest_framework import status
from configuration.models import *
from rest_framework.permissions import AllowAny, IsAuthenticated

def get_object_by_name_or_error(model, name, field=None):
    if field is None:
        field = "name"
    try:
        return model.objects.get(**{f"{field}__iexact": name.strip()})
    except model.DoesNotExist:
        raise serializers.ValidationError(f"{model.__name__} with {field}='{name}' not found.")

def get_related_queryset(request, model, serializer_class, fk_field=None, fk_id=None):
    """
    Fetch related queryset for dropdowns, respecting user allocations.
    Super Admin sees all.
    Others see only allocated ones.
    """
    user = request.user

    try:
        filter_kwargs = {fk_field: fk_id} if fk_field and fk_id else {}
        queryset = model.objects.filter(**filter_kwargs)

        if user.user_role == "super_admin":
            pass
        else:
            allocation_map = {
                "Country": "country_allocation",
                "State": "state_allocation",
                "District": "district_allocation",
                "City": "city_allocation",
                "Village": "village_allocation",
                "Ward": "ward_allocation",
                "Block": "block_allocation",
                "Society": "society_allocation",
                "Continent": "continent_allocation",
            }

            alloc_field = allocation_map.get(model.__name__)
            if alloc_field:
                allocated_queryset = getattr(user, alloc_field).all()
                queryset = queryset.filter(id__in=allocated_queryset.values_list("id", flat=True))

        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

