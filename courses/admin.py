from django.contrib import admin
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name','description','lecturer__username','assigned_class__name', 'created_by__username','created_at',)
    search_fields = ('code', 'name',)
