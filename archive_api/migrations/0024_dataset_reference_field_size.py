# Generated by Django 3.1.14 on 2022-05-04 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive_api', '0023_secret_field_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='additional_reference_information',
            field=models.TextField(blank=True, max_length=2255, null=True),
        ),
        migrations.AlterField(
            model_name='historicaldataset',
            name='additional_reference_information',
            field=models.TextField(blank=True, max_length=2255, null=True),
        ),
    ]
