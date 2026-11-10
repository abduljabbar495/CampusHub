from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.audit import audit
from accounts.base import BaseCreate, BaseList
from accounts.models import User
from accounts.notify import notify
from accounts.permissions import role_required
from accounts.qr import qr_data_uri

from .forms import IncidentForm, IncidentManageForm, PassLookupForm, VisitorPassForm
from .models import Incident, Visitor, VisitorPass

GATE = ("guard", "admin")
GATE_VIEW = ("guard", "admin", "management")


# ------------------------------------------------------------------ visitor passes
class PassList(BaseList):
    allowed_roles = GATE_VIEW
    manage_roles = GATE
    model = VisitorPass
    title = "Visitor passes"
    related = ("visitor",)
    columns = [("Pass", "pk"), ("Visitor", "visitor"), ("Purpose", "visitor.purpose"), ("Host", "visitor.host_name"),
               ("Valid until", "valid_until"), ("Status", "status", "badge"),
               ("In", "checked_in_at"), ("Out", "checked_out_at")]
    actions = [("Open", "security:pass_detail", "btn-outline-secondary", False)]
    create_url = "security:pass_create"
    create_label = "Register visitor"
    top_buttons = [("Scan / lookup", "security:pass_lookup")]
    search_fields = ("visitor__name", "visitor__phone", "visitor__purpose", "visitor__host_name")

    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        return qs.filter(status=status) if status in dict(VisitorPass.Status.choices) else qs

    def get_context_data(self, **kwargs):
        # lazily expire stale passes shown on this page
        for p in VisitorPass.objects.filter(status="issued", valid_until__lt=timezone.now())[:200]:
            p.refresh_status()
        return super().get_context_data(**kwargs)


@role_required(*GATE)
def pass_create(request):
    form = VisitorPassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            visitor = Visitor(name=d["name"], phone=d["phone"], purpose=d["purpose"], host_name=d["host_name"])
            visitor.set_id_number(d["id_number"])
            visitor.save()
            vpass = VisitorPass.objects.create(
                visitor=visitor, issued_by=request.user,
                valid_until=timezone.now() + timedelta(hours=d["valid_hours"]))
        audit(request, "VISITOR_PASS_ISSUED", f"Pass #{vpass.pk} for {visitor.name}")
        messages.success(request, "Visitor registered and pass issued.")
        return redirect("security:pass_detail", pk=vpass.pk)
    return render(request, "generic/form.html", {"form": form, "title": "Register visitor & issue pass",
                                                  "cancel_url": reverse("security:pass_list")})


@role_required(*GATE_VIEW)
def pass_detail(request, pk):
    vpass = get_object_or_404(VisitorPass.objects.select_related("visitor", "issued_by"), pk=pk)
    vpass.refresh_status()
    link = request.build_absolute_uri(reverse("security:pass_scan", args=[vpass.token]))
    return render(request, "security/pass_detail.html", {
        "p": vpass, "qr": qr_data_uri(link), "can_act": request.user.role in GATE})


@role_required(*GATE)
def pass_scan(request, token):
    """Target of the QR code: guards land on the pass and can check the visitor in/out."""
    vpass = get_object_or_404(VisitorPass, token=token)
    audit(request, "VISITOR_PASS_SCANNED", f"Pass #{vpass.pk}")
    return redirect("security:pass_detail", pk=vpass.pk)


@role_required(*GATE)
def pass_lookup(request):
    form = PassLookupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"].strip().rstrip("/").split("/")[-1]
        vpass = VisitorPass.objects.filter(token=code).first()
        if vpass is None and code.isdigit():
            vpass = VisitorPass.objects.filter(pk=int(code)).first()
        if vpass:
            return redirect("security:pass_detail", pk=vpass.pk)
        audit(request, "VISITOR_PASS_INVALID", "Lookup failed")
        messages.error(request, "No pass matches that code.")
    return render(request, "security/pass_lookup.html", {"form": form})


