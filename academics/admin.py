from django.contrib import admin

from .models import Attendance, ClassSession, Course, Enrollment, Result

for model in (Course, Enrollment, ClassSession, Attendance, Result):
    admin.site.register(model)
