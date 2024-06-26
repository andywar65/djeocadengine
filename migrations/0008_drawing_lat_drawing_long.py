# Generated by Django 5.0.6 on 2024-06-08 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("djeocadengine", "0007_remove_drawing_needs_refresh"),
    ]

    operations = [
        migrations.AddField(
            model_name="drawing",
            name="lat",
            field=models.FloatField(default=0, verbose_name="Latitude"),
        ),
        migrations.AddField(
            model_name="drawing",
            name="long",
            field=models.FloatField(default=0, verbose_name="Longitude"),
        ),
    ]
