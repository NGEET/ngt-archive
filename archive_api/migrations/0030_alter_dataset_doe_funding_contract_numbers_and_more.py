# Generated by Django 4.2.2 on 2024-05-30 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive_api', '0029_alter_dataset_funding_organizations_and_more'),
    ]

    def update_null_fields(apps, schema_editor):
        Dataset = apps.get_model('archive_api', 'dataset')
        for dataset in Dataset.objects.filter(doe_funding_contract_numbers=None):
            dataset.doe_funding_contract_numbers = 'DE-AC02-05CH11231'
            dataset.save()

    def reverse_update_null_fields(apps, schema_editor):
        # It is ok not to reverse
        pass

    operations = [
        migrations.RunPython(update_null_fields, reverse_update_null_fields),

    ]