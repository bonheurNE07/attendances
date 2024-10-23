from django.contrib import admin
from .models import Class, AcademicYear


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('year_start', 'year_end',)
    search_fields = ('year_start', 'year_end',)

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year','lecturers_list', 'created_at', 'created_by') 
    search_fields = ('name',)
    
    def lecturers_list(self, obj):
        return ", ".join([lecturer.username for lecturer in obj.lecturers.all()])