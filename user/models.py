from django.db import models
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.db.models import Q, F
from phonenumber_field.modelfields import PhoneNumberField
import re
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from decimal import Decimal
from common.models import AuditMixin, SoftDeleteMixin
from configuration.models import Level, Node


# ---------------------------------------------------------------------------
# Helper: build a dash-separated code string from a {level_id: node_id} JSON.
#
# Dict insertion order is PRESERVED — the caller controls the segment order.
# Example: {"1": 2, "3": 11, "5": 32} → "01-05-08" (each segment zero-padded
#          to the level's configured code_digits).
# Returns None if nodes_json is empty or every entry is invalid.
# ---------------------------------------------------------------------------
def _generate_code_from_nodes(mappings_qs):
    if mappings_qs is not None and mappings_qs.exists():
        codes = []
        mappings = mappings_qs.select_related('level', 'node').order_by('level__sort_order')
        for mapping in mappings:
            digits = mapping.level.code_digits if mapping.level.code_digits else 2
            codes.append(str(mapping.node.code).zfill(digits))
        if codes:
            return "-".join(codes)
    return None


class UserRole(AuditMixin):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):

    def get_queryset(self):
        # By default, hide deleted items across the entire User model
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        # Custom method if you actually need to see everything (e.g. for admins)
        return super().get_queryset()

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
        admin_role_obj, created = UserRole.objects.get_or_create(
            name="admin",
            display_name="Admin"
        )
        super_admin_role_obj, created = UserRole.objects.get_or_create(
            name="super_admin",
            display_name="Super Admin",
            parent=admin_role_obj
        )
        extra_fields.setdefault("user_roles", [super_admin_role_obj])
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        return self.create_user(contact_no, password, **extra_fields)


class ResidentialDetails(AuditMixin):
    history = HistoricalRecords()

    @property
    def residential_code(self):
        """Dash-separated code built from node mappings."""
        try:
            qs = self.node_mappings.all() if self.pk else None
        except Exception:
            qs = None
        return _generate_code_from_nodes(qs)

    def __str__(self):
        return f"{self.id}"
    


