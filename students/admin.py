from django.contrib import admin
from .models import Student, Attendance

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email','student_rollnumber', 'assigned_class__name', 'student_rfidnumber', 'date_of_birth', 'enrollment_date', 'created_by__username', 'updated_by__username')
    search_fields = ('first_name','last_name', 'student_rollnumber', 'student_rfidnumber', 'assigned_class__name')

    def student_first_name(self, obj):
        return obj.first_name
    def student_last_name(self, obj):
        return obj.last_name
    def student_rollnumber(self, obj):
        return obj.student_rollnumber
   

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student__first_name', 'student__last_name', 'student__student_rollnumber', 'course__name','date', 'status', 'check_in', 'check_out', 'recorded_by__username') 
    search_fields = ('student__first_name', 'student__last_name', 'student__student_rollnumber',)
    
    def student_first_name(self, obj):
        return obj.student.first_name
    def student_last_name(self, obj):
        return obj.student.last_name
    def student_rollnumber(self, obj):
        return obj.student.student_rollnumber
   