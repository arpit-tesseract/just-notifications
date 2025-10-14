from django.db import models
# from datetime import timezone
from django.utils import timezone
# from user_management.models import CustomUser
# from django.contrib.postgres.fields import JSONField

from django.utils import timezone

class HoldableSaveMixin:
    def save(self, *args, **kwargs):
        if self.on_hold == False:
            self.hold_date = None
        
        if self.hold_date:
            if self.hold_date >= timezone.now().date():
                self.on_hold = True
            else:
                self.on_hold = False
                self.hold_date = None
        else:
            self.on_hold = False
            
        super().save(*args, **kwargs)
        
# --------------------------------------------------------------------------------
# Residential ->
# --------------------------------------------------------------------------------
class Glob(HoldableSaveMixin, models.Model):
    name = models.CharField("Glob Name", max_length=100, unique=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
        
    def __str__(self):
        return f"{self.name} - {self.code}"


class Continent(HoldableSaveMixin, models.Model):
    glob = models.ForeignKey(Glob, on_delete=models.CASCADE)
    name = models.CharField("Continent", max_length=100, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Country(HoldableSaveMixin, models.Model):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    name = models.CharField("Country", max_length=100, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["continent", "name"], 
                name="unique_country_per_continent",
            )
        ]

    def __str__(self):
        return f"{self.continent.code} - {self.name} - {self.code}"


class State(HoldableSaveMixin, models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField("State", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"], name="unique_state_per_country"
            )
        ]

    def __str__(self):
        return f"{self.country.code} - {self.name} - {self.code}"


class District(HoldableSaveMixin, models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField("District", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["state", "name"], name="unique_district_per_state"
            )
        ]

    def __str__(self):
        return f"{self.state.code} - {self.name} - {self.code}"
    

class Taluka(HoldableSaveMixin, models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField("Taluka", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["district", "name"], name="unique_taluka_per_district"
            )
        ]

    def __str__(self):
        return f"{self.district.code} - {self.name} - {self.code}"


class CityVillage(HoldableSaveMixin, models.Model):
    taluka = models.ForeignKey(Taluka, on_delete=models.CASCADE)
    name = models.CharField("City", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["taluka", "name"], name="unique_city_per_taluka"
            )
        ]

    def __str__(self):
        return f"{self.taluka.code} - {self.name} - {self.code}"


class Ward(HoldableSaveMixin, models.Model):
    city_village = models.ForeignKey(CityVillage, on_delete=models.CASCADE, null=True)
    name = models.CharField("Ward", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["city_village", "code"], name="unique_ward_per_city_village"
            )
        ]

    def __str__(self):
        return f"{self.city_village} - {self.code}"
    
"""    
class Society(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    name = models.CharField("Society", max_length=200)
    code = models.CharField("Code", max_length=10, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ward", "name"], name="unique_society_per_ward"
            )
        ]
    
    

    def __str__(self):
        return f"{self.ward} - {self.name} - {self.code}"


class Block(models.Model):
    society = models.ForeignKey(Society, on_delete=models.CASCADE)
    name = models.CharField("Block", max_length=20)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["society", "name"], name="unique_block_per_society"
            )
        ]

    

    def __str__(self):
        return f"{self.society} - {self.name}"
    
    
class Floor(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    code = models.CharField("Floor Code", max_length=5)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["block", "code"], name="unique_floor_per_block"
            )
        ]

    

    def __str__(self):
        return f"{self.block} - {self.name}"


class Houses(models.Model):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)
    code = models.CharField("House Code")
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["floor", "code"], name="unique_house_per_floor"
            )
        ]
    
    

    def __str__(self):
        return f"{self.block} - {self.code}"
"""

