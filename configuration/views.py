from django.shortcuts import render, get_object_or_404
import pandas as pd
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import *
from configuration.serializers import *

from shashan.utils.validators import get_related_queryset
from rest_framework.decorators import api_view, permission_classes

from .permissions import HasModelAccessPermission
from .mixins import FilteredQuerysetMixin, RecordRuleMixin, SearchMixin
from django.utils import timezone
from django.db.models import Q

from rest_framework.decorators import action


# CRUD Views
# ========================================
# Residential 
# ========================================
class GlobViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Glob.objects.all() # First time load data when server starts
    model = Glob 
    serializer_class = GlobSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

class GlobListView(SearchMixin, RecordRuleMixin, APIView):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Glob.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = GlobSerializer(queryset, many=True)
        return Response(serializer.data)
    

class ContinentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Continent
    queryset = Continent.objects.all() 
    serializer_class = ContinentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ContinentSerializer   # For POST, PUT, PATCH
        return ContinentDetailSerializer

class ContinentListView(SearchMixin,APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]    
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Continent.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = ContinentSerializer(queryset, many=True)
        return Response(serializer.data)


class CountryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Country
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CountrySerializer   # For POST, PUT, PATCH
        return CountryDetailSerializer

class CountryListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Country.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = CountrySerializer(queryset, many=True)
        return Response(serializer.data)
    

class StateViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = State
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return StateSerializer   # For POST, PUT, PATCH
        return StateDetailSerializer

class StateListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return State.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = StateSerializer(queryset, many=True)
        return Response(serializer.data)
   
   
class DistrictViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = District
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DistrictSerializer   # For POST, PUT, PATCH
        return DistrictDetailSerializer

class DistrictListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return District.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = DistrictSerializer(queryset, many=True)
        return Response(serializer.data)


class TalukaViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Taluka
    queryset = Taluka.objects.all()
    serializer_class = TalukaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TalukaSerializer   # For POST, PUT, PATCH
        return TalukaDetailSerializer

class TalukaListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Taluka.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = TalukaSerializer(queryset, many=True)
        return Response(serializer.data)
    

class CityVillageViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = CityVillage
    queryset = CityVillage.objects.all()
    serializer_class = CityVillageSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CityVillageSerializer   # For POST, PUT, PATCH
        return CityVillageDetailSerializer

class CityVillageListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return CityVillage.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = CityVillageSerializer(queryset, many=True)
        return Response(serializer.data)
    

class WardViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Ward
    queryset = Ward.objects.all()
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return WardSerializer   # For POST, PUT, PATCH
        return WardDetailSerializer

class WardListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Ward.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = WardSerializer(queryset, many=True)
        return Response(serializer.data)
    


# ========================================
# Personal 
# ========================================
class ReligionViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Religion
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
class ReligionListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Religion.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = ReligionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    
class SampradayViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Sampraday
    queryset = Sampraday.objects.all()
    serializer_class = SampradaySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]  
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SampradaySerializer   # For POST, PUT, PATCH
        return SampradayDetailSerializer 

class SampradayListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Sampraday.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )     
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = SampradaySerializer(queryset, many=True)
        return Response(serializer.data)


class PanthViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Panth
    queryset = Panth.objects.all()
    serializer_class = PanthSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PanthSerializer   # For POST, PUT, PATCH
        return PanthDetailSerializer

class PanthListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Panth.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = PanthSerializer(queryset, many=True)
        return Response(serializer.data)
    

class VarnaViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Varna
    queryset = Varna.objects.all()
    serializer_class = VarnaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VarnaSerializer   # For POST, PUT, PATCH
        return VarnaDetailSerializer

class VarnaListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Varna.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = VarnaSerializer(queryset, many=True)
        return Response(serializer.data)
    

class CasteViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Caste
    queryset = Caste.objects.all()
    serializer_class = CasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CasteSerializer   # For POST, PUT, PATCH
        return CasteDetailSerializer

class CasteListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Caste.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = CasteSerializer(queryset, many=True)
        return Response(serializer.data)
    
    
class SubCasteViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubCaste
    queryset = SubCaste.objects.all()
    serializer_class = SubCasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]    
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubCasteSerializer   # For POST, PUT, PATCH
        return SubCasteDetailSerializer

class SubCasteListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return SubCaste.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = SubCasteSerializer(queryset, many=True)
        return Response(serializer.data)


class GotraViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Gotra
    queryset = Gotra.objects.all()
    serializer_class = GotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GotraSerializer   # For POST, PUT, PATCH
        return GotraDetailSerializer

class GotraListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Gotra.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = GotraSerializer(queryset, many=True)
        return Response(serializer.data)
    

class SubGotraViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = SubGotra
    queryset = SubGotra.objects.all()
    serializer_class = SubGotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]   
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return SubGotraSerializer   # For POST, PUT, PATCH
        return SubGotraDetailSerializer 

class SubGotraListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return SubGotra.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = SubGotraSerializer(queryset, many=True)
        return Response(serializer.data)


class KulViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Kul
    queryset = Kul.objects.all()
    serializer_class = KulSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return KulSerializer   # For POST, PUT, PATCH
        return KulDetailSerializer

class KulListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Kul.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = KulSerializer(queryset, many=True)
        return Response(serializer.data)


class VanshViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Vansh
    queryset = Vansh.objects.all()
    serializer_class = VanshSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return VanshSerializer   # For POST, PUT, PATCH
        return VanshDetailSerializer

class VanshListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Vansh.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = VanshSerializer(queryset, many=True)
        return Response(serializer.data)

class FamilyViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Family
    queryset = Family.objects.all()
    serializer_class = FamilySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return FamilySerializer   # For POST, PUT, PATCH
        return FamilyDetailSerializer

class FamilyListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Family.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = FamilySerializer(queryset, many=True)
        return Response(serializer.data)


class PidhiViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    model = Pidhi
    queryset = Pidhi.objects.all()
    serializer_class = PidhiSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PidhiSerializer   # For POST, PUT, PATCH
        return PidhiDetailSerializer

class PidhiListView(SearchMixin, APIView, RecordRuleMixin):
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    def get_base_queryset(self):
        today = timezone.now().date()
        
        return Pidhi.objects.filter(
            is_hidden=False,
            on_hold=False
        ).filter(
            Q(hold_date__lte=today) | Q(hold_date__isnull=True)
        )
    
    def get(self, request):
        queryset = self.get_result_queryset()   # search applied automatically
        serializer = PidhiSerializer(queryset, many=True)
        return Response(serializer.data)
    
    
# ========================================
# Professional 
# ========================================
class SectionViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]    


class ClassViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return ClassDetailSerializer
        return super().get_serializer_class()


class ProfCategoryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = ProfCategory.objects.all()
    serializer_class = ProfCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProfCategoryDetailSerializer
        return super().get_serializer_class()
    

class ProfSubCategoryViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = ProfSubCategory.objects.all()
    serializer_class = ProfSubCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProfSubCategoryDetailSerializer
        return super().get_serializer_class()
    
    
class TypeViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return TypeDetailSerializer
        return super().get_serializer_class()
    

class BrandViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return BrandDetailSerializer
        return super().get_serializer_class()


class PostModelViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = PostModel.objects.all()
    serializer_class = PostModelSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostModelDetailSerializer
        return super().get_serializer_class()


class SectorViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return SectorDetailSerializer
        return super().get_serializer_class()
    

class SubSectorViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = SubSector.objects.all()
    serializer_class = SubSectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubSectorDetailSerializer
        return super().get_serializer_class()


class DepartmentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return DepartmentDetailSerializer
        return super().get_serializer_class()
    

class SubDepartmentViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = SubDepartment.objects.all()
    serializer_class = SubDepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubDepartmentDetailSerializer
        return super().get_serializer_class()
    

class RoomFlashViewSet(FilteredQuerysetMixin, RecordRuleMixin, viewsets.ModelViewSet):
    queryset = RoomFlash.objects.all()
    serializer_class = RoomFlashSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    

# ==================
# Import Features
# ==================


def clean(value):
    return str(value).strip() if pd.notnull(value) else None


