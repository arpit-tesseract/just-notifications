from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .permissions import HasModelAccessPermission
from .utils import read_file, normalize_bool, get_regular_query, calculate_hidden_hold
from .mixins import FilteredQuerysetMixin, RecordRuleMixin
from .pagination import ConfigurationPagination
from configuration.serializers import *
from .models import *
import pandas as pd

# CRUD Views
# ========================================
# Residential 
# ========================================
class GlobViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Glob.objects.none() # First time load data when server starts
    model = Glob 
    serializer_class = GlobSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GlobSerializer   # For POST, PUT, PATCH
        return GlobDetailSerializer

# class GlobListView(SearchMixin, RecordRuleMixin, APIView): # MRO goes: SearchMixin → RecordRuleMixin → SafeQueryMixin.
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]
#     def get_base_queryset(self):
#         return get_regular_query(Glob)
    
#     def get(self, request):
#         queryset = self.get_result_queryset()   # search applied automatically
#         serializer = GlobIdNameSerializer(queryset, many=True)
#         return Response(serializer.data)
# GlobListView
#  ├── SearchMixin
#  │    └── super().get_queryset()
#  │         ↳ RecordRuleMixin
#  │              └── super().get_queryset()
#  │                   ↳ BaseQueryMixin
#  │                        ↳ get_base_queryset()   (from GlobListView) 

# Ordered resolution:
# GlobListView.get_base_queryset() →
# RecordRuleMixin.get_queryset() (applies rules) →
# SearchMixin.get_result_queryset() (applies search).   

class ContinentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Continent
    queryset = Continent.objects.none()
    serializer_class = ContinentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'glob': 'glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Continent.objects.select_related('glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ContinentSerializer   # For POST, PUT, PATCH
        return ContinentDetailSerializer
    

class CountryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Country
    queryset = Country.objects.none()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'continent': 'continent__id',
        'glob': 'continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Country.objects.select_related('continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CountrySerializer   # For POST, PUT, PATCH
        return CountryDetailSerializer
    

class StateViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = State
    queryset = State.objects.none()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'country': 'country__id',
        'continent': 'country__continent__id',
        'glob': 'country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = State.objects.select_related('country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return StateSerializer   # For POST, PUT, PATCH
        return StateDetailSerializer
   
   
class DistrictViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = District
    queryset = District.objects.none()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'state': 'state__id',
        'country': 'state__country__id',
        'continent': 'state__country__continent__id',
        'glob': 'state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = District.objects.select_related('state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DistrictSerializer   # For POST, PUT, PATCH
        return DistrictDetailSerializer


class TalukaViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Taluka
    queryset = Taluka.objects.none()
    serializer_class = TalukaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'district': 'district__id',
        'state': 'district__state__id',
        'country': 'district__state__country__id',
        'continent': 'district__state__country__continent__id',
        'glob': 'district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Taluka.objects.select_related('district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TalukaSerializer   # For POST, PUT, PATCH
        return TalukaDetailSerializer
    

class CityVillageViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = CityVillage
    queryset = CityVillage.objects.none()
    serializer_class = CityVillageSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'taluka': 'taluka__id',
        'district': 'taluka__district__id',
        'state': 'taluka__district__state__id',
        'country': 'taluka__district__state__country__id',
        'continent': 'taluka__district__state__country__continent__id',
        'glob': 'taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = CityVillage.objects.select_related('taluka__district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CityVillageSerializer   # For POST, PUT, PATCH
        return CityVillageDetailSerializer
    

class WardViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Ward
    queryset = Ward.objects.none()
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'city_village': 'city_village__id',
        'taluka': 'city_village__taluka__id',
        'district': 'city_village__taluka__district__id',
        'state': 'city_village__taluka__district__state__id',
        'country': 'city_village__taluka__district__state__country__id',
        'continent': 'city_village__taluka__district__state__country__continent__id',
        'glob': 'city_village__taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Ward.objects.select_related('city_village__taluka__district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return WardSerializer   # For POST, PUT, PATCH
        return WardDetailSerializer
    


class SocietyViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Society
    queryset = Society.objects.none()
    serializer_class = SocietySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'ward': 'ward__id',
        'city_village': 'ward__city_village__id',
        'taluka': 'ward__city_village__taluka__id',
        'district': 'ward__city_village__taluka__district__id',
        'state': 'ward__city_village__taluka__district__state__id',
        'country': 'ward__city_village__taluka__district__state__country__id',
        'continent': 'ward__city_village__taluka__district__state__country__continent__id',
        'glob': 'ward__city_village__taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    
    def get_base_queryset(self):
        qs = Society.objects.select_related('ward__city_village__taluka__district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SocietySerializer   # For POST, PUT, PATCH
        return SocietyDetailSerializer


class BlockViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Block
    queryset = Block.objects.none()
    serializer_class = BlockSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'society': 'society__id',
        'ward': 'society__ward__id',
        'city_village': 'society__ward__city_village__id',
        'taluka': 'society__ward__city_village__taluka__id',
        'district': 'society__ward__city_village__taluka__district__id',
        'state': 'society__ward__city_village__taluka__district__state__id',
        'country': 'society__ward__city_village__taluka__district__state__country__id',
        'continent': 'society__ward__city_village__taluka__district__state__country__continent__id',
        'glob': 'society__ward__city_village__taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    
    def get_base_queryset(self):
        qs = Block.objects.select_related('society__ward__city_village__taluka__district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BlockSerializer   # For POST, PUT, PATCH
        return BlockDetailSerializer


class FloorViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Floor
    queryset = Floor.objects.none()
    serializer_class = FloorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'block': 'block__id',
        'society': 'block__society__id',
        'ward': 'block__society__ward__id',
        'city_village': 'block__society__ward__city_village__id',
        'taluka': 'block__society__ward__city_village__taluka__id',
        'district': 'block__society__ward__city_village__taluka__district__id',
        'state': 'block__society__ward__city_village__taluka__district__state__id',
        'country': 'block__society__ward__city_village__taluka__district__state__country__id',
        'continent': 'block__society__ward__city_village__taluka__district__state__country__continent__id',
        'glob': 'block__society__ward__city_village__taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'no'
    }
    
    def get_base_queryset(self):
        qs = Floor.objects.select_related('block__society__ward__city_village__taluka__district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return FloorSerializer   # For POST, PUT, PATCH
        return FloorDetailSerializer
    
class HouseViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = House
    queryset = House.objects.none()
    serializer_class = HouseSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'floor': 'floor__id',
        'block': 'floor__block__id',
        'society': 'floor__block__society__id',
        'ward': 'floor__block__society__ward__id',
        'city_village': 'floor__block__society__ward__city_village__id',
        'taluka': 'floor__block__society__ward__city_village__taluka__id',
        'district': 'floor__block__society__ward__city_village__taluka__district__id',
        'state': 'floor__block__society__ward__city_village__taluka__district__state__id',
        'country': 'floor__block__society__ward__city_village__taluka__district__state__country__id',
        'continent': 'floor__block__society__ward__city_village__taluka__district__state__country__continent__id',
        'glob': 'floor__block__society__ward__city_village__taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'no'
    }
    
    def get_base_queryset(self):
        qs = House.objects.select_related('floor__block__society__ward__city_village__taluka__district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return HouseSerializer   # For POST, PUT, PATCH
        return HouseDetailSerializer


class RoomViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Room
    queryset = Room.objects.none()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'house': 'house__id',
        'floor': 'house__floor__id',
        'block': 'house__floor__block__id',
        'society': 'house__floor__block__society__id',
        'ward': 'house__floor__block__society__ward__id',
        'city_village': 'house__floor__block__society__ward__city_village__id',
        'taluka': 'house__floor__block__society__ward__city_village__taluka__id',
        'district': 'house__floor__block__society__ward__city_village__taluka__district__id',
        'state': 'house__floor__block__society__ward__city_village__taluka__district__state__id',
        'country': 'house__floor__block__society__ward__city_village__taluka__district__state__country__id',
        'continent': 'house__floor__block__society__ward__city_village__taluka__district__state__country__continent__id',
        'glob': 'house__floor__block__society__ward__city_village__taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'room_type__name'
    }
    
    def get_base_queryset(self):
        qs = Room.objects.select_related('house__floor__block__society__ward__city_village__taluka__district__state__country__continent__glob').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RoomSerializer   # For POST, PUT, PATCH
        return RoomDetailSerializer
    
# ========================================
# Personal 
# ========================================
class ReligionViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Religion
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ReligionSerializer   # For POST, PUT, PATCH
        return ReligionDetailSerializer 
        
    
class SampradayViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Sampraday
    queryset = Sampraday.objects.none()
    serializer_class = SampradaySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission] 
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'religion': 'religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Sampraday.objects.select_related('religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SampradaySerializer   # For POST, PUT, PATCH
        return SampradayDetailSerializer 


class PanthViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Panth
    queryset = Panth.objects.none()
    serializer_class = PanthSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'sampraday': 'sampraday__id',
        'religion': 'sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Panth.objects.select_related('sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PanthSerializer   # For POST, PUT, PATCH
        return PanthDetailSerializer


class AwasthaViewSet(FilteredQuerysetMixin, viewsets.ModelViewSet):
    model = Awastha
    queryset = Awastha.objects.none()
    serializer_class = AwasthaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AwasthaSerializer   # For POST, PUT, PATCH
        return AwasthaDetailSerializer

class VarnaViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Varna
    queryset = Varna.objects.none()
    serializer_class = VarnaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'panth': 'panth__id',
        'sampraday': 'panth__sampraday__id',
        'religion': 'panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Varna.objects.select_related('panth__sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VarnaSerializer   # For POST, PUT, PATCH
        return VarnaDetailSerializer
    

class CasteViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Caste
    queryset = Caste.objects.none()
    serializer_class = CasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'varna': 'varna__id',
        'panth': 'varna__panth__id',
        'sampraday': 'varna__panth__sampraday__id',
        'religion': 'varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Caste.objects.select_related('varna__panth__sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CasteSerializer   # For POST, PUT, PATCH
        return CasteDetailSerializer
    
    
class SubCasteViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubCaste
    queryset = SubCaste.objects.none()
    serializer_class = SubCasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission] 
    pagination_class = ConfigurationPagination   
    FILTER_FIELDS = {
        'caste': 'caste__id',
        'varna': 'caste__varna__id',
        'panth': 'caste__varna__panth__id',
        'sampraday': 'caste__varna__panth__sampraday__id',
        'religion': 'caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = SubCaste.objects.select_related('caste__varna__panth__sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubCasteSerializer   # For POST, PUT, PATCH
        return SubCasteDetailSerializer


class GotraViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Gotra
    queryset = Gotra.objects.none()
    serializer_class = GotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'subcaste': 'subcaste__id',
        'caste': 'subcaste__caste__id',
        'varna': 'subcaste__caste__varna__id',
        'panth': 'subcaste__caste__varna__panth__id',
        'sampraday': 'subcaste__caste__varna__panth__sampraday__id',
        'religion': 'subcaste__caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Gotra.objects.select_related('subcaste__caste__varna__panth__sampraday__religion').all()
        return qs 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GotraSerializer   # For POST, PUT, PATCH
        return GotraDetailSerializer
    

class SubGotraViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubGotra
    queryset = SubGotra.objects.none()
    serializer_class = SubGotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission] 
    pagination_class = ConfigurationPagination 
    FILTER_FIELDS = {
        'gotra': 'gotra__id',
        'subcaste': 'gotra__subcaste__id',
        'caste': 'gotra__subcaste__caste__id',
        'varna': 'gotra__subcaste__caste__varna__id',
        'panth': 'gotra__subcaste__caste__varna__panth__id',
        'sampraday': 'gotra__subcaste__caste__varna__panth__sampraday__id',
        'religion': 'gotra__subcaste__caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    } 
    def get_base_queryset(self):
        qs = SubGotra.objects.select_related('gotra__subcaste__caste__varna__panth__sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubGotraSerializer   # For POST, PUT, PATCH
        return SubGotraDetailSerializer 


class KulViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Kul
    queryset = Kul.objects.none()
    serializer_class = KulSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'subgotra': 'subgotra__id',
        'gotra': 'subgotra__gotra__id',
        'subcaste': 'subgotra__gotra__subcaste__id',
        'caste': 'subgotra__gotra__subcaste__caste__id',
        'varna': 'subgotra__gotra__subcaste__caste__varna__id',
        'panth': 'subgotra__gotra__subcaste__caste__varna__panth__id',
        'sampraday': 'subgotra__gotra__subcaste__caste__varna__panth__sampraday__id',
        'religion': 'subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Kul.objects.select_related('subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return KulSerializer   # For POST, PUT, PATCH
        return KulDetailSerializer


class VanshViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Vansh
    queryset = Vansh.objects.none()
    serializer_class = VanshSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'kul': 'kul__id',
        'subgotra': 'kul__subgotra__id',
        'gotra': 'kul__subgotra__gotra__id',
        'subcaste': 'kul__subgotra__gotra__subcaste__id',
        'caste': 'kul__subgotra__gotra__subcaste__caste__id',
        'varna': 'kul__subgotra__gotra__subcaste__caste__varna__id',
        'panth': 'kul__subgotra__gotra__subcaste__caste__varna__panth__id',
        'sampraday': 'kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__id',
        'religion': 'kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Vansh.objects.select_related('kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VanshSerializer   # For POST, PUT, PATCH
        return VanshDetailSerializer


class FamilyViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Family
    queryset = Family.objects.none()
    serializer_class = FamilySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'vansh': 'vansh__id',
        'kul': 'vansh__kul__id',
        'subgotra': 'vansh__kul__subgotra__id',
        'gotra': 'vansh__kul__subgotra__gotra__id',
        'subcaste': 'vansh__kul__subgotra__gotra__subcaste__id',
        'caste': 'vansh__kul__subgotra__gotra__subcaste__caste__id',
        'varna': 'vansh__kul__subgotra__gotra__subcaste__caste__varna__id',
        'panth': 'vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__id',
        'sampraday': 'vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__id',
        'religion': 'vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Family.objects.select_related('vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return FamilySerializer   # For POST, PUT, PATCH
        return FamilyDetailSerializer


class PidhiViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Pidhi
    queryset = Pidhi.objects.all()
    serializer_class = PidhiSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    # FILTER_FIELDS = {
    #     'family': 'family__id',
    #     'vansh': 'family__vansh__id',
    #     'kul': 'family__vansh__kul__id',
    #     'subgotra': 'family__vansh__kul__subgotra__id',
    #     'gotra': 'family__vansh__kul__subgotra__gotra__id',
    #     'subcaste': 'family__vansh__kul__subgotra__gotra__subcaste__id',
    #     'caste': 'family__vansh__kul__subgotra__gotra__subcaste__caste__id',
    #     'varna': 'family__vansh__kul__subgotra__gotra__subcaste__caste__varna__id',
    #     'panth': 'family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__id',
    #     'sampraday': 'family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__id',
    #     'is_hidden': 'is_hidden',
    #     'on_hold': 'on_hold',
    #     'search': 'name'
    # }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PidhiSerializer   # For POST, PUT, PATCH
        return PidhiDetailSerializer
    
class CalibrationViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Calibration
    queryset = Calibration.objects.all()
    serializer_class = CalibrationSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    
class CalibrationListView(APIView):
    def get(self, request):
        calibration_objs = get_regular_query(Calibration)
        serializer = CalibrationSerializer(calibration_objs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
# ========================================
# Professional 
# ========================================
class SectionViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Section
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    } 
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)   
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SectionSerializer   # For POST, PUT, PATCH
        return SectionDetailSerializer


class ClassViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Class
    queryset = Class.objects.none()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'section': 'section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Class.objects.select_related('section').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ClassSerializer   # For POST, PUT, PATCH
        return ClassDetailSerializer


class ProfCategoryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = ProfCategory
    queryset = ProfCategory.objects.none()
    serializer_class = ProfCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'profclass': 'profclass__id',
        'section': 'profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = ProfCategory.objects.select_related('profclass__section').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProfCategorySerializer   # For POST, PUT, PATCH
        return ProfCategoryDetailSerializer
    

class ProfSubCategoryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = ProfSubCategory
    queryset = ProfSubCategory.objects.none()
    serializer_class = ProfSubCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'category': 'category__id',
        'profclass': 'category__profclass__id',
        'section': 'category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name' 
    }
    def get_base_queryset(self):
        qs = ProfSubCategory.objects.select_related('category__profclass__section').all()
        return qs 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProfSubCategorySerializer   # For POST, PUT, PATCH
        return ProfSubCategoryDetailSerializer


class SectorViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Sector
    queryset = Sector.objects.none()
    serializer_class = SectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'subcategory': 'subcategory__id',
        'category': 'subcategory__category__id',
        'profclass': 'subcategory__category__profclass__id',
        'section': 'subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Sector.objects.select_related('subcategory__category__profclass__section').all()
        return qs 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SectorSerializer   # For POST, PUT, PATCH
        return SectorDetailSerializer
    

class SubSectorViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubSector
    queryset = SubSector.objects.none()
    serializer_class = SubSectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'sector': 'sector__id',
        'subcategory': 'sector__subcategory__id',
        'category': 'sector__subcategory__category__id',
        'profclass': 'sector__subcategory__category__profclass__id',
        'section': 'sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = SubSector.objects.select_related('sector__subcategory__category__profclass__section').all()
        return qs 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubSectorSerializer   # For POST, PUT, PATCH
        return SubSectorDetailSerializer


class DepartmentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Department
    queryset = Department.objects.none()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'subsector': 'subsector__id',
        'sector': 'subsector__sector__id',
        'subcategory': 'subsector__sector__subcategory__id',
        'category': 'subsector__sector__subcategory__category__id',
        'profclass': 'subsector__sector__subcategory__category__profclass__id',
        'section': 'subsector__sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Department.objects.select_related('subsector__sector__subcategory__category__profclass__section').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DepartmentSerializer   # For POST, PUT, PATCH
        return DepartmentDetailSerializer
    

class SubDepartmentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubDepartment
    queryset = SubDepartment.objects.none()
    serializer_class = SubDepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'department': 'department__id',
        'subsector': 'department__subsector__id',
        'sector': 'department__subsector__sector__id',
        'subcategory': 'department__subsector__sector__subcategory__id',
        'category': 'department__subsector__sector__subcategory__category__id',
        'profclass': 'department__subsector__sector__subcategory__category__profclass__id',
        'section': 'department__subsector__sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = SubDepartment.objects.select_related('department__subsector__sector__subcategory__category__profclass__section').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubDepartmentSerializer   # For POST, PUT, PATCH
        return SubDepartmentDetailSerializer
    
    
class TypeViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Type
    queryset = Type.objects.none()
    serializer_class = TypeSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'subdepartment': 'subdepartment__id',
        'department': 'subdepartment__department__id',
        'subsector': 'subdepartment__department__subsector__id',
        'sector': 'subdepartment__department__subsector__sector__id',
        'subcategory': 'subdepartment__department__subsector__sector__subcategory__id',
        'category': 'subdepartment__department__subsector__sector__subcategory__category__id',
        'profclass': 'subdepartment__department__subsector__sector__subcategory__category__profclass__id',
        'section': 'subdepartment__department__subsector__sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Type.objects.select_related('subdepartment__department__subsector__sector__subcategory__category__profclass__section').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TypeSerializer   # For POST, PUT, PATCH
        return TypeDetailSerializer
    

