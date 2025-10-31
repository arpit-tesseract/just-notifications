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
from configuration.serializers import *
from .models import *
import pandas as pd

# CRUD Views
# ========================================
# Residential 
# ========================================
class GlobViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Glob.objects.all() # First time load data when server starts
    model = Glob 
    serializer_class = GlobSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)

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
    queryset = Continent.objects.all() 
    serializer_class = ContinentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'glob': 'glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ContinentSerializer   # For POST, PUT, PATCH
        return ContinentDetailSerializer
    

class CountryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Country
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'continent': 'continent__id',
        'glob': 'continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CountrySerializer   # For POST, PUT, PATCH
        return CountryDetailSerializer
    

class StateViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = State
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'country': 'country__id',
        'continent': 'country__continent__id',
        'glob': 'country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return StateSerializer   # For POST, PUT, PATCH
        print(True)
        return StateDetailSerializer
   
   
class DistrictViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = District
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'state': 'state__id',
        'country': 'state__country__id',
        'continent': 'state__country__continent__id',
        'glob': 'state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DistrictSerializer   # For POST, PUT, PATCH
        return DistrictDetailSerializer


class TalukaViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Taluka
    queryset = Taluka.objects.all()
    serializer_class = TalukaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'district': 'district__id',
        'state': 'district__state__id',
        'country': 'district__state__country__id',
        'continent': 'district__state__country__continent__id',
        'glob': 'district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TalukaSerializer   # For POST, PUT, PATCH
        return TalukaDetailSerializer
    

class CityVillageViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = CityVillage
    queryset = CityVillage.objects.all()
    serializer_class = CityVillageSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'taluka': 'taluka__id',
        'district': 'taluka__district__id',
        'state': 'taluka__district__state__id',
        'country': 'taluka__district__state__country__id',
        'continent': 'taluka__district__state__country__continent__id',
        'glob': 'taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CityVillageSerializer   # For POST, PUT, PATCH
        return CityVillageDetailSerializer
    

class WardViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Ward
    queryset = Ward.objects.all()
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'city_village': 'city_village__id',
        'taluka': 'city_village__taluka__id',
        'district': 'city_village__taluka__district__id',
        'state': 'city_village__taluka__district__state__id',
        'country': 'city_village__taluka__district__state__country__id',
        'continent': 'city_village__taluka__district__state__country__continent__id',
        'glob': 'city_village__taluka__district__state__country__continent__glob__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return WardSerializer   # For POST, PUT, PATCH
        return WardDetailSerializer
    


# ========================================
# Personal 
# ========================================
class ReligionViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Religion
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)
        
    
class SampradayViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Sampraday
    queryset = Sampraday.objects.all()
    serializer_class = SampradaySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission] 
    FILTER_FIELDS = {
        'religion': 'religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SampradaySerializer   # For POST, PUT, PATCH
        return SampradayDetailSerializer 


class PanthViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Panth
    queryset = Panth.objects.all()
    serializer_class = PanthSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'sampraday': 'sampraday__id',
        'religion': 'sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PanthSerializer   # For POST, PUT, PATCH
        return PanthDetailSerializer
    

class VarnaViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Varna
    queryset = Varna.objects.all()
    serializer_class = VarnaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'panth': 'panth__id',
        'sampraday': 'panth__sampraday__id',
        'religion': 'panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    def get_base_queryset(self):
        return get_regular_query(self.model)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VarnaSerializer   # For POST, PUT, PATCH
        return VarnaDetailSerializer
    

class CasteViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Caste
    queryset = Caste.objects.all()
    serializer_class = CasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'varna': 'varna__id',
        'panth': 'varna__panth__id',
        'sampraday': 'varna__panth__sampraday__id',
        'religion': 'varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CasteSerializer   # For POST, PUT, PATCH
        return CasteDetailSerializer
    
    
class SubCasteViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubCaste
    queryset = SubCaste.objects.all()
    serializer_class = SubCasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]    
    FILTER_FIELDS = {
        'caste': 'caste__id',
        'varna': 'caste__varna__id',
        'panth': 'caste__varna__panth__id',
        'sampraday': 'caste__varna__panth__sampraday__id',
        'religion': 'caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubCasteSerializer   # For POST, PUT, PATCH
        return SubCasteDetailSerializer


class GotraViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Gotra
    queryset = Gotra.objects.all()
    serializer_class = GotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'subcaste': 'subcaste__id',
        'caste': 'subcaste__caste__id',
        'varna': 'subcaste__caste__varna__id',
        'panth': 'subcaste__caste__varna__panth__id',
        'sampraday': 'subcaste__caste__varna__panth__sampraday__id',
        'religion': 'subcaste__caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GotraSerializer   # For POST, PUT, PATCH
        return GotraDetailSerializer
    

class SubGotraViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubGotra
    queryset = SubGotra.objects.all()
    serializer_class = SubGotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]  
    FILTER_FIELDS = {
        'gotra': 'gotra__id',
        'subcaste': 'gotra__subcaste__id',
        'caste': 'gotra__subcaste__caste__id',
        'varna': 'gotra__subcaste__caste__varna__id',
        'panth': 'gotra__subcaste__caste__varna__panth__id',
        'sampraday': 'gotra__subcaste__caste__varna__panth__sampraday__id',
        'religion': 'gotra__subcaste__caste__varna__panth__sampraday__religion__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    } 
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubGotraSerializer   # For POST, PUT, PATCH
        return SubGotraDetailSerializer 


class KulViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Kul
    queryset = Kul.objects.all()
    serializer_class = KulSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
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
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return KulSerializer   # For POST, PUT, PATCH
        return KulDetailSerializer


class VanshViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Vansh
    queryset = Vansh.objects.all()
    serializer_class = VanshSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
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
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VanshSerializer   # For POST, PUT, PATCH
        return VanshDetailSerializer


class FamilyViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Family
    queryset = Family.objects.all()
    serializer_class = FamilySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
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
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return FamilySerializer   # For POST, PUT, PATCH
        return FamilyDetailSerializer


class PidhiViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Pidhi
    queryset = Pidhi.objects.all()
    serializer_class = PidhiSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'family': 'family__id',
        'vansh': 'family__vansh__id',
        'kul': 'family__vansh__kul__id',
        'subgotra': 'family__vansh__kul__subgotra__id',
        'gotra': 'family__vansh__kul__subgotra__gotra__id',
        'subcaste': 'family__vansh__kul__subgotra__gotra__subcaste__id',
        'caste': 'family__vansh__kul__subgotra__gotra__subcaste__caste__id',
        'varna': 'family__vansh__kul__subgotra__gotra__subcaste__caste__varna__id',
        'panth': 'family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__id',
        'sampraday': 'family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PidhiSerializer   # For POST, PUT, PATCH
        return PidhiDetailSerializer
    
    
# ========================================
# Professional 
# ========================================
class SectionViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Section
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    } 
    # def get_base_queryset(self):
    #     return get_regular_query(self.model)   
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SectionSerializer   # For POST, PUT, PATCH
        return SectionSerializer


class ClassViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Class
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'section': 'section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ClassSerializer   # For POST, PUT, PATCH
        return ClassDetailSerializer


class ProfCategoryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = ProfCategory
    queryset = ProfCategory.objects.all()
    serializer_class = ProfCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'profclass': 'profclass__id',
        'section': 'profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProfCategorySerializer   # For POST, PUT, PATCH
        return ProfCategoryDetailSerializer
    

class ProfSubCategoryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = ProfSubCategory
    queryset = ProfSubCategory.objects.all()
    serializer_class = ProfSubCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'category': 'category__id',
        'profclass': 'category__profclass__id',
        'section': 'category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold' 
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProfSubCategorySerializer   # For POST, PUT, PATCH
        return ProfSubCategoryDetailSerializer


class SectorViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Sector
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'subcategory': 'subcategory__id',
        'category': 'subcategory__category__id',
        'profclass': 'subcategory__category__profclass__id',
        'section': 'subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SectorSerializer   # For POST, PUT, PATCH
        return SectorDetailSerializer
    

class SubSectorViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubSector
    queryset = SubSector.objects.all()
    serializer_class = SubSectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'sector': 'sector__id',
        'subcategory': 'sector__subcategory__id',
        'category': 'sector__subcategory__category__id',
        'profclass': 'sector__subcategory__category__profclass__id',
        'section': 'sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubSectorSerializer   # For POST, PUT, PATCH
        return SubSectorDetailSerializer


class DepartmentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Department
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'subsector': 'subsector__id',
        'sector': 'subsector__sector__id',
        'subcategory': 'subsector__sector__subcategory__id',
        'category': 'subsector__sector__subcategory__category__id',
        'profclass': 'subsector__sector__subcategory__category__profclass__id',
        'section': 'subsector__sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DepartmentSerializer   # For POST, PUT, PATCH
        return DepartmentDetailSerializer
    

class SubDepartmentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubDepartment
    queryset = SubDepartment.objects.all()
    serializer_class = SubDepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    FILTER_FIELDS = {
        'department': 'department__id',
        'subsector': 'department__subsector__id',
        'sector': 'department__subsector__sector__id',
        'subcategory': 'department__subsector__sector__subcategory__id',
        'category': 'department__subsector__sector__subcategory__category__id',
        'profclass': 'department__subsector__sector__subcategory__category__profclass__id',
        'section': 'department__subsector__sector__subcategory__category__profclass__section__id',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubDepartmentSerializer   # For POST, PUT, PATCH
        return SubDepartmentDetailSerializer
    
    
class TypeViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Type
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
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
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TypeSerializer   # For POST, PUT, PATCH
        return TypeDetailSerializer
    

class BrandViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Brand
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
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
        'on_hold': 'on_hold'
    }
    # def get_base_queryset(self):
    #     return get_regular_query(self.model) 
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return BrandSerializer   # For POST, PUT, PATCH
        return BrandDetailSerializer


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
#         'on_hold': 'on_hold'
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
    

# ==================
# Import Features
# ==================


