from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import datetime

# Regex: Starts with Uppercase, allows letters, numbers, and spaces.
TECH_KEY_REGEX = r"^[A-Z][a-zA-Z0-9 ]*$"
tech_key_validator = RegexValidator(
    TECH_KEY_REGEX,
    message="Name must start with an uppercase letter and can contain letters, numbers, and spaces.",
)

class Dimension(models.Model):
    name = models.CharField(max_length=100, unique=True, validators=[tech_key_validator])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Level(models.Model):
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="levels")
    name = models.CharField(max_length=100, validators=[tech_key_validator])
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    sort_order = models.PositiveIntegerField(default=1)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Structure: [{"key": "slug", "label": "Name", "type": "date", "required": True}]
    extra_fields_schema = models.JSONField(default=list, blank=True)
    
    class Meta:
        unique_together = ('dimension', 'name')
        ordering = ['sort_order']

    def __str__(self):
        return self.name

class Node(models.Model):
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="nodes")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="nodes")
    
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=100, unique=True)
    
    is_hidden = models.BooleanField(default=False)
    on_hold = models.BooleanField(default=False)
    hold_date = models.DateField(null=True, blank=True)
    
    attributes = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["dimension", "level"]),
            models.Index(fields=["dimension", "parent"]),
            models.Index(fields=["dimension", "name"]),
        ]
    
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
    
    def clean(self):
        super().clean()
        self.validate_attributes()

    def validate_attributes(self):
        """
        Ensures the JSON data matches the types defined in the Level schema.
        """
        if not self.level:
            return

        schema = self.level.extra_fields_schema or []
        data = self.attributes or {}

        for field_def in schema:
            key = field_def.get('key')
            field_type = field_def.get('type')
            is_required = field_def.get('required', False)
            label = field_def.get('label', key)
            
            value = data.get(key)

            # 1. Check Required
            if is_required and value in [None, ""]:
                raise ValidationError(f"Attribute '{label}' is required.")

            # If empty and not required, skip validation
            if value in [None, ""]:
                continue

            # 2. Type Validation
            try:
                if field_type == 'int':
                    if not isinstance(value, int):
                        # Try converting string "10" to int 10
                        value = int(value) 
                
                elif field_type == 'positive_int':
                    value = int(value)
                    if value < 0:
                        raise ValidationError(f"'{label}' must be a positive integer.")

                elif field_type == 'float':
                    value = float(value)

                elif field_type == 'boolean':
                    if not isinstance(value, bool):
                        if str(value).lower() in ['true', '1', 'yes']:
                            value = True
                        elif str(value).lower() in ['false', '0', 'no']:
                            value = False
                        else:
                            raise ValueError

                elif field_type == 'date':
                    # Fixed: Used datetime.datetime correctly
                    datetime.datetime.strptime(str(value), '%Y-%m-%d')

                elif field_type == 'datetime':
                    # Fixed: Used datetime.datetime correctly
                    datetime.datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')

            except (ValueError, TypeError):
                raise ValidationError(f"Attribute '{label}' must be of type {field_type}. Got: {value}")

    def __str__(self):
        return f"{self.name} ({self.code})"

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

# ==============================================================================
# REQUIRED SIGNAL: Fills the Closure Table Automatically
# ==============================================================================
@receiver(post_save, sender=Node)
def update_node_closure(sender, instance, created, **kwargs):
    if created:
        # 1. Self Reference
        NodeClosure.objects.create(
            dimension=instance.dimension,
            ancestor=instance,
            descendant=instance,
            depth=0
        )
        
        # 2. Copy Parent's Ancestors
        if instance.parent:
            parents_closures = NodeClosure.objects.filter(descendant=instance.parent)
            new_closures = []
            for closure in parents_closures:
                new_closures.append(NodeClosure(
                    dimension=instance.dimension,
                    ancestor=closure.ancestor,
                    descendant=instance,
                    depth=closure.depth + 1
                ))
            NodeClosure.objects.bulk_create(new_closures)