class BrandListView(APIView):
    def get(self, request):
        search = request.query_params.get('search')
        if search:
            brand_objs_lst = Brand.objects.filter(name__icontains=search)[:10]
        else:
            brand_objs_lst = Brand.objects.all()[:10]
        serializer = BrandIdNameSerializer(brand_objs_lst, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BrandViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Brand
    queryset = Brand.objects.none()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'type': 'type__id',
        'subdepartment': 'type__subdepartment__id',
        'department': 'type__subdepartment__department__id',
        'subsector': 'type__subdepartment__department__subsector__id',
        'sector': 'type__subdepartment__department__subsector__sector__id',
        'subcategory': 'type__subdepartment__department__subsector__sector__subcategory__id',
        'category': 'type__subdepartment__department__subsector__sector__subcategory__category__id',
        'profclass': 'type__subdepartment__department__subsector__sector__subcategory__category__profclass__id',
        'section': 'type__subdepartment__department__subsector__sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Brand.objects.select_related('type__subdepartment__department__subsector__sector__subcategory__category__profclass__section').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BrandSerializer   # For POST, PUT, PATCH
        return BrandDetailSerializer


class ProductViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Product
    queryset = Product.objects.none()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'brand': 'brand__id',
        'type': 'brand__type__id',
        'subdepartment': 'brand__type__subdepartment__id',
        'department': 'brand__type__subdepartment__department__id',
        'subsector': 'brand__type__subdepartment__department__subsector__id',
        'sector': 'brand__type__subdepartment__department__subsector__sector__id',
        'subcategory': 'brand__type__subdepartment__department__subsector__sector__subcategory__id',
        'category': 'brand__type__subdepartment__department__subsector__sector__subcategory__category__id',
        'profclass': 'brand__type__subdepartment__department__subsector__sector__subcategory__category__profclass__id',
        'section': 'brand__type__subdepartment__department__subsector__sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    def get_base_queryset(self):
        qs = Product.objects.select_related('brand__type__subdepartment__department__subsector__sector__subcategory__category__profclass__section').all()
        return qs
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductSerializer   # For POST, PUT, PATCH
        return ProductDetailSerializer


class ProductListView(APIView):
    def get(self, request):
        brand_id = request.query_params.get('brand_id')
        if not brand_id:
            return Response({
                "error": "brand_id is required."
            })
        
        brand = get_object_or_404(Brand, id=brand_id)
        
        search = request.query_params.get('search')
        if search:
            product_objs_lst = Product.objects.filter(brand=brand, name__icontains=search)[:10]
        else:
            product_objs_lst = Product.objects.filter(brand=brand)[:10]
            
        serializer = ProductIdNameSerializer(product_objs_lst, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
# class PostModelViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
#     model = PostModel
#     queryset = PostModel.objects.all()
#     serializer_class = PostModelSerializer
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]
#     FILTER_FIELDS = {
#         'brand': 'brand__id',
#         'type': 'brand__type__id',
#         'subdepartment': 'brand__type__subdepartment__id',
#         'department': 'brand__type__subdepartment__department__id',
#         'subsector': 'brand__type__subdepartment__department__subsector__id',
#         'sector': 'brand__type__subdepartment__department__subsector__sector__id',
#         'subcategory': 'brand__type__subdepartment__department__subsector__sector__subcategory__id',
#         'category': 'brand__type__subdepartment__department__subsector__sector__subcategory__category__id',
#         'profclass': 'brand__type__subdepartment__department__subsector__sector__subcategory__category__profclass__id',
#         'section': 'brand__type__subdepartment__department__subsector__sector__subcategory__category__profclass__section__id',
#         'is_hidden': 'is_hidden',
#         'on_hold': 'on_hold',
#         'search': 'name'
#     }
#     # def get_base_queryset(self):
#     #     return get_regular_query(self.model) 
    
#     def get_serializer_class(self):
#         if self.action in ["create", "update", "partial_update"]:
#             return PostModelSerializer   # For POST, PUT, PATCH
#         return PostModelDetailSerializer


class RoomFlashViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = RoomFlash
    queryset = RoomFlash.objects.all()
    serializer_class = RoomFlashSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
            
        if instance.is_used:
            return Response(
                {
                    "error": f"Cannot delete RoomFlash '{instance.name}' (Code: {instance.code}) "
                             "because it is referenced in one or more users ResidentialDetail records.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Proceed with normal deletion if not used
        return super().destroy(request, *args, **kwargs)

class RoomFlashListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        room_flashes = get_regular_query(RoomFlash)
        room_flashes = room_flashes.order_by('code')
        serializer = RoomFlashIdNameSerializer(room_flashes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomTypeViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = RoomType
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
            
        if instance.is_used:
            return Response(
                {
                    "error": f"Cannot delete RoomType '{instance.name}' (Code: {instance.code}) "
                             "because it is referenced in one or more users ResidentialDetail records.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Proceed with normal deletion if not used
        return super().destroy(request, *args, **kwargs)


class RoomTypeListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        room_types = get_regular_query(RoomType)
        room_types = room_types.order_by('code')
        serializer = RoomTypeIdNameSerializer(room_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
# ==================
# Import Features
# ==================


def clean(value):
    # This handles None, np.nan, and pd.NaT all at once
    if pd.isna(value):
        return None
    
    # Convert to string and strip whitespace
    cleaned_value = str(value).strip()
    
    # Return the value if it's not an empty string, otherwise return None
    return cleaned_value if cleaned_value else None


class UploadGlobsView(APIView):
    model = Glob
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["glob", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                name = clean(row.get("glob") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                objs.append(
                    Glob(
                        name=name, 
                        code=code, 
                        is_hidden = is_hidden, 
                        on_hold = on_hold, 
                        hold_date = hold_date
                    )
                )
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.atomic():
                Glob.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Globs uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED)


class UploadContinentsView(APIView):
    model = Continent
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        glob_cache = {g.name: g for g in Glob.objects.all()}
        
        objs = []
        invalid_rows = []

        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                glob_obj = glob_cache.get(glob)
                if not glob_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Glob '{glob}' not found"})
                    continue
                
                objs.append(Continent(
                    glob = glob_obj, 
                    name = continent, 
                    code = code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )        
        try:
            with transaction.atomic():
                Continent.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["glob", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Continents uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED)


class UploadCountriesView(APIView):
    model = Country
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        continent_cache = {
            (c.name, c.glob.name): c
            for c in Continent.objects.select_related('glob').all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()

                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)

                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                continent_obj = continent_cache.get((continent, glob))
                if not continent_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Continent '{continent}' not found for glob: {glob}"})
                    continue
                
                objs.append(Country(
                    continent=continent_obj,
                    name=country, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
                
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )        
        try:
            with transaction.atomic():
                Country.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["continent","name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Countries uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )    
        
        
class UploadStatesView(APIView):
    model = State
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        # This runs 1 query that gets EVERYTHING (countries + contient + glob)
        country_cache = {
            (c.name, c.continent.name, c.continent.glob.name): c
            for c in Country.objects.select_related('continent__glob').all()
        }
                
        objs = []
        invalid_rows = []

        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                country_obj = country_cache.get((country, continent, glob))
                if not country_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Country '{country}' not found for continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(State(
                    country=country_obj,
                    name=state, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})       
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )        
        try:
            with transaction.atomic():
                State.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["country", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} States uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )
            

class UploadDistrictsView(APIView):
    model = District
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        state_cache = {
            (s.name, s.country.name, s.country.continent.name, s.country.continent.glob.name): s
            for s in State.objects.select_related('country__continent__glob').all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                state_obj = state_cache.get((state, country, continent, glob))
                if not state_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"State '{state}' not found for country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                    
                objs.append(District(
                    state=state_obj,
                    name=district, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
                    
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )        
        try:
            with transaction.atomic():
                District.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["state", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Districts uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )    
        
        
class UploadTalukasView(APIView):
    model = Taluka
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        district_cache = {
            (d.name, 
             d.state.name, 
             d.state.country.name, 
             d.state.country.continent.name, 
             d.state.country.continent.glob.name): d
             for d in District.objects.select_related('state__country__continent__glob').all()
        }
         
        objs = []
        invalid_rows = []

        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                district_obj = district_cache.get((district, state, country, continent, glob))
                if not district_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"District '{district}' not found for state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(Taluka(
                    district=district_obj,
                    name=taluka, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                    
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )        
        try:
            with transaction.atomic():
                Taluka.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["district", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Talukas uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )            
            

class UploadCityVillagesView(APIView):
    model = CityVillage
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "city_village", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        taluka_cache = {
            (t.name,
             t.district.name,
             t.district.state.name,
             t.district.state.country.name,
             t.district.state.country.continent.name,
             t.district.state.country.continent.glob.name): t
             for t in Taluka.objects.select_related('district__state__country__continent__glob').all()
        }
           
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                city_village = clean(row.get("city_village") or "")    
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                taluka_obj = taluka_cache.get((taluka, district, state, country, continent, glob))
                if not taluka_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Taluka '{taluka}' not found for district: {district}, state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(CityVillage(
                    taluka=taluka_obj,
                    name=city_village, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )        
        try:
            with transaction.atomic():
                CityVillage.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["taluka", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} City/Villages uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )

class UploadWardsView(APIView):
    model = Ward
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "city_village", "ward", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=400)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
                
        city_village_cache = {
            (cv.name,
             cv.taluka.name,
             cv.taluka.district.name,
             cv.taluka.district.state.name,
             cv.taluka.district.state.country.name,
             cv.taluka.district.state.country.continent.name,
             cv.taluka.district.state.country.continent.glob.name): cv
             for cv in CityVillage.objects.select_related('taluka__district__state__country__continent__glob').all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                city_village = clean(row.get("city_village") or "")
                ward = clean(row.get("ward") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, ward, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                city_village_obj = city_village_cache.get((city_village, taluka, district, state, country, continent, glob))
                if not city_village_obj:   
                    invalid_rows.append({"row": idx + 2, "error": f"City/Village '{city_village}' not found for taluka: {taluka}, district: {district}, state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(Ward(
                    city_village=city_village_obj,
                    name=ward, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                     
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.atomic():
                Ward.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["city_village", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Wards uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )


class UploadSocietiesView(APIView):
    model = Society
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "city_village", "ward", "society", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        ward_cache = {
            (
                w.name,
                w.city_village.name,
                w.city_village.taluka.name,
                w.city_village.taluka.district.name,
                w.city_village.taluka.district.state.name,
                w.city_village.taluka.district.state.country.name,
                w.city_village.taluka.district.state.country.continent.name,
                w.city_village.taluka.district.state.country.continent.glob.name
            ): w
            for w in Ward.objects.select_related('city_village__taluka__district__state__country__continent__glob').all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = row.get("is_hidden", False)
                on_hold = row.get("on_hold", False)
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                city_village = clean(row.get("city_village") or "")
                ward = clean(row.get("ward") or "")
                society = clean(row.get("society") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, ward, society, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                
                ward_obj = ward_cache.get((ward, city_village, taluka, district, state, country, continent, glob))
                if not ward_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Ward '{ward}' not found for city_village: {city_village}, taluka: {taluka}, district: {district}, state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(Society(
                    ward=ward_obj, 
                    name=society, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
                
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            with transaction.atomic():
                Society.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["ward", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Societies uploaded successfully",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )


class UploadBlocksView(APIView):
    model = Block
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "city_village", "ward", "society", "block", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        society_cache = {
            (
                s.name,
                s.ward.name,
                s.ward.city_village.name,
                s.ward.city_village.taluka.name,
                s.ward.city_village.taluka.district.name,
                s.ward.city_village.taluka.district.state.name,
                s.ward.city_village.taluka.district.state.country.name,
                s.ward.city_village.taluka.district.state.country.continent.name,
                s.ward.city_village.taluka.district.state.country.continent.glob.name,
             ): s
            for s in Society.objects.select_related('ward__city_village__taluka__district__state__country__continent__glob').all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields    
                is_hidden = row.get("is_hidden", False)
                on_hold = row.get("on_hold", False)
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                city_village = clean(row.get("city_village") or "")
                ward = clean(row.get("ward") or "")
                society = clean(row.get("society") or "")
                block = clean(row.get("block") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, ward, society, block, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                
                society_obj = society_cache.get((society, ward, city_village, taluka, district, state, country, continent, glob))
                if not society_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Society '{society}' not found for ward: {ward}, city_village: {city_village}, taluka: {taluka}, district: {district}, state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(
                    Block(
                        society=society_obj,
                        name=block,
                        code=code,
                        is_hidden=is_hidden,
                        on_hold=on_hold,
                        hold_date=hold_date
                    )
                )
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
            
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Block.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["society", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Blocks uploaded successfully",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )

class UploadFloorsView(APIView):
    model = Floor
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "city_village", "ward", "society", "block", "floor_no", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        block_cache = {
            (
                b.name,
                b.society.name,
                b.society.ward.name,
                b.society.ward.city_village.name,
                b.society.ward.city_village.taluka.name,
                b.society.ward.city_village.taluka.district.name,
                b.society.ward.city_village.taluka.district.state.name,
                b.society.ward.city_village.taluka.district.state.country.name,
                b.society.ward.city_village.taluka.district.state.country.continent.name,
                b.society.ward.city_village.taluka.district.state.country.continent.glob.name,
             ): b
            for b in Block.objects.select_related('society__ward__city_village__taluka__district__state__country__continent__glob').all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = row.get("is_hidden", False)
                on_hold = row.get("on_hold", False)
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                city_village = clean(row.get("city_village") or "")
                ward = clean(row.get("ward") or "")
                society = clean(row.get("society") or "")
                block = clean(row.get("block") or "")
                floor_no = row.get("floor_no")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, ward, society, block, floor_no, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                
                block_obj = block_cache.get((block, society, ward, city_village, taluka, district, state, country, continent, glob))
                if not block_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Block '{block}' not found for society: {society}, ward: {ward}, city_village: {city_village}, taluka: {taluka}, district: {district}, state: {state}, country: {country}, continent: {continent}, glob: {glob}."})
                    continue
                
                objs.append(
                    Floor(
                        block=block_obj,
                        no=floor_no,
                        code=code,
                        is_hidden=is_hidden,
                        on_hold=on_hold,
                        hold_date=hold_date
                    )
                )
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response(
                {
                    "error": "No valid rows found in the file.",
                    "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            with transaction.atomic():
                Floor.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["block", "no"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Floors uploaded successfully",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )


class UploadHousesView(APIView):
    model = House
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "city_village", "ward", "society", "block", "floor_no", "house_no", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        floor_cache = {
            (
                f.no,
                f.block.name,
                f.block.society.name,
                f.block.society.ward.name,
                f.block.society.ward.city_village.name,
                f.block.society.ward.city_village.taluka.name,
                f.block.society.ward.city_village.taluka.district.name,
                f.block.society.ward.city_village.taluka.district.state.name,
                f.block.society.ward.city_village.taluka.district.state.country.name,
                f.block.society.ward.city_village.taluka.district.state.country.continent.name,
                f.block.society.ward.city_village.taluka.district.state.country.continent.glob.name,
             ): f
            for f in Floor.objects.select_related('block__society__ward__city_village__taluka__district__state__country__continent__glob').all()
        }
        
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = row.get("is_hidden", False)
                on_hold = row.get("on_hold", False)
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                city_village = clean(row.get("city_village") or "")
                ward = clean(row.get("ward") or "")
                society = clean(row.get("society") or "")
                block = clean(row.get("block") or "")
                floor_no = row.get("floor_no")
                house_no = row.get("house_no")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, ward, society, block, floor_no, house_no, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                
                floor_obj = floor_cache.get((floor_no, block, society, ward, city_village, taluka, district, state, country, continent, glob))
                if not floor_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Floor '{floor_no}' not found for block {block}, society {society}, ward {ward}, city_village {city_village}, taluka {taluka}, district {district}, state {state}, country {country}, continent {continent}, glob {glob}."})
                    continue
                
                objs.append(
                    House(
                        floor=floor_obj,
                        no=house_no,
                        code=code,
                        is_hidden=is_hidden,
                        on_hold=on_hold,
                        hold_date=hold_date
                    )
                )
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response(
                {
                    "error": "No valid rows found in the file.",
                    "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                House.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["floor","no"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"]
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Houses uploaded successfully",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )


class UploadRoomsView(APIView):
    model = Room
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["glob", "continent", "country", "state", "district", "taluka", "city_village", "ward", "society", "block", "floor_no", "house_no", "room_no", "room_type", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        house_cache = {
            (
                h.no,
                h.floor.no,
                h.floor.block.name,
                h.floor.block.society.name,
                h.floor.block.society.ward.name,
                h.floor.block.society.ward.city_village.name,
                h.floor.block.society.ward.city_village.taluka.name,
                h.floor.block.society.ward.city_village.taluka.district.name,
                h.floor.block.society.ward.city_village.taluka.district.state.name,
                h.floor.block.society.ward.city_village.taluka.district.state.country.name,
                h.floor.block.society.ward.city_village.taluka.district.state.country.continent.name,
                h.floor.block.society.ward.city_village.taluka.district.state.country.continent.glob.name,
            ): h
            for h in House.objects.all()
        }
        
        room_type_objs =  RoomType.objects.all()
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = row.get("is_hidden", False)
                on_hold = row.get("on_hold", False)
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                glob = clean(row.get("glob") or "")
                continent = clean(row.get("continent") or "")
                country = clean(row.get("country") or "")
                state = clean(row.get("state") or "")
                district = clean(row.get("district") or "")
                taluka = clean(row.get("taluka") or "")
                city_village = clean(row.get("city_village") or "")
                ward = clean(row.get("ward") or "")
                society = clean(row.get("society") or "")
                block = clean(row.get("block") or "")
                floor_no = row.get("floor_no")
                house_no = clean(row.get("house_no") or "")
                room_no = row.get("room_no")
                room_type = clean(row.get("room_type") or "")
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, ward, society, block, floor_no, house_no, room_no,code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                house_obj = house_cache[(house_no, floor_no, block, society, ward, city_village, taluka, district, state, country, continent, glob)]
                if not house_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"House '{house_no}' not found for floor {floor_no}, block {block}, society {society}, ward {ward}, city_village {city_village}, taluka {taluka}, district {district}, state {state}, country {country}, continent {continent}, glob {glob}."})
                    continue
                
                if room_type:
                    room_type_obj = room_type_objs.filter(name=room_type).first()
                    if not room_type_obj:
                        invalid_rows.append({"row": idx + 2, "error": "Room type not found."})
                        continue
                else:
                    room_type_obj = None
                
                objs.append(
                    Room(
                        house=house_obj,
                        no=room_no,
                        room_type = room_type_obj,
                        code=code,
                        is_hidden=is_hidden,
                        on_hold=on_hold,
                        hold_date=hold_date
                    )
                )

            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response(
                {
                    "error": "No valid rows found in the file.",
                    "invalid_rows": invalid_rows,
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Room.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=[
                        "is_hidden",
                        "on_hold",
                        "hold_date",
                        "house",
                        "room_type",
                        "no"
                    ],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} rooms uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )


             
# class UploadRoomFlashesView(APIView):
#     model = RoomFlash
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
#     def post(self, request):
#         serializer = FileUploadSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         file = serializer.validated_data['file']

#         try:
#             df = read_file(file, required_columns=["room_flash", "code", "is_hidden", "on_hold", "hold_date"])
#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if the DataFrame is empty
#         if df.empty:
#             return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
#         objs = []
#         invalid_rows = []
        
#         for idx, row in df.iterrows():
#             try:
#                 hold_date = row.get('hold_date')
#                 if pd.isna(hold_date):  # check for NaT or NaN
#                     hold_date = None
#                 else:
#                     hold_date = pd.to_datetime(hold_date).date()
                    
#                 # Normalize boolean fields
#                 is_hidden = normalize_bool(row.get("is_hidden"))
#                 on_hold = normalize_bool(row.get("on_hold"))
                
#                 # Calculate hidden and on_hold values
#                 is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
#                 # Clean text safely
#                 room_flash_name = clean(row.get("room_flash"))
#                 code = row.get("code")
                
#                 # Skip invalid rows early
#                 if not all([room_flash_name, code]):
#                     invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
#                     continue
                
#                 objs.append(RoomFlash(
#                     name=room_flash_name, 
#                     code=code, 
#                     is_hidden = is_hidden, 
#                     on_hold = on_hold, 
#                     hold_date = hold_date
#                 ))
                   
#             except Exception as e:
#                 invalid_rows.append({"row": idx + 2, "error": str(e)})   

#         if not objs:
#             return Response({
#                 "error": "No valid records found in the file.",
#                 "invalid_rows": invalid_rows
#                 }, status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             with transaction.atomic():
#                 RoomFlash.objects.bulk_create(
#                     objs,
#                     update_conflicts=True,
#                     unique_fields=["code"],
#                     update_fields=["name", "is_hidden", "on_hold", "hold_date"],
#                 )
#         except Exception as e:
#             return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
#         return Response(
#             {
#                 "message": f"{len(objs)} RoomFlash uploaded successfully",
#                 "invalid_rows": invalid_rows,
#             }, status=status.HTTP_201_CREATED
#         )


class UploadRoomTypesView(APIView):
    model = RoomType
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["room_type", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                room_type_name = clean(row.get("room_type"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([room_type_name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                
                objs.append(RoomType(
                    name=room_type_name, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})   

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                RoomType.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} RoomType uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )
                   
class ModelNameView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ModelNameSerializer
    
    def get(self, request):
        user = request.user
        if user.is_system_user==False or user.is_verified==False:
            return Response({"message":"You have not permission to access this resource"}, status=status.HTTP_401_UNAUTHORIZED)
        
        model_names = ModelName.objects.all()
        serializer = self.serializer_class(model_names, many=True)
        return Response(serializer.data)




# ======================================================================
# Personal Upload excel/csv
# ======================================================================
class UploadReligionView(APIView):
    model = Religion
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([religion, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                
                objs.append(Religion(
                    name=religion, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})   

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                Religion.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Religion uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )

class UploadSampradayView(APIView):
    model = Sampraday
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion", "sampraday", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        religion_cache = {
            r.name : r for r in Religion.objects.all() 
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([religion, sampraday, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                religion_obj = religion_cache.get(religion)
                if not religion_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Religion '{religion}' not found"})
                    continue    
                
                objs.append(Sampraday(
                    religion = religion_obj,
                    name=sampraday, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})   

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                Sampraday.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["religion", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Sampraday uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )


class UploadPanthView(APIView):
    model = Panth
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        sampraday_cache = {
            (s.name, s.religion.name) : s for s in Sampraday.objects.select_related("religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                sampraday_obj = sampraday_cache.get((sampraday, religion))
                if not sampraday_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Sampraday '{sampraday}' not found for religion: {religion}"})
                    continue    
                
                objs.append(Panth(
                    sampraday = sampraday_obj,
                    name=panth, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})   

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                Panth.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["sampraday", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Panth uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )


class UploadAwasthaView(APIView):
    model = Awastha
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["awastha", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                awastha = clean(row.get("awastha"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([awastha, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue    
                
                objs.append(Awastha(
                    name=awastha, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Awastha.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Awastha uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )
        

class UploadVarnaView(APIView):
    model = Varna
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        panth_cache = {
            (
                p.name,
                p.sampraday.name,
                p.sampraday.religion.name
            ): p
            for p in Panth.objects.select_related("sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([religion, sampraday, panth, varna, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                panth_obj = panth_cache.get((panth, sampraday, religion))
                if not panth_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Panth '{panth}' not found for sampraday: {sampraday}, religion: {religion}"}) 
                    continue    
                
                objs.append(Varna(
                    panth = panth_obj,
                    name=varna, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})   

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                Varna.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["panth", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Varna uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )


class UploadCasteView(APIView):
    model = Caste
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "caste", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        varna_cache = {
            (v.name,
             v.panth.name,
             v.panth.sampraday.name,
             v.panth.sampraday.religion.name) : v
            for v in Varna.objects.select_related("panth__sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                caste = clean(row.get("caste"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, varna, caste, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                varna_obj = varna_cache.get((varna, panth, sampraday, religion))
                if not varna_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Varna '{varna}' not found for panth: {panth}, sampraday: {sampraday}, religion: {religion}"}) 
                    continue    
                
                objs.append(Caste(
                    varna = varna_obj,
                    name=caste, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})   

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                Caste.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["varna", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Caste uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )
        

class UploadSubCasteView(APIView):
    model = SubCaste
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "caste", "subcaste", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        caste_cache = {
            (c.name, 
             c.varna.name,
             c.varna.panth.name, 
             c.varna.panth.sampraday.name, 
             c.varna.panth.sampraday.religion.name) : c
            for c in Caste.objects.select_related("varna__panth__sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                caste = clean(row.get("caste"))
                subcaste = clean(row.get("subcaste"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, varna, caste, subcaste, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                caste_obj = caste_cache.get((caste, varna, panth, sampraday, religion))
                if not caste_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Caste '{caste}' not found for varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"}) 
                    continue    
                
                objs.append(SubCaste(
                    caste = caste_obj,
                    name=subcaste, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})   

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                SubCaste.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["caste", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} SubCaste uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )

class UploadGotraView(APIView):
    model = Gotra
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]    
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "caste", "subcaste", "gotra", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        subcaste_cache = {
            (s.name, 
             s.caste.name, 
             s.caste.varna.name, 
             s.caste.varna.panth.name, 
             s.caste.varna.panth.sampraday.name, 
             s.caste.varna.panth.sampraday.religion.name) : s
            for s in SubCaste.objects.select_related("caste__varna__panth__sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                caste = clean(row.get("caste"))
                subcaste = clean(row.get("subcaste"))
                gotra = clean(row.get("gotra"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                 
                    
                subcaste_obj = subcaste_cache.get((subcaste, caste, varna, panth, sampraday, religion))
                if not subcaste_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Sub Caste {subcaste} not found for caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}."}) 
                    continue    
                
                objs.append(Gotra(
                    subcaste = subcaste_obj,
                    name=gotra, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                   
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                Gotra.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["subcaste", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Gotra uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )


class UploadSubGotraView(APIView):
    model = SubGotra
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]    
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "caste", "subcaste", "gotra", "subgotra", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        gotra_cache = {
            (g.name, 
             g.subcaste.name, 
             g.subcaste.caste.name, 
             g.subcaste.caste.varna.name,
             g.subcaste.caste.varna.panth.name, 
             g.subcaste.caste.varna.panth.sampraday.name, 
             g.subcaste.caste.varna.panth.sampraday.religion.name) : g
            for g in Gotra.objects.select_related("subcaste__caste__varna__panth__sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                caste = clean(row.get("caste"))
                subcaste = clean(row.get("subcaste"))
                gotra = clean(row.get("gotra"))
                subgotra = clean(row.get("subgotra"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, varna, caste, subcaste, gotra, subgotra, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                gotra_obj = gotra_cache.get((gotra, subcaste, caste, varna, panth, sampraday, religion))
                if not gotra_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Gotra '{gotra}' not found for subcaste: {subcaste}, caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"})
                    continue    
                
                objs.append(SubGotra(
                    gotra = gotra_obj,
                    name=subgotra, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))                                
            
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                SubGotra.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["gotra", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} SubGotra uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )


class UploadKulView(APIView):
    model = Kul
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "caste", "subcaste", "gotra", "subgotra", "kul", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        subgotra_cache = {
            (sg.name,
            sg.gotra.name,
            sg.gotra.subcaste.name,
            sg.gotra.subcaste.caste.name,
            sg.gotra.subcaste.caste.varna.name,
            sg.gotra.subcaste.caste.varna.panth.name,
            sg.gotra.subcaste.caste.varna.panth.sampraday.name,
            sg.gotra.subcaste.caste.varna.panth.sampraday.religion.name): sg
            for sg in SubGotra.objects.select_related("gotra__subcaste__caste__varna__panth__sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                caste = clean(row.get("caste"))
                subcaste = clean(row.get("subcaste"))
                gotra = clean(row.get("gotra"))
                subgotra = clean(row.get("subgotra"))
                kul = clean(row.get("kul"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, subgotra, kul, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                subgotra_obj = subgotra_cache.get((subgotra, gotra, subcaste, caste, varna, panth, sampraday, religion))
                if not subgotra_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"SubGotra '{subgotra}' not found for gotra: {gotra}, sub caste: {subcaste}, caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}."})
                    continue    
                
                objs.append(Kul(
                    subgotra = subgotra_obj,
                    name=kul, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})

        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Kul.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["subgotra", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Kul uploaded successfully",
                "invalid_rows": invalid_rows,
            }, status=status.HTTP_201_CREATED
        )


class UploadVanshView(APIView):
    model = Vansh
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "caste", "subcaste", "gotra", "subgotra", "kul", "vansh", "code", "is_hidden", "on_hold", "hold_date"])   
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        kul_cache = {
            (kul.name,
            kul.subgotra.name,
            kul.subgotra.gotra.name,
            kul.subgotra.gotra.subcaste.name,
            kul.subgotra.gotra.subcaste.caste.name,
            kul.subgotra.gotra.subcaste.caste.varna.name,
            kul.subgotra.gotra.subcaste.caste.varna.name,
            kul.subgotra.gotra.subcaste.caste.varna.panth.name,
            kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.name,
            kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion.name): kul
            for kul in Kul.objects.select_related("subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday"))
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                caste = clean(row.get("caste"))
                subcaste = clean(row.get("subcaste"))
                gotra = clean(row.get("gotra"))
                subgotra = clean(row.get("subgotra"))
                kul = clean(row.get("kul"))
                vansh = clean(row.get("vansh"))
                code = row.get("code")
                
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, subgotra, kul, vansh, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                kul_obj = kul_cache.get((kul, subgotra, gotra, subcaste, caste, varna, panth, sampraday, religion))
                if not kul_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Kul '{kul} not found for subgotra: {subgotra}, gotra: {gotra}, subcaste: {subcaste}, caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"})
                    continue
                
                objs.append(Vansh(
                    kul = kul_obj,
                    name=vansh, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Vansh.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["kul", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:  
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "message": f"{len(objs)} Vansh uploaded successfully",
            "invalid_rows": invalid_rows,
        })


class UploadFamilyView(APIView):
    model = Family
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["religion", "sampraday", "panth", "varna", "caste", "subcaste", "gotra", "subgotra", "kul", "vansh", "family", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        vansh_cache = {
            (v.name,
             v.kul.name,
             v.kul.subgotra.name,
             v.kul.subgotra.gotra.name,
             v.kul.subgotra.gotra.subcaste.name,
             v.kul.subgotra.gotra.subcaste.caste.name,
             v.kul.subgotra.gotra.subcaste.caste.varna.name,
             v.kul.subgotra.gotra.subcaste.caste.varna.name,
             v.kul.subgotra.gotra.subcaste.caste.varna.panth.name,
             v.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.name,
             v.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion.name): v
            for v in Vansh.objects.select_related("kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get("hold_date")
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                religion = clean(row.get("religion"))
                sampraday = clean(row.get("sampraday")) 
                panth = clean(row.get("panth"))
                varna = clean(row.get("varna"))
                caste = clean(row.get("caste"))
                subcaste = clean(row.get("subcaste"))
                gotra = clean(row.get("gotra"))
                subgotra = clean(row.get("subgotra"))
                kul = clean(row.get("kul"))
                vansh = clean(row.get("vansh"))
                family = clean(row.get("family"))
                code = row.get("code")    
                
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, subgotra, kul, vansh, family, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                vansh_obj = vansh_cache.get((vansh, kul, subgotra, gotra, subcaste, caste, varna, panth, sampraday, religion))
                if not vansh_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Vansh '{vansh}' not found for kul: {kul}, subgotra: {subgotra}, gotra: {gotra}, subcaste: {subcaste}, caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"})
                    continue
                
                objs.append(Family(
                    vansh = vansh_obj,
                    name = family,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
                continue
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Family.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["vansh", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Families uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )


# class UploadPidhiView(APIView):
#     model = Pidhi
#     permission_classes = [IsAuthenticated]
#     serializer_class = FileUploadSerializer
    
#     def post(self, request):
#         serializer = FileUploadSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         file = serializer.validated_data['file']

#         try:
#             df = read_file(file, required_columns=["religion","sampraday", "panth", "awastha", "varna", "caste", "subcaste", "gotra", "subgotra", "kul", "vansh", "family", "pidhi", "code", "is_hidden", "on_hold", "hold_date"])
#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
#         # Check if the DataFrame is empty
#         if df.empty:
#             return Response({"error": "File is empty."}, status=status.HTTP_400_BAD_REQUEST)
        
#         family_cache = {
#             (f.name,
#              f.vansh.name,
#              f.vansh.kul.name,
#              f.vansh.kul.subgotra.name,
#              f.vansh.kul.subgotra.gotra.name,
#              f.vansh.kul.subgotra.gotra.subcaste.name,
#              f.vansh.kul.subgotra.gotra.subcaste.caste.name,
#              f.vansh.kul.subgotra.gotra.subcaste.caste.varna.name,
#              f.vansh.kul.subgotra.gotra.subcaste.caste.varna.name,
#              f.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.name,
#              f.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.name,
#              f.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion.name): f
#             for f in Family.objects.all()
#         }
                
    
#         objs = []
#         invalid_rows = []
        
#         for idx, row in df.iterrows():
#             try:
#                 hold_date = row.get('hold_date')
#                 if pd.isna(hold_date):  # check for NaT or NaN
#                     hold_date = None
#                 else:
#                     hold_date = pd.to_datetime(hold_date).date()
                    
#                 # Normalize boolean fields
#                 is_hidden = normalize_bool(row.get("is_hidden"))
#                 on_hold = normalize_bool(row.get("on_hold"))
                
#                 # Calculate hidden and on_hold values
#                 is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
#                 # Clean text safely
#                 religion = clean(row.get("religion"))
#                 sampraday = clean(row.get("sampraday")) 
#                 panth = clean(row.get("panth"))
#                 awastha = clean(row.get("awastha"))
#                 varna = clean(row.get("varna"))
#                 caste = clean(row.get("caste"))
#                 subcaste = clean(row.get("subcaste"))
#                 gotra = clean(row.get("gotra"))
#                 subgotra = clean(row.get("subgotra"))
#                 kul = clean(row.get("kul"))
#                 vansh = clean(row.get("vansh"))
#                 family = clean(row.get("family"))
#                 pidhi = clean(row.get("pidhi"))
#                 code = row.get("code")
                
#                 if not all([religion, sampraday, panth, awastha, varna, caste, subcaste, gotra, subgotra, kul, vansh, family, pidhi, code]):
#                     invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
#                     continue
                
#                 family_obj = family_cache.get((family, vansh, kul, subgotra, gotra, subcaste, caste, varna, awastha, panth, sampraday, religion))
#                 if not family_obj:
#                     invalid_rows.append({"row": idx + 2, "error": f"Family '{family}' not found for vansh: {vansh}, kul: {kul}, subgotra: {subgotra}, gotra: {gotra}, subcaste: {subcaste}, caste: {caste}, varna: {varna}, awastha: {awastha}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"})
#                     continue
                
#                 objs.append(Pidhi(
#                     family = family_obj,
#                     name = pidhi,
#                     code = code,
#                     is_hidden = is_hidden,
#                     on_hold = on_hold,
#                     hold_date = hold_date
#                 ))
                
#             except Exception as e:
#                 invalid_rows.append({"row": idx + 2, "error": str(e)})
        
#         if not objs:
#             return Response({
#                 "error": "No valid records found in the file.",
#                 "invalid_rows": invalid_rows
#                 }, status=status.HTTP_400_BAD_REQUEST
#             )
        
#         try:
#             with transaction.atomic():
#                 Pidhi.objects.bulk_create(
#                     objs,
#                     update_conflicts=True,
#                     unique_fields=["code"],
#                     update_fields=["family", "name", "is_hidden", "on_hold", "hold_date"],
#                 )
#         except Exception as e:
#             return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
#         return Response(
#             {
#                 "message": f"{len(objs)} Pidhis uploaded successfully.",
#                 "invalid_rows": invalid_rows
#             }, status=status.HTTP_201_CREATED
#         )
 
# ======================================================================
# Professional Upload excel/csv
# ====================================================================== 

class UploadSectionView(APIView):
    model = Section
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                objs.append(Section(
                    name = section,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Section.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],  # field(s) to check for conflicts
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],  # fields to update
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Section uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )
   
 
class UploadClassView(APIView):
    model = Class
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        section_cache = {
            s.name : s for s in Section.objects.all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                section_obj = section_cache.get(section)
                if not section_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Section: '{section}' not found."})
                    continue
                
                objs.append(Class(
                    section = section_obj,
                    name = class_name,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Class.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["section", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Class uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )      


class UploadProfCategoryView(APIView):
    model = ProfCategory
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
       
       # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        profclass_cache = {
            (c.name, c.section.name) : c for c in Class.objects.select_related("section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                class_obj = profclass_cache.get((class_name, section))
                if not class_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Class: '{class_name}' not found for section: {section}"})
                    continue
                
                objs.append(ProfCategory(
                    profclass = class_obj,
                    name = category,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                ProfCategory.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["profclass", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} ProfCategory uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )
                
class UploadProfSubCategoryView(APIView):
    model = ProfSubCategory
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "subcategory", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
       
       # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        category_cache = {
            (p.name, 
             p.profclass.name,
             p.profclass.section.name) : p
            for p in ProfCategory.objects.select_related("profclass__section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                subcategory = clean(row.get("subcategory"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                category_obj = category_cache.get((category, class_name, section))
                if not category_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Category: '{category}' not found for class: {class_name}, section: {section}"})
                    continue
                
                objs.append(ProfSubCategory(
                    category = category_obj,
                    name = subcategory,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                ProfSubCategory.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["category", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} ProfSubCategory uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )
                

class UploadSectorView(APIView):
    model = Sector
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "subcategory", "sector", "code", "is_hidden", "on_hold", "hold_date"])    
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        subcategory_cache = {
            (sb.name,
             sb.category.name,
             sb.category.profclass.name,
             sb.category.profclass.section.name) : sb
            for sb in ProfSubCategory.objects.select_related("category__profclass__section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                subcategory = clean(row.get("subcategory"))
                sector = clean(row.get("sector"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                subcategory_obj = subcategory_cache.get((subcategory, category, class_name, section))
                if not subcategory_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"SubCategory: '{subcategory}' not found for category: {category}, class: {class_name}, section: {section}"})
                    continue
                
                objs.append(Sector(
                    subcategory = subcategory_obj,
                    name = sector,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Sector.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["subcategory", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Sector uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )                
                

class UploadSubSectorView(APIView):
    model = SubSector
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "subcategory", "sector", "subsector", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        sector_cache = {
            (s.name,
             s.subcategory.name,
             s.subcategory.category.name,
             s.subcategory.category.profclass.name,
             s.subcategory.category.profclass.section.name) : s
            for s in Sector.objects.select_related("subcategory__category__profclass__section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                subcategory = clean(row.get("subcategory"))
                sector = clean(row.get("sector"))
                subsector = clean(row.get("subsector"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                sector_obj = sector_cache.get((sector, subcategory, category, class_name, section))
                if not sector_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Sector: '{sector}' not found for subcategory: {subcategory}, category: {category}, class: {class_name}, section: {section}"})
                    continue
                
                objs.append(SubSector(
                    sector = sector_obj,
                    name = subsector,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                SubSector.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["sector", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} SubSector uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )                

class UploadDepartmentView(APIView):
    model = Department
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file'] 
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "subcategory", "sector", "subsector", "department", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        subsector_cache = {
            (s.name,
             s.sector.name,
             s.sector.subcategory.name,
             s.sector.subcategory.category.name,
             s.sector.subcategory.category.profclass.name,
             s.sector.subcategory.category.profclass.section.name) : s
            for s in SubSector.objects.select_related("sector__subcategory__category__profclass__section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                subcategory = clean(row.get("subcategory"))
                sector = clean(row.get("sector"))
                subsector = clean(row.get("subsector"))
                department = clean(row.get("department"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                subsector_obj = subsector_cache.get((subsector, sector, subcategory, category, class_name, section))
                if not subsector_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"SubSector: '{subsector}' not found for sector: {sector}, subcategory: {subcategory}, category: {category}, class: {class_name}, section: {section}"})
                    continue
                
                objs.append(Department(
                    subsector = subsector_obj,
                    name = department,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Department.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["subsector", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Department uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )    
                       

class UploadSubDepartmentView(APIView):
    model = SubDepartment
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "subcategory", "sector", "subsector", "department", "subdepartment", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        department_cache = {
            (d.name,
             d.subsector.name,
             d.subsector.sector.name,
             d.subsector.sector.subcategory.name,
             d.subsector.sector.subcategory.category.name,
             d.subsector.sector.subcategory.category.profclass.name,
             d.subsector.sector.subcategory.category.profclass.section.name) : d
            for d in Department.objects.select_related("subsector__sector__subcategory__category__profclass__section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                subcategory = clean(row.get("subcategory"))
                sector = clean(row.get("sector"))
                subsector = clean(row.get("subsector"))
                department = clean(row.get("department"))
                subdepartment = clean(row.get("subdepartment"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, subdepartment, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                department_obj = department_cache.get((department, subsector, sector, subcategory, category, class_name, section))
                if not department_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Department: '{department}' not found for subsector: {subsector}, sector: {sector}, subcategory: {subcategory}, category: {category}, class: {class_name}, section: {section}"})
                    continue
                
                objs.append(SubDepartment(
                    department = department_obj,
                    name = subdepartment,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                SubDepartment.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["department", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Sub Department uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )
     
     
class UploadTypeView(APIView):
    model = Type
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "subcategory", "sector", "subsector", "department", "subdepartment", "type", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)                
                          
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        subdepartment_cache = {
            (sb.name,
             sb.department.name,
             sb.department.subsector.name,
             sb.department.subsector.sector.name,
             sb.department.subsector.sector.subcategory.name,
             sb.department.subsector.sector.subcategory.category.name,
             sb.department.subsector.sector.subcategory.category.profclass.name,
             sb.department.subsector.sector.subcategory.category.profclass.section.name) : sb
            for sb in SubDepartment.objects.select_related("department__subsector__sector__subcategory__category__profclass__section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                subcategory = clean(row.get("subcategory"))
                sector = clean(row.get("sector"))
                subsector = clean(row.get("subsector"))
                department = clean(row.get("department"))
                subdepartment = clean(row.get("subdepartment"))
                type_name = clean(row.get("type"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, subdepartment, type_name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                subdepartment_obj = subdepartment_cache.get((subdepartment, department, subsector, sector, subcategory, category, class_name, section))
                if not subdepartment_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Sub Department: '{subdepartment}' not found for department: {department}, subsector: {subsector}, sector: {sector}, subcategory: {subcategory}, category: {category}, class: {class_name}, section: {section}"})
                    continue
                
                objs.append(Type(
                    subdepartment = subdepartment_obj,
                    name = type_name,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Type.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["subdepartment", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Type uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )      


class UploadBrandView(APIView):
    model = Brand
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        
        try:
            df = read_file(file, required_columns=["section", "class", "category", "subcategory", "sector", "subsector", "department", "subdepartment", "type", "brand", "code", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty."}, status=400)
        
        type_cache = {
            (t.name,
             t.subdepartment.name,
             t.subdepartment.department.name,
             t.subdepartment.department.subsector.name,
             t.subdepartment.department.subsector.sector.name,
             t.subdepartment.department.subsector.sector.subcategory.name,
             t.subdepartment.department.subsector.sector.subcategory.category.name,
             t.subdepartment.department.subsector.sector.subcategory.category.profclass.name,
             t.subdepartment.department.subsector.sector.subcategory.category.profclass.section.name) : t
            for t in Type.objects.select_related("subdepartment__department__subsector__sector__subcategory__category__profclass__section").all()
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                    
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                section = clean(row.get("section"))
                class_name = clean(row.get("class"))
                category = clean(row.get("category"))
                subcategory = clean(row.get("subcategory"))
                sector = clean(row.get("sector"))
                subsector = clean(row.get("subsector"))
                department = clean(row.get("department"))
                subdepartment = clean(row.get("subdepartment"))
                type_name = clean(row.get("type"))
                brand_name = clean(row.get("brand"))
                code = row.get("code")
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, subdepartment, type_name, brand_name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                type_obj = type_cache.get((type_name, subdepartment, department, subsector, sector, subcategory, category, class_name, section))
                
                if not type_obj:
                    invalid_rows.append({"row": idx + 2, "error": f"Type: '{type_name}' not found for subdepartment: {subdepartment}, department: {department}, subsector: {subsector}, sector: {sector}, subcategory: {subcategory}, category: {category}, class: {class_name}, section: {section}"})
                    continue
                
                objs.append(Brand(
                    type = type_obj,
                    name = brand_name,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Brand.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["type", "name"],
                    update_fields=["code", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Brand uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )


class UploadDesignationView(APIView):
    model = Designation
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def post(self, request):
        category = request.query_params.get('category')
        if check_designation_category(category) == False:
            return Response({"error": "Invalid category."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["name","display_name", "code", "reporting_designation", "is_hidden", "on_hold", "hold_date"])
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
         
        # Check if the DataFrame is empty
        if df.empty:
            return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
        # We map the designation 'name' to the actual object
        designation_cache = {
            d.name: d for d in Designation.objects.filter(category=category)
        }
        
        objs = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            try:
                hold_date = row.get('hold_date')
                if pd.isna(hold_date):  # check for NaT or NaN
                    hold_date = None
                else:
                    hold_date = pd.to_datetime(hold_date).date()
                
                # Normalize boolean fields
                is_hidden = normalize_bool(row.get("is_hidden"))
                on_hold = normalize_bool(row.get("on_hold"))
                
                # Calculate hidden and on_hold values
                is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
                # Clean text safely
                name = clean(row.get("name") or "")
                display_name = clean(row.get("display_name") or "")
                code = row.get("code")
                reporting_designation_name = clean(row.get("reporting_designation") or "")
                
                if not all([name, display_name, code, reporting_designation_name]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required field(s)"})
                    continue
                
                if check_designation_name(name) == False:
                    invalid_rows.append({"row": idx + 2, "error": "Invalid name format"})
                    continue
                
                reporting_designation_obj = None
                calculated_post_no = 0
                
                if reporting_designation_name:
                    if check_designation_name(reporting_designation_name) == False:
                         invalid_rows.append({"row": idx + 2, "error": "Invalid reporting designation format"})
                         continue
                
                    # get the actual object from designation_cache
                    reporting_designation_obj = designation_cache.get(reporting_designation_name)
                    if not reporting_designation_obj:
                        invalid_rows.append({"row": idx + 2, "error": f"Designation: '{reporting_designation_name}' not found for category: {category}"})
                        continue
                        
                    calculated_post_no = reporting_designation_obj.post_no + 1
                
                objs.append(Designation(
                    reporting_designation = reporting_designation_obj,
                    name = name,
                    display_name = display_name,
                    code = code,
                    post_no = calculated_post_no,
                    category = category,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
            
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": f"An unexpected error occurred: {str(e)}"})
        
        if not objs:
            return Response({
                "error": "No valid records found in the file.",
                "invalid_rows": invalid_rows
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                Designation.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "display_name", "post_no", "reporting_designation", "category", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Designation uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )
            
# class UploadPostModelView(APIView):
#     model = PostModel
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
#     def post(self, request):
#         serializer = FileUploadSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         file = serializer.validated_data['file']

#         try:
#             df = read_file(file, required_columns=["section", "class", "category", "subcategory", "sector", "subsector", "department", "subdepartment", "type", "brand", "postmodel", "code", "is_hidden", "on_hold", "hold_date"])
#         except ValidationError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": f"Failed to read file: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
#         # Check if the DataFrame is empty
#         if df.empty:
#             return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)
        
#         objs = []
#         invalid_rows = []
        
#         for idx, row in df.iterrows():
#             try:
#                 hold_date = row.get('hold_date')
#                 if pd.isna(hold_date):  # check for NaT or NaN
#                     hold_date = None
#                 else:
#                     hold_date = pd.to_datetime(hold_date).date()
                    
#                 # Normalize boolean fields
#                 is_hidden = normalize_bool(row.get("is_hidden"))
#                 on_hold = normalize_bool(row.get("on_hold"))
                
#                 # Calculate hidden and on_hold values
#                 is_hidden, on_hold, hold_date = calculate_hidden_hold(is_hidden, on_hold, hold_date)
                
#                 # Clean text safely
#                 section = clean(row.get("section"))
#                 class_name = clean(row.get("class"))
#                 category = clean(row.get("category"))
#                 subcategory = clean(row.get("subcategory"))
#                 sector = clean(row.get("sector"))
#                 subsector = clean(row.get("subsector"))
#                 department = clean(row.get("department"))
#                 subdepartment = clean(row.get("subdepartment"))
#                 type_name = clean(row.get("type"))
#                 brand_name = clean(row.get("brand"))
#                 postmodel = clean(row.get("postmodel"))
#                 code = row.get("code")
                
#                 # Skip invalid rows early
#                 if not all([section, class_name, category, subcategory, sector, subsector, department, subdepartment, type_name, brand_name, postmodel, code]):
#                     invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
#                     continue
                
#                 try:
#                     brand_obj = Brand.objects.get(
#                         name=brand_name,
#                         type__name=type_name,
#                         type__subdepartment__name=subdepartment,
#                         type__subdepartment__department__name=department,
#                         type__subdepartment__department__subsector__name=subsector,
#                         type__subdepartment__department__subsector__sector__name=sector,
#                         type__subdepartment__department__subsector__sector__subcategory__name=subcategory,
#                         type__subdepartment__department__subsector__sector__subcategory__category__name=category,
#                         type__subdepartment__department__subsector__sector__subcategory__category__profclass__name=class_name,
#                         type__subdepartment__department__subsector__sector__subcategory__category__profclass__section__name=section
#                     )
#                 except Brand.DoesNotExist:
#                     invalid_rows.append({"row": idx + 2, "error": f"Brand: '{brand_name}' not found for subdepartment: {subdepartment}, department: {department}, subsector: {subsector}, sector: {sector}, subcategory: {subcategory}, category: {category}, class: {class_name}, section: {section}"})
#                     continue
                
#                 objs.append(PostModel(
#                     brand=brand_obj,
#                     name=postmodel,
#                     code=code,
#                     is_hidden=is_hidden,
#                     on_hold=on_hold,
#                     hold_date=hold_date
#                 ))
#             except Exception as e:
#                 invalid_rows.append({"row": idx + 2, "error": str(e)})
        
#         if not objs:
#             return Response({"error": "No valid rows found in the file"}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             with transaction.atomic():
#                 PostModel.objects.bulk_create(
#                     objs,
#                     update_conflicts=True,
#                     unique_fields=["code"],
#                     update_fields=["name", "is_hidden", "on_hold", "hold_date"],
#                 )
#         except Exception as e: 
#             return Response({"error": f"Failed to create records: {e}"}, status=400)
        
#         return Response(
#             {
#                 "message": f"{len(objs)} PostModel uploaded successfully.",
#                 "invalid_rows": invalid_rows
#             }, status=status.HTTP_201_CREATED
#         )
                   
                                                    

class ModelAndAccessRulesView(APIView):
    permission_classes = [IsAuthenticated]
    # serializer_class = BulkModelAccessSerializer
    
    def get(self, request, user_id=None):
        if user_id==None:
            user_id = request.user.id
        user = get_object_or_404(CustomUser, id=user_id)
        serializer = ModelAndRecordRuleAccessOutputSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        if user.is_verified==False:
            return Response({"message":"You have not permission to access this resource"}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ModelAndRecordRuleAccessInputSerializer(data=request.data, context={"request": request} )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class ResidentialSearchView(APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # that variable help to RecordRuleMixin class
        self.action = 'list'
        
        serializer = ResidentialSearchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        search_key = data.get("search_key", "glob")
        glob_name = data.get("glob")
        continent_name = data.get("continent")
        country_name = data.get("country")
        state_name = data.get("state")
        district_name = data.get("district")
        taluka_name = data.get("taluka")
        city_village_name = data.get("city_village")
        ward_name = data.get("ward")
        society_name = data.get("society")
        block_name = data.get("block")
        floor_no = data.get("floor")
        house_no = data.get("house")
        room_no = data.get("room")
        
        filters = {}
        if search_key == "glob":
            qs = get_regular_query(Glob)
            if glob_name:
                filters['name__icontains'] = glob_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj).data,
                    "continent": None,
                    "country": None,
                    "state": None,
                    "district": None,
                    "taluka": None,
                    "city_village": None,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        elif search_key == "continent":
            qs = get_regular_query(Continent).select_related('glob')
            if glob_name:
                filters['glob__name__icontains']=glob_name
            if continent_name:
                filters['name__icontains'] = continent_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.glob).data,
                    "continent": ContinentIdNameSerializer(obj).data,
                    "country": None,
                    "state": None,
                    "district": None,
                    "taluka": None,
                    "city_village": None,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        elif search_key == "country":
            qs = get_regular_query(Country).select_related('continent__glob')
            if glob_name:
                filters['continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['continent__name__icontains'] = continent_name
            if country_name:
                filters['name__icontains'] = country_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.continent).data,
                    "country": CountryIdNameSerializer(obj).data,
                    "state": None,
                    "district": None,
                    "taluka": None,
                    "city_village": None,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        elif search_key == "state":
            qs = get_regular_query(State).select_related('country__continent__glob')
            if glob_name:
                filters['country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['country__continent__name__icontains'] = continent_name
            if country_name:
                filters['country__name__icontains'] = country_name
            if state_name:
                filters['name__icontains'] = state_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.country.continent).data,
                    "country": CountryIdNameSerializer(obj.country).data,
                    "state": StateIdNameSerializer(obj).data,
                    "district": None,
                    "taluka": None,
                    "city_village": None,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        elif search_key == "district":
            qs = get_regular_query(District).select_related('state__country__continent__glob')
            if glob_name:
                filters['state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['state__country__name__icontains'] = country_name
            if state_name:
                filters['state__name__icontains'] = state_name
            if district_name:
                filters['name__icontains'] = district_name
                
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.state.country).data,
                    "state": StateIdNameSerializer(obj.state).data,
                    "district": DistrictIdNameSerializer(obj).data,
                    "taluka": None,
                    "city_village": None,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        elif search_key == "taluka":
            qs = get_regular_query(Taluka).select_related('district__state__country__continent__glob')
            if glob_name:
                filters['district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['district__state__country__name__icontains'] = country_name
            if state_name:
                filters['district__state__name__icontains'] = state_name
            if district_name:
                filters['district__name__icontains'] = district_name
            if taluka_name:
                filters['name__icontains'] = taluka_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.district.state.country).data,
                    "state": StateIdNameSerializer(obj.district.state).data,
                    "district": DistrictIdNameSerializer(obj.district).data,
                    "taluka": TalukaIdNameSerializer(obj).data,
                    "city_village": None,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        elif search_key == "city_village":
            qs = get_regular_query(CityVillage).select_related('taluka__district__state__country__continent__glob')
            if glob_name:
                filters['taluka__district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['taluka__district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['taluka__district__state__country__name__icontains'] = country_name
            if state_name:
                filters['taluka__district__state__name__icontains'] = state_name
            if district_name:
                filters['taluka__district__name__icontains'] = district_name
            if taluka_name:
                filters['taluka__name__icontains'] = taluka_name
            if city_village_name:
                filters['name__icontains'] = city_village_name
            
            qs = qs.filter(**filters)            
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.taluka.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.taluka.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.taluka.district.state.country).data,
                    "state": StateIdNameSerializer(obj.taluka.district.state).data,
                    "district": DistrictIdNameSerializer(obj.taluka.district).data,
                    "taluka": TalukaIdNameSerializer(obj.taluka).data,
                    "city_village": CityVillageIdNameSerializer(obj).data,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]
        
        elif search_key == "ward":
            qs = get_regular_query(Ward).select_related('city_village__taluka__district__state__country__continent__glob')
            if glob_name:
                filters['city_village__taluka__district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['city_village__taluka__district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['city_village__taluka__district__state__country__name__icontains'] = country_name
            if state_name:
                filters['city_village__taluka__district__state__name__icontains'] = state_name
            if district_name:
                filters['city_village__taluka__district__name__icontains'] = district_name
            if taluka_name:
                filters['city_village__taluka__name__icontains'] = taluka_name
            if city_village_name:
                filters['city_village__name__icontains'] = city_village_name
            if ward_name:
                filters['name__icontains'] = ward_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.city_village.taluka.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.city_village.taluka.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.city_village.taluka.district.state.country).data,
                    "state": StateIdNameSerializer(obj.city_village.taluka.district.state).data,
                    "district": DistrictIdNameSerializer(obj.city_village.taluka.district).data,
                    "taluka": TalukaIdNameSerializer(obj.city_village.taluka).data,
                    "city_village": CityVillageIdNameSerializer(obj.city_village).data,
                    "ward": WardIdNameSerializer(obj).data,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]
        
        elif search_key == "society":
            qs = get_regular_query(Society).select_related('ward__city_village__taluka__district__state__country__continent__glob')
            
            if glob_name:
                filters['ward__city_village__taluka__district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['ward__city_village__taluka__district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['ward__city_village__taluka__district__state__country__name__icontains'] = country_name
            if state_name:
                filters['ward__city_village__taluka__district__state__name__icontains'] = state_name
            if district_name:
                filters['ward__city_village__taluka__district__name__icontains'] = district_name
            if taluka_name:
                filters['ward__city_village__taluka__name__icontains'] = taluka_name
            if city_village_name:
                filters['ward__city_village__name__icontains'] = city_village_name
            if ward_name:
                filters['ward__name__icontains'] = ward_name
            if society_name:
                filters['name__icontains'] = society_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.ward.city_village.taluka.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.ward.city_village.taluka.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.ward.city_village.taluka.district.state.country).data,
                    "state": StateIdNameSerializer(obj.ward.city_village.taluka.district.state).data,
                    "district": DistrictIdNameSerializer(obj.ward.city_village.taluka.district).data,
                    "taluka": TalukaIdNameSerializer(obj.ward.city_village.taluka).data,
                    "city_village": CityVillageIdNameSerializer(obj.ward.city_village).data,
                    "ward": WardIdNameSerializer(obj.ward).data,
                    "society": SocietyIdNameSerializer(obj).data,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]
        
        elif search_key == "block":
            qs = get_regular_query(Block).select_related('society__ward__city_village__taluka__district__state__country__continent__glob')
            
            if glob_name:
                filters['society__ward__city_village__taluka__district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['society__ward__city_village__taluka__district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['society__ward__city_village__taluka__district__state__country__name__icontains'] = country_name
            if state_name:
                filters['society__ward__city_village__taluka__district__state__name__icontains'] = state_name
            if district_name:
                filters['society__ward__city_village__taluka__district__name__icontains'] = district_name
            if taluka_name:
                filters['society__ward__city_village__taluka__name__icontains'] = taluka_name
            if city_village_name:
                filters['society__ward__city_village__name__icontains'] = city_village_name
            if ward_name:
                filters['society__ward__name__icontains'] = ward_name
            if society_name:
                filters['society__name__icontains'] = society_name
            if block_name:
                filters['name__icontains'] = block_name
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.society.ward.city_village.taluka.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.society.ward.city_village.taluka.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.society.ward.city_village.taluka.district.state.country).data,
                    "state": StateIdNameSerializer(obj.society.ward.city_village.taluka.district.state).data,
                    "district": DistrictIdNameSerializer(obj.society.ward.city_village.taluka.district).data,
                    "taluka": TalukaIdNameSerializer(obj.society.ward.city_village.taluka).data,
                    "city_village": CityVillageIdNameSerializer(obj.society.ward.city_village).data,
                    "ward": WardIdNameSerializer(obj.society.ward).data,
                    "society": SocietyIdNameSerializer(obj.society).data,
                    "block": BlockIdNameSerializer(obj).data,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]
        
        elif search_key == "floor":
            qs = get_regular_query(Floor).select_related('block__society__ward__city_village__taluka__district__state__country__continent__glob')
            
            if glob_name:
                filters['block__society__ward__city_village__taluka__district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['block__society__ward__city_village__taluka__district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['block__society__ward__city_village__taluka__district__state__country__name__icontains'] = country_name
            if state_name:
                filters['block__society__ward__city_village__taluka__district__state__name__icontains'] = state_name
            if district_name:
                filters['block__society__ward__city_village__taluka__district__name__icontains'] = district_name
            if taluka_name:
                filters['block__society__ward__city_village__taluka__name__icontains'] = taluka_name
            if city_village_name:
                filters['block__society__ward__city_village__name__icontains'] = city_village_name
            if ward_name:
                filters['block__society__ward__name__icontains'] = ward_name
            if society_name:
                filters['block__society__name__icontains'] = society_name
            if block_name:
                filters['block__name__icontains'] = block_name
            if floor_no:
                filters['no'] = floor_no
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.block.society.ward.city_village.taluka.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.block.society.ward.city_village.taluka.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.block.society.ward.city_village.taluka.district.state.country).data,
                    "state": StateIdNameSerializer(obj.block.society.ward.city_village.taluka.district.state).data,
                    "district": DistrictIdNameSerializer(obj.block.society.ward.city_village.taluka.district).data,
                    "taluka": TalukaIdNameSerializer(obj.block.society.ward.city_village.taluka).data,
                    "city_village": CityVillageIdNameSerializer(obj.block.society.ward.city_village).data,
                    "ward": WardIdNameSerializer(obj.block.society.ward).data,
                    "society": SocietyIdNameSerializer(obj.block.society).data,
                    "block": BlockIdNameSerializer(obj.block).data,
                    "floor": FloorIdNameSerializer(obj).data,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        elif search_key == "house":
            qs = get_regular_query(House).select_related('floor__block__society__ward__city_village__taluka__district__state__country__continent__glob')
            
            if glob_name:
                filters['floor__block__society__ward__city_village__taluka__district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['floor__block__society__ward__city_village__taluka__district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['floor__block__society__ward__city_village__taluka__district__state__country__name__icontains'] = country_name
            if state_name:
                filters['floor__block__society__ward__city_village__taluka__district__state__name__icontains'] = state_name
            if district_name:
                filters['floor__block__society__ward__city_village__taluka__district__name__icontains'] = district_name
            if taluka_name:
                filters['floor__block__society__ward__city_village__taluka__name__icontains'] = taluka_name
            if city_village_name:
                filters['floor__block__society__ward__city_village__name__icontains'] = city_village_name
            if ward_name:
                filters['floor__block__society__ward__name__icontains'] = ward_name
            if society_name:
                filters['floor__block__society__name__icontains'] = society_name
            if block_name:
                filters['floor__block__name__icontains'] = block_name
            if floor_no:
                filters['floor__no'] = floor_no
            if house_no:
                filters['no'] = house_no
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.floor.block.society.ward.city_village.taluka.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.floor.block.society.ward.city_village.taluka.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.floor.block.society.ward.city_village.taluka.district.state.country).data,
                    "state": StateIdNameSerializer(obj.floor.block.society.ward.city_village.taluka.district.state).data,
                    "district": DistrictIdNameSerializer(obj.floor.block.society.ward.city_village.taluka.district).data,
                    "taluka": TalukaIdNameSerializer(obj.floor.block.society.ward.city_village.taluka).data,
                    "city_village": CityVillageIdNameSerializer(obj.floor.block.society.ward.city_village).data,
                    "ward": WardIdNameSerializer(obj.floor.block.society.ward).data,
                    "society": SocietyIdNameSerializer(obj.floor.block.society).data,
                    "block": BlockIdNameSerializer(obj.floor.block).data,
                    "floor": FloorIdNameSerializer(obj.floor).data,
                    "house": HouseIdNameSerializer(obj).data,
                    "room": None
                }
                for obj in qs
            ]
        
        elif search_key == "room":
            qs = get_regular_query(Room).select_related('house__floor__block__society__ward__city_village__taluka__district__state__country__continent__glob')
            if glob_name:
                filters['house__floor__block__society__ward__city_village__taluka__district__state__country__continent__glob__name__icontains'] = glob_name
            if continent_name:
                filters['house__floor__block__society__ward__city_village__taluka__district__state__country__continent__name__icontains'] = continent_name
            if country_name:
                filters['house__floor__block__society__ward__city_village__taluka__district__state__country__name__icontains'] = country_name
            if state_name:
                filters['house__floor__block__society__ward__city_village__taluka__district__state__name__icontains'] = state_name
            if district_name:
                filters['house__floor__block__society__ward__city_village__taluka__district__name__icontains'] = district_name
            if taluka_name:
                filters['house__floor__block__society__ward__city_village__taluka__name__icontains'] = taluka_name
            if city_village_name:
                filters['house__floor__block__society__ward__city_village__name__icontains'] = city_village_name
            if ward_name:
                filters['house__floor__block__society__ward__name__icontains'] = ward_name
            if society_name:
                filters['house__floor__block__society__name__icontains'] = society_name
            if block_name:
                filters['house__floor__block__name__icontains'] = block_name
            if floor_no:
                filters['house__floor__no'] = floor_no
            if house_no:
                filters['house__no'] = house_no
            if room_no:
                filters['no'] = room_no
            
            qs = qs.filter(**filters)
            qs = self.apply_record_rules(qs)
            # qs = qs[:10]

            results = [
                {
                    "glob": GlobIdNameSerializer(obj.house.floor.block.society.ward.city_village.taluka.district.state.country.continent.glob).data,
                    "continent": ContinentIdNameSerializer(obj.house.floor.block.society.ward.city_village.taluka.district.state.country.continent).data,
                    "country": CountryIdNameSerializer(obj.house.floor.block.society.ward.city_village.taluka.district.state.country).data,
                    "state": StateIdNameSerializer(obj.house.floor.block.society.ward.city_village.taluka.district.state).data,
                    "district": DistrictIdNameSerializer(obj.house.floor.block.society.ward.city_village.taluka.district).data,
                    "taluka": TalukaIdNameSerializer(obj.house.floor.block.society.ward.city_village.taluka).data,
                    "city_village": CityVillageIdNameSerializer(obj.house.floor.block.society.ward.city_village).data,
                    "ward": WardIdNameSerializer(obj.house.floor.block.society.ward).data,
                    "society": SocietyIdNameSerializer(obj.house.floor.block.society).data,
                    "block": BlockIdNameSerializer(obj.house.floor.block).data,
                    "floor": FloorIdNameSerializer(obj.house.floor).data,
                    "house": HouseIdNameSerializer(obj.house).data,
                    "room": RoomIdNameSerializer(obj).data
                }
                for obj in qs
            ]
            
        else:
            # fallback → default globs
            qs = get_regular_query(Glob)
            qs = self.apply_record_rules(qs)
            qs = qs[:10]
            results = [
                {
                    "glob": GlobIdNameSerializer(obj).data,
                    "continent": None,
                    "country": None,
                    "state": None,
                    "district": None,
                    "taluka": None,
                    "city_village": None,
                    "ward": None,
                    "society": None,
                    "block": None,
                    "floor": None,
                    "house": None,
                    "room": None
                }
                for obj in qs
            ]

        # Return unified response structure
        # output = ResidentialOutputSerializer(results, many=True)
        # return Response(output.data, status=status.HTTP_200_OK)
        return Response(results, status=status.HTTP_200_OK) 
       
            

class PersonalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PersonalInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        search_key = data.get('search_key')
        religion_name = data.get('religion')
        sampraday_name = data.get('sampraday')
        panth_name = data.get('panth')
        awastha_name = data.get('awastha')
        varna_name = data.get('varna')
        caste_name = data.get('caste')
        subcaste_name = data.get('subcaste')
        gotra_name = data.get('gotra')
        subgotra_name = data.get('subgotra')
        kul_name = data.get('kul')
        vansh_name = data.get('vansh')
        family_name = data.get('family')
        pidhi_name = data.get('pidhi')
        
        
        filters = {}
        awastha_objs = get_regular_query(Awastha)
        if awastha_objs.exists():
            awastha_data = AwasthaIdNameSerializer(awastha_objs, many=True).data
        else:
            awastha_data = []
            
        pidhi_objs = get_regular_query(Pidhi)
        if pidhi_objs.exists():
            pidhi_data = PidhiIdNameSerializer(pidhi_objs, many=True).data
        else:
            pidhi_data = []
            
        if search_key == "religion":
            qs = get_regular_query(Religion)
            if religion_name:
                qs = qs.filter(name__icontains=religion_name)
            qs = qs[:10]
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj).data,
                    "sampraday": None,
                    "panth": None,
                    "awastha": awastha_data,
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data,
                }
                for obj in qs
            ]

        elif search_key == "sampraday":
            qs = get_regular_query(Sampraday).select_related('religion')
            if religion_name:
                filters['religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['name__icontains'] = sampraday_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj).data,
                    "panth": None,
                    "awastha": awastha_data,
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data,
                }
                for obj in qs
            ]
        
        elif search_key == "panth":
            qs = get_regular_query(Panth).select_related('sampraday__religion')
            if religion_name:
                filters['sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['name__icontains'] = panth_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.sampraday).data,
                    "panth": PanthIdNameSerializer(obj).data,
                    "awastha": awastha_data,
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data,
                }
                for obj in qs
            ]
        # elif search_key == "awastha":
        #     qs = get_regular_query(Awastha).select_related('panth__sampraday__religion')
        #     if religion_name:
        #         filters['panth__sampraday__religion__name__icontains'] = religion_name
        #     if sampraday_name:
        #         filters['panth__sampraday__name__icontains'] = sampraday_name
        #     if panth_name:
        #         filters['panth__name__icontains'] = panth_name
        #     if awastha_name:
        #         filters['name__icontains'] = awastha_name
            
        #     qs = qs.filter(**filters)
        #     qs = qs[:10]
            
        #     results = [
        #         {
        #             "religion": ReligionIdNameSerializer(obj.panth.sampraday.religion).data,
        #             "sampraday": SampradayIdNameSerializer(obj.panth.sampraday).data,
        #             "panth": PanthIdNameSerializer(obj.panth).data,
        #             "awastha": AwasthaIdNameSerializer(obj).data,
        #             "varna": None,
        #             "caste": None,
        #             "subcaste": None,
        #             "gotra": None,
        #             "subgotra": None,
        #             "kul": None,
        #             "vansh": None,
        #             "family": None,
        #             "pidhi": None,
        #         }
        #         for obj in qs
        #     ]
        
        elif search_key == "varna":
            qs = get_regular_query(Varna).select_related('panth__sampraday__religion')
            if religion_name:
                filters['panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['panth__name__icontains'] = panth_name
            if varna_name:
                filters['name__icontains'] = varna_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj).data,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data,
                }
                for obj in qs
            ]
        
        
        elif search_key == "caste":
            qs = get_regular_query(Caste).select_related('varna__panth__sampraday__religion')
            if religion_name:
                filters['varna__panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['varna__panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['varna__panth__name__icontains'] = panth_name
            if varna_name:
                filters['varna__name__icontains'] = varna_name
            if caste_name:
                filters['name__icontains'] = caste_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.varna.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj.varna).data,
                    "caste": CasteIdNameSerializer(obj).data,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data
                }
                for obj in qs
            ] 
        
        
        elif search_key == "subcaste":
            qs = get_regular_query(SubCaste).select_related('caste__varna__panth__sampraday__religion')
            if religion_name:
                filters['caste__varna__panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['caste__varna__panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['caste__varna__panth__name__icontains'] = panth_name
            if varna_name:
                filters['caste__varna__name__icontains'] = varna_name
            if caste_name:
                filters['caste__name__icontains'] = caste_name
            if subcaste_name:
                filters['name__icontains'] = subcaste_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.caste.varna.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj).data,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data
                }
                for obj in qs
            ] 
        
        
        elif search_key == "gotra":
            qs = get_regular_query(Gotra).select_related('subcaste__caste__varna__panth__sampraday__religion')
            if religion_name:
                filters['subcaste__caste__varna__panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['subcaste__caste__varna__panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['subcaste__caste__varna__panth__name__icontains'] = panth_name
            if varna_name:
                filters['subcaste__caste__varna__name__icontains'] = varna_name
            if caste_name:
                filters['subcaste__caste__name__icontains'] = caste_name
            if subcaste_name:
                filters['subcaste__name__icontains'] = subcaste_name
            if gotra_name:
                filters['name__icontains'] = gotra_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.subcaste.caste.varna.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj).data,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data
                }
                for obj in qs
            ]  
        
        
        elif search_key == "subgotra":
            qs = get_regular_query(SubGotra).select_related('gotra__subcaste__caste__varna__panth__sampraday__religion')
            if religion_name:
                filters['gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['gotra__subcaste__caste__varna__panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['gotra__subcaste__caste__varna__panth__name__icontains'] = panth_name
            if varna_name:
                filters['gotra__subcaste__caste__varna__name__icontains'] = varna_name
            if caste_name:
                filters['gotra__subcaste__caste__name__icontains'] = caste_name
            if subcaste_name:
                filters['gotra__subcaste__name__icontains'] = subcaste_name
            if gotra_name:
                filters['gotra__name__icontains'] = gotra_name
            if subgotra_name:
                filters['name__icontains'] = subgotra_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.gotra.subcaste.caste.varna.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj).data,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data
                }
                for obj in qs
            ]
        
        elif search_key == "kul":
            qs = get_regular_query(Kul).select_related('subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion')
            if religion_name:
                filters['subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['subgotra__gotra__subcaste__caste__varna__panth__name__icontains'] = panth_name
            if varna_name:
                filters['subgotra__gotra__subcaste__caste__varna__name__icontains'] = varna_name
            if caste_name:
                filters['subgotra__gotra__subcaste__caste__name__icontains'] = caste_name
            if subcaste_name:
                filters['subgotra__gotra__subcaste__name__icontains'] = subcaste_name
            if gotra_name:
                filters['subgotra__gotra__name__icontains'] = gotra_name
            if subgotra_name:
                filters['subgotra__name__icontains'] = subgotra_name
            if kul_name:
                filters['name__icontains'] = kul_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.subgotra.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.subgotra.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.subgotra.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj.subgotra).data,
                    "kul": KulIdNameSerializer(obj).data,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data
                }
                for obj in qs
            ]
        
        elif search_key == "vansh":
            qs = get_regular_query(Vansh).select_related('kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion')
            if religion_name:
                filters['kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['kul__subgotra__gotra__subcaste__caste__varna__panth__name__icontains'] = panth_name
            if varna_name:
                filters['kul__subgotra__gotra__subcaste__caste__varna__name__icontains'] = varna_name
            if caste_name:
                filters['kul__subgotra__gotra__subcaste__caste__name__icontains'] = caste_name
            if subcaste_name:
                filters['kul__subgotra__gotra__subcaste__name__icontains'] = subcaste_name
            if gotra_name:
                filters['kul__subgotra__gotra__name__icontains'] = gotra_name  
            if subgotra_name:
                filters['kul__subgotra__name__icontains'] = subgotra_name  
            if kul_name:
                filters['kul__name__icontains'] = kul_name
            if vansh_name:
                filters['name__icontains'] = vansh_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.kul.subgotra.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.kul.subgotra.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj.kul.subgotra).data,
                    "kul": KulIdNameSerializer(obj.kul).data,
                    "vansh": VanshIdNameSerializer(obj).data,
                    "family": None,
                    "pidhi": pidhi_data
                }
                for obj in qs
            ]  
            
        elif search_key == "family":
            qs = get_regular_query(Family).select_related('vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion')
            if religion_name:
                filters['vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains'] = religion_name
            if sampraday_name:
                filters['vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains'] = sampraday_name
            if panth_name:
                filters['vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__name__icontains'] = panth_name
            if varna_name:
                filters['vansh__kul__subgotra__gotra__subcaste__caste__varna__name__icontains'] = varna_name
            if caste_name:
                filters['vansh__kul__subgotra__gotra__subcaste__caste__name__icontains'] = caste_name
            if subcaste_name:
                filters['vansh__kul__subgotra__gotra__subcaste__name__icontains'] = subcaste_name
            if gotra_name:
                filters['vansh__kul__subgotra__gotra__name__icontains'] = gotra_name  
            if subgotra_name:
                filters['vansh__kul__subgotra__name__icontains'] = subgotra_name  
            if kul_name:
                filters['vansh__kul__name__icontains'] = kul_name
            if vansh_name:    
                filters['vansh__name__icontains'] = vansh_name
            if family_name:
                filters['name__icontains'] = family_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth).data,
                    "awastha": awastha_data,
                    "varna": VarnaIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.vansh.kul.subgotra.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj.vansh.kul.subgotra).data,
                    "kul": KulIdNameSerializer(obj.vansh.kul).data,
                    "vansh": VanshIdNameSerializer(obj.vansh).data,
                    "family": FamilyIdNameSerializer(obj).data,
                    "pidhi": pidhi_data
                }                
                for obj in qs
            ]

        
        # elif search_key == "pidhi":
        #     qs = get_regular_query(Pidhi).select_related('family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion')
        #     if pidhi_name:
        #         filters['name__icontains'] = pidhi_name
        #     if family_name:
        #         filters['family__name__icontains'] = family_name
        #     if vansh_name:
        #         filters['family__vansh__name__icontains'] = vansh_name    
        #     if kul_name:
        #         filters['family__vansh__kul__name__icontains'] = kul_name
        #     if subgotra_name:
        #         filters['family__vansh__kul__subgotra__name__icontains'] = subgotra_name  
        #     if gotra_name:
        #         filters['family__vansh__kul__subgotra__gotra__name__icontains'] = gotra_name  
        #     if subcaste_name:
        #         filters['family__vansh__kul__subgotra__gotra__subcaste__name__icontains'] = subcaste_name
        #     if caste_name:
        #         filters['family__vansh__kul__subgotra__gotra__subcaste__caste__name__icontains'] = caste_name
        #     if varna_name:
        #         filters['family__vansh__kul__subgotra__gotra__subcaste__caste__varna__name__icontains'] = varna_name
        #     if awastha_name:
        #         filters['family__vansh__kul__subgotra__gotra__subcaste__caste__varna__name__icontains'] = awastha_name
        #     if panth_name:
        #         filters['family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__name__icontains'] = panth_name
        #     if sampraday_name:
        #         filters['family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains'] = sampraday_name
        #     if religion_name:
        #         filters['family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains'] = religion_name
            
        #     qs = qs.filter(**filters)
        #     qs = qs[:10]
            
        #     results = [
        #         {
        #             "religion": ReligionIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
        #             "sampraday": SampradayIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
        #             "panth": PanthIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth).data,
        #             "awastha": AwasthaIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna.awastha).data,
        #             "varna": VarnaIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna).data,
        #             "caste": CasteIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste).data,
        #             "subcaste": SubCasteIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste).data,
        #             "gotra": GotraIdNameSerializer(obj.family.vansh.kul.subgotra.gotra).data,
        #             "subgotra": SubGotraIdNameSerializer(obj.family.vansh.kul.subgotra).data,
        #             "kul": KulIdNameSerializer(obj.family.vansh.kul).data,
        #             "vansh": VanshIdNameSerializer(obj.family.vansh).data,
        #             "family": FamilyIdNameSerializer(obj.family).data,
        #             "pidhi": PidhiIdNameSerializer(obj).data
        #         }                
        #         for obj in qs
        #     ]
        
        else:
            # fallback - default religions
            qs = get_regular_query(Religion)
            qs = qs[:10]
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj).data,
                    "sampraday": None,
                    "panth": None,
                    "awastha": awastha_data,
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": pidhi_data
                }                
                for obj in qs
            ]
        
        # return unified response structure
        output = PersonalOutputSerializer(results, many=True)
        return Response(results, status=status.HTTP_200_OK)
        # return Response(output.data, status=200)


class ProfessionalSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ProfessionalInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        search_key = data.get("search_key")  
        section_name = data.get("section")
        profclass_name = data.get("profclass")
        category_name = data.get("category")
        subcategory_name = data.get("subcategory")
        sector_name = data.get("sector")
        subsector_name = data.get("subsector")
        department_name = data.get("department")
        subdepartment_name = data.get("subdepartment")
        type_name = data.get("type")
        brand_name = data.get("brand")
        
        
        if search_key == "section":
            qs = get_regular_query(Section)
            if section_name:
                qs = qs.filter(name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj).data,
                    "profclass": None,
                    "category": None,
                    "subcategory": None,
                    "sector": None,
                    "subsector": None,
                    "department": None,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }                
                for obj in qs
            ]
        
        elif search_key == "profclass":
            qs = get_regular_query(Class).select_related("section")
            if profclass_name:
                qs = qs.filter(name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.section).data,
                    "profclass": ClassIdNameSerializer(obj).data,
                    "category": None,
                    "subcategory": None,
                    "sector": None,
                    "subsector": None,
                    "department": None,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "category":
            qs = get_regular_query(ProfCategory).select_related("profclass__section")
            if category_name:
                qs = qs.filter(name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj).data,
                    "subcategory": None,
                    "sector": None,
                    "subsector": None,
                    "department": None,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "subcategory":
            qs = get_regular_query(ProfSubCategory).select_related("category__profclass__section")
            if subcategory_name:
                qs = qs.filter(name__icontains=subcategory_name)
            if category_name:
                qs = qs.filter(category__name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(category__profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(category__profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.category.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.category.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj.category).data,
                    "subcategory": ProfSubCategoryIdNameSerializer(obj).data,
                    "sector": None,
                    "subsector": None,
                    "department": None,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "sector":
            qs = get_regular_query(Sector).select_related("subcategory__category__profclass__section")
            if sector_name:
                qs = qs.filter(name__icontains=sector_name)
            if subcategory_name:
                qs = qs.filter(subcategory__name__icontains=subcategory_name)
            if category_name:
                qs = qs.filter(subcategory__category__name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(subcategory__category__profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(subcategory__category__profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.subcategory.category.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.subcategory.category.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj.subcategory.category).data,
                    "subcategory": ProfSubCategoryIdNameSerializer(obj.subcategory).data,
                    "sector": SectorIdNameSerializer(obj).data,
                    "subsector": None,
                    "department": None,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "subsector":
            qs = get_regular_query(SubSector).select_related("sector__subcategory__category__profclass__section")
            if subsector_name:
                qs = qs.filter(name__icontains=subsector_name)
            if sector_name:
                qs = qs.filter(sector__name__icontains=sector_name)
            if subcategory_name:
                qs = qs.filter(sector__subcategory__name__icontains=subcategory_name)
            if category_name:
                qs = qs.filter(sector__subcategory__category__name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(sector__subcategory__category__profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(sector__subcategory__category__profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.sector.subcategory.category.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.sector.subcategory.category.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj.sector.subcategory.category).data,
                    "subcategory": ProfSubCategoryIdNameSerializer(obj.sector.subcategory).data,
                    "sector": SectorIdNameSerializer(obj.sector).data,
                    "subsector": SubSectorIdNameSerializer(obj).data,
                    "department": None,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "department":
            qs = get_regular_query(Department).select_related("subsector__sector__subcategory__category__profclass__section")
            if department_name:
                qs = qs.filter(name__icontains=department_name)
            if subsector_name:
                qs = qs.filter(subsector__name__icontains=subsector_name)
            if sector_name:
                qs = qs.filter(subsector__sector__name__icontains=sector_name)
            if subcategory_name:
                qs = qs.filter(subsector__sector__subcategory__name__icontains=subcategory_name)
            if category_name:
                qs = qs.filter(subsector__sector__subcategory__category__name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(subsector__sector__subcategory__category__profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(subsector__sector__subcategory__category__profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.subsector.sector.subcategory.category.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.subsector.sector.subcategory.category.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj.subsector.sector.subcategory.category).data,
                    "subcategory": ProfSubCategoryIdNameSerializer(obj.subsector.sector.subcategory).data,
                    "sector": SectorIdNameSerializer(obj.subsector.sector).data,
                    "subsector": SubSectorIdNameSerializer(obj.subsector).data,
                    "department": DepartmentIdNameSerializer(obj).data,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "subdepartment":
            qs = get_regular_query(SubDepartment).select_related("department__subsector__sector__subcategory__category__profclass__section")
            if subdepartment_name:
                qs = qs.filter(name__icontains=subdepartment_name)
            if department_name:
                qs = qs.filter(department__name__icontains=department_name)
            if subsector_name:
                qs = qs.filter(department__subsector__name__icontains=subsector_name)
            if sector_name:
                qs = qs.filter(department__subsector__sector__name__icontains=sector_name)
            if subcategory_name:
                qs = qs.filter(department__subsector__sector__subcategory__name__icontains=subcategory_name)
            if category_name:
                qs = qs.filter(department__subsector__sector__subcategory__category__name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(department__subsector__sector__subcategory__category__profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(department__subsector__sector__subcategory__category__profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.department.subsector.sector.subcategory.category.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.department.subsector.sector.subcategory.category.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj.department.subsector.sector.subcategory.category).data,
                    "subcategory": ProfSubCategoryIdNameSerializer(obj.department.subsector.sector.subcategory).data,
                    "sector": SectorIdNameSerializer(obj.department.subsector.sector).data,
                    "subsector": SubSectorIdNameSerializer(obj.department.subsector).data,
                    "department": DepartmentIdNameSerializer(obj.department).data,
                    "subdepartment": SubDepartmentIdNameSerializer(obj).data,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "type":
            qs = get_regular_query(Type).select_related("subdepartment__department__subsector__sector__subcategory__category__profclass__section")
            if type_name:
                qs = qs.filter(name__icontains=type_name)
            if subdepartment_name:
                qs = qs.filter(subdepartment__name__icontains=subdepartment_name)
            if department_name:
                qs = qs.filter(subdepartment__department__name__icontains=department_name)
            if subsector_name:
                qs = qs.filter(subdepartment__department__subsector__name__icontains=subsector_name)
            if sector_name:
                qs = qs.filter(subdepartment__department__subsector__sector__name__icontains=sector_name)
            if subcategory_name:
                qs = qs.filter(subdepartment__department__subsector__sector__subcategory__name__icontains=subcategory_name)
            if category_name:
                qs = qs.filter(subdepartment__department__subsector__sector__subcategory__category__name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(subdepartment__department__subsector__sector__subcategory__category__profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(subdepartment__department__subsector__sector__subcategory__category__profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.subdepartment.department.subsector.sector.subcategory.category.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.subdepartment.department.subsector.sector.subcategory.category.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj.subdepartment.department.subsector.sector.subcategory.category).data,
                    "subcategory": ProfSubCategoryIdNameSerializer(obj.subdepartment.department.subsector.sector.subcategory).data,
                    "sector": SectorIdNameSerializer(obj.subdepartment.department.subsector.sector).data,
                    "subsector": SubSectorIdNameSerializer(obj.subdepartment.department.subsector).data,
                    "department": DepartmentIdNameSerializer(obj.subdepartment.department).data,
                    "subdepartment": SubDepartmentIdNameSerializer(obj.subdepartment).data,
                    "type": TypeIdNameSerializer(obj).data,
                    "brand": None,
                }
                for obj in qs
            ]
        
        elif search_key == "brand":
            qs = get_regular_query(Brand).select_related("type__subdepartment__department__subsector__sector__subcategory__category__profclass__section")
            if brand_name:
                qs = qs.filter(name__icontains=brand_name)
            if type_name:
                qs = qs.filter(type__name__icontains=type_name)
            if subdepartment_name:
                qs = qs.filter(type__subdepartment__name__icontains=subdepartment_name)
            if department_name:
                qs = qs.filter(type__subdepartment__department__name__icontains=department_name)
            if subsector_name:
                qs = qs.filter(type__subdepartment__department__subsector__name__icontains=subsector_name)
            if sector_name:
                qs = qs.filter(type__subdepartment__department__subsector__sector__name__icontains=sector_name)
            if subcategory_name:
                qs = qs.filter(type__subdepartment__department__subsector__sector__subcategory__name__icontains=subcategory_name)
            if category_name:
                qs = qs.filter(type__subdepartment__department__subsector__sector__subcategory__category__name__icontains=category_name)
            if profclass_name:
                qs = qs.filter(type__subdepartment__department__subsector__sector__subcategory__category__profclass__name__icontains=profclass_name)
            if section_name:
                qs = qs.filter(type__subdepartment__department__subsector__sector__subcategory__category__profclass__section__name__icontains=section_name)
            qs = qs[:10]
            
            results = [
                {
                    "section": SectionIdNameSerializer(obj.type.subdepartment.department.subsector.sector.subcategory.category.profclass.section).data,
                    "profclass": ClassIdNameSerializer(obj.type.subdepartment.department.subsector.sector.subcategory.category.profclass).data,
                    "category": ProfCategoryIdNameSerializer(obj.type.subdepartment.department.subsector.sector.subcategory.category).data,
                    "subcategory": ProfSubCategoryIdNameSerializer(obj.type.subdepartment.department.subsector.sector.subcategory).data,
                    "sector": SectorIdNameSerializer(obj.type.subdepartment.department.subsector.sector).data,
                    "subsector": SubSectorIdNameSerializer(obj.type.subdepartment.department.subsector).data,
                    "department": DepartmentIdNameSerializer(obj.type.subdepartment.department).data,
                    "subdepartment": SubDepartmentIdNameSerializer(obj.type.subdepartment).data,
                    "type": TypeIdNameSerializer(obj.type).data,
                    "brand": BrandIdNameSerializer(obj).data,
                }
                for obj in qs
            ]
            
        
        else:
            # fallback - default sections
            qs = get_regular_query(Section)
            qs = qs[:10]
            results = [
                {
                    "section": SectionIdNameSerializer(obj).data,
                    "profclass": None,
                    "category": None,
                    "subcategory": None,
                    "sector": None,
                    "subsector": None,
                    "department": None,
                    "subdepartment": None,
                    "type": None,
                    "brand": None,
                }
                for obj in qs
            ]
        
        output = ProfessionalOutputSerializer(results, many=True)
        return Response(results, status=status.HTTP_200_OK)
        # return Response(output.data, status=status.HTTP_200_OK)
    
    
class DesignationViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Designation
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    pagination_class = ConfigurationPagination
    FILTER_FIELDS = {
        'category': 'category',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold',
        'search': 'name'
    }
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DesignationSerializer   # For POST, PUT, PATCH
        return DesignationGetSerializer


class DesignationListView(RecordRuleMixin, APIView):
    model = Designation
    permission_classes = [IsAuthenticated]
    def get_base_queryset(self):
        return get_regular_query(self.model)
    
    def get(self, request):
        qs = self.get_base_queryset()
        category = request.query_params.get('category', "").strip()
        
        if category == '':
            return Response(
                {
                    "error": "Query paramter 'category' cannot be empty."
                }, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            qs = qs.filter(category=category)
        
        qs = qs.order_by('code')
        output = DesignationIdNameSerializer(qs, many=True)
        return Response(output.data, status=status.HTTP_200_OK)
    

class DownloadSampleFile(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        router = request.query_params.get('router', "").strip()
        if router == '':
            return Response({"error": "Query paramter 'router' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            file = SampleFile.objects.get(router=router)
        except SampleFile.DoesNotExist:
            return Response({"error": "Sample file not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get sample file: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not file.file:
            return Response({"error": "File not associated with this record."}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({"file_url": file.file.url}, status=status.HTTP_200_OK)


# =======================================================
# Flash Views
# =======================================================

class ProductSearchView(RecordRuleMixin, APIView):
    model = Product
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ProductSearchInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        input_data = serializer.validated_data
        search_key = input_data.get('search_key')
        sector_name = input_data.get('sector')
        brand_name = input_data.get('brand')
        product_name = input_data.get('product')
        
        filters = {}
        if search_key == "sector":
            qs = get_regular_query(Sector)
            if sector_name:
                qs = qs.filter(name__icontains=sector_name)
            qs = qs[:10]
            
            results = [
                {
                    "sector": SectorIdNameSerializer(obj).data,
                    "brand": None,
                    "product": None,
                }
                for obj in qs
            ]
            
        elif search_key == "brand":
            qs = get_regular_query(Brand)
            if brand_name:
                filters['name__icontains'] = brand_name
            if sector_name:
                filters['type__subdepartment__department__subsector__sector__name__icontains'] = sector_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "sector": SectorIdNameSerializer(obj.type.subdepartment.department.subsector.sector).data,
                    "brand": BrandIdNameSerializer(obj).data,
                    "product": None,
                }
                for obj in qs
            ]
        
        elif search_key == "product":
            qs = get_regular_query(Product)
            if product_name:
                filters['name__icontains'] = product_name
            if brand_name:
                filters['brand__name__icontains'] = brand_name
            if sector_name:
                filters['brand__type__subdepartment__department__subsector__sector__name__icontains'] = sector_name
            
            qs = qs.filter(**filters)
            qs = qs[:10]
            
            results = [
                {
                    "sector": SectorIdNameSerializer(obj.brand.type.subdepartment.department.subsector.sector).data,
                    "brand": BrandIdNameSerializer(obj.brand).data,
                    "product": ProductIdNameSerializer(obj).data,
                }
                for obj in qs
            ]
        
        else:
            qs = get_regular_query(Sector)
            qs = qs[:10]
            results = [
                {
                    "sector": SectorIdNameSerializer(obj).data,
                    "brand": None,
                    "product": None,
                }
                for obj in qs
            ]
        
        output_data = ProductSearchOutputSerializer(results, many=True).data
        return Response(output_data, status=status.HTTP_200_OK)
            
                
            
            
class WardFlashView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    model = WardFlash
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get(self, request):
        ward_id = request.query_params.get('ward_id', "").strip()
        if ward_id == '':
            return Response({"error": "Query paramter 'ward_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ward_obj = Ward.objects.get(id=ward_id)
        except Ward.DoesNotExist:
            return Response({"error": "Ward not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get ward: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = WardFlashOutputSerializer(ward_obj.ward_flashes.all(), many=True)
        return Response(serializer.data)

    def post(self, request):
        ward_id = request.query_params.get('ward_id', "").strip()
        if ward_id == '':
            return Response({"error": "Query paramter 'ward_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            ward_obj = Ward.objects.get(id=ward_id)
        except Ward.DoesNotExist:
            return Response({"error": "Ward not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get ward: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = WardFlashBulkInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flash_data = serializer.validated_data.get("flashes", [])
        incoming_flash_ids = [
            f.get("existing_id")
            for f in flash_data
            if f.get("existing_id")
        ]
        try:
            with transaction.atomic():
                # Delete existing flashes which are not included in new request
                WardFlash.objects.filter(ward=ward_obj).exclude(id__in=incoming_flash_ids).delete()
                
                for flash in flash_data:
                    flash_id = flash.pop("existing_id")
                    product = flash.get("product")
                    value = flash.get("value")

                    if flash_id:  # update existing
                        obj = get_object_or_404(WardFlash, id=flash_id, ward=ward_obj)
                        obj.product = product
                        obj.value = value
                        obj.save()
                    else:
                        # Create new flash
                        WardFlash.objects.create(
                            ward=ward_obj,
                            product=product,
                            value=value
                        )
                        
        except Exception as e:
            return Response(
                {
                    "error": f"Failed to update ward flashes.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        updated_ward_flashes = ward_obj.ward_flashes.all()
        serializer = WardFlashOutputSerializer(updated_ward_flashes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SocietyFlashView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    model = SocietyFlash
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get(self, request):
        society_id = request.query_params.get('society_id', "").strip()
        if society_id == '':
            return Response({"error": "Query paramter 'society_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            society_obj = Society.objects.get(id=society_id)
        except Society.DoesNotExist:
            return Response({"error": "Society not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get society: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = SocietyFlashOutputSerializer(society_obj.society_flashes.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        society_id = request.query_params.get('society_id', "").strip()
        if society_id == '':
            return Response({"error": "Query paramter 'society_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            society_obj = Society.objects.get(id=society_id)
        except Society.DoesNotExist:
            return Response({"error": "Society not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get society: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = SocietyFlashBulkInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flash_data = serializer.validated_data.get("flashes", [])
        incoming_flash_ids = [
            f.get("existing_id")
            for f in flash_data
            if f.get("existing_id")
        ]
        
        try:
            with transaction.atomic():
                # Delete existing flashes which are not included in new request
                SocietyFlash.objects.filter(society=society_obj).exclude(id__in=incoming_flash_ids).delete()
                
                for flash in flash_data:
                    flash_id = flash.pop("existing_id")
                    product = flash.get("product")
                    value = flash.get("value")
                    if flash_id:  # update existing
                        obj = get_object_or_404(SocietyFlash, id=flash_id, society=society_obj)
                        obj.product = product
                        obj.value = value
                        obj.save()
                    else:
                        # Create new flash
                        SocietyFlash.objects.create(
                            society=society_obj,
                            product=product,
                            value=value
                        )
                        
        except Exception as e:
            return Response(
                {
                    "error": f"Failed to update society flashes.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
            
        updated_society_flashes = society_obj.society_flashes.all()
        serializer = SocietyFlashOutputSerializer(updated_society_flashes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BlockFlashView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    model = BlockFlash
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get(self, request):
        block_id = request.query_params.get('block_id', "").strip()
        if block_id == '':
            return Response({"error": "Query paramter 'block_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            block_obj = Block.objects.get(id=block_id)
        except Block.DoesNotExist:
            return Response({"error": "Block not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get block: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = BlockFlashOutputSerializer(block_obj.block_flashes.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        block_id = request.query_params.get('block_id', "").strip()
        if block_id == '':
            return Response({"error": "Query paramter 'block_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            block_obj = Block.objects.get(id=block_id)
        except Block.DoesNotExist:
            return Response({"error": "Block not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get block: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = BlockFlashBulkInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flash_data = serializer.validated_data.get("flashes", [])
        incoming_flash_ids = [
            f.get("existing_id")
            for f in flash_data
            if f.get("existing_id")
        ]
        
        try:
            with transaction.atomic():
                # Delete existing flashes which are not included in new request
                BlockFlash.objects.filter(block=block_obj).exclude(id__in=incoming_flash_ids).delete()
                
                for flash in flash_data:
                    flash_id = flash.pop("existing_id")
                    product = flash.get("product")
                    value = flash.get("value")
                    
                    if flash_id:  # update existing
                        obj = get_object_or_404(BlockFlash, id=flash_id, block=block_obj)
                        obj.product = product
                        obj.value = value
                        obj.save()
                    else:
                        # Create new flash
                        BlockFlash.objects.create(
                            block=block_obj,
                            product=product,
                            value=value
                        )

        except Exception as e:
            return Response(
                {
                    "error": f"Failed to update block flashes.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        updated_block_flashes = block_obj.block_flashes.all()
        serializer = BlockFlashOutputSerializer(updated_block_flashes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FloorFlashView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    model = FloorFlash
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get(self, request):
        floor_id = request.query_params.get('floor_id', "").strip()
        if floor_id == '':
            return Response({"error": "Query paramter 'floor_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            floor_obj = Floor.objects.get(id=floor_id)
        except Floor.DoesNotExist:
            return Response({"error": "Floor not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get floor: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = FloorFlashOutputSerializer(floor_obj.floor_flashes.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        floor_id = request.query_params.get('floor_id', "").strip()
        if floor_id == '':
            return Response({"error": "Query paramter 'floor_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            floor_obj = Floor.objects.get(id=floor_id)
        except Floor.DoesNotExist:
            return Response({"error": "Floor not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get floor: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = FloorFlashBulkInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flash_data = serializer.validated_data.get("flashes", [])
        incoming_flash_ids = [
            f.get("existing_id")
            for f in flash_data
            if f.get("existing_id")
        ]
        
        try:
            with transaction.atomic():
                # Delete existing flashes which are not included in new request
                FloorFlash.objects.filter(floor=floor_obj).exclude(id__in=incoming_flash_ids).delete()
                
                for flash in flash_data:
                    flash_id = flash.pop("existing_id")
                    product = flash.get("product")
                    value = flash.get("value")
                    
                    if flash_id:  # update existing
                        obj = get_object_or_404(FloorFlash, id=flash_id, floor=floor_obj)
                        obj.product = product
                        obj.value = value
                        obj.save()
                    else:
                        # Create new flash
                        FloorFlash.objects.create(
                            floor=floor_obj,
                            product=product,
                            value=value
                        )

        except Exception as e:
            return Response(
                {
                    "error": f"Failed to update floor flashes.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        updated_floor_flashes = floor_obj.floor_flashes.all()
        serializer = FloorFlashOutputSerializer(updated_floor_flashes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class HouseFlashView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    model = HouseFlash
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get(self, request):
        house_id = request.query_params.get('house_id', "").strip()
        if house_id == '':
            return Response({"error": "Query paramter 'house_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            house_obj = House.objects.get(id=house_id)
        except House.DoesNotExist:
            return Response({"error": "House not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get house: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = HouseFlashOutputSerializer(house_obj.house_flashes.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        house_id = request.query_params.get('house_id', "").strip()
        if house_id == '':
            return Response({"error": "Query paramter 'house_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            house_obj = House.objects.get(id=house_id)
        except House.DoesNotExist:
            return Response({"error": "House not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get house: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = HouseFlashBulkInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flash_data = serializer.validated_data.get("flashes", [])
        incoming_flash_ids = [
            f.get("existing_id")
            for f in flash_data
            if f.get("existing_id")
        ]
        
        try:
            with transaction.atomic():
                # Delete existing flashes which are not included in new request
                HouseFlash.objects.filter(house=house_obj).exclude(id__in=incoming_flash_ids).delete()
                
                for flash in flash_data:
                    flash_id = flash.pop("existing_id")
                    product = flash.get("product")
                    value = flash.get("value")

                    if flash_id:  # update existing
                        obj = get_object_or_404(HouseFlash, id=flash_id, house=house_obj)
                        obj.product = product
                        obj.value = value
                        obj.save()
                    else:
                        # Create new flash
                        HouseFlash.objects.create(
                            house=house_obj,
                            product=product,
                            value=value
                        )

        except Exception as e:
            return Response(
                {
                    "error": f"Failed to update house flashes.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        updated_house_flashes = house_obj.house_flashes.all()
        serializer = HouseFlashOutputSerializer(updated_house_flashes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RoomFlashView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    model = RoomFlash
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get(self, request):
        room_id = request.query_params.get('room_id', "").strip()
        if room_id == '':
            return Response({"error": "Query paramter 'room_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            room_obj = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get room: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = RoomFlashOutputSerializer(room_obj.room_flashes.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        room_id = request.query_params.get('room_id', "").strip()
        if room_id == '':
            return Response({"error": "Query paramter 'room_id' cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            room_obj = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Failed to get room: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        serializer = RoomFlashBulkInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        flash_data = serializer.validated_data.get("flashes", [])
        incoming_flash_ids = [
            f.get("existing_id")
            for f in flash_data
            if f.get("existing_id")
        ]
        
        try:
            with transaction.atomic():
                # Delete existing flashes which are not included in new request
                RoomFlash.objects.filter(room=room_obj).exclude(id__in=incoming_flash_ids).delete()
                
                for flash in flash_data:
                    flash_id = flash.pop("existing_id")
                    product = flash.get("product")
                    value = flash.get("value")

                    if flash_id:  # update existing
                        obj = get_object_or_404(RoomFlash, id=flash_id, room=room_obj)
                        obj.product = product
                        obj.value = value
                        obj.save()
                    else:
                        # Create new flash
                        RoomFlash.objects.create(
                            room=room_obj,
                            product=product,
                            value=value
                        )

        except Exception as e:
            return Response(
                {
                    "error": f"Failed to update room flashes.",
                    "details": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        updated_room_flashes = room_obj.room_flashes.all()
        serializer = RoomFlashOutputSerializer(updated_room_flashes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)