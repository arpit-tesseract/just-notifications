from rest_framework import serializers
from .models import *
from shashan.utils.validators import get_object_by_name_or_error
from user_management.models import CustomUser
from .utils import *
from django.apps import apps
from django.db import transaction

class ContinentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):
    continent = serializers.CharField(required=True)
    class Meta:
        model = Country
        fields = '__all__'

    def validate_continent(self, value):
        return get_object_by_name_or_error(Continent, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class StateSerializer(serializers.ModelSerializer):
    country = serializers.CharField(required=False)
    class Meta:
        model = State
        fields = '__all__'
    
    def validate_country(self, value):
        return get_object_by_name_or_error(Country, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class DistrictSerializer(serializers.ModelSerializer):
    state = serializers.CharField(required=False)

    class Meta:
        model = District
        fields = '__all__'

    def validate_state(self, value):
        return get_object_by_name_or_error(State, value)
    
    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class CitySerializer(serializers.ModelSerializer):
    district = serializers.CharField(required=False)

    class Meta:
        model = City
        fields = '__all__'

    def validate_district(self, value):
        return get_object_by_name_or_error(District, value)
    
    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class VillageSerializer(serializers.ModelSerializer):
    district = serializers.CharField(required=True)
    city = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Village
        fields = '__all__'

    def validate_district(self, value):
        return get_object_by_name_or_error(District, value)

    def validate_city(self, value):
        if value:
            return get_object_by_name_or_error(City, value)
        return None

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class WardSerializer(serializers.ModelSerializer):
    city = serializers.CharField(required=False, allow_null=True)
    village = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Ward
        fields = '__all__'

    def validate_village(self, value):
        return get_object_by_name_or_error(Village, value)
    
    def validate_city(self,value):
        return get_object_by_name_or_error(City, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class SocietySerializer(serializers.ModelSerializer):
    ward = serializers.CharField(required=True)

    class Meta:
        model = Society
        fields = '__all__'

    def validate_ward(self, value):
        return get_object_by_name_or_error(Ward, value, "code")

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class BlockSerializer(serializers.ModelSerializer):
    society = serializers.CharField(required=True)

    class Meta:
        model = Block
        fields = '__all__'

    def validate_society(self, value):
        return get_object_by_name_or_error(Society, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class HousesSerializer(serializers.ModelSerializer):
    block = serializers.CharField(required=True)

    class Meta:
        model = Houses
        fields = '__all__'

    def validate_block(self, value):
        return get_object_by_name_or_error(Block, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
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

class ReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Religion
        fields = '__all__'

class SampradaySerializer(serializers.ModelSerializer):
    religion = serializers.CharField(required=True)

    class Meta:
        model = Sampraday
        fields = '__all__'

    def validate_religion(self, value):
        return get_object_by_name_or_error(Religion, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class PanthSerializer(serializers.ModelSerializer):
    sampraday = serializers.CharField(required=True)

    class Meta:
        model = Panth
        fields = '__all__'

    def validate_sampraday(self, value):
        return get_object_by_name_or_error(Sampraday, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class VarnaSerializer(serializers.ModelSerializer):
    panth = serializers.CharField(required=True)
    class Meta:
        model = Varna
        fields = '__all__'

    def validate_panth(self, value):
        return get_object_by_name_or_error(Panth, value)
    
    def create(self, validated_data):
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class CasteSerializer(serializers.ModelSerializer):
    varna = serializers.CharField(required=True)

    class Meta:
        model = Caste
        fields = '__all__'

    def validate_varna(self, value):
        return get_object_by_name_or_error(Varna, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class SubCasteSerializer(serializers.ModelSerializer):
    caste = serializers.CharField(required=True)

    class Meta:
        model = SubCaste
        fields = '__all__'
    
    def validate_caste(self, value):
        return get_object_by_name_or_error(Caste, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class GotraSerializer(serializers.ModelSerializer):
    subcaste = serializers.CharField(required=True)

    class Meta:
        model = Gotra
        fields = '__all__'

    def validate_subcaste(self, value):
        return get_object_by_name_or_error(SubCaste, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class SubGotraSerializer(serializers.ModelSerializer):
    gotra = serializers.CharField(required=True)

    class Meta:
        model = SubGotra
        fields = '__all__'

    def validate_gotra(self, value):
        return get_object_by_name_or_error(Gotra, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class PidhiSerializer(serializers.ModelSerializer):
    subgotra = serializers.CharField(required=True)

    class Meta:
        model = Pidhi
        fields = '__all__'

    def validate_subgotra(self, value):
        return get_object_by_name_or_error(SubGotra, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'

class ClassSerializer(serializers.ModelSerializer):
    section = serializers.CharField(required=True)

    class Meta:
        model = Class
        fields = '__all__'

    def validate_section(self, value):
        return get_object_by_name_or_error(Section, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class ProfCategorySerializer(serializers.ModelSerializer):
    profclass = serializers.CharField(required=True)

    class Meta:
        model = ProfCategory
        fields = '__all__'

    def validate_profclass(self, value):
        return get_object_by_name_or_error(Class, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class ProfSubCategorySerializer(serializers.ModelSerializer):
    category = serializers.CharField(required=True)

    class Meta:
        model = ProfSubCategory
        fields = '__all__'

    def validate_category(self, value):
        return get_object_by_name_or_error(ProfCategory, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
class SectorSerializer(serializers.ModelSerializer):
    subcategory = serializers.CharField(required=True)

    class Meta:
        model = Sector
        fields = '__all__'

    def validate_subcategory(self, value):
        return get_object_by_name_or_error(ProfSubCategory, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class SubSectorSerializer(serializers.ModelSerializer):
    sector = serializers.CharField(required=True)

    class Meta:
        model = SubSector
        fields = '__all__'

    def validate_sector(self, value):
        return get_object_by_name_or_error(Sector, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class DepartmentSerializer(serializers.ModelSerializer):
    subsector = serializers.CharField(required=True)

    class Meta:
        model = Department
        fields = '__all__'

    def validate_subsector(self, value):
        return get_object_by_name_or_error(SubSector, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class SubDepartmentSerializer(serializers.ModelSerializer):
    department = serializers.CharField(required=True)

    class Meta:
        model = SubDepartment
        fields = '__all__'

    def validate_department(self, value):
        return get_object_by_name_or_error(Department, value)
    
    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class TypeSerializer(serializers.ModelSerializer):
    subdepartment = serializers.CharField(required=True)

    class Meta:
        model = Type
        fields = '__all__'

    def validate_subdepartment(self, value):
        return get_object_by_name_or_error(SubDepartment, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class BrandSerializer(serializers.ModelSerializer):
    type = serializers.CharField(required=True)

    class Meta:
        model = Brand
        fields = '__all__'

    def validate_type(self, value):
        return get_object_by_name_or_error(Type, value)
    
    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class PostModelSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(required=True)

    class Meta:
        model = PostModel
        fields = '__all__'

    def validate_brand(self, value):
        return get_object_by_name_or_error(Brand, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class RoomFlashSerializer(serializers.ModelSerializer):

    class Meta:
        model = RoomFlash
        fields = '__all__'


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