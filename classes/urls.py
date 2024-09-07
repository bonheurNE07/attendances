# classes/urls.py

from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    path('', views.list_classes, name='list_classes'),
    path('update/<int:class_id>/', views.update_class, name='update_class'),
    path('delete/<int:class_id>/', views.delete_class, name='delete_class'),
    path('create/', views.create_class, name='create_class'),
    
    path('academic_years/create/', views.create_academic_year, name='create_academic_year'),
    path('academic_years/', views.list_academic_years, name='list_academic_years'),
    path('academic_years/update/<int:year_id>/', views.update_academic_year, name='update_academic_year'),
    path('academic_years/delete/<int:year_id>/', views.delete_academic_year, name='delete_academic_year'),
]

