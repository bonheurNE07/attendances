from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('create/', views.create_exam, name='create_exam'),
    path('list/', views.list_exams, name='list_exams'),
    path('update/<int:exam_id>/', views.update_exam, name='update_exam'),
    path('delete/<int:exam_id>/', views.delete_exam, name='delete_exam'),
    path('confirm-eligibility/<int:exam_id>/', views.confirm_exam_eligibility, name='confirm_exam_eligibility'),
    path('attendance/<int:exam_id>/', views.exam_attendance_check, name='exam_attendance_check'),
    path('attendance/list/', views.list_exam_attendance, name='list_exam_attendance'),
    path('attendance/export/', views.export_exam_attendance, name='export_exam_attendance'),
]
