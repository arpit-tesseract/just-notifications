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
]
