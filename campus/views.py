from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property

from accounts.audit import audit
from accounts.base import BaseCreate, BaseDelete, BaseList, BaseUpdate
from accounts.models import User
from accounts.notify import notify
from accounts.permissions import role_required
from academics.utils import can_manage_course, courses_for_manage, courses_visible

from .forms import (AssignmentForm, ComplaintForm, ComplaintResponseForm, EventForm, GradeForm,
                    MaterialForm, NoticeForm, QuestionForm, QuizForm, SubmissionForm)
from .models import (Assignment, Complaint, Event, Material, Notice, Question, Quiz, QuizAttempt, Submission)

TEACHING = ("teacher", "staff", "admin")
TEACHER_ADMIN = ("teacher", "admin")


# ------------------------------------------------------------------ materials
class MaterialList(BaseList):
    model = Material
    title = "Learning materials"
    related = ("course", "uploaded_by")
    columns = [("Title", "title"), ("Course", "course.code"), ("Uploaded by", "uploaded_by"),
               ("Date", "created"), ("File", "file", "file")]
    actions = [("Delete", "campus:material_delete", "btn-outline-danger", True)]
    create_url = "campus:material_create"
    create_label = "Upload material"
    manage_roles = TEACHING
    search_fields = ("title", "course__code", "course__title")

    def get_base_queryset(self):
        return Material.objects.filter(course__in=courses_visible(self.request.user))

    def row_manageable(self, obj):
        return can_manage_course(self.request.user, obj.course)


class MaterialCreate(BaseCreate):
    allowed_roles = TEACHING
    model = Material
    form_class = MaterialForm
    title = "Upload learning material"
    success_url = reverse_lazy("campus:material_list")


class MaterialDelete(BaseDelete):
    allowed_roles = TEACHING
    model = Material
    success_url = reverse_lazy("campus:material_list")

    def get_queryset(self):
        return Material.objects.filter(course__in=courses_for_manage(self.request.user))


# ------------------------------------------------------------------ assignments
def visible_assignments(user):
    return Assignment.objects.filter(course__in=courses_visible(user)).select_related("course")


class AssignmentList(BaseList):
    model = Assignment
    title = "Assignments"
    columns = [("Title", "title"), ("Course", "course.code"), ("Due", "due_date"), ("Max marks", "max_marks")]
    actions = [("Open", "campus:assignment_detail", "btn-outline-secondary", False),
               ("Edit", "campus:assignment_edit", "btn-outline-primary", True),
               ("Delete", "campus:assignment_delete", "btn-outline-danger", True)]
    create_url = "campus:assignment_create"
    create_label = "New assignment"
    manage_roles = TEACHING
    search_fields = ("title", "course__code")

    def get_base_queryset(self):
        return visible_assignments(self.request.user)

    def row_manageable(self, obj):
        return can_manage_course(self.request.user, obj.course)


class AssignmentCreate(BaseCreate):
    allowed_roles = TEACHING
    model = Assignment
    form_class = AssignmentForm
    title = "New assignment"
    success_url = reverse_lazy("campus:assignment_list")

    def after_save(self, obj, adding):
        notify([e.student for e in obj.course.enrollments.select_related("student")],
               f"New assignment in {obj.course.code}: {obj.title}", reverse("campus:assignment_detail", args=[obj.pk]))


class AssignmentUpdate(BaseUpdate):
    allowed_roles = TEACHING
    model = Assignment
    form_class = AssignmentForm
    title = "Edit assignment"
    success_url = reverse_lazy("campus:assignment_list")

    def get_queryset(self):
        return Assignment.objects.filter(course__in=courses_for_manage(self.request.user))


class AssignmentDelete(BaseDelete):
    allowed_roles = TEACHING
    model = Assignment
    success_url = reverse_lazy("campus:assignment_list")

    def get_queryset(self):
        return Assignment.objects.filter(course__in=courses_for_manage(self.request.user))


