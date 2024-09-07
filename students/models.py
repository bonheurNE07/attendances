from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone 
from classes.models import Class
from courses.models import Course
from django.conf import settings 

CustomUser = get_user_model()

class Student(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    student_rollnumber = models.CharField(max_length=20, unique=True)
    student_rfidnumber = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    enrollment_date = models.DateField(default=timezone.now)
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)

    assigned_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name='students')
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='students_created')
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='students_updated')

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_rollnumber})"
    
    

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    selected_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='class_attendance', null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_attendance', null=True)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='attendances_recorded')

    def __str__(self):
        return f"Attendance of {self.student} on {self.date} for {self.course} - {self.get_status_display()}"