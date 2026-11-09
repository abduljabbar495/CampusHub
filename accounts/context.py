MENUS = {
    "student": [
        ("Dashboard", "accounts:dashboard"), ("Courses", "academics:course_list"),
        ("Schedule", "academics:session_list"), ("Attendance", "academics:my_attendance"),
        ("Results", "academics:result_list"), ("Materials", "campus:material_list"),
        ("Assignments", "campus:assignment_list"), ("Quizzes", "campus:quiz_list"),
        ("Notices", "campus:notice_list"), ("Events", "campus:event_list"),
        ("Complaints", "campus:complaint_list"), ("Incidents", "security:incident_list"),
    ],
    "teacher": [
        ("Dashboard", "accounts:dashboard"), ("Courses", "academics:course_list"),
        ("Students", "academics:student_list"), ("Schedule", "academics:session_list"),
        ("Results", "academics:result_list"), ("Materials", "campus:material_list"),
        ("Assignments", "campus:assignment_list"), ("Quizzes", "campus:quiz_list"),
        ("Notices", "campus:notice_list"), ("Events", "campus:event_list"),
        ("Incidents", "security:incident_list"),
    ],
    "staff": [
        ("Dashboard", "accounts:dashboard"), ("Students", "academics:student_list"),
        ("Courses", "academics:course_list"), ("Enrollments", "academics:enrollment_list"),
        ("Schedule", "academics:session_list"), ("Notices", "campus:notice_list"),
        ("Events", "campus:event_list"), ("Complaints", "campus:complaint_list"),
        ("Incidents", "security:incident_list"),
    ],
    "guard": [
        ("Dashboard", "accounts:dashboard"), ("Visitor passes", "security:pass_list"),
        ("New visitor", "security:pass_create"), ("Scan / lookup", "security:pass_lookup"),
        ("Incidents", "security:incident_list"), ("Notices", "campus:notice_list"),
    ],
    "admin": [
        ("Dashboard", "accounts:dashboard"), ("Users", "accounts:user_list"),
        ("Courses", "academics:course_list"), ("Students", "academics:student_list"),
        ("Enrollments", "academics:enrollment_list"), ("Schedule", "academics:session_list"),
        ("Results", "academics:result_list"), ("Notices", "campus:notice_list"),
        ("Events", "campus:event_list"), ("Complaints", "campus:complaint_list"),
        ("Visitors", "security:pass_list"), ("Incidents", "security:incident_list"),
        ("Audit log", "accounts:audit_list"), ("Reports", "accounts:reports"),
    ],
    "management": [
        ("Dashboard", "accounts:dashboard"), ("Reports", "accounts:reports"),
        ("Complaints", "campus:complaint_list"), ("Incidents", "security:incident_list"),
        ("Visitors", "security:pass_list"), ("Audit log", "accounts:audit_list"),
        ("Courses", "academics:course_list"), ("Notices", "campus:notice_list"),
        ("Events", "campus:event_list"),
    ],
}


def layout(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    return {
        "menu": MENUS.get(user.role, MENUS["student"]),
        "unread_count": user.notifications.filter(is_read=False).count(),
    }
