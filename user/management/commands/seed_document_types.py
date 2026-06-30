from django.core.management.base import BaseCommand
from user.models import DocumentType

class Command(BaseCommand):
    help = 'Seed database with initial Document Types'

    def handle(self, *args, **kwargs):
        documents_data = [
            {
                "name": "photo",
                "display_name": "Photo",
                "order": 1,
                "is_required": False,
                "is_active": True,
                "regex_pattern": None
            },
            {
                "name": "adhar_card",
                "display_name": "Adhar Card",
                "order": 2,
                "is_required": False,
                "is_active": True,
                "regex_pattern": None
            },
            {
                "name": "pan_card",
                "display_name": "Pan card",
                "order": 3,
                "is_required": False,
                "is_active": True,
                "regex_pattern": None
            },
            {
                "name": "driving_license",
                "display_name": "Driving License",
                "order": 4,
                "is_required": False,
                "is_active": True,
                "regex_pattern": None
            },
            {
                "name": "voter_id",
                "display_name": "Voter ID",
                "order": 5,
                "is_required": False,
                "is_active": True,
                "regex_pattern": None
            },
            {
                "name": "ration_card",
                "display_name": "Ration Card",
                "order": 6,
                "is_required": False,
                "is_active": True,
                "regex_pattern": None
            }
        ]

        self.stdout.write("Starting to seed Document Types...")

        for doc_data in documents_data:
            doc_type, created = DocumentType.objects.update_or_create(
                name=doc_data['name'],
                defaults={
                    'display_name': doc_data['display_name'],
                    'order': doc_data['order'],
                    'is_required': doc_data['is_required'],
                    'is_active': doc_data['is_active'],
                    'regex_pattern': doc_data['regex_pattern'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created DocumentType: {doc_type.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified DocumentType: {doc_type.name}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Document Types!'))
