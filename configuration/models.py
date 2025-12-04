from django.db import models
from django.utils import timezone


# An abstract model mixin that provides is_hidden, on_hold,
# and hold_date fields, along with the automated save logic.
class HoldableMixin(models.Model):
    # --- Fields to be reused ---
    is_hidden = models.BooleanField("hidden", default=False)
    on_hold = models.BooleanField("on hold", default=False)
    hold_date = models.DateField("hold upto", null=True, blank=True)

    # --- Reusable logic ---
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

    class Meta:
        abstract = True

class OrderByMixin(models.Model):
    class Meta:
        abstract = True
        ordering = ["name"]      
          
          

# for example:-
# house: foundation size, material, product usage
# ward: road, gutter, garden, street light
class Flash(OrderByMixin, HoldableMixin):
    CATEGORY_CHOICES = (
        ("ward", "Ward"),
        ("society", "Society"),
        ("floor", "Floor"),
        ("house", "House"),
        ("room", "Room"),
    )
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=100)
    code = models.PositiveIntegerField(unique=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="unique_flash_per_category"
            )
        ]
    def __str__(self):
        return f"{self.name} - {self.code}"
    
# --------------------------------------------------------------------------------
# Residential ->
# --------------------------------------------------------------------------------
class Glob(OrderByMixin, HoldableMixin):
    name = models.CharField(max_length=100, unique=True)
    code = models.PositiveIntegerField(unique=True)
        
    def __str__(self):
        return f"{self.name} - {self.code}"


class Continent(OrderByMixin, HoldableMixin):
    glob = models.ForeignKey(Glob, on_delete=models.CASCADE, related_name="continents")
    name = models.CharField(max_length=100, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Country(OrderByMixin, HoldableMixin):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name="countries")
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


class State(OrderByMixin, HoldableMixin):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
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


class District(OrderByMixin, HoldableMixin):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")
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
    

class Taluka(OrderByMixin, HoldableMixin):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="talukas")
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


class CityVillage(OrderByMixin, HoldableMixin):
    taluka = models.ForeignKey(Taluka, on_delete=models.CASCADE, related_name="city_villages")
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


class Ward(OrderByMixin, HoldableMixin):
    city_village = models.ForeignKey(CityVillage, on_delete=models.CASCADE, related_name="wards")
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["city_village", "name"], name="unique_ward_per_city_village"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class Society(OrderByMixin, HoldableMixin):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="societies")
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Block(OrderByMixin, HoldableMixin):
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="blocks")
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["society", "name"], name="unique_block_per_society"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class Floor(OrderByMixin, HoldableMixin):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="floors")
    no = models.IntegerField(default=0)
    code = models.PositiveIntegerField(unique=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["block", "no"], name="unique_floor_per_block"
            )
        ]

    def __str__(self):
        return f"{self.no} - {self.code}"


class House(OrderByMixin, HoldableMixin):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="houses")
    no = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["floor", "no"], name="unique_house_per_floor"
            )
        ]

    def __str__(self):
        return f"{self.no} - {self.code}"

class RoomType(OrderByMixin, HoldableMixin):
    name = models.CharField(max_length=20)
    is_used = models.BooleanField(default=False)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    
class Room(OrderByMixin, HoldableMixin):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name="rooms_of_room_type")
    no = models.IntegerField()
    code = models.PositiveIntegerField(unique=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["house", "no"], name="unique_room_no_per_house"
            )
        ]

    def __str__(self):
        return f"{self.no} - {self.code}"

 
# class RoomFlash(OrderByMixin, HoldableMixin):
#     name = models.CharField(max_length=20)
#     is_used = models.BooleanField(default=False)
#     code = models.PositiveIntegerField(unique=True)

#     def __str__(self):
#         return f"{self.code} - {self.name}"

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
    user = models.ForeignKey('user_management.CustomUser', on_delete=models.CASCADE, related_name='model_access_permission')
    model = models.ForeignKey(ModelName, on_delete=models.CASCADE)

    can_read = models.BooleanField(default=True)
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
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} For: '{self.user.email}'"


