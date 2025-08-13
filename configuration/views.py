from django.shortcuts import render
import pandas as pd
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import *
from .serializers import *

# ==================
# CRUD Views
# ==================


class ContinentViewSet(viewsets.ModelViewSet):
    queryset = Continent.objects.all()
    serializer_class = ContinentSerializer
    permission_classes = [IsAuthenticated]


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]


class StateViewSet(viewsets.ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [AllowAny]


class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [AllowAny]


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]


class VillageViewSet(viewsets.ModelViewSet):
    queryset = Village.objects.all()
    serializer_class = VillageSerializer
    permission_classes = [AllowAny]


class WardViewSet(viewsets.ModelViewSet):
    queryset = Ward.objects.all()
    serializer_class = WardSerializer
    permission_classes = [AllowAny]


class SocietyViewSet(viewsets.ModelViewSet):
    queryset = Society.objects.all()
    serializer_class = SocietySerializer
    permission_classes = [AllowAny]


class BlockViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    permission_classes = [AllowAny]


class HousesViewSet(viewsets.ModelViewSet):
    queryset = Houses.objects.all()
    serializer_class = HousesSerializer
    permission_classes = [AllowAny]


class AccessesViewSet(viewsets.ModelViewSet):
    queryset = Accesses.objects.all()
    serializer_class = AccessesSerializer
    permission_classes = [AllowAny]


class ReligionViewSet(viewsets.ModelViewSet):
    queryset = Religion.objects.all()
    serializer_class = ReligionSerializer
    permission_classes = [AllowAny]


class SampradayViewSet(viewsets.ModelViewSet):
    queryset = Sampraday.objects.all()
    serializer_class = SampradaySerializer
    permission_classes = [AllowAny]


class PanthViewSet(viewsets.ModelViewSet):
    queryset = Panth.objects.all()
    serializer_class = PanthSerializer
    permission_classes = [AllowAny]


class VarnaViewSet(viewsets.ModelViewSet):
    queryset = Varna.objects.all()
    serializer_class = VarnaSerializer
    permission_classes = [AllowAny]


class CasteViewSet(viewsets.ModelViewSet):
    queryset = Caste.objects.all()
    serializer_class = CasteSerializer
    permission_classes = [AllowAny]


class SubCasteViewSet(viewsets.ModelViewSet):
    queryset = SubCaste.objects.all()
    serializer_class = SubCasteSerializer
    permission_classes = [AllowAny]


class GotraViewSet(viewsets.ModelViewSet):
    queryset = Gotra.objects.all()
    serializer_class = GotraSerializer
    permission_classes = [AllowAny]


class SubGotraViewSet(viewsets.ModelViewSet):
    queryset = SubGotra.objects.all()
    serializer_class = SubGotraSerializer
    permission_classes = [AllowAny]


class PidhiViewSet(viewsets.ModelViewSet):
    queryset = Pidhi.objects.all()
    serializer_class = PidhiSerializer
    permission_classes = [AllowAny]


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [AllowAny]


class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [AllowAny]


class ProfCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProfCategory.objects.all()
    serializer_class = ProfCategorySerializer
    permission_classes = [AllowAny]


class ProfSubCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProfSubCategory.objects.all()
    serializer_class = ProfSubCategorySerializer
    permission_classes = [AllowAny]


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [AllowAny]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]


class PostModelViewSet(viewsets.ModelViewSet):
    queryset = PostModel.objects.all()
    serializer_class = PostModelSerializer
    permission_classes = [AllowAny]


class SectorViewSet(viewsets.ModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [AllowAny]


class SubSectorViewSet(viewsets.ModelViewSet):
    queryset = SubSector.objects.all()
    serializer_class = SubSectorSerializer
    permission_classes = [AllowAny]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]


class SubDepartmentViewSet(viewsets.ModelViewSet):
    queryset = SubDepartment.objects.all()
    serializer_class = SubDepartmentSerializer
    permission_classes = [AllowAny]


class RoomFlashViewSet(viewsets.ModelViewSet):
    queryset = RoomFlash.objects.all()
    serializer_class = RoomFlashSerializer
    permission_classes = [AllowAny]


# ==================
# Import Features
# ==================


def clean(value):
    return str(value).strip() if pd.notnull(value) else None


