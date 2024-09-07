from django.db import models
from core.models import CustomUser  # Import the CustomUser model

class Course(models.Model):
    code = models.CharField(max_length=10, unique=True, default='DEFAULT123')
    name = models.CharField(max_length=255)
    description = models.TextField()
    lecturer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'lecturer'})
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='courses_created')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
