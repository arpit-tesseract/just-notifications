from django.db import models
from django.utils import timezone



class AuditMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        

class StatusModelName(models.Model):
    app_label = models.CharField(max_length=100)  # e.g. "yourapp"
    model = models.CharField(max_length=100)      # e.g. "City"
    technical_name = models.CharField(max_length=200, unique=True)  # "yourapp.City"
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.model


class Status(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    model = models.ForeignKey(StatusModelName, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
        
    class Meta:
        unique_together = ('model', 'name')
    
    def __str__(self):
        return self.name
    
    def get_or_create_status_by_model_name_and_status_name(model_name, status_name):
        model_obj, _ = StatusModelName.objects.get_or_create(model=model_name)
        try:
            status = Status.objects.get(model__model=model_name, name=status_name)
        except Status.DoesNotExist:
            status = Status.objects.create(model=model_obj, name=status_name)
        except Status.MultipleObjectsReturned:
            status = Status.objects.filter(model__model=model_name, name=status_name).first()
        return status


# 1. Custom Manager to hide deleted items by default
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # By default, hide deleted items
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        # Custom method if you actually need to see everything (e.g. for admins)
        return super().get_queryset()
   


class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "user.User", null=True, blank=True, on_delete=models.SET_NULL
    )
    
    # Hook up the manager
    objects = SoftDeleteManager() 
    # Optional: Keep a reference to the plain manager if you need raw access
    all_objects = models.Manager()
    
    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
        
    def restore(self):
        """
        Restores a soft-deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
