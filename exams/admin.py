from django.contrib import admin
from .models import Exam, ExamEligibility

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('course__name', 'assigned_class', 'date','start_time','end_time', 'created_by', 'is_active',)
    search_fields = ('course__name', )


@admin.register(ExamEligibility)
class ExamEligibilityAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_first_name', 'student_last_name', 'student_rollnumber', 'exam', 'is_allowed',) 
    search_fields = ('student_first_name', 'student_last_name', 'student_rollnumber', 'exam')
    
    def student_first_name(self, obj):
        return obj.student.first_name
    def student_last_name(self, obj):
        return obj.student.last_name
    def student_rollnumber(self, obj):
        return obj.student.student_rollnumber