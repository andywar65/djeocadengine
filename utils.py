from math import atan2, cos, degrees, radians, sin  # noqa

from ezdxf import colors
from ezdxf.addons import geo
from ezdxf.math import Vec3
from pyproj import Transformer
from shapely.geometry import Point, shape  # noqa

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
    geodata.coordinate_system_definition = drawing.get_epsg_xml()
    geodata.dxf.design_point = (drawing.designx, drawing.designy, 0)
    geodata.dxf.reference_point = utm_wcs
    geodata.dxf.north_direction = (sin(rot), cos(rot))
    return geodata
