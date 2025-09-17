from rest_framework import serializers
from .models import *
from shashan.utils.validators import get_object_by_name_or_error
from user_management.models import CustomUser
from .utils import *
from django.apps import apps
from django.db import transaction

# Residential ->
class GlobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Glob
        fields = '__all__'
        read_only_fields = ['id']


class ContinentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = '__all__'
        read_only_fields = ['id']


class CountrySerializer(serializers.ModelSerializer):
    # continent = serializers.CharField(required=True)
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = ['id']

    # def validate_continent(self, value):
    #     return get_object_by_name_or_error(Continent, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = ['id']
    
    
class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = ['id']


class TalukaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taluka
        fields = '__all__'
        read_only_fields = ['id']


class CityVillageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityVillage
        fields = '__all__'
        read_only_fields = ['id']

    
class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = '__all__'
        read_only_fields = ['id']

    
class SocietySerializer(serializers.ModelSerializer):
    class Meta:
        model = Society
        fields = '__all__'
        read_only_fields = ['id']


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'
        read_only_fields = ['id']

    
class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = ['id']
    
    
class HousesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Houses
        fields = '__all__'
        read_only_fields = ['id']

    
# class PermisionModuleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PermissionModule
#         fields = '__all__'

# class PermissionActionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PermissionAction
#         fields = '__all__'

# class AccessesSerializer(serializers.ModelSerializer):
#     module = PermisionModuleSerializer(read_only=True)
#     permission = PermissionActionSerializer(read_only=True)

#     class Meta:
#         model = Accesses
#         fields = '__all__'

# Personal ->
class ReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Religion
        fields = '__all__'
        read_only_fields = ['id']


class SampradaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Sampraday
        fields = '__all__'
        read_only_fields = ['id']


class PanthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Panth
        fields = '__all__'
        read_only_fields = ['id']


class VarnaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Varna
        fields = '__all__'
        read_only_fields = ['id']


class CasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = '__all__'
        read_only_fields = ['id']


class SubCasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCaste
        fields = '__all__'
        read_only_fields = ['id']
    
    
class GotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gotra
        fields = '__all__'
        read_only_fields = ['id']


class SubGotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGotra
        fields = '__all__'
        read_only_fields = ['id']


class KulSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kul
        fields = '__all__'
        read_only_fields = ['id']
        

class VanshSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vansh
        fields = '__all__'
        read_only_fields = ['id']
        

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = '__all__'
        read_only_fields = ['id']


class PidhiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pidhi
        fields = '__all__'
        read_only_fields = ['id']


# Professional ->
class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'
        read_only_fields = ['id']


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id']


class ProfCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfCategory
        fields = '__all__'
        read_only_fields = ['id']


class ProfSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfSubCategory
        fields = '__all__'
        read_only_fields = ['id']

    
class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = ['id']


class SubSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = '__all__'
        read_only_fields = ['id']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['id']


class SubDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubDepartment
        fields = '__all__'
        read_only_fields = ['id']


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = '__all__'
        read_only_fields = ['id']


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ['id']


class PostModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostModel
        fields = '__all__'
        read_only_fields = ['id']


class RoomFlashSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFlash
        fields = '__all__'
        read_only_fields = ['id']


class ModelNameSerializer(serializers.ModelSerializer):

    class Meta:
        model = ModelName
        fields = ['id', 'model', 'technical_name']
        read_only_fields = ['id','model', 'technical_name']
        
# class RecordRuleAccessInputSerializer(serializers.Serializer):
#     domain_filter = serializers.JSONField()
#     can_read = serializers.BooleanField(default=False)
#     can_create = serializers.BooleanField(default=False)
#     can_write = serializers.BooleanField(default=False)
#     can_delete = serializers.BooleanField(default=False)
    
        
class ModelRuleAccessInputSerializer(serializers.Serializer):
    model_id = serializers.IntegerField()
    model_name = serializers.CharField(read_only=True)
    can_read = serializers.BooleanField(default=False)
    can_create = serializers.BooleanField(default=False)
    can_update = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)
    domain_filter = serializers.JSONField(required=False)

    

