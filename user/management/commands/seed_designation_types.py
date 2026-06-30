from django.core.management.base import BaseCommand
from user.models import DesignationType

class Command(BaseCommand):
    help = 'Seed database with initial Designation Types'

    def handle(self, *args, **kwargs):
        designations_data = [
            {
                "name": "owner",
                "display_name": "Owner",
                "order": 1,
                "is_active": True
            },
            {
                "name": "partner",
                "display_name": "Partner",
                "order": 2,
                "is_active": True
            },
            {
                "name": "manager",
                "display_name": "Manager",
                "order": 3,
                "is_active": True
            },
            {
                "name": "account",
                "display_name": "Account",
                "order": 4,
                "is_active": True
            },
            {
                "name": "employee",
                "display_name": "Employee",
                "order": 5,
                "is_active": True
            },
            {
                "name": "labour",
                "display_name": "Labour",
                "order": 6,
                "is_active": True
            }
        ]

        self.stdout.write("Starting to seed Designation Types...")

        for desig_data in designations_data:
            designation, created = DesignationType.objects.update_or_create(
                name=desig_data['name'],
                defaults={
                    'display_name': desig_data['display_name'],
                    'order': desig_data['order'],
                    'is_active': desig_data['is_active'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created DesignationType: {designation.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified DesignationType: {designation.name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Designation Types!'))
