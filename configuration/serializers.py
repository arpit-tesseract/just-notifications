from rest_framework import serializers
from .models import *
from shashan.utils.validators import get_object_by_name_or_error
from user_management.models import CustomUser
from .utils import *
from django.apps import apps
from django.db import transaction
from rest_framework.validators import UniqueTogetherValidator

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
        validators = [
            UniqueTogetherValidator(
                queryset=Continent.objects.all(),
                fields=['glob', 'name'],
                message="A continent with this name already exists in the selected glob.",
            )
        ]


class ContinentDetailSerializer(serializers.ModelSerializer):
    glob = GlobSerializer()
    class Meta:
        model = Continent
        fields = '__all__'
        read_only_fields = [f for f in Continent._meta.fields]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Country.objects.all(),
                fields=['continent', 'name'],
                message="A country with this name already exists in the selected continent.",
            )
        ]

class CountryDetailSerializer(serializers.ModelSerializer):
    continent = ContinentDetailSerializer()
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = [f for f in Country._meta.fields]


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=State.objects.all(),
                fields=['country', 'name'],
                message="A state with this name already exists in the selected country.",
            )
        ]


class StateDetailSerializer(serializers.ModelSerializer):
    country = CountryDetailSerializer()
    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = [f for f in State._meta.fields]
    
    
class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=District.objects.all(),
                fields=['state', 'name'],
                message="A district with this name already exists in the selected state.",
            )
        ]


class DistrictDetailSerializer(serializers.ModelSerializer):
    state = StateDetailSerializer()
    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = [f for f in District._meta.fields]


class TalukaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taluka
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Taluka.objects.all(),
                fields=['district', 'name'],
                message="A taluka with this name already exists in the selected district.",
            )
        ]


class TalukaDetailSerializer(serializers.ModelSerializer):
    district = DistrictDetailSerializer()
    class Meta:
        model = Taluka
        fields = '__all__'
        read_only_fields = [f for f in Taluka._meta.fields]


class CityVillageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityVillage
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=CityVillage.objects.all(),
                fields=['taluka', 'name'],
                message="A city/village with this name already exists in the selected taluka.",
            )
        ]


class CityVillageDetailSerializer(serializers.ModelSerializer):
    taluka = TalukaDetailSerializer()
    class Meta:
        model = CityVillage
        fields = '__all__'
        read_only_fields = [f for f in CityVillage._meta.fields]

    
class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Ward.objects.all(),
                fields=['city_village', 'name'],
                message="A ward with this name already exists in the selected city/village.",
            )
        ]


class WardDetailSerializer(serializers.ModelSerializer):
    city_village = CityVillageDetailSerializer()
    class Meta:
        model = Ward
        fields = '__all__'
        read_only_fields = [f for f in Ward._meta.fields]

    
class SocietySerializer(serializers.ModelSerializer):
    class Meta:
        model = Society
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Society.objects.all(),
                fields=['ward', 'name'],
                message="A society with this name already exists in the selected ward.",
            )
        ]


class SocietyDetailSerializer(serializers.ModelSerializer):
    ward = WardDetailSerializer()
    class Meta:
        model = Society
        fields = '__all__'
        read_only_fields = [f for f in Society._meta.fields]


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Block.objects.all(),
                fields=['society', 'name'],
                message="A block with this name already exists in the selected society.",
            )
        ]

class BlockDetailSerializer(serializers.ModelSerializer):
    society = SocietyDetailSerializer()
    class Meta:
        model = Block
        fields = '__all__'
        read_only_fields = [f for f in Block._meta.fields]

    
class FloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Floor.objects.all(),
                fields=['block', 'name'],
                message="A floor with this name already exists in the selected block.",
            )
        ]

class FloorDetailSerializer(serializers.ModelSerializer):
    block = BlockDetailSerializer()
    class Meta:
        model = Floor
        fields = '__all__'
        read_only_fields = [f for f in Floor._meta.fields]
    
    
class HousesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Houses
        fields = '__all__'
        read_only_fields = ['id']
        validators = [
            UniqueTogetherValidator(
                queryset=Houses.objects.all(),
                fields=['floor', 'code'],
                message="A house with this code already exists in the selected floor.",
            )
        ]

class HousesDetailSerializer(serializers.ModelSerializer):
    floor = FloorDetailSerializer()
    class Meta:
        model = Houses
        fields = '__all__'
        read_only_fields = [f for f in Houses._meta.fields]

    

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

class SampradayDetailSerializer(serializers.ModelSerializer):
    religion = ReligionSerializer()
    class Meta:
        model = Sampraday
        fields = '__all__'
        read_only_fields = [f for f in Sampraday._meta.fields]


class PanthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Panth
        fields = '__all__'
        read_only_fields = ['id']
        
class PanthDetailSerializer(serializers.ModelSerializer):
    sampraday = SampradayDetailSerializer()
    class Meta:
        model = Panth
        fields = '__all__'
        read_only_fields = [f for f in Panth._meta.fields]


class VarnaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Varna
        fields = '__all__'
        read_only_fields = ['id']

class VarnaDetailSerializer(serializers.ModelSerializer):
    panth = PanthDetailSerializer()
    class Meta:
        model = Varna
        fields = '__all__'
        read_only_fields = [f for f in Varna._meta.fields]


class CasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = '__all__'
        read_only_fields = ['id']

class CasteDetailSerializer(serializers.ModelSerializer):
    varna = VarnaDetailSerializer()
    class Meta:
        model = Caste
        fields = '__all__'
        read_only_fields = [f for f in Caste._meta.fields]


class SubCasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCaste
        fields = '__all__'
        read_only_fields = ['id']

class SubCasteDetailSerializer(serializers.ModelSerializer):
    caste = CasteDetailSerializer()
    class Meta:
        model = SubCaste
        fields = '__all__'
        read_only_fields = [f for f in SubCaste._meta.fields]
    
    
class GotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gotra
        fields = '__all__'
        read_only_fields = ['id']

class GotraDetailSerializer(serializers.ModelSerializer):
    caste = CasteDetailSerializer()
    class Meta:
        model = Gotra
        fields = '__all__'
        read_only_fields = [f for f in Gotra._meta.fields]


class SubGotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGotra
        fields = '__all__'
        read_only_fields = ['id']

class SubGotraDetailSerializer(serializers.ModelSerializer):
    gotra = GotraDetailSerializer()
    class Meta:
        model = SubGotra
        fields = '__all__'
        read_only_fields = [f for f in SubGotra._meta.fields]


class KulSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kul
        fields = '__all__'
        read_only_fields = ['id']

class KulDetailSerializer(serializers.ModelSerializer):
    caste = CasteDetailSerializer()
    class Meta:
        model = Kul
        fields = '__all__'
        read_only_fields = [f for f in Kul._meta.fields]
        

class VanshSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vansh
        fields = '__all__'
        read_only_fields = ['id']

class VanshDetailSerializer(serializers.ModelSerializer):
    caste = CasteDetailSerializer()
    class Meta:
        model = Vansh
        fields = '__all__'
        read_only_fields = [f for f in Vansh._meta.fields]
        

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = '__all__'
        read_only_fields = ['id']

class FamilyDetailSerializer(serializers.ModelSerializer):
    caste = CasteDetailSerializer()
    class Meta:
        model = Family
        fields = '__all__'
        read_only_fields = [f for f in Family._meta.fields]


class PidhiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pidhi
        fields = '__all__'
        read_only_fields = ['id']

class PidhiDetailSerializer(serializers.ModelSerializer):
    caste = CasteDetailSerializer()
    class Meta:
        model = Pidhi
        fields = '__all__'
        read_only_fields = [f for f in Pidhi._meta.fields]


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

class ClassDetailSerializer(serializers.ModelSerializer):
    section = SectionSerializer()
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = [f for f in Class._meta.fields]


class ProfCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfCategory
        fields = '__all__'
        read_only_fields = ['id']

class ProfCategoryDetailSerializer(serializers.ModelSerializer):
    profclass = ClassDetailSerializer()
    class Meta:
        model = ProfCategory
        fields = '__all__'
        read_only_fields = [f for f in ProfCategory._meta.fields]
        


class ProfSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfSubCategory
        fields = '__all__'
        read_only_fields = ['id']

class ProfSubCategoryDetailSerializer(serializers.ModelSerializer):
    category = ProfCategoryDetailSerializer()
    class Meta:
        model = ProfSubCategory
        fields = '__all__'
        read_only_fields = [f for f in ProfSubCategory._meta.fields]

    
class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = ['id']

class SectorDetailSerializer(serializers.ModelSerializer):
    subcategory = ProfSubCategoryDetailSerializer()
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = [f for f in Sector._meta.fields]


class SubSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = '__all__'
        read_only_fields = ['id']

class SubSectorDetailSerializer(serializers.ModelSerializer):
    sector = SectorDetailSerializer()
    class Meta:
        model = SubSector
        fields = '__all__'
        read_only_fields = [f for f in SubSector._meta.fields]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['id']

class DepartmentDetailSerializer(serializers.ModelSerializer):
    subsector = SubSectorDetailSerializer()
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = [f for f in Department._meta.fields]


class SubDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubDepartment
        fields = '__all__'
        read_only_fields = ['id']

class SubDepartmentDetailSerializer(serializers.ModelSerializer):
    department = DepartmentDetailSerializer()
    class Meta:
        model = SubDepartment
        fields = '__all__'
        read_only_fields = [f for f in SubDepartment._meta.fields]


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = '__all__'
        read_only_fields = ['id']

class TypeDetailSerializer(serializers.ModelSerializer):
    subdepartment = SubDepartmentDetailSerializer()
    class Meta:
        model = Type
        fields = '__all__'
        read_only_fields = [f for f in Type._meta.fields]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ['id']

class BrandDetailSerializer(serializers.ModelSerializer):
    type = TypeDetailSerializer()
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = [f for f in Brand._meta.fields]


class PostModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostModel
        fields = '__all__'
        read_only_fields = ['id']

class PostModelDetailSerializer(serializers.ModelSerializer):
    brand = BrandDetailSerializer()
    class Meta:
        model = PostModel
        fields = '__all__'
        read_only_fields = [f for f in PostModel._meta.fields]


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