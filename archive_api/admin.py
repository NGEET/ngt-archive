
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from daterange_filter.filter import DateRangeFilter
from archive_api.models import MeasurementVariable, Site, Person, Plot, DataSetDownloadLog


@admin.register(MeasurementVariable)
class MeasurementVariableAdmin(ModelAdmin):
    list_display = ('name',)


@admin.register(Person)
class PersonAdmin(ModelAdmin):
    list_display = ('first_name', 'last_name', 'institution_affiliation',)


@admin.register(Plot)
class PlotAdmin(ModelAdmin):
    list_display = ('plot_id', 'description',)


@admin.register(Site)
class SiteAdmin(ModelAdmin):
    list_display = ('site_id', 'name', 'description',)


@admin.register(DataSetDownloadLog)
class DataSetDownloadLogAdmin(ModelAdmin):
    """
    This Admin interface allows user to search by date range and user.  The resulting items
    in the list may be downloaded to a CSV file
    """
    list_filter = (('datetime',DateRangeFilter),'user',)
    actions = ('download_csv',)
    list_display = ('datetime', 'user_name', 'dataset_status', 'dataset', 'request_url',)
    readonly_fields = ('datetime', 'user', 'dataset_status', 'dataset', 'request_url', 'ip_address')

    fieldsets = [
        (None, {'fields': ()}),
    ]

    def __init__(self, *args, **kwargs):
        """
        Override the parent method in order to remove display links
        that navigate to show info page.
        :param args:
        :param kwargs:
        """
        super(self.__class__, self).__init__(*args, **kwargs)
        self.list_display_links = None  # no display links

    def has_add_permission(self, request):
        """
        Disallow add through the admin interface. These records
        should only be created when a DataSet archive file is downloaded
        :param request:
        :return:
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Disallow delete from anywhere in the admin interface.  These records are
        never to be deleted.

        :param request:
        :param obj:
        :return:
        """
        return False

    def user_name(self, obj):
        """
        Format the user name with full name and email address.
        :param obj:
        :return:
        """
        return "{} <{}>".format(obj.user.get_full_name(), obj.user.email)

    def get_actions(self, request):
        """Overrides parent. Removed the delete selected action"""
        actions = super(self.__class__, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def download_csv(self, request, queryset):
        """
        Allow users to download the selected records

        :param request:
        :param queryset:
        :return:
        """
        import csv
        from django.http import HttpResponse
        import io

        f = io.StringIO()
        writer = csv.writer(f)
        writer.writerow(["datetime", "user_name", "dataset_status", 'dataset_name', "ip_address", "request_url"])

        for row in queryset:
            writer.writerow([row.datetime, self.user_name(row),row.get_dataset_status_display(),
                             str(row.dataset), row.ip_address, row.request_url
                             ])

        f.seek(0)
        response = HttpResponse(f, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=download_log.csv'
        return response

    download_csv.short_description = "Download CSV file for selected download activity."


