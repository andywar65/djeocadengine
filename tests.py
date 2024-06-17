from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from users.models import User

from .models import Drawing

pword = settings.DJANGO_SUPERUSER_PASSWORD


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT).joinpath("tests"))
class GeoCADViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser("boss", "boss@example.com", pword)
        img_path = Path(settings.BASE_DIR).joinpath(
            "djeocadengine/static/djeocadengine/tests/nogeo.dxf"
        )
        with open(img_path, "rb") as f:
            content = f.read()
        Drawing.objects.create(
            title="Drawing 1",
            dxf=SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf"),
            geom={"type": "Point", "coordinates": [12.0, 42.0]},
            epsg=32633,
        )
        Drawing.objects.create(
            title="Drawing 2",
            dxf=SimpleUploadedFile("nogeo.dxf", content, "image/x-dxf"),
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

    def test_unlogged_list_status_code(self):
        response = self.client.get(reverse("djeocadengine:base_list"))
        self.assertEqual(response.status_code, 200)

    def test_unlogged_detail_status_code(self):
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_detail", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_unlogged_htmx_list_status_code(self):
        response = self.client.get(
            reverse("djeocadengine:base_list"),
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 200)

    def test_unlogged_htmx_detail_status_code(self):
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_detail", kwargs={"pk": draw.id}),
            headers={"Hx-Request": "true"},
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
        self.assertEqual(response.status_code, 302)

    def test_unlogged_htmx_create_status_code(self):
        response = self.client.get(
            reverse("djeocadengine:drawing_create"), headers={"Hx-Request": "true"}
        )
        self.assertEqual(response.status_code, 302)

    def test_unlogged_htmx_update_status_code(self):
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_update", kwargs={"pk": draw.id}),
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 302)

    def test_logged_delete_status_code(self):
        self.client.login(username="boss", password=pword)
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_delete", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 404)

    def test_logged_htmx_create_status_code(self):
        self.client.login(username="boss", password=pword)
        response = self.client.get(
            reverse("djeocadengine:drawing_create"), headers={"Hx-Request": "true"}
        )
        self.assertEqual(response.status_code, 200)

    def test_logged_htmx_update_status_code(self):
        self.client.login(username="boss", password=pword)
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_update", kwargs={"pk": draw.id}),
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 200)

    def test_logged_htmx_delete_status_code(self):
        self.client.login(username="boss", password=pword)
        draw = Drawing.objects.first()
        response = self.client.get(
            reverse("djeocadengine:drawing_delete", kwargs={"pk": draw.id}),
            headers={"Hx-Request": "true"},
        )
        self.assertEqual(response.status_code, 200)

    def test_create_drawing_from_georeferenced(self):
        dxf_path = Path(settings.BASE_DIR).joinpath(
            "djeocadengine/static/djeocadengine/tests/yesgeo.dxf"
        )
        with open(dxf_path, "rb") as f:
            dxf_content = f.read()
        self.client.login(username="boss", password=pword)
        # add this call to make next one work. why?
        self.client.get(reverse("djeocadengine:drawing_create"))
        response = self.client.post(
            reverse("djeocadengine:drawing_create"),
            {
                "title": "Georeferenced",
                "dxf": SimpleUploadedFile("yesgeo.dxf", dxf_content, "text/dxf"),
            },
            headers={"HX-Request": "true"},
            follow=True,
        )
        draw = Drawing.objects.get(title="Georeferenced")
        self.assertRedirects(
            response,
            reverse("djeocadengine:drawing_detail", kwargs={"pk": draw.id}),
            status_code=302,
            target_status_code=200,
        )
        response = self.client.get(
            reverse("djeocadengine:drawing_download", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("djeocadengine:drawing_csv", kwargs={"pk": draw.id})
        )
        self.assertEqual(response.status_code, 200)
        dxf_path = Path(settings.BASE_DIR).joinpath(
            "djeocadengine/static/djeocadengine/tests/nogeo.dxf"
        )
        with open(dxf_path, "rb") as f:
            dxf_content = f.read()
        response = self.client.post(
            reverse("djeocadengine:drawing_create"),
            {
                "title": "Not Georeferenced",
                "dxf": SimpleUploadedFile("nogeo.dxf", dxf_content, "text/dxf"),
            },
            headers={"HX-Request": "true"},
            follow=True,
        )
        draw2 = Drawing.objects.get(title="Not Georeferenced")
        self.assertRedirects(
            response,
            reverse("djeocadengine:drawing_geodata", kwargs={"pk": draw2.id}),
            status_code=302,
            target_status_code=200,
        )
        response = self.client.post(
            reverse("djeocadengine:drawing_geodata", kwargs={"pk": draw2.id}),
            {
                "parent": draw.id,
            },
            headers={"HX-Request": "true"},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("djeocadengine:drawing_detail", kwargs={"pk": draw2.id}),
            status_code=302,
            target_status_code=200,
        )

    def test_create_drawing_from_not_georeferenced(self):
        dxf_path = Path(settings.BASE_DIR).joinpath(
            "djeocadengine/static/djeocadengine/tests/nogeo.dxf"
        )
        with open(dxf_path, "rb") as f:
            dxf_content = f.read()
        self.client.login(username="boss", password=pword)
        response = self.client.post(
            reverse("djeocadengine:drawing_create"),
            {
                "title": "Again not Georeferenced",
                "dxf": SimpleUploadedFile("nogeo.dxf", dxf_content, "text/dxf"),
            },
            headers={"HX-Request": "true"},
            follow=True,
        )
        draw = Drawing.objects.get(title="Again not Georeferenced")
        self.assertRedirects(
            response,
            reverse("djeocadengine:drawing_geodata", kwargs={"pk": draw.id}),
            status_code=302,
            target_status_code=200,
        )
        response = self.client.post(
            reverse("djeocadengine:drawing_manual", kwargs={"pk": draw.id}),
            {
                "lat": 42,
                "long": 12,
                "designx": 0,
                "designy": 0,
                "rotation": 0,
            },
            headers={"HX-Request": "true"},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("djeocadengine:drawing_detail", kwargs={"pk": draw.id}),
            status_code=302,
            target_status_code=200,
        )
        response = self.client.post(
            reverse("djeocadengine:drawing_update", kwargs={"pk": draw.id}),
            {
                "lat": 42,
                "long": 11,
                "designx": 0,
                "designy": 0,
                "rotation": 0,
                "title": "Again not Georeferenced",
                "dxf": "uploads/djeocad/dxf/nogeo.dxf",
            },
            headers={"HX-Request": "true"},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("djeocadengine:drawing_detail", kwargs={"pk": draw.id}),
            status_code=302,
            target_status_code=200,
        )
