from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import Employee, EmployeeAttendance
from django.contrib.auth import get_user_model
from django.utils import timezone
import csv
from django.http import HttpResponse
from datetime import date
from core.views import text_to_speech


from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from django.utils import timezone
from io import BytesIO
from django.utils.timezone import localtime
# from Devices.servo import set_angle
import time
from datetime import timedelta

CustomUser = get_user_model()

def is_finance(user):
    return user.is_authenticated and user.role == 'finance'

def is_security(user):
    return user.is_authenticated and user.role == 'security'

@login_required
def register_employee(request):
    if not is_finance(request.user):
        raise PermissionDenied

    if request.method == 'POST':
        # Extract form data
        photo = request.FILES.get('photo')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        employee_rfidnumber = request.POST.get('employee_rfidnumber')
        role = request.POST.get('role')
        date_of_birth = request.POST.get('date_of_birth')

        # Check if the RFID number or roll number already exists
        if Employee.objects.filter(employee_rfidnumber=employee_rfidnumber).exists():
            messages.error(request, 'An Employee with this RFID number already exists.')
            return redirect('employees:register_employee')
        
        # Create new employee
        Employee.objects.create(
            photo=photo,
            first_name=first_name,
            last_name=last_name,
            email=email,
            employee_rfidnumber=employee_rfidnumber,
            role=role,
            date_of_birth=date_of_birth,
            created_by=request.user
        )
        messages.success(request, 'Employee registered successfully!')
        return redirect(reverse_lazy('employees:list_employees'))

    return render(request, 'employees/register_employee.html')

@login_required
def list_employees(request):
    if request.user.role in ['finance', ]:
        employees = Employee.objects.all()
        return render(request, 'employees/list_employees.html', {'employees': employees})
    else:
        raise PermissionDenied

@login_required
def update_employee(request, employee_id):
    if not is_finance(request.user):
        raise PermissionDenied

    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        # Update employee data
        employee.photo = request.FILES.get('photo', employee.photo)
        employee.first_name = request.POST.get('first_name', employee.first_name)
        employee.last_name = request.POST.get('last_name', employee.last_name)
        employee.email = request.POST.get('email', employee.email)
        employee.employee_rfidnumber = request.POST.get('employee_rfidnumber', employee.employee_rfidnumber)
        employee.role = request.POST.get('role', employee.role)
        employee.date_of_birth = request.POST.get('date_of_birth', employee.date_of_birth)
        employee.save()

        messages.success(request, 'Employee updated successfully!')
        return redirect('employees:list_employees')

    return render(request, 'employees/update_employee.html', {'employee': employee})

@login_required
def delete_employee(request, employee_id):
    if not is_finance(request.user):
        raise PermissionDenied

    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully!')
        return redirect(reverse_lazy('employees:list_employees'))

    return render(request, 'employees/delete_employee.html', {'employee': employee})


@login_required
def record_employee_attendance(request):
    if not is_security(request.user):
        text_to_speech ('Permission denied')
        raise PermissionDenied

    employee = None
    status = 'not ready'
    entry_point = request.session.get('entry_point') 
    if request.method == 'POST':
        rfid_number = request.POST.get('rfid_number')
        entry_point = request.POST.get('entry_point')
        
        if rfid_number and entry_point:
            try:
                # Find the employee based on RFID number
                employee = Employee.objects.get(employee_rfidnumber=rfid_number)

                # Find attendance records for this employee that have not been checked out
                today = timezone.now().date()
                attendances = EmployeeAttendance.objects.filter(employee=employee, check_out_time__isnull=True)

                if attendances.exists():
                    # Handle existing open records
                    for attendance in attendances:
                        if not attendance.check_out_time:
                            # Update existing open record to check out
                            attendance.check_out_time = timezone.now()
                            attendance.entry_point = entry_point
                            attendance.recorded_by = request.user
                            attendance.save()
                            text_to_speech('Thank you.')
                            messages.success(request, f'Check-out recorded for {employee.first_name} {employee.last_name}.')
                            status = 'checked out'
                            # set_angle(90)
                            # time.sleep(2.1)
                            # set_angle(0)
                            break
                    if status != 'checked out':
                        # If no open record was found, create a new check-in record
                        EmployeeAttendance.objects.create(
                            employee=employee,
                            check_in_time=timezone.now(),
                            entry_point=entry_point,
                            recorded_by=request.user
                        )
                        messages.success(request, f'Check-in recorded for {employee.first_name} {employee.last_name}.')
                        status = 'checked in'
                        # set_angle(90)
                        # time.sleep(2.1)
                        # set_angle(0)
                else:
                    # Create new attendance record if none exists
                    EmployeeAttendance.objects.create(
                        employee=employee,
                        check_in_time=timezone.now(),
                        entry_point=entry_point,
                        recorded_by=request.user
                    )
                    messages.success(request, f'Check-in recorded for {employee.first_name} {employee.last_name}.')
                    status = 'checked in'
                    # set_angle(90)
                    # time.sleep(2.1)
                    # set_angle(0)
                
            except Employee.DoesNotExist:
                messages.error(request, 'Employee not found. Please check the RFID number.')
    print(entry_point)

    return render(request, 'employees/record_employee_attendance.html', {
        'employee': employee,
        'status': status,
        'entry_point': entry_point,
    })


