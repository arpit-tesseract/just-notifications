from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *

router = DefaultRouter()
router.register(r'globs', GlobViewSet)
router.register(r'countries', CountryViewSet)
router.register(r'continents', ContinentViewSet)
router.register(r'states', StateViewSet)
router.register(r'districts', DistrictViewSet)
router.register(r'talukas', TalukaViewSet)
router.register(r'cityvillages', CityVillageViewSet)
router.register(r'wards', WardViewSet)

router.register(r'religions', ReligionViewSet)
router.register(r'sampradays', SampradayViewSet)
router.register(r'panths', PanthViewSet)
router.register(r'varnas', VarnaViewSet)
router.register(r'castes', CasteViewSet)
router.register(r'subcastes', SubCasteViewSet)
router.register(r'gotras', GotraViewSet)
router.register(r'subgotras', SubGotraViewSet)
router.register(r'kuls', KulViewSet)
router.register(r'vanshes', VanshViewSet)
router.register(r'families', FamilyViewSet)
router.register(r'pidhis', PidhiViewSet)

router.register(r'sections', SectionViewSet)
router.register(r'profclasses', ClassViewSet)
router.register(r'categories', ProfCategoryViewSet)
router.register(r'subcategories', ProfSubCategoryViewSet)
router.register(r'sectors', SectorViewSet)
router.register(r'subsectors', SubSectorViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'subdepartments', SubDepartmentViewSet)
router.register(r'types', TypeViewSet)
router.register(r'brands', BrandViewSet)
router.register(r'roomflashes', RoomFlashViewSet)

router.register(r'designations', DesignationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    path('upload/globs/', UploadGlobsView.as_view()),
    path('upload/continents/', UploadContinentsView.as_view()),
    path('upload/countries/', UploadCountriesView.as_view()),
    path('upload/states/', UploadStatesView.as_view()),
    path('upload/districts/', UploadDistrictsView.as_view()),
    path('upload/talukas/', UploadTalukasView.as_view()),
    path('upload/cityvillages/', UploadCityVillagesView.as_view()),
    path('upload/wards/', UploadWardsView.as_view()),
    
    path('upload/religions/', UploadReligionView.as_view()),
    path('upload/sampradays/', UploadSampradayView.as_view()),
    path('upload/panths/', UploadPanthView.as_view()),
    path('upload/varnas/', UploadVarnaView.as_view()),
    path('upload/castes/', UploadCasteView.as_view()),
    path('upload/subcastes/', UploadSubCasteView.as_view()),
    path('upload/gotras/', UploadGotraView.as_view()),
    path('upload/subgotras/', UploadSubGotraView.as_view()),
    path('upload/kuls/', UploadKulView.as_view()),
    path('upload/vanshes/', UploadVanshView.as_view()),
    path('upload/families/', UploadFamilyView.as_view()),
    path('upload/pidhis/', UploadPidhiView.as_view()),
    
    path('upload/sections/', UploadSectionView.as_view()),
    path('upload/profclasses/', UploadClassView.as_view()),
    path('upload/categories/', UploadProfCategoryView.as_view()),
    path('upload/subcategories/', UploadProfSubCategoryView.as_view()),
    path('upload/sectors/', UploadSectorView.as_view()),
    path('upload/subsectors/', UploadSubSectorView.as_view()),
    path('upload/departments/', UploadDepartmentView.as_view()),
    path('upload/subdepartments/', UploadSubDepartmentView.as_view()),
    path('upload/types/', UploadTypeView.as_view()),
    path('upload/brands/', UploadBrandView.as_view()),

    
    path("models/", ModelNameView.as_view(), name="get_models"),
    path("model_access_rules/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    path("model_access_rules/<int:user_id>/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    
    path("residential_search/", ResidentialSearchView.as_view(), name="search_residential"),
    path("personal_search/", PersonalSearchView.as_view(), name="search_personal"),
    path("professional_search/", ProfessionalSearchView.as_view(), name="search_professional"),
    
    path("designation_lst/", DesignationListView.as_view(), name="designation_lst"),
    path("room-flash-lst/", RoomFlashListView.as_view(), name="room_flash_lst"),
]
