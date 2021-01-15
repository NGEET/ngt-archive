import io

from daterangefilter.filters import DateRangeFilter
from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms import forms
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.datetime_safe import datetime

from archive_api.models import DataSet, DataSetDownloadLog, MeasurementVariable, Person, Plot, Site


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(MeasurementVariable)
class MeasurementVariableAdmin(ModelAdmin):
    list_display = ('name',)


@admin.register(Person)
class PersonAdmin(ModelAdmin):

    change_list_template = "entities/persons_change_list.html"
    list_display = ('first_name', 'last_name', 'institution_affiliation','email', 'orcid')
    actions = ('download_csv',)

    def get_urls(self):
        """
        Extends ancestor by adding update_orcids/ path to returned URLs for this view
        :return:
        """
        urls = super().get_urls()
        my_urls = [
            path('update-orcids/', self.update_orcids),
        ]
        return my_urls + urls

    def update_orcids(self, request, ):
        """ Allow users to update orcids"""

        import csv
        expected_headers = {'first_name', 'last_name', 'institution_affiliation', 'email', 'orcid'}

        # Only allow POST method
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]

            # Fail if not CSV file
            if csv_file.content_type == 'text/csv':

                # Upload file is a BytesIO and the csv reader needs a string
                file_wrapper = io.TextIOWrapper(csv_file.file, encoding='utf-8')

                header = None
                updated_count = 0
                reader = csv.reader(file_wrapper)
                for row in reader:
                    if not header:
                        header = row
                        if expected_headers.difference(set(header)):
                            self.message_user(request, f"Cancelling update. Your header row is missing: {expected_headers.difference(set(header))}")
                            break
                    else:
                        if len(header) != len(row):
                            self.message_user(request,
                                              f"Cancelling update. Data row is invalid: {row}")
                            break
                        else:
                            result_dict = dict(zip(header, row))
                            # Create Person objects from passed in data

                            try:
                                # Find the perscon record.
                                # if first_name, last_name, institiution and email are not found,
                                #   not records are updated.
                                person = Person.objects.get(first_name=result_dict['first_name'],
                                                            last_name=result_dict['last_name'],
                                                            institution_affiliation=result_dict[
                                                                'institution_affiliation'],
                                                            email=result_dict['email'])

                                # Assign the orcid. We are not checking if the ORCiD exists or
                                # is being changed.
                                person.orcid = result_dict['orcid']

                                # Full clean forces validation
                                person.full_clean()
                                person.save()
                                updated_count += 1
                            except Person.DoesNotExist:
                                self.message_user(request, f"NOT FOUND {list(result_dict.values())}", level=messages.WARNING)
                            except ValidationError as e:
                                # Do something based on the errors contained in e.message_dict.
                                # Display them to a user, or handle them programmatically.
                                for msg in e.messages:
                                    self.message_user(request, f"{msg} {list(result_dict.values())}", level=messages.ERROR)

                self.message_user(request, f"{updated_count} records found and were updated.",
                                      level=updated_count and messages.INFO or messages.WARNING)

            else:
                self.message_user(request, "File must be text/csv. Your csv file has NOT been imported")
            return redirect("..")

        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "admin/csv_form.html", payload
        )

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
        writer.writerow(['first_name', 'last_name', 'institution_affiliation', 'email', 'orcid'])

        for row in queryset:
            writer.writerow([row.first_name, row.last_name, row.institution_affiliation, row.email,
                             row.orcid
                             ])

        f.seek(0)
        response = HttpResponse(f, content_type='text/csv')
        current_date = datetime.now().strftime("%Y%m%dT%H%M")
        response['Content-Disposition'] = f'attachment; filename=download_ngeet_people_{current_date}.csv'
        return response

    download_csv.short_description = "Download CSV file for selected people"



@admin.register(Plot)
class PlotAdmin(ModelAdmin):
    list_display = ('plot_id', 'description',)


@admin.register(Site)
class SiteAdmin(ModelAdmin):
    list_display = ('site_id', 'name', 'description',)


@admin.register(DataSet)
class DraftDataSetAdmin(ModelAdmin):

    actions = ("mark_as_deleted",)
    list_display = ('ngt_id', 'version','name', 'created_by', 'created_date','modified_by','modified_date',)
    readonly_fields = ('ngt_id', 'version', 'name', 'created_by', 'created_date','modified_by','modified_date',)

    def __init__(self, *args, **kwargs):
        """
        Override the parent method in order to remove display links
        that navigate to show info page.
        :param args:
        :param kwargs:
        """
        super(self.__class__, self).__init__(*args, **kwargs)
        self.list_display_links = None  # no display links

        # This will affect the Title of the page on in the Admin site
        self.model._meta.verbose_name = 'Draft data set'
        self.model._meta.verbose_name_plural = 'Draft data sets'

    def get_actions(self, request):
        """Overrides parent. Removed the delete selected action"""
        actions = super(self.__class__, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        """
        Returns a QuerySet of all DRAFT DataSets
        """
        qs = super(DraftDataSetAdmin,self).get_queryset(request)
        return qs.filter(status=DataSet.STATUS_DRAFT)

    def has_add_permission(self, request):
        """
        Disallow add through the admin interface. These records
        should only be created in the main site

        param request:
        :return: False
        """
        return False

    def mark_as_deleted(self, request, queryset):
        """
        Mark the DRAFT Datasets as deleted. Datasets marked
        as deleted will not show up in the Archive Service

        :param request: The current http request
        :param queryset: the selected objects to mark deleted
        :return: None
        """

        # Check that the user has delete permission for the actual model
        if not self.has_delete_permission(request):
            raise PermissionDenied

        n = queryset.count()
        if n:
            for obj in queryset:
                # We just want to mark deleted NOT physically delte
                obj.status = DataSet.STATUS_DELETED
                obj.save()

            self.message_user(request,
                                    "Successfully marked %(count)d %(items)s as DELETED." % {
                                        "count": n,
                                        "items": model_ngettext(self.opts, n)
                                    }, messages.SUCCESS)
        # Return None to display the change list page again.
        return None

    mark_as_deleted.short_description = "Mark draft data sets as DELETED"


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

    def get_actions(self, request):
        """Overrides parent. Removed the delete selected action"""
        actions = super(self.__class__, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

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


