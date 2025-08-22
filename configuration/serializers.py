from rest_framework import serializers
from .models import *
from shashan.utils.validators import get_object_by_name_or_error

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

class AccessesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accesses
        fields = '__all__'

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