@login_required
def list_employee_attendance(request):
    if request.user.role in ['finance', 'security']:
        employees = Employee.objects.all()
        attendances = EmployeeAttendance.objects.all()

        # Filter by employee
        employee_id = request.GET.get('employee_id')
        if employee_id:
            attendances = attendances.filter(employee__id=employee_id)

        # Filter by entry point
        entry_point = request.GET.get('entry_point')
        if entry_point:
            attendances = attendances.filter(entry_point=entry_point)

        return render(request, 'employees/list_employee_attendance.html', {
            'employees': employees,
            'attendances': attendances
        })
    else:
        raise PermissionDenied

@login_required
def export_attendance_report(request):
    if request.user.role in ['finance', 'security']:
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="employees_attendance_report_{date.today()}.csv"'

        # Create a CSV writer
        writer = csv.writer(response)
        writer.writerow(['Employee Name', 'Check-in Time', 'Check-out Time', 'Entry Point', 'Hours Worked'])

        # Get all attendance records
        attendances = EmployeeAttendance.objects.filter()

        employee_id = request.GET.get('employee_id')
        if employee_id:
            attendances = attendances.filter(employee__id=employee_id)

        # Filter by entry point
        entry_point = request.GET.get('entry_point')
        if entry_point:
            attendances = attendances.filter(entry_point=entry_point)

        # Write data to CSV
        for attendance in attendances:
            check_in = localtime(attendance.check_in_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_in_time else 'N/A'
            check_out = localtime(attendance.check_out_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_out_time else 'N/A'
            hours_worked = ''
        
            if attendance.check_in_time and attendance.check_out_time:
                time_diff = attendance.check_out_time - attendance.check_in_time
                total_minutes = time_diff.total_seconds() / 60
                hours, minutes = divmod(total_minutes, 60)
                hours_worked = f"{int(hours)}h {int(minutes)}m"
            writer.writerow([
                f"{attendance.employee.first_name} {attendance.employee.last_name}",
                check_in,
                check_out,
                attendance.entry_point,
                hours_worked
            ])

        return response
    else:
        raise PermissionDenied




@login_required
def export_attendance_report_pdf(request):
    if request.user.role not in ['finance', 'security']:
        raise PermissionDenied

    employee_id = request.GET.get('employee_id')
    entry_point = request.GET.get('entry_point')

    # Initialize variables
    attendances = EmployeeAttendance.objects.all()

    if employee_id:
        attendances = attendances.filter(employee__id=employee_id)

    if entry_point:
        attendances = attendances.filter(entry_point=entry_point)

    # Create the PDF response with landscape format
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="employee_attendance_report_{date.today()}.pdf"'

    pdf_canvas = canvas.Canvas(response, pagesize=landscape(letter))
    pdf_canvas.setTitle("Employee Attendance Report")

    # Add title
    pdf_canvas.setFont("Helvetica-Bold", 20)
    pdf_canvas.drawString(1 * inch, 7.5 * inch, "Employee Attendance Report")

    # Add table headers
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(1 * inch, 7 * inch, "Employee Name")
    pdf_canvas.drawString(3 * inch, 7 * inch, "Check-in Time")
    pdf_canvas.drawString(5 * inch, 7 * inch, "Check-out Time")
    pdf_canvas.drawString(7 * inch, 7 * inch, "Entry Point")
    pdf_canvas.drawString(9 * inch, 7 * inch, "Hours Worked")

    # Write attendance data
    y = 6.7 * inch
    for attendance in attendances:
        check_in = localtime(attendance.check_in_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_in_time else 'N/A'
        check_out = localtime(attendance.check_out_time).strftime("%d/%m/%Y, %H:%M") if attendance.check_out_time else 'N/A'
        hours_worked = ''
        
        if attendance.check_in_time and attendance.check_out_time:
            time_diff = attendance.check_out_time - attendance.check_in_time
            total_minutes = time_diff.total_seconds() / 60
            hours, minutes = divmod(total_minutes, 60)
            hours_worked = f"{int(hours)}h {int(minutes)}m"

        pdf_canvas.drawString(1 * inch, y, f"{attendance.employee.first_name} {attendance.employee.last_name}")
        pdf_canvas.drawString(3 * inch, y, str(check_in))
        pdf_canvas.drawString(5 * inch, y, str(check_out))
        pdf_canvas.drawString(7 * inch, y, attendance.entry_point)
        pdf_canvas.drawString(9 * inch, y, hours_worked)

        y -= 0.3 * inch

    # Finalize the PDF
    pdf_canvas.showPage()
    pdf_canvas.save()

    return response
