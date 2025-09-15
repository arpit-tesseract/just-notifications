from django.db import models
# from datetime import timezone
from django.utils import timezone
# from user_management.models import CustomUser
# from django.contrib.postgres.fields import JSONField

# Create your models here.
class Continent(models.Model):
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

    def save(self, *args, **kwargs):
        if self.hold_date:
            self.on_hold = True
            if self.hold_date < timezone.now().date():
                self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.state.code} - {self.name} - {self.code}"


class City(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField("City", max_length=200)
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
        return f"{self.district.code} - {self.name} - {self.code}"


class Village(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True)
    name = models.CharField("Village", max_length=200)
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
        return f"{self.city or 'No City'} - {self.name} - {self.code}"


class Ward(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE, null=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True)
    # name = models.CharField("Ward", max_length=200)
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
        return f"{self.village} - {self.code}"
    
class Society(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE)
    name = models.CharField("Society", max_length=200)
    code = models.CharField("Code", max_length=10, unique=True)
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
        return f"{self.ward} - {self.name} - {self.code}"


class Block(models.Model):
    society = models.ForeignKey(Society, on_delete=models.CASCADE)
    name = models.CharField("Block", max_length=20)
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
        return f"{self.society} - {self.name}"


class Houses(models.Model):
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    code = models.CharField("House Code")
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
        return f"{self.block} - {self.code}"


# class PermissionModule(models.Model):
#     name = models.CharField(max_length=100, unique=True)  # e.g. "residential_details", "personal_details", "professional_details"
#     code = models.CharField(max_length=50, unique=True)  # e.g. "RD001"
#     display_name = models.CharField(max_length=150)       # e.g. "Residential Details"

#     def __str__(self):
#         return self.display_name


# class PermissionAction(models.Model):
#     name = models.CharField(max_length=50, unique=True)  # e.g. "create", "read", "update", "delete"
#     code = models.CharField(max_length=20, unique=True)   # e.g. "C001", "R001", etc.

#     def __str__(self):
#         return self.name


# class Accesses(models.Model): # custom permissions system,
#     module = models.ForeignKey(PermissionModule, on_delete=models.CASCADE)
#     permission = models.ForeignKey(PermissionAction, on_delete=models.CASCADE)
#     is_hidden = models.BooleanField("Hidden", default=False)
#     on_hold = models.BooleanField("On Hold", default=False)
#     hold_date = models.DateField("Hold Upto", null=True, blank=True)

#     def save(self, *args, **kwargs):
#         if self.hold_date:
#             self.on_hold = True
#             if self.hold_date < timezone.now().date():
#                 self.on_hold = False
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.module.display_name} - {self.permission.name}"


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

# class Accesses(models.Model):
#     name = models.CharField("Access Activity", max_length=255)
#     is_hidden = models.BooleanField("Hidden", default=False)
#     on_hold = models.BooleanField("On Hold", default=False)
#     hold_date = models.DateField("Hold Upto", null=True, blank=True)

#     def save(self, *args, **kwargs):
#         if self.hold_date and self.hold_date < timezone.now().date():
#             self.on_hold = False
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.name


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


class Pidhi(models.Model):
    subgotra = models.ForeignKey(SubGotra, on_delete=models.CASCADE)
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
        return self.name
