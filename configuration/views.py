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

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
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
            df = pd.read_excel(file, dtype={'Code': str})
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
                defaults={"name": name, "code": code}
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
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'Country', 'Code', or 'Continent Code'")
                continue

            try:
                continent = Continent.objects.get(code__iexact=continent_code)
                obj, is_created = Country.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    continent=continent,
                    defaults={"name": name, "code": code, "continent": continent}
                )
                if is_created:
                    created += 1
            except Continent.DoesNotExist:
                errors.append(f"Row {row_num}: Continent with code '{continent_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportStates(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'State', 'Code', or 'Country Code'")
                continue

            try:
                country = Country.objects.get(code__iexact=country_code)
                obj, is_created = State.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    country=country,
                    defaults={"name": name, "code": code, "country": country}
                )
                if is_created:
                    created += 1
            except Country.DoesNotExist:
                errors.append(f"Row {row_num}: Country with code '{country_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportDistricts(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'District', 'Code', or 'State Code'")
                continue

            try:
                state = State.objects.get(code__iexact=state_code)
                obj, is_created = District.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    state=state,
                    defaults={"name": name, "code": code, "state": state}
                )
                if is_created:
                    created += 1
            except State.DoesNotExist:
                errors.append(f"Row {row_num}: State with code '{state_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportCities(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'City', 'Code', or 'District Code'")
                continue

            try:
                district = District.objects.get(code__iexact=district_code)
                obj, is_created = City.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    district=district,
                    defaults={"name": name, "code": code, "district": district}
                )
                if is_created:
                    created += 1
            except District.DoesNotExist:
                errors.append(f"Row {row_num}: District with code '{district_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportVillages(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'Village', 'Code', or 'District Code'")
                continue

            try:
                district = District.objects.get(code__iexact=district_code)
                city = None
                if city_code:
                    try:
                        city = City.objects.get(code__iexact=city_code)
                    except City.DoesNotExist:
                        errors.append(f"Row {row_num}: City with code '{city_code}' not found")

                village_defaults = {"name": name, "code": code, "district": district}
                if city:
                    village_defaults["city"] = city

                obj, is_created = Village.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    district=district,
                    defaults=village_defaults
                )
                if is_created:
                    created += 1
            except District.DoesNotExist:
                errors.append(f"Row {row_num}: District with code '{district_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportReligions(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded."}, status=400)
        
        try:
            df = pd.read_excel(file, dtype={'Code': str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)
        
        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            name = clean(row.get('Religion'))
            code = clean(row.get('Code'))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Religion' or 'Code'")
                continue

            obj, is_created = Religion.objects.get_or_create(
                name__iexact=name,
                code__iexact=code,
                defaults={"name": name, "code": code}
            )
            if is_created:
                created+= 1

        return Response({"created": created, "errors": errors})

class ImportSampradays(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'Sampraday', 'Code', or 'Religion Code'")
                continue

            try:
                religion = Religion.objects.get(code__iexact=religion_code)
                obj, is_created = Sampraday.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    religion=religion,
                    defaults={"name": name, "code": code, "religion": religion}
                )
                if is_created:
                    created += 1
            except Religion.DoesNotExist:
                errors.append(f"Row {row_num}: Religion with code '{religion_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportPanths(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'Panth', 'Code', or 'Sampraday Code'")
                continue

            try:
                sampraday = Sampraday.objects.get(code__iexact=sampraday_code)
                obj, is_created = Panth.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    sampraday=sampraday,
                    defaults={"name": name, "code": code, "sampraday": sampraday}
                )
                if is_created:
                    created += 1
            except Sampraday.DoesNotExist:
                errors.append(f"Row {row_num}: Sampraday with code '{sampraday_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportVarnas(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded."}, status=400)
        
        try:
            df = pd.read_excel(file, dtype={'Code': str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)
        
        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            name = clean(row.get('Varna'))
            code = clean(row.get('Code'))

            if not name or not code:
                errors.append(f"Row {row_num}: Missing 'Varna' or 'Code'")
                continue

            obj, is_created = Varna.objects.get_or_create(
                name__iexact=name,
                code__iexact=code,
                defaults={"name": name, "code": code}
            )
            if is_created:
                created+= 1

        return Response({"created": created, "errors": errors})

class ImportCastes(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'Caste', 'Code', or 'Varna Code'")
                continue

            try:
                varna = Varna.objects.get(code__iexact=varna_code)
                obj, is_created = Caste.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    varna=varna,
                    defaults={"name": name, "code": code, "varna": varna}
                )
                if is_created:
                    created += 1
            except Varna.DoesNotExist:
                errors.append(f"Row {row_num}: Varna with code '{varna_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportSubCastes(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'SubCaste', 'Code', or 'Caste Code'")
                continue

            try:
                caste = Caste.objects.get(code__iexact=caste_code)
                obj, is_created = SubCaste.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    caste=caste,
                    defaults={"name": name, "code": code, "caste": caste}
                )
                if is_created:
                    created += 1
            except Caste.DoesNotExist:
                errors.append(f"Row {row_num}: Caste with code '{caste_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportGotras(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
        except Exception as e:
            return Response({"error": f"Invalid file format: {str(e)}"}, status=400)

        created = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = idx + 2
            caste_code = clean(row.get("Caste Code"))
            name = clean(row.get("Gotra"))
            code = clean(row.get("Code"))

            if not name or not code or not caste_code:
                errors.append(f"Row {row_num}: Missing 'Gotra', 'Code', or 'Caste Code'")
                continue

            try:
                caste = Caste.objects.get(code__iexact=caste_code)
                obj, is_created = Gotra.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    caste=caste,
                    defaults={"name": name, "code": code, "caste": caste}
                )
                if is_created:
                    created += 1
            except Caste.DoesNotExist:
                errors.append(f"Row {row_num}: Caste with code '{caste_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportSubGotras(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'SubGotra', 'Code', or 'Gotra Code'")
                continue

            try:
                gotra = Gotra.objects.get(code__iexact=gotra_code)
                obj, is_created = SubGotra.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    gotra=gotra,
                    defaults={"name": name, "code": code, "gotra": gotra}
                )
                if is_created:
                    created += 1
            except Gotra.DoesNotExist:
                errors.append(f"Row {row_num}: Gotra with code '{gotra_code}' not found")

        return Response({"created": created, "errors": errors})

class ImportPidhis(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [AllowAny]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        try:
            df = pd.read_excel(file, dtype={'Code': str})
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
                errors.append(f"Row {row_num}: Missing 'Pidhi', 'Code', or 'SubGotra Code'")
                continue

            try:
                subgotra = SubGotra.objects.get(code__iexact=subgotra_code)
                obj, is_created = Pidhi.objects.get_or_create(
                    name__iexact=name,
                    code__iexact=code,
                    subgotra=subgotra,
                    defaults={"name": name, "code": code, "subgotra": subgotra}
                )
                if is_created:
                    created += 1
            except SubGotra.DoesNotExist:
                errors.append(f"Row {row_num}: SubGotra with code '{subgotra_code}' not found")

        return Response({"created": created, "errors": errors})
