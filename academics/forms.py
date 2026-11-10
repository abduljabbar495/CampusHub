from django import forms

from accounts.forms import BModelForm, DateInput, TimeInput
from accounts.models import User

from .models import ClassSession, Course, Enrollment, Result
from .utils import courses_for_manage


class CourseForm(BModelForm):
    class Meta:
        model = Course
        fields = ["code", "title", "description", "credits", "semester", "teacher"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher"].queryset = User.objects.filter(role="teacher", is_approved=True)
        if self.user and self.user.role == "teacher":
            del self.fields["teacher"]

    def save(self, commit=True):
        if self.user and self.user.role == "teacher":
            self.instance.teacher = self.user
        return super().save(commit)


class SessionForm(BModelForm):
    class Meta:
        model = ClassSession
        fields = ["course", "title", "date", "start_time", "end_time", "room"]
        widgets = {"date": DateInput(), "start_time": TimeInput(), "end_time": TimeInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = courses_for_manage(self.user)

    def clean(self):
        data = super().clean()
        if data.get("start_time") and data.get("end_time") and data["end_time"] <= data["start_time"]:
            raise forms.ValidationError("End time must be after start time.")
        return data


class EnrollmentForm(BModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "course"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = User.objects.filter(role="student", is_active=True)


class ResultForm(BModelForm):
    class Meta:
        model = Result
        fields = ["student", "course", "exam_name", "marks", "total_marks", "remarks", "published"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = courses_for_manage(self.user)
        self.fields["student"].queryset = User.objects.filter(role="student")

    def clean(self):
        data = super().clean()
        marks, total = data.get("marks"), data.get("total_marks")
        if marks is not None and total is not None and (marks < 0 or marks > total):
            raise forms.ValidationError("Marks must be between 0 and the total marks.")
        student, course = data.get("student"), data.get("course")
        if student and course and not Enrollment.objects.filter(student=student, course=course).exists():
            raise forms.ValidationError("This student is not enrolled in the selected course.")
        return data