class User(AbstractBaseUser, PermissionsMixin, AuditMixin, SoftDeleteMixin):
    USER_CATEGORY_CHOICES = [
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
        ('grp_tenant', 'Group Tenant')
    ]
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    contact_no = PhoneNumberField(max_length=50, unique=True)
    roles = models.ManyToManyField(UserRole)
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    user_category = models.CharField(choices=USER_CATEGORY_CHOICES, max_length=20, null=True, blank=True)

    current_residential_details = models.ForeignKey(
        ResidentialDetails, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="users"
    )

    USERNAME_FIELD = 'contact_no'
    REQUIRED_FIELDS = []

    objects = UserManager()
    all_objects = models.Manager()

    history = HistoricalRecords()

    def soft_delete(self, user=None):
        timestamp = int(timezone.now().timestamp())
        post_fix = f"_del_{timestamp}"

        if self.contact_no and not str(self.contact_no).endswith(post_fix):
            self.contact_no = f"{str(self.contact_no)}{post_fix}"
        
        if getattr(self, 'email', None) and not self.email.endswith(post_fix):
            parts = self.email.split('@')
            if len(parts) == 2:
                self.email = f"{parts[0]}{post_fix}@{parts[1]}"
            else:
                self.email = f"{self.email}{post_fix}"

        return super().soft_delete(user)

    def is_admin(self):
        return self.roles.filter(parent__name="admin").exists()
    
    def is_super_admin(self):
        return getattr(self, 'is_superuser', False) or self.roles.filter(name="super_admin").exists()

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
    EDUCATION_CHOICES = [
        ('below_10th', 'Below 10th'),
        ('10th', '10th Pass'),
        ('12th', '12th Pass'),
        ('diploma', 'Diploma'),
        ('graduate', 'Graduate'),
        ('post_graduate', 'Post Graduate'),
        ('doctorate', 'Doctorate'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    pet_name = models.CharField(max_length=100, blank=True, null=True)
    father_name = models.CharField(max_length=150, blank=True, null=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    birth_time = models.TimeField(blank=True, null=True)
    birth_place = models.CharField(max_length=100, blank=True, null=True)
    blood_group = models.CharField(max_length=10, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    # Marriage date — relevant only when marital_status == 'married'
    marriage_date = models.DateField(blank=True, null=True)
    # Education
    education = models.CharField(max_length=50, choices=EDUCATION_CHOICES, blank=True, null=True)
    education_detail = models.CharField(
        max_length=200, blank=True, null=True,
        help_text="Free-text detail, e.g. 'B.Tech - Computer Science from XYZ University'"
    )
    expired_date = models.DateField(blank=True, null=True)
    expired_time = models.TimeField(blank=True, null=True)
    expired_place = models.CharField(max_length=100, blank=True, null=True)
    cremation_place = models.CharField(max_length=100, blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"Profile of {self.user.full_name}"


class DocumentType(AuditMixin):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField()
    is_required = models.BooleanField(default=False)
    regex_pattern = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.display_name

class UserDocument(AuditMixin, SoftDeleteMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    document_no = models.CharField(max_length=100, blank=True, null=True)
    document = models.FileField(upload_to='user_documents/', null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.full_name} - {self.document_type.display_name}"

    def clean(self):
        super().clean()
        if self.document_no and self.document_type and self.document_type.regex_pattern:
            if not re.match(self.document_type.regex_pattern, self.document_no):
                raise ValidationError({
                    'document_no': f"Invalid format for {self.document_type.display_name}. Please enter a valid number."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class BusinessFamily(AuditMixin):
    COMPANY_TYPE_CHOICES = [
        ('headquarter', 'Headquarter'), # Controls the entire organization.
        ('regional_office', 'Regional Office'), # Manages operations for an entire region (multiple cities or states).
        ('branch', 'Branch'), # Serves a specific local area or city.
    ]

    BUSINESS_TYPE_CHOICES = [
        ("private_limited", "Private Limited"),
        ("public_limited", "Public Limited"),
        ("government", "Government"),
        ("ngo", "NGO"),
    ]

    SIZE_CHOICES = [
        ("1-10", "1-10"),
        ("11-50", "11-50"),
        ("51-200", "51-200"),
        ("201-500", "201-500"),
        ("500+", "500+"),
    ]

    role = models.ForeignKey(
        UserRole, 
        on_delete=models.PROTECT, 
        related_name='role_business_families',
        null=True, blank=True
    )
    sub_role = models.ForeignKey(
        UserRole, 
        on_delete=models.PROTECT, 
        related_name='sub_role_business_families',
        null=True, blank=True
    )

    # Business Information
    registration_no = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Government registration number"
    )

    pan_no = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    gstin = models.CharField(max_length=15, unique=True, blank=True, null=True)


    business_type = models.CharField(
        max_length=50,
        choices=BUSINESS_TYPE_CHOICES
    )

    company_size = models.CharField(
        max_length=20,
        choices=SIZE_CHOICES,
        blank=True,
        null=True
    )
    
    email = models.EmailField()
    contact_no = PhoneNumberField(max_length=50, unique=True)
    website = models.URLField(null=True, blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    logo = models.ImageField(upload_to='business_family_logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    priority_score = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    name = models.CharField(max_length=100)
    # NEW: Link to parent company (Headquarter)
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='branches'
    )
    
    # NEW: Optional field to classify
    
    company_type = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES, default='headquarter')
    is_verified = models.BooleanField(default=False)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.id} - {self.name}"


class BusinessOperatingHours(AuditMixin):
    DAY_OF_WEEK_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    business_family = models.ForeignKey(BusinessFamily, on_delete=models.SET_NULL, null=True, blank=True)
    day_of_week = models.CharField(max_length=50, choices=DAY_OF_WEEK_CHOICES)
    open_time = models.TimeField()
    close_time = models.TimeField()

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business_family", "day_of_week"],
                name="uq_boh_business_day",
            ),
            models.CheckConstraint(
                condition=Q(close_time__gt=F("open_time")),
                name="chk_boh_close_gt_open",
            ),
        ]



class BusinessFamilyProfessionalNodeMapping(AuditMixin):
    business_family = models.ForeignKey(
        BusinessFamily, 
        on_delete=models.CASCADE, 
        related_name='professional_node_mappings',
    )
    level = models.ForeignKey('configuration.Level', on_delete=models.CASCADE)
    node = models.ForeignKey('configuration.Node', on_delete=models.PROTECT)

    history = HistoricalRecords()


class UserProfessionalDetails(AuditMixin):
    business_family = models.ForeignKey(BusinessFamily, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='professional_details')
    residential_details = models.ForeignKey(ResidentialDetails, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey('DesignationType', on_delete=models.SET_NULL, null=True, blank=True)
    # Duration of employment / engagement
    joined_date = models.DateField(blank=True, null=True, help_text="Date the person joined this role")
    left_date = models.DateField(blank=True, null=True, help_text="Date the person left (null = currently active)")
    experience = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Human-readable experience summary, e.g. '3 years 2 months'"
    )
    salary = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Salary or compensation amount"
    )
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['business_family', 'user'],
                name='unique_business_professional_user',
                violation_error_message="A professional detail record for this user and business already exists."
            )
        ]

    @property
    def professional_code(self):
        """Dash-separated code built from node mappings."""
        try:
            qs = self.professional_node_mappings.all() if self.pk else None
        except Exception:
            qs = None
        base_code = _generate_code_from_nodes(qs)
        if base_code and self.user_id:
            return f"{base_code}-{self.user_id}"
        return base_code

    def __str__(self):
        company = self.business_family.name if self.business_family else "—"
        return f"{self.user.full_name} @ {company}"


class UserPersonalDetails(AuditMixin):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personal_details')
    is_verified = models.BooleanField(default=False)

    history = HistoricalRecords()

    @property
    def personal_code(self):
        """Dash-separated code built from node mappings."""
        try:
            qs = self.node_mappings.all() if self.pk else None
        except Exception:
            qs = None
        base_code = _generate_code_from_nodes(qs)
        if base_code and self.user_id:
            return f"{base_code}-{self.user_id}"
        return base_code

    def __str__(self):
        return f"PersonalDetails({self.user.full_name})"


class ResidentialType(AuditMixin):
    roles = models.ManyToManyField(UserRole)
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
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('in_laws', 'In Laws'),
        ('maternal', 'Maternal'),
    ]
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    post_no = models.PositiveBigIntegerField(null=True, blank=True)
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class DesignationType(AuditMixin):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    post_no = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['post_no']

    def __str__(self):
        return self.display_name


