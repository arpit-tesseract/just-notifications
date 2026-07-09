from django.core.management.base import BaseCommand
from configuration.models import Dimension

class Command(BaseCommand):
    help = 'Seed database with initial Dimensions'

    def handle(self, *args, **kwargs):
        dimensions_data = [
            {
                "name": "Personal",
                "is_active": True
            },
            {
                "name": "Professional",
                "is_active": True
            },
            {
                "name": "Residential",
                "is_active": True
            }
        ]

        self.stdout.write("Starting to seed Dimensions...")

        for dim_data in dimensions_data:
            dimension, created = Dimension.objects.update_or_create(
                name=dim_data['name'],
                defaults={
                    'is_active': dim_data['is_active'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Dimension: {dimension.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified Dimension: {dimension.name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Dimensions!'))