class ImportContinents(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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


class ImportCities(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            district_code = clean(row.get("District Code"))
            name = clean(row.get("City"))
            code = clean(row.get("Code"))

            if not name or not code or not district_code:
                errors.append(
                    f"Row {row_num}: Missing 'City', 'Code', or 'District Code'"
                )
                continue

            try:
                district = District.objects.get(code__iexact=district_code)
                obj, is_created = City.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    district=district,
                    defaults={"name": name, "code": code, "district": district},
                )
                if is_created:
                    created += 1
            except District.DoesNotExist:
                errors.append(
                    f"Row {row_num}: District with code '{district_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportVillages(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            district_code = clean(row.get("District Code"))
            name = clean(row.get("Village"))
            code = clean(row.get("Code"))
            city_code = clean(row.get("City Code"))

            if not name or not code or not district_code:
                errors.append(
                    f"Row {row_num}: Missing 'Village', 'Code', or 'District Code'"
                )
                continue

            try:
                district = District.objects.get(code__iexact=district_code)
                city = None
                if city_code:
                    try:
                        city = City.objects.get(code__iexact=city_code)
                    except City.DoesNotExist:
                        errors.append(
                            f"Row {row_num}: City with code '{city_code}' not found"
                        )

                village_defaults = {"name": name, "code": code, "district": district}
                if city:
                    village_defaults["city"] = city

                obj, is_created = Village.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    district=district,
                    defaults=village_defaults,
                )
                if is_created:
                    created += 1
            except District.DoesNotExist:
                errors.append(
                    f"Row {row_num}: District with code '{district_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportWards(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            village_code = clean(row.get("Village Code"))
            name = clean(row.get("Ward"))
            code = clean(row.get("Code"))

            if not name or not code or not village_code:
                errors.append(
                    f"Row {row_num}: Missing 'Ward', 'Code', or 'Village Code'"
                )
                continue

            try:
                village = Village.objects.get(code__iexact=village_code)

                obj, is_created = Ward.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    village=village,
                    defaults={"name": name, "code": code, "village": village},
                )
                if is_created:
                    created += 1
            except Village.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Village with code '{village_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportSocities(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            ward_code = clean(row.get("Ward Code"))
            name = clean(row.get("Society"))
            code = clean(row.get("Code"))

            if not name or not code or not ward_code:
                errors.append(
                    f"Row {row_num}: Missing 'Society', 'Code', or 'Ward Code'"
                )
                continue

            try:
                ward = Ward.objects.get(code__iexact=ward_code)

                obj, is_created = Society.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    ward=ward,
                    defaults={"name": name, "code": code, "ward": ward},
                )
                if is_created:
                    created += 1
            except Ward.DoesNotExist:
                errors.append(f"Row {row_num}: Ward with code '{ward_code}' not found")

        return Response({"created": created, "errors": errors})