# -------------------------------------------------------------------------------------------------
# Personal ->
# -------------------------------------------------------------------------------------------------
class Religion(OrderByMixin, HoldableMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Sampraday(OrderByMixin, HoldableMixin):
    religion = models.ForeignKey(Religion, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Panth(OrderByMixin, HoldableMixin):
    sampraday = models.ForeignKey(Sampraday, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Awastha(OrderByMixin, HoldableMixin):
    panth = models.ForeignKey(Panth, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Varna(OrderByMixin, HoldableMixin):
    awastha = models.ForeignKey(Awastha, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Caste(OrderByMixin, HoldableMixin):
    varna = models.ForeignKey(Varna, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class SubCaste(OrderByMixin, HoldableMixin):
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Gotra(OrderByMixin, HoldableMixin):
    subcaste = models.ForeignKey(SubCaste, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class SubGotra(OrderByMixin, HoldableMixin):
    gotra = models.ForeignKey(Gotra, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Kul(OrderByMixin, HoldableMixin):
    subgotra = models.ForeignKey(SubGotra, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Vansh(OrderByMixin, HoldableMixin):
    kul = models.ForeignKey(Kul, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Family(OrderByMixin, HoldableMixin):
    vansh = models.ForeignKey(Vansh, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Pidhi(OrderByMixin, HoldableMixin):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


# ----------------------------------------------------------------------------------------------
# Professional ->
# ----------------------------------------------------------------------------------------------
class Section(OrderByMixin, HoldableMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Class(OrderByMixin, HoldableMixin):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfCategory(OrderByMixin, HoldableMixin):
    profclass = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfSubCategory(OrderByMixin, HoldableMixin):
    category = models.ForeignKey(ProfCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    
class Sector(OrderByMixin, HoldableMixin):
    subcategory = models.ForeignKey(ProfSubCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"

class SubSector(OrderByMixin, HoldableMixin):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Department(OrderByMixin, HoldableMixin):
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class SubDepartment(OrderByMixin, HoldableMixin):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Type(OrderByMixin, HoldableMixin):
    subdepartment = models.ForeignKey(SubDepartment, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Brand(OrderByMixin, HoldableMixin):
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Product(OrderByMixin, HoldableMixin):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

# class PostModel(OrderByMixin, HoldableMixin):
#     brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
#     name = models.CharField("Post Model", max_length=200, db_index=True)
#     code = models.PositiveIntegerField(unique=True)

#     def __str__(self):
#         return f"{self.name} - {self.code}"


# Example: (Manager -> Team Lead -> Developer), (Super admin -> Main admin -> etc..)
class Designation(OrderByMixin, HoldableMixin):
    CATEGORY_CHOICES = [
        ('personal', 'Personal'),        
        ('resident', 'Resident'),
        ('professional', 'Professional'),
    ]
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20)
    name = models.CharField(max_length=100)
    code = models.PositiveIntegerField(help_text="Hierarchy level, 1=top", unique=True) # code / Designation number / level / post no 
    reporting_designation = models.ForeignKey(
        "self",
        null=True,
        blank=True, 
        related_name="children",
        on_delete=models.SET_NULL,
        help_text="Parent designation for hierarchy"
    )

    def __str__(self):
        return f"{self.category} - {self.name} (Level {self.code})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="unique_name_per_category"
            )
        ]
    
    # def save(self, *args, **kwargs):
    #     # Auto-set hierarchy level based on parent
    #     if self.post_no != 0 or self.post_no is None:
    #         self.post_no = self.reporting_designation.post_no + 1 if self.reporting_designation else 1
    #     super().save(*args, **kwargs)

import os
from django.db import models

def sample_file_upload_path(instance, filename):
    """
    Store files like:
    sample_files/<category>/<filename>
    """
    category = instance.category.lower()
    return os.path.join('sample_files', category, filename)

class SampleFile(models.Model):
    # CATEGORY_CHOICES = [
    #     ('personal', 'Personal'),
    #     ('residential', 'Residential'),
    #     ('professional', 'Professional'),
    # ]
    # category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    router = models.CharField(max_length=100)
    file = models.FileField(upload_to=sample_file_upload_path, blank=True, null=True)
    
    def __str__(self):
        return f"{self.router} ({self.category})"
    


# ====================================
# flash model
# ====================================

class WardFlash(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="ward_flashes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ward_flashes_of_product")
    value = models.CharField(max_length=255)


class SocietyFlash(models.Model):
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="society_flashes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="society_flashes_of_product")
    value = models.CharField(max_length=255)
    

class BlockFlash(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="block_flashes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="block_flashes_of_product")
    value = models.CharField(max_length=255)
    
    
class FloorFlash(models.Model):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="floor_flashes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="floor_flashes_of_product")
    value = models.CharField(max_length=255)
    


class HouseFlash(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="house_flashes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="house_flashes_of_product")
    value = models.CharField(max_length=255)


class RoomFlash(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="room_flashes")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="room_flashes_of_product")
    value = models.CharField(max_length=255)

