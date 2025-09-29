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
# router.register(r'societies_in_details', SocietyViewSet)
# router.register(r'blocks_in_details', BlockViewSet)
# router.register(r'floors_in_details', FloorViewSet)
# router.register(r'housenums_in_details', HousesViewSet)

# router.register(r'accessactivity', AccessesViewSet)
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
router.register(r'classes_in_details', ClassViewSet)
router.register(r'profCategories_in_details', ProfCategoryViewSet)
router.register(r'profSubCategories_in_details', ProfSubCategoryViewSet)
router.register(r'types_in_details', TypeViewSet)
router.register(r'brands_in_details', BrandViewSet)
router.register(r'postmodeles_in_details', PostModelViewSet)
router.register(r'sectors_in_details', SectorViewSet)
router.register(r'subsectors_in_details', SubSectorViewSet)
router.register(r'departments_in_details', DepartmentViewSet)
router.register(r'subdepartments_in_details', SubDepartmentViewSet)
router.register(r'roomflashes', RoomFlashViewSet)

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
    
    path('religions/', ReligionListView.as_view()),
    path('sampradays/', SampradayListView.as_view()),
    path('panths/', PanthListView.as_view()),
    path('varnas/', VarnaListView.as_view()),
    path('castes/', CasteListView.as_view()),
    path('subcastes/', SubCasteListView.as_view()),
    path('gotras/', GotraListView.as_view()),
    path('subgotras/', SubGotraListView.as_view()),
    path('kuls/', KulListView.as_view()),
    path('vanshes/', VanshListView.as_view()),
    path('families/', FamilyListView.as_view()),
    path('pidhis/', PidhiListView.as_view()),
    
    path('sections/', SectionListView.as_view()),
    path('classes/', ClassListView.as_view()),
    path('profCategories/', ProfCategoryListView.as_view()),
    path('profSubCategories/', ProfSubCategoryListView.as_view()),
    path('types/', TypeListView.as_view()),
    path('brands/', BrandListView.as_view()),
    path('postmodeles/', PostModelListView.as_view()),
    path('sectors/', SectorListView.as_view()),
    path('subsectors/', SubSectorListView.as_view()),
    path('departments/', DepartmentListView.as_view()),
    path('subdepartments/', SubDepartmentListView.as_view()),
    
    path("import/continent/", ImportContinents.as_view()),
    path("import/country/", ImportCountries.as_view()),
    path("import/state/", ImportStates.as_view()),
    path("import/district/", ImportDistricts.as_view()),
    # path("import/city/", ImportCities.as_view()),
    # path("import/village/", ImportVillages.as_view()),
    # path("import/ward/", ImportWards.as_view()),
    # path("import/society/", ImportSocities.as_view()),
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
    path("talukas_by_district/<int:district_id>/", TalukaByDistrictView.as_view(), name="get_taluka_by_district"),
    path("cityvillages_by_taluka/<int:taluka_id>/", CityVillagesByTalukaView.as_view(), name="get_city_village_by_taluka"),
    path("wards_by_cityvillage/<int:cityvillage_id>/", WardsByCityVillageView.as_view(), name="get_wards_by_cityvillage"),
    # path("societies_by_ward/<int:ward_id>/", SocietiesByWardView.as_view(), name="get_societies_by_ward"),

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
    path("kuls_by_subgotra/<int:subgotra_id>/", KulBySubGotraView.as_view(), name="get_kuls_by_subgotra"),
    path("vanshes_by_kul/<int:kul_id>/", VanshByKulView.as_view(), name="get_vansh_by_kul"),
    path("families_by_vansh/<int:vansh_id>/", FamilyByVanshView.as_view(), name="get_family_by_vansh"),
    path("pidhis_by_family/<int:family_id>/", PidhiByFamilyView.as_view(), name="get_pidhis_by_family"),
    
    path("models/", ModelNameView.as_view(), name="get_models"),
    path("model_access_rules/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    path("model_access_rules/<int:user_id>/", ModelAndAccessRulesView.as_view(), name="model_access_rules"),
    
]
