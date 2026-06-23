from django.db import models
from django.utils import timezone
from django.db.models import F
from simple_history.models import HistoricalRecords
from django.db.models import Q
from common.models import AuditMixin, SoftDeleteMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import datetime

def get_type_label(type_val):
    if type_val == "int":
        return "Number"
    elif type_val == "float":
        return "Decimal"
    elif type_val == "date":
        return "Date"
    elif type_val == "datetime":
        return "Date Time"
    elif type_val == "boolean":
        return "Boolean"
    else:
        return "Text"



DIMENSION_NAME_REGEX = r"^[A-Z][a-zA-Z0-9 ]*$"
dimension_name_validator = RegexValidator(
    DIMENSION_NAME_REGEX,
    message="Name must start with an uppercase letter and can not contain letters, numbers, and spaces.",
)

class Dimension(models.Model):
    name = models.CharField(max_length=100, unique=True, validators=[dimension_name_validator])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name


# Regex: only allow lowercase letters and underscores
LEVEL_NAME_REGEX = r"^[a-z_]*$"
level_name_validator = RegexValidator(
    LEVEL_NAME_REGEX,
    message="Name must be lowercase and contain only letters and underscores.",
)

class Level(SoftDeleteMixin):
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="levels")
    display_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100, validators=[level_name_validator])
    single_mode = models.BooleanField(default=False)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    sort_order = models.PositiveIntegerField(default=1)
    code_digits = models.PositiveIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Structure: [{"key": "slug", "label": "Name", "type": "date", "required": True}]
    extra_fields_schema = models.JSONField(default=list, blank=True, null=True)
    
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['sort_order']

        constraints = [
            models.UniqueConstraint(
                fields=['dimension', 'name'],
                name='unique_active_level_name_per_dimension',
                condition=Q(is_deleted=False)
            )
        ]

    def __str__(self):
        return self.name