@login_required
def assignment_detail(request, pk):
    user = request.user
    assignment = get_object_or_404(visible_assignments(user), pk=pk)
    ctx = {"a": assignment, "now": timezone.now()}
    if user.role == "student":
        submission = Submission.objects.filter(assignment=assignment, student=user).first()
        form = SubmissionForm(request.POST or None, request.FILES or None, instance=submission)
        if request.method == "POST":
            if timezone.now() > assignment.due_date:
                messages.error(request, "The deadline has passed.")
                return redirect("campus:assignment_detail", pk=pk)
            if submission and submission.marks is not None:
                messages.error(request, "This submission was already graded and can't be changed.")
                return redirect("campus:assignment_detail", pk=pk)
            if form.is_valid():
                sub = form.save(commit=False)
                sub.assignment, sub.student = assignment, user
                sub.save()
                audit(request, "SUBMIT_ASSIGNMENT", f"{assignment} #{sub.pk}")
                messages.success(request, "Submission saved.")
                return redirect("campus:assignment_detail", pk=pk)
        ctx.update(submission=submission, form=form)
    elif user.role in ("teacher", "admin", "staff", "management"):
        ctx["can_grade"] = user.role in TEACHER_ADMIN and can_manage_course(user, assignment.course)
        ctx["submissions"] = assignment.submissions.select_related("student")
    return render(request, "campus/assignment_detail.html", ctx)


class GradeSubmission(BaseUpdate):
    allowed_roles = TEACHER_ADMIN
    model = Submission
    form_class = GradeForm
    title = "Grade submission"

    def get_queryset(self):
        return Submission.objects.filter(assignment__course__in=courses_for_manage(self.request.user)).select_related("assignment", "student")

    def get_success_url(self):
        return reverse("campus:assignment_detail", args=[self.object.assignment_id])

    def get_cancel_url(self):
        return reverse("campus:assignment_detail", args=[self.object.assignment_id])

    def after_save(self, obj, adding):
        notify(obj.student, f"Your submission for '{obj.assignment.title}' was graded.", reverse("campus:assignment_detail", args=[obj.assignment_id]))


# ------------------------------------------------------------------ quizzes
def visible_quizzes(user):
    qs = Quiz.objects.filter(course__in=courses_visible(user)).select_related("course")
    return qs.filter(is_published=True) if user.role == "student" else qs


class QuizList(BaseList):
    model = Quiz
    title = "Online quizzes"
    columns = [("Title", "title"), ("Course", "course.code"), ("Duration (min)", "duration_minutes"),
               ("Questions", "question_count"), ("Published", "is_published", "bool")]
    actions = [("Open", "campus:quiz_detail", "btn-outline-secondary", False),
               ("Edit", "campus:quiz_edit", "btn-outline-primary", True),
               ("Delete", "campus:quiz_delete", "btn-outline-danger", True)]
    create_url = "campus:quiz_create"
    create_label = "New quiz"
    manage_roles = TEACHING
    search_fields = ("title", "course__code")

    def get_base_queryset(self):
        return visible_quizzes(self.request.user)

    def row_manageable(self, obj):
        return can_manage_course(self.request.user, obj.course)


class QuizCreate(BaseCreate):
    allowed_roles = TEACHING
    model = Quiz
    form_class = QuizForm
    title = "New quiz"
    success_url = reverse_lazy("campus:quiz_list")


class QuizUpdate(BaseUpdate):
    allowed_roles = TEACHING
    model = Quiz
    form_class = QuizForm
    title = "Edit quiz"
    success_url = reverse_lazy("campus:quiz_list")

    def get_queryset(self):
        return Quiz.objects.filter(course__in=courses_for_manage(self.request.user))


class QuizDelete(BaseDelete):
    allowed_roles = TEACHING
    model = Quiz
    success_url = reverse_lazy("campus:quiz_list")

    def get_queryset(self):
        return Quiz.objects.filter(course__in=courses_for_manage(self.request.user))


@login_required
def quiz_detail(request, pk):
    user = request.user
    quiz = get_object_or_404(visible_quizzes(user), pk=pk)
    ctx = {"quiz": quiz, "questions": quiz.questions.all()}
    if user.role == "student":
        ctx["attempt"] = QuizAttempt.objects.filter(quiz=quiz, student=user).first()
    else:
        ctx["can_manage"] = user.role in TEACHING and can_manage_course(user, quiz.course)
        ctx["attempts"] = quiz.attempts.select_related("student").exclude(submitted_at=None)
    return render(request, "campus/quiz_detail.html", ctx)


