from django.core.management.base import BaseCommand
from configuration.models import Dimension, Level

class Command(BaseCommand):
    help = 'Seed database with initial Levels'

    def handle(self, *args, **kwargs):
        levels_data = [
            # Personal Dimension
            {"dimension": "Personal", "display_name": "Religion", "name": "religion", "single_mode": False},
            {"dimension": "Personal", "display_name": "Sampraday", "name": "sampraday", "single_mode": False},
            {"dimension": "Personal", "display_name": "Panth", "name": "panth", "single_mode": False},
            {"dimension": "Personal", "display_name": "Awastha", "name": "awastha", "single_mode": True},
            {"dimension": "Personal", "display_name": "Varna", "name": "varna", "single_mode": False},
            {"dimension": "Personal", "display_name": "Caste", "name": "caste", "single_mode": False},
            {"dimension": "Personal", "display_name": "Sub Caste", "name": "sub_caste", "single_mode": False},
            {"dimension": "Personal", "display_name": "Gotra", "name": "gotra", "single_mode": False},
            {"dimension": "Personal", "display_name": "Subgotra", "name": "subgotra", "single_mode": False},
            {"dimension": "Personal", "display_name": "Kul", "name": "kul", "single_mode": False},
            {"dimension": "Personal", "display_name": "Vansh", "name": "vansh", "single_mode": False},
            {"dimension": "Personal", "display_name": "Family", "name": "family", "single_mode": True},
            {"dimension": "Personal", "display_name": "Pidhi", "name": "pidhi", "single_mode": True},
            
            # Professional Dimension
            {"dimension": "Professional", "display_name": "Section", "name": "section", "single_mode": False},
            {"dimension": "Professional", "display_name": "Class", "name": "class", "single_mode": False},
            {"dimension": "Professional", "display_name": "Category", "name": "category", "single_mode": False},
            {"dimension": "Professional", "display_name": "Subcategory", "name": "subcategory", "single_mode": False},
            {"dimension": "Professional", "display_name": "Sector", "name": "sector", "single_mode": False},
            {"dimension": "Professional", "display_name": "Sub Sector", "name": "sub_sector", "single_mode": False},
            {"dimension": "Professional", "display_name": "Department", "name": "department", "single_mode": False},
            {"dimension": "Professional", "display_name": "Sub Department", "name": "sub_department", "single_mode": False},
            {"dimension": "Professional", "display_name": "Type", "name": "type", "single_mode": False},
            {"dimension": "Professional", "display_name": "Brand", "name": "brand", "single_mode": False},
            
            # Residential Dimension
            {"dimension": "Residential", "display_name": "Gob", "name": "gob", "single_mode": False},
            {"dimension": "Residential", "display_name": "Continent", "name": "continent", "single_mode": False},
            {"dimension": "Residential", "display_name": "Country", "name": "country", "single_mode": False},
            {"dimension": "Residential", "display_name": "State", "name": "state", "single_mode": False},
            {"dimension": "Residential", "display_name": "District", "name": "district", "single_mode": False},
            {"dimension": "Residential", "display_name": "Taluka", "name": "taluka", "single_mode": False},
            {"dimension": "Residential", "display_name": "City Village", "name": "city_village", "single_mode": False},
            {"dimension": "Residential", "display_name": "Ward", "name": "ward", "single_mode": False},
            {"dimension": "Residential", "display_name": "Society", "name": "society", "single_mode": False},
            {"dimension": "Residential", "display_name": "Block", "name": "block", "single_mode": False},
            {"dimension": "Residential", "display_name": "Floor", "name": "floor", "single_mode": False},
            {"dimension": "Residential", "display_name": "House", "name": "house", "single_mode": False},
            {"dimension": "Residential", "display_name": "Room", "name": "room", "single_mode": False},
        ]

        self.stdout.write("Starting to seed Levels...")

        # Keep track of the last created level per dimension to set as parent
        last_level_for_dimension = {}
        sort_order_for_dimension = {}

        for level_data in levels_data:
            dimension_name = level_data['dimension']
            dimension = Dimension.objects.filter(name=dimension_name).first()
            
            if not dimension:
                self.stdout.write(self.style.ERROR(f"Dimension '{dimension_name}' not found! Run `python manage.py seed_dimensions` first."))
                continue

            # Calculate sort_order and parent
            current_order = sort_order_for_dimension.get(dimension_name, 0) + 1
            sort_order_for_dimension[dimension_name] = current_order
            parent = last_level_for_dimension.get(dimension_name)

            level, created = Level.objects.update_or_create(
                dimension=dimension,
                name=level_data['name'],
                defaults={
                    'display_name': level_data['display_name'],
                    'single_mode': level_data['single_mode'],
                    'parent': parent,
                    'sort_order': current_order,
                }
            )

            # Update the last level to the one we just created
            last_level_for_dimension[dimension_name] = level
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Level: {level.display_name} under {dimension_name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated Level: {level.display_name} under {dimension_name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Levels!'))
