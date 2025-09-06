from django.db import migrations


def seed_environment_types(apps, schema_editor):
    EnvironmentType = apps.get_model("workspaces", "EnvironmentType")
    defaults = [
        {"name": "Development", "slug": "DEV", "display_order": 1},
        {"name": "Staging", "slug": "STAGING", "display_order": 2},
        {"name": "Production", "slug": "PROD", "display_order": 3},
    ]
    for d in defaults:
        EnvironmentType.objects.get_or_create(slug=d["slug"], defaults=d)


class Migration(migrations.Migration):

    dependencies = [
        ("workspaces", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_environment_types, migrations.RunPython.noop),
    ]

