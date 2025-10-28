import datetime
from django.core.management.base import BaseCommand
from configuration.models import (
    Section, Class, ProfCategory, ProfSubCategory,
    Sector, SubSector, Department, SubDepartment,
    Type, Brand, PostModel
)

class Command(BaseCommand):
    help = 'Seeds example professional hierarchical data (Section → Class → ... → PostModel) into the database.'

    def handle(self, *args, **options):
        # --- Constants ---
        FUTURE_HOLD_DATE = datetime.date(2026, 6, 15)  # For on_hold = True
        PAST_HOLD_DATE = datetime.date(2024, 1, 1)     # For on_hold = False

        # --- Helper Function to Create or Update ---
        def create_or_update(Model, code, **kwargs):
            obj, created = Model.objects.update_or_create(
                code=code,
                defaults=kwargs
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} {Model.__name__}: {str(obj)}")
            return obj

        self.stdout.write("Starting professional hierarchy seeding...")

        # 1. Section
        self.stdout.write("\n--- 1. Section ---")
        section_eng = create_or_update(
            Section, code="SEC01", name="Engineering", is_hidden=False, hold_date=None
        )
        section_med = create_or_update(
            Section, code="SEC02", name="Medical", is_hidden=True, hold_date=FUTURE_HOLD_DATE
        )

        # 2. Class
        self.stdout.write("\n--- 2. Class ---")
        class_mech = create_or_update(
            Class, code="CLS01", section=section_eng, name="Mechanical", is_hidden=False, hold_date=None
        )
        class_civil = create_or_update(
            Class, code="CLS02", section=section_eng, name="Civil", is_hidden=False, hold_date=PAST_HOLD_DATE
        )

        # 3. ProfCategory
        self.stdout.write("\n--- 3. ProfCategory ---")
        category_prod = create_or_update(
            ProfCategory, code="CAT01", profclass=class_mech, name="Production", is_hidden=False, hold_date=None
        )
        category_design = create_or_update(
            ProfCategory, code="CAT02", profclass=class_mech, name="Design", is_hidden=False, hold_date=None
        )

        # 4. ProfSubCategory
        self.stdout.write("\n--- 4. ProfSubCategory ---")
        subcat_auto = create_or_update(
            ProfSubCategory, code="SCA01", category=category_prod, name="Automobile", is_hidden=False, hold_date=None
        )
        subcat_aero = create_or_update(
            ProfSubCategory, code="SCA02", category=category_design, name="Aerospace", is_hidden=False, hold_date=None
        )

        # 5. Sector
        self.stdout.write("\n--- 5. Sector ---")
        sector_vehicle = create_or_update(
            Sector, code="SEC10", subcategory=subcat_auto, name="Vehicle Manufacturing", is_hidden=False, hold_date=None
        )
        sector_tools = create_or_update(
            Sector, code="SEC11", subcategory=subcat_aero, name="Tool Production", is_hidden=False, hold_date=None
        )

        # 6. SubSector
        self.stdout.write("\n--- 6. SubSector ---")
        subsector_cars = create_or_update(
            SubSector, code="SSC01", sector=sector_vehicle, name="Car Assembly", is_hidden=False, hold_date=None
        )
        subsector_planes = create_or_update(
            SubSector, code="SSC02", sector=sector_tools, name="Aircraft Components", is_hidden=False, hold_date=None
        )

        # 7. Department
        self.stdout.write("\n--- 7. Department ---")
        dept_design = create_or_update(
            Department, code="DEP01", subsector=subsector_cars, name="Design Department", is_hidden=False, hold_date=None
        )
        dept_prod = create_or_update(
            Department, code="DEP02", subsector=subsector_planes, name="Production Department", is_hidden=False, hold_date=None
        )

        # 8. SubDepartment
        self.stdout.write("\n--- 8. SubDepartment ---")
        subdept_cad = create_or_update(
            SubDepartment, code="SDE01", department=dept_design, name="CAD", is_hidden=False, hold_date=None
        )
        subdept_qc = create_or_update(
            SubDepartment, code="SDE02", department=dept_prod, name="Quality Control", is_hidden=False, hold_date=None
        )

        # 9. Type
        self.stdout.write("\n--- 9. Type ---")
        type_electric = create_or_update(
            Type, code="TYP01", subdepartment=subdept_cad, name="Electric Type", is_hidden=False, hold_date=None
        )
        type_petrol = create_or_update(
            Type, code="TYP02", subdepartment=subdept_qc, name="Petrol Type", is_hidden=False, hold_date=None
        )

        # 10. Brand
        self.stdout.write("\n--- 10. Brand ---")
        brand_tesla = create_or_update(
            Brand, code="BRD01", type=type_electric, name="Tesla", is_hidden=False, hold_date=None
        )
        brand_bmw = create_or_update(
            Brand, code="BRD02", type=type_petrol, name="BMW", is_hidden=False, hold_date=None
        )

        # 11. PostModel
        self.stdout.write("\n--- 11. PostModel ---")
        post_model_y = create_or_update(
            PostModel, code="PM01", brand=brand_tesla, name="Model Y", is_hidden=False, hold_date=None
        )
        post_model_i8 = create_or_update(
            PostModel, code="PM02", brand=brand_bmw, name="i8", is_hidden=False, hold_date=None
        )

        self.stdout.write(self.style.SUCCESS("\nSuccessfully seeded professional hierarchy data!"))
