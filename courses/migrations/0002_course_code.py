# Generated by Django 5.1 on 2024-09-03 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="code",
            field=models.CharField(default="DEFAULT123", max_length=10, unique=True),
        ),
    ]
