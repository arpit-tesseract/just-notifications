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
router.register(r'wards', WardViewSet)
router.register(r'societies', SocietyViewSet)
router.register(r'blocks', BlockViewSet)
router.register(r'housenums', HousesViewSet)
# router.register(r'accessactivity', AccessesViewSet)
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
router.register(r'roomflash', RoomFlashViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("import/continent/", ImportContinents.as_view()),
    path("import/country/", ImportCountries.as_view()),
    path("import/state/", ImportStates.as_view()),
    path("import/district/", ImportDistricts.as_view()),
    path("import/city/", ImportCities.as_view()),
    path("import/village/", ImportVillages.as_view()),
    path("import/ward/", ImportWards.as_view()),
    path("import/society/", ImportSocities.as_view()),
    path("import/block/", ImportBlocks.as_view()),
    path("import/housenum/", ImportHouses.as_view()),
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
    path('import/roomflash/', ImportRoomFlash.as_view()),

    # To get the related queryset
    # path("get_countries/<int:continent_id>/", get_countries_by_continent),
    path("get_countries/<int:continent_id>/", CountriesByContinentView.as_view(), name="get_countries_by_continent"),

    path("get_states/<int:country_id>/", get_states_by_country),
    path("get_districts/<int:state_id>/", get_districts_by_state),
    path("get_cities/<int:district_id>/", get_cities_by_district),
    path("get_villages/by-district/<int:district_id>/", get_villages_by_district_city, name="get_villages_by_district"),
    path("get_villages/by-city/<int:city_id>/", get_villages_by_district_city, name="get_villages_by_city"),
    path("get_wards/by-city/<int:city_id>/", get_wards_by_village_city, name="get_wards_by_city"),
    path("get_wards/by-village/<int:village_id>/", get_wards_by_village_city, name="get_wards_by_village"),
    path("get_societies/<int:ward_id>/", get_society_by_ward),
    path("get_blocks/<int:society_id>/", get_blocks_by_society),
    path("get_houses/<int:block_id>", get_houses_by_block),
    path("get_classes/<int:section_id>/", get_classes_by_section),
    path("get_categories/<int:class_id>/", get_category_by_class),
    path("get_subcategories/<int:category_id>/", get_subcategory_by_category),
    path("get_sectors/<int:subcategory_id>/", get_sectors_by_subcategory),
    path("get_subsectors/<int:sector_id>/", get_subsectors_by_sector),
    path("get_depts/<int:subsector_id>/", get_depts_by_subsector),
    path("get_subdepts/<int:dept_id>/", get_subdepts_by_dept),
    path("get_types/<int:subdept_id>/", get_types_by_subdept),
    path("get_brands/<int:type_id>/", get_brands_by_type),
    path("get_postmodels/<int:brand_id>/", get_postmodels_by_brand),
    path("get_sampradays/<int:religion_id>/", get_sampradays_by_religion),
    path("get_panths/<int:sampraday_id>/", get_panths_by_sampraday),
    path("get_varnas/<int:panth_id>/", get_varnas_by_panth),
    path("get_castes/<int:varna_id>/", get_castes_by_varna),
    path("get_subcastes/<int:caste_id>/", get_subcastes_by_caste),
    path("get_gotras/<int:subcaste_id>/", get_gotras_by_subcaste),
    path("get_subgotras/<int:gotra_id>/", get_subgotras_by_gotra),
    path("get_pidhis/<int:subgotra_id>/", get_pidhis_by_subgotra),
]
