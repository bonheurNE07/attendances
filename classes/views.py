from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import Class, AcademicYear
from core.models import CustomUser  # Assuming this is the user model with a role field

# Create a new class
@login_required
def create_class(request):
    if request.user.role not in ['admin', 'hod']:
        raise PermissionDenied

    if request.method == 'POST':
        name = request.POST.get('name')
        academic_year_id = request.POST.get('academic_year')
        lecturer_ids = request.POST.getlist('lecturers')

        academic_year = AcademicYear.objects.filter(id=academic_year_id).first()
        if not academic_year:
            messages.error(request, 'Invalid academic year selected.')
            return redirect(reverse_lazy('classes:create_class'))

        lecturers = CustomUser.objects.filter(id__in=lecturer_ids, role='lecturer')
        if not lecturers.exists():
            messages.error(request, 'Invalid lecturers selected.')
            return redirect(reverse_lazy('classes:create_class'))

        new_class = Class.objects.create(
            name=name,
            academic_year=academic_year,
            created_by=request.user
        )
        new_class.lecturers.set(lecturers)

        messages.success(request, 'Class created successfully!')
        return redirect(reverse_lazy('classes:list_classes'))
    
    academic_years = AcademicYear.objects.all()
    lecturers = CustomUser.objects.filter(role='lecturer')
    return render(request, 'classes/create_class.html', {'academic_years': academic_years, 'lecturers': lecturers})

# List all classes
@login_required
def list_classes(request):
    classes = Class.objects.all()
    return render(request, 'classes/list_classes.html', {'classes': classes})

# Update a class
@login_required
def update_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)

    if request.user.role not in ['admin', 'hod']:
        raise PermissionDenied

    if request.method == 'POST':
        class_obj.name = request.POST.get('name')
        academic_year_id = request.POST.get('academic_year')
        lecturer_ids = request.POST.getlist('lecturers')

        academic_year = AcademicYear.objects.filter(id=academic_year_id).first()
        if not academic_year:
            messages.error(request, 'Invalid academic year selected.')
            return redirect('update_class', class_id=class_obj.id)

        lecturers = CustomUser.objects.filter(id__in=lecturer_ids, role='lecturer')
        if not lecturers.exists():
            messages.error(request, 'Invalid lecturers selected.')
            return redirect('update_class', class_id=class_obj.id)

        class_obj.academic_year = academic_year
        class_obj.lecturers.set(lecturers)
        class_obj.save()

        messages.success(request, 'Class updated successfully!')
        return redirect(reverse_lazy('classes:list_classes'))

    academic_years = AcademicYear.objects.all()
    lecturers = CustomUser.objects.filter(role='lecturer')
    return render(request, 'classes/update_class.html', {'class_obj': class_obj, 'academic_years': academic_years, 'lecturers': lecturers})

# Delete a class
@login_required
def delete_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)

    if request.user.role not in ['admin', 'hod']:
        raise PermissionDenied

    class_obj.delete()
    messages.success(request, 'Class deleted successfully!')
    return redirect(reverse_lazy('classes:list_classes'))











# View to create a new academic year
@login_required
def create_academic_year(request):
    if request.user.role not in ['admin', 'hod']:
        messages.error(request, 'You are not authorized to create academic years.')
        return redirect('home')

    if request.method == 'POST':
        year_start = request.POST.get('year_start')
        year_end = request.POST.get('year_end')

        if not year_start.isdigit() or not year_end.isdigit():
            messages.error(request, 'Invalid input. Please enter valid years.')
            return redirect('classes:create_academic_year')

        year_start = int(year_start)
        year_end = int(year_end)

        if year_start >= year_end:
            messages.error(request, 'The start year must be before the end year.')
            return redirect('classes:create_academic_year')

        # Check for duplicate academic years
        if AcademicYear.objects.filter(year_start=year_start, year_end=year_end).exists():
            messages.error(request, 'This academic year already exists.')
            return redirect('classes:create_academic_year')

        AcademicYear.objects.create(year_start=year_start, year_end=year_end)
        messages.success(request, 'Academic year created successfully!')
        return redirect('classes:list_academic_years')

    return render(request, 'classes/create_academic_year.html')

# View to list all academic years
@login_required
def list_academic_years(request):
    academic_years = AcademicYear.objects.all()
    return render(request, 'classes/list_academic_years.html', {'academic_years': academic_years})

# View to update an academic year
@login_required
def update_academic_year(request, year_id):
    academic_year = get_object_or_404(AcademicYear, id=year_id)

    if request.user.role not in ['admin', 'hod']:
        messages.error(request, 'You are not authorized to update academic years.')
        return redirect('classes:list_academic_years')

    if request.method == 'POST':
        year_start = request.POST.get('year_start')
        year_end = request.POST.get('year_end')

        if not year_start.isdigit() or not year_end.isdigit():
            messages.error(request, 'Invalid input. Please enter valid years.')
            return redirect('update_academic_year', year_id=year_id)

        year_start = int(year_start)
        year_end = int(year_end)

        if year_start >= year_end:
            messages.error(request, 'The start year must be before the end year.')
            return redirect('update_academic_year', year_id=year_id)

        academic_year.year_start = year_start
        academic_year.year_end = year_end
        academic_year.save()

        messages.success(request, 'Academic year updated successfully!')
        return redirect('classes:list_academic_years')

    return render(request, 'classes/update_academic_year.html', {'academic_year': academic_year})

# View to delete an academic year
@login_required
def delete_academic_year(request, year_id):
    academic_year = get_object_or_404(AcademicYear, id=year_id)

    if request.user.role not in ['admin', 'hod']:
        messages.error(request, 'You are not authorized to delete academic years.')
        return redirect('classes:list_academic_years')

    academic_year.delete()
    messages.success(request, 'Academic year deleted successfully!')
    return redirect('classes:list_academic_years')
