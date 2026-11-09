import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


def new_token():
    return secrets.token_urlsafe(24)


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits = models.PositiveSmallIntegerField(default=3)
    semester = models.CharField(max_length=30, default="Fall 2026")
    teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="courses_taught",
                                limit_choices_to={"role": "teacher"})
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} – {self.title}"


class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments", limit_choices_to={"role": "student"})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["course__code", "student__username"]

    def __str__(self):
        return f"{self.student} in {self.course.code}"


class ClassSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=150)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    qr_token = models.CharField(max_length=64, unique=True, default=new_token)
    attendance_open = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date", "start_time"]

    def __str__(self):
        return f"{self.course.code} {self.title} ({self.date})"

    def time_range(self):
        return f"{self.start_time:%H:%M} – {self.end_time:%H:%M}"


class Attendance(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="attendances")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendances")
    marked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "student")


class Result(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="results", limit_choices_to={"role": "student"})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="results")
    exam_name = models.CharField(max_length=100, help_text="e.g. Midterm, Final, Quiz 1")
    marks = models.DecimalField(max_digits=6, decimal_places=2)
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("100"))
    remarks = models.CharField(max_length=200, blank=True)
    published = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="results_entered")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.student} {self.course.code} {self.exam_name}"

    def score_text(self):
        return f"{self.marks:g} / {self.total_marks:g}"

    def grade(self):
        pct = float(self.marks) * 100 / float(self.total_marks) if self.total_marks else 0
        for limit, grade in ((80, "A+"), (75, "A"), (70, "A-"), (65, "B+"), (60, "B"), (55, "B-"), (50, "C"), (40, "D")):
            if pct >= limit:
                return grade
        return "F"
