from django.contrib import admin

from .models import (Assignment, Complaint, Event, Material, Notice, Question, Quiz, QuizAttempt, Submission)

for model in (Material, Assignment, Submission, Quiz, Question, QuizAttempt, Notice, Event, Complaint):
    admin.site.register(model)
