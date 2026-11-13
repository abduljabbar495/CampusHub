from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from accounts.decorators import role_required
from .models import Notice, Event
from .forms import NoticeForm, EventForm

@login_required
def notice_list(request):
    qs = Notice.objects.filter(published=True).order_by("-priority", "-created_at")
    if request.user.role in ("ADMIN", "STAFF") or request.user.is_superuser:
        qs = Notice.objects.all().order_by("-priority", "-created_at")
    q = request.GET.get("q", "")
    category = request.GET.get("category", "")
    if q: qs = qs.filter(title__icontains=q)
    if category: qs = qs.filter(category=category)
    return render(request, "campus_events/notice_list.html", {"notices": qs, "q": q, "categories": Notice.Category.choices})

@role_required("ADMIN", "STAFF")
def notice_create(request):
    form = NoticeForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.created_by = request.user; obj.save()
        messages.success(request, "Notice saved.")
        return redirect("notice_list")
    return render(request, "form_page.html", {"form": form, "title": "Create notice"})

@login_required
def event_list(request):
    qs = Event.objects.filter(published=True, event_date__gte=timezone.localdate())
    if request.user.role in ("ADMIN", "STAFF") or request.user.is_superuser: qs = Event.objects.all()
    return render(request, "campus_events/event_list.html", {"events": qs})

@role_required("ADMIN", "STAFF")
def event_create(request):
    form = EventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False); obj.created_by = request.user; obj.save()
        messages.success(request, "Event saved.")
        return redirect("event_list")
    return render(request, "form_page.html", {"form": form, "title": "Create campus event"})

@role_required("ADMIN", "STAFF")
def notice_delete(request, pk):
    obj = get_object_or_404(Notice, pk=pk)
    if request.method == "POST": obj.delete()
    return redirect("notice_list")
