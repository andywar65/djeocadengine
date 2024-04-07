from django.urls import path
from django.utils.translation import gettext_lazy as _

from .views import (
    BaseListView,
    DrawingCreateView,
    DrawingDetailView,
    DrawingGeodataView,
    DrawingManualView,
    DrawingUpdateView,
    LayerDetailView,
    LayerUpdateView,
    csv_download,
    drawing_delete_view,
    layer_delete_view,
)

app_name = "djeocadengine"
urlpatterns = [
    path("", BaseListView.as_view(), name="base_list"),
    path(
        _("drawing/add/"),
        DrawingCreateView.as_view(),
        name="drawing_create",
    ),
    path(
        _("drawing/<pk>/"),
        DrawingDetailView.as_view(),
        name="drawing_detail",
    ),
    path(
        _("drawing/<pk>/geodata"),
        DrawingGeodataView.as_view(),
        name="drawing_geodata",
    ),
    path(
        _("drawing/<pk>/manual"),
        DrawingManualView.as_view(),
        name="drawing_manual",
    ),
    path(
        _("drawing/<pk>/update"),
        DrawingUpdateView.as_view(),
        name="drawing_update",
    ),
    path(
        "drawing/<pk>/delete",
        drawing_delete_view,
        name="drawing_delete",
    ),
    path(
        "layer/<pk>/",
        LayerDetailView.as_view(),
        name="layer_detail",
    ),
    path(
        "layer/<pk>/update",
        LayerUpdateView.as_view(),
        name="layer_update",
    ),
    path(
        "layer/<pk>/delete",
        layer_delete_view,
        name="layer_delete",
    ),
    path(
        "drawing/<pk>/csv",
        csv_download,
        name="drawing_csv",
    ),
]
