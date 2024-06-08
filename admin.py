from django.contrib import admin

from .models import Drawing, Layer


class LayerInline(admin.TabularInline):
    model = Layer
    fields = ("name", "color_field", "linetype")
    extra = 0


@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display = ("title",)
    exclude = ("temp_image", "geom")
    inlines = [
        LayerInline,
    ]
