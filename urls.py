from django.urls import path
from django.utils.translation import gettext_lazy as _

from .views import DrawingCreateView, DrawingDetailView

app_name = "djeocad"
urlpatterns = [
    path(
        _("drawing/add/"),
        DrawingCreateView.as_view(),
        name="drawing_simple_create",
    ),
    path(
        _("drawing/<pk>/"),
        DrawingDetailView.as_view(),
        name="drawing_detail",
    ),
]
