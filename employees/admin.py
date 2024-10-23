from django.contrib import admin
from .models import Employee, EmployeeAttendance

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('photo', 'first_name', 'last_name','email','employee_rfidnumber', 'role', 'date_of_birth', 'created_by',)
    search_fields = ('first_name', 'last_name', 'email', 'employee_rfidnumber', 'role')

@admin.register(EmployeeAttendance)
class EmployeeAttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee_first_name', 'employee_last_name', 'check_in_time','check_out_time', 'entry_point', 'recorded_by') 
    search_fields = ('employee__first_name', 'employee__last_name', 'entry_point', 'recorded_by__username')
    
    def employee_first_name(self, obj):
        return obj.employee.first_name
    def employee_last_name(self, obj):
        return obj.employee.last_name