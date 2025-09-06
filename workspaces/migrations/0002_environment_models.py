from django.db import migrations, models


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
        migrations.CreateModel(
            name="EnvironmentType",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=50, unique=True)),
                ("slug", models.SlugField(max_length=20, unique=True)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
            ],
            options={"ordering": ["display_order", "name"]},
        ),
        migrations.CreateModel(
            name="WorkspaceEnvironment",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "workspace",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="workspace_environments",
                        to="workspaces.workspace",
                    ),
                ),
                (
                    "environment_type",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="workspace_environments",
                        to="workspaces.environmenttype",
                    ),
                ),
            ],
            options={"ordering": ["workspace_id", "environment_type_id"]},
        ),
        migrations.AddIndex(
            model_name="workspaceenvironment",
            index=models.Index(
                fields=["workspace", "environment_type"],
                name="workenv_ws_env_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="workspaceenvironment",
            unique_together={("workspace", "environment_type")},
        ),
        migrations.RunPython(seed_environment_types, migrations.RunPython.noop),
    ]
