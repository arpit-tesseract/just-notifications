from django.core.management.base import BaseCommand
from django.db import transaction

from common.models import StatusModelName, Status

class Command(BaseCommand):
    help = "Seed ModelName and Status master data"
    
    # -------------------------
    # Helpers
    # -------------------------
    def create_model_name(self, app_label, model, description=None):
        technical_name = f"{app_label}.{model}"

        obj, created = StatusModelName.objects.get_or_create(
            technical_name=technical_name,
            defaults={
                "app_label": app_label,
                "model": model,
                "description": description,
            }
        )

        if created:
            self.stdout.write(f"  ✔ ModelName created: {technical_name}")

        return obj

    
    def create_statuses(self, model, statuses):
        for name in statuses:
            obj, created = Status.objects.get_or_create(
                model=model,
                name=name,
                defaults={"is_active": True}
            )

            if created:
                self.stdout.write(
                    f"    ✔ Status created: {model.technical_name} → {name}"
                )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding ModelName & Status masters..."))
        
        wallet_model = self.create_model_name(
            app_label="wallet",
            model="Wallet",
        )
        
        transaction_model = self.create_model_name(
            app_label="wallet",
            model="Transaction",
            description="Transaction workflow statuses"
        )
        
        self.create_statuses(
            model=wallet_model,
            statuses=[
                "ACTIVE",
                "INACTIVE",
                "BLOCKED",
                "CLOSED",
            ]
        )
        
        self.create_statuses(
            model=transaction_model,
            statuses=[
                "INITIATED",
                "PENDING",
                "SUCCESS",
                "FAILED",
                "CANCELLED",
                "REVERSED",
            ]
        )
        
        self.stdout.write(self.style.SUCCESS("✅ Status master data seeded successfully"))
        
        
