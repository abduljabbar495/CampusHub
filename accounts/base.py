"""Reusable generic views used by every app (list / create / update / delete with RBAC + audit)."""
from django.contrib import messages
from django.core.paginator import Paginator  # noqa: F401
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .audit import audit
from .permissions import RoleRequiredMixin


class BaseList(RoleRequiredMixin, ListView):
    template_name = "generic/list.html"
    paginate_by = 15
    title = ""
    columns = []          # (label, "attr.path"[, "badge"|"file"|"bool"])
    actions = []          # (label, url_name, css_class, manage_only)
    create_url = None
    create_label = "Add new"
    top_buttons = []      # (label, url_name)
    manage_roles = ()
    search_fields = ()
    related = ()

    def can_manage(self):
        return self.request.user.role in self.manage_roles

    def row_manageable(self, obj):
        return self.can_manage()

    def get_base_queryset(self):
        return self.model._default_manager.all()

    def get_queryset(self):
        qs = self.get_base_queryset()
        if self.related:
            qs = qs.select_related(*self.related)
        q = self.request.GET.get("q", "").strip()
        if q and self.search_fields:
            cond = Q()
            for field in self.search_fields:
                cond |= Q(**{f"{field}__icontains": q})
            qs = qs.filter(cond)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for obj in ctx["object_list"]:
            obj.manageable = self.row_manageable(obj)
        ctx.update(
            title=self.title,
            columns=self.columns,
            actions=self.actions,
            colspan=len(self.columns) + 1,
            searchable=bool(self.search_fields),
            top_buttons=self.top_buttons,
            create_url=reverse(self.create_url) if (self.create_url and self.can_manage()) else None,
            create_label=self.create_label,
        )
        return ctx


class AuditedFormMixin:
    title = ""
    success_message = "Saved successfully."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_cancel_url(self):
        return str(self.success_url) if self.success_url else "/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = self.title
        ctx["cancel_url"] = self.get_cancel_url()
        return ctx

    def after_save(self, obj, adding):
        pass

    def form_valid(self, form):
        adding = form.instance._state.adding
        response = super().form_valid(form)
        audit(self.request, "CREATE" if adding else "UPDATE", f"{self.model.__name__} #{self.object.pk}: {self.object}")
        messages.success(self.request, self.success_message)
        self.after_save(self.object, adding)
        return response


class BaseCreate(RoleRequiredMixin, AuditedFormMixin, CreateView):
    template_name = "generic/form.html"


class BaseUpdate(RoleRequiredMixin, AuditedFormMixin, UpdateView):
    template_name = "generic/form.html"


class BaseDelete(RoleRequiredMixin, DeleteView):
    template_name = "generic/confirm_delete.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cancel_url"] = str(self.success_url)
        return ctx

    def form_valid(self, form):
        desc = f"{self.model.__name__} #{self.object.pk}: {self.object}"
        response = super().form_valid(form)
        audit(self.request, "DELETE", desc)
        messages.success(self.request, "Deleted.")
        return response
