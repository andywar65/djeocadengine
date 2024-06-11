from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from users.models import User

from .models import Drawing

pword = settings.DJANGO_SUPERUSER_PASSWORD


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT).joinpath("temp"))
class UserViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        print("\nTest user views")
        User.objects.create_superuser("boss", "boss@example.com", pword)
        img_path = Path(settings.BASE_DIR).joinpath(
            "djeocadengine/static/djeocadengine/tests/nogeo.dxf"
        )
        with open(img_path, "rb") as f:
            content = f.read()
        Drawing.objects.create(
            title="Drawing 1",
            description="Drawing 1",
            dxf=SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf"),
            lat=42.0,
            long=12.0,
            geom={"type": "Point", "coordinates": [12.0, 42.0]},
            epsg=32633,
        )
        Drawing.objects.create(
            title="Drawing 2",
            description="Drawing 2",
            dxf=SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf"),
            lat=42.1,
            long=12.1,
            geom={"type": "Point", "coordinates": [12.1, 42.1]},
            epsg=32633,
        )
        f.close()

    def tearDown(self):
        """Checks existing files, then removes them"""
        try:
            path = Path(settings.MEDIA_ROOT).joinpath("uploads/djeocad/dxf/")
            list = [e for e in path.iterdir() if e.is_file()]
            for file in list:
                Path(file).unlink()
        except FileNotFoundError:
            pass
