from django.core.management.base import BaseCommand
from user.models import ResidentialDetails, UserPersonalDetails, UserProfessionalDetails

class Command(BaseCommand):
    help = 'Syncs existing node JSON blobs into the new mapping tables'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting synchronization of ResidentialDetails..."))
        count = 0
        for obj in ResidentialDetails.objects.iterator():
            if obj.nodes:
                obj.save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Synced {count} ResidentialDetails records."))

        self.stdout.write(self.style.SUCCESS("Starting synchronization of UserPersonalDetails..."))
        count = 0
        for obj in UserPersonalDetails.objects.iterator():
            if obj.nodes:
                obj.save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Synced {count} UserPersonalDetails records."))

        self.stdout.write(self.style.SUCCESS("Starting synchronization of UserProfessionalDetails..."))
        count = 0
        for obj in UserProfessionalDetails.objects.iterator():
            if obj.personal_nodes or obj.professional_nodes:
                obj.save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Synced {count} UserProfessionalDetails records."))

        self.stdout.write(self.style.SUCCESS("All node mappings have been successfully synced!"))
