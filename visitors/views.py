import io
import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from accounts.decorators import role_required
from .models import Visitor
from .forms import VisitorForm

@role_required("SECURITY", "ADMIN")
def visitor_register(request):
    form = VisitorForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.registered_by = request.user; obj.save()
        return redirect("visitor_pass", pk=obj.pk)
    return render(request, "form_page.html", {"form": form, "title": "Register visitor"})

@role_required("SECURITY", "ADMIN")
def visitor_list(request):
    qs = Visitor.objects.all().order_by("-created_at")
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(phone__icontains=q) | qs.filter(pass_id__icontains=q)
    date = request.GET.get("date", "")
    if date: qs = qs.filter(created_at__date=date)
    return render(request, "visitors/visitor_list.html", {"visitors": qs, "q": q})

@role_required("SECURITY", "ADMIN")
def visitor_pass(request, pk):
    visitor = get_object_or_404(Visitor, pk=pk)
    return render(request, "visitors/visitor_pass.html", {"visitor": visitor})

@role_required("SECURITY", "ADMIN")
def visitor_qr(request, pk):
    visitor = get_object_or_404(Visitor, pk=pk)
    target = request.build_absolute_uri(reverse("visitor_scan", args=[visitor.pass_id]))
    img = qrcode.make(target)
    buffer = io.BytesIO(); img.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")

@role_required("SECURITY", "ADMIN")
def visitor_scan(request, pass_id):
    visitor = get_object_or_404(Visitor, pass_id=pass_id)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "in" and visitor.check_in():
            messages.success(request, "Visitor checked in.")
        elif action == "out" and visitor.check_out():
            messages.success(request, "Visitor checked out.")
        else:
            messages.error(request, "Invalid or duplicate check-in/check-out action.")
        return redirect("visitor_scan", pass_id=visitor.pass_id)
    return render(request, "visitors/visitor_scan.html", {"visitor": visitor})
