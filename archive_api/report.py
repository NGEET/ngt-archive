"""
Reporting functions
"""
from archive_api.models import ACCESS_CHOICES, DataSet
from django.db.models import Count, Q


def report_datasets(start_date, end_date, user):
    """
    Prepare the datasets for all statuses
    in the specified date range

    :param start_date:
    :param end_date:
    :param user:
    :return:
    """

    def _get_metric(q: Q, label):
        return {
            "label": label,
            "num": DataSet.objects.filter(q).count()}

    metrics_datasets = []

    # Determine who has permissions to view the metrics
    q_perm = Q(publication_date__isnull=False,
               access_level__gte=DataSet.ACCESS_NGEET)
    q_created = Q(Q(created_date__gte=start_date,
                    created_date__lte=end_date) & q_perm)
    q_submitted = Q(Q(submission_date__gte=start_date,
                      submission_date__lte=end_date) & q_perm)

    if user.has_perm('archive_api.view_all_datasets') or user.is_staff:
        q_perm = Q(status__gte=DataSet.STATUS_DRAFT,
                   access_level__gte=DataSet.ACCESS_PRIVATE)
        q_created = Q(Q(created_date__gte=start_date,
                        created_date__lte=end_date) & q_perm)
        q_submitted = Q(Q(submission_date__gte=start_date,
                          submission_date__lte=end_date) & q_perm)
        metrics_datasets.append(_get_metric(q_created, "Created"))
        metrics_datasets.append(_get_metric(q_submitted, "Submitted"))

    # Build sub queries
    q_approved = Q(Q(publication_date__gte=start_date,
                     publication_date__lte=end_date) & q_perm)
    metrics_datasets.append(_get_metric(q_approved, "Approved"))

    query_result = DataSet.objects.filter(q_created | q_submitted | q_approved)

    # Build the dataset metrics for access level
    metrics_query = DataSet.objects.filter(q_submitted).values('access_level').annotate(Count('ngt_id')).order_by()
    for m in metrics_query:
        metrics_datasets.append({"label": f"{ACCESS_CHOICES[m['access_level']][1]} access",
                                 "num": m['ngt_id__count']})

    # Get the DOIs issued for submitted datasets
    metrics_datasets.append({"label": "DOIs issued",
                             "num": DataSet.objects.filter(q_submitted).aggregate(Count('doi'))[
                                 'doi__count']})

    return {
        "metrics": metrics_datasets,
        "datasets": query_result

    }
