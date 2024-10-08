# Generated by Django 5.1 on 2024-09-06 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_customuser_role"),
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
                    ("security", "Security Employee"),
                ],
                max_length=20,
            ),
        ),
    ]
