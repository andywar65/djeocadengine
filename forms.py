from django.forms import ModelForm

from djeocadengine.models import Drawing


class DrawingCreateForm(ModelForm):
    class Meta:
        model = Drawing
        fields = ["title", "dxf", "temp_image", "image"]


class DrawingParentForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(DrawingParentForm, self).__init__(*args, **kwargs)
        self.fields["parent"].queryset = Drawing.objects.exclude(epsg=None)

    class Meta:
        model = Drawing
        fields = ["parent"]
