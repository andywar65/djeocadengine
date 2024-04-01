from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView
from filer.models import Image

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
    template_name = "djeocadengine/htmx/drawing_create.html"

    def form_valid(self, form):
        if form.cleaned_data["temp_image"]:
            img = Image.objects.create(
                owner=self.request.user,
                original_filename=form.cleaned_data["title"],
                file=form.cleaned_data["temp_image"],
            )
            form.instance.image = img
            form.instance.temp_image = None
        return super(DrawingCreateView, self).form_valid(form)

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
