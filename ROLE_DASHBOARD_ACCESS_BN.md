# CampusHub Role & Dashboard Update (বাংলা)

## Dashboard structure
- Student Dashboard: enrolled course count/list, published result count, CGPA, earned/attempted credits, materials and campus updates.
- Teacher Dashboard: assigned course/student/result-sheet overview, course and result actions, materials.
- Admin Dashboard: active user counts, course/exam/result/event overview, student-by-student academic progress, user creation and audit/visitor oversight.
- Authorized Staff Dashboard: create events and list/edit/delete only events created by the same staff account.
- Security Dashboard: visitor totals/status and visitor registration/records.
- Django Admin (`/admin/`): separate framework administration panel.

## Staff event ownership rules
- Staff can create an event. `created_by` is always the logged-in user.
- Staff can edit or delete only events where `created_by_id` matches their own user ID.
- Staff cannot create, edit or delete notices.
- Admin can manage all events and notices.
- Other users can view published campus events/notices according to the existing visibility rules.

## Database and migration
This update changes views, URL patterns, templates and access checks only. No model schema was changed, so no new migration is expected. Existing role choices and the academic result calculation/model files remain unchanged.

## Local verification
```powershell
python manage.py check
python manage.py test campus_events
python manage.py runserver
```

Runtime tests must be executed in the project's installed virtual environment.
