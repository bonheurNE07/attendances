import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.http import HttpResponse
from django.utils.timezone import localtime

from .models import Exam, ExamEligibility, ExamAttendance
from students.models import Student
from classes.models import Class
from courses.models import Course
from students.models import Attendance
from core.views import text_to_speech

from Devices.servo import set_angle
import time
from datetime import datetime, date

from io import BytesIO
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas

def is_hod(user):
    return user.is_authenticated and user.role == 'hod'

def is_finance(user):
    return user.is_authenticated and user.role == 'finance'
    

@login_required
def get_courses_by_class(request):
    class_id = request.GET.get('class_id')
    print(f"Received class_id: {class_id}")  # Debug print
    courses = Course.objects.filter(assigned_class__id=class_id)
    print(f"Filtered courses: {courses}")  # Debug print to check what courses are being returned
    course_list = [{'id': course.id, 'name': course.name} for course in courses]
    return JsonResponse({'courses': course_list})


@login_required
def create_exam(request):
    if request.user.role != 'hod':
        raise PermissionDenied("Only HOD can create exams.")

    classes = Class.objects.all()
    courses = Course.objects.all()  # Initialize with no courses

    # Check if a class was selected in the GET or POST request
    selected_class_id = request.POST.get('assigned_class') if request.method == 'POST' else None

    if selected_class_id:
        # Filter courses by the selected class if a class is selected
        courses = Course.objects.filter(assigned_class__id=selected_class_id)

    if request.method == 'POST':
        course_id = request.POST.get('course')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        # Validate start_time and end_time
        if not start_time or not end_time:
            messages.error(request, 'Start time and end time cannot be empty.')
            return render(request, 'exams/create_exam.html', {
                'classes': classes,
                'courses': courses,
                'selected_class_id': selected_class_id
            })

        # Adjusting the format to match "HH:MM"
        start_time = datetime.strptime(start_time, "%H:%M")
        end_time = datetime.strptime(end_time, "%H:%M")

        course = get_object_or_404(Course, id=course_id)
        assigned_class = get_object_or_404(Class, id=selected_class_id)

        Exam.objects.create(
            course=course,
            assigned_class=assigned_class,
            date=date,
            start_time=start_time.time(),
            end_time=end_time.time(),
            created_by=request.user
        )

        messages.success(request, 'Exam created successfully.')
        return redirect(reverse_lazy('exams:list_exams'))

    return render(request, 'exams/create_exam.html', {
        'classes': classes,
        'courses': courses,
        'selected_class_id': selected_class_id
    })


@login_required
def list_exams(request):
    if request.user.role == 'hod' or request.user.role == 'finance':
        exams = Exam.objects.all()
        return render(request, 'exams/list_exams.html', {'exams': exams})
    else:
        raise PermissionDenied

@login_required
def update_exam(request, exam_id):
    if not is_hod(request.user):
        raise PermissionDenied("Only HOD can update exams.")

    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        course_id = request.POST.get('course')
        class_id = request.POST.get('assigned_class')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        # Adjusting the format to match "HH:MM"
        start_time = datetime.strptime(start_time, "%H:%M")
        end_time = datetime.strptime(end_time, "%H:%M")

        course = get_object_or_404(Course, id=course_id)
        assigned_class = get_object_or_404(Class, id=class_id)

        exam.course = course
        exam.assigned_class = assigned_class
        exam.date = date
        exam.start_time = start_time.time()
        exam.end_time = end_time.time()
        exam.save()

        messages.success(request, 'Exam updated successfully.')
        return redirect(reverse_lazy('exams:list_exams'))

    classes = Class.objects.all()
    courses = Course.objects.all()
    return render(request, 'exams/update_exam.html', {'exam': exam, 'classes': classes, 'courses': courses})

@login_required
def delete_exam(request, exam_id):
    if not is_hod(request.user):
        raise PermissionDenied("Only HOD can delete exams.")

    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted successfully.')
        return redirect(reverse_lazy('exams:list_exams'))

    return render(request, 'exams/delete_exam.html', {'exam': exam})

