from django.db import models
from django.utils import timezone

def get_two_digit(num):
    return str(num).zfill(2)

def get_three_digit(num):
    return str(num).zfill(3)

# An abstract model mixin that provides is_hidden, on_hold,
# and hold_date fields, along with the automated save logic.
class CommonFieldMixin(models.Model):
    # --- Fields to be reused ---
    code = models.PositiveIntegerField(null=True, blank=True)
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
    
    # @staticmethod
    # def get_two_digit(num):
    #     return str(num).zfill(2)

    class Meta:
        abstract = True
        
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
class Flash(OrderByMixin, CommonFieldMixin):
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
class Glob(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=100, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def get_formatted_code(self):
        return f"{get_two_digit(self.code)}"
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Continent(OrderByMixin, CommonFieldMixin):
    glob = models.ForeignKey(Glob, on_delete=models.CASCADE, related_name="continents")
    name = models.CharField(max_length=100, db_index=True)

    def get_formatted_code(self):
        continent_count = self.glob.continents.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(continent_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Country(OrderByMixin, CommonFieldMixin):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name="countries")
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["continent", "name"], 
                name="unique_country_per_continent",
            )
        ]

    def get_formatted_code(self):
        country_count = self.continent.countries.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(country_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class State(OrderByMixin, CommonFieldMixin):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=200, db_index=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"], name="unique_state_per_country"
            )
        ]

    def get_formatted_code(self):
        state_count = self.country.states.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(state_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class District(OrderByMixin, CommonFieldMixin):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=200, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["state", "name"], name="unique_district_per_state"
            )
        ]

    def get_formatted_code(self):
        district_count = self.state.districts.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(district_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Taluka(OrderByMixin, CommonFieldMixin):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="talukas")
    name = models.CharField(max_length=200, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["district", "name"], name="unique_taluka_per_district"
            )
        ]
        
    def get_formatted_code(self):
        taluka_count = self.district.talukas.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(taluka_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class CityVillage(OrderByMixin, CommonFieldMixin):
    taluka = models.ForeignKey(Taluka, on_delete=models.CASCADE, related_name="city_villages")
    name = models.CharField(max_length=200, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["taluka", "name"], name="unique_city_village_per_taluka"
            )
        ]
    
    def get_formatted_code(self):
        city_village_count = self.taluka.city_villages.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(city_village_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class Ward(OrderByMixin, CommonFieldMixin):
    city_village = models.ForeignKey(CityVillage, on_delete=models.CASCADE, related_name="wards")
    name = models.CharField(max_length=200, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["city_village", "name"], name="unique_ward_per_city_village"
            )
        ]
    
    def get_formatted_code(self):
        ward_count = self.city_village.wards.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(ward_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class Society(OrderByMixin, CommonFieldMixin):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="societies")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        society_count = self.ward.societies.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(society_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class Block(OrderByMixin, CommonFieldMixin):
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="blocks")
    name = models.CharField(max_length=200, db_index=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["society", "name"], name="unique_block_per_society"
            )
        ]
    
    def get_formatted_code(self):
        block_count = self.society.blocks.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(block_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class Floor(OrderByMixin, CommonFieldMixin):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="floors")
    no = models.IntegerField(default=0)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["block", "no"], name="unique_floor_per_block"
            )
        ]
    
    def get_formatted_code(self):
        floor_count = self.block.floors.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(floor_count)})"

    def __str__(self):
        return f"{self.no} - {self.code}"


class House(OrderByMixin, CommonFieldMixin):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="houses")
    no = models.CharField(max_length=200, db_index=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["floor", "no"], name="unique_house_per_floor"
            )
        ]
    
    def get_formatted_code(self):
        house_count = self.floor.houses.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(house_count)})"

    def __str__(self):
        return f"{self.no} - {self.code}"

