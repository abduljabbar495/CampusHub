import os
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from academics.models import ClassSession, Course, Enrollment
from accounts.models import User
from campus.models import Notice


class Command(BaseCommand):
    help = "Create demo users (one per role), a course, a class session and a notice. DEV/DEMO ONLY."

    def handle(self, *args, **options):
        password = os.environ.get("DEMO_PASSWORD", "CampusHub@2026!")
        specs = [("demo_admin", "admin"), ("demo_staff", "staff"), ("demo_teacher", "teacher"),
                 ("demo_guard", "guard"), ("demo_mgmt", "management"), ("demo_student", "student")]
        users = {}
        for username, role in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"role": role, "email": f"{username}@example.com", "first_name": username.split("_")[1].title(),
                          "last_name": "Demo", "is_approved": True},
            )
            if created:
                user.set_password(password)
                user.save()
            users[role] = user
        users["student"].student_id = users["student"].student_id or "232-00-001"
        users["student"].save()
        course, _ = Course.objects.get_or_create(code="SE331", defaults={"title": "Information Security Project", "teacher": users["teacher"]})
        Enrollment.objects.get_or_create(student=users["student"], course=course)
        today = timezone.localdate()
        ClassSession.objects.get_or_create(course=course, title="Lecture 1", date=today,
                                           defaults={"start_time": "10:00", "end_time": "11:30", "room": "Room 301"})
        Notice.objects.get_or_create(title="Welcome to CampusHub", defaults={"body": "This is a demo notice.", "audience": "all", "created_by": users["admin"]})
        self.stdout.write(self.style.SUCCESS(f"Demo data ready. Password for all demo_* users: {password}"))