class ImportContinents(APIView):
    model = Continent
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            name = clean(row.get("Continent"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Continent' or 'Code'")
                continue

            obj, is_created = Continent.objects.get_or_create(
                name__iexact=name,
                code__iexact=code,
                defaults={"name": name, "code": code},
            )
            if is_created:
                created += 1

        return Response({"created": created, "errors": errors})


class ImportCountries(APIView):
    model = Country
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            continent_code = clean(row.get("Continent Code"))
            name = clean(row.get("Country"))
            code = clean(row.get("Code"))

            if not name or not code or not continent_code:
                errors.append(
                    f"Row {row_num}: Missing 'Country', 'Code', or 'Continent Code'"
                )
                continue

            try:
                continent = Continent.objects.get(code__iexact=continent_code)
                obj, is_created = Country.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    continent=continent,
                    defaults={"name": name, "code": code, "continent": continent},
                )
                if is_created:
                    created += 1
            except Continent.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Continent with code '{continent_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportStates(APIView):
    model = State
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            country_code = clean(row.get("Country Code"))
            name = clean(row.get("State"))
            code = clean(row.get("Code"))

            if not name or not code or not country_code:
                errors.append(
                    f"Row {row_num}: Missing 'State', 'Code', or 'Country Code'"
                )
                continue

            try:
                country = Country.objects.get(code__iexact=country_code)
                obj, is_created = State.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    country=country,
                    defaults={"name": name, "code": code, "country": country},
                )
                if is_created:
                    created += 1
            except Country.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Country with code '{country_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportDistricts(APIView):
    model = District
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            state_code = clean(row.get("State Code"))
            name = clean(row.get("District"))
            code = clean(row.get("Code"))

            if not name or not code or not state_code:
                errors.append(
                    f"Row {row_num}: Missing 'District', 'Code', or 'State Code'"
                )
                continue

            try:
                state = State.objects.get(code__iexact=state_code)
                obj, is_created = District.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    state=state,
                    defaults={"name": name, "code": code, "state": state},
                )
                if is_created:
                    created += 1
            except State.DoesNotExist:
                errors.append(
                    f"Row {row_num}: State with code '{state_code}' not found"
                )

        return Response({"created": created, "errors": errors})


# class ImportCities(APIView):
#     model = City
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]

#     def post(self, request):
#         file = request.FILES.get("file")
#         if not file:
#             return Response({"error": "No file uploaded."}, status=400)

#         try:
#             df = pd.read_excel(file, dtype={"Code": str})
#         except Exception as e:
#             return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

#         created = 0
#         errors = []

#         for idx, row in df.iterrows():
#             row_num = idx + 2
#             district_code = clean(row.get("District Code"))
#             name = clean(row.get("City"))
#             code = clean(row.get("Code"))

#             if not name or not code or not district_code:
#                 errors.append(
#                     f"Row {row_num}: Missing 'City', 'Code', or 'District Code'"
#                 )
#                 continue

#             try:
#                 district = District.objects.get(code__iexact=district_code)
#                 obj, is_created = City.objects.get_or_create(
#                     name__iexact=name,
#                     code__iexact=code,
#                     district=district,
#                     defaults={"name": name, "code": code, "district": district},
#                 )
#                 if is_created:
#                     created += 1
#             except District.DoesNotExist:
#                 errors.append(
#                     f"Row {row_num}: District with code '{district_code}' not found"
#                 )

#         return Response({"created": created, "errors": errors})


# class ImportVillages(APIView):
#     model = Village
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]

#     def post(self, request):
#         file = request.FILES.get("file")
#         if not file:
#             return Response({"error": "No file uploaded."}, status=400)

#         try:
#             df = pd.read_excel(file, dtype={"Code": str})
#         except Exception as e:
#             return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

#         created = 0
#         errors = []

#         for idx, row in df.iterrows():
#             row_num = idx + 2
#             district_code = clean(row.get("District Code"))
#             name = clean(row.get("Village"))
#             code = clean(row.get("Code"))
#             city_code = clean(row.get("City Code"))

#             if not name or not code or not district_code:
#                 errors.append(
#                     f"Row {row_num}: Missing 'Village', 'Code', or 'District Code'"
#                 )
#                 continue

#             try:
#                 district = District.objects.get(code__iexact=district_code)
#                 city = None
#                 if city_code:
#                     try:
#                         city = City.objects.get(code__iexact=city_code)
#                     except City.DoesNotExist:
#                         errors.append(
#                             f"Row {row_num}: City with code '{city_code}' not found"
#                         )

#                 village_defaults = {"name": name, "code": code, "district": district}
#                 if city:
#                     village_defaults["city"] = city

#                 obj, is_created = Village.objects.get_or_create(
#                     name__iexact=name,
#                     code__iexact=code,
#                     district=district,
#                     defaults=village_defaults,
#                 )
#                 if is_created:
#                     created += 1
#             except District.DoesNotExist:
#                 errors.append(
#                     f"Row {row_num}: District with code '{district_code}' not found"
#                 )

#         return Response({"created": created, "errors": errors})


# class ImportWards(APIView):
#     model = Ward
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]

#     def post(self, request):
#         file = request.FILES.get("file")
#         if not file:
#             return Response({"error": "No file uploaded."}, status=400)

#         try:
#             df = pd.read_excel(file, dtype={"Code": str})
#         except Exception as e:
#             return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

#         created = 0
#         errors = []

#         for idx, row in df.iterrows():
#             row_num = idx + 2
#             village_code = clean(row.get("Village Code"))
#             code = clean(row.get("Ward"))
#             city_code = clean(row.get("City Code"))