class ModelAndRecordRuleAccessInputSerializer(serializers.Serializer):
    user = serializers.IntegerField()  # <-- You need this
    model_access_rule = ModelRuleAccessInputSerializer(many=True)
    

    def create(self, validated_data):
        request_user = self.context["request"].user
        user_id = validated_data.get("user")
        
        # Ensure user exists
        target_user = check_obj_exists(CustomUser, user_id)
        if not isinstance(target_user, CustomUser):
            raise serializers.ValidationError("User does not exist")
        
        # (request_user) main admin designation level = 1, admin disignation level = 0, (1>0) True
        if request_user.is_system_user and target_user.is_system_user:
            if (
                getattr(request_user.designation, "reporting_designation", None)
                and request_user.designation.level > target_user.designation.level
            ):
                raise serializers.ValidationError("You do not have permission to assign access")

        
        model_access_rules = validated_data.get("model_access_rule")
        result = []

        with transaction.atomic():
            for model_rule in model_access_rules:
                model_id = model_rule.get("model_id")
                
                # Ensure model exists
                model_obj = check_obj_exists(ModelName, model_id)
                if not isinstance(model_obj, ModelName):
                    raise serializers.ValidationError("Model does not exist")
                
                # Super Admin of system user
                if request_user.is_system_user and getattr(request_user.designation, "level", None) == 0:
                    pass
                else:
                    validate_assignable_permissions(request_user, model_id, model_rule)
                
                model_access, _ = ModelAccess.objects.update_or_create(
                    user_id=user_id,     # lookup by user + model
                    model_id=model_id,
                    defaults={
                        "can_create": model_rule.get("can_create", False),
                        "can_read": model_rule.get("can_read", False),
                        "can_update": model_rule.get("can_update", False),
                        "can_delete": model_rule.get("can_delete", False),
                    },
                )
                
                domain_filter = model_rule.get("domain_filter", None)
                
                if domain_filter is not None:
                    django_model = apps.get_model(model_obj.app_label, model_obj.model)
                    validate_domain_filter(django_model, domain_filter)
                    
                    
                    record_access, _ = RecordRule.objects.update_or_create(
                        model_id=model_id,
                        domain_filter = domain_filter,
                        defaults={
                            "user": target_user,
                            "can_read": model_rule.get("can_read", False), # default use model rule for record acess rule
                            "can_create": model_rule.get("can_create", False),
                            "can_write": model_rule.get("can_write", False),
                            "can_delete": model_rule.get("can_delete", False),
                        },
                    )
                
                result.append({
                "model_id": model_access.model_id,
                "model_name": model_access.model.technical_name,
                "can_create": model_access.can_create,
                "can_read": model_access.can_read,
                "can_update": model_access.can_update,
                "can_delete": model_access.can_delete,
                "domain_filter": domain_filter
                })
            
        return {
        "user": user_id,
        "model_access_rule": result
    }
        


# ---------------- OUTPUT SERIALIZER (GET) ----------------
class ModelRuleAccessOutputSerializer(serializers.Serializer):
    model_id = serializers.IntegerField()
    model_name = serializers.CharField()
    can_read = serializers.BooleanField()
    can_create = serializers.BooleanField()
    can_update = serializers.BooleanField()
    can_delete = serializers.BooleanField()
    domain_filter = serializers.JSONField(required=False)


class ModelAndRecordRuleAccessOutputSerializer(serializers.Serializer):
    user = serializers.IntegerField(source="id")
    model_access_rule = serializers.SerializerMethodField()

    def get_model_access_rule(self, user_obj):
        model_accesses = ModelAccess.objects.filter(user=user_obj)
        result = []

        for model_access in model_accesses:
            print(user_obj, model_access)
            try:
                record_rule = RecordRule.objects.get(
                    user=user_obj, model=model_access.model
                )
            except RecordRule.DoesNotExist:
                record_rule = None

            result.append({
                "model_id": model_access.model_id,
                "model_name": model_access.model.technical_name,
                "can_read": model_access.can_read,
                "can_create": model_access.can_create,
                "can_update": model_access.can_update,
                "can_delete": model_access.can_delete,
                "domain_filter": record_rule.domain_filter if record_rule else None,
            })
        return result