from django.forms import CharField, FileInput, ModelForm, TextInput

from djeocadengine.models import Drawing, Layer


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
        fields = ["lat", "long", "designx", "designy", "rotation"]

    class Media:
        # not used
        js = ("djeocadengine/js/locate_user.js",)


class DrawingUpdateForm(ModelForm):
    class Meta:
        model = Drawing
        fields = [
            "title",
            "dxf",
            "temp_image",
            "lat",
            "long",
            "designx",
            "designy",
            "rotation",
        ]
        widgets = {
            "dxf": FileInput(),
        }


class LayerUpdateForm(ModelForm):
    color_field = CharField(
        label="Color",
        required=True,
        widget=TextInput(
            attrs={"class": "form-control form-control-color", "type": "color"}
        ),
    )

    class Meta:
        model = Layer
        fields = ["color_field", "linetype"]
