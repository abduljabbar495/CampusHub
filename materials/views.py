from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from academics.models import Course
from .models import CourseMaterial
from .forms import MaterialForm

@login_required
def material_list(request):
    qs = CourseMaterial.objects.select_related("course", "uploaded_by")
    if request.user.role == "STUDENT":
        qs = qs.filter(course__students=request.user)
    elif request.user.role == "TEACHER":
        qs = qs.filter(course__teacher=request.user)
    q = request.GET.get("q", "")
    if q: qs = qs.filter(title__icontains=q)
    return render(request, "materials/material_list.html", {"materials": qs, "q": q})

@role_required("TEACHER", "ADMIN")
def material_upload(request):
    form = MaterialForm(request.POST or None, request.FILES or None)
    if request.user.role == "TEACHER":
        form.fields["course"].queryset = Course.objects.filter(teacher=request.user)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        if request.user.role == "TEACHER" and item.course.teacher_id != request.user.id:
            messages.error(request, "You can only upload to your assigned courses.")
        else:
            item.uploaded_by = request.user
            item.save()
            return redirect("material_list")
    return render(request, "form_page.html", {"form": form, "title": "Upload course material"})

@login_required
def material_download(request, pk):
    item = get_object_or_404(CourseMaterial, pk=pk)
    if request.user.role == "STUDENT" and not item.course.students.filter(pk=request.user.pk).exists():
        raise Http404
    if request.user.role == "TEACHER" and item.course.teacher_id != request.user.id:
        raise Http404
    return FileResponse(item.file.open("rb"), as_attachment=True, filename=item.file.name.split("/")[-1])

@role_required("TEACHER", "ADMIN")
def material_delete(request, pk):
    item = get_object_or_404(CourseMaterial, pk=pk)
    if request.user.role == "TEACHER" and item.uploaded_by_id != request.user.id:
        raise Http404
    if request.method == "POST":
        item.delete()
    return redirect("material_list")
