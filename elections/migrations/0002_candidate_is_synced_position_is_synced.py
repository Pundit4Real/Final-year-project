# Generated by Django 5.2.1 on 2025-07-06 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("elections", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidate",
            name="is_synced",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="position",
            name="is_synced",
            field=models.BooleanField(default=False),
        ),
    ]
