from django.contrib import admin

from .models import Incident, Visitor, VisitorPass

for model in (Visitor, VisitorPass, Incident):
    admin.site.register(model)
