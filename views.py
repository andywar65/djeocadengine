import csv
import json

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from filer.models import Image

from .forms import (
    DrawingCreateForm,
    DrawingManualForm,
    DrawingParentForm,
    DrawingUpdateForm,
    LayerUpdateForm,
)
from .models import Drawing, Entity, Layer


class HxPageTemplateMixin:
    """Switches template depending on request.htmx"""

    def get_template_names(self):
        if not self.request.htmx:
            return [self.template_name.replace("htmx/", "")]
        return [self.template_name]


class BaseListView(HxPageTemplateMixin, ListView):
    model = Drawing
    context_object_name = "drawings"
    template_name = "djeocadengine/htmx/base_list.html"

    def dispatch(self, request, *args, **kwargs):
        response = super(BaseListView, self).dispatch(request, *args, **kwargs)
        if request.htmx:
            dict = {"refreshCollections": True}
            response["HX-Trigger-After-Swap"] = json.dumps(dict)
        return response


class DrawingCreateView(PermissionRequiredMixin, HxPageTemplateMixin, CreateView):
    model = Drawing
    permission_required = "djeocadengine.add_drawing"
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
            return reverse(
                "djeocadengine:drawing_geodata",
                kwargs={"pk": self.object.id},
            )
        return reverse(
            "djeocadengine:drawing_detail",
            kwargs={"pk": self.object.id},
        )


class DrawingGeodataView(PermissionRequiredMixin, HxPageTemplateMixin, UpdateView):
    model = Drawing
    permission_required = "djeocadengine.change_drawing"
    template_name = "djeocadengine/htmx/drawing_geodata.html"
    form_class = DrawingParentForm

    def get_success_url(self):
        return reverse(
            "djeocadengine:drawing_detail",
            kwargs={"pk": self.object.id},
        )


class DrawingManualView(PermissionRequiredMixin, HxPageTemplateMixin, UpdateView):
    model = Drawing
    permission_required = "djeocadengine.change_drawing"
    template_name = "djeocadengine/includes/drawing_manual.html"
    form_class = DrawingManualForm

    def get_success_url(self):
        return reverse(
            "djeocadengine:drawing_detail",
            kwargs={"pk": self.object.id},
        )


class DrawingDetailView(HxPageTemplateMixin, DetailView):
    model = Drawing
    template_name = "djeocadengine/htmx/drawing_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        layers = self.object.related_layers.filter(is_block=False)
        id_list = layers.values_list("id", flat=True)
        context["lines"] = Entity.objects.filter(
            layer_id__in=id_list
        ).prefetch_related()
        context["drawings"] = self.object
        name_list = layers.values_list("name", flat=True)
        context["layer_list"] = list(dict.fromkeys(name_list))
        context["layer_list"] = [_("Layer - ") + s for s in context["layer_list"]]
        return context

    def dispatch(self, request, *args, **kwargs):
        response = super(DrawingDetailView, self).dispatch(request, *args, **kwargs)
        if request.htmx:
            dict = {"refreshCollections": True}
            response["HX-Trigger-After-Swap"] = json.dumps(dict)
        return response


class DrawingUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "djeocadengine.change_drawing"
    model = Drawing
    form_class = DrawingUpdateForm
    template_name = "djeocadengine/includes/drawing_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["layers"] = self.object.related_layers.filter(is_block=False)
        context["blocks"] = self.object.related_layers.filter(is_block=True)
        return context

    def form_valid(self, form):
        if form.cleaned_data["temp_image"]:
            img = Image.objects.create(
                owner=self.request.user,
                original_filename=form.cleaned_data["title"],
                file=form.cleaned_data["temp_image"],
            )
            form.instance.image = img
            form.instance.temp_image = None
        return super(DrawingUpdateView, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            "djeocadengine:drawing_detail",
            kwargs={"pk": self.object.id},
        )


@permission_required("djeocadengine.delete_drawing")
def drawing_delete_view(request, pk):
    if not request.htmx:
        raise Http404("Request without HTMX headers")
    drawing = get_object_or_404(Drawing, id=pk)
    drawing.delete()
    return TemplateResponse(
        request,
        "djeocadengine/htmx/drawing_delete.html",
        {},
    )


class LayerDetailView(DetailView):
    model = Layer
    template_name = "djeocadengine/htmx/layer_inline.html"
    context_object_name = "layer"

    def get_template_names(self):
        if not self.request.htmx:
            raise Http404("Request without HTMX headers")
        return [self.template_name]


class LayerUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = "djeocadengine.change_layer"
    model = Layer
    form_class = LayerUpdateForm
    template_name = "djeocadengine/htmx/layer_update.html"

    def get_template_names(self):
        if not self.request.htmx:
            raise Http404("Request without HTMX headers")
        return [self.template_name]

    def get_success_url(self):
        return reverse(
            "djeocadengine:layer_detail",
            kwargs={"pk": self.object.id},
        )


@permission_required("djeocadengine.delete_layer")
def layer_delete_view(request, pk):
    layer = get_object_or_404(Layer, id=pk)
    if not request.htmx or layer.name == "0":
        raise Http404("Request without HTMX headers")
    layer.delete()
    return TemplateResponse(
        request,
        "djeocadengine/htmx/layer_delete.html",
        {},
    )


def csv_download(request, pk):
    drawing = get_object_or_404(Drawing, id=pk)
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{drawing.title}.csv"'
    writer = csv.writer(response)
    writer = drawing.write_csv(writer)

    return response


def drawing_download(request, pk):
    drawing = get_object_or_404(Drawing, id=pk)
    if drawing.needs_refresh:
        drawing.add_geodata_to_file()
    response = HttpResponse(drawing.dxf, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename=%s.dxf" % drawing.title

    return response
