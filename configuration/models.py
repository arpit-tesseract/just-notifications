from django.db import models
# from datetime import timezone
from django.utils import timezone
# from user_management.models import CustomUser
# from django.contrib.postgres.fields import JSONField

from django.utils import timezone

# class HoldableMixin:
#     def save(self, *args, **kwargs):
#         if self.on_hold == False:
#             self.hold_date = None
        
#         if self.hold_date:
#             if self.hold_date >= timezone.now().date():
#                 self.on_hold = True
#             else:
#                 self.on_hold = False
#                 self.hold_date = None
#         else:
#             self.on_hold = False
            
#         super().save(*args, **kwargs)


# An abstract model mixin that provides is_hidden, on_hold,
# and hold_date fields, along with the automated save logic.
class HoldableMixin(models.Model):
    # --- Fields to be reused ---
    is_hidden = models.BooleanField("hidden", default=False)
    on_hold = models.BooleanField("on hold", default=False)
    hold_date = models.DateField("hold upto", null=True, blank=True)

    # --- Reusable logic ---
    def save(self, *args, **kwargs):
        today = timezone.now().date()
        
        # This logic is cleaner: the hold_date drives the on_hold status.
        if self.hold_date and self.hold_date >= today:
            # Date is set for today or the future, so it MUST be on hold.
            self.on_hold = True
        else:
            # Date is either in the past or not set (None).
            self.on_hold = False
            if self.hold_date:
                # Clear any date that is in the past.
                self.hold_date = None
                
        super().save(*args, **kwargs)

    # --- The most important part! ---
    class Meta:
        abstract = True        
# --------------------------------------------------------------------------------
# Residential ->
# --------------------------------------------------------------------------------
class Glob(HoldableMixin):
    name = models.CharField(max_length=100, unique=True)
    code = models.PositiveIntegerField(unique=True)
        
    def __str__(self):
        return f"{self.name} - {self.code}"


class Continent(HoldableMixin):
    glob = models.ForeignKey(Glob, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Country(HoldableMixin):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["continent", "name"], 
                name="unique_country_per_continent",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class State(HoldableMixin):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"], name="unique_state_per_country"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class District(HoldableMixin):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["state", "name"], name="unique_district_per_state"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Taluka(HoldableMixin):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["district", "name"], name="unique_taluka_per_district"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class CityVillage(HoldableMixin):
    taluka = models.ForeignKey(Taluka, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["taluka", "name"], name="unique_city_village_per_taluka"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class Ward(HoldableMixin):
    city_village = models.ForeignKey(CityVillage, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["city_village", "code"], name="unique_ward_per_city_village"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"
    


class RoomFlash(HoldableMixin):
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.code} - {self.name}"


# -------------------------------------------------------------------------------------------------
# Model & Record Rule Access
# -------------------------------------------------------------------------------------------------
class ModelName(models.Model):
    app_label = models.CharField(max_length=100)  # e.g. "yourapp"
    model = models.CharField(max_length=100)      # e.g. "City"
    technical_name = models.CharField(max_length=200, unique=True)  # "yourapp.City"
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.technical_name
    
class ModelAccess(models.Model):
    user = models.ForeignKey('user_management.CustomUser', on_delete=models.CASCADE, related_name='model_access_rule')
    model = models.ForeignKey(ModelName, on_delete=models.CASCADE, related_name='model_access_rule')

    can_read = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "model")

    def __str__(self):
        return f"{self.user} → {self.model}"
    
class RecordRule(models.Model):
    user = models.ForeignKey('user_management.CustomUser', on_delete=models.CASCADE, related_name="record_rules")
    model = models.ForeignKey(ModelName, on_delete=models.CASCADE, related_name="record_rules")

    name = models.CharField(max_length=100, null=True, blank=True)
    domain_filter = models.JSONField(default=dict)  # e.g. {"state__name": "Gujarat"}

    can_read = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.model})"


# -------------------------------------------------------------------------------------------------
# Personal ->
# -------------------------------------------------------------------------------------------------
class Religion(HoldableMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Sampraday(HoldableMixin):
    religion = models.ForeignKey(Religion, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Panth(HoldableMixin):
    sampraday = models.ForeignKey(Sampraday, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Varna(HoldableMixin):
    panth = models.ForeignKey(Panth, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Caste(HoldableMixin):
    varna = models.ForeignKey(Varna, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class SubCaste(HoldableMixin):
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Gotra(HoldableMixin):
    subcaste = models.ForeignKey(SubCaste, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class SubGotra(HoldableMixin):
    gotra = models.ForeignKey(Gotra, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Kul(HoldableMixin):
    subgotra = models.ForeignKey(SubGotra, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Vansh(HoldableMixin):
    kul = models.ForeignKey(Kul, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Family(HoldableMixin):
    vansh = models.ForeignKey(Vansh, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Pidhi(HoldableMixin):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


# ----------------------------------------------------------------------------------------------
# Professional ->
# ----------------------------------------------------------------------------------------------
class Section(HoldableMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Class(HoldableMixin):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfCategory(HoldableMixin):
    profclass = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfSubCategory(HoldableMixin):
    category = models.ForeignKey(ProfCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    
class Sector(HoldableMixin):
    subcategory = models.ForeignKey(ProfSubCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"

class SubSector(HoldableMixin):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Department(HoldableMixin):
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class SubDepartment(HoldableMixin):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Type(HoldableMixin):
    subdepartment = models.ForeignKey(SubDepartment, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Brand(HoldableMixin):
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

# class PostModel(HoldableMixin):
#     brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
#     name = models.CharField("Post Model", max_length=200, db_index=True)
#     code = models.PositiveIntegerField(unique=True)

#     def __str__(self):
#         return f"{self.name} - {self.code}"


# Example: (Manager -> Team Lead -> Developer), (Super admin -> Main admin -> etc..)
class Designation(HoldableMixin):
    category_choices = [
        ('personal', 'Personal'),
        ('professional', 'Professional'),
        ('residential', 'Residential'),        
    ]
    category = models.CharField("Designation Category",choices=category_choices, max_length=20)
    name = models.CharField(max_length=100, unique=True)
    code = models.PositiveIntegerField(unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    reporting_designation = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
        help_text="Parent designation for hierarchy"
    )
    post_no = models.PositiveIntegerField(default=0, help_text="Hierarchy level, 0=top") # Designation number / level / post no


    def __str__(self):
        return f"{self.display_name} (Level {self.post_no})"
    
    def save(self, *args, **kwargs):
        # Auto-set hierarchy level based on parent
        self.post_no = self.reporting_designation.post_no + 1 if self.reporting_designation else 0
        super().save(*args, **kwargs)