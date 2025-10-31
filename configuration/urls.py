from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import *

router = DefaultRouter()
router.register(r'globs_in_details', GlobViewSet)
router.register(r'countries_in_details', CountryViewSet)
router.register(r'continents_in_details', ContinentViewSet)
router.register(r'states_in_details', StateViewSet)
router.register(r'districts_in_details', DistrictViewSet)
router.register(r'talukas_in_details', TalukaViewSet)
router.register(r'cityvillages_in_details', CityVillageViewSet)
router.register(r'wards_in_details', WardViewSet)

router.register(r'religions_in_details', ReligionViewSet)
router.register(r'sampradays_in_details', SampradayViewSet)
router.register(r'panths_in_details', PanthViewSet)
router.register(r'varnas_in_details', VarnaViewSet)
router.register(r'castes_in_details', CasteViewSet)
router.register(r'subcastes_in_details', SubCasteViewSet)
router.register(r'gotras_in_details', GotraViewSet)
router.register(r'subgotras_in_details', SubGotraViewSet)
router.register(r'kuls_in_details', KulViewSet)
router.register(r'vanshes_in_details', VanshViewSet)
router.register(r'families_in_details', FamilyViewSet)
router.register(r'pidhis_in_details', PidhiViewSet)

router.register(r'sections_in_details', SectionViewSet)
router.register(r'profclasses_in_details', ClassViewSet)
router.register(r'categories_in_details', ProfCategoryViewSet)
router.register(r'subcategories_in_details', ProfSubCategoryViewSet)
router.register(r'sectors_in_details', SectorViewSet)
router.register(r'subsectors_in_details', SubSectorViewSet)
router.register(r'departments_in_details', DepartmentViewSet)
router.register(r'subdepartments_in_details', SubDepartmentViewSet)
router.register(r'types_in_details', TypeViewSet)
router.register(r'brands_in_details', BrandViewSet)
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
]
