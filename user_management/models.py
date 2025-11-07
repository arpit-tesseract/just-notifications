from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from datetime import datetime
from django.utils import timezone
from configuration import models as configm

class ArchiveQuerySet(models.QuerySet):
    def active(self):
        """Return only non-archived records."""
        return self.filter(is_archive=False)
    
    def archived(self):
        """Return only archived records."""
        return self.filter(is_archive=True)

# class ArchiveManager(models.Manager):
#     def get_queryset(self):
#         # Default queryset excludes archived records
#         return ArchiveQuerySet(self.model, using=self._db).filter(is_archive=False)
    
#     # Optional: allow direct calls like CustomUser.objects.archived()
#     def archived(self):
#         return self.get_queryset().archived()

class ArchiveMixin(models.Model):
    is_archive = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
    
    # objects = ArchiveManager()       # Default — hides archived
    # all_objects = models.Manager()   # For admin / debugging access to all records

    def archive(self):
        """Used to Soft delete (archive) this record."""
        self.is_archive = True
        self.archived_at = timezone.now()
        self.save(update_fields=['is_archive', 'archived_at'])

    def restore(self):
        """Used to Restore an archived record."""
        self.is_archive = False
        self.archived_at = None
        self.save(update_fields=['is_archive', 'archived_at'])
        
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
    
class ResidentialDetail(models.Model):
    residential_type_choice = [
        ('home','Home'),
        ('bussiness','Bussiness'),
    ]
    # user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    residential_type = models.CharField(choices=residential_type_choice, max_length=20)
    glob = models.ForeignKey(configm.Glob, on_delete=models.SET_NULL, null=True, blank=True)
    continent = models.ForeignKey(configm.Continent, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(configm.Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(configm.State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(configm.District, on_delete=models.SET_NULL, null=True, blank=True)
    taluka = models.ForeignKey(configm.Taluka, on_delete=models.SET_NULL, null=True, blank=True)
    city_village = models.ForeignKey(configm.CityVillage, on_delete=models.SET_NULL, null=True, blank=True)
    ward = models.ForeignKey(configm.Ward, on_delete=models.SET_NULL, null=True, blank=True)
    society = models.CharField(max_length=255, null=True, blank=True)
    block = models.CharField(max_length=20, null=True, blank=True)
    floor = models.CharField(max_length=20, null=True, blank=True)
    house_no = models.CharField(max_length=20, null=True, blank=True)
    total_no_of_rooms = models.IntegerField(default=1)
    room_details = models.JSONField(null=True, blank=True)
    pending_rooms_to_allocate = models.JSONField(null=True, blank=True)
    residential_code = models.CharField(max_length=255,blank=True, null=True, unique=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Check if 'update_fields' is used. If it is, and 'residential_code' 
        # is the only field, just let it save. This helps prevent recursion.
        if 'update_fields' in kwargs and list(kwargs['update_fields']) == ['residential_code']:
            super().save(*args, **kwargs)
            return

        # Save the object. If it's new, this will create it and populate self.id.
        # If it's an update, it saves the other fields.
        super().save(*args, **kwargs)

        # Now, self.id is guaranteed to have a value.
        # Generate the new code.
        new_code = f"{self.id}-" \
                   f"{self.glob.code if self.glob else '00'}-" \
                   f"{self.continent.code if self.continent else '00'}-" \
                   f"{self.country.code if self.country else '00'}-" \
                   f"{self.state.code if self.state else '00'}-" \
                   f"{self.district.code if self.district else '00'}-" \
                   f"{self.taluka.code if self.taluka else '00'}-" \
                   f"{self.city_village.code if self.city_village else '00'}-" \
                   f"{self.ward.code if self.ward else '00'}-"

        # Only save again if the code has actually changed.
        # This prevents an infinite loop on updates.
        if self.residential_code != new_code:
            self.residential_code = new_code
            # Save *only* the residential_code field.
            super().save(update_fields=['residential_code'])
    
    def __str__(self):
        return f"{self.residential_type} - {self.residential_code}"

# class ActiveCustomUserManager(CustomUserManager):
#     """
#     Custom manager that filters out all archived users
#     by default.
#     """
#     def get_queryset(self):
#         # Get the initial queryset from the parent (CustomUserManager)
#         # Then, chain the filter to it.
#         return super().get_queryset().filter(is_archive=False)

class CustomUser(AbstractBaseUser, PermissionsMixin, ArchiveMixin):
    email = models.EmailField(unique=True)
    contact_no = models.CharField(max_length=20, unique=True)
    user_role = models.ManyToManyField(UserRole)
    is_super_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    full_name = models.CharField( max_length=50)
    pet_name = models.CharField(max_length=50, null=True, blank=True)
    father_name = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='users/photo/', blank=True, null=True)
    gender = models.CharField(choices=[('male','Male'), ('female','Female'), ('other','Other')], max_length=20)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=4, null=True, blank=True)
    marital_status = models.CharField(choices=[('single','Single'), ('married','Married')], max_length=20)
    expired_date = models.DateField(null=True, blank=True)
    residential_details = models.ForeignKey(ResidentialDetail, on_delete=models.SET_NULL, null=True, blank=True)
    category_of_user = models.CharField(choices=[('owner','Owner'), ('tenant','Tenant'), ('grp_tenant','Group Tenant')], max_length=20)
    allocated_rooms = models.JSONField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    # all_objects = models.Manager()

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
    personal_code = models.CharField(max_length=100, null=True, blank=True, unique=True)
    is_verified = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Prevent recursion if we are just saving the code
        if 'update_fields' in kwargs and list(kwargs['update_fields']) == ['personal_code']:
            super().save(*args, **kwargs)
            return

        # Save the object *first* to get self.id
        super().save(*args, **kwargs)

        # Now, generate the code with a valid self.id
        new_code = f"{self.id}-" \
                   f"{self.religion.code if self.religion else '00'}-" \
                   f"{self.sampraday.code if self.sampraday else '00'}-" \
                   f"{self.panth.code if self.panth else '00'}-" \
                   f"{self.varna.code if self.varna else '00'}-" \
                   f"{self.caste.code if self.caste else '00'}-" \
                   f"{self.subcaste.code if self.subcaste else '00'}-" \
                   f"{self.gotra.code if self.gotra else '00'}-" \
                   f"{self.subgotra.code if self.subgotra else '00'}-" \
                   f"{self.kul.code if self.kul else '00'}-" \
                   f"{self.vansh.code if self.vansh else '00'}-" \
                   f"{self.family.code if self.family else '00'}-" \
                   f"{self.pidhi.code if self.pidhi else '00'}"

        # Save again *only* if the code has changed
        if self.personal_code != new_code:
            self.personal_code = new_code
            super().save(update_fields=['personal_code'])
    
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
    relation_category = models.CharField(choices=relation_category_choices, max_length=20)
    designation = models.ForeignKey("configuration.Designation", on_delete=models.CASCADE) # option-1 (Father, mother)
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="to_user")
    post_no = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.from_user} - {self.designation.name} - {self.to_user}"

