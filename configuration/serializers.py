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

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ReligionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Religion
        fields = '__all__'

class SampradaySerializer(serializers.ModelSerializer):
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
    class Meta:
        model = Varna
        fields = '__all__'

class CasteSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = Pidhi
        fields = '__all__'

    def validate_subgotra(self, value):
        return get_object_by_name_or_error(SubGotra, value)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
