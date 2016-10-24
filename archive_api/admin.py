from django.contrib import admin
from django.contrib.admin import ModelAdmin

from archive_api.models import DataSet, MeasurementVariable, Site, Contact, Plot


@admin.register(DataSet)
class DataSetAdmin(ModelAdmin):
    list_display = ('data_set_id', 'description',)


@admin.register(MeasurementVariable)
class MeasurementVariableAdmin(ModelAdmin):
    list_display = ('name',)


@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ('first_name', 'last_name', 'institution_affiliation',)


@admin.register(Plot)
class PlotAdmin(ModelAdmin):
    list_display = ('plot_id', 'description',)


@admin.register(Site)
class SiteAdmin(ModelAdmin):
    list_display = ('site_id', 'name', 'description',)
