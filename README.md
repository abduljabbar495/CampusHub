# CampusHub — Group 9 Capstone

A Django starter implementation for Abdul Jabbar's assigned requirements:
- **FR-04:** Examination Results & Academic Performance
- **FR-05:** Course Materials Management
- **FR-07:** Campus Notices & Events
- **FR-09:** Visitor Management with QR passes

## Requirements
- Python 3.10+
- Django 5.2.19
- SQLite (built into Python; no XAMPP/MySQL setup required)

## 1. Open in VS Code
Extract the ZIP, then open the `CampusHub` folder in VS Code.

## 2. Create virtual environment (Windows PowerShell)
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## 3. Configure environment
Copy `.env.example` to `.env`. The default configuration uses SQLite, so you can run the first test without configuring MySQL.

## 4. Create database tables and administrator
```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000/

Admin panel: http://127.0.0.1:8000/admin/

## 5. Database

This delivery uses **SQLite only**. Django stores the database in `db.sqlite3` beside `manage.py`. No MySQL server, XAMPP, database creation, or database credentials are required. Keep `db.sqlite3` private and back it up before applying migrations.

## 6. Initial data setup
Sign in to `/admin/` using the superuser:
1. Create teacher accounts and set their role to `TEACHER`.
2. Create student accounts and set their role to `STUDENT`.
3. Create staff/security accounts with roles `STAFF` or `SECURITY`.
4. Create Courses, assign each course a teacher, and add students in the course's Students field.
5. Use the normal dashboard to access the features.

**Important:** The public registration form is for student accounts. For security, staff, teacher, security and admin accounts should be created by an administrator through Django Admin. If a user selects another role during public registration, change that behavior before production deployment.

## Role summary
- Admin: configure courses and monitor all records.
- Teacher: create exams, enter results for assigned courses, upload course materials.
- Student: view published results and course materials for enrolled courses.
- Authorized Staff: create notices and events.
- Security Guard: register visitors and process check-in/check-out.

## Notes and limitations in this starter
- The grade thresholds are implemented in `academics/models.py` as a configurable starter scale. Confirm the official grading scale required by your university before submission.
- QR pass generation is implemented. This starter's QR code opens a staff-authenticated scan/check-in page; it does not use a browser camera scanner. Security staff can scan the QR with a phone QR reader and open the link while logged in.
- Student result pages show semester-wise GPA, published course grades, earned/attempted credits and overall credit-weighted CGPA. Confirm the official grading scale and repeat-course policy with the university before treating CGPA as an official transcript value.
- File extension and size checks are included for course materials. Production deployment should additionally validate file content, scan uploads, serve media securely, and configure HTTPS.
- This is a starter capstone implementation. Review permissions and test with separate Student, Teacher, Staff and Security accounts before presenting or deploying.

## Troubleshooting
- `No module named django`: activate `.venv`, then `pip install -r requirements.txt`.
- MySQL connection error: check XAMPP MySQL is running, database name, port, username and password in `.env`.
- `makemigrations` / `migrate` errors: run commands from the folder containing `manage.py`.
- Uploaded files are stored under `media/` during development.

## Academic Results (Theory and Lab)

Course setup includes course type (Theory/Lab), credit value, assigned teacher, and enrolled students. A teacher can create a result sheet for a course and semester, then enter marks by Student ID. Teachers can only work with their assigned courses; students see only their own published results.

- Theory: Attendance 7, Assignment 5, Presentation 8, Quiz 15, Midterm 25, Final 40 (100 total).
- Lab: Attendance 10, Evaluation 25, Report 25, Lab Final 40 (100 total).

Students can sign in with their Student ID and password. Teachers can sign in with their Teacher ID and password. Admins can still use their username. Configure each user's Student ID / Teacher ID and role in Django Admin. Course credit is used to calculate semester GPA and cumulative CGPA. Students see only their own published results. Teachers see a separate result workspace for courses assigned to them and can create result sheets, enter marks and publish results. Failed courses count as attempted credits but not earned credits. The grade-point scale in `academics/models.py` is a starter scale and should be checked against the university's official grading policy before final submission.


## FR-04 presentation checklist
1. Create Teacher and Student test accounts in Django Admin.
2. Create a Theory course and a Lab course, assign a teacher, and enroll the test student.
3. Create a semester result sheet for each course.
4. Sign in as the assigned teacher and enter marks using the correct assessment breakdown.
5. Open the Examinations page and publish the result sheet (publishing is a POST action).
6. Sign in as the student and verify that only published results are visible.
7. Verify the course credit, total marks, grade, grade point, semester GPA and overall CGPA.
8. Sign in as a different student and verify that another student's results are not visible.
9. Sign in as a teacher assigned to another course and verify that the teacher cannot enter or publish results for courses not assigned to them.

**Academic policy note:** The proposal supplies assessment mark distributions but does not specify an official grade-point conversion table. The current A+–F thresholds are a configurable demonstration scale, not a claim that they match DIU's official grading policy. Confirm the official scale with the supervisor before treating GPA/CGPA as institutionally authoritative.


## Bulk Result Entry
Teachers can open a draft result sheet from the Teacher Result Workspace or Examinations page and select **Bulk entry**. The page lists all students enrolled in that course, allows marks to be entered in one table, pre-fills existing draft entries, validates each component against its maximum, and saves the batch atomically. Published result sheets are locked. Only the assigned teacher or an administrator can access this page.


## Abdul Jabbar — Assigned Requirements in this build
- **Module 1, FR-04:** Academic Results & Performance — retained from the uploaded project.
- **Module 2, FR-05:** Course Materials — teacher uploads to assigned courses; enrolled students can view/download.
- **Module 2, FR-07:** Campus Notices & Events — authorized Staff/Admin can create and publish; other roles see published content.
- **Module 3, FR-09:** Visitor Management — Security/Admin registration, unique QR pass, check-in and check-out.

See `FR05_FR07_FR09_IMPLEMENTATION_BN.md` for the updated feature guide and test workflow.


## Additional RBAC, Enrollment and Audit implementation

This package includes an approval-based `EnrollmentRequest` workflow, same-course student directory, Security-only visitor registration and state changes, `VisitLog`, and a separate Admin-only `AuditLog` interface at `/audit-logs/`. FR-04 academic result model and calculation source files were not edited by this enhancement.

### Apply migrations

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
```

Run these commands from the directory containing `manage.py`. Back up your database before applying migrations.
