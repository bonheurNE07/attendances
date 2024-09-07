from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    path('register/', views.register_employee, name='register_employee'),
    path('list/', views.list_employees, name='list_employees'),
    path('update/<int:employee_id>/', views.update_employee, name='update_employee'),
    path('delete/<int:employee_id>/', views.delete_employee, name='delete_employee'),
    path('attendance/record/', views.record_employee_attendance, name='record_employee_attendance'),
    path('attendance/list/', views.list_employee_attendance, name='list_employee_attendance'),
    path('attendance/export/', views.export_attendance_report, name='export_attendance_report'),
]
