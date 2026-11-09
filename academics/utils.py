from django.utils import timezone

from accounts.models import User

from .models import Attendance, ClassSession, Course, Enrollment


def can_manage_course(user, course):
    return user.role in ("admin", "staff") or (user.role == "teacher" and course.teacher_id == user.id)


def courses_for_manage(user):
    if user.role in ("admin", "staff"):
        return Course.objects.all()
    return Course.objects.filter(teacher=user)


def courses_visible(user):
    if user.role == "student":
        return Course.objects.filter(enrollments__student=user)
    if user.role == "teacher":
        return Course.objects.filter(teacher=user)
    return Course.objects.all()


def students_for(user):
    qs = User.objects.filter(role="student")
    if user.role == "teacher":
        qs = qs.filter(enrollments__course__teacher=user).distinct()
    return qs


def attendance_summary(student):
    today = timezone.localdate()
    rows = []
    for e in Enrollment.objects.filter(student=student).select_related("course"):
        total = ClassSession.objects.filter(course=e.course, date__lte=today).count()
        present = Attendance.objects.filter(student=student, session__course=e.course).count()
        rows.append({"course": e.course, "total": total, "present": present,
                     "pct": round(present * 100 / total) if total else 0})
    return rows
