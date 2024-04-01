from django.forms import ModelForm

from djeocadengine.models import Drawing


class DrawingCreateForm(ModelForm):
    class Meta:
        model = Drawing
        fields = ["title", "dxf", "temp_image"]
