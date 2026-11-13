from django import forms
from .models import Notice, Event
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ("title", "description", "category", "attachment", "priority", "published")
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ("name", "description", "event_date", "start_time", "location", "published")
        widgets = {"event_date": forms.DateInput(attrs={"type": "date"}), "start_time": forms.TimeInput(attrs={"type": "time"})}
