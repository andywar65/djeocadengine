import json

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, DetailView
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
            "djeocadengine:drawing_detail",
            kwargs={"pk": self.object.id},
        )


class DrawingDetailView(HxPageTemplateMixin, DetailView):
    model = Drawing
    template_name = "djeocadengine/htmx/drawing_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["lines"] = self.object.related_layers.filter(is_block=False)
        # context["blocks"] = self.object.related_layers.filter(is_block=True)
        # id_list = context["lines"].values_list("id", flat=True)
        # context["insertions"] = Insertion.objects.filter(layer_id__in=id_list)
        context["drawings"] = self.object
        # context["author_list"] = [_("Author - ") + self.object.user.username]
        # name_list = context["lines"].values_list("name", flat=True)
        # context["layer_list"] = list(dict.fromkeys(name_list))
        # context["layer_list"] = [_("Layer - ") + s for s in context["layer_list"]]
        return context

    def dispatch(self, request, *args, **kwargs):
        response = super(DrawingDetailView, self).dispatch(request, *args, **kwargs)
        if request.htmx:
            dict = {"refreshCollections": True}
            response["HX-Trigger-After-Swap"] = json.dumps(dict)
        return response
