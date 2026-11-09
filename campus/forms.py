from django import forms

from accounts.forms import BModelForm, DateTimeInput
from academics.utils import courses_for_manage

from .models import Assignment, Complaint, Event, Material, Notice, Question, Quiz, Submission


class CourseScopedForm(BModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "course" in self.fields:
            self.fields["course"].queryset = courses_for_manage(self.user)


class MaterialForm(CourseScopedForm):
    owner_field = "uploaded_by"

    class Meta:
        model = Material
        fields = ["course", "title", "description", "file"]


class AssignmentForm(CourseScopedForm):
    owner_field = "created_by"

    class Meta:
        model = Assignment
        fields = ["course", "title", "description", "attachment", "due_date", "max_marks"]
        widgets = {"due_date": DateTimeInput(), "description": forms.Textarea(attrs={"rows": 4})}


class SubmissionForm(BModelForm):
    class Meta:
        model = Submission
        fields = ["text", "file"]
        widgets = {"text": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        data = super().clean()
        if not data.get("text") and not data.get("file") and not (self.instance and self.instance.file):
            raise forms.ValidationError("Write an answer or attach a file.")
        return data


class GradeForm(BModelForm):
    class Meta:
        model = Submission
        fields = ["marks", "feedback"]

    def clean_marks(self):
        marks = self.cleaned_data["marks"]
        if marks is not None and (marks < 0 or marks > self.instance.assignment.max_marks):
            raise forms.ValidationError(f"Marks must be between 0 and {self.instance.assignment.max_marks}.")
        return marks


class QuizForm(CourseScopedForm):
    owner_field = "created_by"

    class Meta:
        model = Quiz
        fields = ["course", "title", "duration_minutes", "is_published"]


class QuestionForm(BModelForm):
    class Meta:
        model = Question
        fields = ["text", "option_a", "option_b", "option_c", "option_d", "correct", "marks"]
        widgets = {"text": forms.Textarea(attrs={"rows": 2})}


class NoticeForm(BModelForm):
    owner_field = "created_by"

    class Meta:
        model = Notice
        fields = ["title", "body", "audience", "pinned"]
        widgets = {"body": forms.Textarea(attrs={"rows": 5})}


class EventForm(BModelForm):
    owner_field = "created_by"

    class Meta:
        model = Event
        fields = ["title", "description", "location", "start", "end"]
        widgets = {"start": DateTimeInput(), "end": DateTimeInput(), "description": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        data = super().clean()
        if data.get("start") and data.get("end") and data["end"] <= data["start"]:
            raise forms.ValidationError("The event must end after it starts.")
        return data


class ComplaintForm(BModelForm):
    owner_field = "submitted_by"

    class Meta:
        model = Complaint
        fields = ["category", "title", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class ComplaintResponseForm(BModelForm):
    class Meta:
        model = Complaint
        fields = ["status", "response"]
        widgets = {"response": forms.Textarea(attrs={"rows": 3})}
