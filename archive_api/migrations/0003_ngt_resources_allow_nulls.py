# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-31 14:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive_api', '0002_order_sites_plots'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='ngee_tropics_resources',
            field=models.NullBooleanField(),
        ),
    ]
