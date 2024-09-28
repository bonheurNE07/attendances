from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from core.models import CustomUser
from .models import Course
from classes.models import Class  # Import the Class model

@login_required
def create_course(request):
    if request.user.role not in ['admin', 'hod']:
        messages.error(request, 'You are not authorized to create courses.')
        return redirect(reverse_lazy('core:home'))

    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        description = request.POST.get('description')
        lecturer_id = request.POST.get('lecturer')
        class_id = request.POST.get('assigned_class')  # Retrieve assigned class

        # Check if the course code already exists
        if Course.objects.filter(code=code).exists():
            messages.error(request, 'A course with this code already exists.')
            return redirect('courses:create_course')

        lecturer = CustomUser.objects.filter(id=lecturer_id, role='lecturer').first()
        if not lecturer:
            messages.error(request, 'Invalid lecturer selected.')
            return redirect('courses:create_course')

        assigned_class = Class.objects.filter(id=class_id).first()
        if not assigned_class:
            messages.error(request, 'Invalid class selected.')
            return redirect('courses:create_course')

        # Create the new course
        Course.objects.create(
            code=code,
            name=name,
            description=description,
            lecturer=lecturer,
            assigned_class=assigned_class,  # Add assigned class here
            created_by=request.user
        )
        messages.success(request, 'Course created successfully!')
        return redirect(reverse_lazy('courses:list_courses'))

    lecturers = CustomUser.objects.filter(role='lecturer')
    classes = Class.objects.all()  # Get all available classes

    return render(request, 'courses/create_course.html', {'lecturers': lecturers, 'classes': classes})

@login_required
def update_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.role not in ['admin', 'hod']:
        messages.error(request, 'You are not authorized to update courses.')
        return redirect(reverse_lazy('courses:list_courses'))
    
    if request.method == 'POST':
        new_code = request.POST.get('code')
        name = request.POST.get('name')
        description = request.POST.get('description')
        lecturer_id = request.POST.get('lecturer')
        class_id = request.POST.get('assigned_class')  # Get the new class ID

        # Check if the new code is different from the current code
        if new_code != course.code:
            if Course.objects.exclude(id=course_id).filter(code=new_code).exists():
                messages.error(request, 'A course with this code already exists.')
                return redirect(reverse_lazy('courses:list_courses'))

            # Update code
            course.code = new_code

        # Update other fields
        course.name = name
        course.description = description

        lecturer = CustomUser.objects.filter(id=lecturer_id, role='lecturer').first()
        if not lecturer:
            messages.error(request, 'Invalid lecturer selected.')
            return redirect(reverse_lazy('courses:list_courses'))

        course.lecturer = lecturer

        assigned_class = Class.objects.filter(id=class_id).first()  # Update the class
        if not assigned_class:
            messages.error(request, 'Invalid class selected.')
            return redirect(reverse_lazy('courses:list_courses'))

        course.assigned_class = assigned_class  # Update assigned class
        course.save()

        messages.success(request, 'Course updated successfully!')
        return redirect(reverse_lazy('courses:list_courses'))

    lecturers = CustomUser.objects.filter(role='lecturer')
    classes = Class.objects.all()  # Get all available classes

    return render(request, 'courses/update_course.html', {'course': course, 'lecturers': lecturers, 'classes': classes})


# View the list of all courses
@login_required
def list_courses(request):
    courses = Course.objects.all()
    return render(request, 'courses/list_courses.html', {'courses': courses})


# Delete a course
@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.role not in ['admin', 'hod']:
        messages.error(request, 'You are not authorized to delete courses.')
        return redirect(reverse_lazy('courses:list_courses'))

    course.delete()
    messages.success(request, 'Course deleted successfully!')
    return redirect(reverse_lazy('courses:list_courses'))
