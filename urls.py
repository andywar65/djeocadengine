from django.urls import path
from django.utils.translation import gettext_lazy as _

from .views import (
    BaseListView,
    DrawingCreateView,
    DrawingDetailView,
    DrawingGeodataView,
    DrawingManualView,
    DrawingUpdateView,
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
]
