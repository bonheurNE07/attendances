from django.db import models
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

# Define entry points choices
ENTRY_POINTS = [
    ('Main Gate', 'Main Gate'),
    ('Office Entrance', 'Office Entrance'),
    ('Gate A', 'Gate A'),
    ('Gate B', 'Gate B'),
    ('Back Entrance', 'Back Entrance'),
]

class Employee(models.Model):
    ROLE_CHOICES = [
        ('Finance', 'Finance Employee'),
        ('Security', 'Security Employee'),
        ('Other', 'Other Employee'),
    ]
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    employee_rfidnumber = models.CharField(max_length=50, unique=True)  # RFID for employee entry tracking
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='employee_photos/', blank=True, null=True)  # Employee photo field
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='employees_created')

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_role_display()}"

class EmployeeAttendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    entry_point = models.CharField(max_length=100, choices=ENTRY_POINTS)  # Entry point choice field
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='employee_attendances_recorded')

    def __str__(self):
        return f"Attendance for {self.employee} on {self.check_in_time.date() if self.check_in_time else 'N/A'}"