@login_required
def confirm_exam_eligibility(request, exam_id):
    # Ensure only Finance users can access this view
    if not is_finance(request.user):
        raise PermissionDenied("Only Finance employees can confirm exam eligibility.")

    exam = get_object_or_404(Exam, id=exam_id)

    # Get all students in the class assigned to the exam
    students_in_class = Student.objects.filter(assigned_class=exam.assigned_class)

    # Calculate attendance percentage for each student in the course
    eligible_students = []
    for student in students_in_class:
        # Get the total number of lectures held for the course (number of Attendance records for all students)
        total_attendance_count = Attendance.objects.filter(
            course=exam.course, 
            selected_class=exam.assigned_class
        ).values('date').distinct().count()

        # Get the student's attendance count (status 'P' for present)
        student_attendance_count = Attendance.objects.filter(
            student=student, 
            course=exam.course,
            selected_class=exam.assigned_class,
            status='P'
        ).count()

        # Calculate attendance percentage
        if total_attendance_count > 0:
            attendance_percentage = (student_attendance_count / total_attendance_count) * 100
        else:
            attendance_percentage = 0

        # Determine eligibility (if attendance >= 70%)
        is_eligible = attendance_percentage >= 70

        eligible_students.append({
            'student': student,
            'attendance_percentage': attendance_percentage,
            'is_eligible': is_eligible
        })

    # Handle the form submission to confirm eligibility
    if request.method == 'POST':
        for entry in eligible_students:
            student = entry['student']
            confirm_eligible = request.POST.get(f'confirm_{student.id}')

            # Only allow eligibility confirmation if the student has met the 70% attendance requirement
            if entry['is_eligible']:
                is_allowed = True if confirm_eligible else False
                # Update or create the eligibility record
                ExamEligibility.objects.update_or_create(
                    exam=exam,
                    student=student,
                    defaults={'is_allowed': is_allowed}
                )
            else:
                # Automatically mark the student as ineligible if attendance is less than 70%
                ExamEligibility.objects.update_or_create(
                    exam=exam,
                    student=student,
                    defaults={'is_allowed': False}
                )

        messages.success(request, "Eligibility confirmed successfully.")
        return redirect(reverse_lazy('exams:list_exams'))

    # Render the template
    return render(request, 'exams/confirm_exam_eligibility.html', {
        'exam': exam,
        'eligible_students': eligible_students
    })

from django.utils import timezone

@login_required
def exam_attendance_check(request, exam_id):
    if request.user.role == 'finance':
        # Get the exam based on the ID passed to the view
        exam = get_object_or_404(Exam, id=exam_id)

        # Check if the exam is active
        if not exam.is_active:
            messages.error(request, "This exam is not active.")
            return redirect(reverse_lazy('exams:list_exams'))

        # Initialize student and status variables
        student = None
        status = 'not ready'

        # Get the current date and time
        current_date = timezone.localdate()  # Get current date
        current_time = timezone.localtime().time() # .strftime("%I:%M %p") # Get current time
        # formatted_time = current_time.strftime("%I:%M %p")
        
        

        # Check if the exam date matches today's date
        if current_date != exam.date:
            messages.error(request, f"Exam attendance is only allowed on the exam date ({exam.date}).")
            return redirect(reverse_lazy('exams:list_exams'))

        # Handle POST request for checking attendance
        if request.method == 'POST':
            rfid_number = request.POST.get('rfid_number')

            try:
                # Find the student based on RFID number
                student = Student.objects.get(student_rfidnumber=rfid_number)
            except Student.DoesNotExist:
                messages.error(request, "Student not found.")
                text_to_speech('Not Allowed!')
                return redirect('exams:exam_attendance_check', exam_id=exam_id)

            # Check if the student is eligible for the exam
            eligibility = ExamEligibility.objects.filter(student=student, exam=exam, is_allowed=True).first()
            if not eligibility:
                messages.error(request, "Student is not eligible to take this exam.")
                text_to_speech('Not Eligible')
                return redirect('exams:exam_attendance_check', exam_id=exam_id)

            # Check if the current time is before the exam start time
            if current_time < exam.start_time:
                messages.error(request, f"Check-in is only allowed after the exam starts at {exam.start_time}.")
                return redirect('exams:exam_attendance_check', exam_id=exam_id)
            if current_time > exam.end_time:
                messages.error(request, f"Check-in is only allowed before the exam ends at {exam.end_time}.")
                return redirect('exams:exam_attendance_check', exam_id=exam_id)

            # Get or create the attendance record for the student and exam
            attendance, created = ExamAttendance.objects.get_or_create(student=student, exam=exam)

            if attendance.check_in_time and not attendance.check_out_time:
                # Student is checking out
                if current_time > exam.end_time:
                    messages.error(request, f"Check-out is only allowed before the exam ends at {exam.end_time}.")
                    return redirect('exams:exam_attendance_check', exam_id=exam_id)
                attendance.check_out_time = timezone.now()
                attendance.save()
                messages.success(request, f"Check-out recorded for {student.first_name} {student.last_name}.")
                text_to_speech('Thank you.')
                set_angle(90)
                time.sleep(2.1)
                set_angle(0)
            elif not attendance.check_in_time:
                set_angle(90)
                time.sleep(2.1)
                set_angle(0)
                # Student is checking in
                attendance.check_in_time = timezone.now()
                attendance.save()
                messages.success(request, f"Check-in recorded for {student.first_name} {student.last_name}.")
            else:
                text_to_speech('Thank you.')
                messages.info(request, "Student has already checked in and out.")
                set_angle(90)
                time.sleep(2.1)
                set_angle(0)

        # Render the attendance check-in page with student info if available
        return render(request, 'exams/exam_attendance_check.html', {
            'exam': exam,
            'student': student,
        })
    else:
        raise PermissionDenied

