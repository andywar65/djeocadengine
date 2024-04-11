# django-geocad-engine (djeocadengine)
Django app that imports CAD drawings in Leaflet maps
## Overview
Show CAD drawings in interactive web maps, download previously uploaded files with geo location, download CSV files with extracted data. This app is a stripped version of [djeocad](https://github.com/andywar65/djeocad) without some CRUD functionalities.
## Requirements
This app is tested on Django 5.0 and Python 3.12. It heavily relies on outstanding [ezdxf](https://ezdxf.mozman.at/) for handling DXF files, [pyproj](https://pyproj4.github.io/pyproj/stable/) for geographic projections, [django-leaflet](https://django-leaflet.readthedocs.io/en/latest/index.html/) as map engine, [django-geojson](https://django-geojson.readthedocs.io/en/latest/) for storing geodata, [shapely](https://shapely.readthedocs.io/en/stable/manual.html) for polygon verification, [django-filer](https://django-filer.readthedocs.io/en/latest/) for managing pictures, [django-colorfield](https://github.com/fabiocaccamo/django-colorfield) for admin color fields, [HTMX](https://htmx.org) and [hyperscript](https://hyperscript.org) to manage interactions. I use [Bootstrap 5](https://getbootstrap.com/) for styling.
## Installation
See `requirements.in` for required libraries. In your project root type `git clone https://github.com/andywar65/djeocadengine`, add `djeocad.apps.DjeocadengineConfig` to `INSTALLED_APPS` and `path(_('geocad/'), include('djeocadengine.urls', namespace = 'djeocadengine'))` to your project `urls.py`, migrate and collectstatic. You also need to add initial map defaults to `settings.py` (these are the settings for Rome, change them to your city of choice):
`LEAFLET_CONFIG = {
    "DEFAULT_CENTER": (41.8988, 12.5451),
    "DEFAULT_ZOOM": 10,
    "RESET_VIEW": False,
}`.
## View drawings
On the navigation bar look for `Documents/GeoCAD`. You will be presented with a `List of all drawings`, where drawings are just markers on the map. Click on a marker and follow the link in the popup: you will land on the `Drawing Detail` page, with layers displayed on the map. Layers may be switched on and off.
## Create drawings
To create a `Drawing` you will need a `DXF file` in ASCII format. `DXF` is a drawing exchange format widely used in `CAD` applications.
If `geodata` is embedded in the file, the drawing will be imported in the exact geographical location. If `geodata` is unavailable, you will have to insert it manually: to geolocate the drawing you need to define a point on the drawing of known Latitude / Longitude. Mark the point on the map and insert it's coordinates with respect to DXF `World Coordinate System origin (0,0,0)`. A good position for the `Reference / Design point` could be the cornerstone of a building, or another geographic landmark nearby the entities of your drawing.
Check also the rotation of the drawing with respect to the `True North`: it is typical to orient the drawings most conveniently for drafting purposes, unrespectful of True North. Please note that in CAD counterclockwise rotations are positive, so if you have to rotate the drawing clockwise to orient it correctly, you will have to enter a negative angle.
Alternatively, you can select a `Parent` drawing, that will lend geolocation to uploaded file. This can be useful when you want to upload different floors of a single building.
Try uploading files with few entities at the building scale, as the conversion may be unaccurate for small items (units must be in meters).
Press the `Save` button. If all goes well the `DXF file` will be extracted and a list of `Layers` will be attached to your drawing. Each layer inherits the `Name` and color originally assigned in CAD. `POINT`, `ARC`, `CIRCLE`, `ELLIPSE`, `SPLINE`, `3DFACE`, `HATCH`, `LINE` and `LWPOLYLINE` entities are visible on the map panel, where they inherit layer color. If unnested `BLOCKS` are present in the drawing, they will be extracted and inserted on respective layer.
## Downloading
In `Drawing Detail` view it is possible to download back the `DXF file`. `GeoData` will be associated to the `DXF`, so if you work on the file and upload it again, it will be automatically located on the map.
You can also download a `CSV` file that contains basic informations of some entities, notably `Polylines` and `Blocks`. Layer, area, surface, width and thickness are associated to `Polylines`, while block name, insertion point, scale, rotation and attribute key/values are associated to `Blocks`. If a `TEXT/MTEXT` is contained in a `Polyline` of the same layer, also the text content will be associated to the entity.
## Modify drawings
You can modify geolocation and appearance of drawings, but the `DXF` will not be affected. This behaviour is radically different from previous app [djeocad](https://github.com/andywar65/djeocad), where you had full CRUD functionality. If you want to modify the file, download it and use your favourite CAD application, then upload it back again.
## About Geodata
Geodata can be stored in DXF, but `ezdxf` library can't deal with all kind of coordinate reference systems (CRS). If Geodata is not found in the file (or if the CRS is not compatible) `django-geocad-engine` asks for user input: the location of a point both on the map and on the drawing coordinates system, and the rotation with respect to True North. The `pyproj` library hands over the best Universal Transverse Mercator CRS for the location (UTM is compatible with `ezdxf`). Thanks to UTM, Reference / Design Point and rotation input, Geodata can be built from scratch and incorporated into the file.
