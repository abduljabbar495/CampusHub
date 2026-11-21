
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import User
from academics.models import Course, Exam, Result
from academics.views import _student_academic_summary
from campus_events.models import Event, Notice
from visitors.models import Visitor


@login_required
def dashboard(request):
    user = request.user

    # ADMIN DASHBOARD
    if user.is_superuser or user.role == User.Role.ADMIN:
        students = User.objects.filter(
            role=User.Role.STUDENT,
            is_active=True
        ).order_by("username")

        student_progress = []

        for student in students:
            summary = _student_academic_summary(student)

            student_progress.append({
                "student": student,
                "enrolled_count": student.enrolled_courses.count(),
                "cgpa": summary["cgpa"],
                "completed_courses": summary["completed_courses"],
                "attempted_credits": summary["attempted_credits"],
            })

        context = {
            "student_count": students.count(),

            "teacher_count": User.objects.filter(
                role=User.Role.TEACHER,
                is_active=True
            ).count(),

            "staff_count": User.objects.filter(
                role=User.Role.STAFF,
                is_active=True
            ).count(),

            "security_count": User.objects.filter(
                role=User.Role.SECURITY,
                is_active=True
            ).count(),

            "course_count": Course.objects.count(),

            "published_exam_count": Exam.objects.filter(
                published=True
            ).count(),

            "published_result_count": Result.objects.filter(
                exam__published=True
            ).count(),

            "event_count": Event.objects.count(),

            "notice_count": Notice.objects.filter(
                published=True
            ).count(),

            "visitor_count": Visitor.objects.count(),

            "student_progress": student_progress,

            "stats": [
                ("Active Students", students.count()),
                (
                    "Active Teachers",
                    User.objects.filter(
                        role=User.Role.TEACHER,
                        is_active=True
                    ).count()
                ),
                (
                    "Authorized Staff",
                    User.objects.filter(
                        role=User.Role.STAFF,
                        is_active=True
                    ).count()
                ),
                (
                    "Security Users",
                    User.objects.filter(
                        role=User.Role.SECURITY,
                        is_active=True
                    ).count()
                ),
                ("Courses", Course.objects.count()),
                (
                    "Published Exams",
                    Exam.objects.filter(published=True).count()
                ),
                (
                    "Published Results",
                    Result.objects.filter(
                        exam__published=True
                    ).count()
                ),
                ("Campus Events", Event.objects.count()),
            ],
        }

        return render(request, "dashboard.html", context)

    # TEACHER DASHBOARD
    if user.role == User.Role.TEACHER:
        courses = Course.objects.filter(teachers=user)

        return render(request, "dashboard_teacher.html", {
            "my_courses_count": courses.count(),

            "my_student_count": User.objects.filter(
                enrolled_courses__in=courses,
                role=User.Role.STUDENT
            ).distinct().count(),

            "my_exam_count": Exam.objects.filter(
                course__in=courses
            ).count(),
        })

    # STUDENT DASHBOARD
    if user.role == User.Role.STUDENT:
        summary = _student_academic_summary(user)

        enrolled_courses = user.enrolled_courses.all().order_by("code")

        return render(request, "dashboard_student.html", {
            "enrolled_courses": enrolled_courses,
            "enrolled_count": enrolled_courses.count(),
            "academic_summary": summary,
            "published_result_count": len(
                summary["published_results"]
            ),
            "material_count": sum(
                course.materials.count()
                for course in enrolled_courses
            ),
        })

    # STAFF DASHBOARD
    if user.role == User.Role.STAFF:
        own_events = Event.objects.filter(
            created_by=user
        ).order_by("event_date", "start_time")

        return render(request, "dashboard_staff.html", {
            "own_events": own_events,
            "own_event_count": own_events.count(),
        })

    # SECURITY DASHBOARD
    if user.role == User.Role.SECURITY:
        return render(request, "dashboard_security.html", {
            "total_visitors": Visitor.objects.count(),

            "pending_visitors": Visitor.objects.filter(
                status=Visitor.Status.PENDING
            ).count(),

            "checked_in_visitors": Visitor.objects.filter(
                status=Visitor.Status.CHECKED_IN
            ).count(),

            "checked_out_visitors": Visitor.objects.filter(
                status=Visitor.Status.CHECKED_OUT
            ).count(),

            "stats": [
                ("Total Visitors", Visitor.objects.count()),
                (
                    "Pending",
                    Visitor.objects.filter(
                        status=Visitor.Status.PENDING
                    ).count()
                ),
                (
                    "Checked In",
                    Visitor.objects.filter(
                        status=Visitor.Status.CHECKED_IN
                    ).count()
                ),
                (
                    "Checked Out",
                    Visitor.objects.filter(
                        status=Visitor.Status.CHECKED_OUT
                    ).count()
                ),
            ],
        })

    # FALLBACK
    return render(request, "dashboard.html")
