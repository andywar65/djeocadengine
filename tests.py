from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from users.models import User

from .models import Drawing

pword = settings.DJANGO_SUPERUSER_PASSWORD


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT).joinpath("temp"))
class GeoCADViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser("boss", "boss@example.com", pword)
        img_path = Path(settings.BASE_DIR).joinpath(
            "djeocadengine/static/djeocadengine/tests/nogeo.dxf"
        )
        with open(img_path, "rb") as f:
            content = f.read()
        draw1 = Drawing(
            title="Drawing 1",
            dxf=SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf"),
            lat=42.0,
            long=12.0,
        )
        draw1.save()
        draw2 = Drawing(
            title="Drawing 2",
            dxf=SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf"),
            lat=42.1,
            long=12.1,
        )
        draw2.save()
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

    def test_unlogged_list_status_code(self):
        response = self.client.get(reverse("djeocadengine:base_list"))
        self.assertEqual(response.status_code, 200)

    def test_unlogged_detail_status_code(self):
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_detail", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_unlogged_create_status_code(self):
        response = self.client.get(reverse("djeocadengine:drawing_create"))
        self.assertEqual(response.status_code, 404)

    def test_unlogged_update_status_code(self):
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_update", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 404)

    def test_unlogged_delete_status_code(self):
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_delete", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 404)