class RoomType(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    code = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"
    
    
class Room(OrderByMixin, CommonFieldMixin):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name="rooms")
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, blank=True, null=True, related_name="rooms_of_room_type")
    no = models.PositiveIntegerField()
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["house", "no"], name="unique_room_no_per_house"
            )
        ]
    
    def get_formatted_code(self):
        room_count = self.house.rooms.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(room_count)})"

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
class Religion(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    
    def get_formatted_code(self):
        return get_two_digit(self.code)


class Sampraday(OrderByMixin, CommonFieldMixin):
    religion = models.ForeignKey(Religion, on_delete=models.CASCADE, related_name="sampradays")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        sampraday_count = self.religion.sampradays.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(sampraday_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class Panth(OrderByMixin, CommonFieldMixin):
    sampraday = models.ForeignKey(Sampraday, on_delete=models.CASCADE, related_name="panths")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        panth_count = self.sampraday.panths.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(panth_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"

class Awastha(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def get_formatted_code(self):
        return get_two_digit(self.code)

    def __str__(self):
        return f"{self.name} - {self.code}"

class Varna(OrderByMixin, CommonFieldMixin):
    panth = models.ForeignKey(Panth, on_delete=models.CASCADE, related_name="varnas")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        varna_count = self.panth.varnas.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(varna_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class Caste(OrderByMixin, CommonFieldMixin):
    varna = models.ForeignKey(Varna, on_delete=models.CASCADE, related_name="castes")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        caste_count = self.varna.castes.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(caste_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class SubCaste(OrderByMixin, CommonFieldMixin):
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE, related_name="subcastes")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        subcaste_count = self.caste.subcastes.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(subcaste_count)})"
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Gotra(OrderByMixin, CommonFieldMixin):
    subcaste = models.ForeignKey(SubCaste, on_delete=models.CASCADE, related_name="gotras")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        gotra_count = self.subcaste.gotras.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(gotra_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class SubGotra(OrderByMixin, CommonFieldMixin):
    gotra = models.ForeignKey(Gotra, on_delete=models.CASCADE, related_name="subgotras")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        subgotra_count = self.gotra.subgotras.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(subgotra_count)})"
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Kul(OrderByMixin, CommonFieldMixin):
    subgotra = models.ForeignKey(SubGotra, on_delete=models.CASCADE, related_name="kuls")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        kul_count = self.subgotra.kuls.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(kul_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Vansh(OrderByMixin, CommonFieldMixin):
    kul = models.ForeignKey(Kul, on_delete=models.CASCADE, related_name="vanshs")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        vansh_count = self.kul.vanshs.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(vansh_count)})"
  
    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Family(OrderByMixin, CommonFieldMixin):
    vansh = models.ForeignKey(Vansh, on_delete=models.CASCADE, related_name="families")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        family_count = self.vansh.families.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(family_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"

class Pidhi(OrderByMixin, CommonFieldMixin):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Calibration(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    unit = models.CharField(max_length=50, null=True, blank=True) # e.g: cm, kg

    def __str__(self):
        return f"{self.name} - {self.code}"
    
    def get_formatted_code(self):
        return get_two_digit(self.code)


# ----------------------------------------------------------------------------------------------
# Professional ->
# ----------------------------------------------------------------------------------------------
class Section(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def get_formatted_code(self):
        return get_two_digit(self.code)
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Class(OrderByMixin, CommonFieldMixin):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="profclasses")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        profclass_count = self.section.profclasses.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(profclass_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfCategory(OrderByMixin, CommonFieldMixin):
    profclass = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        category_count = self.profclass.categories.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(category_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfSubCategory(OrderByMixin, CommonFieldMixin):
    category = models.ForeignKey(ProfCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        subcategory_count = self.category.subcategories.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(subcategory_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    
class Sector(OrderByMixin, CommonFieldMixin):
    subcategory = models.ForeignKey(ProfSubCategory, on_delete=models.CASCADE, related_name="sectors")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        sector_count = self.subcategory.sectors.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(sector_count)})"
    
    def __str__(self):
        return f"{self.name} - {self.code}"

class SubSector(OrderByMixin, CommonFieldMixin):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="subsectors")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        subsector_count = self.sector.subsectors.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(subsector_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"

class Department(OrderByMixin, CommonFieldMixin):
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        department_count = self.subsector.departments.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(department_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"

class SubDepartment(OrderByMixin, CommonFieldMixin):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subdepartments")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        subdepartment_count = self.department.subdepartments.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(subdepartment_count)})"
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Type(OrderByMixin, CommonFieldMixin):
    subdepartment = models.ForeignKey(SubDepartment, on_delete=models.CASCADE, related_name="types")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        type_count = self.subdepartment.types.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(type_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"

class Brand(OrderByMixin, CommonFieldMixin):
    type = models.ForeignKey(Type, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=200, db_index=True)
    
    def get_formatted_code(self):
        brand_count = self.type.brands.count()
        return f"({get_two_digit(self.code)}/{get_two_digit(brand_count)})"

    def __str__(self):
        return f"{self.name} - {self.code}"


class Product(OrderByMixin, HoldableMixin):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)

    def __str__(self):
        return f"{self.name} - {self.code}"

# class PostModel(OrderByMixin, HoldableMixin):
#     brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
#     name = models.CharField("Post Model", max_length=200, db_index=True)
#     code = models.PositiveIntegerField(unique=True)

#     def __str__(self):
#         return f"{self.name} - {self.code}"


# Example: (Manager -> Team Lead -> Developer), (Super admin -> Main admin -> etc..)
class Designation(OrderByMixin, CommonFieldMixin):
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