class QuestionMixin:
    allowed_roles = TEACHING
    model = Question
    form_class = QuestionForm


class QuestionCreate(QuestionMixin, BaseCreate):
    title = "Add question"

    @cached_property
    def quiz(self):
        return get_object_or_404(Quiz.objects.filter(course__in=courses_for_manage(self.request.user)), pk=self.kwargs["quiz_pk"])

    def form_valid(self, form):
        form.instance.quiz = self.quiz
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("campus:quiz_detail", args=[self.quiz.pk])

    def get_cancel_url(self):
        return self.get_success_url()


class QuestionUpdate(QuestionMixin, BaseUpdate):
    title = "Edit question"

    def get_queryset(self):
        return Question.objects.filter(quiz__course__in=courses_for_manage(self.request.user))

    def get_success_url(self):
        return reverse("campus:quiz_detail", args=[self.object.quiz_id])

    def get_cancel_url(self):
        return self.get_success_url()


class QuestionDelete(BaseDelete):
    allowed_roles = TEACHING
    model = Question

    def get_queryset(self):
        return Question.objects.filter(quiz__course__in=courses_for_manage(self.request.user))

    def get_success_url(self):
        return reverse("campus:quiz_detail", args=[self.object.quiz_id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = self.get_success_url()
        return ctx


@role_required("student")
def quiz_take(request, pk):
    quiz = get_object_or_404(visible_quizzes(request.user), pk=pk)
    questions = list(quiz.questions.all())
    if not questions:
        messages.error(request, "This quiz has no questions yet.")
        return redirect("campus:quiz_detail", pk=pk)
    attempt, _ = QuizAttempt.objects.get_or_create(
        quiz=quiz, student=request.user, defaults={"total": sum(q.marks for q in questions)})
    if attempt.submitted_at:
        return redirect("campus:quiz_detail", pk=pk)
    now = timezone.now()
    limit = attempt.started_at + timedelta(minutes=quiz.duration_minutes)
    if request.method == "POST" or now > limit:
        in_time = now <= limit + timedelta(seconds=60)
        answers = request.POST if (request.method == "POST" and in_time) else {}
        attempt.score = sum(q.marks for q in questions if answers.get(f"q{q.pk}") == q.correct)
        attempt.submitted_at = now
        attempt.save()
        audit(request, "QUIZ_SUBMIT", f"{quiz} score {attempt.score}/{attempt.total}")
        if not in_time:
            messages.warning(request, "Time ran out before submission.")
        return redirect("campus:quiz_detail", pk=pk)
    return render(request, "campus/quiz_take.html", {"quiz": quiz, "questions": questions,
                                                      "remaining": max(int((limit - now).total_seconds()), 0)})


# ------------------------------------------------------------------ notices
class NoticeList(BaseList):
    model = Notice
    template_name = "campus/notice_list.html"
    title = "Campus notices"
    manage_roles = ("staff", "admin")
    create_url = "campus:notice_create"
    create_label = "Post notice"
    search_fields = ("title", "body")
    related = ("created_by",)

    def get_base_queryset(self):
        user = self.request.user
        if user.role in ("staff", "admin", "management"):
            return Notice.objects.all()
        return Notice.objects.filter(Q(audience="all") | Q(audience=user.role))


class NoticeMixin:
    allowed_roles = ("staff", "admin")
    model = Notice
    form_class = NoticeForm
    success_url = reverse_lazy("campus:notice_list")


class NoticeCreate(NoticeMixin, BaseCreate):
    title = "Post a notice"

    def after_save(self, obj, adding):
        users = User.objects.filter(is_active=True)
        if obj.audience != "all":
            users = users.filter(role=obj.audience)
        notify(users.exclude(pk=self.request.user.pk), f"New notice: {obj.title}", reverse("campus:notice_list"))


class NoticeUpdate(NoticeMixin, BaseUpdate):
    title = "Edit notice"


class NoticeDelete(BaseDelete):
    allowed_roles = ("staff", "admin")
    model = Notice
    success_url = reverse_lazy("campus:notice_list")


# ------------------------------------------------------------------ events
class EventList(BaseList):
    model = Event
    title = "Campus events"
    columns = [("Title", "title"), ("Location", "location"), ("Starts", "start"), ("Ends", "end"), ("Going", "going")]
    actions = [("Details", "campus:event_detail", "btn-outline-secondary", False),
               ("Edit", "campus:event_edit", "btn-outline-primary", True),
               ("Delete", "campus:event_delete", "btn-outline-danger", True)]
    create_url = "campus:event_create"
    create_label = "New event"
    manage_roles = ("staff", "admin")
    search_fields = ("title", "location")


class EventMixin:
    allowed_roles = ("staff", "admin")
    model = Event
    form_class = EventForm
    success_url = reverse_lazy("campus:event_list")


class EventCreate(EventMixin, BaseCreate):
    title = "New event"

    def after_save(self, obj, adding):
        notify(User.objects.filter(is_active=True).exclude(pk=self.request.user.pk), f"New event: {obj.title}",
               reverse("campus:event_detail", args=[obj.pk]))


class EventUpdate(EventMixin, BaseUpdate):
    title = "Edit event"


class EventDelete(BaseDelete):
    allowed_roles = ("staff", "admin")
    model = Event
    success_url = reverse_lazy("campus:event_list")


@login_required
def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        if event.attendees.filter(pk=request.user.pk).exists():
            event.attendees.remove(request.user)
            messages.info(request, "RSVP cancelled.")
        else:
            event.attendees.add(request.user)
            messages.success(request, "You're going!")
        return redirect("campus:event_detail", pk=pk)
    return render(request, "campus/event_detail.html", {
        "event": event, "going": event.attendees.filter(pk=request.user.pk).exists(),
        "can_manage": request.user.role in ("staff", "admin"),
        "attendees": event.attendees.all() if request.user.role in ("staff", "admin") else None,
    })


# ------------------------------------------------------------------ complaints
class ComplaintList(BaseList):
    allowed_roles = ("student", "staff", "admin", "management")
    model = Complaint
    title = "Complaints"
    related = ("submitted_by",)
    columns = [("#", "pk"), ("Title", "title"), ("Category", "category"), ("Status", "status", "badge"),
               ("Submitted by", "submitted_by"), ("Date", "created")]
    actions = [("Open", "campus:complaint_detail", "btn-outline-secondary", False)]
    create_url = "campus:complaint_create"
    create_label = "File a complaint"
    manage_roles = ("student",)
    search_fields = ("title", "description", "submitted_by__username")

    def get_base_queryset(self):
        user = self.request.user
        return Complaint.objects.filter(submitted_by=user) if user.role == "student" else Complaint.objects.all()


class ComplaintCreate(BaseCreate):
    allowed_roles = ("student",)
    model = Complaint
    form_class = ComplaintForm
    title = "File a complaint"
    success_url = reverse_lazy("campus:complaint_list")

    def after_save(self, obj, adding):
        notify(User.objects.filter(role__in=["staff", "admin"], is_active=True), f"New complaint: {obj.title}",
               reverse("campus:complaint_detail", args=[obj.pk]))


@login_required
def complaint_detail(request, pk):
    user = request.user
    qs = Complaint.objects.select_related("submitted_by", "handled_by")
    if user.role == "student":
        qs = qs.filter(submitted_by=user)
    elif user.role not in ("staff", "admin", "management"):
        raise PermissionDenied
    complaint = get_object_or_404(qs, pk=pk)
    form = None
    if user.role in ("staff", "admin"):
        form = ComplaintResponseForm(request.POST or None, instance=complaint, user=user)
        if request.method == "POST" and form.is_valid():
            complaint = form.save(commit=False)
            complaint.handled_by = user
            complaint.save()
            audit(request, "COMPLAINT_UPDATE", f"#{complaint.pk} → {complaint.status}")
            notify(complaint.submitted_by, f"Your complaint '{complaint.title}' is now: {complaint.get_status_display()}",
                   reverse("campus:complaint_detail", args=[complaint.pk]))
            messages.success(request, "Complaint updated.")
            return redirect("campus:complaint_detail", pk=pk)
    return render(request, "campus/complaint_detail.html", {"c": complaint, "form": form})