class ImportBlocks(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            society_code = clean(row.get("Society Code"))
            name = clean(row.get("Block"))

            if not name or not society_code:
                errors.append(f"Row {row_num}: Missing 'Block' or 'Society Code'")
                continue

            try:
                society = Society.objects.get(code__iexact=society_code)

                obj, is_created = Block.objects.get_or_create(
                    name__iexact=name,
                    society=society,
                    defaults={"name": name, "society": society},
                )
                if is_created:
                    created += 1
            except Society.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Society with code '{society_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportHouses(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            block = clean(row.get("Block"))
            code = clean(row.get("Number of Flats/Houses"))

            if not code or not block:
                errors.append(
                    f"Row {row_num}: Missing 'Block' or 'Number of Flats/Houses'"
                )
                continue

            try:
                block = Block.objects.get(name__iexact=block)

                obj, is_created = Houses.objects.get_or_create(
                    code__iexact=code,
                    block=block,
                    defaults={"code": code, "block": block},
                )
                if is_created:
                    created += 1
            except Block.DoesNotExist:
                errors.append(f"Row {row_num}: '{block}' not found")

        return Response({"created": created, "errors": errors})


class ImportReligions(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            panth_code = clean(row.get("Panth Code"))
            name = clean(row.get("Varna"))
            code = clean(row.get("Code"))

            if not name or not code or not panth_code:
                errors.append(
                    f"Row {row_num}: Missing 'Varna' or 'Code' or 'Panth Code'"
                )
                continue

            try:
                panth = Panth.objects.get(code__iexact=panth_code)
                obj, is_created = Varna.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    panth=panth,
                    defaults={"name": name, "code": code, "panth": panth},
                )
                if is_created:
                    created += 1
            except Panth.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Panth with code '{panth_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportCastes(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
                errors.append(
                    f"Row {row_num}: Missing 'Gotra', 'Code', or 'SubCaste Code'"
                )
                continue

            try:
                subcaste = SubCaste.objects.get(code__iexact=subcaste_code)
                obj, is_created = Gotra.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    subcaste=subcaste,
                    defaults={"name": name, "code": code, "subcaste": subcaste},
                )
                if is_created:
                    created += 1
            except Caste.DoesNotExist:
                errors.append(
                    f"Row {row_num}: SubCaste with code '{subcaste_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportSubGotras(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
                errors.append(
                    f"Row {row_num}: Category with code '{category_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportSector(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            subcategory_code = clean(row.get("SubCategory Code"))
            name = clean(row.get("Sector"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Sector' or 'Code' or 'SubCategory Code'"
                )
                continue

            try:
                subcategory = ProfSubCategory.objects.get(code__iexact=subcategory_code)

                obj, is_created = Sector.objects.get_or_create(
                    subcategory=subcategory,
                    name__iexact=name,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "subcategory": subcategory},
                )
                if is_created:
                    created += 1
            except ProfSubCategory.DoesNotExist:
                errors.append(
                    f"Row {row_num}: SubCategory with code '{subcategory_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportSubSector(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            sector_code = clean(row.get("Sector Code"))
            name = clean(row.get("Sub Sector"))
            code = clean(row.get("Code"))

            if not sector_code or not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Sector Code', 'Sub Sector' or 'Code'"
                )
                continue

            try:
                sector = Sector.objects.get(code__iexact=sector_code)
                obj, is_created = SubSector.objects.get_or_create(
                    name__iexact=name,
                    sector=sector,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "sector": sector},
                )
                if is_created:
                    created += 1

            except Sector.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Sector with code '{sector_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportDepartment(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            subsector_code = clean(row.get("SubSector Code"))
            name = clean(row.get("Department"))
            code = clean(row.get("Code"))

            if not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Department' or 'Code' or 'SubSector Code'"
                )
                continue

            try:
                subsector = SubSector.objects.get(code__iexact=subsector_code)
                obj, is_created = Department.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    subsector=subsector,
                    defaults={"name": name, "code": code, "subsector": subsector},
                )
                if is_created:
                    created += 1
            except SubSector.DoesNotExist:
                errors.append(
                    f"Row {row_num}: SubSector with code '{subsector_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportSubDepartment(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            department_code = clean(row.get("Department Code"))
            name = clean(row.get("Sub Department"))
            code = clean(row.get("Code"))

            if not department_code or not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Department Code', 'Sub Department' or 'Code'"
                )
                continue

            try:
                department = Department.objects.get(code__iexact=department_code)
                obj, is_created = SubDepartment.objects.get_or_create(
                    name__iexact=name,
                    department=department,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "department": department},
                )
                if is_created:
                    created += 1

            except Department.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Department with code '{department_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportType(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            subdepartment_code = clean(row.get("SubDepartment Code"))
            name = clean(row.get("Type"))
            code = clean(row.get("Code"))

            if not subdepartment_code or not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'SubDepartment Code', 'Type' or 'Code'"
                )
                continue

            try:
                subdepartment = SubDepartment.objects.get(
                    code__iexact=subdepartment_code
                )
                obj, is_created = Type.objects.get_or_create(
                    name__iexact=name,
                    subdepartment=subdepartment,
                    code__iexact=code,
                    defaults={
                        "name": name,
                        "code": code,
                        "subdepartment": subdepartment,
                    },
                )
                if is_created:
                    created += 1

            except SubDepartment.DoesNotExist:
                errors.append(
                    f"Row {row_num}: SubDepartment with code '{subdepartment_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportBrand(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            type_code = clean(row.get("Type Code"))
            name = clean(row.get("Brand"))
            code = clean(row.get("Code"))

            if not type_code or not name or not code:
                errors.append(f"Row {row_num}: Missing 'Type Code', 'Brand' or 'Code'")
                continue

            try:
                type = Type.objects.get(code__iexact=type_code)
                obj, is_created = Brand.objects.get_or_create(
                    name__iexact=name,
                    type=type,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "type": type},
                )
                if is_created:
                    created += 1

            except Type.DoesNotExist:
                errors.append(f"Row {row_num}: Type with code '{type_code}' not found")

        return Response({"created": created, "errors": errors})


class ImportPostModel(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

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
            brand_code = clean(row.get("Brand Code"))
            name = clean(row.get("Post Model"))
            code = clean(row.get("Code"))

            if not brand_code or not name or not code:
                errors.append(
                    f"Row {row_num}: Missing 'Brand Code', 'Post Model' or 'Code'"
                )
                continue

            try:
                brand = Brand.objects.get(code__iexact=brand_code)
                obj, is_created = PostModel.objects.get_or_create(
                    name__iexact=name,
                    brand=brand,
                    code__iexact=code,
                    defaults={"name": name, "code": code, "brand": brand},
                )
                if is_created:
                    created += 1

            except Brand.DoesNotExist:
                errors.append(
                    f"Row {row_num}: Brand with code '{brand_code}' not found"
                )

        return Response({"created": created, "errors": errors})


class ImportRoomFlash(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)
        try:
            df = pd.read_excel(file, dtype={"Code": str})
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
                defaults={"name": name, "code": code},
            )
            if is_created:
                created += 1

        return Response({"created": created, "errors": errors})
