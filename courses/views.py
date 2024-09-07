from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib import messages
from core.models import CustomUser
from .models import Course

# Create a new course
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

        lecturer = CustomUser.objects.filter(id=lecturer_id, role='lecturer').first()
        if not lecturer:
            messages.error(request, 'Invalid lecturer selected.')
            return redirect('create_course')

        course = Course.objects.create(
            code=code,
            name=name,
            description=description,
            lecturer=lecturer,
            created_by=request.user
        )
        messages.success(request, 'Course created successfully!')
        return redirect(reverse_lazy('courses:list_courses'))

    lecturers = CustomUser.objects.filter(role='lecturer')
    return render(request, 'courses/create_course.html', {'lecturers': lecturers})


# View the list of all courses
@login_required
def list_courses(request):
    courses = Course.objects.all()
    return render(request, 'courses/list_courses.html', {'courses': courses})


# Update a course
@login_required
def update_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.user.role not in ['admin', 'hod']:
        messages.error(request, 'You are not authorized to update courses.')
        return redirect(reverse_lazy('courses:list_courses'))
    
    if request.method == 'POST':
        course.code = request.POST.get('code')
        course.name = request.POST.get('name')
        course.description = request.POST.get('description')
        lecturer_id = request.POST.get('lecturer')

        lecturer = CustomUser.objects.filter(id=lecturer_id, role='lecturer').first()
        if not lecturer:
            messages.error(request, 'Invalid lecturer selected.')
            return redirect('update_course', course_id=course.id)

        course.lecturer = lecturer
        course.save()

        messages.success(request, 'Course updated successfully!')
        return redirect(reverse_lazy('courses:list_courses'))

    lecturers = CustomUser.objects.filter(role='lecturer')
    return render(request, 'courses/update_course.html', {'course': course, 'lecturers': lecturers})


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