class Node(SoftDeleteMixin):
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="nodes")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="nodes")
    
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    
    name = models.CharField(max_length=255, db_index=True)
    code = models.PositiveIntegerField()
    
    note = models.TextField(null=True, blank=True)
    
    is_hidden = models.BooleanField(default=False)
    on_hold = models.BooleanField(default=False)
    hold_date = models.DateField(null=True, blank=True)

    merge_date = models.DateField(null=True, blank=True)
    split_date = models.DateField(null=True, blank=True)
    
    attributes = models.JSONField(default=dict, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NEW: Materialized path for lightning-fast hierarchical ordering
    hierarchy_path = models.CharField(max_length=500, db_index=True, blank=True, null=True)
    
    history = HistoricalRecords()
    
    class Meta:
        # unique_together = ('dimension', 'level', 'code')
        ordering = ['dimension', 'hierarchy_path']
        indexes = [
            models.Index(fields=["dimension", "level"]),
            models.Index(fields=["dimension", "parent"]),
            models.Index(fields=["dimension", "name"]),
            models.Index(fields=["dimension", "hierarchy_path"]),
        ]
        constraints = [
            # 1. Constraint for Child Nodes (parent is NOT NULL)
            models.UniqueConstraint(
                fields=['parent', 'level', 'code'], 
                name='unique_code_per_parent_level',
                condition=Q(parent__isnull=False) & Q(is_deleted=False)
            ),
            # 2. Constraint for Global/Top Nodes (parent IS NULL)
            # This ensures only one 'Code 1' exists at the top of a Level/Dimension
            models.UniqueConstraint(
                fields=['dimension', 'level', 'code'], 
                name='unique_code_at_top_level',
                condition=Q(parent__isnull=True) & Q(is_deleted=False)
            )
        ]
    
    def _segment(self) -> str:
        digits = getattr(self.level, "code_digits", 2) or 2
        return str(self.code).zfill(digits)

    def rebuild_path_key(self) -> str:
        seg = self._segment()
        if self.parent_id:
            return f"{self.parent.path_key}.{seg}"
        return seg
    
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

        # --- NEW: HIERARCHY PATH LOGIC ---
        # 1. Pad the code using the level's configured digits
        pad_length = self.level.code_digits if self.level_id else 2
        padded_code = str(self.code).zfill(pad_length)

        # 2. Build the new path
        if self.parent:
            new_path = f"{self.parent.hierarchy_path}/{padded_code}"
        else:
            new_path = padded_code

        # 3. Detect if the path is changing (meaning the node was moved or its code changed)
        path_changed = False
        if self.pk:
            old_path = Node.objects.filter(pk=self.pk).values_list('hierarchy_path', flat=True).first()
            if old_path != new_path:
                path_changed = True

        self.hierarchy_path = new_path
        
        # Save the instance
        super().save(*args, **kwargs)

        # 4. If the path changed, we MUST update all descendants so their paths stay accurate
        if path_changed:
            self.update_descendants_paths()

    def update_descendants_paths(self):
        """
        Recursively triggers a save on all immediate children so they 
        recalculate their hierarchy_path based on this node's new path.
        """
        for child in self.children.all():
            child.save()

    
    def clean(self):
        """
        Django's standard validation hook. 
        We call our custom validator here.
        """
        super().clean()
        self.validate_attributes()

    def validate_attributes(self):
        """
        Validates 'attributes' JSON against 'level.extra_fields_schema'.
        """
        if not self.level:
            return

        # 1. Get Schema (Columns Definition)
        schema = self.level.extra_fields_schema or []
        
        # 2. Get Data (User Input)
        data = self.attributes or {}

        # --- DEBUG PRINT ---
        # print(f"DEBUG: Validating Node {self.name}")
        # print(f"DEBUG: Data: {data}")
        # for col in schema:
        #     print(f"DEBUG: Column '{col['name']}' Required setting is: {col.get('required')} (Type: {type(col.get('required'))})")
        
        for field_def in schema:
            
            name = field_def.get('name')
            field_type = field_def.get('type')
            is_required = field_def.get('required', False)
            max_len = field_def.get('max_length') # Custom constraint for char
            default_value = field_def.get('default_value')

            # Fetch value from JSON
            value = data.get(name)

            # --- A. Check Required ---
            # If value is missing/empty and field is required -> Error
            if value in [None, ""] and is_required:
                print("Default Value:", default_value)
                if default_value in [None, ""]:
                    raise ValidationError({'attributes': f"The field '{name}' is required."})
            
            # If value is missing and NOT required -> Allow it (it stays Null/None)
            if value in [None, ""]:
                continue

            # --- B. Type Validation ---
            try:
                # 1. Char (String with Limit)
                if field_type == 'char':
                    if not isinstance(value, str):
                        raise ValidationError(f"'{name}' must be a text string.")
                    
                    # Enforce Max Length if defined in schema
                    if max_len and isinstance(max_len, int):
                        if len(value) > max_len:
                            raise ValidationError(f"'{name}' cannot exceed {max_len} characters.")

                # 2. Text (Unlimited String)
                elif field_type == 'text':
                    if not isinstance(value, str):
                        raise ValidationError(f"'{name}' must be a text string.")

                # 3. Integers (int, bigint)
                elif field_type in ['int', 'bigint']:
                    try:
                        float_val = float(value)
                        if not float_val.is_integer():
                            raise ValueError
                        # Normalize 50.0 to 50 in the JSON payload so it saves cleanly
                        data[name] = int(float_val) 
                    except (ValueError, TypeError):
                        raise ValueError

                # Positive Integers
                elif field_type == 'positive_int':
                    try:
                        float_val = float(value)
                        if not float_val.is_integer() or float_val < 0:
                            raise ValueError
                        # Normalize 50.0 to 50 in the JSON payload
                        data[name] = int(float_val)
                    except (ValueError, TypeError):
                        raise ValueError

                # 4. Float
                elif field_type == 'float':
                    float(value)

                # 5. Boolean
                elif field_type == 'boolean':
                    if str(value).lower() not in ['true', '1', 'yes', 'on', 'false', '0', 'no', 'off']:
                        raise ValueError

                # 6. Date / DateTime
                elif field_type == 'date':
                    datetime.datetime.strptime(str(value), '%Y-%m-%d')

                elif field_type == 'datetime':
                     # Try strictly ISO format first, fallback if needed
                    datetime.datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')

                # 7. Dropdown
                elif field_type == 'dropdown':
                    options = field_def.get('options', [])
                    if str(value) not in options:
                        raise ValidationError(f"'{name}' must be one of the following options: {', '.join(options)}")

            except (ValueError, TypeError):
                type_label = get_type_label(field_type)
                raise ValidationError(f"The value '{value}' for '{name}' is invalid. Expected type: {type_label}.")
    

    def __str__(self):
        return f"{self.name} ({self.code})"


class NodeAlias(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="aliases")
    name = models.CharField(max_length=255)
    note = models.TextField(null=True, blank=True)
    
    history = HistoricalRecords()
    class Meta:
        unique_together = (("node", "name"),)
        ordering = ["node", "name"]
        
    def __str__(self):
        return f"{self.node.name} -> {self.name}"

class NodeClosure(models.Model):
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE)
    ancestor = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="descendant_closures")
    descendant = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="ancestor_closures")
    depth = models.PositiveIntegerField()
    
    class Meta:
        unique_together = (("ancestor", "descendant"),)
        indexes = [
            models.Index(fields=["ancestor"]),
            models.Index(fields=["descendant"]),
        ]

    def __str__(self):
        return f"{self.ancestor} -> {self.descendant} ({self.depth})"
    


