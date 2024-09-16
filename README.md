# RFID-Based Attendance Management System

This repository contains the code for an RFID-based attendance management system, developed using a Raspberry Pi 4B and Django framework. The system automates attendance tracking for students and employees by leveraging RFID technology to log attendance in real-time, manage reports, and monitor access control through simulated door control mechanisms.

## Features
- **Automated Attendance Logging:** Use RFID cards to scan and log attendance for students and employees.
- **Real-time Monitoring:** Centralized database ensures real-time access to attendance records.
- **Role-Based Dashboards:** Separate dashboards for Heads of Departments, lecturers, finance employees, and security personnel.
- **Report Generation:** Export attendance reports in CSV and PDF formats.
- **Access Control:** Simulates door control with a servo motor, opening or closing doors based on RFID scans.
- **Security and Authentication:** Role-based access control to ensure data security and privacy.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/bonheurNE07/attendances.git
   cd attendances
   
 2. Install dependencies:

    ```bash
    pip install -r requirements.txt

 3. Run the Django development server:

    ```bash
    python manage.py runserver
    Access the application at http://localhost:8000.

## Hardware Setup
Raspberry Pi 4B: The central processing unit.
**RFID Scanner:** Used to scan RFID cards and log attendance.
**Servo Motor:** Simulates door control by opening/closing based on RFID scans.
Monitor: Displays real-time data and system status for users.

## System Components
- **Core App:** Manages authentication and role-based access.
- **Classes App:** Handles class and academic year management.
- **Courses App:** Manages course information.
- **Students App:** Manages student data and attendance tracking.
- **Employees App:** Manages employee attendance.
- **Exams App:** Tracks student exam attendance and eligibility.

## Usage
- **User Authentication:** Log in with your credentials to access the system.
- **Attendance Logging:** RFID cards are scanned to log attendance.
- **Reports:** Generate and download attendance reports from your dashboard.
- **Access Control:** Simulate door control based on scanned RFID cards.

## Future Enhancements
Cloud integration for better scalability.
Mobile-friendly interface or app for easier access.
Advanced security measures like two-factor authentication.

## License
This project is licensed under the MIT License.
