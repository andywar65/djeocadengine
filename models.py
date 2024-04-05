import json
from math import atan2, cos, degrees, radians, sin  # noqa
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
from ezdxf import colors
from ezdxf.addons import geo
from ezdxf.lldxf.const import InvalidGeoDataException
from ezdxf.math import Vec3
from filer.fields.image import FilerImageField
from pyproj import Transformer
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from shapely.geometry import Point, shape  # noqa


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
    layer_blacklist = [
        "Defpoints",
    ]
    name_blacklist = ["*Model_Space", "DynamicInputDot"]
    entity_types = [
        "POINT",
        "LINE",
        "LWPOLYLINE",
        "POLYLINE",
        "3DFACE",
        "CIRCLE",
        "ARC",
        "ELLIPSE",
        "SPLINE",
        "HATCH",
    ]

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
            "djeocadengine:drawing_detail",
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
            else:
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
                            geodata.dxf.north_direction[0],
                            geodata.dxf.north_direction[1],
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
        # with geom (insertion) we can extract DXF!
        if self.geom:
            if (
                self.__original_dxf != self.dxf
                or self.__original_geom != self.geom
                or self.__original_designx != self.designx
                or self.__original_designy != self.designy
                or self.__original_rotation != self.rotation
            ):
                self.related_layers.all().delete()
                extract_dxf(self)
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


"""
    Collection of utilities
"""


def cad2hex(color):
    if isinstance(color, tuple):
        return "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
    rgb24 = colors.DXF_DEFAULT_COLORS[color]
    return "#{:06X}".format(rgb24)


def get_geo_proxy(drawing, entity, matrix, transformer):
    geo_proxy = geo.proxy(entity)
    if geo_proxy.geotype == "Polygon":
        if not shape(geo_proxy).is_valid:
            return False
    geo_proxy.wcs_to_crs(matrix)
    geo_proxy.apply(lambda v: Vec3(transformer.transform(v.x, v.y)))
    return geo_proxy


def get_epsg_xml(drawing):
    xml = """<?xml version="1.0"
encoding="UTF-16" standalone="no" ?>
<Dictionary version="1.0" xmlns="http://www.osgeo.org/mapguide/coordinatesystem">
<Alias id="%(epsg)s" type="CoordinateSystem">
<ObjectId>EPSG=%(epsg)s</ObjectId>
<Namespace>EPSG Code</Namespace>
</Alias>
<Axis uom="METER">
<CoordinateSystemAxis>
<AxisOrder>1</AxisOrder>
<AxisName>Easting</AxisName>
<AxisAbbreviation>E</AxisAbbreviation>
<AxisDirection>east</AxisDirection>
</CoordinateSystemAxis>
<CoordinateSystemAxis>
<AxisOrder>2</AxisOrder>
<AxisName>Northing</AxisName>
<AxisAbbreviation>N</AxisAbbreviation>
<AxisDirection>north</AxisDirection>
</CoordinateSystemAxis>
</Axis>
</Dictionary>""" % {
        "epsg": drawing.epsg
    }
    return xml


def prepare_transformers(drawing):
    world2utm = Transformer.from_crs(4326, drawing.epsg, always_xy=True)
    utm2world = Transformer.from_crs(drawing.epsg, 4326, always_xy=True)
    utm_wcs = world2utm.transform(
        drawing.geom["coordinates"][0], drawing.geom["coordinates"][1]
    )
    rot = radians(drawing.rotation)
    return world2utm, utm2world, utm_wcs, rot


def fake_geodata(drawing, geodata, utm_wcs, rot):
    geodata.coordinate_system_definition = get_epsg_xml(drawing)
    geodata.dxf.design_point = (drawing.designx, drawing.designy, 0)
    geodata.dxf.reference_point = utm_wcs
    geodata.dxf.north_direction = (sin(rot), cos(rot))
    return geodata


def extract_dxf(drawing):
    # following conditional for test to work
    if isinstance(drawing.geom, str):
        drawing.geom = json.loads(drawing.geom)
    # prepare transformers
    world2utm, utm2world, utm_wcs, rot = prepare_transformers(drawing)
    # get DXF
    doc = ezdxf.readfile(Path(settings.MEDIA_ROOT).joinpath(str(drawing.dxf)))
    msp = doc.modelspace()
    geodata = msp.get_geodata()
    if not geodata:
        # faking geodata
        geodata = msp.new_geodata()
        geodata = fake_geodata(drawing, geodata, utm_wcs, rot)
    # get transform matrix from true or fake geodata
    m, epsg = geodata.get_crs_transformation(no_checks=True)  # noqa
    # create layers
    for layer in doc.layers:
        if layer.dxf.name in drawing.layer_blacklist:
            continue
        if layer.rgb:
            color = cad2hex(layer.rgb)
        else:
            color = cad2hex(layer.color)
        Layer.objects.create(
            drawing_id=drawing.id,
            name=layer.dxf.name,
            color_field=color,
        )
