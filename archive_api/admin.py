from django.contrib import admin

# Register your models here.

# Register your models here.
from django.contrib.admin import ModelAdmin

from archive_api.models import DataSet


@admin.register(DataSet)
class DataSetAdmin(ModelAdmin):
    list_display = ('data_set_id', 'description')
