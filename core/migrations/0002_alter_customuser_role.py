# Generated by Django 5.1 on 2024-09-05 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Admin"),
                    ("hod", "Head of Department"),
                    ("lecturer", "Lecturer"),
                    ("finance", "Finance Employee"),
                    ("employees", "Employee"),
                ],
                max_length=20,
            ),
        ),
    ]
