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