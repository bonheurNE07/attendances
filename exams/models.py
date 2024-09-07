from django.db import models
from django.contrib.auth import get_user_model
from students.models import Student
from classes.models import Class
from courses.models import Course

CustomUser = get_user_model()

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    assigned_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='exams')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='exams_created')
    is_active = models.BooleanField(default=True)  # Flag to indicate if the exam is still active

    def __str__(self):
        return f"Exam for {self.course.name} in {self.assigned_class.name} on {self.date}"

class ExamEligibility(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_eligibilities')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='eligible_students')
    is_allowed = models.BooleanField(default=False)  # Confirmed by finance employee

    def __str__(self):
        status = 'Allowed' if self.is_allowed else 'Not Allowed'
        return f"{self.student} - {self.exam} ({status})"

class ExamAttendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_attendances')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attendance for {self.student} on {self.exam}"
