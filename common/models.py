from django.db import models

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
    
    