#             if not code or (not village_code and not city_code):
#                 errors.append(
#                     f"Row {row_num}: Missing 'Ward', or invalid 'Village Code'/'City Code'. "
#                     "Provide either Village Code or City Code."
#                 )
#                 continue

#             city = None
#             village = None

#             # Resolve City
#             if city_code:
#                 try:
#                     city = City.objects.get(code__iexact=city_code)
#                 except City.DoesNotExist:
#                     errors.append(f"Row {row_num}: City with code '{city_code}' not found")
#                     continue

#             # Resolve Village
#             if village_code:
#                 try:
#                     village = Village.objects.get(code__iexact=village_code)
#                 except Village.DoesNotExist:
#                     errors.append(f"Row {row_num}: Village with code '{village_code}' not found")
#                     continue

#             ward = Ward.objects.filter(
#                 code__iexact=code,
#                 village=village,
#                 city=city
#             ).first()

#             if not ward:
#                 Ward.objects.create(code=code, village=village, city=city)
#                 created += 1

#         return Response({"created": created, "errors": errors})


# class ImportSocities(APIView):
#     model = Society
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]

#     def post(self, request):
#         file = request.FILES.get("file")
#         if not file:
#             return Response({"error": "No file uploaded."}, status=400)

#         try:
#             df = pd.read_excel(file, dtype={"Code": str})
#         except Exception as e:
#             return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

#         created = 0
#         errors = []

#         for idx, row in df.iterrows():
#             row_num = idx + 2
#             ward_code = clean(row.get("Ward Code"))
#             name = clean(row.get("Society"))
#             code = clean(row.get("Code"))

#             if not name or not code or not ward_code:
#                 errors.append(
#                     f"Row {row_num}: Missing 'Society', 'Code', or 'Ward Code'"
#                 )
#                 continue

#             try:
#                 ward = Ward.objects.get(code__iexact=ward_code)

#                 obj, is_created = Society.objects.get_or_create(
#                     name__iexact=name,
#                     code__iexact=code,
#                     ward=ward,
#                     defaults={"name": name, "code": code, "ward": ward},
#                 )
#                 if is_created:
#                     created += 1
#             except Ward.DoesNotExist:
#                 errors.append(f"Row {row_num}: Ward with code '{ward_code}' not found")

#         return Response({"created": created, "errors": errors})


# class ImportBlocks(APIView):
#     model = Block
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]

#     def post(self, request):
#         file = request.FILES.get("file")
#         if not file:
#             return Response({"error": "No file uploaded."}, status=400)

#         try:
#             df = pd.read_excel(file, dtype={"Code": str})
#         except Exception as e:
#             return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

#         created = 0
#         errors = []

#         for idx, row in df.iterrows():
#             row_num = idx + 2
#             society_code = clean(row.get("Society Code"))
#             name = clean(row.get("Block"))

#             if not name or not society_code:
#                 errors.append(f"Row {row_num}: Missing 'Block' or 'Society Code'")
#                 continue

#             try:
#                 society = Society.objects.get(code__iexact=society_code)

#                 obj, is_created = Block.objects.get_or_create(
#                     name__iexact=name,
#                     society=society,
#                     defaults={"name": name, "society": society},
#                 )
#                 if is_created:
#                     created += 1
#             except Society.DoesNotExist:
#                 errors.append(
#                     f"Row {row_num}: Society with code '{society_code}' not found"
#                 )

#         return Response({"created": created, "errors": errors})


# class ImportHouses(APIView):
#     model = Houses
#     parser_classes = [MultiPartParser]
#     permission_classes = [IsAuthenticated, HasModelAccessPermission]

#     def post(self, request):
#         file = request.FILES.get("file")
#         if not file:
#             return Response({"error": "No file uploaded."}, status=400)

#         try:
#             df = pd.read_excel(file, dtype={"Code": str})
#         except Exception as e:
#             return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

#         created = 0
#         errors = []

#         for idx, row in df.iterrows():
#             row_num = idx + 2
#             block = clean(row.get("Block"))
#             code = clean(row.get("Number of Flats/Houses"))

#             if not code or not block:
#                 errors.append(
#                     f"Row {row_num}: Missing 'Block' or 'Number of Flats/Houses'"
#                 )
#                 continue

#             try:
#                 block = Block.objects.get(name__iexact=block)

#                 obj, is_created = Houses.objects.get_or_create(
#                     code__iexact=code,
#                     block=block,
#                     defaults={"code": code, "block": block},
#                 )
#                 if is_created:
#                     created += 1
#             except Block.DoesNotExist:
#                 errors.append(f"Row {row_num}: '{block}' not found")

