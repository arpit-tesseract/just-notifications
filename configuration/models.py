from django.db import models
from datetime import timezone

# Create your models here.
class Continent(models.Model):
    name = models.CharField("Continent", max_length=100,unique=True)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.district.code} - {self.name} - {self.code}"


class Village(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField("Village", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.city or 'No City'} - {self.name} - {self.code}"
   
class Category(models.Model):
    name = models.CharField("Category", max_length=255)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
class Religion(models.Model):
    name = models.CharField("Religion", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Varna(models.Model):
    name = models.CharField("Varna", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Gotra(models.Model):
    caste = models.ForeignKey(Caste, on_delete=models.CASCADE)
    name = models.CharField("Gotra", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Type(models.Model):
    subcategory = models.ForeignKey(ProfSubCategory, on_delete=models.CASCADE)
    name = models.CharField("Type", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class PostModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CharField)
    name = models.CharField("Post Model", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Sector(models.Model):
    name = models.CharField("Sector", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField("Department", max_length=200)
    code = models.CharField("Code", max_length=5, unique=True)
    is_hidden = models.BooleanField("Hidden", default=False)
    on_hold = models.BooleanField("On Hold", default=False)
    hold_date = models.DateField("Hold Upto", null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.hold_date and self.hold_date < timezone.now().date():
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
        if self.hold_date and self.hold_date < timezone.now().date():
            self.on_hold = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name