from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.list_students, name='list_students'),
    path('register/', views.register_student, name='register_student'),
    path('attendance/', views.take_attendance, name='take_attendance'),
    path('view-attendance/', views.view_attendance_list, name='view_attendance_list'),
    path('student/update/<int:id>/', views.update_student, name='update_student'),
    path('student/delete/<int:id>/', views.delete_student, name='delete_student'),
    path('export-attendance/', views.export_student_attendance, name='export_student_attendance'),
    path('export_attendance_pdf/', views.export_student_attendance_pdf, name='export_student_attendance_pdf'),
]