#         return Response({"created": created, "errors": errors})

class ImportReligions(APIView):
    model = Religion
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            name = clean(row.get("Religion"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Religion' or 'Code'")
                continue

            obj, is_created = Religion.objects.get_or_create(
                name__iexact=name,
                code__iexact=code,
                defaults={"name": name, "code": code},
            )
            if is_created:
                created += 1

        return Response({"created": created, "errors": errors})


class ImportSampradays(APIView):
    model = Sampraday
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            religion_code = clean(row.get("Religion Code"))
            name = clean(row.get("Sampraday"))
            code = clean(row.get("Code"))

            if not name or not code or not religion_code:
                errors.append(
                    f"Row {row_num}: Missing 'Sampraday', 'Code', or 'Religion Code'"
                )
                continue

            try:
                religion = Religion.objects.get(code__iexact=religion_code)
                obj, is_created = Sampraday.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    religion=religion,
                    defaults={"name": name, "code": code, "religion": religion},
                )
                if is_created:
                    created += 1
            except Religion.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Religion with code '{religion_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportPanths(APIView):
    model = Panth
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            sampraday_code = clean(row.get("Sampraday Code"))
            name = clean(row.get("Panth"))
            code = clean(row.get("Code"))

            if not name or not code or not sampraday_code:
                errors.append(
                    f"Row {row_num}: Missing 'Panth', 'Code', or 'Sampraday Code'"
                )
                continue

            try:
                sampraday = Sampraday.objects.get(code__iexact=sampraday_code)
                obj, is_created = Panth.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    sampraday=sampraday,
                    defaults={"name": name, "code": code, "sampraday": sampraday},
                )
                if is_created:
                    created += 1
            except Sampraday.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Sampraday with code '{sampraday_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportVarnas(APIView):
    model = Varna
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            panth_code = clean(row.get('Panth Code'))
            name = clean(row.get('Varna'))
            code = clean(row.get('Code'))

            if not name or not code or not panth_code:
                errors.append(f"Row {row_num}: Missing 'Varna' or 'Code' or 'Panth Code'")
                continue

            try:
                panth = Panth.objects.get(code__iexact=panth_code)
                obj, is_created = Varna.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    panth=panth,
                    defaults={"name": name, "code": code, "panth":panth}
                )
                if is_created:
                    created+= 1
            except Panth.DoesNotExist:
                errors.append(f"Row {row_num}: Panth with code '{panth_code}' not found")

        return Response({"created": created, "errors": errors})


class ImportCastes(APIView):
    model = Caste
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            varna_code = clean(row.get("Varna Code"))
            name = clean(row.get("Caste"))
            code = clean(row.get("Code"))

            if not name or not code or not varna_code:
                errors.append(
                    f"Row {row_num}: Missing 'Caste', 'Code', or 'Varna Code'"
                )
                continue

            try:
                varna = Varna.objects.get(code__iexact=varna_code)
                obj, is_created = Caste.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    varna=varna,
                    defaults={"name": name, "code": code, "varna": varna},
                )
                if is_created:
                    created += 1
            except Varna.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Varna with code '{varna_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportSubCastes(APIView):
    model = SubCaste
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            caste_code = clean(row.get("Caste Code"))
            name = clean(row.get("SubCaste"))
            code = clean(row.get("Code"))

            if not name or not code or not caste_code:
                errors.append(
                    f"Row {row_num}: Missing 'SubCaste', 'Code', or 'Caste Code'"
                )
                continue

            try:
                caste = Caste.objects.get(code__iexact=caste_code)
                obj, is_created = SubCaste.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    caste=caste,
                    defaults={"name": name, "code": code, "caste": caste},
                )
                if is_created:
                    created += 1
            except Caste.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Caste with code '{caste_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportGotras(APIView):
    model = Gotra
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            subcaste_code = clean(row.get("SubCaste Code"))
            name = clean(row.get("Gotra"))
            code = clean(row.get("Code"))

            if not name or not code or not subcaste_code:
                errors.append(f"Row {row_num}: Missing 'Gotra', 'Code', or 'SubCaste Code'")
                continue

            try:
                subcaste = SubCaste.objects.get(code__iexact=subcaste_code)
                obj, is_created = Gotra.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    subcaste=subcaste,
                    defaults={"name": name, "code": code, "subcaste": subcaste}
                )
                if is_created:
                    created += 1
            except Caste.DoesNotExist:
                errors.append(f"Row {row_num}: SubCaste with code '{subcaste_code}' not found")

        return Response({"created": created, "errors": errors})


