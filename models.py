import json
from math import atan2, degrees
from pathlib import Path

import ezdxf
from colorfield.fields import ColorField
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from djgeojson.fields import GeometryCollectionField, PointField
from easy_thumbnails.files import get_thumbnailer
from ezdxf.lldxf.const import InvalidGeoDataException
from filer.fields.image import FilerImageField
from pyproj import Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info


class Drawing(models.Model):

    title = models.CharField(
        _("Name"),
        help_text=_("Name of the drawing"),
        max_length=50,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="parent_drawing",
        verbose_name=_("Parent Drawing"),
        null=True,
        blank=True,
    )
    image = FilerImageField(
        null=True, blank=True, related_name="drawing_image", on_delete=models.SET_NULL
    )
    temp_image = models.ImageField(_("Image"), null=True, blank=True)
    dxf = models.FileField(
        _("DXF file"),
        max_length=200,
        upload_to="uploads/djeocad/dxf/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "dxf",
                ]
            )
        ],
    )
    geom = PointField(_("Location"), null=True)
    designx = models.FloatField(
        _("Design point X..."),
        default=0,
    )
    designy = models.FloatField(
        _("...Y"),
        default=0,
    )
    rotation = models.FloatField(
        _("Rotation"),
        default=0,
    )
    needs_refresh = models.BooleanField(
        _("Refresh DXF file from layers"),
        default=True,
        editable=False,
    )
    epsg = models.IntegerField(
        _("CRS code"),
        null=True,
        editable=False,
    )

    class Meta:
        verbose_name = _("Drawing")
        verbose_name_plural = _("Drawings")

    __original_dxf = None
    __original_geom = None
    __original_designx = None
    __original_designy = None
    __original_rotation = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_dxf = self.dxf
        self.__original_geom = self.geom
        self.__original_designx = self.designx
        self.__original_designy = self.designy
        self.__original_rotation = self.rotation

    def __str__(self):
        return self.title

    @property
    def popupContent(self):
        url = reverse(
            "djeocad:drawing_detail",
            kwargs={"pk": self.id},
        )
        title_str = '<h5><a href="%(url)s">%(title)s</a></h5>' % {
            "title": self.title,
            "url": url,
        }
        image = self.image
        if not image:
            return {"content": title_str}
        thumbnailer = get_thumbnailer(image)
        thumb = thumbnailer.get_thumbnail({"size": (256, 256), "crop": True})
        image_str = '<img src="%(image)s">' % {"image": thumb.url}
        return {"content": title_str + image_str}

    def save(self, *args, **kwargs):
        # save and eventually upload DXF
        super(Drawing, self).save(*args, **kwargs)
        # check if we have coordinate system
        if not self.epsg:
            # search geodata in parent
            if self.parent:
                self.geom = self.parent.geom
                self.epsg = self.parent.epsg
                self.designx = self.parent.designx
                self.designy = self.parent.designy
                self.rotation = self.parent.rotation
                super(Drawing, self).save(*args, **kwargs)
            # search for geodata in DXF
            doc = ezdxf.readfile(Path(settings.MEDIA_ROOT).joinpath(str(self.dxf)))
            msp = doc.modelspace()
            geodata = msp.get_geodata()
            if geodata:
                # check if valid XML and axis order
                try:
                    self.epsg, axis = geodata.get_crs()
                    if not axis:
                        return
                except InvalidGeoDataException:
                    return
                utm2world = Transformer.from_crs(self.epsg, 4326, always_xy=True)
                world_point = utm2world.transform(
                    geodata.dxf.reference_point[0], geodata.dxf.reference_point[1]
                )
                self.geom = {"type": "Point", "coordinates": world_point}
                self.designx = geodata.dxf.design_point[0]
                self.designy = geodata.dxf.design_point[1]
                self.rotation = degrees(
                    atan2(
                        geodata.dxf.north_direction[0], geodata.dxf.north_direction[1]
                    )
                )
                super(Drawing, self).save(*args, **kwargs)
            else:
                # can't find geodata in DXF, need manual insertion
                # check if user has inserted origin on map
                if self.geom:
                    # following conditional for test to work
                    if isinstance(self.geom, str):
                        self.geom = json.loads(self.geom)
                    # let's try to find proper UTM
                    utm_crs_list = query_utm_crs_info(
                        datum_name="WGS 84",
                        area_of_interest=AreaOfInterest(
                            west_lon_degree=self.geom["coordinates"][0],
                            south_lat_degree=self.geom["coordinates"][1],
                            east_lon_degree=self.geom["coordinates"][0],
                            north_lat_degree=self.geom["coordinates"][1],
                        ),
                    )
                    self.epsg = utm_crs_list[0].code
                    super(Drawing, self).save(*args, **kwargs)
        # without geom (insertion) we can't extract DXF
        if self.geom:
            if (
                self.__original_dxf != self.dxf
                or self.__original_geom != self.geom
                or self.__original_designx != self.designx
                or self.__original_designy != self.designy
                or self.__original_rotation != self.rotation
            ):
                self.related_layers.all().delete()
                # self.extract_dxf()
                # flag drawing as refreshable
                if not self.needs_refresh:
                    self.needs_refresh = True
                    super(Drawing, self).save()


class Layer(models.Model):

    drawing = models.ForeignKey(
        Drawing,
        on_delete=models.CASCADE,
        related_name="related_layers",
        verbose_name=_("Drawing"),
    )
    name = models.CharField(
        _("Layer name"),
        max_length=50,
    )
    color_field = ColorField(default="#FFFFFF")
    linetype = models.BooleanField(
        _("Continuous linetype"),
        default=True,
    )
    is_block = models.BooleanField(
        default=False,
        editable=False,
    )

    class Meta:
        verbose_name = _("Layer")
        verbose_name_plural = _("Layers")
        ordering = ("name",)


class Entity(models.Model):

    layer = models.ForeignKey(
        Layer,
        on_delete=models.CASCADE,
        related_name="related_entities",
    )
    label = models.JSONField(
        null=True,
    )
    data = models.JSONField(
        null=True,
    )
    geom = GeometryCollectionField()
    insertion = PointField(
        null=True,
    )

    class Meta:
        verbose_name = _("Entity")
        verbose_name_plural = _("Entities")
