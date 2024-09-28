from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('hod', 'Head of Department'),
        ('lecturer', 'Lecturer'),
        ('finance', 'Finance Employee'),
        ('security', 'Security Employee'),
    ]
    is_hod = models.BooleanField(default=False)
    is_finance_employee = models.BooleanField(default=False)
    is_security_employee = models.BooleanField(default=False)
    is_lecturer = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
