# Create your views here
from datetime import datetime

import csv

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (
    Http404, HttpResponse, HttpResponseRedirect,
)
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.utils import timezone

from archive_api.models import DataSet, DataSetDownloadLog

from archive_api.forms import MetricsFilterForm
from archive_api.report import report_datasets


def _get_citation_author_list(dataset: DataSet) -> str:
    """
    Return the citation formatted author list

    :param dataset: The dataset
    :return: A citation formatted author list
    :rtype: str
    """

    author_list = ["{} {}".format(o.author.last_name, o.author.first_name[0]) for o in
                   dataset.author_set.all().order_by('order')]
    return "; ".join(author_list)


def metrics_datasets(request):
    """
    Handles metrics requests

    :param request:
    :return:
    """
    current_tz = timezone.get_current_timezone()

    # Check the request to see if a search was performed
    if request.POST and "clear" not in request.POST:
        form = MetricsFilterForm(request.POST)
    else:
        # no search or clear (use default parameters)
        form = MetricsFilterForm({
            'start_date': timezone.datetime(2016, 1, 1, tzinfo=current_tz).strftime("%Y-%m-%d"),
            'end_date': timezone.now().strftime("%Y-%m-%d")
        })

    metrics_users = []
    metrics_datasets = []
    if form.is_valid():

        # Get the start and end dates and set them to the server timezone
        start_date = datetime.strptime(form.data['start_date'], "%Y-%m-%d")
        start_date = datetime(start_date.year, start_date.month, start_date.day, tzinfo=current_tz)
        end_date = datetime.strptime(form.data['end_date'], "%Y-%m-%d")
        end_date = datetime(end_date.year, end_date.month, end_date.day, tzinfo=current_tz)

        # Build the datasets metrics for statuses (Submitted, Approved)
        dataset_report = report_datasets(start_date, end_date, request.user)
        metrics_datasets = dataset_report['metrics']

        # Get the user meterics
        metrics_users = []
        metrics_users.append({"label": "Registered", "num": User.objects.filter(date_joined__gte=start_date,
                                                                                date_joined__lte=end_date).count()})
        metrics_users.append({"label": "Data Downloads",
                              "num": DataSetDownloadLog.objects.filter(datetime__gte=start_date,
                                                                       datetime__lte=end_date).count()})

        if request.POST and 'download' in request.POST:
            response = HttpResponse(
                content_type='text/csv'
            )
            response[
                'Content-Disposition'] = f'attachment; filename="dataset_report_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv"'

            writer = csv.writer(response)
            writer.writerow(
                ['NGT ID', 'Access Level', 'Title', 'Approval Date', 'Contact', 'Authors', 'DOI', 'Downloads',
                                                                                                            'Citation'])
            for dataset in dataset_report['datasets']:
                writer.writerow([dataset.data_set_id(),
                                 dataset.get_access_level_display(),
                                 dataset.name,
                                 dataset.publication_date or '',
                                 dataset.contact and str(dataset.contact) or '',
                                 _get_citation_author_list(dataset), dataset.doi,
                                 DataSetDownloadLog.objects.filter(datetime__gte=start_date,
                                                                   datetime__lte=end_date,
                                                                   dataset__ngt_id=dataset.ngt_id).count(),
                                 dataset.citation])

            return response

    return render(request, 'archive_api/metrics.html', context={'user': request.user,
                                                                'metrics_datasets': metrics_datasets,
                                                                'metrics_users': metrics_users,
                                                                'form': form})


def dois(request):
    """
    List all public doi pages
    :param request:
    :return:
    """
    read_only = settings.READ_ONLY

    data_sets = get_list_or_404(DataSet, publication_date__isnull=False, publication_date__lt=timezone.now(),
                                access_level__in=(DataSet.ACCESS_NGEET, DataSet.ACCESS_PUBLIC))

    return render(request, 'archive_api/dois.html', context={'user': request.user,
                                                             'datasets': data_sets,
                                                             'readonly': read_only})


def doi(request, ngt_id=None):
    """
    Public doi pages
    :param request:
    :return:
    """

    dataset = get_object_or_404(DataSet, ngt_id=int(ngt_id[3:]))
    read_only = settings.READ_ONLY

    if (dataset.publication_date is not None and dataset.publication_date < timezone.now() and \
            dataset.access_level in [DataSet.ACCESS_PUBLIC, DataSet.ACCESS_NGEET]):
        authors = _get_citation_author_list(dataset)

        site_id_list = [o.site_id for o in dataset.sites.all()]
        site_ids = "; ".join(site_id_list)

        site_list = [o.name for o in dataset.sites.all()]
        sites = "; ".join(site_list)

        variable_list = [o.name for o in dataset.variables.all()]
        variables = "; ".join(variable_list)

        return render(request, 'archive_api/doi.html', context={'user': request.user,
                                                                'dataset': dataset,
                                                                'authors': authors,
                                                                'site_ids': site_ids,
                                                                'sites': sites,
                                                                'variables': variables,
                                                                'readonly': read_only})
    else:
        raise Http404('That dataset does not exist')


@login_required(login_url="/login")
def download(request, ngt_id):
    """
    Download the dataset

    :param request:
    :param ngt_id:
    :return:
    """

    dataset = get_object_or_404(DataSet, ngt_id=int(ngt_id[3:]))
    return HttpResponseRedirect("/api/v1/datasets/{}/archive".format(dataset.id), )
