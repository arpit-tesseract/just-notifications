from django.core.management.base import BaseCommand
from user.models import ResidentialType, UserRole

class Command(BaseCommand):
    help = 'Seed database with initial Residential Types'

    def handle(self, *args, **kwargs):
        types_data = [
            {"name": "current", "display_name": "Current", "order": 1, "is_active": True, "role_names": ["user"]},
            {"name": "owner_tenant", "display_name": "Owner Tenant", "order": 1, "is_active": True, "role_names": ["merchant", "service_provider"]},
            {"name": "owner", "display_name": "Owner", "order": 2, "is_active": True, "role_names": ["user"]},
            {"name": "group_tenant", "display_name": "Group Tenant", "order": 2, "is_active": True, "role_names": ["merchant", "service_provider"]},
            {"name": "permanent", "display_name": "Permanent", "order": 3, "is_active": True, "role_names": ["user"]},
            {"name": "native", "display_name": "Native", "order": 4, "is_active": True, "role_names": ["user"]},
            {"name": "in_laws", "display_name": "In-Laws", "order": 5, "is_active": True, "role_names": ["user"]},
            {"name": "maternal", "display_name": "Maternal", "order": 6, "is_active": True, "role_names": ["user"]},
            {"name": "business", "display_name": "Business", "order": 7, "is_active": True, "role_names": ["user"]},
        ]

        self.stdout.write("Starting to seed Residential Types...")

        for type_data in types_data:
            role_names = type_data.pop('role_names', [])
            
            res_type, created = ResidentialType.objects.update_or_create(
                name=type_data['name'],
                defaults={
                    'display_name': type_data['display_name'],
                    'order': type_data['order'],
                    'is_active': type_data['is_active'],
                }
            )
            
            if role_names:
                roles = UserRole.objects.filter(name__in=role_names)
                res_type.roles.set(roles)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created ResidentialType: {res_type.name} with roles {role_names}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified ResidentialType: {res_type.name} with roles {role_names}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Residential Types!'))
