from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import Student, Attendance
from classes.models import Class, AcademicYear
from courses.models import Course
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils import timezone 

from django.http import HttpResponse
import csv

from core.views import text_to_speech




CustomUser = get_user_model()

def is_hod(user):
    return user.is_authenticated and user.role == 'hod'

def is_admin(user):
    return user.is_authenticated and user.is_superuser

def is_finance(user):
    return user.is_authenticated and user.role == 'finance'

def is_lecturer(user):
    return user.is_authenticated and user.role == 'lecturer'

def is_employee(user):
    return user.is_authenticated and user.role == 'security'

def can_manage_students(user):
    return is_hod(user) or is_admin(user) or is_finance(user)


@login_required
def register_student(request):
    if request.user.role == 'admin' or request.user.role == 'finance':
        if request.method == 'POST':
            photo = request.FILES.get('photo')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            student_rollnumber = request.POST.get('student_rollnumber')
            student_rfidnumber = request.POST.get('student_rfidnumber')
            date_of_birth = request.POST.get('date_of_birth')
            assigned_class_id = request.POST.get('assigned_class')
            assigned_class = Class.objects.get(id=assigned_class_id) if assigned_class_id else None

            # Check if the RFID number or roll number already exists
            if Student.objects.filter(student_rfidnumber=student_rfidnumber).exists():
                messages.error(request, 'A student with this RFID number already exists.')
                return redirect('students:register_student')
            
            if Student.objects.filter(student_rollnumber=student_rollnumber).exists():
                messages.error(request, 'A student with this roll number already exists.')
                return redirect('students:register_student')
            
            
            Student.objects.create(
                photo=photo,
                first_name=first_name,
                last_name=last_name,
                email=email,
                student_rollnumber=student_rollnumber,
                student_rfidnumber=student_rfidnumber,
                date_of_birth=date_of_birth,
                assigned_class=assigned_class,
                created_by=request.user
            )
            print('creation done')

            messages.success(request, 'Student registered successfully!')
            return redirect(reverse_lazy('students:list_students'))

        # For GET requests
        classes = Class.objects.all()
        academic_years = AcademicYear.objects.all()
        return render(request, 'students/register_student.html', {
            'classes': classes,
            'academic_years': academic_years
        })
    else:
        raise PermissionDenied
    
@login_required
def update_student(request, id):
    if request.user.role == 'lecturer' or request.user.role == 'security':
            raise PermissionDenied
    else:
        student = get_object_or_404(Student, id=id)
        if request.method == 'POST':
            # Update student data from form inputs
            student.photo = request.FILES.get('photo', student.photo)
            student.first_name = request.POST.get('first_name')
            student.last_name = request.POST.get('last_name')
            student.email = request.POST.get('email')
            student.student_rollnumber = request.POST.get('student_rollnumber')
            date_of_birth = request.POST.get('date_of_birth')
            student.student_rfidnumber = request.POST.get('rfid')
            assigned_class_id = request.POST.get('assigned_class')
            assigned_class = Class.objects.get(id=assigned_class_id) if assigned_class_id else None

            if date_of_birth:
                student.date_of_birth = date_of_birth

            # Update assigned class
            if assigned_class_id:
                student.assigned_class_id = assigned_class_id

            
            # Validate and save
            if not student.student_rfidnumber.isdigit() or len(student.student_rfidnumber) != 10:
                messages.error(request, 'Invalid RFID Number. Must be exactly 10 digits.')
                return redirect('update_student', student_id=student.id)

            student.updated_by = request.user
            student.save()
            messages.success(request, 'Student updated successfully!')
            return redirect(reverse_lazy('students:list_students'))
        
        
        classes = Class.objects.all()
        return render(request, 'students/update_student.html', {'student': student, 'classes': classes})

@login_required
#@user_passes_test(lambda user: is_hod(user) or is_admin(user))
def list_students(request):
    user = request.user
    if user.role == 'lecturer':
        # Get the classes that the lecturer is assigned to
        lecturer_classes = user.classes.all()
        # Get students from these classes
        students = Student.objects.filter(assigned_class__in=lecturer_classes)
    elif user.role in ['hod', 'admin', 'finance']:
        # List all students if the user is HOD, admin, or finance
        students = Student.objects.all()
    else:
        students = Student.objects.none()  # No students if the user role is not recognized
        raise PermissionDenied

    context = {
        'students': students
    }
    return render(request, 'students/list_students.html', context)


@login_required
#@user_passes_test(can_manage_students)
def delete_student(request, id):
    if request.user.role != 'admin' or request.user.role != 'finance':
        student = get_object_or_404(Student, id=id)
        if request.method == 'POST':
            student.delete()
            messages.success(request, 'Student deleted successfully!')
            return redirect(reverse_lazy('students:list_students'))

        return render(request, 'students/delete_student.html', {'student': student})
    else:
        raise PermissionDenied


