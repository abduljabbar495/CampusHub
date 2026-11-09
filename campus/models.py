from django.conf import settings
from django.db import models

from academics.models import Course
from accounts.validators import UploadTo, validate_upload

User = settings.AUTH_USER_MODEL


class Material(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    file = models.FileField(upload_to=UploadTo("materials"), validators=[validate_upload])
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="materials")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to=UploadTo("assignments"), validators=[validate_upload], blank=True)
    due_date = models.DateTimeField()
    max_marks = models.PositiveSmallIntegerField(default=10)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="assignments_created")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return self.title


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    text = models.TextField(blank=True)
    file = models.FileField(upload_to=UploadTo("submissions"), validators=[validate_upload], blank=True)
    submitted_at = models.DateTimeField(auto_now=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student} → {self.assignment}"


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=200)
    duration_minutes = models.PositiveSmallIntegerField(default=15)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="quizzes_created")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name_plural = "quizzes"

    def __str__(self):
        return self.title

    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    CHOICES = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct = models.CharField(max_length=1, choices=CHOICES)
    marks = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text[:60]

    def options(self):
        return [("A", self.option_a), ("B", self.option_b), ("C", self.option_c), ("D", self.option_d)]


class QuizAttempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("quiz", "student")
        ordering = ["-started_at"]


class Notice(models.Model):
    AUDIENCES = [("all", "Everyone"), ("student", "Students"), ("teacher", "Teachers"),
                 ("staff", "Administrative staff"), ("guard", "Security team")]
    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=10, choices=AUDIENCES, default="all")
    pinned = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="notices")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pinned", "-created"]

    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=150)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="events_created")
    attendees = models.ManyToManyField(User, blank=True, related_name="events_attending")

    class Meta:
        ordering = ["start"]

    def __str__(self):
        return self.title

    def going(self):
        return self.attendees.count()


class Complaint(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_REVIEW = "in_review", "In review"
        RESOLVED = "resolved", "Resolved"
        REJECTED = "rejected", "Rejected"

    class Category(models.TextChoices):
        ACADEMIC = "academic", "Academic"
        FACILITY = "facility", "Facilities"
        ADMIN = "administrative", "Administrative"
        HARASSMENT = "harassment", "Harassment / safety"
        OTHER = "other", "Other"

    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="complaints")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    response = models.TextField(blank=True)
    handled_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="complaints_handled")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title