class NodeRelationship(SoftDeleteMixin):
    # The territory (e.g., Hong Kong, Kashmir)
    territory = models.ForeignKey(
        Node, 
        on_delete=models.CASCADE, 
        related_name="controlling_states"
    )
    
    # The country claiming or controlling it (e.g., UK, India, Pakistan)
    controller = models.ForeignKey(
        Node, 
        on_delete=models.CASCADE, 
        related_name="controlled_territories"
    )
    
    # What kind of relationship is this?
    RELATIONSHIP_CHOICES = [
        ('administered_by', 'Administered By (De Facto)'),
        ('leased_to', 'Leased To'),
        ('claimed_by', 'Claimed By (Disputed)'),
        ('historical', 'Historical / Former Controller')
    ]
    relationship_type = models.CharField(
        max_length=50, 
        choices=RELATIONSHIP_CHOICES, 
    )

    # 1. LEASE TIMING & HISTORY
    start_date = models.DateField(null=True, blank=True, help_text="When did this control/lease begin?")
    end_date = models.DateField(null=True, blank=True, help_text="When does the lease expire, or when was it handed back?")
    
    # 2. CONTEXT
    notes = models.TextField(null=True, blank=True, help_text="E.g., 'Treaty of Nanking 1898' or 'UN Resolution 47'")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        # We remove unique_together because a country might have leased it, 
        # given it back, and leased it again later!
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=["territory", "controller", "relationship_type"], 
                name="unique_active_relationship",
                condition=models.Q(is_deleted=False) # Only enforce uniqueness on active records!
            )
        ]

    def __str__(self):
        return f"[{self.get_relationship_type_display()}] {self.territory.name} -> {self.controller.name}"

    def get_relationship_type_display(self):
        return dict(self.RELATIONSHIP_CHOICES)[self.relationship_type]

# ====================================================================
# OLD MODELS
# ====================================================================
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
    CATEGORY_CHOICES = [
        ('personal', 'Personal'),
        ('residential', 'Residential'),
        ('professional', 'Professional'),
    ]

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    model_name = models.CharField(max_length=100)
    file = models.FileField(upload_to=sample_file_upload_path, blank=True, null=True)

    class Meta:
        unique_together = ('category', 'model_name')

    def __str__(self):
        return f"{self.model_name} ({self.category})"

    


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

