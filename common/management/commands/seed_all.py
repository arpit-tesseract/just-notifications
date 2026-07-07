from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Run all seed files in the correct hierarchical sequence to avoid foreign key errors'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting master seed process..."))

        # The sequence matters! 
        # 1. Parents/Standalone tables must be seeded first
        # 2. Children tables that depend on them must be seeded next

        commands_sequence = [
            'seed_user_roles',         # Standalone (needed for relation types)
            'seed_relation_types',     # Depends on User Roles
            'seed_designation_types',  # Standalone
            'seed_document_types',     # Standalone
            'seed_residential_types',  # Standalone
            'seed_dimensions',         # Standalone (needed for levels)
            'seed_levels',             # Depends on Dimensions
            'seed_notification_templates', # Standalone (Notification)
        ]

        for command_name in commands_sequence:
            self.stdout.write(self.style.SUCCESS(f"\n--- Running: {command_name} ---"))
            try:
                call_command(command_name)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed while running {command_name}: {e}"))
                return # Stop execution if a dependency fails

        self.stdout.write(self.style.SUCCESS("\n=============================================="))
        self.stdout.write(self.style.SUCCESS("All seed files have been executed successfully!"))
        self.stdout.write(self.style.SUCCESS("=============================================="))
