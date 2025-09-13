from django.db import migrations


def seed_environment_types(apps, schema_editor):
    EnvironmentType = apps.get_model("workspaces", "EnvironmentType")
    defaults = [
        ("DEV", "Development", 0),
        ("STAGING", "Staging", 1),
        ("PROD", "Production", 2),
    ]
    for slug, name, order in defaults:
        EnvironmentType.objects.get_or_create(
            slug=slug, defaults={"name": name, "display_order": order}
        )


def unseed_environment_types(apps, schema_editor):
    # Leave data in place intentionally (idempotent, safe to keep)
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("workspaces", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_environment_types, unseed_environment_types),
    ]
