from django.core.management.base import BaseCommand
from user.models import UserRole

class Command(BaseCommand):
    help = 'Seed database with initial User Roles'

    def handle(self, *args, **kwargs):
        # Initial data fetched from your current database setup
        roles_data = [
            {"name": "admin", "display_name": "Admin", "parent_name": None, "is_active": True},
            {"name": "super_admin", "display_name": "Super Admin", "parent_name": "admin", "is_active": True},
            {"name": "system_admin", "display_name": "System Admin", "parent_name": "super_admin", "is_active": True},
            {"name": "group_admin", "display_name": "Group Admin", "parent_name": "system_admin", "is_active": True},
            {"name": "sub_group_admin", "display_name": "Sub Group Admin", "parent_name": "group_admin", "is_active": True},
            {"name": "user", "display_name": "User", "parent_name": None, "is_active": True},
            {"name": "merchant", "display_name": "Merchant", "parent_name": None, "is_active": True},
            {"name": "service_provider", "display_name": "Service Provider", "parent_name": None, "is_active": True},
            {"name": "vendor", "display_name": "Vendor", "parent_name": "merchant", "is_active": True},
            {"name": "supplier", "display_name": "Supplier", "parent_name": "merchant", "is_active": True},
            {"name": "manufacture", "display_name": "Manufacture", "parent_name": "merchant", "is_active": True},
            {"name": "job_worker", "display_name": "Job Worker", "parent_name": "service_provider", "is_active": True},
            {"name": "transporter", "display_name": "Transporter", "parent_name": "service_provider", "is_active": True},
            {"name": "consultant", "display_name": "Consultant", "parent_name": "service_provider", "is_active": True},
            {"name": "agency", "display_name": "Agency", "parent_name": "service_provider", "is_active": True},
            {"name": "freelancer", "display_name": "Freelancer", "parent_name": "service_provider", "is_active": True},
        ]

        self.stdout.write("Starting to seed User Roles...")

        for role_data in roles_data:
            parent_name = role_data.pop('parent_name', None)
            parent_role = None
            
            if parent_name:
                parent_role = UserRole.objects.filter(name=parent_name).first()
                if not parent_role:
                    self.stdout.write(self.style.ERROR(f"Parent role '{parent_name}' not found for '{role_data['name']}'!"))
                    continue
            
            role, created = UserRole.objects.update_or_create(
                name=role_data['name'],
                defaults={
                    'display_name': role_data['display_name'],
                    'parent': parent_role,
                    'is_active': role_data['is_active'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created role: {role.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified role: {role.name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded UserRoles!'))
