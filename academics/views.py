from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from accounts.audit import audit
from accounts.base import BaseCreate, BaseDelete, BaseList, BaseUpdate
from accounts.models import User
from accounts.notify import notify
from accounts.permissions import RoleRequiredMixin, role_required
from accounts.qr import qr_data_uri

from .forms import CourseForm, EnrollmentForm, ResultForm, SessionForm
from .models import Attendance, ClassSession, Course, Enrollment, Result, new_token
from .utils import attendance_summary, can_manage_course, courses_for_manage, students_for

COURSE_MANAGERS = ("admin", "staff", "teacher")


# ------------------------------------------------------------------ courses
class CourseList(BaseList):
    model = Course
    title = "Courses"
    related = ("teacher",)
    columns = [("Code", "code"), ("Title", "title"), ("Teacher", "teacher"), ("Credits", "credits"), ("Semester", "semester")]
    actions = [("View", "academics:course_detail", "btn-outline-secondary", False),
               ("Edit", "academics:course_edit", "btn-outline-primary", True),
               ("Delete", "academics:course_delete", "btn-outline-danger", True)]
    create_url = "academics:course_create"
    create_label = "New course"
    manage_roles = COURSE_MANAGERS
    search_fields = ("code", "title")

    def row_manageable(self, obj):
        return can_manage_course(self.request.user, obj)


class CourseCreate(BaseCreate):
    allowed_roles = COURSE_MANAGERS
    model = Course
    form_class = CourseForm
    title = "New course"
    success_url = reverse_lazy("academics:course_list")


class CourseUpdate(BaseUpdate):
    allowed_roles = COURSE_MANAGERS
    model = Course
    form_class = CourseForm
    title = "Edit course"
    success_url = reverse_lazy("academics:course_list")

    def get_queryset(self):
        return courses_for_manage(self.request.user)


class CourseDelete(BaseDelete):
    allowed_roles = COURSE_MANAGERS
    model = Course
    success_url = reverse_lazy("academics:course_list")

    def get_queryset(self):
        return courses_for_manage(self.request.user)


class CourseDetail(RoleRequiredMixin, DetailView):
    model = Course
    template_name = "academics/course_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        course, user = self.object, self.request.user
        can_manage = can_manage_course(user, course)
        ctx.update(
            is_enrolled=user.role == "student" and course.enrollments.filter(student=user).exists(),
            sessions=course.sessions.all()[:10],
            enrolled_count=course.enrollments.count(),
            can_manage=can_manage,
            enrollments=course.enrollments.select_related("student") if (can_manage or user.role in ("management",)) else None,
        )
        return ctx


@role_required("student")
@require_POST
def enroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    _, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if created:
        audit(request, "ENROLL", course.code)
        messages.success(request, f"Enrolled in {course.code}.")
    return redirect("academics:course_detail", pk=pk)


@role_required("student")
@require_POST
def unenroll(request, pk):
    course = get_object_or_404(Course, pk=pk)
    Enrollment.objects.filter(student=request.user, course=course).delete()
    audit(request, "UNENROLL", course.code)
    messages.info(request, f"You left {course.code}.")
    return redirect("academics:course_detail", pk=pk)


# ------------------------------------------------------------------ students & enrollments
class StudentList(BaseList):
    allowed_roles = ("admin", "staff", "teacher", "management")
    model = User
    title = "Students"
    columns = [("Student ID", "student_id"), ("Name", "get_full_name"), ("Username", "username"),
               ("Program", "program"), ("Batch", "batch"), ("Email", "email")]
    actions = [("Profile", "academics:student_detail", "btn-outline-secondary", False)]
    search_fields = ("username", "first_name", "last_name", "student_id", "email")

    def get_base_queryset(self):
        return students_for(self.request.user)


