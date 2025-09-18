from django.db import models
# from datetime import timezone
from django.utils import timezone
# from user_management.models import CustomUser
# from django.contrib.postgres.fields import JSONField


# --------------------------------------------------------------------------------
# Residential ->
# --------------------------------------------------------------------------------
class Glob(models.Model):
    name = models.CharField("Glob Name", max_length=100, unique=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.name} - {self.code}"


class Continent(models.Model):
    glob = models.ForeignKey(Glob, on_delete=models.CASCADE)
    name = models.CharField("Continent", max_length=100, unique=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.code}"


class Country(models.Model):
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    name = models.CharField("Country", max_length=100)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["continent", "name"], name="unique_country_per_continent"
            )
        ]
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.continent.code} - {self.name} - {self.code}"


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField("State", max_length=200)
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

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.country.code} - {self.name} - {self.code}"


class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField("District", max_length=200)
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

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.state.code} - {self.name} - {self.code}"
    

class Taluka(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField("Taluka", max_length=200)
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

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.district.code} - {self.name} - {self.code}"


class CityVillage(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField("City", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["district", "name"], name="unique_city_per_district"
            )
        ]

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.district.code} - {self.name} - {self.code}"


class Ward(models.Model):
    city_village = models.ForeignKey(CityVillage, on_delete=models.CASCADE, null=True)
    # name = models.CharField("Ward", max_length=200)
    code = models.CharField("Code", max_length=5)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["city_village", "code"], name="unique_ward_per_city_village"
            )
        ]
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.city_village} - {self.code}"
    
    
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
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

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

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

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
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.block} - {self.code}"


class RoomFlash(models.Model):
    name = models.CharField("Room Name", max_length=20)
    code = models.CharField("Number", max_length=10)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

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
class Religion(models.Model):
    name = models.CharField("Religion", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Sampraday(models.Model):
    religion = models.ForeignKey(Religion, on_delete=models.CASCADE)
    name = models.CharField("Sampraday", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)


    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Panth(models.Model):
    sampraday = models.ForeignKey(Sampraday, on_delete=models.CASCADE)
    name = models.CharField("Panth", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Varna(models.Model):
    panth = models.ForeignKey(Panth, on_delete=models.CASCADE)
    name = models.CharField("Varna", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Caste(models.Model):
    varna = models.ForeignKey(Varna, on_delete=models.CASCADE)
    name = models.CharField("Caste", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SubCaste(models.Model):
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE)
    name = models.CharField("Sub-Caste", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Gotra(models.Model):
    subcaste = models.ForeignKey(SubCaste, on_delete=models.CASCADE)
    name = models.CharField("Gotra", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SubGotra(models.Model):
    gotra = models.ForeignKey(Gotra, on_delete=models.CASCADE)
    name = models.CharField("Sub-Gotra", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Kul(models.Model):
    subgotra = models.ForeignKey(SubGotra, on_delete=models.CASCADE)
    name = models.CharField("Kul", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Vansh(models.Model):
    kul = models.ForeignKey(Kul, on_delete=models.CASCADE)
    name = models.CharField("Vansh", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

class Family(models.Model):
    vansh = models.ForeignKey(Vansh, on_delete=models.CASCADE)
    name = models.CharField("Family", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Pidhi(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    name = models.CharField("Pidhi", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------------------------------
# Professional ->
# ----------------------------------------------------------------------------------------------
class Section(models.Model):
    name = models.CharField("Section", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Class(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.CharField("Class", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProfCategory(models.Model):
    profclass = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField("Category", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProfSubCategory(models.Model):
    category = models.ForeignKey(ProfCategory, on_delete=models.CASCADE)
    name = models.CharField("Sub Category", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Sector(models.Model):
    subcategory = models.ForeignKey(ProfSubCategory, on_delete=models.CASCADE)
    name = models.CharField("Sector", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SubSector(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE)
    name = models.CharField("Sub Sector", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Department(models.Model):
    subsector = models.ForeignKey(SubSector, on_delete=models.CASCADE)
    name = models.CharField("Department", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SubDepartment(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField("Sub Department", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Type(models.Model):
    subdepartment = models.ForeignKey(SubDepartment, on_delete=models.CASCADE)
    name = models.CharField("Type", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Brand(models.Model):
    type = models.ForeignKey(Type, on_delete=models.CASCADE)
    name = models.CharField("Brand", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class PostModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField("Post Model", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

