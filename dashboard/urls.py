from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('finance/', views.finance_dashboard, name='finance_dashboard'),
    path('lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('security/', views.security_dashboard, name='security_dashboard'),
    # Add other role-specific dashboards here
]