class Document(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    adhar_card_no = models.CharField(max_length=12, unique=True, blank=True, null=True)
    adhar_card_file = models.FileField(upload_to='users/documents/adharCard/', blank=True, null=True)
    pan_card_no = models.CharField(max_length=10, unique=True, blank=True, null=True)
    pan_card_file = models.FileField(upload_to='users/documents/panCard/', blank=True, null=True)
    voter_card_no = models.CharField(max_length=10, unique=True, blank=True, null=True)
    voter_card_file = models.FileField(upload_to='users/documents/voterCard/', blank=True, null=True)
    driving_licence_no = models.CharField(max_length=20, unique=True, blank=True, null=True)
    driving_licence_file = models.FileField(upload_to='users/documents/drivingLicence/', blank=True, null=True)
    ration_card_no = models.CharField(max_length=20, blank=True, null=True)
    ration_card_file = models.FileField(upload_to='users/documents/rationCard/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user}"



        

# class RoomDetail(models.Model):
#     residential_details = models.ForeignKey(ResidentialDetail, on_delete=models.CASCADE)
#     room_flash = models.ForeignKey(configm.RoomFlash, on_delete=models.SET_NULL, null=True)
#     room_no = models.CharField(max_length=20, null=True, blank=True)
#     room_member_count = models.IntegerField(null=True,blank=True)


# class RoomMembersDetail(models.Model):
#     room = models.ForeignKey(RoomDetail, on_delete=models.CASCADE)
#     members = models.ManyToManyField(CustomUser)


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
    pay_scale = models.CharField(max_length=20)
    mfg_dt_time = models.DateTimeField("MFG date & time")
    mfg_life = models.CharField("MFG life", max_length=20)
    professional_code = models.CharField("Professional ID", max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Prevent recursion if we are just saving the code
        if 'update_fields' in kwargs and list(kwargs['update_fields']) == ['professional_code']:
            super().save(*args, **kwargs)
            return

        # Save the object *first* to get self.id
        super().save(*args, **kwargs)

        # Now, generate the code with a valid self.id
        new_code = f"{self.id}-" \
                   f"{self.section.code if self.section else '00'}-" \
                   f"{self.profclass.code if self.profclass else '00'}-" \
                   f"{self.category.code if self.category else '00'}-" \
                   f"{self.subcategory.code if self.subcategory else '00'}-" \
                   f"{self.sector.code if self.sector else '00'}-" \
                   f"{self.subsector.code if self.subsector else '00'}-" \
                   f"{self.department.code if self.department else '00'}-" \
                   f"{self.subdepartment.code if self.subdepartment else '00'}-" \
                   f"{self.type.code if self.type else '00'}-" \
                   f"{self.brand.code if self.brand else '00'}-" \
                   f"{self.designation.code if self.designation else '00'}-"  # <-- Fixed typo here

        # Save again *only* if the code has changed
        if self.professional_code != new_code:
            self.professional_code = new_code
            super().save(update_fields=['professional_code'])

    def __str__(self):
        return f"{self.user} - {self.professional_code}"

class ReportCard(models.Model):
    prof_detail = models.ForeignKey(ProfessionalDetail, on_delete=models.CASCADE)
    input_diet = models.CharField(max_length=20)
    input_quantity = models.IntegerField(default=0)
    input_rate = models.FloatField()
    GENDER_CHOICES = [
        ('female','Female'),
        ('male','Male'),
        ('other','Other'),
    ]
    gender = models.CharField(choices=GENDER_CHOICES, max_length=6)
    color = models.CharField(max_length=20)
    height = models.FloatField()
    length = models.FloatField()
    width = models.FloatField()
    volume = models.FloatField()
    used_item = models.CharField(max_length=20)
    used_rate = models.FloatField()
    used_quantity = models.IntegerField()
    capacity = models.FloatField("capacity/strength")
    
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