@login_required
def list_exam_attendance(request):
    if request.user.role == 'hod' or request.user.role == 'finance':
        exams = Exam.objects.all()  # Get all exams for filtering

        exam_id = request.GET.get('exam')
        class_id = request.GET.get('class')
        date = request.GET.get('date')

        # Filter the attendance records based on the selected exam, class, and date
        attendances = ExamAttendance.objects.all()

        if exam_id:
            attendances = attendances.filter(exam_id=exam_id)
        if class_id:
            attendances = attendances.filter(exam__assigned_class_id=class_id)
        if date:
            attendances = attendances.filter(exam__date=date)

        return render(request, 'exams/list_exam_attendance.html', {
            'attendances': attendances,
            'exams': exams,
            'selected_exam': exam_id,
            'selected_class': class_id,
            'selected_date': date,
        })
    else:
        raise PermissionDenied

@login_required
def export_exam_attendance(request):
    if request.user.role == 'hod' or request.user.role == 'finance':
        exam_id = request.GET.get('exam')
        class_id = request.GET.get('class')
        date = request.GET.get('date')

        # Filter the attendance records based on the selected exam, class, and date
        attendances = ExamAttendance.objects.all()

        if exam_id:
            attendances = attendances.filter(exam_id=exam_id)
        if class_id:
            attendances = attendances.filter(exam__assigned_class_id=class_id)
        if date:
            attendances = attendances.filter(exam__date=date)

        # Create the HTTP response for CSV export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="exam_attendance_report_{date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Student ID', 'Student Name', 'Exam', 'Check-in Time', 'Check-out Time'])

        for attendance in attendances:
            check_in = localtime(attendance.check_in_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_in_time else 'N/A'
            check_out = localtime(attendance.check_out_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_out_time else 'N/A'
            writer.writerow([
                attendance.student.student_rollnumber,
                f"{attendance.student.first_name} {attendance.student.last_name}",
                f"{attendance.exam.course.name} ({attendance.exam.assigned_class.name})",
                check_in,
                check_out
            ])
        text_to_speech('Exported')

        return response
    else:
        raise PermissionDenied



@login_required
def export_exam_attendance_pdf(request):
    if request.user.role == 'hod' or request.user.role == 'finance':
        exam_id = request.GET.get('exam')
        class_id = request.GET.get('class')
        date_ = request.GET.get('date')

        # Filter the attendance records based on the selected exam, class, and date
        attendances = ExamAttendance.objects.all()

        if exam_id:
            attendances = attendances.filter(exam_id=exam_id)
        if class_id:
            attendances = attendances.filter(exam__assigned_class_id=class_id)
        if date_:
            attendances = attendances.filter(exam__date=date_)
        else:
            date_ = date.today()

        # Create the PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="exam_attendance_report_{date_}.pdf"'

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=landscape(A4))

        # Add content to the PDF
        pdf.setFont("Helvetica", 12)
        pdf.drawString(100, 550, "Exam Attendance Report")
        pdf.drawString(100, 530, f"Date: {date}")
        pdf.drawString(100, 510, " ")

        # Table headers
        pdf.drawString(100, 480, "Student ID")
        pdf.drawString(200, 480, "Student Name")
        pdf.drawString(400, 480, "Exam")
        pdf.drawString(550, 480, "Check-in Time")
        pdf.drawString(700, 480, "Check-out Time")

        y = 460
        for attendance in attendances:
            check_in = localtime(attendance.check_in_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_in_time else 'N/A'
            check_out = localtime(attendance.check_out_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_out_time else 'N/A'
            pdf.drawString(100, y, attendance.student.student_rollnumber)
            pdf.drawString(200, y, f"{attendance.student.first_name} {attendance.student.last_name}")
            pdf.drawString(400, y, f"{attendance.exam.course.name[:24]}")
            pdf.drawString(550, y, check_in)
            pdf.drawString(700, y, check_out)
            y -= 20  # Move down for the next row

        pdf.save()
        buffer.seek(0)
        response.write(buffer.getvalue())
        buffer.close()
        return response
    else:
        raise PermissionDenied
