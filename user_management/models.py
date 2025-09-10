from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from configuration import models as configm

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    USER_ROLE_CHOICES = [
        ('super_admin','Super Admin'),
        ('main_admin','Main Admin'),
        ('admin','Admin'),
        ('sub_admin','Sub Admin'),
        ('group_admin','Group Admin'),
        ('under_group_admin','Under Group Admin'),
    ]
    user_role = models.CharField(choices=USER_ROLE_CHOICES, max_length=100)
    is_system_user = models.BooleanField(default=False)
    continent_allocation = models.ManyToManyField(configm.Continent, blank=True)
    country_allocation = models.ManyToManyField(configm.Country, blank=True)
    state_allocation = models.ManyToManyField(configm.State, blank=True)
    district_allocation = models.ManyToManyField(configm.District, blank=True)
    city_allocation = models.ManyToManyField(configm.City, blank=True)
    village_allocation = models.ManyToManyField(configm.Village, blank=True)
    ward_allocation = models.ManyToManyField(configm.Ward, blank=True)
    block_allocation = models.ManyToManyField(configm.Block, blank=True)
    society_allocation = models.ManyToManyField(configm.Society, blank=True)
    access = models.ManyToManyField(configm.Accesses)
    date_of_birth = models.DateField(null=True, blank=True)
    category_of_user = models.CharField(choices=[('owner','Owner'), ('tenant','Tenant'), ('grp_tenant','Group Tenant')], max_length=20, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    ADDRESS_CHOICES = [
        ('current','Current Address'),
        ('owner','Owner Address'),
        ('permanent','Permanent Address'),
        ('native','Native Address'),
        ('inlaws','InLaws Address'),
        ('maternal','Maternal Address'),
        ('business','Business Address')
    ]
    address_type = models.CharField("Address Type", max_length=20, choices=ADDRESS_CHOICES)
    block_number = models.CharField("Block Number", max_length=20)
    floor = models.CharField("Floor", max_length=20)
    room_count = models.IntegerField("Room Count", default=0)
    house_number = models.CharField("House Number", max_length=20)
    main_person = models.CharField("Main/Mukhiya's Name", max_length=30)
    mobile_number = models.CharField("Mobile Number", max_length=14)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        user = self.user

        if Address.objects.filter(user=user).exists():
            has_unverified = Address.objects.filter(user=user, is_verified=False).exists()
            if has_unverified:
                user.is_verified = False
            else:
                user.is_verified = True
            user.save(update_fields=['is_verified'])

class RoomDetail(models.Model):
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    room_name = models.CharField("Room Type", max_length=10)
    room_member_count = models.IntegerField("Total Room Members", default=0)
    room_flash = models.ForeignKey(configm.RoomFlash, on_delete=models.SET_NULL, null=True)

class RoomMembersDetail(models.Model):
    room = models.ForeignKey(RoomDetail, on_delete=models.CASCADE)
    member_name = models.CharField("Member Name", max_length=20, null=True, blank=True)
    
class PersonalTable(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    religion = models.ForeignKey(configm.Religion, on_delete=models.SET_NULL, null=True)
    sampraday = models.ForeignKey(configm.Sampraday, on_delete=models.SET_NULL, null=True)
    panth = models.ForeignKey(configm.Panth, on_delete=models.SET_NULL, null=True)
    varna = models.ForeignKey(configm.Varna, on_delete=models.SET_NULL, null=True)
    caste = models.ForeignKey(configm.Caste, on_delete=models.SET_NULL, null=True)
    subcaste = models.ForeignKey(configm.SubCaste, on_delete=models.SET_NULL, null=True)
    gotra = models.ForeignKey(configm.Gotra, on_delete=models.SET_NULL, null=True)
    subgotra = models.ForeignKey(configm.SubGotra, on_delete=models.SET_NULL, null=True)
    pidhi = models.ForeignKey(configm.Pidhi, on_delete=models.SET_NULL, null=True)
    personal_code = models.CharField("Personal ID", max_length=100, null=True)

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

class Relation(models.Model):
    personal_table = models.ForeignKey(
        PersonalTable, 
        on_delete=models.CASCADE,
        related_name="relations"
    )
    designation = models.CharField("Designation", max_length=20)
    designation_number = models.CharField("Designation Number", max_length=10)
    real_name = models.CharField("Real Name", max_length=50)
    pet_name = models.CharField("Pet Name", max_length=50)
    father_name = models.CharField("Father Name", max_length=50)
    mobile = models.CharField("Mobile Number", max_length=14)
    photo = models.ImageField("Photo", upload_to='relations/', blank=True, null=True)
    date_of_birth = models.DateField("Date of Birth")
    blood_group = models.CharField("Blood Group", max_length=4)

class ProfessionalDetail(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    section = models.ForeignKey(configm.Section, on_delete=models.SET_NULL, null=True, blank=True)
    classs = models.ForeignKey(configm.Class, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(configm.ProfCategory, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(configm.ProfSubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    sector = models.ForeignKey(configm.Sector, on_delete=models.SET_NULL, null=True, blank=True)
    subsector = models.ForeignKey(configm.SubSector, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(configm.Department, on_delete=models.SET_NULL, null=True, blank=True)
    subdepartment = models.ForeignKey(configm.SubDepartment, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.ForeignKey(configm.Type, on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.ForeignKey(configm.Brand, on_delete=models.SET_NULL, null=True, blank=True)
    postmodel = models.ForeignKey(configm.PostModel, on_delete=models.SET_NULL, null=True, blank=True)
    pay_scale = models.CharField("Pay Scale", max_length=20)
    mfg_dt_time = models.DateTimeField("MFG Date & Time")
    mfg_life = models.CharField("MFG Life", max_length=20)
    professional_code = models.CharField("Professional ID", max_length=100, null=True)

    def save(self, *args, **kwargs):
        self.professional_code = f"{self.section.code if self.section else '00'}-" \
                             f"{self.classs.code if self.classs else '00'}-" \
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

class ResidentialDetail(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    continent = models.ForeignKey(configm.Continent, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(configm.Country, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(configm.State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(configm.District, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(configm.City, on_delete=models.SET_NULL, null=True, blank=True)
    village = models.ForeignKey(configm.Village, on_delete=models.SET_NULL, null=True, blank=True)
    ward = models.ForeignKey(configm.Ward, on_delete=models.SET_NULL, null=True, blank=True)
    society = models.ForeignKey(configm.Society, on_delete=models.SET_NULL, null=True, blank=True)
    block = models.ForeignKey(configm.Block, on_delete=models.SET_NULL, null=True, blank=True)
    houses = models.ForeignKey(configm.Houses, on_delete=models.SET_NULL, null=True, blank=True)
    residential_code = models.CharField("Residential ID", max_length=100, null=True)

    def save(self, *args, **kwargs):
        self.residential_code = f"{self.continent.code if self.continent else '00'}-" \
                            f"{self.country.code if self.country else '00'}-" \
                            f"{self.state.code if self.state else '00'}-" \
                            f"{self.city.code if self.city else '00'}-" \
                            f"{self.village.code if self.village else '00'}-" \
                            f"{self.ward.code if self.ward else '00'}-" \
                            f"{self.society.code if self.society else '00'}-" \
                            f"{self.block.name if self.block else '00'}-" \
                            f"{self.houses.code if self.houses else '00'}"
        super().save(*args, **kwargs)

