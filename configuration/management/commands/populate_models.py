from django.core.management.base import BaseCommand
from django.apps import apps
from configuration.models import ModelName  # Update with your app name

class Command(BaseCommand):
    help = 'Populate the ModelName table with all models in the project'

    def handle(self, *args, **kwargs):
        all_models = apps.get_models()
        count = 0

        for model in all_models:
            app_label = model._meta.app_label
            model_name = model.__name__
            technical_name = f"{app_label}.{model_name}"

            obj, created = ModelName.objects.get_or_create(
                technical_name=technical_name,
                defaults={
                    'app_label': app_label,
                    'model': model_name,
                    'description': model.__doc__ or ""
                }
            )
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Added: {technical_name}"))
            else:
                self.stdout.write(f"Exists: {technical_name}")

        self.stdout.write(self.style.SUCCESS(f"Total new models added: {count}"))
