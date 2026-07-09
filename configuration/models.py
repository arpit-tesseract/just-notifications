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
    is_mandatory = models.BooleanField(default=False, help_text="If True, users must provide a node for this level when saving data in this dimension.")
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


class NodeEventLog(models.Model):
    EVENT_CHOICES = (
        ('MERGE', 'Merge'),
        ('SPLIT', 'Split'),
    )
    event_type = models.CharField(max_length=10, choices=EVENT_CHOICES)
    source_node = models.ForeignKey(Node, on_delete=models.SET_NULL, null=True, related_name="source_events")
    target_node = models.ForeignKey(Node, on_delete=models.SET_NULL, null=True, related_name="target_events")
    effective_date = models.DateField(null=True, blank=True)
    performed_by = models.ForeignKey('user.User', on_delete=models.SET_NULL, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type}: {self.source_node} -> {self.target_node}"


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
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='model_access_permission')
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
    user = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="record_rules")
    model = models.ForeignKey(ModelName, on_delete=models.CASCADE, related_name="record_rules")

    name = models.CharField(max_length=100, null=True, blank=True)
    domain_filter = models.JSONField(default=dict)  # e.g. {"state__name": "Gujarat"}

    can_read = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    def __str__(self):
        
        return f"{self.name} For: '{self.user.email}'"