class StudentDetail(RoleRequiredMixin, DetailView):
    allowed_roles = ("admin", "staff", "teacher", "management")
    template_name = "academics/student_detail.html"
    context_object_name = "student"

    def get_queryset(self):
        return students_for(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        results = Result.objects.filter(student=self.object).select_related("course")
        if self.request.user.role == "teacher":
            results = results.filter(course__teacher=self.request.user)
        ctx.update(attendance=attendance_summary(self.object), results=results,
                   enrollments=Enrollment.objects.filter(student=self.object).select_related("course"))
        return ctx


class EnrollmentList(BaseList):
    allowed_roles = ("admin", "staff", "teacher", "management")
    manage_roles = ("admin", "staff")
    model = Enrollment
    title = "Enrollments"
    related = ("student", "course")
    columns = [("Student", "student"), ("Student ID", "student.student_id"), ("Course", "course"), ("Enrolled", "enrolled_at")]
    actions = [("Remove", "academics:enrollment_delete", "btn-outline-danger", True)]
    create_url = "academics:enrollment_create"
    create_label = "Enroll a student"
    search_fields = ("student__username", "student__first_name", "student__last_name", "course__code")

    def get_base_queryset(self):
        qs = Enrollment.objects.all()
        if self.request.user.role == "teacher":
            qs = qs.filter(course__teacher=self.request.user)
        return qs


class EnrollmentCreate(BaseCreate):
    allowed_roles = ("admin", "staff")
    model = Enrollment
    form_class = EnrollmentForm
    title = "Enroll a student"
    success_url = reverse_lazy("academics:enrollment_list")


class EnrollmentDelete(BaseDelete):
    allowed_roles = ("admin", "staff")
    model = Enrollment
    success_url = reverse_lazy("academics:enrollment_list")


# ------------------------------------------------------------------ class schedule & QR attendance
def sessions_for(user):
    qs = ClassSession.objects.select_related("course")
    if user.role == "student":
        return qs.filter(course__enrollments__student=user)
    if user.role == "teacher":
        return qs.filter(course__teacher=user)
    return qs


class SessionList(BaseList):
    model = ClassSession
    title = "Class schedule"
    columns = [("Course", "course"), ("Title", "title"), ("Date", "date"), ("Time", "time_range"),
               ("Room", "room"), ("Attendance open", "attendance_open", "bool")]
    actions = [("Attendance / QR", "academics:session_attendance", "btn-outline-success", True),
               ("Edit", "academics:session_edit", "btn-outline-primary", True),
               ("Delete", "academics:session_delete", "btn-outline-danger", True)]
    create_url = "academics:session_create"
    create_label = "New class"
    manage_roles = COURSE_MANAGERS
    search_fields = ("course__code", "title", "room")

    def get_base_queryset(self):
        return sessions_for(self.request.user)

    def row_manageable(self, obj):
        return can_manage_course(self.request.user, obj.course)


class SessionCreate(BaseCreate):
    allowed_roles = COURSE_MANAGERS
    model = ClassSession
    form_class = SessionForm
    title = "New class session"
    success_url = reverse_lazy("academics:session_list")


class SessionUpdate(BaseUpdate):
    allowed_roles = COURSE_MANAGERS
    model = ClassSession
    form_class = SessionForm
    title = "Edit class session"
    success_url = reverse_lazy("academics:session_list")

    def get_queryset(self):
        return ClassSession.objects.filter(course__in=courses_for_manage(self.request.user))


class SessionDelete(BaseDelete):
    allowed_roles = COURSE_MANAGERS
    model = ClassSession
    success_url = reverse_lazy("academics:session_list")

    def get_queryset(self):
        return ClassSession.objects.filter(course__in=courses_for_manage(self.request.user))


@role_required(*COURSE_MANAGERS)
def session_attendance(request, pk):
    session = get_object_or_404(ClassSession.objects.select_related("course"), pk=pk)
    if not can_manage_course(request.user, session.course):
        raise PermissionDenied
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "toggle":
            session.attendance_open = not session.attendance_open
            session.save(update_fields=["attendance_open"])
            audit(request, "ATTENDANCE_TOGGLE", f"{session} open={session.attendance_open}")
        elif action == "regenerate":
            session.qr_token = new_token()
            session.save(update_fields=["qr_token"])
            audit(request, "ATTENDANCE_QR_REGENERATED", str(session))
        elif action in ("mark", "unmark"):
            student_id = request.POST.get("student", "")
            student = User.objects.filter(pk=student_id, role="student").first() if student_id.isdigit() else None
            if student and session.course.enrollments.filter(student=student).exists():
                if action == "mark":
                    Attendance.objects.get_or_create(session=session, student=student)
                else:
                    Attendance.objects.filter(session=session, student=student).delete()
                audit(request, "ATTENDANCE_MANUAL", f"{action} {student.username} for {session}")
        return redirect("academics:session_attendance", pk=pk)

    present_ids = set(session.attendances.values_list("student_id", flat=True))
    enrolled = [e.student for e in session.course.enrollments.select_related("student")]
    link = request.build_absolute_uri(reverse("academics:attend", args=[session.qr_token]))
    return render(request, "academics/session_attendance.html", {
        "session": session,
        "present": [s for s in enrolled if s.id in present_ids],
        "absent": [s for s in enrolled if s.id not in present_ids],
        "qr": qr_data_uri(link) if session.attendance_open else None,
        "link": link,
    })


@role_required("student")
def attend(request, token):
    """Students land here after scanning the session QR code."""
    session = get_object_or_404(ClassSession.objects.select_related("course"), qr_token=token)
    problem = None
    if not session.course.enrollments.filter(student=request.user).exists():
        problem = "You are not enrolled in this course."
    elif not session.attendance_open:
        problem = "Attendance is not open for this class right now."
    elif session.date != timezone.localdate():
        problem = "This QR code is not valid today."
    already = Attendance.objects.filter(session=session, student=request.user).exists()
    if request.method == "POST" and not problem and not already:
        Attendance.objects.get_or_create(session=session, student=request.user)
        audit(request, "ATTENDANCE_MARK", str(session))
        messages.success(request, "Attendance recorded. Thank you!")
        return redirect("academics:my_attendance")
    return render(request, "academics/attend.html", {"session": session, "problem": problem, "already": already})


@role_required("student")
def my_attendance(request):
    return render(request, "academics/my_attendance.html", {"rows": attendance_summary(request.user)})


# ------------------------------------------------------------------ results
class ResultList(BaseList):
    model = Result
    title = "Academic results"
    related = ("student", "course")
    columns = [("Student", "student"), ("Course", "course.code"), ("Exam", "exam_name"),
               ("Marks", "score_text"), ("Grade", "grade"), ("Published", "published", "bool")]
    actions = [("Edit", "academics:result_edit", "btn-outline-primary", True),
               ("Delete", "academics:result_delete", "btn-outline-danger", True)]
    create_url = "academics:result_create"
    create_label = "Enter result"
    manage_roles = COURSE_MANAGERS
    search_fields = ("student__username", "student__first_name", "student__last_name", "course__code", "exam_name")

    def get_base_queryset(self):
        user = self.request.user
        if user.role == "student":
            return Result.objects.filter(student=user, published=True)
        if user.role == "teacher":
            return Result.objects.filter(course__teacher=user)
        return Result.objects.all()

    def row_manageable(self, obj):
        return can_manage_course(self.request.user, obj.course)


class ResultMixin:
    allowed_roles = COURSE_MANAGERS
    model = Result
    form_class = ResultForm
    success_url = reverse_lazy("academics:result_list")

    def after_save(self, obj, adding):
        if obj.published:
            notify(obj.student, f"Result published: {obj.course.code} {obj.exam_name}", reverse("academics:result_list"))


class ResultCreate(ResultMixin, BaseCreate):
    title = "Enter result"


class ResultUpdate(ResultMixin, BaseUpdate):
    title = "Edit result"

    def get_queryset(self):
        return Result.objects.filter(course__in=courses_for_manage(self.request.user))


class ResultDelete(BaseDelete):
    allowed_roles = COURSE_MANAGERS
    model = Result
    success_url = reverse_lazy("academics:result_list")

    def get_queryset(self):
        return Result.objects.filter(course__in=courses_for_manage(self.request.user))