@role_required(*GATE)
@require_POST
def pass_action(request, pk):
    vpass = get_object_or_404(VisitorPass, pk=pk)
    vpass.refresh_status()
    action = request.POST.get("action")
    now = timezone.now()
    if action == "checkin":
        if vpass.status != "issued":
            messages.error(request, f"Cannot check in: pass is {vpass.get_status_display().lower()}.")
        elif not vpass.is_valid_now():
            messages.error(request, "Pass is outside its validity window.")
        else:
            vpass.status, vpass.checked_in_at = "checked_in", now
            vpass.save(update_fields=["status", "checked_in_at"])
            audit(request, "VISITOR_CHECK_IN", f"Pass #{vpass.pk} {vpass.visitor}")
            messages.success(request, "Visitor checked in.")
    elif action == "checkout":
        if vpass.status != "checked_in":
            messages.error(request, "Visitor is not checked in.")
        else:
            vpass.status, vpass.checked_out_at = "checked_out", now
            vpass.save(update_fields=["status", "checked_out_at"])
            audit(request, "VISITOR_CHECK_OUT", f"Pass #{vpass.pk} {vpass.visitor}")
            messages.success(request, "Visitor checked out.")
    elif action == "revoke":
        if vpass.status in ("issued", "checked_in"):
            vpass.status = "revoked"
            vpass.save(update_fields=["status"])
            audit(request, "VISITOR_PASS_REVOKED", f"Pass #{vpass.pk}")
            messages.warning(request, "Pass revoked.")
    return redirect("security:pass_detail", pk=pk)


# ------------------------------------------------------------------ incidents
class IncidentList(BaseList):
    model = Incident
    title = "Security incidents"
    related = ("reporter",)
    columns = [("#", "pk"), ("Title", "title"), ("Location", "location"), ("Severity", "severity", "badge"),
               ("Status", "status", "badge"), ("Reported by", "reporter"), ("Date", "created")]
    actions = [("Open", "security:incident_detail", "btn-outline-secondary", False)]
    create_url = "security:incident_create"
    create_label = "Report incident"
    manage_roles = ("student", "teacher", "staff", "guard", "admin")
    search_fields = ("title", "location", "description")

    def get_base_queryset(self):
        user = self.request.user
        if user.role in ("guard", "admin", "management"):
            return Incident.objects.all()
        return Incident.objects.filter(reporter=user)


class IncidentCreate(BaseCreate):
    allowed_roles = ("student", "teacher", "staff", "guard", "admin")
    model = Incident
    form_class = IncidentForm
    title = "Report a security incident"
    success_url = reverse_lazy("security:incident_list")

    def after_save(self, obj, adding):
        notify(User.objects.filter(role__in=["guard", "admin"], is_active=True).exclude(pk=obj.reporter_id),
               f"New {obj.get_severity_display().lower()} incident: {obj.title}", reverse("security:incident_detail", args=[obj.pk]))


@login_required
def incident_detail(request, pk):
    user = request.user
    qs = Incident.objects.select_related("reporter", "assigned_to")
    if user.role not in ("guard", "admin", "management"):
        qs = qs.filter(reporter=user)
    incident = get_object_or_404(qs, pk=pk)
    form = None
    if user.role in GATE:
        old_status = incident.status
        form = IncidentManageForm(request.POST or None, instance=incident, user=user)
        if request.method == "POST" and form.is_valid():
            incident = form.save()
            audit(request, "INCIDENT_UPDATE", f"#{incident.pk} {old_status} → {incident.status}")
            if incident.status != old_status:
                notify(incident.reporter, f"Your incident '{incident.title}' is now: {incident.get_status_display()}",
                       reverse("security:incident_detail", args=[incident.pk]))
            if incident.assigned_to_id and incident.assigned_to_id != user.id:
                notify(incident.assigned_to, f"Incident assigned to you: {incident.title}",
                       reverse("security:incident_detail", args=[incident.pk]))
            messages.success(request, "Incident updated.")
            return redirect("security:incident_detail", pk=pk)
    return render(request, "security/incident_detail.html", {"i": incident, "form": form})
