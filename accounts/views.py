import csv
import time
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .audit import audit
from .base import BaseCreate, BaseList, BaseUpdate
from .forms import (AdminUserCreateForm, AdminUserForm, LoginForm, MFACodeForm,
                    ProfileForm, RegisterForm, StyleMixin)
from .mfa import new_secret, provisioning_uri, verify
from .models import AuditLog, Notification, User
from .permissions import RoleRequiredMixin, role_required
from .qr import qr_data_uri

MAX_MFA_TRIES = 5


def error_403(request, exception=None):
    return render(request, "403.html", status=403)


# ------------------------------------------------------------------ authentication
def _safe_next(request, target):
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return reverse("accounts:dashboard")


def _complete_login(request, user, target):
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    audit(request, "LOGIN_SUCCESS", f"{user.username} signed in", user=user)
    return redirect(_safe_next(request, target))


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"].strip()
        password = form.cleaned_data["password"]
        target = request.POST.get("next", "")
        account = User.objects.filter(username=username).first()
        if account and account.is_locked():
            audit(request, "LOGIN_BLOCKED", f"Locked account: {username}", user=account)
            messages.error(request, "This account is temporarily locked after repeated failed logins. Try again later.")
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                if account:
                    account.register_failure()
                audit(request, "LOGIN_FAILED", f"Failed login for '{username}'", user=account)
                messages.error(request, "Invalid username or password.")
            elif not user.is_approved:
                audit(request, "LOGIN_BLOCKED", "Account not approved", user=user)
                messages.error(request, "Your account is waiting for administrator approval.")
            else:
                user.reset_failures()
                if user.mfa_enabled:
                    request.session["pre_mfa"] = {"uid": user.pk, "ts": time.time(), "next": target, "tries": 0}
                    return redirect("accounts:mfa_verify")
                return _complete_login(request, user, target)
    return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", "")})


def mfa_verify(request):
    state = request.session.get("pre_mfa")
    if not state or time.time() - state["ts"] > 300:
        request.session.pop("pre_mfa", None)
        messages.error(request, "Your sign-in session expired. Please log in again.")
        return redirect("accounts:login")
    user = get_object_or_404(User, pk=state["uid"])
    form = MFACodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if verify(user.get_mfa_secret(), form.cleaned_data["code"]):
            request.session.pop("pre_mfa", None)
            return _complete_login(request, user, state["next"])
        state["tries"] += 1
        request.session["pre_mfa"] = state
        audit(request, "MFA_FAILED", f"Wrong MFA code for {user.username}", user=user)
        if state["tries"] >= MAX_MFA_TRIES:
            request.session.pop("pre_mfa", None)
            user.lock()
            messages.error(request, "Too many wrong codes. The account has been temporarily locked.")
            return redirect("accounts:login")
        messages.error(request, "Invalid code. Please try again.")
    return render(request, "accounts/mfa_verify.html", {"form": form})


@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        audit(request, "LOGOUT", f"{request.user.username} signed out")
    logout(request)
    return redirect("accounts:login")


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        audit(request, "REGISTER", f"New {user.role} account: {user.username}", user=user)
        if user.is_approved:
            messages.success(request, "Account created. You can sign in now.")
        else:
            messages.info(request, "Account created. An administrator must approve it before you can sign in.")
        return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})


# ------------------------------------------------------------------ profile / MFA / notifications
@login_required
def profile(request):
    return render(request, "accounts/profile.html")


class ProfileEdit(BaseUpdate):
    form_class = ProfileForm
    model = User
    title = "Edit profile"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user


class PasswordChange(RoleRequiredMixin, PasswordChangeView):
    template_name = "generic/form.html"
    success_url = reverse_lazy("accounts:profile")
    form_class = type("StyledPasswordChangeForm", (StyleMixin, PasswordChangeForm), {})
    extra_context = {"title": "Change password", "cancel_url": reverse_lazy("accounts:profile")}

    def form_valid(self, form):
        audit(self.request, "PASSWORD_CHANGED", self.request.user.username)
        messages.success(self.request, "Password changed.")
        return super().form_valid(form)


