# Generated by Django 3.1.2 on 2022-02-28 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive_api', '0012_dataset_managed_by_editable'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dataset',
            options={'ordering': ('-modified_date',), 'permissions': (('approve_submitted_dataset', "Can approve a 'submitted' dataset"), ('edit_own_dataset', 'Can edit own dataset'), ('edit_all_dataset', 'Can edit any  dataset'), ('view_all_datasets', 'Can view all datasets'), ('view_ngeet_approved_datasets', 'Can view all approved NGEE Tropics datasets'), ('upload_large_file_dataset', 'Can upload a large file to a dataset'))},
        ),
        migrations.AddField(
            model_name='dataset',
            name='approval_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]