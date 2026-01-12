from django.core.management.base import BaseCommand
from django.db import transaction

from wallet.models import (
    WalletType,
    LimitType,
    TransactionCategory,
    TransactionType,
)

class Command(BaseCommand):
    help = "Seed Wallet Master Data."
    
    def create_wallet_types(self):
        wallet_types = [
            "INDIVIDUAL",
            "FAMILY",
            "PROFESSIONAL",
        ]

        for name in wallet_types:
            obj, created = WalletType.objects.get_or_create(
                name=name,
                defaults={"is_active": True}
            )
            if created:
                self.stdout.write(f"  ✔ WalletType created: {name}")

    # -----------------------
    # Limit Types
    # -----------------------
    def create_limit_types(self):
        limit_types = [
            "PER_TRANSACTION",
            "DAILY",
            "MONTHLY",
            "YEARLY",
        ]

        for name in limit_types:
            obj, created = LimitType.objects.get_or_create(
                name=name,
                defaults={"is_active": True}
            )
            if created:
                self.stdout.write(f"  ✔ LimitType created: {name}")
        
    
    # -----------------------
    # Transaction Categories
    # -----------------------
    def create_transaction_categories(self):
        categories = [
            "SHASHAN_COMMISION",
            "GOVERNMENT",
            "HOME_ASSET",
            "PRIVATE",
            "COMMON",
            "FAMILY_PERSONAL",
            "DONATION",
            "SEFT",
            "PROFESSIONAL",
            "GUEST",
            "OTHER",
        ]

        for name in categories:
            obj, created = TransactionCategory.objects.get_or_create(
                name=name,
                defaults={"is_active": True}
            )
            if created:
                self.stdout.write(f"  ✔ TransactionCategory created: {name}")
    
    
    # -----------------------
    # Transaction Types
    # -----------------------
    def create_transaction_types(self):
        transaction_types = [
            "CASH",
            "WALLET_TRANSFER",
            "BANK_TRANSFER",
            "CHEQUE",
            "PAYMENT_GATEWAY",
            "UPI",
            "CARD",
            "OTHER",
        ]

        for name in transaction_types:
            obj, created = TransactionType.objects.get_or_create(
                name=name,
                defaults={"is_active": True}
            )
            if created:
                self.stdout.write(f"  ✔ TransactionType created: {name}")
    
    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding wallet master data..."))
        
        self.create_wallet_types()
        self.create_limit_types()
        self.create_transaction_categories()
        self.create_transaction_types()

        self.stdout.write(self.style.SUCCESS("✅ Wallet master data seeded successfully"))