from django.core.management.base import BaseCommand
from django.utils import timezone
from django.apps import apps
from django.db import models
from configuration.models import HoldableMixin

class Command(BaseCommand):
    help = ("Finds all items with an expired hold_date and updates them "
            "by calling their .save() method.")

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f"Checking for expired holds on {today}...")

        total_updated = 0
        
        # 1. Automatically find all (non-abstract) models that use the mixin
        models_to_check = [
            model for model in apps.get_models()
            # This is the fix: check against the mixin you imported
            if issubclass(model, HoldableMixin) and not model._meta.abstract
        ]
        
        # This line is just for logging
        # self.stdout.write(f"Found {len(models_to_check)} models to check: "
        #                   f"{[m.__name__ for m in models_to_check]}")

        # 2. Process each model
        for model in models_to_check:
            model_name = model.__name__
            try:
                # Find all items that are on hold with a date in the past
                expired_items = model.objects.filter(
                    on_hold=True,
                    hold_date__lt=today
                )

                count = 0
                
                # --- THIS IS THE KEY ---
                # We loop and call .save() on each one.
                # This triggers your mixin's custom save() logic.
                # It's slower than .update() but 100% correct and maintainable.
                for item in expired_items.iterator(): # .iterator() saves memory
                    item.save()
                    count += 1
                # ---------------------
                
                if count > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully released {count} items from {model_name}'
                    ))
                    total_updated += count

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Error processing {model_name}: {e}'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Task complete. Total items released: {total_updated}'
        ))