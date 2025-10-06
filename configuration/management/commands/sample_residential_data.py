import datetime
from django.core.management.base import BaseCommand
from configuration.models import (
    Glob, Continent, Country, State, District, Taluka, CityVillage, Ward
)
# NOTE: Replace 'your_app_name' with your actual Django app name.

class Command(BaseCommand):
    help = 'Seeds initial hierarchical geopolitical data (Glob -> Continent -> Country -> ...) into the database.'

    def handle(self, *args, **options):
        # --- Constants (Current date is 2025-10-01) ---
        FUTURE_HOLD_DATE = datetime.date(2026, 6, 15) # For on_hold = True
        PAST_HOLD_DATE = datetime.date(2024, 1, 1)    # For on_hold = False (due to save logic)
        
        # --- Helper Function to Create/Update ---
        def create_or_update(Model, code, **kwargs):
            # Use 'code' for checking existence, as it's guaranteed unique across all records of a model.
            obj, created = Model.objects.update_or_create(
                code=code,
                defaults=kwargs
            )
            action = "Created" if created else "Updated"
            # Use __str__ for detailed output
            self.stdout.write(f"  {action} {Model.__name__}: {str(obj)}")
            return obj

        self.stdout.write("Starting location data seeding (will create new data or update if 'code' exists)...")

        # 1. Glob (e.g., Earth)
        self.stdout.write("\n--- 1. Glob ---")
        glob_earth = create_or_update(
            Glob, code="GLB01", name="Earth", is_hidden=False, hold_date=None
        )
        glob_mars = create_or_update(
            Glob, code="GLB02", name="Mars", is_hidden=True, hold_date=FUTURE_HOLD_DATE
        ) # on_hold will be True

        # 2. Continent
        self.stdout.write("\n--- 2. Continent ---")
        continent_asia = create_or_update(
            Continent, code="AST01", glob=glob_earth, name="Asia", is_hidden=False, hold_date=None
        )
        continent_na = create_or_update(
            Continent, code="NAM02", glob=glob_earth, name="North America", is_hidden=False, hold_date=PAST_HOLD_DATE
        ) # on_hold will be False

        # 3. Country
        self.stdout.write("\n--- 3. Country ---")
        country_india = create_or_update(
            Country, code="IND01", continent=continent_asia, name="India", is_hidden=False, hold_date=FUTURE_HOLD_DATE
        ) # on_hold will be True
        country_usa = create_or_update(
            Country, code="USA02", continent=continent_na, name="United States", is_hidden=False, hold_date=None
        )

        # 4. State
        self.stdout.write("\n--- 4. State ---")
        state_gujarat = create_or_update(
            State, code="GUJ01", country=country_india, name="Gujarat", is_hidden=False, hold_date=None
        )
        state_california = create_or_update(
            State, code="CAL02", country=country_usa, name="California", is_hidden=False, hold_date=None
        )

        # 5. District
        self.stdout.write("\n--- 5. District ---")
        district_surat = create_or_update(
            District, code="SRT01", state=state_gujarat, name="Surat", is_hidden=False, hold_date=None
        )
        district_ahmedabad = create_or_update(
            District, code="AHD02", state=state_gujarat, name="Ahmedabad", is_hidden=False, hold_date=PAST_HOLD_DATE
        ) # on_hold will be False

        # 6. Taluka (Sub-division of District)
        self.stdout.write("\n--- 6. Taluka ---")
        taluka_choryasi = create_or_update(
            Taluka, code="CHR01", district=district_surat, name="Choryasi", is_hidden=False, hold_date=None
        )
        taluka_olpad = create_or_update(
            Taluka, code="OLP02", district=district_surat, name="Olpad", is_hidden=False, hold_date=None
        )

        # 7. CityVillage (City, also under District)
        self.stdout.write("\n--- 7. CityVillage ---")
        city_surat = create_or_update(
            CityVillage, code="CTY01", taluka=taluka_choryasi, name="Surat City", is_hidden=False, hold_date=FUTURE_HOLD_DATE
        ) # on_hold will be True
        city_baroda = create_or_update(
            CityVillage, code="CTY02", taluka=taluka_olpad, name="Baroda Village", is_hidden=False, hold_date=None
        )

        # 8. Ward
        self.stdout.write("\n--- 8. Ward ---")
        ward_katargam = create_or_update(
            Ward, code="W0001", city_village=city_surat, name="Katargam Ward", is_hidden=False, hold_date=None
        )
        ward_varachha = create_or_update(
            Ward, code="W0002", city_village=city_surat, name="Varachha Ward", is_hidden=False, hold_date=None
        )

        self.stdout.write(self.style.SUCCESS('\nSuccessfully seeded hierarchical location data! 🗺️'))