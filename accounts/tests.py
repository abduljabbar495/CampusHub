import time
from datetime import time as dtime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from academics.models import Attendance, ClassSession, Course, Enrollment
from accounts import mfa
from accounts.models import AuditLog, User

PASSWORD = "S3cure-Test-Pass!"


def make_user(username, role, **extra):
    return User.objects.create_user(username=username, password=PASSWORD, role=role, **extra)


class SecurityTests(TestCase):
    def test_totp_roundtrip(self):
        secret = mfa.new_secret()
        code = mfa._code(secret, int(time.time() // 30))
        self.assertTrue(mfa.verify(secret, code))
        self.assertFalse(mfa.verify(secret, "000000" if code != "000000" else "111111"))

    def test_rbac_blocks_student_from_admin_pages(self):
        make_user("stu", "student")
        self.client.login(username="stu", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("accounts:user_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("accounts:audit_list")).status_code, 403)
        self.assertTrue(AuditLog.objects.filter(action="ACCESS_DENIED").exists())

    def test_admin_can_open_user_list(self):
        make_user("boss", "admin")
        self.client.login(username="boss", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("accounts:user_list")).status_code, 200)

    def test_account_locks_after_repeated_failures(self):
        user = make_user("victim", "student")
        for _ in range(5):
            self.client.post(reverse("accounts:login"), {"username": "victim", "password": "wrong"})
        user.refresh_from_db()
        self.assertTrue(user.is_locked())
        resp = self.client.post(reverse("accounts:login"), {"username": "victim", "password": PASSWORD})
        self.assertEqual(resp.status_code, 200)  # still on login page: locked even with right password

    def test_teacher_needs_approval(self):
        make_user("teach", "teacher", is_approved=False)
        resp = self.client.post(reverse("accounts:login"), {"username": "teach", "password": PASSWORD})
        self.assertEqual(resp.status_code, 200)


class AttendanceTests(TestCase):
    def setUp(self):
        self.teacher = make_user("t1", "teacher")
        self.student = make_user("s1", "student")
        self.course = Course.objects.create(code="SE331", title="Project", teacher=self.teacher)
        Enrollment.objects.create(student=self.student, course=self.course)
        self.session = ClassSession.objects.create(
            course=self.course, title="L1", date=timezone.localdate(),
            start_time=dtime(10, 0), end_time=dtime(11, 0), room="R1", attendance_open=True)

    def test_student_marks_attendance_via_qr_link(self):
        self.client.login(username="s1", password=PASSWORD)
        url = reverse("academics:attend", args=[self.session.qr_token])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url)
        self.assertTrue(Attendance.objects.filter(session=self.session, student=self.student).exists())

    def test_closed_session_rejects_attendance(self):
        self.session.attendance_open = False
        self.session.save()
        self.client.login(username="s1", password=PASSWORD)
        self.client.post(reverse("academics:attend", args=[self.session.qr_token]))
        self.assertFalse(Attendance.objects.exists())