class RoomFlash(HoldableSaveMixin, models.Model):
    name = models.CharField("Room Name", max_length=20)
    code = models.CharField("Number", max_length=10)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

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
class Religion(HoldableSaveMixin, models.Model):
    name = models.CharField("Religion", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name


class Sampraday(HoldableSaveMixin, models.Model):
    religion = models.ForeignKey(Religion, on_delete=models.CASCADE)
    name = models.CharField("Sampraday", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)   

    def __str__(self):
        return self.name


class Panth(HoldableSaveMixin, models.Model):
    sampraday = models.ForeignKey(Sampraday, on_delete=models.CASCADE)
    name = models.CharField("Panth", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name


class Varna(HoldableSaveMixin, models.Model):
    panth = models.ForeignKey(Panth, on_delete=models.CASCADE)
    name = models.CharField("Varna", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name


class Caste(HoldableSaveMixin, models.Model):
    varna = models.ForeignKey(Varna, on_delete=models.CASCADE)
    name = models.CharField("Caste", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True) 

    def __str__(self):
        return self.name


class SubCaste(HoldableSaveMixin, models.Model):
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE)
    name = models.CharField("Sub-Caste", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)  

    def __str__(self):
        return self.name


class Gotra(HoldableSaveMixin, models.Model):
    subcaste = models.ForeignKey(SubCaste, on_delete=models.CASCADE)
    name = models.CharField("Gotra", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name


class SubGotra(HoldableSaveMixin, models.Model):
    gotra = models.ForeignKey(Gotra, on_delete=models.CASCADE)
    name = models.CharField("Sub-Gotra", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)  

    def __str__(self):
        
        
        
        
        return self.name


class Kul(HoldableSaveMixin, models.Model):
    subgotra = models.ForeignKey(SubGotra, on_delete=models.CASCADE)
    name = models.CharField("Kul", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name
    

class Vansh(HoldableSaveMixin, models.Model):
    kul = models.ForeignKey(Kul, on_delete=models.CASCADE)
    name = models.CharField("Vansh", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)  

    def __str__(self):
        return self.name
    

class Family(HoldableSaveMixin, models.Model):
    vansh = models.ForeignKey(Vansh, on_delete=models.CASCADE)
    name = models.CharField("Family", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name

class Pidhi(HoldableSaveMixin, models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField("Pidhi", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)   

    def __str__(self):
        return self.name

# Defines a type of relation like Father-1, Mother-2, Son-3, Friend, etc.
# class RelationType(models.Model): # Use designation model....
#     name = models.CharField("Relation", max_length=100, unique=True) # e.g. Father, Mother, Friend
#     display_name = models.CharField("Display Name", max_length=100, unique=True)
#     post_no = models.IntegerField("Post No")
    
#     def __str__(self):
#         return self.name



# Example: (Manager -> Team Lead -> Developer), (Super admin -> Main admin -> etc..)
class Designation(models.Model):
    category_choices = [
        ('personal', 'Personal'),
        ('professional', 'Professional'),
        ('residential', 'Residential'),        
    ]
    category = models.CharField("Designation Category",choices=category_choices, max_length=20)
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    reporting_designation = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.SET_NULL,
        help_text="Parent designation for hierarchy"
    )
    designation_no = models.PositiveIntegerField(default=0, help_text="Hierarchy level, 0=top") # Designation number / level / post no
    
    def __str__(self):
        return f"{self.name} (Level {self.designation_no})"
    
    def save(self, *args, **kwargs):
        # Auto-set hierarchy level based on parent
        self.level = self.reporting_designation.designation_no + 1 if self.reporting_designation else 0
        super().save(*args, **kwargs)


# ----------------------------------------------------------------------------------------------
# Professional ->
# ----------------------------------------------------------------------------------------------
class Section(HoldableSaveMixin, models.Model):
    name = models.CharField("Section", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)    

    def __str__(self):
        return self.name


class Class(HoldableSaveMixin, models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.CharField("Class", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)    

    def __str__(self):
        return self.name


class ProfCategory(HoldableSaveMixin, models.Model):
    profclass = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField("Category", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)    

    def __str__(self):
        return self.name


class ProfSubCategory(HoldableSaveMixin, models.Model):
    category = models.ForeignKey(ProfCategory, on_delete=models.CASCADE)
    name = models.CharField("Sub Category", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)    

    def __str__(self):
        return self.name
    
class Sector(HoldableSaveMixin, models.Model):
    subcategory = models.ForeignKey(ProfSubCategory, on_delete=models.CASCADE)
    name = models.CharField("Sector", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)    

    def __str__(self):
        return self.name

class SubSector(HoldableSaveMixin, models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    name = models.CharField("Sub Sector", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name

class Department(HoldableSaveMixin, models.Model):
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE)
    name = models.CharField("Department", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name

class SubDepartment(HoldableSaveMixin, models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField("Sub Department", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)  

    def __str__(self):
        return self.name


class Type(HoldableSaveMixin, models.Model):
    subdepartment = models.ForeignKey(SubDepartment, on_delete=models.CASCADE)
    name = models.CharField("Type", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True) 

    def __str__(self):
        return self.name

class Brand(HoldableSaveMixin, models.Model):
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    name = models.CharField("Brand", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def __str__(self):
        return self.name

class PostModel(HoldableSaveMixin, models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField("Post Model", max_length=200, db_index=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)   

    def __str__(self):
        return self.name

# Current / Owner / Permanent / Native / InLaws(Girl / Boy) / Maternal / Business
class RelationTypes(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=5, unique=True)
    
    def __str__(self):
        return self.display_name