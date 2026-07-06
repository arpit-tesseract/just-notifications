from django.core.management.base import BaseCommand
from user.models import RelationType, UserRole

class Command(BaseCommand):
    help = 'Seed database with initial Relation Types'

    def handle(self, *args, **kwargs):
        relations_data = [
            {
                "name": "husband",
                "display_name": "Husband",
                "is_active": True,
                "category": "general",
                "post_no": 1,
                "role_name": "user"
            },
            {
                "name": "wife",
                "display_name": "Wife",
                "is_active": True,
                "category": "general",
                "post_no": 2,
                "role_name": "user"
            },
            {
                "name": "son",
                "display_name": "Son",
                "is_active": True,
                "category": "general",
                "post_no": 3,
                "role_name": "user"
            },
            {
                "name": "guest",
                "display_name": "Guest",
                "is_active": True,
                "category": "general",
                "post_no": 4,
                "role_name": "user"
            },
            {
                "name": "worker",
                "display_name": "Worker",
                "is_active": True,
                "category": "general",
                "post_no": 5,
                "role_name": "user"
            },
            {
                "name": "daughter",
                "display_name": "Daughter",
                "is_active": True,
                "category": "general",
                "post_no": 6,
                "role_name": "user"
            },
            {
                "name": "father",
                "display_name": "Father",
                "is_active": True,
                "category": "general",
                "post_no": 7,
                "role_name": "user"
            },
            {
                "name": "mother",
                "display_name": "Mother",
                "is_active": True,
                "category": "general",
                "post_no": 8,
                "role_name": "user"
            },
            {
                "name": "uncle",
                "display_name": "Uncle",
                "is_active": True,
                "category": "general",
                "post_no": 9,
                "role_name": "user"
            },
            {
                "name": "aunty",
                "display_name": "Aunty",
                "is_active": True,
                "category": "general",
                "post_no": 10,
                "role_name": "user"
            },
            {
                "name": "grand_father",
                "display_name": "Grand Father",
                "is_active": True,
                "category": "general",
                "post_no": 11,
                "role_name": "user"
            },
            {
                "name": "grand_mother",
                "display_name": "Grand Mother",
                "is_active": True,
                "category": "general",
                "post_no": 12,
                "role_name": "user"
            },
            {
                "name": "father_in_law",
                "display_name": "Father-in-law",
                "is_active": True,
                "category": "in_laws",
                "post_no": 13,
                "role_name": "user"
            },
            {
                "name": "mother_in_law",
                "display_name": "Mother-in-law",
                "is_active": True,
                "category": "in_laws",
                "post_no": 14,
                "role_name": "user"
            },
            {
                "name": "sister_in_law",
                "display_name": "Sister-in-law",
                "is_active": True,
                "category": "in_laws",
                "post_no": 15,
                "role_name": "user"
            },
            {
                "name": "nana",
                "display_name": "Nana",
                "is_active": True,
                "category": "maternal",
                "post_no": 16,
                "role_name": "user"
            },
            {
                "name": "nani",
                "display_name": "Nani",
                "is_active": True,
                "category": "maternal",
                "post_no": 17,
                "role_name": "user"
            },
            {
                "name": "mama",
                "display_name": "Mama",
                "is_active": True,
                "category": "general",
                "post_no": 18,
                "role_name": "user"
            },
            {
                "name": "masi",
                "display_name": "Masi",
                "is_active": True,
                "category": "general",
                "post_no": 19,
                "role_name": "user"
            },
            {
                "name": "brother",
                "display_name": "Brother",
                "is_active": True,
                "category": "general",
                "post_no": 20,
                "role_name": "user"
            },
            {
                "name": "sister",
                "display_name": "Sister",
                "is_active": True,
                "category": "general",
                "post_no": 21,
                "role_name": "user"
            }
        ]

        self.stdout.write("Starting to seed Relation Types...")

        for rel_data in relations_data:
            role_name = rel_data.pop('role_name', None)
            role = None
            
            if role_name:
                role = UserRole.objects.filter(name=role_name).first()
                if not role:
                    self.stdout.write(self.style.WARNING(f"Role '{role_name}' not found for RelationType '{rel_data['name']}'. Make sure to run `python manage.py seed_user_roles` first."))
                    continue
            
            relation, created = RelationType.objects.update_or_create(
                name=rel_data['name'],
                defaults={
                    'display_name': rel_data['display_name'],
                    'is_active': rel_data['is_active'],
                    'category': rel_data['category'],
                    'post_no': rel_data['post_no'],
                    'role': role,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created RelationType: {relation.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified RelationType: {relation.name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Relation Types!'))
