from django.core.management.base import BaseCommand
from notification.models import NotificationCategory, NotificationTemplate

class Command(BaseCommand):
    help = 'Seed database with initial Notification Templates for Login and Registration'

    def handle(self, *args, **kwargs):
        categories_data = [
            {"name": "security", "display_name": "Security & Alerts"},
            {"name": "account", "display_name": "Account Updates"},
        ]

        self.stdout.write("Starting to seed Notification Categories...")
        for cat_data in categories_data:
            category, created = NotificationCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults={"display_name": cat_data["display_name"]}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {category.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Category already exists: {category.name}"))

        security_category = NotificationCategory.objects.get(name="security")
        account_category = NotificationCategory.objects.get(name="account")

        templates_data = [
            {
                "category": security_category,
                "title": "New Login Alert",
                "content": "We noticed a recent login to your account from IP address {{ ip_address }} on {{ device_info }} at {{ login_time }}. If this was you, you can ignore this alert. If you don't recognize this activity, please change your password immediately.",
                "icon": "bi-shield-lock-fill",
                "icon_color": "warning",
                "channels": ["email", "in_app"],
                "is_active": True,
            },
            {
                "category": account_category,
                "title": "Welcome to Shashan!",
                "content": "Hi {{ user_name }}, welcome to Shashan! We are thrilled to have you on board. Please explore your dashboard and complete your profile to get the most out of our platform.",
                "icon": "bi-person-check-fill",
                "icon_color": "success",
                "channels": ["email", "in_app"],
                "is_active": True,
            }
        ]

        self.stdout.write("Starting to seed Notification Templates...")
        for tpl_data in templates_data:
            category = tpl_data.pop("category")
            title = tpl_data["title"]
            
            template, created = NotificationTemplate.objects.update_or_create(
                category=category,
                title=title,
                defaults=tpl_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created template: {template.title}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated/Verified template: {template.title}"))

        self.stdout.write(self.style.SUCCESS('Successfully seeded Notification Templates!'))
