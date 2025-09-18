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
router.register(r'societies_in_details', SocietyViewSet)
router.register(r'blocks_in_details', BlockViewSet)
router.register(r'floors_in_details', FloorViewSet)
router.register(r'housenums_in_details', HousesViewSet)

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
    path('globs/', GlobListView.as_view()),
    path('continents/', ContinentListView.as_view()),
    path('countries/', CountryListView.as_view()),
    path('states/', StateListView.as_view()),
    path('districts/', DistrictListView.as_view()),
    path('talukas/', TalukaListView.as_view()),
    path('cityvillages/', CityVillageListView.as_view()),
    path('wards/', WardListView.as_view()),
    path('societies/', SocietyListView.as_view()),
    path('blocks/', BlockListView.as_view()),
    path('floors/', FloorListView.as_view()),
    path('housenums/', HousesListView.as_view()),
    
    
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
    path("continents_by_glob/<int:glob_id>/", ContinentsByGlobView.as_view(), name="get_continents_by_glob"),
    path("countries_by_continent/<int:continent_id>/", CountriesByContinentView.as_view(), name="get_countries_by_continent"),
    path("states_by_country/<int:country_id>/", StatesByCountryView.as_view(), name="get_states_by_country"),
    path("districts_by_state/<int:state_id>/", DistrictsByStateView.as_view(), name="get_districts_by_state"),
    path("taluka_by_district/<int:district_id>/", TalukaByDistrictView.as_view(), name="get_taluka_by_district"),
    path("city_villages_by_taluka/<int:taluka_id>/", CityVillagesByTalukaView.as_view(), name="get_city_village_by_taluka"),
    path("wards_by_cityvillage/<int:cityvillage_id>/", WardsByCityVillageView.as_view(), name="get_wards_by_cityvillage"),
    path("societies_by_ward/<int:ward_id>/", SocietiesByWardView.as_view(), name="get_societies_by_ward"),
    path("blocks_by_society/<int:society_id>/", BlockBySocietyView.as_view(), name="get_blocks_by_society"),
    path("floors_by_block/<int:block_id>/", FloorsByBlockView.as_view(), name="get_floors_by_block"),
    path("houses_by_floor/<int:floor_id>/", HousesByFloorView.as_view(), name="get_houses_by_floor"),
    
    path("classes_by_section/<int:section_id>/", ClassesBySectionView.as_view(), name="get_classes_by_section"),
    path("categories_by_class/<int:class_id>/", ProfCategoryByClassView.as_view(), name="get_categories_by_class"),
    path("subcategories_by_category/<int:category_id>/", ProfSubCategoryByCategoryView.as_view(), name="get_subcategories_by_category"),
    path("sectors_by_subcategory/<int:subcategory_id>/", SectorBySubCategoryView.as_view(), name="get_sectors_by_subcategory"),
    path("subsectors_by_sector/<int:sector_id>/", SubSectorBySectorView.as_view(), name="get_subsectors_by_sector"),
    path("depts_by_subsector/<int:subsector_id>/", DepartmentsBySubSectorView.as_view(), name="get_depts_by_subsector"),
    path("subdepts_by_dept/<int:dept_id>/", SubDepartmentsByDepartmentView.as_view(), name="get_subdepts_by_dept"),
    path("types_by_subdept/<int:subdept_id>/", TypeBySubDepartmentView.as_view(), name="get_types_by_subdept"),
    path("brands_by_type/<int:type_id>/", BrandByTypeView.as_view(), name="get_brands_by_type"),
    path("postmodels_by_brand/<int:brand_id>/", PostModelByBrandView.as_view(), name="get_postmodels_by_brand"),
    
    path("sampradays_by_religion/<int:religion_id>/", SampradayByReligionView.as_view(), name="get_sampradays_by_religion"),
    path("panths_by_sampraday/<int:sampraday_id>/", PanthBySampradayView.as_view(), name="get_panths_by_sampraday"),
    path("varnas_by_panth/<int:panth_id>/", VarnaByPanthView.as_view(), name="get_varnas_by_panth"),
    path("castes_by_varna/<int:varna_id>/", CasteByVarnaView.as_view(), name="get_castes_by_varna"),
    path("subcastes_by_caste/<int:caste_id>/", SubCasteByCasteView.as_view(), name="get_subcastes_by_caste"),
    path("gotras_by_subcaste/<int:subcaste_id>/", GotraBySubCasteView.as_view(), name="get_gotras_by_subcaste"),
    path("subgotras_by_gotra/<int:gotra_id>/", SubGotraByGotraView.as_view(), name="get_subgotras_by_gotra"),
    path("kul_by_subgotra/<int:subgotra_id>/", KulBySubGotraView.as_view(), name="get_kuls_by_subgotra"),
    path("vansh_by_kul/<int:kul_id>/", VanshByKulView.as_view(), name="get_vansh_by_kul"),
    path("family_by_vansh/<int:vansh_id>/", FamilyByVanshView.as_view(), name="get_family_by_vansh"),
    path("pidhis_by_family/<int:family_id>/", PidhiByFamilyView.as_view(), name="get_pidhis_by_family"),
    
    path("models/", ModelNameView.as_view(), name="get_models"),
    path("model_access_rules/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    path("model_access_rules/<int:user_id>/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    
]
