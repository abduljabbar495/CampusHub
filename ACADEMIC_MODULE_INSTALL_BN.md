# CampusHub Academic Result Module — Setup (Bangla)

## কী আছে
- Student ও Teacher role নির্বাচন করে public registration (Admin approval নেই)।
- Teacher dashboard এবং Student dashboard আলাদা।
- একাধিক Teacher একটি Course-এ assign করা যায়; Teacher নিজেও Course তৈরি করতে পারে।
- Teacher assigned course-এর exam/result sheet তৈরি, Student ID দিয়ে marks entry, bulk marks entry এবং publish করতে পারে।
- Student কেবল নিজের published results, semester GPA, credit-weighted CGPA, earned credits এবং performance suggestions দেখতে পারে।
- Backend role/assignment checks রাখা হয়েছে।

## গুরুত্বপূর্ণ database নির্দেশনা
এই ZIP-এ `db.sqlite3` নেই। তোমার বর্তমান database ও backup আলাদা করে রাখবে। পুরোনো Student account সরাসরি delete করলে `Result.student` CASCADE-এর কারণে সেই Student-এর results মুছে যেতে পারে। তাই পুরোনো account purge করার আগে data mapping/retention plan ছাড়া delete করবে না।

## Windows PowerShell setup
1. ZIP extract করে project folder-এ ঢুকো (যেখানে `manage.py` আছে)।
2. Existing project-এর `db.sqlite3` এবং `db_backup_before_account_reset.sqlite3` নিরাপদে আলাদা backup রাখো।
3. Virtual environment activate করে requirements install করো:
   `pip install -r requirements.txt`
4. Migration files তৈরি করো:
   `python manage.py makemigrations accounts academics materials campus_events visitors`
5. Migration SQL review করো:
   `python manage.py sqlmigrate academics 0001`
   (migration number তোমার generated file অনুযায়ী বদলাতে পারে.)
6. Database-এ migrate করো:
   `python manage.py migrate`
7. System check:
   `python manage.py check`
8. Admin user না থাকলে create করো:
   `python manage.py createsuperuser`
9. Server চালাও:
   `python manage.py runserver`
10. Browser: `http://127.0.0.1:8000/`

## Existing SQLite database
এই source ZIP-এর migration folders-এ শুধু `__init__.py` আছে। তাই migration files প্রথমবার generate করার আগে database backup বাধ্যতামূলক। যদি existing database-এ আগেই tables থাকে, `migrate`-এর আগে `showmigrations` এবং `migrate --plan` দেখে নাও। কোনো `--fake` command অন্ধভাবে চালাবে না।

## Registration & use
- Register page-এ Student অথবা Teacher নির্বাচন করবে।
- Teacher: Dashboard → Add Course → course type/credits/students/teachers set করবে → Result Sheets → Create Sheet → Bulk Entry অথবা Individual Entry → Publish.
- Student: Dashboard → My Academic Results. শুধু published result দেখাবে।

## Marks distribution
Theory: Attendance 7, Assignment 5, Presentation 8, Quiz 15, Midterm 25, Final 40.
Lab: Attendance 10, Evaluation 25, Report 25, Lab Final 40.

## Test checklist
- Student login দিয়ে Teacher URL খুললে access denied/redirect হওয়া উচিত।
- Student অন্য Student-এর result দেখতে পারবে না।
- Teacher অন্য Teacher-এর course-এ exam/result/publish করতে পারবে না।
- Unpublished result Student dashboard-এ আসবে না।
- Published result-এর GPA/CGPA course credit দিয়ে weighted হবে।

**Note:** এই delivery source-level update; runtime database migration ও browser integration তোমার local Windows environment-এ উপরের ধাপগুলো অনুসারে complete করতে হবে।