def clean(value):
    return str(value).strip() if pd.notnull(value) else None


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
                code = clean(row.get("code") or "")
                
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
            return Response({"error": "No valid rows found in the file."}, status=400)

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
                glob = clean(row.get("glob"))
                continent = clean(row.get("continent"))
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([glob, continent, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    glob = Glob.objects.get(name=glob)
                except Glob.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Glob '{glob}' not found"})
                    continue
                
                objs.append(Continent(
                    glob = glob, 
                    name = continent, 
                    code = code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({"error": "No valid rows found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                Continent.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                glob = clean(row.get("glob"))
                continent = clean(row.get("continent"))
                country = clean(row.get("country"))
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([glob, continent, country, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    continent = Continent.objects.get(
                        name=continent, 
                        glob__name=glob
                    )
                except Continent.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Continent '{continent}' not found for glob: {glob}"})
                    continue
                
                objs.append(Country(
                    continent=continent,
                    name=country, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
                
        if not objs:
            return Response({"error": "No valid rows found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                Country.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                glob = clean(row.get("glob"))
                continent = clean(row.get("continent"))
                country = clean(row.get("country"))
                state = clean(row.get("state"))
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                try:
                    country = Country.objects.get(
                        name=country, 
                        continent__name=continent, 
                        continent__glob__name=glob
                    )
                    
                except Country.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Country '{country}' not found for continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(State(
                    country=country,
                    name=state, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})       
        
        if not objs:
            return Response({"error": "No valid rows found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                State.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                glob = clean(row.get("glob"))
                continent = clean(row.get("continent"))
                country = clean(row.get("country"))
                state = clean(row.get("state"))
                district = clean(row.get("district"))
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                try:
                    state = State.objects.get(
                        name=state, 
                        country__name=country, 
                        country__continent__name=continent, 
                        country__continent__glob__name=glob
                    )
                except State.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"State '{state}' not found for country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                    
                objs.append(District(
                    state=state,
                    name=district, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
                    
        if not objs:
            return Response({"error": "No valid rows found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                District.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                glob = clean(row.get("glob"))
                continent = clean(row.get("continent"))
                country = clean(row.get("country"))
                state = clean(row.get("state"))
                district = clean(row.get("district"))
                taluka = clean(row.get("taluka"))
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    district = District.objects.get(
                        name=district, 
                        state__name=state, 
                        state__country__name=country, 
                        state__country__continent__name=continent, 
                        state__country__continent__glob__name=glob
                    )
                    
                except District.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"District '{district}' not found for state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(Taluka(
                    district=district,
                    name=taluka, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                    
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({"error": "No valid rows found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                Taluka.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                glob = clean(row.get("glob"))
                continent = clean(row.get("continent"))
                country = clean(row.get("country"))
                state = clean(row.get("state"))
                district = clean(row.get("district"))
                taluka = clean(row.get("taluka"))
                city_village = clean(row.get("city_village"))    
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    taluka = Taluka.objects.get(
                        name=taluka, 
                        district__name=district, 
                        district__state__name=state, 
                        district__state__country__name=country, 
                        district__state__country__continent__name=continent, 
                        district__state__country__continent__glob__name=glob
                    )
                    
                except Taluka.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Taluka '{taluka}' not found for district: {district}, state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(CityVillage(
                    taluka=taluka,
                    name=city_village, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date)
                )
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({"error": "No valid rows found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                CityVillage.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                glob = clean(row.get("glob"))
                continent = clean(row.get("continent"))
                country = clean(row.get("country"))
                state = clean(row.get("state"))
                district = clean(row.get("district"))
                taluka = clean(row.get("taluka"))
                city_village = clean(row.get("city_village"))
                ward = clean(row.get("ward"))
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([glob, continent, country, state, district, taluka, city_village, ward, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    city_village = CityVillage.objects.get(
                        name=city_village, 
                        taluka__name=taluka, 
                        taluka__district__name=district, 
                        taluka__district__state__name=state, 
                        taluka__district__state__country__name=country, 
                        taluka__district__state__country__continent__name=continent, 
                        taluka__district__state__country__continent__glob__name=glob
                    )
                except CityVillage.DoesNotExist:    
                    invalid_rows.append({"row": idx + 2, "error": f"City/Village '{city_village}' not found for taluka: {taluka}, district: {district}, state: {state}, country: {country}, continent: {continent}, glob: {glob}"})
                    continue
                
                objs.append(Ward(
                    city_village=city_village,
                    name=ward, 
                    code=code, 
                    is_hidden = is_hidden, 
                    on_hold = on_hold, 
                    hold_date = hold_date
                ))
                     
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})

        if not objs:
            return Response({"error": "No valid rows found in the file."}, status=400)

        try:
            with transaction.atomic():
                Ward.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=400)
        
        return Response(
            {
                "message": f"{len(objs)} Wards uploaded successfully",
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
                code = clean(row.get("code"))
                
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([religion, sampraday, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                try:
                    religion_obj = Religion.objects.get(name=religion)
                except Religion.DoesNotExist:
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                Sampraday.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                try:
                    sampraday_obj = Sampraday.objects.get(name=sampraday, religion__name=religion)
                except Sampraday.DoesNotExist:
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                Panth.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Panth uploaded successfully",
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([religion, sampraday, panth, varna, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                try:
                    panth_obj = Panth.objects.get(
                        name=panth, 
                        sampraday__name=sampraday, 
                        sampraday__religion__name=religion
                    )
                except Panth.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Panth '{panth}' not found for sampraday: {sampraday} and religion: {religion}"}) 
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                Varna.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, varna, caste, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                try:
                    varna_obj = Varna.objects.get(
                        name=varna, 
                        panth__name=panth, 
                        panth__sampraday__name=sampraday, 
                        panth__sampraday__religion__name=religion
                    )
                except Varna.DoesNotExist:
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                Caste.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, varna, caste, subcaste, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                try:
                    caste_obj = Caste.objects.get(
                        name=caste, 
                        varna__name=varna, 
                        varna__panth__name=panth, 
                        varna__panth__sampraday__name=sampraday, 
                        varna__panth__sampraday__religion__name=religion
                    )
                except Caste.DoesNotExist:
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                SubCaste.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                 
                    
                try:
                    subcaste_obj = SubCaste.objects.get(
                        name=subcaste, 
                        caste__name=caste, 
                        caste__varna__name=varna, 
                        caste__varna__panth__name=panth, 
                        caste__varna__panth__sampraday__name=sampraday, 
                        caste__varna__panth__sampraday__religion__name=religion
                    )
                except SubCaste.DoesNotExist:
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                Gotra.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([sampraday, religion, panth, varna, caste, subcaste, gotra, subgotra, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields"})
                    continue
                    
                try:
                    gotra_obj = Gotra.objects.get(
                        name=gotra, 
                        subcaste__caste__name=caste, 
                        subcaste__caste__varna__name=varna, 
                        subcaste__caste__varna__panth__name=panth, 
                        subcaste__caste__varna__panth__sampraday__name=sampraday, 
                        subcaste__caste__varna__panth__sampraday__religion__name=religion
                    )
                except Gotra.DoesNotExist:
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                SubGotra.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, subgotra, kul, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                try:
                    subgotra_obj = SubGotra.objects.get(
                        name=subgotra, 
                        gotra__name=gotra, 
                        gotra__subcaste__caste__name=caste, 
                        gotra__subcaste__caste__varna__name=varna, 
                        gotra__subcaste__caste__varna__panth__name=panth, 
                        gotra__subcaste__caste__varna__panth__sampraday__name=sampraday, 
                        gotra__subcaste__caste__varna__panth__sampraday__religion__name=religion
                    )
                except SubGotra.DoesNotExist:
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Kul.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, subgotra, kul, vansh, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    kul_obj = Kul.objects.get(
                        name = kul,
                        subgotra__name = subgotra,
                        subgotra__gotra__name = gotra,
                        subgotra__gotra__subcaste__caste__name = caste,
                        subgotra__gotra__subcaste__caste__varna__name = varna,
                        subgotra__gotra__subcaste__caste__varna__panth__name = panth,
                        subgotra__gotra__subcaste__caste__varna__panth__sampraday__name = sampraday,
                        subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name = religion
                    )
                except Kul.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Kul '{kul} not found for subgotra: {subgotra}, gotra: {gotra}, caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"})
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
            return Response({"error": "No valid rows found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Vansh.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))    
                
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, subgotra, kul, vansh, family, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    vansh_obj = Vansh.objects.get(
                        name = vansh,
                        kul__name = kul,
                        kul__subgotra__name = subgotra,
                        kul__subgotra__gotra__name = gotra,
                        kul__subgotra__gotra__subcaste__name = subcaste,
                        kul__subgotra__gotra__subcaste__caste__name = caste,
                        kul__subgotra__gotra__subcaste__caste__varna__name = varna,
                        kul__subgotra__gotra__subcaste__caste__varna__panth__name = panth,
                        kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name = sampraday,
                        kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name = religion
                    )
                except Vansh.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Vansh '{vansh}' not found for kul: {kul}, subgotra: {subgotra}, gotra: {gotra}, caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"})
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
            return Response({"error": "No valid data found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Family.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Families uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )


class UploadPidhiView(APIView):
    model = Pidhi
    permission_classes = [IsAuthenticated]
    serializer_class = FileUploadSerializer
    
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            df = read_file(file, required_columns=["religion","sampraday", "panth", "varna", "caste", "subcaste", "gotra", "subgotra", "kul", "vansh", "family", "pidhi", "code", "is_hidden", "on_hold", "hold_date"])
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
                pidhi = clean(row.get("pidhi"))
                code = clean(row.get("code"))
                
                if not all([religion, sampraday, panth, varna, caste, subcaste, gotra, subgotra, kul, vansh, family, pidhi, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    family_obj = Family.objects.get(
                        name = family,
                        vansh__name = vansh,
                        vansh__kul__name = kul,
                        vansh__kul__subgotra__name = subgotra,
                        vansh__kul__subgotra__gotra__name = gotra,
                        vansh__kul__subgotra__gotra__subcaste__name = subcaste,
                        vansh__kul__subgotra__gotra__subcaste__caste__name = caste,
                        vansh__kul__subgotra__gotra__subcaste__caste__varna__name = varna,
                        vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__name = panth,
                        vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name = sampraday,
                        vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name = religion
                    )
                except Exception as e:
                    invalid_rows.append({"row": idx + 2, "error": f"Family '{family}' not found for vansh: {vansh}, kul: {kul}, subgotra: {subgotra}, gotra: {gotra}, subcaste: {subcaste}, caste: {caste}, varna: {varna}, panth: {panth}, sampraday: {sampraday}, religion: {religion}"})
                    continue
                
                objs.append(Pidhi(
                    family = family_obj,
                    name = pidhi,
                    code = code,
                    is_hidden = is_hidden,
                    on_hold = on_hold,
                    hold_date = hold_date
                ))
                
            except Exception as e:
                invalid_rows.append({"row": idx + 2, "error": str(e)})
        
        if not objs:
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Pidhi.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Pidhis uploaded successfully.",
                "invalid_rows": invalid_rows
            }, status=status.HTTP_201_CREATED
        )
 
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
                code = clean(row.get("code"))
                
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
            return Response({"error": "No valid records found in the file."}, status=400)
        
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    section_obj = Section.objects.get(name=section)
                except Section.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                Class.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    class_obj = Class.objects.get(name=class_name, section__name=section)
                except Class.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=400)
        
        try:
            with transaction.atomic():
                ProfCategory.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    category_obj = ProfCategory.objects.get(name=category, profclass__name=class_name, profclass__section__name=section)
                except ProfCategory.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                ProfSubCategory.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    subcategory_obj = ProfSubCategory.objects.get(name=subcategory, category__name=category, category__profclass__name=class_name, category__profclass__section__name=section)
                except ProfSubCategory.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Sector.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    sector_obj = Sector.objects.get(name=sector, subcategory__name=subcategory, subcategory__category__name=category, subcategory__category__profclass__name=class_name, subcategory__category__profclass__section__name=section)
                except Sector.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                SubSector.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                try:
                    subsector_obj = SubSector.objects.get(
                        name=subsector,
                        sector__name=sector,
                        sector__subcategory__name=subcategory,
                        sector__subcategory__category__name=category,
                        sector__subcategory__category__profclass__name=class_name,
                        sector__subcategory__category__profclass__section__name=section 
                    )
                except SubSector.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Department.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, subdepartment, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                    
                try:
                    department_obj = Department.objects.get(
                        name=department,
                        subsector__name=subsector,
                        subsector__sector__name=sector,
                        subsector__sector__subcategory__name=subcategory,
                        subsector__sector__subcategory__category__name=category,
                        subsector__sector__subcategory__category__profclass__name=class_name,
                        subsector__sector__subcategory__category__profclass__section__name=section 
                        )
                except Department.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                SubDepartment.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, subdepartment, type_name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    subdepartment_obj = SubDepartment.objects.get(
                        name = subdepartment,
                        department__name = department,
                        department__subsector__name = subsector,
                        department__subsector__sector__name = sector,
                        department__subsector__sector__subcategory__name = subcategory,
                        department__subsector__sector__subcategory__category__name = category,
                        department__subsector__sector__subcategory__category__profclass__name = class_name,
                        department__subsector__sector__subcategory__category__profclass__section__name = section 
                        )
                except SubDepartment.DoesNotExist:
                    invalid_rows.append({"row": idx + 2, "error": f"Sub Department: '{subdepartment}' not found for sector: {sector}, subcategory: {subcategory}, category: {category}, class: {class_name}, section: {section}"})
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
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Type.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
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
                code = clean(row.get("code"))
                
                # Skip invalid rows early
                if not all([section, class_name, category, subcategory, sector, subsector, department, subdepartment, type_name, brand_name, code]):
                    invalid_rows.append({"row": idx + 2, "error": "Missing required fields."})
                    continue
                
                try:
                    type_obj = Type.objects.get(
                        name = type_name,
                        subdepartment__name = subdepartment,
                        subdepartment__department__name = department,
                        subdepartment__department__subsector__name = subsector,
                        subdepartment__department__subsector__sector__name = sector,
                        subdepartment__department__subsector__sector__subcategory__name = subcategory,
                        subdepartment__department__subsector__sector__subcategory__category__name = category,
                        subdepartment__department__subsector__sector__subcategory__category__profclass__name = class_name,
                        subdepartment__department__subsector__sector__subcategory__category__profclass__section__name = section 
                        )
                except Type.DoesNotExist:
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
            return Response({"error": "No valid records found in the file."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                Brand.objects.bulk_create(
                    objs,
                    update_conflicts=True,
                    unique_fields=["code"],
                    update_fields=["name", "is_hidden", "on_hold", "hold_date"],
                )
        except Exception as e:
            return Response({"error": f"Failed to create records: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(
            {
                "message": f"{len(objs)} Brand uploaded successfully.",
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
#                 code = clean(row.get("code"))
                
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
        

class ResidentialSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
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
        
        

        if search_key == "glob":
            qs = get_regular_query(Glob)
            if glob_name:
                qs = qs.filter(name__icontains=glob_name)
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
                    "ward": None
                }
                for obj in qs
            ]

        elif search_key == "continent":
            qs = get_regular_query(Continent)
            if continent_name:
                qs = qs.filter(name__icontains=continent_name)
            if glob_name:
                qs = qs.filter(glob__name__icontains=glob_name)
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
                    "ward": None
                }
                for obj in qs
            ]

        elif search_key == "country":
            qs = get_regular_query(Country)
            if country_name:
                qs = qs.filter(name__icontains=country_name)
            if continent_name:
                qs = qs.filter(continent__name__icontains=continent_name)
            if glob_name:
                qs = qs.filter(continent__glob__name__icontains=glob_name)
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
                    "ward": None
                }
                for obj in qs
            ]

        elif search_key == "state":
            qs = get_regular_query(State)
            if state_name:
                qs = qs.filter(name__icontains=state_name)
            if country_name:
                qs = qs.filter(country__name__icontains=country_name)
            if continent_name:
                qs = qs.filter(country__continent__name__icontains=continent_name)
            if glob_name:
                qs = qs.filter(country__continent__glob__name__icontains=glob_name)
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
                    "ward": None
                }
                for obj in qs
            ]

        elif search_key == "district":
            qs = get_regular_query(District)
            if district_name:
                qs = qs.filter(name__icontains=district_name)
            if state_name:
                qs = qs.filter(state__name__icontains=state_name)
            if country_name:
                qs = qs.filter(state__country__name__icontains=country_name)
            if continent_name:
                qs = qs.filter(state__country__continent__name__icontains=continent_name)
            if glob_name:
                qs = qs.filter(state__country__continent__glob__name__icontains=glob_name)
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
                    "ward": None
                }
                for obj in qs
            ]

        elif search_key == "taluka":
            qs = get_regular_query(Taluka)
            if taluka_name:
                qs = qs.filter(name__icontains=taluka_name)
            if district_name:
                qs = qs.filter(district__name__icontains=district_name)
            if state_name:
                qs = qs.filter(district__state__name__icontains=state_name)
            if country_name:
                qs = qs.filter(district__state__country__name__icontains=country_name)
            if continent_name:
                qs = qs.filter(district__state__country__continent__name__icontains=continent_name)
            if glob_name:
                qs = qs.filter(district__state__country__continent__glob__name__icontains=glob_name)
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
                    "ward": None
                }
                for obj in qs
            ]

        elif search_key == "city_village":
            qs = get_regular_query(CityVillage)
            if city_village_name:
                qs = qs.filter(name__icontains=city_village_name)
            if taluka_name:
                qs = qs.filter(taluka__name__icontains=taluka_name)
            if district_name:
                qs = qs.filter(taluka__district__name__icontains=district_name)
            if state_name:
                qs = qs.filter(taluka__district__state__name__icontains=state_name)
            if country_name:
                qs = qs.filter(taluka__district__state__country__name__icontains=country_name)
            if continent_name:
                qs = qs.filter(taluka__district__state__country__continent__name__icontains=continent_name)
            if glob_name:
                qs = qs.filter(taluka__district__state__country__continent__glob__name__icontains=glob_name)
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
                    "ward": None
                }
                for obj in qs
            ]
        
        elif search_key == "ward":
            qs = get_regular_query(Ward)
            if ward_name:
                qs = qs.filter(name__icontains=ward_name)
            if city_village_name:
                qs = qs.filter(city_village__name__icontains=city_village_name)
            if taluka_name:
                qs = qs.filter(city_village__taluka__name__icontains=taluka_name)
            if district_name:
                qs = qs.filter(city_village__taluka__district__name__icontains=district_name)
            if state_name:
                qs = qs.filter(city_village__taluka__district__state__name__icontains=state_name)
            if country_name:
                qs = qs.filter(city_village__taluka__district__state__country__name__icontains=country_name)
            if continent_name:
                qs = qs.filter(city_village__taluka__district__state__country__continent__name__icontains=continent_name)
            if glob_name:
                qs = qs.filter(city_village__taluka__district__state__country__continent__glob__name__icontains=glob_name)
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
                    "ward": WardIdNameSerializer(obj).data
                }
                for obj in qs
            ]

        else:
            # fallback → default globs
            qs = get_regular_query(Glob)
            results = [
                {
                    "glob": GlobIdNameSerializer(obj).data,
                    "continent": None,
                    "country": None,
                    "state": None,
                    "district": None,
                    "taluka": None,
                    "city_village": None,
                    "ward": None
                }
                for obj in qs
            ]

        # Return unified response structure
        output = ResidentialOutputSerializer(results, many=True)
        return Response(output.data) 
       
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
        varna_name = data.get('varna')
        caste_name = data.get('caste')
        subcaste_name = data.get('subcaste')
        gotra_name = data.get('gotra')
        subgotra_name = data.get('subgotra')
        kul_name = data.get('kul')
        vansh_name = data.get('vansh')
        family_name = data.get('family')
        pidhi_name = data.get('pidhi')
        
        
        
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
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None,
                }
                for obj in qs
            ]

        elif search_key == "sampraday":
            qs = get_regular_query(Sampraday)
            if sampraday_name:
                qs = qs.filter(name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj).data,
                    "panth": None,
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None,
                }
                for obj in qs
            ]
        
        elif search_key == "panth":
            qs = get_regular_query(Panth)
            if panth_name:
                qs = qs.filter(name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.sampraday).data,
                    "panth": PanthIdNameSerializer(obj).data,
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None,
                }
                for obj in qs
            ]
        
        elif search_key == "varna":
            qs = get_regular_query(Varna)
            if varna_name:
                qs = qs.filter(name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.panth).data,
                    "varna": VarnaIdNameSerializer(obj).data,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None,
                }
                for obj in qs
            ]
        
        
        elif search_key == "caste":
            qs = get_regular_query(Caste)
            if caste_name:
                qs = qs.filter(name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(varna__panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.varna).data,
                    "caste": CasteIdNameSerializer(obj).data,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None
                }
                for obj in qs
            ] 
        
        
        elif search_key == "subcaste":
            qs = get_regular_query(SubCaste)
            if subcaste_name:
                qs = qs.filter(name__icontains=subcaste_name)
            if caste_name:
                qs = qs.filter(caste__name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(caste__varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(caste__varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(caste__varna__panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(caste__varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.caste.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj).data,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None
                }
                for obj in qs
            ] 
        
        
        elif search_key == "gotra":
            qs = get_regular_query(Gotra)
            if gotra_name:
                qs = qs.filter(name__icontains=gotra_name)
            if subcaste_name:
                qs = qs.filter(subcaste__name__icontains=subcaste_name)
            if caste_name:
                qs = qs.filter(subcaste__caste__name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(subcaste__caste__varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(subcaste__caste__varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(subcaste__caste__varna__panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(subcaste__caste__varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.subcaste.caste.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj).data,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None
                }
                for obj in qs
            ]  
        
        
        elif search_key == "subgotra":
            qs = get_regular_query(SubGotra)
            if subgotra_name:
                qs = qs.filter(name__icontains=subgotra_name)
            if gotra_name:
                qs = qs.filter(gotra__name__icontains=gotra_name)
            if subcaste_name:
                qs = qs.filter(gotra__subcaste__name__icontains=subcaste_name)
            if caste_name:
                qs = qs.filter(gotra__subcaste__caste__name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(gotra__subcaste__caste__varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(gotra__subcaste__caste__varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(gotra__subcaste__caste__varna__panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.gotra.subcaste.caste.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj).data,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None
                }
                for obj in qs
            ]
        
        elif search_key == "kul":
            qs = get_regular_query(Kul)
            if kul_name:
                qs = qs.filter(name__icontains=kul_name)
            if subgotra_name:
                qs = qs.filter(subgotra__name__icontains=subgotra_name) 
            if gotra_name:
                qs = qs.filter(subgotra__gotra__name__icontains=gotra_name)
            if subcaste_name:
                qs = qs.filter(subgotra__gotra__subcaste__name__icontains=subcaste_name)
            if caste_name:
                qs = qs.filter(subgotra__gotra__subcaste__caste__name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(subgotra__gotra__subcaste__caste__varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(subgotra__gotra__subcaste__caste__varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains=sampraday_name)       
            if religion_name:
                qs = qs.filter(subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.subgotra.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.subgotra.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.subgotra.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.subgotra.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj.subgotra).data,
                    "kul": KulIdNameSerializer(obj).data,
                    "vansh": None,
                    "family": None,
                    "pidhi": None
                }
                for obj in qs
            ]
        
        elif search_key == "vansh":
            qs = get_regular_query(Vansh)
            if vansh_name:
                qs = qs.filter(name__icontains=vansh_name)
            if kul_name:
                qs = qs.filter(kul__name__icontains=kul_name)
            if subgotra_name:  
                qs = qs.filter(kul__subgotra__name__icontains=subgotra_name)                  
            if gotra_name:  
                qs = qs.filter(kul__subgotra__gotra__name__icontains=gotra_name)
            if subcaste_name:
                qs = qs.filter(kul__subgotra__gotra__subcaste__name__icontains=subcaste_name)
            if caste_name:
                qs = qs.filter(kul__subgotra__gotra__subcaste__caste__name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(kul__subgotra__gotra__subcaste__caste__varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(kul__subgotra__gotra__subcaste__caste__varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.kul.subgotra.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.kul.subgotra.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.kul.subgotra.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj.kul.subgotra).data,
                    "kul": KulIdNameSerializer(obj.kul).data,
                    "vansh": VanshIdNameSerializer(obj).data,
                    "family": None,
                    "pidhi": None
                }
                for obj in qs
            ]  
            
        elif search_key == "family":
            qs = get_regular_query(Family)
            if family_name:
                qs = qs.filter(name__icontains=family_name)
            if vansh_name:    
                qs = qs.filter(vansh__name__icontains=vansh_name)
            if kul_name:
                qs = qs.filter(vansh__kul__name__icontains=kul_name)
            if subgotra_name:  
                qs = qs.filter(vansh__kul__subgotra__name__icontains=subgotra_name)                  
            if gotra_name:  
                qs = qs.filter(vansh__kul__subgotra__gotra__name__icontains=gotra_name)
            if subcaste_name:
                qs = qs.filter(vansh__kul__subgotra__gotra__subcaste__name__icontains=subcaste_name)
            if caste_name:
                qs = qs.filter(vansh__kul__subgotra__gotra__subcaste__caste__name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(vansh__kul__subgotra__gotra__subcaste__caste__varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.vansh.kul.subgotra.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.vansh.kul.subgotra.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj.vansh.kul.subgotra).data,
                    "kul": KulIdNameSerializer(obj.vansh.kul).data,
                    "vansh": VanshIdNameSerializer(obj.vansh).data,
                    "family": FamilyIdNameSerializer(obj).data,
                    "pidhi": None
                }                
                for obj in qs
            ]

        
        elif search_key == "pidhi":
            qs = get_regular_query(Pidhi)
            if pidhi_name:
                qs = qs.filter(name__icontains=pidhi_name)
            if family_name:
                qs = qs.filter(family__name__icontains=family_name)    
            if vansh_name:    
                qs = qs.filter(family__vansh__name__icontains=vansh_name)
            if kul_name:
                qs = qs.filter(family__vansh__kul__name__icontains=kul_name)
            if subgotra_name:  
                qs = qs.filter(family__vansh__kul__subgotra__name__icontains=subgotra_name)                  
            if gotra_name:  
                qs = qs.filter(family__vansh__kul__subgotra__gotra__name__icontains=gotra_name)
            if subcaste_name:
                qs = qs.filter(family__vansh__kul__subgotra__gotra__subcaste__name__icontains=subcaste_name)
            if caste_name:
                qs = qs.filter(family__vansh__kul__subgotra__gotra__subcaste__caste__name__icontains=caste_name)
            if varna_name:
                qs = qs.filter(family__vansh__kul__subgotra__gotra__subcaste__caste__varna__name__icontains=varna_name)
            if panth_name:
                qs = qs.filter(family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__name__icontains=panth_name)
            if sampraday_name:
                qs = qs.filter(family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__name__icontains=sampraday_name)
            if religion_name:
                qs = qs.filter(family__vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__name__icontains=religion_name)
            qs = qs[:10]
            
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday.religion).data,
                    "sampraday": SampradayIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth.sampraday).data,
                    "panth": PanthIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna.panth).data,
                    "varna": VarnaIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste.varna).data,
                    "caste": CasteIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste.caste).data,
                    "subcaste": SubCasteIdNameSerializer(obj.family.vansh.kul.subgotra.gotra.subcaste).data,
                    "gotra": GotraIdNameSerializer(obj.family.vansh.kul.subgotra.gotra).data,
                    "subgotra": SubGotraIdNameSerializer(obj.family.vansh.kul.subgotra).data,
                    "kul": KulIdNameSerializer(obj.family.vansh.kul).data,
                    "vansh": VanshIdNameSerializer(obj.family.vansh).data,
                    "family": FamilyIdNameSerializer(obj.family).data,
                    "pidhi": PidhiIdNameSerializer(obj).data
                }                
                for obj in qs
            ]
        
        else:
            # fallback - default religions
            qs = get_regular_query(Religion)
            results = [
                {
                    "religion": ReligionIdNameSerializer(obj).data,
                    "sampraday": None,
                    "panth": None,
                    "varna": None,
                    "caste": None,
                    "subcaste": None,
                    "gotra": None,
                    "subgotra": None,
                    "kul": None,
                    "vansh": None,
                    "family": None,
                    "pidhi": None
                }                
                for obj in qs
            ]
        
        # return unified response structure
        output = PersonalOutputSerializer(results, many=True)
        return Response(output.data, status=200)


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
            qs = get_regular_query(Class)
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
            qs = get_regular_query(ProfCategory)
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
            qs = get_regular_query(ProfSubCategory)
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
            qs = get_regular_query(Sector)
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
            qs = get_regular_query(SubSector)
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
            qs = get_regular_query(Department)
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
            qs = get_regular_query(SubDepartment)
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
            qs = get_regular_query(Type)
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
            qs = get_regular_query(Brand)
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
        return Response(output.data, status=status.HTTP_200_OK)
            
                    
# class DesignationView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]
#     FILTER_FIELDS = {
#         'relation_category': 'relation_category'
#     }
    
#     def get_base_queryset(self):
#         today = timezone.now().date()
        
#         return Designation.objects.filter(
#             is_hidden=False,
#             on_hold=False
#         ).filter(
#             Q(hold_date__lte=today) | Q(hold_date__isnull=True)
#         )
    
#     def get(self, request):
#         qs = self.get_result_queryset()
#         output = DesignationSerializer(qs, many=True)
#         return Response(output.data, status=status.HTTP_200_OK)
    
#     def post(self, request):
#         serializer = DesignationSerializer(data=request.data)
        
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)                       
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
    
#     def put(self, request, pk):
#         try:
#             designation_obj = Designation.objects.get(pk=pk)
#         except Designation.DoesNotExist:
#             return Response({"error": "Designation does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        
#         serializer = DesignationSerializer(designation_obj, data=request.data)
        
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     def delete(self, request, pk):
#         try:
#             designation_obj = Designation.objects.get(pk=pk)
#         except Designation.DoesNotExist:
#             return Response({"error": "Designation does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        
#         designation_obj.delete()
#         return Response({"message": "Successfully deleted"}, status=status.HTTP_200_OK)
    
class DesignationViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Designation
    queryset = Designation.objects.all()
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    serializer_class = DesignationSerializer
    FILTER_FIELDS = {
        'category': 'category',
        'is_hidden': 'is_hidden',
        'on_hold': 'on_hold'
    }

class DesignationListView(RecordRuleMixin, APIView):
    model = Designation
    permission_classes = [IsAuthenticated]
    def get_base_queryset(self):
        return get_regular_query(self.model)
    
    def get(self, request):
        qs = self.get_base_queryset()
        category = request.query_params.get('category', None)
        if category and category != '':
            qs = qs.filter(category=category)
        output = DesignationIdNameSerializer(qs, many=True)
        return Response(output.data, status=status.HTTP_200_OK)
    
