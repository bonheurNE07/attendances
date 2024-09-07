from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import csv
from django.http import HttpResponse

from .models import Exam, ExamEligibility, ExamAttendance
from students.models import Student
from classes.models import Class
from courses.models import Course
from students.models import Attendance
from core.views import text_to_speech

def is_hod(user):
    return user.is_authenticated and user.role == 'hod'

def is_finance(user):
    return user.is_authenticated and user.role == 'finance'

@login_required
def create_exam(request):
    print(request.user.role)
    if request.user.role != 'hod':
        raise PermissionDenied("Only HOD can create exams.")

    if request.method == 'POST':
        course_id = request.POST.get('course')
        class_id = request.POST.get('assigned_class')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        course = get_object_or_404(Course, id=course_id)
        assigned_class = get_object_or_404(Class, id=class_id)

        Exam.objects.create(
            course=course,
            assigned_class=assigned_class,
            date=date,
            start_time=start_time,
            end_time=end_time,
            created_by=request.user
        )

        messages.success(request, 'Exam created successfully.')
        return redirect(reverse_lazy('exams:list_exams'))

    classes = Class.objects.all()
    courses = Course.objects.all()
    return render(request, 'exams/create_exam.html', {'classes': classes, 'courses': courses})

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

        course = get_object_or_404(Course, id=course_id)
        assigned_class = get_object_or_404(Class, id=class_id)

        exam.course = course
        exam.assigned_class = assigned_class
        exam.date = date
        exam.start_time = start_time
        exam.end_time = end_time
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
        # Get the total attendance count for the course
        total_attendance_count = Attendance.objects.filter(
            student=student, 
            recorded_by__in=[exam.course.lecturer], 
            course=exam.course
        ).count()

        # Calculate attendance count for the student
        student_attendance_count = Attendance.objects.filter(
            student=student, 
            recorded_by__in=[exam.course.lecturer], 
            course=exam.course,
            status='P'  # Assuming 'P' stands for Present
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

            # If the finance employee confirms the student is eligible
            if confirm_eligible:
                # Create or update the ExamEligibility record
                ExamEligibility.objects.update_or_create(
                    exam=exam,
                    student=student,
                    defaults={'is_allowed': True}
                )
            else:
                # Mark as not eligible if not confirmed
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

@login_required
def exam_attendance_check(request, exam_id):
    if request.user.role == 'finance':
        # Get the exam based on the ID passed to the view
        exam = get_object_or_404(Exam, id=exam_id)

        # Check if the exam is active
        if not exam.is_active:
            messages.error(request, "This exam is not active.")
            return redirect(reverse_lazy('exams:list_exams'))

        student = None  # Initialize the student variable to be used in the template
        status = 'not ready'

        # Handle POST request for checking attendance
        if request.method == 'POST':
            rfid_number = request.POST.get('rfid_number')
            
            try:
                # Find the student based on RFID number
                student = Student.objects.get(student_rfidnumber=rfid_number)
            except Student.DoesNotExist:
                messages.error(request, "Student not found.")
                text_to_speech('Student not found.')
                return redirect('exams:exam_attendance_check', exam_id=exam_id)

            # Check if the student is eligible for the exam
            eligibility = ExamEligibility.objects.filter(student=student, exam=exam, is_allowed=True).first()
            if not eligibility:
                messages.error(request, "Student is not eligible to take this exam.")
                text_to_speech('Not Eligible')
                return redirect('exams:exam_attendance_check', exam_id=exam_id)

            # Check if the student has already checked in
            attendance, created = ExamAttendance.objects.get_or_create(student=student, exam=exam)

            if attendance.check_in_time and not attendance.check_out_time:
                # Student is checking out
                attendance.check_out_time = timezone.now()
                attendance.save()
                messages.success(request, f"Check-out recorded for {student.first_name} {student.last_name}.")
            elif not attendance.check_in_time:
                # Student is checking in
                attendance.check_in_time = timezone.now()
                attendance.save()
                text_to_speech(f'{student.first_name} Thank you.')
                messages.success(request, f"Check-in recorded for {student.first_name} {student.last_name}.")
            else:
                messages.info(request, "Student has already checked in and out.")

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
            writer.writerow([
                attendance.student.student_rollnumber,
                f"{attendance.student.first_name} {attendance.student.last_name}",
                f"{attendance.exam.course.name} ({attendance.exam.assigned_class.name})",
                attendance.check_in_time or '',
                attendance.check_out_time or ''
            ])
        text_to_speech('Exported')

        return response
    
    else:
        raise PermissionDenied