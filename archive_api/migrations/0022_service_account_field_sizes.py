# Generated by Django 3.1.14 on 2022-05-04 00:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive_api', '0021_essdivetransfer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serviceaccount',
            name='identity',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='serviceaccount',
            name='name',
            field=models.CharField(max_length=40),
        ),
    ]