from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

from common.models import AuditMixin
# Create your models here.

class UserRole(AuditMixin):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, contact_no, password=None, **extra_fields):
        if not contact_no:
            raise ValueError("Contact number must be provided")
        
        email = extra_fields.pop("email", None)
        if email:
            email = self.normalize_email(email)

        roles = extra_fields.pop("user_roles", None)

        user = self.model(contact_no=contact_no, **extra_fields)

        if password:
            user.set_password(password)
        user.save()

        if roles:
            if not isinstance(roles, list):
                roles = [roles]
            user.roles.set(roles)


        return user

    def create_superuser(self, contact_no, password=None, **extra_fields):
        role, _ = UserRole.objects.get_or_create(
            name="system_admin",
            display_name="System Admin"
        )
        extra_fields.setdefault("user_roles", [role])
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        return self.create_user(contact_no, password, **extra_fields)


class UserResidentialDetails(AuditMixin):
    nodes = models.JSONField(default=dict, null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.id}"
    


class User(AbstractBaseUser, PermissionsMixin, AuditMixin):
    USER_CATEGORY_CHOICES = [
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
        ('grp_tenant', 'Group Tenant')
    ]
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    contact_no = models.CharField(max_length=20, unique=True)
    roles = models.ManyToManyField(UserRole)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    user_category = models.CharField(choices=USER_CATEGORY_CHOICES, max_length=20, null=True, blank=True)

    current_residential_details = models.ForeignKey(
        UserResidentialDetails, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="users"
    )

    USERNAME_FIELD = 'contact_no'
    REQUIRED_FIELDS = []

    objects = UserManager()

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.full_name} - {self.contact_no}"


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-')
    ]
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    pet_name = models.CharField(max_length=100, blank=True, null=True)
    father_name = models.CharField(max_length=150, blank=True, null=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    expired_date = models.DateField(blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"Profile of {self.user.full_name}"


class DocumentType(AuditMixin):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField()
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.display_name

class UserDocument(AuditMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    document_no = models.CharField(max_length=100, blank=True, null=True)
    document = models.FileField(upload_to='user_documents/', null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.full_name} - {self.document_type.display_name}"

class UserProfessionalDetails(AuditMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='professional_details')
    nodes = models.JSONField(default=dict, null=True, blank=True)

    history = HistoricalRecords()


class UserPersonalDetails(AuditMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personal_details')
    nodes = models.JSONField(default=dict, null=True, blank=True)

    history = HistoricalRecords()


class FamilyType(AuditMixin):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.display_name
    
class RelationType(AuditMixin):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Family(AuditMixin):
    name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.name}"
    

class FamilyMember(AuditMixin):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    self_relation_type = models.ForeignKey(RelationType, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_main_user = models.BooleanField(default=False)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.family.id} - {self.user.full_name}"


class FamilyResident(AuditMixin):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='residents')
    residential_details = models.ForeignKey(UserResidentialDetails, on_delete=models.SET_NULL, null=True, blank=True)
    family_type = models.ForeignKey(FamilyType, on_delete=models.PROTECT)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.family.id} - {self.residential_details}"



class UserRelations(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="from_user")
    relation_type = models.ForeignKey(RelationType, on_delete=models.PROTECT)
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="to_user")

    def __str__(self):
        return f"{self.from_user.full_name} - {self.relation_type.display_name} - {self.to_user.full_name}"

