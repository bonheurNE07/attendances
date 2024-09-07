# Generated by Django 5.1 on 2024-09-05 09:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("classes", "0001_initial"),
        ("students", "0005_attendance_course"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="selected_class",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="class_attendance",
                to="classes.class",
            ),
        ),
    ]