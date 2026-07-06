from django.core.management.base import BaseCommand
from user.models import DesignationType

class Command(BaseCommand):
    help = 'Seed database with initial Designation Types'

    def handle(self, *args, **kwargs):
        designations_data = [
            {
                "name": "owner",
                "display_name": "Owner",
                "post_no": 1,
                "is_active": True
            },
            {
                "name": "partner",
                "display_name": "Partner",
                "post_no": 2,
                "is_active": True
            },
            {
                "name": "manager",
                "display_name": "Manager",
                "post_no": 3,
                "is_active": True
            },
            {
                "name": "account",
                "display_name": "Account",
                "post_no": 4,
                "is_active": True
            },
            {
                "name": "employee",
                "display_name": "Employee",
                "post_no": 5,
                "is_active": True
            },
            {
                "name": "labour",
                "display_name": "Labour",
                "post_no": 6,
                "is_active": True
            }
        ]

        self.stdout.write("Starting to seed Designation Types...")

        for desig_data in designations_data:
            designation, created = DesignationType.objects.update_or_create(
                name=desig_data['name'],
                defaults={
                    'display_name': desig_data['display_name'],
                    'post_no': desig_data['post_no'],
                    'is_active': desig_data['is_active'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created DesignationType: {designation.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified DesignationType: {designation.name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Designation Types!'))
