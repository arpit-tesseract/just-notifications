# configuration/management/commands/load_samplefiles.py
from django.core.management.base import BaseCommand
from configuration.models import SampleFile

class Command(BaseCommand):
    help = "Creates default SampleFile records by category"

    def handle(self, *args, **options):
        data = {
            "residential": [
                "globs", "continents", "countries", "states", "districts",
                "talukas", "cityvillages", "wards", "roomflashes", "roomtypes"
            ],
            "personal": [
                "religions", "sampradays", "panths", "varnas", "castes",
                "subcastes", "gotras", "subgotras", "kuls", "vanshes", "families", "pidhis"
            ],
            "professional": [
                "sections", "profclasses", "categories", "subcategories", "sectors",
                "subsectors", "departments", "subdepartments", "types", "brands"
            ],
        }

        created, skipped = 0, 0
        for category, models in data.items():
            for model_name in models:
                obj, was_created = SampleFile.objects.get_or_create(
                    category=category,
                    model_name=model_name
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Done! Created: {created}, Skipped (already existed): {skipped}"
        ))
