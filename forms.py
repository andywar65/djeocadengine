from django.forms import ModelForm
from djeocadengine.models import Drawing, Layer
from leaflet.forms.widgets import LeafletWidget


class DrawingCreateForm(ModelForm):
    class Meta:
        model = Drawing
        fields = ["title", "dxf", "temp_image"]


class DrawingParentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DrawingParentForm, self).__init__(*args, **kwargs)
        self.fields["parent"].queryset = Drawing.objects.exclude(epsg=None)

    class Meta:
        model = Drawing
        fields = ["parent"]


class DrawingManualForm(ModelForm):
    class Meta:
        model = Drawing
        fields = ["geom", "designx", "designy", "rotation"]
        widgets = {
            "geom": LeafletWidget(
                attrs={
                    "geom_type": "Point",
                }
            )
        }

    class Media:
        js = ("djeocadengine/js/locate_user.js",)


class DrawingUpdateForm(ModelForm):
    class Meta:
        model = Drawing
        fields = [
            "title",
            "dxf",
            "temp_image",
            "geom",
            "designx",
            "designy",
            "rotation",
        ]
        widgets = {
            "geom": LeafletWidget(
                attrs={
                    "geom_type": "Point",
                }
            )
        }


class LayerUpdateForm(ModelForm):
    class Meta:
        model = Layer
        fields = ["color_field", "linetype"]
