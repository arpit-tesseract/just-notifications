from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(StatusModelName)

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', "name", "model", "is_active", "time_stamp")
    list_filter = ("model", "is_active")