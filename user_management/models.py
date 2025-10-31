from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import datetime
from configuration import models as configm

# class CustomUserManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError("Email must be provided")
#         email = self.normalize_email(email)
        
#         # Extract roles before creating the instance
#         roles = extra_fields.pop("user_role", None)
        
#         user = self.model(email=email, **extra_fields)  # <-- no ManyToMany in extra_fields
#         user.set_password(password)
#         user.save()  # must save before setting ManyToMany
        
#         if roles:
#             if not isinstance(roles, list):
#                 roles = [roles]
#             user.user_role.set(roles)  # <-- safe
#         return user

#     def create_superuser(self, email, password, **extra_fields):
#         # get or create admin role
#         role, _ = UserRole.objects.get_or_create(
#             name="tesseract_admin",
#             display_name="Tesseract Admin"
#         )
#         extra_fields.setdefault("is_staff", True)
#         extra_fields.setdefault("is_superuser", True)
        
#         # Pass role separately, not in extra_fields
#         return self.create_user(email, password, user_role=[role], **extra_fields)

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)

        # Extract roles before creating the instance (don't pass M2M into model __init__)
        roles = extra_fields.pop("user_role", None)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        if roles:
            if not isinstance(roles, (list, tuple)):
                roles = [roles]
            user.user_role.set(roles)

        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        # Django's createsuperuser already prompts for email & password; they come here
        # Ensure we don't accidentally prompt for them again or pass them twice.
        # Remove them from extra_fields if present.
        extra_fields.pop("email", None)
        extra_fields.pop("password", None)

        # ensure admin role exists
        role, _ = UserRole.objects.get_or_create(
            name="tesseract_admin",
            display_name="Tesseract Admin"
        )

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        # Build list of NOT NULL concrete fields to prompt for,
        # but exclude these known ones that are handled by Django or are auto fields.
        skip_field_names = {
            "id", "email", "password", "last_login", "is_staff", "is_superuser", "is_super_admin"
        }

        not_null_fields = [
            f for f in CustomUser._meta.get_fields()
            if (getattr(f, "concrete", False)
                and not getattr(f, "null", False)
                and not getattr(f, "auto_created", False)
                and f.name not in skip_field_names
                and not isinstance(f, models.ManyToManyField))
        ]

        # Prompt for missing required fields (email already provided by caller)
        for field in not_null_fields:
            if field.name in extra_fields:
                continue  # caller provided it already

            prompt_label = f"Enter {getattr(field, 'verbose_name', field.name)} ({field.name}): "

            if isinstance(field, models.DateField):
                while True:
                    val = input(prompt_label + " (YYYY-MM-DD): ").strip()
                    if not val:
                        print("This field is required.")
                        continue
                    try:
                        extra_fields[field.name] = datetime.strptime(val, "%Y-%m-%d").date()
                        break
                    except ValueError:
                        print("Invalid date. Use YYYY-MM-DD.")
            else:
                while True:
                    val = input(prompt_label).strip()
                    if not val:
                        print("This field is required.")
                        continue
                    extra_fields[field.name] = val
                    break

        # Now create the user (pass email and password as single values)
        return self.create_user(email=email, password=password, user_role=[role], **extra_fields)




# System Admin / User / Merchant / Service Provider 
class UserRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    



