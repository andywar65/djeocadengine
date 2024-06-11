from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from users.models import User

pword = settings.DJANGO_SUPERUSER_PASSWORD


@override_settings(MEDIA_ROOT=Path(settings.MEDIA_ROOT).joinpath("temp"))
class UserViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        print("\nTest user views")
        User.objects.create_superuser("boss", "boss@example.com", pword)

    def tearDown(self):
        """Checks existing files, then removes them"""
        try:
            path = Path(settings.MEDIA_ROOT).joinpath("uploads/djeocad/dxf/")
            list = [e for e in path.iterdir() if e.is_file()]
            for file in list:
                Path(file).unlink()
        except FileNotFoundError:
            pass
