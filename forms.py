from django.core.exceptions import ValidationError
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

    def clean(self):
        cleaned_data = super().clean()
        if "lat" not in cleaned_data:
            raise ValidationError("Invalid Latitude entry", code="invalid_lat")
        if "long" not in cleaned_data:
            raise ValidationError("Invalid Longitude entry", code="invalid_long")
        lat = cleaned_data["lat"]
        long = cleaned_data["long"]
        if lat > 90 or lat < -90:
            self.add_error("lat", "Invalid value")
        if long > 180 or long < -180:
            self.add_error("long", "Invalid value")
        return cleaned_data


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

    def clean(self):
        cleaned_data = super().clean()
        if "lat" not in cleaned_data:
            raise ValidationError("Invalid Latitude entry", code="invalid_lat")
        if "long" not in cleaned_data:
            raise ValidationError("Invalid Longitude entry", code="invalid_long")
        lat = cleaned_data["lat"]
        long = cleaned_data["long"]
        if lat > 90 or lat < -90:
            self.add_error("lat", "Invalid value")
        if long > 180 or long < -180:
            self.add_error("long", "Invalid value")
        return cleaned_data


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
