# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-30 23:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0003_auto_20150831_1118'),
    ]

    operations = [
        migrations.RenameField(
            model_name='board',
            old_name='class_id',
            new_name='course_id',
        ),
    ]
