from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView

from .forms import DrawingCreateForm
from .models import Drawing


class HxPageTemplateMixin:
    """Switches template depending on request.htmx"""

    def get_template_names(self):
        if not self.request.htmx:
            return [self.template_name.replace("htmx/", "")]
        return [self.template_name]


class DrawingCreateView(PermissionRequiredMixin, HxPageTemplateMixin, CreateView):
    model = Drawing
    permission_required = "djeocad.add_drawing"
    form_class = DrawingCreateForm
    template_name = "djeocad/htmx/drawing_create.html"

    def get_success_url(self):
        if not self.object.epsg:
            pass
            # return reverse(
            # "djeocad:drawing_simple_geodata",
            # kwargs={"pk": self.object.id},
            # )
        return reverse(
            "home"
            # "djeocad:drawing_detail",
            # kwargs={"pk": self.object.id},
        )
