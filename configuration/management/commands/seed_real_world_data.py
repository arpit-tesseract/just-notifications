from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from configuration.models import Dimension, Level, Node
from user.models import (
    User, UserRole, UserPersonalDetails, ResidentialDetails, UserProfessionalDetails,
    PersonalNodeMapping, ResidentialNodeMapping, ProfessionalNodeMapping, BusinessFamily
)
from notification.models import NotificationCategory, NotificationTemplate

class Command(BaseCommand):
    help = 'Seed database with real world dimensions, levels, nodes, and corresponding users'

    def handle(self, *args, **kwargs):
        self.stdout.write("Running basic seed commands...")
        # 1. Run seed_dimensions and seed_levels
        call_command('seed_dimensions')
        call_command('seed_levels')

        self.stdout.write("Starting real-world data seeding...")

        try:
            with transaction.atomic():
                # --- Fetch Dimensions ---
                personal_dim = Dimension.objects.get(name="Personal")
                prof_dim = Dimension.objects.get(name="Professional")
                res_dim = Dimension.objects.get(name="Residential")

                # --- Fetch Levels ---
                religion_lvl = Level.objects.get(dimension=personal_dim, name="religion")
                sampraday_lvl = Level.objects.get(dimension=personal_dim, name="sampraday")
                panth_lvl = Level.objects.get(dimension=personal_dim, name="panth")

                section_lvl = Level.objects.get(dimension=prof_dim, name="section")
                class_lvl = Level.objects.get(dimension=prof_dim, name="class")
                category_lvl = Level.objects.get(dimension=prof_dim, name="category")

                continent_lvl = Level.objects.get(dimension=res_dim, name="continent")
                country_lvl = Level.objects.get(dimension=res_dim, name="country")
                state_lvl = Level.objects.get(dimension=res_dim, name="state")
                district_lvl = Level.objects.get(dimension=res_dim, name="district")

                # --- 1. Seed Nodes (Hierarchical) ---
                # A. Personal Nodes
                hinduism, _ = Node.objects.get_or_create(
                    dimension=personal_dim, level=religion_lvl, code=1, parent=None,
                    defaults={'name': 'Hinduism'}
                )
                vaishnavism, _ = Node.objects.get_or_create(
                    dimension=personal_dim, level=sampraday_lvl, code=1, parent=hinduism,
                    defaults={'name': 'Vaishnavism'}
                )
                pushtimarg, _ = Node.objects.get_or_create(
                    dimension=personal_dim, level=panth_lvl, code=1, parent=vaishnavism,
                    defaults={'name': 'Pushtimarg'}
                )

                # B. Residential Nodes
                asia, _ = Node.objects.get_or_create(
                    dimension=res_dim, level=continent_lvl, code=1, parent=None,
                    defaults={'name': 'Asia'}
                )
                india, _ = Node.objects.get_or_create(
                    dimension=res_dim, level=country_lvl, code=1, parent=asia,
                    defaults={'name': 'India'}
                )
                gujarat, _ = Node.objects.get_or_create(
                    dimension=res_dim, level=state_lvl, code=1, parent=india,
                    defaults={'name': 'Gujarat'}
                )
                ahmedabad, _ = Node.objects.get_or_create(
                    dimension=res_dim, level=district_lvl, code=1, parent=gujarat,
                    defaults={'name': 'Ahmedabad'}
                )
                surat, _ = Node.objects.get_or_create(
                    dimension=res_dim, level=district_lvl, code=2, parent=gujarat,
                    defaults={'name': 'Surat'}
                )

                # C. Professional Nodes
                it_section, _ = Node.objects.get_or_create(
                    dimension=prof_dim, level=section_lvl, code=1, parent=None,
                    defaults={'name': 'Information Technology'}
                )
                dev_class, _ = Node.objects.get_or_create(
                    dimension=prof_dim, level=class_lvl, code=1, parent=it_section,
                    defaults={'name': 'Software Development'}
                )
                web_cat, _ = Node.objects.get_or_create(
                    dimension=prof_dim, level=category_lvl, code=1, parent=dev_class,
                    defaults={'name': 'Web Engineering'}
                )

                self.stdout.write(self.style.SUCCESS("Hierarchical nodes seeded successfully!"))

                # --- 2. Seed Users & Assign Node Mappings ---
                # Ensure a default role exists
                user_role, _ = UserRole.objects.get_or_create(
                    name="member", defaults={"display_name": "Member"}
                )

                # Create a sample business family
                business, _ = BusinessFamily.objects.get_or_create(
                    name="Tesseract Techno Labs",
                    defaults={
                        "business_type": "private_limited",
                        "email": "info@tesseract.com",
                        "contact_no": "1234567890"
                    }
                )

                # Create User 1: Dev Patel (Ahmedabad, IT, Pushtimarg)
                u1, created_u1 = User.objects.get_or_create(
                    contact_no="9999999991",
                    defaults={
                        "full_name": "Dev Patel",
                        "email": "dev.patel@example.com",
                        "is_verified": True
                    }
                )
                if created_u1:
                    u1.set_password("password123")
                    u1.roles.add(user_role)
                    u1.save()

                    # Personal mapping
                    p1 = UserPersonalDetails.objects.create(user=u1, is_verified=True)
                    PersonalNodeMapping.objects.create(personal_detail=p1, level=religion_lvl, node=hinduism)
                    PersonalNodeMapping.objects.create(personal_detail=p1, level=sampraday_lvl, node=vaishnavism)
                    PersonalNodeMapping.objects.create(personal_detail=p1, level=panth_lvl, node=pushtimarg)

                    # Residential mapping
                    r1 = ResidentialDetails.objects.create()
                    ResidentialNodeMapping.objects.create(residential_detail=r1, level=continent_lvl, node=asia)
                    ResidentialNodeMapping.objects.create(residential_detail=r1, level=country_lvl, node=india)
                    ResidentialNodeMapping.objects.create(residential_detail=r1, level=state_lvl, node=gujarat)
                    ResidentialNodeMapping.objects.create(residential_detail=r1, level=district_lvl, node=ahmedabad)
                    u1.current_residential_details = r1
                    u1.save()

                    # Professional mapping
                    prof1 = UserProfessionalDetails.objects.create(user=u1, business_family=business, is_active=True)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof1, level=section_lvl, node=it_section)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof1, level=class_lvl, node=dev_class)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof1, level=category_lvl, node=web_cat)

                    self.stdout.write(self.style.SUCCESS("Created Dev Patel (User 1) with node mappings"))

                # Create User 2: Arpit Shah (Surat, IT, Hinduism)
                u2, created_u2 = User.objects.get_or_create(
                    contact_no="9999999992",
                    defaults={
                        "full_name": "Arpit Shah",
                        "email": "arpit.shah@example.com",
                        "is_verified": True
                    }
                )
                if created_u2:
                    u2.set_password("password123")
                    u2.roles.add(user_role)
                    u2.save()

                    # Personal mapping
                    p2 = UserPersonalDetails.objects.create(user=u2, is_verified=True)
                    PersonalNodeMapping.objects.create(personal_detail=p2, level=religion_lvl, node=hinduism)

                    # Residential mapping
                    r2 = ResidentialDetails.objects.create()
                    ResidentialNodeMapping.objects.create(residential_detail=r2, level=continent_lvl, node=asia)
                    ResidentialNodeMapping.objects.create(residential_detail=r2, level=country_lvl, node=india)
                    ResidentialNodeMapping.objects.create(residential_detail=r2, level=state_lvl, node=gujarat)
                    ResidentialNodeMapping.objects.create(residential_detail=r2, level=district_lvl, node=surat)
                    u2.current_residential_details = r2
                    u2.save()

                    # Professional mapping
                    prof2 = UserProfessionalDetails.objects.create(user=u2, business_family=business, is_active=True)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof2, level=section_lvl, node=it_section)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof2, level=class_lvl, node=dev_class)

                    self.stdout.write(self.style.SUCCESS("Created Arpit Shah (User 2) with node mappings"))

                # Create User 3: Test Kinws (pahovi1231@kinws.com)
                u3, created_u3 = User.objects.get_or_create(
                    contact_no="9999999993",
                    defaults={
                        "full_name": "Test Kinws User",
                        "email": "pahovi1231@kinws.com",
                        "is_verified": True
                    }
                )
                if created_u3:
                    u3.set_password("password123")
                    u3.roles.add(user_role)
                    u3.save()

                    # Personal mapping
                    p3 = UserPersonalDetails.objects.create(user=u3, is_verified=True)
                    PersonalNodeMapping.objects.create(personal_detail=p3, level=religion_lvl, node=hinduism)
                    PersonalNodeMapping.objects.create(personal_detail=p3, level=sampraday_lvl, node=vaishnavism)
                    PersonalNodeMapping.objects.create(personal_detail=p3, level=panth_lvl, node=pushtimarg)

                    # Residential mapping
                    r3 = ResidentialDetails.objects.create()
                    ResidentialNodeMapping.objects.create(residential_detail=r3, level=continent_lvl, node=asia)
                    ResidentialNodeMapping.objects.create(residential_detail=r3, level=country_lvl, node=india)
                    ResidentialNodeMapping.objects.create(residential_detail=r3, level=state_lvl, node=gujarat)
                    ResidentialNodeMapping.objects.create(residential_detail=r3, level=district_lvl, node=ahmedabad)
                    u3.current_residential_details = r3
                    u3.save()

                    # Professional mapping
                    prof3 = UserProfessionalDetails.objects.create(user=u3, business_family=business, is_active=True)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof3, level=section_lvl, node=it_section)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof3, level=class_lvl, node=dev_class)
                    ProfessionalNodeMapping.objects.create(professional_detail=prof3, level=category_lvl, node=web_cat)

                    self.stdout.write(self.style.SUCCESS("Created Test Kinws User (User 3) with node mappings"))

                # Seed the notification category (acts as a folder/group for templates)
                auth_category, _ = NotificationCategory.objects.get_or_create(
                    name="authentication",
                    defaults={"display_name": "Authentication Alerts"}
                )

                # Template 1: Login Alert
                NotificationTemplate.objects.get_or_create(
                    name="user.login",
                    defaults={
                        "category": auth_category,
                        "title": "Login Alert",
                        "content": "Hello {{ full_name }}, a new login was detected on your account.",
                        "channels": ["in_app", "email"],
                        "is_active": True
                    }
                )
                self.stdout.write(self.style.SUCCESS("Seeded 'user.login' notification template under 'authentication' category"))

                # Template 2: Login OTP
                NotificationTemplate.objects.get_or_create(
                    name="user.login_otp",
                    defaults={
                        "category": auth_category,
                        "title": "OTP Login Alert",
                        "content": "Hello {{ full_name }}, a new login via OTP was detected.",
                        "channels": ["in_app"],
                        "is_active": True
                    }
                )
                self.stdout.write(self.style.SUCCESS("Seeded 'user.login_otp' notification template under 'authentication' category"))
                
                # Template 3: Password Reset
                NotificationTemplate.objects.get_or_create(
                    name="user.password_reset",
                    defaults={
                        "category": auth_category,
                        "title": "Password Reset Request",
                        "content": "Hello {{ full_name }}, your password reset link is: {{ reset_link }}.",
                        "channels": ["in_app", "email"],
                        "is_active": True
                    }
                )
                self.stdout.write(self.style.SUCCESS("Seeded 'user.password_reset' notification template under 'authentication' category"))

            self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during seeding: {e}"))