@login_required
def mfa_setup(request):
    user = request.user
    if user.mfa_enabled:
        messages.info(request, "MFA is already enabled.")
        return redirect("accounts:profile")
    secret = request.session.get("pending_mfa") or new_secret()
    request.session["pending_mfa"] = secret
    form = MFACodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if verify(secret, form.cleaned_data["code"]):
            user.set_mfa_secret(secret)
            user.mfa_enabled = True
            user.save(update_fields=["mfa_secret", "mfa_enabled"])
            request.session.pop("pending_mfa", None)
            audit(request, "MFA_ENABLED", user.username)
            messages.success(request, "Multi-factor authentication is now enabled.")
            return redirect("accounts:profile")
        messages.error(request, "That code is not valid. Check your authenticator app and try again.")
    uri = provisioning_uri(secret, user.username)
    return render(request, "accounts/mfa_setup.html", {"form": form, "secret": secret, "qr": qr_data_uri(uri)})


@login_required
@require_POST
def mfa_disable(request):
    user = request.user
    if user.check_password(request.POST.get("password", "")):
        user.mfa_enabled = False
        user.mfa_secret = ""
        user.save(update_fields=["mfa_enabled", "mfa_secret"])
        audit(request, "MFA_DISABLED", user.username)
        messages.success(request, "MFA disabled.")
    else:
        messages.error(request, "Wrong password. MFA was not changed.")
    return redirect("accounts:profile")


@login_required
def notifications(request):
    if request.method == "POST":
        request.user.notifications.filter(is_read=False).update(is_read=True)
        return redirect("accounts:notifications")
    items = list(request.user.notifications.all()[:50])
    return render(request, "accounts/notifications.html", {"items": items})


# ------------------------------------------------------------------ user administration
class UserList(BaseList):
    allowed_roles = ("admin",)
    manage_roles = ("admin",)
    model = User
    title = "Users"
    columns = [("Username", "username"), ("Name", "get_full_name"), ("Role", "role", "badge"),
               ("Active", "is_active", "bool"), ("Approved", "is_approved", "bool"), ("MFA", "mfa_enabled", "bool")]
    actions = [("Edit", "accounts:user_edit", "btn-outline-primary", True)]
    create_url = "accounts:user_create"
    create_label = "Create user"
    search_fields = ("username", "email", "first_name", "last_name", "student_id")


