# classes/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AcademicYear(models.Model):
    year_start = models.IntegerField()
    year_end = models.IntegerField()

    def __str__(self):
        return f"{self.year_start}-{self.year_end}"

class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes')
    lecturers = models.ManyToManyField(User, limit_choices_to={'role': 'lecturer'}, related_name='classes')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_classes')

    def __str__(self):
        return f"{self.name} ({self.academic_year})"
