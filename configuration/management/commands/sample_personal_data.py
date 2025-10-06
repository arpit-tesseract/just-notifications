import datetime
from django.core.management.base import BaseCommand
from configuration.models import (
    Religion, Sampraday, Panth, Varna, Caste, SubCaste,
    Gotra, SubGotra, Kul, Vansh, Family, Pidhi
)
# NOTE: Replace 'your_app_name' with your actual Django app name.

class Command(BaseCommand):
    help = 'Seeds initial hierarchical religious, caste, and family data, updating if the code exists.'

    def handle(self, *args, **options):
        # --- Constants ---
        FUTURE_HOLD_DATE = datetime.date(2026, 1, 1)
        PAST_HOLD_DATE = datetime.date(2020, 1, 1)
        
        # --- Helper Function to Create/Update ---
        def create_or_update(Model, code, **kwargs):
            obj, created = Model.objects.update_or_create(
                code=code,
                defaults=kwargs
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} {Model.__name__}: {obj.name} (Code: {obj.code})")
            return obj

        self.stdout.write("Starting data seeding process (will create new data or update if 'code' exists)...")

        # 1. Religion
        self.stdout.write("\n--- 1. Religion ---")
        religion_hinduism = create_or_update(
            Religion, code="HIN01", name="Hinduism", is_hidden=False, hold_date=FUTURE_HOLD_DATE
        )
        religion_jainism = create_or_update(
            Religion, code="JAI02", name="Jainism", is_hidden=False, hold_date=None
        )
        religion_buddhism = create_or_update(
            Religion, code="BUD03", name="Buddhism", is_hidden=True, hold_date=PAST_HOLD_DATE
        )

        # 2. Sampraday
        self.stdout.write("\n--- 2. Sampraday ---")
        sampraday_shaivism = create_or_update(
            Sampraday, code="SHV01", religion=religion_hinduism, name="Shaivism", hold_date=None
        )
        sampraday_digambara = create_or_update(
            Sampraday, code="DIG02", religion=religion_jainism, name="Digambara", hold_date=FUTURE_HOLD_DATE
        )

        # 3. Panth
        self.stdout.write("\n--- 3. Panth ---")
        panth_nath = create_or_update(
            Panth, code="NTH01", sampraday=sampraday_shaivism, name="Nath Sampraday", hold_date=None
        )
        panth_taran = create_or_update(
            Panth, code="TRN02", sampraday=sampraday_digambara, name="Taran Panth", hold_date=PAST_HOLD_DATE
        )

        # 4. Varna
        self.stdout.write("\n--- 4. Varna ---")
        varna_brahmin = create_or_update(
            Varna, code="BRM01", panth=panth_nath, name="Brahmin", hold_date=None
        )

        # 5. Caste
        self.stdout.write("\n--- 5. Caste ---")
        caste_bhatt = create_or_update(
            Caste, code="BHT01", varna=varna_brahmin, name="Bhatt", hold_date=None
        )

        # 6. SubCaste
        self.stdout.write("\n--- 6. SubCaste ---")
        subcaste_shrimali = create_or_update(
            SubCaste, code="SHM01", caste=caste_bhatt, name="Shrimali", hold_date=None
        )

        # 7. Gotra
        self.stdout.write("\n--- 7. Gotra ---")
        gotra_kashyap = create_or_update(
            Gotra, code="KAS01", subcaste=subcaste_shrimali, name="Kashyap", hold_date=FUTURE_HOLD_DATE
        )

        # 8. SubGotra
        self.stdout.write("\n--- 8. SubGotra ---")
        subgotra_a = create_or_update(
            SubGotra, code="KSA01", gotra=gotra_kashyap, name="Kashyap-A", hold_date=None
        )

        # 9. Kul
        self.stdout.write("\n--- 9. Kul ---")
        kul_chauhan = create_or_update(
            Kul, code="CHU01", subgotra=subgotra_a, name="Chauhan", hold_date=None
        )

        # 10. Vansh
        self.stdout.write("\n--- 10. Vansh ---")
        vansh_surya = create_or_update(
            Vansh, code="SRV01", kul=kul_chauhan, name="Surya Vansh", hold_date=None
        )

        # 11. Family
        self.stdout.write("\n--- 11. Family ---")
        family_modi = create_or_update(
            Family, code="MOD01", vansh=vansh_surya, name="Modi", hold_date=FUTURE_HOLD_DATE
        )

        # 12. Pidhi
        self.stdout.write("\n--- 12. Pidhi ---")
        pidhi_gen1 = create_or_update(
            Pidhi, code="GEN01", family=family_modi, name="Generation 1", hold_date=None
        )

        self.stdout.write(self.style.SUCCESS('\nSuccessfully seeded data without deleting existing records! 🚀'))

# import datetime
# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from configuration.models import (
#     Religion, Sampraday, Panth, Varna, Caste, SubCaste,
#     Gotra, SubGotra, Kul, Vansh, Family, Pidhi
# )

