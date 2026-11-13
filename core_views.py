from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.models import User

@login_required
def dashboard(request):
    if request.user.role == User.Role.TEACHER:
        return render(request, "dashboard_teacher.html")
    if request.user.role == User.Role.STUDENT:
        return render(request, "dashboard_student.html")
    return render(request, "dashboard.html")