class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    contact_no = models.CharField(max_length=15)
    user_role = models.ManyToManyField(UserRole)
    is_super_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    full_name = models.CharField("Real Name", max_length=50)
    pet_name = models.CharField("Pet Name", max_length=50, null=True, blank=True)
    father_name = models.CharField("Father Name", max_length=50)
    photo = models.ImageField("Photo", upload_to='users/photo/', blank=True, null=True)
    date_of_birth = models.DateField("Date of Birth")
    blood_group = models.CharField("Blood Group", max_length=4, null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def check_is_system_admin(self):
        # Check user role (case-insensitive match)
        return self.user_role.filter(name__iexact="system_admin").exists()
    
    def check_is_super_admin(self):
        # Check boolean field
        if self.is_super_admin and self.user_role.filter(name__iexact="system_admin").exists():
            return True
        # Check user role (case-insensitive match)
        return False
    
    
# class Address(models.Model):
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
#     ADDRESS_CHOICES = [
#         ('current','Current Address'),
#         ('owner','Owner Address'),
#         ('permanent','Permanent Address'),
#         ('native','Native Address'),
#         ('inlaws','InLaws Address'),
#         ('maternal','Maternal Address'),
#         ('business','Business Address')
#     ]
#     address_type = models.CharField("Address Type", max_length=20, choices=ADDRESS_CHOICES)
#     block_number = models.CharField("Block Number", max_length=20)
#     floor = models.CharField("Floor", max_length=20)
#     room_count = models.IntegerField("Room Count", default=0)
#     house_number = models.CharField("House Number", max_length=20)
#     main_person = models.CharField("Main/Mukhiya's Name", max_length=30)
#     mobile_number = models.CharField("Mobile Number", max_length=14)
#     is_verified = models.BooleanField(default=False)

#     def save(self, *args, **kwargs):
#         super().save(*args, **kwargs)
#         user = self.user

#         if Address.objects.filter(user=user).exists():
#             has_unverified = Address.objects.filter(user=user, is_verified=False).exists()
#             if has_unverified:
#                 user.is_verified = False
#             else:
#                 user.is_verified = True
#             user.save(update_fields=['is_verified'])


# class Relation(models.Model):
#     relation_category_choices = [
#         ('current','Current'),
#         ('owner','Owner'),
#         ('permanent','Permanent'),
#         ('native','Native'),
#         ('inlaws','InLaws'),
#         ('maternal','Maternal'),
#         ('business','Business')
#     ]
#     from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="from_user")
#     relation_category = models.CharField("Relation Category",choices=relation_category_choices, max_length=20)
#     designation = models.ForeignKey("configuration.Designation", on_delete=models.CASCADE) # option-1 (Father, mother)
#     to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="to_user")

#     def __str__(self):
#         return f"{self.from_user} - {self.designation.name} - {self.to_user}"
    
    
class PersonalDetail(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    religion = models.ForeignKey(configm.Religion, on_delete=models.SET_NULL, null=True, blank=True)
    sampraday = models.ForeignKey(configm.Sampraday, on_delete=models.SET_NULL, null=True, blank=True)
    panth = models.ForeignKey(configm.Panth, on_delete=models.SET_NULL, null=True, blank=True)
    varna = models.ForeignKey(configm.Varna, on_delete=models.SET_NULL, null=True, blank=True)
    caste = models.ForeignKey(configm.Caste, on_delete=models.SET_NULL, null=True, blank=True)
    subcaste = models.ForeignKey(configm.SubCaste, on_delete=models.SET_NULL, null=True, blank=True)
    gotra = models.ForeignKey(configm.Gotra, on_delete=models.SET_NULL, null=True, blank=True)
    subgotra = models.ForeignKey(configm.SubGotra, on_delete=models.SET_NULL, null=True, blank=True)
    kul = models.ForeignKey(configm.Kul, on_delete=models.SET_NULL, null=True, blank=True)
    vansh = models.ForeignKey(configm.Vansh, on_delete=models.SET_NULL, null=True, blank=True)
    family = models.ForeignKey(configm.Family, on_delete=models.SET_NULL, null=True, blank=True)
    pidhi = models.ForeignKey(configm.Pidhi, on_delete=models.SET_NULL, null=True, blank=True)
    personal_code = models.CharField("Personal ID", max_length=100, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        self.personal_code = f"{self.religion.code if self.religion else '00'}-" \
                         f"{self.sampraday.code if self.sampraday else '00'}-" \
                         f"{self.panth.code if self.panth else '00'}-" \
                         f"{self.varna.code if self.varna else '00'}-" \
                         f"{self.caste.code if self.caste else '00'}-" \
                         f"{self.subcaste.code if self.subcaste else '00'}-" \
                         f"{self.gotra.code if self.gotra else '00'}-" \
                         f"{self.subgotra.code if self.subgotra else '00'}-" \
                         f"{self.pidhi.code if self.pidhi else '00'}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user} - {self.personal_code}"

class Relation(models.Model):
    relation_category_choices = [
        ('current','Current'),
        ('owner','Owner'),
        ('permanent','Permanent'),
        ('native','Native'),
        ('inlaws','InLaws'),
        ('maternal','Maternal'),
        ('business','Business')
    ]
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="from_user")
    relation_category = models.CharField("Relation Category",choices=relation_category_choices, max_length=20)
    designation = models.ForeignKey("configuration.Designation", on_delete=models.CASCADE) # option-1 (Father, mother)
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="to_user")
    custom_post_no = models.FloatField("Post Number", null=True, blank=True)
    
    def __str__(self):
        return f"{self.from_user} - {self.designation.name} - {self.to_user}"

class Document(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    adhar_card_no = models.CharField("Adhar Card Number", max_length=12, unique=True, blank=True, null=True)
    adhar_card_file = models.FileField("Adhar Card", upload_to='users/documents/adharCard/', blank=True, null=True)
    pan_card_no = models.CharField("Pan Card Number", max_length=10, unique=True, blank=True, null=True)
    pan_card_file = models.FileField("Pan Card", upload_to='users/documents/panCard/', blank=True, null=True)
    voter_card_no = models.CharField("Voter Card Number", max_length=10, unique=True, blank=True, null=True)
    voter_card_file = models.FileField("Voter Card", upload_to='users/documents/voterCard/', blank=True, null=True)
    driving_licence_no = models.CharField("Driving Licence Number", max_length=20, unique=True, blank=True, null=True)
    driving_licence_file = models.FileField("Driving Licence", upload_to='users/documents/drivingLicence/', blank=True, null=True)
    ration_card_no = models.CharField("Ration Card Number", max_length=20, blank=True, null=True)
    ration_card_file = models.FileField("Ration Card", upload_to='users/documents/rationCard/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user}"


class ResidentialDetail(models.Model):
    residential_type_choice = [
        ('home','Home'),
        ('bussiness','Bussiness'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    residential_type = models.CharField("Residential Type", choices=residential_type_choice, max_length=20, null=True, blank=True)
    category_of_user = models.CharField(choices=[('owner','Owner'), ('tenant','Tenant'), ('grp_tenant','Group Tenant')], max_length=20)
    glob = models.ForeignKey(configm.Glob, on_delete=models.SET_NULL, null=True, blank=True)
    continent = models.ForeignKey(configm.Continent, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(configm.Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(configm.State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(configm.District, on_delete=models.SET_NULL, null=True, blank=True)
    taluka = models.ForeignKey(configm.Taluka, on_delete=models.SET_NULL, null=True, blank=True)
    city_village = models.ForeignKey(configm.CityVillage, on_delete=models.SET_NULL, null=True, blank=True)
    ward = models.ForeignKey(configm.Ward, on_delete=models.SET_NULL, null=True, blank=True)
    society = models.CharField("Society", max_length=255, null=True, blank=True)
    block = models.CharField("Block", max_length=20, null=True, blank=True)
    floor = models.CharField("Floor", max_length=20, null=True, blank=True)
    house_no = models.CharField("House No", max_length=20, null=True, blank=True)
    no_of_rooms = models.IntegerField("No. of Rooms", default=1)
    residential_code = models.CharField("Residential ID", max_length=100,blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.residential_code = f"{self.glob.code if self.glob else '00'}-" \
                            f"{self.continent.code if self.continent else '00'}-" \
                            f"{self.country.code if self.country else '00'}-" \
                            f"{self.state.code if self.state else '00'}-" \
                            f"{self.district.code if self.district else '00'}-" \
                            f"{self.taluka.code if self.taluka else '00'}-" \
                            f"{self.city_village.code if self.city_village else '00'}-" \
                            f"{self.ward.code if self.ward else '00'}-" 
                            # f"{self.society.code if self.society else '00'}-"
                            # f"{self.block.name if self.block else '00'}-" \
                            # f"{self.floor.code if self.floor else '00'}-" \
                            # f"{self.houses.code if self.houses else '00'}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user} - {self.residential_code}"
        

class RoomDetail(models.Model):
    residential_details = models.ForeignKey(ResidentialDetail, on_delete=models.CASCADE)
    room_flash = models.ForeignKey(configm.RoomFlash, on_delete=models.SET_NULL, null=True)
    room_no = models.CharField("Room No", max_length=20, null=True, blank=True)
    room_member_count = models.IntegerField("Total Room Members",null=True,blank=True, default=0)

class RoomMembersDetail(models.Model):
    room = models.ForeignKey(RoomDetail, on_delete=models.CASCADE)
    member_name = models.CharField("Member Name", max_length=20, null=True, blank=True)


class ProfessionalDetail(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    section = models.ForeignKey(configm.Section, on_delete=models.SET_NULL, null=True, blank=True)
    profclass = models.ForeignKey(configm.Class, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(configm.ProfCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(configm.ProfSubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    sector = models.ForeignKey(configm.Sector, on_delete=models.SET_NULL, null=True, blank=True)
    subsector = models.ForeignKey(configm.SubSector, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(configm.Department, on_delete=models.SET_NULL, null=True, blank=True)
    subdepartment = models.ForeignKey(configm.SubDepartment, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(configm.Type, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(configm.Brand, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(configm.Designation, on_delete=models.SET_NULL, null=True, blank=True)
    residential_details = models.ForeignKey(ResidentialDetail, on_delete=models.SET_NULL, null=True, blank=True)
    pay_scale = models.CharField("Pay Scale", max_length=20)
    mfg_dt_time = models.DateTimeField("MFG Date & Time")
    mfg_life = models.CharField("MFG Life", max_length=20)
    professional_code = models.CharField("Professional ID", max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.professional_code = f"{self.section.code if self.section else '00'}-" \
                             f"{self.profclass.code if self.profclass else '00'}-" \
                             f"{self.category.code if self.category else '00'}-" \
                             f"{self.subcategory.code if self.subcategory else '00'}-" \
                             f"{self.sector.code if self.sector else '00'}-" \
                             f"{self.subsector.code if self.subsector else '00'}-" \
                             f"{self.department.code if self.department else '00'}-" \
                             f"{self.subdepartment.code if self.subdepartment else '00'}-" \
                             f"{self.type.code if self.type else '00'}-" \
                             f"{self.brand.code if self.brand else '00'}-" \
                             f"{self.postmodel.code if self.postmodel else '00'}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user} - {self.professional_code}"

class ReportCard(models.Model):
    prof_detail = models.ForeignKey(ProfessionalDetail, on_delete=models.CASCADE)
    input_diet = models.CharField("Input Diet", max_length=20)
    input_quantity = models.IntegerField("Input Qunatity", default=0)
    input_rate = models.FloatField("Input Rate")
    GENDER_CHOICES = [
        ('female','Female'),
        ('male','Male'),
        ('other','Other'),
    ]
    gender = models.CharField(choices=GENDER_CHOICES, max_length=6)
    color = models.CharField("Colour", max_length=20)
    height = models.FloatField("Height")
    length = models.FloatField("Length")
    width = models.FloatField("Width")
    volume = models.FloatField("Volume")
    used_item = models.CharField("Used Item", max_length=20)
    used_rate = models.FloatField("Used Rate")
    used_quantity = models.IntegerField("Used Quantity")
    capacity = models.FloatField("Capacity/ Strength")
    
    def __str__(self):
        return f"{self.prof_detail}"



class OTP(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    email = models.EmailField()
    contact_no = models.CharField(max_length=15, null=True, blank=True)
    otp = models.CharField(max_length=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expired_at = models.DateTimeField()
    
    def __str__(self):
        return f"{self.email}, OTP: {self.otp}"