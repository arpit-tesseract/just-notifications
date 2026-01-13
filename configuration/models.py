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
    time_stamp = models.DateTimeField(auto_now_add=True)

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
    
    parent_field_name = None
    
    def _get_code(self):
        return get_two_digit(self.code) if self.code else 00 
    
    # def _get_code_chain(self):
    #     current_code = get_two_digit(self.code)
        
    #     if not self.parent_field_name:
    #         return current_code
        
    #     parent = getattr(self, self.parent_field_name)
    #     # Check if parent exists
    #     if parent:
    #         return f"{parent._get_code_chain()}{current_code}"
        
    #     # Fallback if parent is a plain model
    #     return current_code
    
    def get_formatted_code(self):
        current_code = self._get_code()
        
        # Check if parent field name exists
        if not self.parent_field_name:
            return current_code
        
        parent = getattr(self, self.parent_field_name)  
        field = self._meta.get_field(self.parent_field_name)
        related_name = field.remote_field.get_accessor_name()
        
        # Count siblings
        sibling_count = getattr(parent, related_name).count()
        
        return f"{current_code}/{get_two_digit(sibling_count)}"
    
    
    # def get_formatted_code(self):
    #     # 1. Build the full hierarchy code (e.g., 010205...)
    #     code_chain = self._get_code_chain()
        
    #     # 2. If root, return just the code
    #     if not self.parent_field_name:
    #         return code_chain
        
    #     # 3. Calculate sibling count dynamically
    #     parent = getattr(self, self.parent_field_name)
        
    #     # Introspect the model to find the 'related_name' used by the parent
    #     # This automatically finds 'continents', 'countries', 'states', etc.
    #     field = self._meta.get_field(self.parent_field_name)
    #     related_name = field.remote_field.get_accessor_name()
        
    #     # Count siblings
    #     sibling_count = getattr(parent, related_name).count()
        
    #     return f"{code_chain}/{get_two_digit(sibling_count)}"
    
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
    
    # def get_formatted_code(self):
    #     return f"{get_two_digit(self.code)}"
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Continent(OrderByMixin, CommonFieldMixin):
    glob = models.ForeignKey(Glob, on_delete=models.CASCADE, related_name="continents")
    name = models.CharField(max_length=100, db_index=True)

    parent_field_name = "glob"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["glob", "name"], 
                name="unique_continent_per_glob",
            )
        ]
        ordering = ['glob__code', 'code']
    # def get_formatted_code(self):
    #     continent_count = self.glob.continents.count()
    #     return f"({get_two_digit(self.code)}/{get_two_digit(continent_count)})"
    
    # def get_formatted_code(self):
    #     continent_count = self.glob.continents.count()
    #     formatted_code = f"{get_two_digit(self.glob.code)}"\
    #                      f"{get_two_digit(self.code)}"\
    #                      f"/{get_two_digit(continent_count)}"
    #     return formatted_code
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Country(OrderByMixin, CommonFieldMixin):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name="countries")
    name = models.CharField(max_length=100, db_index=True)

    parent_field_name = "continent"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["continent", "name"], 
                name="unique_country_per_continent",
            )
        ]
        ordering = [
            'continent__glob__code', 
            'continent__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class State(OrderByMixin, CommonFieldMixin):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "country"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"], name="unique_state_per_country"
            )
        ]
        ordering = [
            'country__continent__glob__code', 
            'country__continent__code', 
            'country__code', 
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class District(OrderByMixin, CommonFieldMixin):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="districts")
    name = models.CharField(max_length=200, db_index=True)

    parent_field_name = "state"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["state", "name"], name="unique_district_per_state"
            )
        ]
        ordering = [
            'state__country__continent__glob__code',
            'state__country__continent__code',
            'state__country__code',
            'state__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Taluka(OrderByMixin, CommonFieldMixin):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="talukas")
    name = models.CharField(max_length=200, db_index=True)

    parent_field_name = "district"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["district", "name"], name="unique_taluka_per_district"
            )
        ]
        ordering = [
            'district__state__country__continent__glob__code',
            'district__state__country__continent__code',
            'district__state__country__code',
            'district__state__code',
            'district__code',
            'code'
        ]
        
    def __str__(self):
        return f"{self.name} - {self.code}"


