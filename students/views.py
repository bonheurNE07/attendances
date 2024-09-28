import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.utils import timezone 
from django.contrib import messages
from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4

from .models import Student, Attendance
from classes.models import Class, AcademicYear
from courses.models import Course

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
    try:
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
    except PermissionDenied:
        print("user non authorized")
        return redirect('core:home')
    
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
    if request.user.role == 'admin' or request.user.role == 'finance':
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

    # Get assigned classes and courses for the user
    if request.user.role == 'lecturer':
        lecturer = request.user
        assigned_classes = Class.objects.filter(lecturers__in=[lecturer])
        assigned_courses = Course.objects.filter(lecturer=lecturer)
    else:
        assigned_classes = Class.objects.all()
        assigned_courses = Course.objects.all()

    if request.method == 'POST':
        selected_class_id = request.POST.get('selected_class') or None
        selected_course_id = request.POST.get('selected_course') or None
        rfid_number = request.POST.get('rfid')

        # Only proceed if both class and course are selected
        if selected_class_id and selected_course_id and rfid_number:
            selected_class = get_object_or_404(Class, id=selected_class_id)
            selected_course = get_object_or_404(Course, id=selected_course_id)

            try:
                # Ensure the student is in the selected class
                student = Student.objects.get(student_rfidnumber=rfid_number, assigned_class=selected_class)

                # Check if attendance already exists for this student, class, course, and date
                today = timezone.now().date()
                attendance = Attendance.objects.filter(
                    student=student,
                    selected_class=selected_class,
                    course=selected_course,
                    date=today
                ).first()

                if attendance:
                    # If attendance exists but check-out not recorded, record check-out time
                    if not attendance.check_out:
                        attendance.check_out = timezone.now()
                        attendance.save()
                        text_to_speech('Check-out recorded')
                        status = 'checked out'
                        messages.success(request, f'Check-out recorded for {student.first_name} {student.last_name} in {selected_class} for {selected_course}.')
                    else:
                        status = 'already checked out'
                        messages.error(request, f'{student.first_name} {student.last_name} has already checked out for {selected_course} today.')

                else:
                    print('first time record')
                    # If no attendance exists, record check-in time
                    Attendance.objects.create(
                        student=student,
                        selected_class=selected_class,
                        course=selected_course,
                        status='P',
                        recorded_by=request.user,
                        check_in=timezone.now()
                    )
                    text_to_speech('Present')
                    status = 'checked in'
                    messages.success(request, f'Check-in recorded for {student.first_name} {student.last_name} in {selected_class} for {selected_course}.')
            
            except Student.DoesNotExist:
                messages.error(request, 'Student not found in the selected class. Please check the RFID number.')
        else:
            messages.error(request, 'Please select both a class and a course before submitting.')

    # Render the template with the necessary data
    return render(request, 'students/take_attendance.html', {
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
    student_stats = {}

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
    headers = ['Student Name', 'Roll Number', 'Date', 'Status', 'Check-in Time', 'Check-out Time', 'Total Hours', 'Recorded By']
    writer.writerow(headers)

    # Write data rows
    for attendance in attendances:
        check_in = attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else 'N/A'
        check_out = attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else 'N/A'
        total_hours = (attendance.check_out - attendance.check_in).total_seconds() / 3600 if attendance.check_in and attendance.check_out else 0

        row = [
            f"{attendance.student.first_name} {attendance.student.last_name}",
            attendance.student.student_rollnumber,
            attendance.date,
            attendance.get_status_display(),
            check_in,
            check_out,
            round(total_hours, 2),  # Rounded to 2 decimal places
            attendance.recorded_by
        ]
        writer.writerow(row)

        # Track stats for summary
        student_name = f"{attendance.student.first_name} {attendance.student.last_name}"
        if student_name not in student_stats:
            student_stats[student_name] = {'days_attended': 0, 'total_hours': 0.0}

        if attendance.status == 'P':  # Count only if the student was present
            student_stats[student_name]['days_attended'] += 1
            student_stats[student_name]['total_hours'] += total_hours
            

    # Add summary section
    writer.writerow([])  # Blank line
    writer.writerow(['Summary'])
    writer.writerow(['Student Name', 'Total Days Attended', 'Total Hours'])

    for student_name, stats in student_stats.items():
        summary_row = [
            student_name,
            stats['days_attended'],
            round(stats['total_hours'], 2)  # Rounded to 2 decimal places
        ]
        writer.writerow(summary_row)

    return response


@login_required
def export_student_attendance_pdf(request):
    if is_employee(request.user):
        raise PermissionDenied

    selected_class_id = request.GET.get('selected_class')
    selected_course_id = request.GET.get('selected_course')
    selected_date = request.GET.get('selected_date')

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

    # Create the PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="attendance_records_{selected_date}.pdf"'

    # Generate the PDF
    pdf_canvas = canvas.Canvas(response, pagesize=letter)
    pdf_canvas.setTitle("Attendance Records")

    # Add a title
    pdf_canvas.setFont("Helvetica-Bold", 20)
    pdf_canvas.drawString(1 * inch, 10.5 * inch, "Attendance Report")

    # Write header information
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(1 * inch, 10 * inch, f"Class: {selected_class.name if selected_class else 'N/A'}")
    pdf_canvas.drawString(1 * inch, 9.75 * inch, f"Course: {selected_course.name if selected_course else 'N/A'}")
    pdf_canvas.drawString(1 * inch, 9.5 * inch, f"Date: {selected_date if selected_date else 'N/A'}")
    pdf_canvas.drawString(1 * inch, 9.25 * inch, f"Downloaded by: {request.user.username}")

    # Write table headers
    pdf_canvas.drawString(1 * inch, 8.8 * inch, "Student Name")
    pdf_canvas.drawString(3 * inch, 8.8 * inch, "Roll Number")
    pdf_canvas.drawString(4.5 * inch, 8.8 * inch, "Date")
    pdf_canvas.drawString(5.75 * inch, 8.8 * inch, "Check-in")
    pdf_canvas.drawString(7 * inch, 8.8 * inch, "Check-out")
    pdf_canvas.drawString(8.5 * inch, 8.8 * inch, "Total Hours")

    # Write attendance data
    y = 8.55 * inch
    student_stats = {}

    for attendance in attendances:
        student_name = f"{attendance.student.first_name} {attendance.student.last_name}"
        roll_number = attendance.student.student_rollnumber
        date = str(attendance.date)
        check_in = attendance.check_in.strftime('%H:%M:%S') if attendance.check_in else 'N/A'
        check_out = attendance.check_out.strftime('%H:%M:%S') if attendance.check_out else 'N/A'
        total_time = (attendance.check_out - attendance.check_in).total_seconds() / 3600 if attendance.check_in and attendance.check_out else 0

        # Track total days and hours for the student
        if student_name not in student_stats:
            student_stats[student_name] = {'days': 0, 'hours': 0}
        if attendance.status == 'P':
            student_stats[student_name]['days'] += 1
            student_stats[student_name]['hours'] += total_time

        pdf_canvas.drawString(1 * inch, y, student_name)
        pdf_canvas.drawString(3 * inch, y, roll_number)
        pdf_canvas.drawString(4.5 * inch, y, date)
        pdf_canvas.drawString(5.75 * inch, y, check_in)
        pdf_canvas.drawString(7 * inch, y, check_out)
        pdf_canvas.drawString(8.5 * inch, y, f"{round(total_time, 2)} hours")

        y -= 0.25 * inch

    # Add summary table at the end
    y -= 0.5 * inch
    pdf_canvas.setFont("Helvetica-Bold", 14)
    pdf_canvas.drawString(1 * inch, y, "Student Attendance Summary")
    y -= 0.25 * inch
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(1 * inch, y, "Student Name")
    pdf_canvas.drawString(4 * inch, y, "Total Days")
    pdf_canvas.drawString(6 * inch, y, "Total Hours")

    y -= 0.25 * inch
    for student, stats in student_stats.items():
        pdf_canvas.drawString(1 * inch, y, student)
        pdf_canvas.drawString(4 * inch, y, str(stats['days']))
        pdf_canvas.drawString(6 * inch, y, f"{round(stats['hours'], 2)} hours")
        y -= 0.25 * inch

    # Finalize the PDF
    pdf_canvas.showPage()
    pdf_canvas.save()

    return response

