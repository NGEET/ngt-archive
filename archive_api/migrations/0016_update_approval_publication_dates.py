from django.db import migrations, models


def update_approval_publication_dates(apps, schema_editor):
    """
    Set the approval date and publication date to the modifed_date

    :param apps:
    :param schema_editor:
    :return:
    """
    DataSet = apps.get_model('archive_api', 'DataSet')
    for row in DataSet.objects.all():
        if row.status == 2:
            row.publication_date = row.modified_date
            row.approval_date = row.modified_date
            row.save(update_fields=['publication_date', 'approval_date'])


class Migration(migrations.Migration):
    dependencies = [
        ('archive_api', '0015_managed_modified_date'),
    ]

    operations = [
        migrations.RunPython(update_approval_publication_dates,
                             reverse_code=migrations.RunPython.noop),
    ]