class ImportSubGotras(APIView):
    model = SubGotra
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            gotra_code = clean(row.get("Gotra Code"))
            name = clean(row.get("SubGotra"))
            code = clean(row.get("Code"))

            if not name or not code or not gotra_code:
                errors.append(
                    f"Row {row_num}: Missing 'SubGotra', 'Code', or 'Gotra Code'"
                )
                continue

            try:
                gotra = Gotra.objects.get(code__iexact=gotra_code)
                obj, is_created = SubGotra.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    gotra=gotra,
                    defaults={"name": name, "code": code, "gotra": gotra},
                )
                if is_created:
                    created += 1
            except Gotra.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Gotra with code '{gotra_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportPidhis(APIView):
    model = Pidhi
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={"Code": str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            subgotra_code = clean(row.get("SubGotra Code"))
            name = clean(row.get("Pidhi"))
            code = clean(row.get("Code"))

            if not name or not code or not subgotra_code:
                errors.append(
                    f"Row {row_num}: Missing 'Pidhi', 'Code', or 'SubGotra Code'"
                )
                continue

            try:
                subgotra = SubGotra.objects.get(code__iexact=subgotra_code)
                obj, is_created = Pidhi.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    subgotra=subgotra,
                    defaults={"name": name, "code": code, "subgotra": subgotra},
                )
                if is_created:
                    created += 1
            except SubGotra.DoesNotExist:
                errors.append(
                    f"Row {row_num}: SubGotra with code '{subgotra_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportSection(APIView):
    model = Section
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []
        for idx, row in df.iterrows():
            row_num = idx + 2
            name = clean(row.get("Section"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Section' or 'Code'")
                continue

            obj, is_created = Section.objects.get_or_create(
                name__iexact=name,
                code__iexact=code,
                defaults={"name": name, "code": code},
            )
            if is_created:
                created += 1

        return Response({"created": created, "errors": errors})


class ImportClass(APIView):
    model = Class
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            section_code = clean(row.get("Section Code"))
            name = clean(row.get("Class"))
            code = clean(row.get("Code"))

            if not section_code or not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Section Code', 'Class' or 'Code'"
                )
                continue

            try:
                section = Section.objects.get(code__iexact=section_code)
                obj, is_created = Class.objects.get_or_create(
                    name__iexact=name,
                    section=section,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "section": section},
                )
                if is_created:
                    created += 1

            except Section.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Section with code '{section_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportProfCategory(APIView):
    model = ProfCategory
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            class_code = clean(row.get("Class Code"))
            name = clean(row.get("Category"))
            code = clean(row.get("Code"))

            if not class_code or not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Class Code', 'Category' or 'Code'"
                )
                continue

            try:
                profclass = Class.objects.get(code__iexact=class_code)
                obj, is_created = ProfCategory.objects.get_or_create(
                    name__iexact=name,
                    profclass=profclass,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "profclass": profclass},
                )
                if is_created:
                    created += 1

            except Class.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Class with code '{class_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportProfSubCategory(APIView):
    model = ProfSubCategory
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            category_code = clean(row.get("Category Code"))
            name = clean(row.get("Sub Category"))
            code = clean(row.get("Code"))

            if not category_code or not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Category Code', 'Sub Category' or 'Code'"
                )
                continue

            try:
                category = ProfCategory.objects.get(code__iexact=category_code)
                obj, is_created = ProfSubCategory.objects.get_or_create(
                    name__iexact=name,
                    category=category,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "category": category},
                )
                if is_created:
                    created += 1

            except ProfCategory.DoesNotExist:
                errors.append(f"Row {row_num}: Category with code '{category_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportSector(APIView):
    model = Sector
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded."}, status=400)
        
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)
        
        created, errors = 0, []
        for idx, row in df.iterrows():
            row_num = idx + 2
            subcategory_code = clean(row.get("SubCategory Code"))
            name = clean(row.get("Sector"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Sector' or 'Code' or 'SubCategory Code'")
                continue

            try:
                subcategory = ProfSubCategory.objects.get(code__iexact=subcategory_code)

                obj, is_created = Sector.objects.get_or_create(
                    subcategory = subcategory,
                    name__iexact=name,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "subcategory": subcategory}
                )
                if is_created:
                    created += 1
            except ProfSubCategory.DoesNotExist:
                errors.append(f"Row {row_num}: SubCategory with code '{subcategory_code}' not found")


        return Response({"created": created, "errors": errors})

class ImportSubSector(APIView):
    model = SubSector
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            sector_code = clean(row.get('Sector Code')) 
            name = clean(row.get('Sub Sector'))
            code = clean(row.get('Code'))

            if not sector_code or not name or not code:
                errors.append(f"Row {row_num}: Missing 'Sector Code', 'Sub Sector' or 'Code'")
                continue

            try:
                sector = Sector.objects.get(code__iexact=sector_code)
                obj, is_created = SubSector.objects.get_or_create(
                    name__iexact=name,
                    sector=sector,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "sector": sector}
                )
                if is_created:
                    created +=1
            
            except Sector.DoesNotExist:
                errors.append(f"Row {row_num}: Sector with code '{sector_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportDepartment(APIView):
    model = Department
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded."}, status=400)
        
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)
        
        created, errors = 0, []
        for idx, row in df.iterrows():
            row_num = idx + 2
            subsector_code = clean(row.get("SubSector Code"))
            name = clean(row.get("Department"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Department' or 'Code' or 'SubSector Code'")
                continue

            try:
                subsector = SubSector.objects.get(code__iexact=subsector_code)
                obj, is_created = Department.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    subsector=subsector,
                    defaults={"name": name, "code": code, "subsector":subsector}
                )
                if is_created:
                    created += 1
            except SubSector.DoesNotExist:
                errors.append(f"Row {row_num}: SubSector with code '{subsector_code}' not found")

        return Response({"created": created, "errors": errors})
    
class ImportSubDepartment(APIView):
    model = SubDepartment
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            department_code = clean(row.get('Department Code')) 
            name = clean(row.get('Sub Department'))
            code = clean(row.get('Code'))

            if not department_code or not name or not code:
                errors.append(f"Row {row_num}: Missing 'Department Code', 'Sub Department' or 'Code'")
                continue

            try:
                department = Department.objects.get(code__iexact=department_code)
                obj, is_created = SubDepartment.objects.get_or_create(
                    name__iexact=name,
                    department=department,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "department": department}
                )
                if is_created:
                    created +=1
            
            except Department.DoesNotExist:
                errors.append(f"Row {row_num}: Department with code '{department_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportType(APIView):
    model = Type
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            subdepartment_code = clean(row.get('SubDepartment Code')) 
            name = clean(row.get('Type'))
            code = clean(row.get('Code'))

            if not subdepartment_code or not name or not code:
                errors.append(f"Row {row_num}: Missing 'SubDepartment Code', 'Type' or 'Code'")
                continue

            try:
                subdepartment = SubDepartment.objects.get(code__iexact=subdepartment_code)
                obj, is_created = Type.objects.get_or_create(
                    name__iexact=name,
                    subdepartment=subdepartment,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "subdepartment": subdepartment}
                )
                if is_created:
                    created +=1
            
            except SubDepartment.DoesNotExist:
                errors.append(f"Row {row_num}: SubDepartment with code '{subdepartment_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportBrand(APIView):
    model = Brand
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            type_code = clean(row.get('Type Code')) 
            name = clean(row.get('Brand'))
            code = clean(row.get('Code'))

            if not type_code or not name or not code:
                errors.append(f"Row {row_num}: Missing 'Type Code', 'Brand' or 'Code'")
                continue

            try:
                type = Type.objects.get(code__iexact=type_code)
                obj, is_created = Brand.objects.get_or_create(
                    name__iexact=name,
                    type=type,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "type": type}
                )
                if is_created:
                    created +=1
            
            except Type.DoesNotExist:
                errors.append(f"Row {row_num}: Type with code '{type_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportPostModel(APIView):
    model = PostModel
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file Uploaded."}, status=400)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            brand_code = clean(row.get('Brand Code')) 
            name = clean(row.get('Post Model'))
            code = clean(row.get('Code'))

            if not brand_code or not name or not code:
                errors.append(f"Row {row_num}: Missing 'Brand Code', 'Post Model' or 'Code'")
                continue

            try:
                brand = Brand.objects.get(code__iexact=brand_code)
                obj, is_created = PostModel.objects.get_or_create(
                    name__iexact=name,
                    brand=brand,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "brand": brand}
                )
                if is_created:
                    created +=1
            
            except Brand.DoesNotExist:
                errors.append(f"Row {row_num}: Brand with code '{brand_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportRoomFlash(APIView):
    model = RoomFlash
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded."}, status=400)
        try:
            df = pd.read_excel(file, dtype={'Code': str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created, errors = 0, []

        for idx, row in df.iterrows():
            row_num = idx + 2
            name = clean(row.get("Room Name"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Room Name' or 'Code'")
                continue

            obj, is_created = RoomFlash.objects.get_or_create(
                name__iexact=name,
                code__iexact=code,
                defaults={"name":name, "code":code}
            )
            if is_created:
                created += 1

        return Response({"created": created, "errors": errors})
    
# @api_view(['GET'])
# @permission_classes([IsAuthenticated, HasModelAccessPermission])
# def get_countries_by_continent(request, continent_id):
#     return get_related_queryset(request, Country, CountrySerializer, "continent", continent_id)

class ContinentsByGlobView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Continent.objects.all()
    serializer_class = ContinentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]
    
    def get(self, request, glob_id):
        qs = self.queryset.filter(glob=glob_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)

class CountriesByContinentView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, continent_id):
        qs = self.queryset.filter(continent=continent_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class StatesByCountryView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, country_id):
        qs = self.queryset.filter(country=country_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class DistrictsByStateView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, state_id):
        qs = self.queryset.filter(state=state_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class TalukaByDistrictView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Taluka.objects.all()
    serializer_class = TalukaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, district_id):
        qs = self.queryset.filter(district=district_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class CityVillagesByTalukaView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = CityVillage.objects.all()
    serializer_class = CityVillageSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, taluka_id):
        qs = self.queryset.filter(taluka=taluka_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class WardsByCityVillageView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Ward.objects.all()
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, cityvillage_id):
        qs = self.queryset.filter(city_village=cityvillage_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)



class ClassesBySectionView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, section_id):
        qs = self.queryset.filter(section=section_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class ProfCategoryByClassView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = ProfCategory.objects.all()
    serializer_class = ProfCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, class_id):
        qs = self.queryset.filter(profclass=class_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class ProfSubCategoryByCategoryView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = ProfSubCategory.objects.all()
    serializer_class = ProfSubCategorySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, category_id):
        qs = self.queryset.filter(category=category_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class SectorBySubCategoryView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, subcategory_id):
        qs = self.queryset.filter(subcategory=subcategory_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class SubSectorBySectorView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = SubSector.objects.all()
    serializer_class = SubSectorSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, sector_id):
        qs = self.queryset.filter(sector=sector_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class DepartmentsBySubSectorView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, subsector_id):
        qs = self.queryset.filter(subsector=subsector_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class SubDepartmentsByDepartmentView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = SubDepartment.objects.all()
    serializer_class = SubDepartmentSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, department_id):
        qs = self.queryset.filter(department=department_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class TypeBySubDepartmentView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, subdepartment_id):
        qs = self.queryset.filter(subdepartment=subdepartment_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class BrandByTypeView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, type_id):
        qs = self.queryset.filter(type=type_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class PostModelByBrandView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = PostModel.objects.all()
    serializer_class = PostModelSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, brand_id):
        qs = self.queryset.filter(brand=brand_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class SampradayByReligionView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Sampraday.objects.all()
    serializer_class = SampradaySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, religion_id):
        qs = self.queryset.filter(religion=religion_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class PanthBySampradayView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Panth.objects.all()
    serializer_class = PanthSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, sampraday_id):
        qs = self.queryset.filter(sampraday=sampraday_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class VarnaByPanthView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Varna.objects.all()
    serializer_class = VarnaSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, panth_id):
        qs = self.queryset.filter(panth=panth_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class CasteByVarnaView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Caste.objects.all()
    serializer_class = CasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, varna_id):
        qs = self.queryset.filter(varna=varna_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class SubCasteByCasteView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = SubCaste.objects.all()
    serializer_class = SubCasteSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, caste_id):
        qs = self.queryset.filter(caste=caste_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class GotraBySubCasteView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Gotra.objects.all()
    serializer_class = GotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, subcaste_id):
        qs = self.queryset.filter(subcaste=subcaste_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class SubGotraByGotraView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = SubGotra.objects.all()
    serializer_class = SubGotraSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, gotra_id):
        qs = self.queryset.filter(gotra=gotra_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class KulBySubGotraView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Kul.objects.all()
    serializer_class = KulSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, subgotra_id):
        qs = self.queryset.filter(subgotra=subgotra_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class VanshByKulView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Vansh.objects.all()
    serializer_class = VanshSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, kul_id):
        qs = self.queryset.filter(kul=kul_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class FamilyByVanshView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, vansh_id):
        qs = self.queryset.filter(vansh=vansh_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class PidhiByFamilyView(FilteredQuerysetMixin, RecordRuleMixin, APIView):
    queryset = Pidhi.objects.all()
    serializer_class = PidhiSerializer
    permission_classes = [IsAuthenticated, HasModelAccessPermission]

    def get(self, request, family_id):
        qs = self.queryset.filter(family=family_id)
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


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