class UserCreate(BaseCreate):
    allowed_roles = ("admin",)
    model = User
    form_class = AdminUserCreateForm
    title = "Create user"
    success_url = reverse_lazy("accounts:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop("user", None)
        return kwargs


class UserEdit(BaseUpdate):
    allowed_roles = ("admin",)
    model = User
    form_class = AdminUserForm
    title = "Edit user"
    success_url = reverse_lazy("accounts:user_list")


# ------------------------------------------------------------------ audit & reports
class AuditList(BaseList):
    allowed_roles = ("admin", "management")
    model = AuditLog
    title = "Audit log & security monitoring"
    paginate_by = 30
    columns = [("Time", "created"), ("User", "username"), ("Action", "action", "badge"),
               ("Detail", "detail"), ("IP", "ip_address")]
    search_fields = ("username", "action", "detail", "ip_address")
    top_buttons = [("Export CSV", "accounts:export_audit")]


CSV_EXPORTS = {}


def _safe_cell(value):
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text  # CSV-injection guard


def _csv_response(name, header, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{name}-{timezone.localdate()}.csv"'
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow([_safe_cell(c) for c in row])
    return response


@role_required("admin", "management")
def export(request, kind):
    from academics.models import Attendance
    from campus.models import Complaint
    from security.models import Incident, VisitorPass

    audit(request, "EXPORT", f"CSV export: {kind}")
    if kind == "audit":
        rows = [(a.created, a.username, a.action, a.detail, a.ip_address) for a in AuditLog.objects.all()[:5000]]
        return _csv_response("audit-log", ["Time", "User", "Action", "Detail", "IP"], rows)
    if kind == "complaints":
        rows = [(c.pk, c.submitted_by, c.category, c.title, c.status, c.created) for c in Complaint.objects.select_related("submitted_by")]
        return _csv_response("complaints", ["ID", "By", "Category", "Title", "Status", "Created"], rows)
    if kind == "incidents":
        rows = [(i.pk, i.title, i.location, i.severity, i.status, i.reporter, i.created) for i in Incident.objects.select_related("reporter")]
        return _csv_response("incidents", ["ID", "Title", "Location", "Severity", "Status", "Reporter", "Created"], rows)
    if kind == "visitors":
        rows = [(p.pk, p.visitor.name, p.visitor.purpose, p.status, p.valid_until, p.checked_in_at, p.checked_out_at)
                for p in VisitorPass.objects.select_related("visitor")]
        return _csv_response("visitors", ["Pass", "Visitor", "Purpose", "Status", "Valid until", "In", "Out"], rows)
    if kind == "attendance":
        rows = [(a.session.course.code, a.session.date, a.student.student_id, a.student, a.marked_at)
                for a in Attendance.objects.select_related("session__course", "student")]
        return _csv_response("attendance", ["Course", "Date", "Student ID", "Student", "Marked at"], rows)
    if kind == "users":
        rows = [(u.username, u.get_full_name(), u.email, u.role, u.is_active, u.mfa_enabled) for u in User.objects.all()]
        return _csv_response("users", ["Username", "Name", "Email", "Role", "Active", "MFA"], rows)
    raise Http404


@role_required("admin", "management")
def reports(request):
    from academics.models import Attendance, ClassSession, Course, Enrollment
    from campus.models import Complaint
    from security.models import Incident, Visitor

    today = timezone.localdate()
    week = [today - timedelta(days=i) for i in range(6, -1, -1)]
    visitors_per_day = [(d, Visitor.objects.filter(created__date=d).count()) for d in week]
    ctx = {
        "users_by_role": [(label, User.objects.filter(role=r).count()) for r, label in User.Role.choices],
        "complaints": [(label, Complaint.objects.filter(status=s).count()) for s, label in Complaint.Status.choices],
        "incidents_status": [(label, Incident.objects.filter(status=s).count()) for s, label in Incident.Status.choices],
        "incidents_severity": [(label, Incident.objects.filter(severity=s).count()) for s, label in Incident.Severity.choices],
        "visitors_per_day": visitors_per_day,
        "totals": [("Courses", Course.objects.count()), ("Enrollments", Enrollment.objects.count()),
                   ("Class sessions", ClassSession.objects.count()), ("Attendance records", Attendance.objects.count())],
        "audit_actions": AuditLog.objects.filter(created__gte=timezone.now() - timedelta(days=7))
                         .values_list("action").annotate(c=Count("id")).order_by("-c")[:10],
        "exports": ["audit", "complaints", "incidents", "visitors", "attendance", "users"],
    }
    return render(request, "accounts/reports.html", ctx)


# ------------------------------------------------------------------ dashboard
@login_required
def dashboard(request):
    from academics.models import Attendance, ClassSession, Course, Enrollment
    from academics.utils import attendance_summary
    from campus.models import Assignment, Complaint, Event, Notice, Submission
    from security.models import Incident, VisitorPass

    u = request.user
    today = timezone.localdate()
    now = timezone.now()
    cards, panels = [], []

    def notices_panel():
        qs = Notice.objects.all() if u.role in ("staff", "admin", "management") else Notice.objects.filter(Q(audience="all") | Q(audience=u.role))
        return {"title": "Latest notices", "rows": [(n.title, f"{n.created:%d %b %Y}", reverse("campus:notice_list")) for n in qs[:5]]}

    def events_panel():
        return {"title": "Upcoming events", "rows": [(e.title, f"{e.start:%d %b, %H:%M} · {e.location}", reverse("campus:event_detail", args=[e.pk]))
                                                  for e in Event.objects.filter(end__gte=now).order_by("start")[:5]]}

    if u.role == "student":
        enrolled = Course.objects.filter(enrollments__student=u)
        summary = attendance_summary(u)
        total = sum(r["total"] for r in summary)
        present = sum(r["present"] for r in summary)
        pending = Assignment.objects.filter(course__in=enrolled, due_date__gte=now).exclude(submissions__student=u)
        cards = [("Enrolled courses", enrolled.count(), reverse("academics:course_list")),
                 ("Attendance", f"{round(present * 100 / total) if total else 0}%", reverse("academics:my_attendance")),
                 ("Pending assignments", pending.count(), reverse("campus:assignment_list")),
                 ("Open complaints", Complaint.objects.filter(submitted_by=u, status__in=["open", "in_review"]).count(), reverse("campus:complaint_list"))]
        panels = [
            {"title": "Upcoming classes", "rows": [(f"{s.course.code} – {s.title}", f"{s.date:%a %d %b} {s.start_time:%H:%M} · {s.room}", reverse("academics:session_list"))
                                                  for s in ClassSession.objects.filter(course__in=enrolled, date__gte=today).select_related("course").order_by("date", "start_time")[:5]]},
            {"title": "Assignments due", "rows": [(a.title, f"{a.course.code} · due {a.due_date:%d %b %H:%M}", reverse("campus:assignment_detail", args=[a.pk]))
                                                  for a in pending.select_related("course").order_by("due_date")[:5]]},
            notices_panel(), events_panel()]
    elif u.role == "teacher":
        mine = Course.objects.filter(teacher=u)
        cards = [("My courses", mine.count(), reverse("academics:course_list")),
                 ("Students", Enrollment.objects.filter(course__teacher=u).values("student").distinct().count(), reverse("academics:student_list")),
                 ("Submissions to grade", Submission.objects.filter(assignment__course__teacher=u, marks__isnull=True).count(), reverse("campus:assignment_list")),
                 ("Today's classes", ClassSession.objects.filter(course__teacher=u, date=today).count(), reverse("academics:session_list"))]
        panels = [
            {"title": "Today's & upcoming classes", "rows": [(f"{s.course.code} – {s.title}", f"{s.date:%a %d %b} {s.start_time:%H:%M} · {s.room}", reverse("academics:session_attendance", args=[s.pk]))
                                                           for s in ClassSession.objects.filter(course__teacher=u, date__gte=today).select_related("course").order_by("date", "start_time")[:6]]},
            notices_panel(), events_panel()]
    elif u.role == "staff":
        cards = [("Students", User.objects.filter(role="student").count(), reverse("academics:student_list")),
                 ("Courses", Course.objects.count(), reverse("academics:course_list")),
                 ("Open complaints", Complaint.objects.filter(status__in=["open", "in_review"]).count(), reverse("campus:complaint_list")),
                 ("Upcoming events", Event.objects.filter(end__gte=now).count(), reverse("campus:event_list"))]
        panels = [{"title": "Newest complaints", "rows": [(c.title, f"{c.get_status_display()} · {c.submitted_by}", reverse("campus:complaint_detail", args=[c.pk]))
                                                           for c in Complaint.objects.select_related("submitted_by")[:6]]},
                  notices_panel(), events_panel()]
    elif u.role == "guard":
        inside = VisitorPass.objects.filter(status="checked_in")
        cards = [("Visitors inside", inside.count(), reverse("security:pass_list")),
                 ("Passes issued today", VisitorPass.objects.filter(created__date=today).count(), reverse("security:pass_list")),
                 ("Open incidents", Incident.objects.filter(status__in=["reported", "investigating"]).count(), reverse("security:incident_list"))]
        panels = [{"title": "Currently on campus", "rows": [(p.visitor.name, f"since {p.checked_in_at:%H:%M} · host {p.visitor.host_name}", reverse("security:pass_detail", args=[p.pk])) for p in inside.select_related("visitor")[:8]]},
                  {"title": "Open incidents", "rows": [(i.title, f"{i.get_severity_display()} · {i.location}", reverse("security:incident_detail", args=[i.pk]))
                                                       for i in Incident.objects.filter(status__in=["reported", "investigating"])[:6]]},
                  notices_panel()]
    else:  # admin & management
        since = now - timedelta(hours=24)
        cards = [("Users", User.objects.count(), reverse("accounts:user_list") if u.role == "admin" else reverse("accounts:reports")),
                 ("Open incidents", Incident.objects.filter(status__in=["reported", "investigating"]).count(), reverse("security:incident_list")),
                 ("Open complaints", Complaint.objects.filter(status__in=["open", "in_review"]).count(), reverse("campus:complaint_list")),
                 ("Failed logins (24h)", AuditLog.objects.filter(action="LOGIN_FAILED", created__gte=since).count(), reverse("accounts:audit_list")),
                 ("Locked accounts", User.objects.filter(locked_until__gt=now).count(), reverse("accounts:audit_list")),
                 ("Visitors inside", VisitorPass.objects.filter(status="checked_in").count(), reverse("security:pass_list"))]
        panels = [{"title": "Open incidents by severity",
                   "rows": [(label, f"{Incident.objects.filter(severity=s, status__in=['reported', 'investigating']).count()} open", reverse("security:incident_list")) for s, label in Incident.Severity.choices]},
                  {"title": "Recent security events",
                   "rows": [(f"{a.action} – {a.username or 'anonymous'}", f"{a.created:%d %b %H:%M} · {a.ip_address or ''}", reverse("accounts:audit_list"))
                            for a in AuditLog.objects.exclude(action__in=["CREATE", "UPDATE", "DELETE"])[:8]]},
                  notices_panel(), events_panel()]
    return render(request, "accounts/dashboard.html", {"cards": cards, "panels": panels})
