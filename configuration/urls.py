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
    # path("import/city/", ImportCities.as_view()),
    # path("import/village/", ImportVillages.as_view()),
    # path("import/ward/", ImportWards.as_view()),
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
    path("get_continents/<int:glob_id>/", ContinentsByGlobView.as_view(), name="get_continents_by_glob"),
    path("get_countries/<int:continent_id>/", CountriesByContinentView.as_view(), name="get_countries_by_continent"),
    path("get_states/<int:country_id>/", StatesByCountryView.as_view(), name="get_states_by_country"),
    path("get_districts/<int:state_id>/", DistrictsByStateView.as_view(), name="get_districts_by_state"),
    path("get_taluka/<int:district_id>/", TalukaByDistrictView.as_view(), name="get_taluka_by_district"),
    path("get_city_villages/<int:taluka_id>/", CityVillagesByTalukaView.as_view(), name="get_city_village_by_taluka"),
    path("get_wards/<int:cityvillage_id>/", WardsByCityVillageView.as_view(), name="get_wards_by_cityvillage"),
    path("get_societies/<int:ward_id>/", SocietiesByWardView.as_view(), name="get_societies_by_ward"),
    path("get_blocks/<int:society_id>/", BlockBySocietyView.as_view(), name="get_blocks_by_society"),
    path("get_floors/<int:block_id>/", FloorsByBlockView.as_view(), name="get_floors_by_block"),
    path("get_houses/<int:floor_id>/", HousesByFloorView.as_view(), name="get_houses_by_floor"),
    path("get_classes/<int:section_id>/", ClassesBySectionView.as_view(), name="get_classes_by_section"),
    path("get_categories/<int:class_id>/", ProfCategoryByClassView.as_view(), name="get_categories_by_class"),
    path("get_subcategories/<int:category_id>/", ProfSubCategoryByCategoryView.as_view(), name="get_subcategories_by_category"),
    path("get_sectors/<int:subcategory_id>/", SectorBySubCategoryView.as_view(), name="get_sectors_by_subcategory"),
    path("get_subsectors/<int:sector_id>/", SubSectorBySectorView.as_view(), name="get_subsectors_by_sector"),
    path("get_depts/<int:subsector_id>/", DepartmentsBySubSectorView.as_view(), name="get_depts_by_subsector"),
    path("get_subdepts/<int:dept_id>/", SubDepartmentsByDepartmentView.as_view(), name="get_subdepts_by_dept"),
    path("get_types/<int:subdept_id>/", TypeBySubDepartmentView.as_view(), name="get_types_by_subdept"),
    path("get_brands/<int:type_id>/", BrandByTypeView.as_view(), name="get_brands_by_type"),
    path("get_postmodels/<int:brand_id>/", PostModelByBrandView.as_view(), name="get_postmodels_by_brand"),
    
    path("get_sampradays/<int:religion_id>/", SampradayByReligionView.as_view(), name="get_sampradays_by_religion"),
    path("get_panths/<int:sampraday_id>/", PanthBySampradayView.as_view(), name="get_panths_by_sampraday"),
    path("get_varnas/<int:panth_id>/", VarnaByPanthView.as_view(), name="get_varnas_by_panth"),
    path("get_castes/<int:varna_id>/", CasteByVarnaView.as_view(), name="get_castes_by_varna"),
    path("get_subcastes/<int:caste_id>/", SubCasteByCasteView.as_view(), name="get_subcastes_by_caste"),
    path("get_gotras/<int:subcaste_id>/", GotraBySubCasteView.as_view(), name="get_gotras_by_subcaste"),
    path("get_subgotras/<int:gotra_id>/", SubGotraByGotraView.as_view(), name="get_subgotras_by_gotra"),
    path("get_kul/<int:subgotra_id>/", KulBySubGotraView.as_view(), name="get_kuls_by_subgotra"),
    path("get_vansh/<int:kul_id>/", VanshByKulView.as_view(), name="get_vansh_by_kul"),
    path("get_family/<int:vansh_id>/", FamilyByVanshView.as_view(), name="get_family_by_vansh"),
    path("get_pidhis/<int:family_id>/", PidhiByFamilyView.as_view(), name="get_pidhis_by_family"),
    
    path("models/", ModelNameView.as_view(), name="get_models"),
    path("model_access_rules/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    path("model_access_rules/<int:user_id>/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    
]
