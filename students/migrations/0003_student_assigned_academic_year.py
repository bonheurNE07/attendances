# Generated by Django 5.1 on 2024-09-04 15:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("classes", "0001_initial"),
        ("students", "0002_alter_student_enrollment_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="assigned_academic_year",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="students",
                to="classes.academicyear",
            ),
        ),
    ]