# class Command(BaseCommand):
#     help = 'Seeds initial hierarchical religious, caste, and family data into the database.'

#     def handle(self, *args, **options):
#         # Define a future date for "on hold" demonstration
#         FUTURE_HOLD_DATE = datetime.date(2026, 1, 1) # Set to a date in the future
#         PAST_HOLD_DATE = datetime.date(2020, 1, 1) # Set to a date in the past
        
#         # Clear existing data to prevent unique constraint errors on 'code'
#         self.stdout.write("Clearing existing data...")
#         Pidhi.objects.all().delete()
#         Family.objects.all().delete()
#         Vansh.objects.all().delete()
#         Kul.objects.all().delete()
#         SubGotra.objects.all().delete()
#         Gotra.objects.all().delete()
#         SubCaste.objects.all().delete()
#         Caste.objects.all().delete()
#         Varna.objects.all().delete()
#         Panth.objects.all().delete()
#         Sampraday.objects.all().delete()
#         Religion.objects.all().delete()
#         self.stdout.write(self.style.SUCCESS("Existing data cleared."))

#         self.stdout.write("Starting data seeding process...")

#         # 1. Religion
#         religion_hinduism = Religion.objects.create(
#             name="Hinduism", code="HIN01", is_hidden=False, hold_date=FUTURE_HOLD_DATE
#         ) # on_hold will be True after save
#         religion_jainism = Religion.objects.create(
#             name="Jainism", code="JAI02", is_hidden=False
#         )
#         religion_buddhism = Religion.objects.create(
#             name="Buddhism", code="BUD03", is_hidden=True, hold_date=PAST_HOLD_DATE
#         ) # on_hold will be False after save
#         self.stdout.write(f"Created 3 Religion records.")

#         # 2. Sampraday
#         sampraday_shaivism = Sampraday.objects.create(
#             religion=religion_hinduism, name="Shaivism", code="SHV01"
#         )
#         sampraday_digambara = Sampraday.objects.create(
#             religion=religion_jainism, name="Digambara", code="DIG02", hold_date=FUTURE_HOLD_DATE
#         ) # on_hold will be True after save
#         self.stdout.write(f"Created 2 Sampraday records.")

#         # 3. Panth
#         panth_nath = Panth.objects.create(
#             sampraday=sampraday_shaivism, name="Nath Sampraday", code="NTH01"
#         )
#         panth_taran = Panth.objects.create(
#             sampraday=sampraday_digambara, name="Taran Panth", code="TRN02", hold_date=PAST_HOLD_DATE
#         ) # on_hold will be False after save
#         self.stdout.write(f"Created 2 Panth records.")

#         # 4. Varna
#         varna_brahmin = Varna.objects.create(
#             panth=panth_nath, name="Brahmin", code="BRM01"
#         )
#         self.stdout.write(f"Created 1 Varna record.")

#         # 5. Caste
#         caste_bhatt = Caste.objects.create(
#             varna=varna_brahmin, name="Bhatt", code="BHT01"
#         )
#         self.stdout.write(f"Created 1 Caste record.")

#         # 6. SubCaste
#         subcaste_shrimali = SubCaste.objects.create(
#             caste=caste_bhatt, name="Shrimali", code="SHM01"
#         )
#         self.stdout.write(f"Created 1 SubCaste record.")

#         # 7. Gotra
#         gotra_kashyap = Gotra.objects.create(
#             subcaste=subcaste_shrimali, name="Kashyap", code="KAS01", hold_date=FUTURE_HOLD_DATE
#         ) # on_hold will be True after save
#         self.stdout.write(f"Created 1 Gotra record.")

#         # 8. SubGotra
#         subgotra_a = SubGotra.objects.create(
#             gotra=gotra_kashyap, name="Kashyap-A", code="KSA01"
#         )
#         self.stdout.write(f"Created 1 SubGotra record.")

#         # 9. Kul
#         kul_chauhan = Kul.objects.create(
#             subgotra=subgotra_a, name="Chauhan", code="CHU01"
#         )
#         self.stdout.write(f"Created 1 Kul record.")

#         # 10. Vansh
#         vansh_surya = Vansh.objects.create(
#             kul=kul_chauhan, name="Surya Vansh", code="SRV01"
#         )
#         self.stdout.write(f"Created 1 Vansh record.")

#         # 11. Family
#         family_modi = Family.objects.create(
#             vansh=vansh_surya, name="Modi", code="MOD01", hold_date=FUTURE_HOLD_DATE
#         ) # on_hold will be True after save
#         self.stdout.write(f"Created 1 Family record.")

#         # 12. Pidhi
#         pidhi_gen1 = Pidhi.objects.create(
#             family=family_modi, name="Generation 1", code="GEN01"
#         )
#         self.stdout.write(f"Created 1 Pidhi record.")


#         self.stdout.write(self.style.SUCCESS('\nSuccessfully seeded all hierarchical data! ✨'))