class CityVillage(OrderByMixin, CommonFieldMixin):
    taluka = models.ForeignKey(Taluka, on_delete=models.CASCADE, related_name="city_villages")
    name = models.CharField(max_length=200, db_index=True)

    parent_field_name = "taluka"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["taluka", "name"], name="unique_city_village_per_taluka"
            )
        ]
        ordering = [
            'taluka__district__state__country__continent__glob__code',
            'taluka__district__state__country__continent__code',
            'taluka__district__state__country__code',
            'taluka__district__state__code',
            'taluka__district__code',
            'taluka__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Ward(OrderByMixin, CommonFieldMixin):
    city_village = models.ForeignKey(CityVillage, on_delete=models.CASCADE, related_name="wards")
    name = models.CharField(max_length=200, db_index=True)

    parent_field_name = "city_village"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["city_village", "name"], name="unique_ward_per_city_village"
            )
        ]
        ordering = [
            'city_village__taluka__district__state__country__continent__glob__code',
            'city_village__taluka__district__state__country__continent__code',
            'city_village__taluka__district__state__country__code',
            'city_village__taluka__district__state__code',
            'city_village__taluka__district__code',
            'city_village__taluka__code',
            'city_village__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Society(OrderByMixin, CommonFieldMixin):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="societies")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "ward"
    class Meta:
        ordering = [
            'ward__city_village__taluka__district__state__country__continent__glob__code',
            'ward__city_village__taluka__district__state__country__continent__code',
            'ward__city_village__taluka__district__state__country__code',
            'ward__city_village__taluka__district__state__code',
            'ward__city_village__taluka__district__code',
            'ward__city_village__taluka__code',
            'ward__city_village__code',
            'ward__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class Block(OrderByMixin, CommonFieldMixin):
    society = models.ForeignKey(Society, on_delete=models.CASCADE, related_name="blocks")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "society"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["society", "name"], name="unique_block_per_society"
            )
        ]
        ordering = [
            'society__ward__city_village__taluka__district__state__country__continent__glob__code',
            'society__ward__city_village__taluka__district__state__country__continent__code',
            'society__ward__city_village__taluka__district__state__country__code',
            'society__ward__city_village__taluka__district__state__code',
            'society__ward__city_village__taluka__district__code',
            'society__ward__city_village__taluka__code',
            'society__ward__city_village__code',
            'society__ward__code',
            'society__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Floor(OrderByMixin, CommonFieldMixin):
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="floors")
    no = models.IntegerField(default=0)
    
    parent_field_name = "block"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["block", "no"], name="unique_floor_per_block"
            )
        ]
        ordering = [
            'block__society__ward__city_village__taluka__district__state__country__continent__glob__code',
            'block__society__ward__city_village__taluka__district__state__country__continent__code',
            'block__society__ward__city_village__taluka__district__state__country__code',
            'block__society__ward__city_village__taluka__district__state__code',
            'block__society__ward__city_village__taluka__district__code',
            'block__society__ward__city_village__taluka__code',
            'block__society__ward__city_village__code',
            'block__society__ward__code',
            'block__society__code',
            'block__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.no} - {self.code}"


class House(OrderByMixin, CommonFieldMixin):
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name="houses")
    no = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "floor"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["floor", "no"], name="unique_house_per_floor"
            )
        ]
        ordering = [
            'floor__block__society__ward__city_village__taluka__district__state__country__continent__glob__code',
            'floor__block__society__ward__city_village__taluka__district__state__country__continent__code',
            'floor__block__society__ward__city_village__taluka__district__state__country__code',
            'floor__block__society__ward__city_village__taluka__district__state__code',
            'floor__block__society__ward__city_village__taluka__district__code',
            'floor__block__society__ward__city_village__taluka__code',
            'floor__block__society__ward__city_village__code',
            'floor__block__society__ward__code',
            'floor__block__society__code',
            'floor__block__code',
            'floor__code',
            'code'
        ]
    
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
    
    parent_field_name = "house"
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["house", "no"], name="unique_room_no_per_house"
            )
        ]
        ordering = [
            'house__floor__block__society__ward__city_village__taluka__district__state__country__continent__glob__code',
            'house__floor__block__society__ward__city_village__taluka__district__state__country__continent__code',
            'house__floor__block__society__ward__city_village__taluka__district__state__country__code',
            'house__floor__block__society__ward__city_village__taluka__district__state__code',
            'house__floor__block__society__ward__city_village__taluka__district__code',
            'house__floor__block__society__ward__city_village__taluka__code',
            'house__floor__block__society__ward__city_village__code',
            'house__floor__block__society__ward__code',
            'house__floor__block__society__code',
            'house__floor__block__code',
            'house__floor__code',
            'house__code',
            'code'
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
class Religion(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    
    class Meta:
        ordering = ['code']


class Sampraday(OrderByMixin, CommonFieldMixin):
    religion = models.ForeignKey(Religion, on_delete=models.CASCADE, related_name="sampradays")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "religion"
    class Meta:
        ordering = ['religion__code', 'code']
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Panth(OrderByMixin, CommonFieldMixin):
    sampraday = models.ForeignKey(Sampraday, on_delete=models.CASCADE, related_name="panths")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "sampraday"
    class Meta:
        ordering = [
            'sampraday__religion__code',
            'sampraday__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"

class Awastha(OrderByMixin, CommonFieldMixin):
    name = models.CharField(max_length=200, unique=True)
    code = models.PositiveIntegerField(unique=True)
    
    def __str__(self):
        return f"{self.name} - {self.code}"

class Varna(OrderByMixin, CommonFieldMixin):
    panth = models.ForeignKey(Panth, on_delete=models.CASCADE, related_name="varnas")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "panth"
    class Meta:
        ordering = [
            'panth__sampraday__religion__code',
            'panth__sampraday__code',
            'panth__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Caste(OrderByMixin, CommonFieldMixin):
    varna = models.ForeignKey(Varna, on_delete=models.CASCADE, related_name="castes")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "varna"
    class Meta:
        ordering = [
            'varna__panth__sampraday__religion__code',
            'varna__panth__sampraday__code',
            'varna__panth__code',
            'varna__code',
            'code'
        ]
        
    def __str__(self):
        return f"{self.name} - {self.code}"


class SubCaste(OrderByMixin, CommonFieldMixin):
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE, related_name="subcastes")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "caste"
    class Meta:
        ordering = [
            'caste__varna__panth__sampraday__religion__code',
            'caste__varna__panth__sampraday__code',
            'caste__varna__panth__code',
            'caste__varna__code',
            'caste__code',
            'code'
        ]
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Gotra(OrderByMixin, CommonFieldMixin):
    subcaste = models.ForeignKey(SubCaste, on_delete=models.CASCADE, related_name="gotras")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "subcaste"
    class Meta:
        ordering = [
            'subcaste__caste__varna__panth__sampraday__religion__code',
            'subcaste__caste__varna__panth__sampraday__code',
            'subcaste__caste__varna__panth__code',
            'subcaste__caste__varna__code',
            'subcaste__caste__code',
            'subcaste__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class SubGotra(OrderByMixin, CommonFieldMixin):
    gotra = models.ForeignKey(Gotra, on_delete=models.CASCADE, related_name="subgotras")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "gotra"
    class Meta:
        ordering = [
            'gotra__subcaste__caste__varna__panth__sampraday__religion__code',
            'gotra__subcaste__caste__varna__panth__sampraday__code',
            'gotra__subcaste__caste__varna__panth__code',
            'gotra__subcaste__caste__varna__code',
            'gotra__subcaste__caste__code',
            'gotra__subcaste__code',
            'gotra__code',
            'code'
        ]
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Kul(OrderByMixin, CommonFieldMixin):
    subgotra = models.ForeignKey(SubGotra, on_delete=models.CASCADE, related_name="kuls")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "subgotra"
    class Meta:
        ordering = [
            'subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__code',
            'subgotra__gotra__subcaste__caste__varna__panth__sampraday__code',
            'subgotra__gotra__subcaste__caste__varna__panth__code',
            'subgotra__gotra__subcaste__caste__varna__code',
            'subgotra__gotra__subcaste__caste__code',
            'subgotra__gotra__subcaste__code',
            'subgotra__gotra__code',
            'subgotra__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Vansh(OrderByMixin, CommonFieldMixin):
    kul = models.ForeignKey(Kul, on_delete=models.CASCADE, related_name="vanshs")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "kul"
    class Meta:
        ordering = [
            'kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__code',
            'kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__code',
            'kul__subgotra__gotra__subcaste__caste__varna__panth__code',
            'kul__subgotra__gotra__subcaste__caste__varna__code',
            'kul__subgotra__gotra__subcaste__caste__code',
            'kul__subgotra__gotra__subcaste__code',
            'kul__subgotra__gotra__code',
            'kul__subgotra__code',
            'kul__code',
            'code'
        ]
  
    def __str__(self):
        return f"{self.name} - {self.code}"
    

class Family(OrderByMixin, CommonFieldMixin):
    vansh = models.ForeignKey(Vansh, on_delete=models.CASCADE, related_name="families")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "vansh"
    class Meta:
        ordering = [
            'vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__religion__code',
            'vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__sampraday__code',
            'vansh__kul__subgotra__gotra__subcaste__caste__varna__panth__code',
            'vansh__kul__subgotra__gotra__subcaste__caste__varna__code',
            'vansh__kul__subgotra__gotra__subcaste__caste__code',
            'vansh__kul__subgotra__gotra__subcaste__code',
            'vansh__kul__subgotra__gotra__code',
            'vansh__kul__subgotra__code',
            'vansh__kul__code',
            'vansh__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"

class Pidhi(OrderByMixin, CommonFieldMixin):
    # family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)

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
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class Class(OrderByMixin, CommonFieldMixin):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="profclasses")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "section"
    class Meta:
        ordering = ['section__code', 'code']
        
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfCategory(OrderByMixin, CommonFieldMixin):
    profclass = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "profclass"
    class Meta:
        ordering = [
            'profclass__section__code',
            'profclass__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"


class ProfSubCategory(OrderByMixin, CommonFieldMixin):
    category = models.ForeignKey(ProfCategory, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "category"
    class Meta:
        ordering = [
            'category__profclass__section__code',
            'category__profclass__code',
            'category__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"
    
class Sector(OrderByMixin, CommonFieldMixin):
    subcategory = models.ForeignKey(ProfSubCategory, on_delete=models.CASCADE, related_name="sectors")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "subcategory"
    class Meta:
        ordering = [
            'subcategory__category__profclass__section__code',
            'subcategory__category__profclass__code',
            'subcategory__category__code',
            'subcategory__code',
            'code'
        ]
    
    def __str__(self):
        return f"{self.name} - {self.code}"

class SubSector(OrderByMixin, CommonFieldMixin):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="subsectors")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "sector"
    class Meta:
        ordering = [
            'sector__subcategory__category__profclass__section__code',
            'sector__subcategory__category__profclass__code',
            'sector__subcategory__category__code',
            'sector__subcategory__code',
            'sector__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"

class Department(OrderByMixin, CommonFieldMixin):
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "subsector"
    class Meta:
        ordering = [
            'subsector__sector__subcategory__category__profclass__section__code',
            'subsector__sector__subcategory__category__profclass__code',
            'subsector__sector__subcategory__category__code',
            'subsector__sector__subcategory__code',
            'subsector__sector__code',
            'subsector__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"

class SubDepartment(OrderByMixin, CommonFieldMixin):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subdepartments")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "department"
    class Meta:
        ordering = [
            'department__subsector__sector__subcategory__category__profclass__section__code',
            'department__subsector__sector__subcategory__category__profclass__code',
            'department__subsector__sector__subcategory__category__code',
            'department__subsector__sector__subcategory__code',
            'department__subsector__sector__code',
            'department__subsector__code',
            'department__code',
            'code'
        ]
  
    def __str__(self):
        return f"{self.name} - {self.code}"


class Type(OrderByMixin, CommonFieldMixin):
    subdepartment = models.ForeignKey(SubDepartment, on_delete=models.CASCADE, related_name="types")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "subdepartment"
    class Meta:
        ordering = [
            'subdepartment__department__subsector__sector__subcategory__category__profclass__section__code',
            'subdepartment__department__subsector__sector__subcategory__category__profclass__code',
            'subdepartment__department__subsector__sector__subcategory__category__code',
            'subdepartment__department__subsector__sector__subcategory__code',
            'subdepartment__department__subsector__sector__code',
            'subdepartment__department__subsector__code',
            'subdepartment__department__code',
            'subdepartment__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"

class Brand(OrderByMixin, CommonFieldMixin):
    type = models.ForeignKey(Type, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=200, db_index=True)
    
    parent_field_name = "type"
    class Meta:
        ordering = [
            'type__subdepartment__department__subsector__sector__subcategory__category__profclass__section__code',
            'type__subdepartment__department__subsector__sector__subcategory__category__profclass__code',
            'type__subdepartment__department__subsector__sector__subcategory__category__code',
            'type__subdepartment__department__subsector__sector__subcategory__code',
            'type__subdepartment__department__subsector__sector__code',
            'type__subdepartment__department__subsector__code',
            'type__subdepartment__department__code',
            'type__subdepartment__code',
            'type__code',
            'code'
        ]

    def __str__(self):
        return f"{self.name} - {self.code}"


class Product(OrderByMixin, HoldableMixin):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, db_index=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Item(OrderByMixin, HoldableMixin):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
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

