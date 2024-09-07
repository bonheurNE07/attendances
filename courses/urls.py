from django.urls import path
from .views import create_course, list_courses, update_course, delete_course

app_name = 'courses'

urlpatterns = [
    path('', list_courses, name='list_courses'),
    path('create/', create_course, name='create_course'),
    path('update/<int:course_id>/', update_course, name='update_course'),
    path('delete/<int:course_id>/', delete_course, name='delete_course'),
]
