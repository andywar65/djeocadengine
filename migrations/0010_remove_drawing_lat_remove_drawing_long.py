# Generated by Django 5.0.6 on 2024-08-10 19:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("djeocadengine", "0009_alter_drawing_lat_alter_drawing_long"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="drawing",
            name="lat",
        ),
        migrations.RemoveField(
            model_name="drawing",
            name="long",
        ),
    ]