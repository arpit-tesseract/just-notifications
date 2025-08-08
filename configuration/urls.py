from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *

router = DefaultRouter()
router.register(r'countries', CountryViewSet)
router.register(r'continents', ContinentViewSet)
router.register(r'states', StateViewSet)
router.register(r'districts', DistrictViewSet)
router.register(r'cities', CityViewSet)
router.register(r'villages', VillageViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'religion', ReligionViewSet)
router.register(r'sampraday', SampradayViewSet)
router.register(r'panth', PanthViewSet)
router.register(r'varna', VarnaViewSet)
router.register(r'caste', CasteViewSet)
router.register(r'subcaste', SubCasteViewSet)
router.register(r'gotra', GotraViewSet)
router.register(r'subgotra', SubGotraViewSet)
router.register(r'pidhi', PidhiViewSet)
router.register(r'section', SectionViewSet)
router.register(r'class', ClassViewSet)
router.register(r'profCategory', ProfCategoryViewSet)
router.register(r'profSubCategory', ProfSubCategoryViewSet)
router.register(r'type', TypeViewSet)
router.register(r'brand', BrandViewSet)
router.register(r'postmodel', PostModelViewSet)
router.register(r'sector', SectorViewSet)
router.register(r'subsector', SubSectorViewSet)
router.register(r'department', DepartmentViewSet)
router.register(r'subdepartment', SubDepartmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("import/continent/", ImportContinents.as_view()),
    path("import/country/", ImportCountries.as_view()),
    path("import/state/", ImportStates.as_view()),
    path("import/district/", ImportDistricts.as_view()),
    path("import/city/", ImportCities.as_view()),
    path("import/village/", ImportVillages.as_view()),
    path("import/religion/", ImportReligions.as_view()),
    path("import/sampraday/", ImportSampradays.as_view()),
    path("import/panth/", ImportPanths.as_view()),
    path("import/varna/", ImportVarnas.as_view()),
    path("import/caste/", ImportCastes.as_view()),
    path("import/subcaste/", ImportSubCastes.as_view()),
    path("import/gotra/", ImportGotras.as_view()),
    path("import/subgotra/", ImportSubGotras.as_view()),
    path("import/pidhi/", ImportPidhis.as_view()),
    path('import/section/', ImportSection.as_view()),
    path('import/class/', ImportClass.as_view()),
    path('import/profcategory/', ImportProfCategory.as_view()),
    path('import/profsubcategory/', ImportProfSubCategory.as_view()),
    path('import/type/', ImportType.as_view()),
    path('import/brand/', ImportBrand.as_view()),
    path('import/postmodel/', ImportPostModel.as_view()),
    path('import/sector/', ImportSector.as_view()),
    path('import/subsector/', ImportSubSector.as_view()),
    path('import/department/', ImportDepartment.as_view()),
    path('import/subdepartment/', ImportSubDepartment.as_view()),
]
