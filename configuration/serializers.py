from rest_framework import serializers
from .models import *
from shashan.utils.validators import get_object_by_name_or_error
from user_management.models import CustomUser
from .utils import *
from django.apps import apps
from django.db import transaction
from rest_framework.validators import UniqueTogetherValidator

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    Base serializer that allows dynamic exclusion of fields
    via either context={'exclude_fields': [...]} or argument exclude_fields=[...].
    """
    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', None)
        super().__init__(*args, **kwargs)

        if exclude_fields is None:
            exclude_fields = self.context.get('exclude_fields', [])

        for field in exclude_fields:
            self.fields.pop(field, None)


# =================================================
# Residential 
# =================================================
class GlobSerializer(DynamicFieldsModelSerializer):
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


class ContinentDetailSerializer(DynamicFieldsModelSerializer):
    glob = serializers.SerializerMethodField()
    class Meta:
        model = Continent
        fields = '__all__'
        read_only_fields = ['id']
    
    def get_glob(self, obj):
        serializer = GlobSerializer(
            obj.glob,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


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

class CountryDetailSerializer(DynamicFieldsModelSerializer):
    continent = serializers.SerializerMethodField()
    class Meta:
        model = Country
        fields = '__all__'
        read_only_fields = [f for f in Country._meta.fields]
    
    def get_continent(self, obj):
        serializer = ContinentDetailSerializer(
            obj.continent,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


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


class StateDetailSerializer(DynamicFieldsModelSerializer):
    country = serializers.SerializerMethodField()
    class Meta:
        model = State
        fields = '__all__'
        read_only_fields = [f for f in State._meta.fields]
    
    def get_country(self, obj):
        serializer = CountryDetailSerializer(
            obj.country,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data
    
    
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


class DistrictDetailSerializer(DynamicFieldsModelSerializer):
    state = serializers.SerializerMethodField()
    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = [f for f in District._meta.fields]
    
    def get_state(self, obj):
        serializer = StateDetailSerializer(
            obj.state,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


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


class TalukaDetailSerializer(DynamicFieldsModelSerializer):
    district = serializers.SerializerMethodField()
    class Meta:
        model = Taluka
        fields = '__all__'
        read_only_fields = [f for f in Taluka._meta.fields]
    
    def get_district(self, obj):
        serializer = DistrictDetailSerializer(
            obj.district,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


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


class CityVillageDetailSerializer(DynamicFieldsModelSerializer):
    taluka = serializers.SerializerMethodField()
    class Meta:
        model = CityVillage
        fields = '__all__'
        read_only_fields = [f for f in CityVillage._meta.fields]
    
    def get_taluka(self, obj):
        serializer = TalukaDetailSerializer(
            obj.taluka,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data

    
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


class WardDetailSerializer(DynamicFieldsModelSerializer):
    city_village = serializers.SerializerMethodField()
    class Meta:
        model = Ward
        fields = '__all__'
        read_only_fields = [f for f in Ward._meta.fields]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure our method field overrides model FK field
        self.fields['city_village'] = serializers.SerializerMethodField()
    
    def get_city_village(self, obj):
        if not obj.city_village:
            return None
        serializer = CityVillageDetailSerializer(
            obj.city_village,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data

# ======================================================
# Personal 
# ======================================================
class ReligionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Religion
        fields = '__all__'
        read_only_fields = ['id']


class SampradaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Sampraday
        fields = '__all__'
        read_only_fields = ['id']

class SampradayDetailSerializer(DynamicFieldsModelSerializer):
    religion = serializers.SerializerMethodField()
    class Meta:
        model = Sampraday
        fields = '__all__'
        read_only_fields = [f for f in Sampraday._meta.fields]
    
    def get_religion(self, obj):
        serializer = ReligionSerializer(
            obj.religion,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class PanthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Panth
        fields = '__all__'
        read_only_fields = ['id']
        
class PanthDetailSerializer(DynamicFieldsModelSerializer):
    sampraday = serializers.SerializerMethodField()
    class Meta:
        model = Panth
        fields = '__all__'
        read_only_fields = [f for f in Panth._meta.fields]
    
    def get_sampraday(self, obj):
        serializer = SampradayDetailSerializer(
            obj.sampraday,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class VarnaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Varna
        fields = '__all__'
        read_only_fields = ['id']

class VarnaDetailSerializer(DynamicFieldsModelSerializer):
    panth = serializers.SerializerMethodField()
    class Meta:
        model = Varna
        fields = '__all__'
        read_only_fields = [f for f in Varna._meta.fields]
    
    def get_panth(self, obj):
        serializer = PanthDetailSerializer(
            obj.panth,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class CasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = '__all__'
        read_only_fields = ['id']

class CasteDetailSerializer(DynamicFieldsModelSerializer):
    varna = serializers.SerializerMethodField()
    class Meta:
        model = Caste
        fields = '__all__'
        read_only_fields = [f for f in Caste._meta.fields]
    
    def get_varna(self, obj):
        serializer = VarnaDetailSerializer(
            obj.varna,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class SubCasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCaste
        fields = '__all__'
        read_only_fields = ['id']

class SubCasteDetailSerializer(DynamicFieldsModelSerializer):
    caste = serializers.SerializerMethodField()
    class Meta:
        model = SubCaste
        fields = '__all__'
        read_only_fields = [f for f in SubCaste._meta.fields]
    
    def get_caste(self, obj):
        serializer = CasteDetailSerializer(
            obj.caste,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data
    
    
class GotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gotra
        fields = '__all__'
        read_only_fields = ['id']

class GotraDetailSerializer(DynamicFieldsModelSerializer):
    subcaste = serializers.SerializerMethodField()
    class Meta:
        model = Gotra
        fields = '__all__'
        read_only_fields = [f for f in Gotra._meta.fields]
    
    def get_subcaste(self, obj):
        serializer = SubCasteDetailSerializer(
            obj.subcaste,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class SubGotraSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGotra
        fields = '__all__'
        read_only_fields = ['id']

class SubGotraDetailSerializer(DynamicFieldsModelSerializer):
    gotra = serializers.SerializerMethodField()
    class Meta:
        model = SubGotra
        fields = '__all__'
        read_only_fields = [f for f in SubGotra._meta.fields]
    
    def get_gotra(self, obj):
        serializer = GotraDetailSerializer(
            obj.gotra,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class KulSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kul
        fields = '__all__'
        read_only_fields = ['id']

class KulDetailSerializer(DynamicFieldsModelSerializer):
    subgotra = serializers.SerializerMethodField()
    class Meta:
        model = Kul
        fields = '__all__'
        read_only_fields = [f for f in Kul._meta.fields]
    
    def get_subgotra(self, obj):
        serializer = SubGotraDetailSerializer(
            obj.subgotra,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data
        

class VanshSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vansh
        fields = '__all__'
        read_only_fields = ['id']

class VanshDetailSerializer(DynamicFieldsModelSerializer):
    kul = serializers.SerializerMethodField()
    class Meta:
        model = Vansh
        fields = '__all__'
        read_only_fields = [f for f in Vansh._meta.fields]
    
    def get_kul(self, obj):
        serializer = KulDetailSerializer(
            obj.kul,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data
        

class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = '__all__'
        read_only_fields = ['id']

class FamilyDetailSerializer(DynamicFieldsModelSerializer):
    vansh = serializers.SerializerMethodField()
    class Meta:
        model = Family
        fields = '__all__'
        read_only_fields = [f for f in Family._meta.fields]
    
    def get_vansh(self, obj):
        serializer = VanshDetailSerializer(
            obj.vansh,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class PidhiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pidhi
        fields = '__all__'
        read_only_fields = ['id']

class PidhiDetailSerializer(DynamicFieldsModelSerializer):
    family = serializers.SerializerMethodField()
    class Meta:
        model = Pidhi
        fields = '__all__'
        read_only_fields = [f for f in Pidhi._meta.fields]
    
    def get_family(self, obj):
        serializer = FamilyDetailSerializer(
            obj.family,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data

# ===================================================
# Professional 
# ===================================================
class SectionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Section
        fields = '__all__'
        read_only_fields = ['id']


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = ['id']

class ClassDetailSerializer(DynamicFieldsModelSerializer):
    section = serializers.SerializerMethodField()
    class Meta:
        model = Class
        fields = '__all__'
        read_only_fields = [f for f in Class._meta.fields]
    
    def get_section(self, obj):
        serializer = SectionSerializer(
            obj.section,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class ProfCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfCategory
        fields = '__all__'
        read_only_fields = ['id']

class ProfCategoryDetailSerializer(DynamicFieldsModelSerializer):
    profclass = serializers.SerializerMethodField()
    class Meta:
        model = ProfCategory
        fields = '__all__'
        read_only_fields = [f for f in ProfCategory._meta.fields]
    
    def get_profclass(self, obj):
        serializer = ClassDetailSerializer(
            obj.profclass,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data
        


class ProfSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfSubCategory
        fields = '__all__'
        read_only_fields = ['id']

class ProfSubCategoryDetailSerializer(DynamicFieldsModelSerializer):
    category = serializers.SerializerMethodField()
    class Meta:
        model = ProfSubCategory
        fields = '__all__'
        read_only_fields = [f for f in ProfSubCategory._meta.fields]
    
    def get_category(self, obj):
        serializer = ProfCategoryDetailSerializer(
            obj.category,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data
    
    
class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = ['id']

class SectorDetailSerializer(DynamicFieldsModelSerializer):
    subcategory = serializers.SerializerMethodField()
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = [f for f in Sector._meta.fields]
    
    def get_subcategory(self, obj):
        serializer = ProfSubCategoryDetailSerializer(
            obj.subcategory,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class SubSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = '__all__'
        read_only_fields = ['id']

class SubSectorDetailSerializer(DynamicFieldsModelSerializer):
    sector = serializers.SerializerMethodField()
    class Meta:
        model = SubSector
        fields = '__all__'
        read_only_fields = [f for f in SubSector._meta.fields]
    
    def get_sector(self, obj):
        serializer = SectorDetailSerializer(
            obj.sector,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['id']

class DepartmentDetailSerializer(DynamicFieldsModelSerializer):
    subsector = serializers.SerializerMethodField()
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = [f for f in Department._meta.fields]
    
    def get_subsector(self, obj):
        serializer = SubSectorDetailSerializer(
            obj.subsector,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class SubDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubDepartment
        fields = '__all__'
        read_only_fields = ['id']

class SubDepartmentDetailSerializer(DynamicFieldsModelSerializer):
    department = serializers.SerializerMethodField()
    class Meta:
        model = SubDepartment
        fields = '__all__'
        read_only_fields = [f for f in SubDepartment._meta.fields]
    
    def get_department(self, obj):
        serializer = DepartmentDetailSerializer(
            obj.department,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = '__all__'
        read_only_fields = ['id']

class TypeDetailSerializer(DynamicFieldsModelSerializer):
    subdepartment = serializers.SerializerMethodField()
    class Meta:
        model = Type
        fields = '__all__'
        read_only_fields = [f for f in Type._meta.fields]
    
    def get_subdepartment(self, obj):
        serializer = SubDepartmentDetailSerializer(
            obj.subdepartment,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = ['id']

class BrandDetailSerializer(DynamicFieldsModelSerializer):
    type = serializers.SerializerMethodField()
    class Meta:
        model = Brand
        fields = '__all__'
        read_only_fields = [f for f in Brand._meta.fields]
    
    def get_type(self, obj):
        serializer = TypeDetailSerializer(
            obj.type,
            context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
        )
        return serializer.data

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'
        read_only_fields = ['id']


        
# class PostModelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PostModel
#         fields = '__all__'
#         read_only_fields = ['id']

# class PostModelDetailSerializer(DynamicFieldsModelSerializer):
#     brand = serializers.SerializerMethodField()
#     class Meta:
#         model = PostModel
#         fields = '__all__'
#         read_only_fields = [f.name for f in PostModel._meta.fields]
    
#     def get_brand(self, obj):
#         serializer = BrandDetailSerializer(
#             obj.brand,
#             context={'exclude_fields': ['is_hidden', 'on_hold', 'hold_date']}
#         )
#         return serializer.data


class RoomFlashSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFlash
        fields = '__all__'
        read_only_fields = ['id']

class RoomFlashNameCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFlash
        fields = ['name', 'code']


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFlash
        fields = '__all__'
        read_only_fields = ['id']

class RoomTypeNameCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFlash
        fields = ['name', 'code']

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



class ResidentialSearchInputSerializer(serializers.Serializer):
    glob = serializers.CharField(required=False, allow_blank=True)
    continent = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    district = serializers.CharField(required=False, allow_blank=True)
    taluka = serializers.CharField(required=False, allow_blank=True)
    city_village = serializers.CharField(required=False, allow_blank=True)
    ward = serializers.CharField(required=False, allow_blank=True)
    search_key = serializers.CharField(required=False, allow_blank=True)

class GlobIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Glob
        fields = ["id", "name"]

class ContinentIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Continent
        fields = ["id", "name"]

class CountryIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]

class StateIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name"]

class DistrictIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]

class TalukaIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Taluka
        fields = ["id", "name"]

class CityVillageIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CityVillage
        fields = ["id", "name"]

class WardIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ["id", "name"]
    
# Residential Unified Output Serializer (always same structure)
class ResidentialOutputSerializer(serializers.Serializer):
    glob = GlobIdNameSerializer(allow_null=True)
    continent = ContinentIdNameSerializer(allow_null=True)
    country = CountryIdNameSerializer(allow_null=True)
    state = StateIdNameSerializer(allow_null=True)
    district = DistrictIdNameSerializer(allow_null=True)
    taluka = TalukaIdNameSerializer(allow_null=True)
    city_village = CityVillageIdNameSerializer(allow_null=True)
    ward = WardIdNameSerializer(allow_null=True)

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    

class ReligionIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Religion
        fields = ["id", "name"]

class SampradayIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sampraday
        fields = ["id", "name"]

class PanthIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Panth
        fields = ["id", "name"]

class VarnaIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Varna
        fields = ["id", "name"]

class CasteIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caste
        fields = ["id", "name"]

class SubCasteIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCaste
        fields = ["id", "name"]

class GotraIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gotra
        fields = ["id", "name"]

class SubGotraIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubGotra
        fields = ["id", "name"]

class KulIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kul
        fields = ["id", "name"]

class VanshIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vansh
        fields = ["id", "name"]

class FamilyIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ["id", "name"]

class PidhiIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pidhi
        fields = ["id", "name"]

class PersonalInputSerializer(serializers.Serializer):
    religion = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    sampraday = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    panth = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    varna = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    caste = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subcaste = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    gotra = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subgotra = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    kul = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    vansh = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    family = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    pidhi = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    search_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class PersonalOutputSerializer(serializers.Serializer):
    religion = ReligionIdNameSerializer(allow_null=True)
    sampraday = SampradayIdNameSerializer(allow_null=True)
    panth = PanthIdNameSerializer(allow_null=True)
    varna = VarnaIdNameSerializer(allow_null=True)
    caste = CasteIdNameSerializer(allow_null=True)
    subcaste = SubCasteIdNameSerializer(allow_null=True)
    gotra = GotraIdNameSerializer(allow_null=True)
    subgotra = SubGotraIdNameSerializer(allow_null=True)
    kul = KulIdNameSerializer(allow_null=True)
    vansh = VanshIdNameSerializer(allow_null=True)
    family = FamilyIdNameSerializer(allow_null=True)
    pidhi = PidhiIdNameSerializer(allow_null=True)


class SectionIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ["id", "name"]

class ClassIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ["id", "name"]

class ProfCategoryIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfCategory
        fields = ["id", "name"]

class ProfSubCategoryIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfSubCategory
        fields = ["id", "name"]

class SectorIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["id", "name"]

class SubSectorIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = ["id", "name"]

class DepartmentIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]

class SubDepartmentIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubDepartment
        fields = ["id", "name"]

class TypeIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Type
        fields = ["id", "name"]

class BrandIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name"]

# class PostModelIdNameSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PostModel
#         fields = ["id", "name"]

class ProfessionalInputSerializer(serializers.Serializer):
    section = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    profclass = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    category = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subcategory = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    sector = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subsector = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    department = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    subdepartment = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    type = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    brand = serializers.CharField(required=False, allow_blank=True,  allow_null=True)
    search_key = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class ProfessionalOutputSerializer(serializers.Serializer):
    section = SectionIdNameSerializer(allow_null=True)
    profclass = ClassIdNameSerializer(allow_null=True)
    category = ProfCategoryIdNameSerializer(allow_null=True)
    subcategory = ProfSubCategoryIdNameSerializer(allow_null=True)
    sector = SectorIdNameSerializer(allow_null=True)
    subsector = SubSectorIdNameSerializer(allow_null=True)
    department = DepartmentIdNameSerializer(allow_null=True)
    subdepartment = SubDepartmentIdNameSerializer(allow_null=True)
    type = TypeIdNameSerializer(allow_null=True)
    brand = BrandIdNameSerializer(allow_null=True)


class DesignationIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = ["id", "name", "code"]


class DesignationSerializer(serializers.ModelSerializer):
    # access id in input...
    reporting_designation = serializers.PrimaryKeyRelatedField(
        queryset=Designation.objects.all(),
        required=False,
        allow_null=True
    )
    class Meta:
        model = Designation
        fields = "__all__"
        read_only_fields = ["id"]
        validators = [
            UniqueTogetherValidator(
                queryset=Designation.objects.all(),
                fields=['category', 'name'],
                message="A continent with this name already exists in the selected category.",
            )
        ]
        # extra_kwargs = {
        #     'code': {'required': False}
        # }
    
    def to_representation(self, instance):
        """
        Override output representation — show nested reporting_designation.
        """
        data = super().to_representation(instance)
        if instance.reporting_designation:
            data["reporting_designation"] = {
                "id": instance.reporting_designation.id,
                "name": instance.reporting_designation.name,
            }
        else:
            data["reporting_designation"] = None
        return data
    
    def validate_name(self, value):
        """
        Validate that name does not contain special characters.
        Allow only letters, numbers, and spaces.
        """
        if not re.match(r'^[A-Za-z ]+$', value):
            raise serializers.ValidationError(
                "Name can only contain letters and spaces."
            )
        return value
    
    def validate(self, attrs):        
        code = attrs.get('code')
        reporting_designation = attrs.get('reporting_designation')

        if code is not None:
            # Case 1: User *provided* a code.
            # We just need to validate it.
            if code == 0 and (attrs.get('name') != 'self' or attrs.get('name') != 'Self'):
                    raise serializers.ValidationError({"code": "Invalid post no. Cannot be 0."})
            # The provided code is fine, so we'll use it.
            attrs['code'] = code
        
        else:
            # Case 2: User did *not* provide a code.
            # We will set it based on your logic.
            if reporting_designation:
                # Set code = parent's code + 1
                attrs['code'] = reporting_designation.code + 1
            else:
                # Set code = 1 (for top-level designations)
                attrs['code'] = 1

        return attrs
