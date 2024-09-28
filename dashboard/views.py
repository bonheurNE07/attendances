from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from students.models import Student, Attendance
from classes.models import Class
from courses.models import Course
from exams.models import Exam, ExamAttendance
from core.models import CustomUser
from students.models import Student, Attendance
from employees.models import Employee, EmployeeAttendance

@login_required
def hod_dashboard(request):
    # Get relevant data
    student_count = Student.objects.count()
    student_attendance_count = Attendance.objects.count()
    class_count = Class.objects.count()
    course_count = Course.objects.count()
    exam_count = Exam.objects.count()
    exam_attendance_count = ExamAttendance.objects.count()
    users = CustomUser.objects.count()
 

    # Pass data to the template
    context = {
        'student_count': student_count,
        'student_attendance_count': student_attendance_count,
        'class_count': class_count,
        'course_count': course_count,
        'exam_count': exam_count,
        'user_count': users,
        'attendance_count': exam_attendance_count,
    }
    return render(request, 'dashboard/hod_dashboard.html', context)


@login_required
def finance_dashboard(request):
    # Ensure the user is a finance employee
    if not request.user.is_authenticated or request.user.role != 'finance':
        raise PermissionDenied

    # Fetch data for the dashboard
    exams = Exam.objects.all()
    students = Student.objects.all()
    employees = Employee.objects.all()
    exam_attendances = ExamAttendance.objects.all()
    employee_attendances = EmployeeAttendance.objects.all()

    context = {
        'exams': exams,
        'students': students,
        'employees': employees,
        'exam_attendances': exam_attendances,
        'employee_attendances': employee_attendances,
    }

    return render(request, 'dashboard/finance_dashboard.html', context)


@login_required
def lecturer_dashboard(request):
    # Ensure the user is a lecturer
    if not request.user.is_authenticated or request.user.role != 'lecturer':
        raise PermissionDenied

    # Fetch the classes the lecturer is assigned to
    classes = request.user.classes.all()

    # Fetch the courses that the lecturer provides
    courses = Course.objects.filter(lecturer=request.user)

    # Fetch students in the lecturer's classes
    students = Student.objects.filter(assigned_class__in=classes)

    # Filter attendance records for the students and the courses taught by the lecturer
    attendances = Attendance.objects.filter(student__in=students, course__in=courses)

    # Additional context data for the dashboard
    context = {
        'students': students,
        'attendances': attendances,
        'classes': classes,
        'courses': courses,
    }

    return render(request, 'dashboard/lecturer_dashboard.html', context)


@login_required
def security_dashboard(request):
    # Ensure the user is authenticated and has a security role
    if not request.user.is_authenticated or request.user.role != 'security':
        raise PermissionDenied

    # Fetch data for the dashboard
    employees = Employee.objects.all()
    employee_attendances = EmployeeAttendance.objects.all()

    context = {
        'employees': employees,
        'employee_attendances': employee_attendances,
    }
    
    return render(request, 'dashboard/security_dashboard.html', context)