@login_required
def take_attendance(request):
    if is_employee(request.user) or is_hod(request.user):
        raise PermissionDenied

    # Initialize variables
    student = None
    status = 'not ready'
    selected_class_id = None
    selected_course_id = None
    assigned_classes = []
    assigned_courses = []

    if request.user.role == 'lecturer':
        lecturer = request.user
        # Get classes and courses assigned to the lecturer
        assigned_classes = Class.objects.filter(lecturers=lecturer)
        assigned_courses = Course.objects.filter(lecturer=lecturer)

    assigned_classes = Class.objects.all()
    assigned_courses = Course.objects.all()

    if request.method == 'POST':
        selected_class_id = request.POST.get('selected_class') or None
        selected_course_id = request.POST.get('selected_course') or None
        rfid_number = request.POST.get('rfid')

        # Only proceed if both class and course are selected
        if selected_class_id and selected_course_id and rfid_number:
            selected_class = Class.objects.filter(id=selected_class_id).first()
            selected_course = Course.objects.filter(id=selected_course_id).first()

            if selected_class and selected_course:
                try:
                    # Ensure the student is in the selected class
                    student = Student.objects.get(student_rfidnumber=rfid_number, assigned_class=selected_class)

                    # Check if attendance already exists for this student, class, course, and date
                    today = timezone.now().date()
                    if Attendance.objects.filter(student=student, selected_class=selected_class, course=selected_course, date=today).exists():
                        status = 'ready'
                        messages.error(request, f'Attendance for {student.first_name} {student.last_name} has already been recorded today for {selected_course}.')
                    else:
                        status = 'not ready'
                        # Record attendance if not already taken
                        Attendance.objects.create(student=student, selected_class=selected_class, course=selected_course, status='P', recorded_by=request.user)
                        text_to_speech(f'{student.first_name} Present')
                        messages.success(request, f'Attendance recorded for {student.first_name} {student.last_name} in {selected_class} for {selected_course}.')
                
                except Student.DoesNotExist:
                    messages.error(request, 'Student not found in the selected class. Please check the RFID number.')
            else:
                messages.error(request, 'Invalid class or course selection.')
        else:
            messages.error(request, 'Please select both a class and a course before submitting.')

    # Render the template with the necessary data
    return render(request, 'students/take_attendance.html', {
        'student': student,
        'student': student,
        'status': status,
        'assigned_classes': assigned_classes,
        'assigned_courses': assigned_courses,
        'selected_class_id': selected_class_id,
        'selected_course_id': selected_course_id,
    })


@login_required
def view_attendance_list(request):
    if is_employee(request.user):
        raise PermissionDenied
    
    # Initialize variables
    attendances = []
    selected_class_id = request.GET.get('selected_class') or None
    selected_course_id = request.GET.get('selected_course') or None
    selected_date = request.GET.get('selected_date') or None
    assigned_classes = []
    assigned_courses = []

    lecturer = request.user
    # Get classes and courses assigned to the lecturer
    assigned_classes = Class.objects.filter(lecturers=lecturer)
    assigned_courses = Course.objects.filter(lecturer=lecturer)

    if request.user.role == 'hod':
        assigned_classes = Class.objects.all()
        assigned_courses = Course.objects.all()

    print(assigned_classes)
    print(assigned_courses)
    if selected_class_id and selected_course_id:
        selected_class = Class.objects.filter(id=selected_class_id).first()
        selected_course = Course.objects.filter(id=selected_course_id).first()

        if selected_class and selected_course:
            # Filter attendance records by selected class, course, and date
            attendances = Attendance.objects.filter(
                selected_class=selected_class,
                course=selected_course
            )
            
            if selected_date:
                try:
                    selected_date = timezone.datetime.strptime(selected_date, "%Y-%m-%d").date()
                    attendances = attendances.filter(date=selected_date)
                except ValueError:
                    messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
        else:
            messages.error(request, 'Invalid class or course selection.')
    else:
        messages.error(request, 'Please select both a class and a course to view attendance.')

    return render(request, 'students/view_attendance_list.html', {
        'attendances': attendances,
        'assigned_classes': assigned_classes,
        'assigned_courses': assigned_courses,
        'selected_class_id': selected_class_id,
        'selected_course_id': selected_course_id,
        'selected_date': selected_date,
    })



@login_required
def export_student_attendance(request):
    if is_employee(request.user):
        raise PermissionDenied

    selected_class_id = request.GET.get('selected_class')
    selected_course_id = request.GET.get('selected_course')
    selected_date = request.GET.get('selected_date')

    # Initialize variables
    attendances = []
    selected_class = None
    selected_course = None

    if selected_class_id and selected_course_id:
        selected_class = Class.objects.filter(id=selected_class_id).first()
        selected_course = Course.objects.filter(id=selected_course_id).first()

        if selected_class and selected_course:
            attendances = Attendance.objects.filter(
                selected_class=selected_class,
                course=selected_course
            )
            
            if selected_date:
                try:
                    selected_date = timezone.datetime.strptime(selected_date, "%Y-%m-%d").date()
                    attendances = attendances.filter(date=selected_date)
                except ValueError:
                    messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')

    # Create HTTP response with CSV content
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_records.csv"'

    writer = csv.writer(response)
    # Write header
    headers = ['Student Name', 'Roll Number', 'Date', 'Status', 'Recorded By']
    writer.writerow(headers)

    # Write data rows
    for attendance in attendances:
        row = [
            f"{attendance.student.first_name} {attendance.student.last_name}",
            attendance.student.student_rollnumber,
            attendance.date,
            attendance.get_status_display(),
            attendance.recorded_by
        ]
        writer.writerow(row)

    return response