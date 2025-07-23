from datetime import datetime

import io

from django.contrib import admin, messages
from django.contrib.admin import DateFieldListFilter, ModelAdmin
from django.core.exceptions import ValidationError
from django.forms import forms
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext

from archive_api.models import DataSet, DataSetDownloadLog, EssDiveTransfer, MeasurementVariable, Person, Plot, \
    ServiceAccount, Site

from archive_api.forms import ServiceAccountForm
from simple_history.admin import SimpleHistoryAdmin

from archive_api.service import osti


@admin.register(ServiceAccount)
class ServiceAccountAdmin(ModelAdmin):
    form = ServiceAccountForm
    list_display = ["name", "service", "endpoint"]


@admin.register(DataSet)
class DataSetHistoryAdmin(SimpleHistoryAdmin):
    list_filter = ('access_level', 'status', 'modified_date', 'publication_date', 'approval_date', 'submission_date')
    list_display = ["data_set_id", "version", "status", "access_level", "doi", "name", "modified_date",
                    "last_transfer_date", "last_transfer_status"]
    history_list_display = ["list_changes"]
    search_fields = ['name', 'status', "ngt_id", "version"]

    actions = ['osti_synchronize', 'osti_mint', 'essdive_transfer_metadata', 'essdive_transfer_data',
               'update_essdive_permissions']

    def last_transfer_status(self, obj):
        """
        Get the last transfer status for the dataset

        :param obj:
        :return:
        """
        trasfer_result = EssDiveTransfer.objects.all().filter(dataset=obj)
        if trasfer_result:
            return trasfer_result.order_by('-create_time')[0].get_status_display()
        else:
            return None

    def last_transfer_date(self, obj):
        """
        Get the last transfer date for the dataset
        :param obj:
        :return:
        """
        trasfer_result = EssDiveTransfer.objects.all().filter(dataset=obj)
        if trasfer_result:
            return trasfer_result.order_by('-create_time')[0].create_time
        else:
            return None

    def update_essdive_permissions(self, request, queryset):
        """Update permissions for dataset in ESS-DIVE"""
        return self._essdive_transfer(request, queryset, EssDiveTransfer.TYPE_PERMISSIONS)

    update_essdive_permissions.short_description = "Update permissions for dataset in ESS-DIVE"

    def essdive_transfer_data(self, request, queryset):
        """Transfer dataset metadata+data to ESS-DIVE"""
        return self._essdive_transfer(request, queryset, EssDiveTransfer.TYPE_DATA)

    essdive_transfer_data.short_description = "Transfer dataset metadata+data to ESS-DIVE"

    def essdive_transfer_metadata(self, request, queryset):
        """Transfer dataset metadata to ESS-DIVE"""
        return self._essdive_transfer(request, queryset, EssDiveTransfer.TYPE_METADATA)

    essdive_transfer_metadata.short_description = "Transfer dataset metadata to ESS-DIVE"

    def _essdive_transfer(self, request, queryset, transfer_type):

        transfer_count = 0
        for dataset in queryset:

            if dataset.access_level in (DataSet.ACCESS_PUBLIC, DataSet.ACCESS_NGEET) and dataset.submission_date is not None:
                transfer_count += 1
                EssDiveTransfer.objects.create(dataset=dataset, type=transfer_type)
                self.message_user(request,
                                  f"Requested transfer of {dataset.data_set_id()}.",
                                  messages.SUCCESS)
            else:
                if dataset.access_level not in (DataSet.ACCESS_PUBLIC, DataSet.ACCESS_NGEET):
                    self.message_user(request,
                                      f"Dataset {dataset.data_set_id()} id not public or ngee-tropics access level and cannot be transferred to ESS-DIVE",
                                      messages.WARNING)
                if dataset.approval_date is None:
                    self.message_user(request,
                                      f"Dataset {dataset.data_set_id()} has never been approved and cannot be transferred to ESS-DIVE",
                                      messages.WARNING)

        if transfer_count > 0:
            self.message_user(request, ngettext(
                '%d dataset transfer was requested.',
                '%d dataset transfers were requested.',
                transfer_count,
            ) % transfer_count, messages.SUCCESS)
        else:
            self.message_user(request, "No datasets were transferred to ESS-DIVE.", messages.WARNING)

    def osti_synchronize(self, request, queryset):
        """Synchronizes published datasets with OSTI"""

        self.message_user(request, "OSTI Functionality has been removed.", messages.WARNING)

    osti_synchronize.short_description = 'Synchronize via OSTI for selected datasets (deprecated)'

    def osti_mint(self, request, queryset):
        """Mint DOIs via OSTI with selected datasets"""

        self.message_user(request,f"OSTI Functionality has been removed. ",
                                  messages.WARNING)



    osti_mint.short_description = 'Mint DOIs via OSTI for selected datasets (deprecated)'

    def list_changes(self, obj):
        """
        Lists the changes between revisions in the Admin UI

        See: https://django-simple-history.readthedocs.io/en/latest/history_diffing.html

        :param obj:
        :return:
        """
        diff = []
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            for change in delta.changes:
                diff.append("<b>- {}:</b> changed from `{}` to `{}`".format(change.field, change.old, change.new))

        # Mark safe (https://docs.djangoproject.com/en/4.0/ref/utils/#django.utils.safestring.mark_safe)
        return mark_safe("\n<br>".join(diff))


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(MeasurementVariable)
class MeasurementVariableAdmin(ModelAdmin):
    list_display = ('name',)


@admin.register(Person)
class PersonAdmin(ModelAdmin):
    change_list_template = "entities/persons_change_list.html"
    list_display = ('first_name', 'last_name', 'institution_affiliation', 'email', 'orcid')
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
                            self.message_user(request,
                                              f"Cancelling update. Your header row is missing: {expected_headers.difference(set(header))}")
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
                                self.message_user(request, f"NOT FOUND {list(result_dict.values())}",
                                                  level=messages.WARNING)
                            except ValidationError as e:
                                # Do something based on the errors contained in e.message_dict.
                                # Display them to a user, or handle them programmatically.
                                for msg in e.messages:
                                    self.message_user(request, f"{msg} {list(result_dict.values())}",
                                                      level=messages.ERROR)

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


@admin.register(EssDiveTransfer)
class EssDiveTransferAdmin(ModelAdmin):
    search_fields = ['dataset__name', 'status', "message", "type", "id"]
    list_filter = ['type', 'status', "create_time", "start_time", "end_time"]
    list_display = ["id", "dataset", "type", "status", "create_time", "start_time", "end_time"]
    readonly_fields = ('dataset', 'type', 'status', 'message', 'start_time', 'end_time', 'response')

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


@admin.register(DataSetDownloadLog)
class DataSetDownloadLogAdmin(ModelAdmin):
    """
    This Admin interface allows user to search by date range and user.  The resulting items
    in the list may be downloaded to a CSV file
    """
    list_filter = (('datetime', DateFieldListFilter), 'user',)
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
            writer.writerow([row.datetime, self.user_name(row), row.get_dataset_status_display(),
                             str(row.dataset), row.ip_address, row.request_url
                             ])

        f.seek(0)
        response = HttpResponse(f, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=download_log.csv'
        return response

    download_csv.short_description = "Download CSV file for selected download activity."