class Family(AuditMixin):
    name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.name}"
    

class FamilyMember(AuditMixin):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    self_relation_type = models.ForeignKey(RelationType, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_no = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_main_user = models.BooleanField(default=False)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.family.id} - {self.user.full_name}"



class BusinessFamilyMember(AuditMixin):
    business_family = models.ForeignKey(BusinessFamily, on_delete=models.CASCADE, related_name='members')
    self_designation_type = models.ForeignKey(DesignationType, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_no = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['business_family', 'user'],
                name='unique_business_family_member',
                violation_error_message="This user is already a member of this business family."
            )
        ]

    def __str__(self):
        return f"{self.business_family.id} - {self.user.full_name}"
    

class ResidentMapping(AuditMixin):
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='residents')
    business_family = models.ForeignKey(BusinessFamily, on_delete=models.SET_NULL, null=True, blank=True, related_name='residents')
    residential_details = models.ForeignKey(ResidentialDetails, on_delete=models.SET_NULL, null=True, blank=True)
    residential_type = models.ForeignKey(ResidentialType, on_delete=models.PROTECT)
    # Duration of stay at this address
    stay_from = models.DateField(
        blank=True, null=True,
        help_text="Date the family moved in / association started"
    )
    stay_to = models.DateField(
        blank=True, null=True,
        help_text="Date the family moved out (null = currently residing)"
    )
    is_current = models.BooleanField(
        default=True,
        help_text="True when this is the active / ongoing address for this type"
    )

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['family', 'residential_details'],
                name='unique_family_residential_details',
                violation_error_message="This family is already mapped to this residential details."
            ),
            models.UniqueConstraint(
                fields=['business_family', 'residential_details'],
                name='unique_business_residential_details',
                violation_error_message="This business is already mapped to this residential details."
            ),
            models.UniqueConstraint(
                fields=['residential_details', 'residential_type'],
                name='unique_resident_residential_type',
                violation_error_message="A record with this residential details and family type already exists."
            )
        ]

    def __str__(self):
        stay = f" ({self.stay_from} → {self.stay_to or 'present'})" if self.stay_from else ""
        return f"{self.residential_details}{stay}"
    



class UserRelations(AuditMixin):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="from_user")
    relation_type = models.ForeignKey(RelationType, on_delete=models.PROTECT)
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="to_user")

    def __str__(self):
        return f"{self.from_user.full_name} - {self.relation_type.display_name} - {self.to_user.full_name}"


class ResidentialNodeMapping(AuditMixin):
    residential_detail = models.ForeignKey('ResidentialDetails', on_delete=models.CASCADE, related_name='node_mappings')
    level = models.ForeignKey('configuration.Level', on_delete=models.CASCADE)
    node = models.ForeignKey('configuration.Node', on_delete=models.PROTECT)

    history = HistoricalRecords()

class PersonalNodeMapping(AuditMixin):
    personal_detail = models.ForeignKey('UserPersonalDetails', on_delete=models.CASCADE, related_name='node_mappings')
    level = models.ForeignKey('configuration.Level', on_delete=models.CASCADE)
    node = models.ForeignKey('configuration.Node', on_delete=models.PROTECT)

    history = HistoricalRecords()

class ProfessionalPersonalNodeMapping(AuditMixin):
    professional_detail = models.ForeignKey('UserProfessionalDetails', on_delete=models.CASCADE, related_name='personal_node_mappings')
    level = models.ForeignKey('configuration.Level', on_delete=models.CASCADE)
    node = models.ForeignKey('configuration.Node', on_delete=models.PROTECT)

    history = HistoricalRecords()

class ProfessionalNodeMapping(AuditMixin):
    professional_detail = models.ForeignKey('UserProfessionalDetails', on_delete=models.CASCADE, related_name='professional_node_mappings')
    level = models.ForeignKey('configuration.Level', on_delete=models.CASCADE)
    node = models.ForeignKey('configuration.Node', on_delete=models.PROTECT)

    history = HistoricalRecords()


# =====================================================
# Admin assignments
# =====================================================

class AdminResidentialNodeAssignment(AuditMixin):
    """
    Assigns specific hierarchical nodes (and their corresponding levels) to an Admin.
    This is used for Row-Level Security so the admin only sees data falling under this node.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='node_assignments')
    level = models.ForeignKey(
        'configuration.Level', 
        on_delete=models.CASCADE, 
        related_name='assigned_admins'
    )
    node = models.ForeignKey(
        'configuration.Node', 
        on_delete=models.CASCADE, 
        related_name='assigned_admins'
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='assigned_admins'
    )
    is_active = models.BooleanField(default=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'level', 'node'], 
                name='unique_admin_node_assignment'
            )
        ]
