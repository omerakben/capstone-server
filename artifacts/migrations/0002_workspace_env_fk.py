from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workspaces", "0002_environment_models"),
        ("artifacts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="artifact",
            name="workspace_env",
            field=models.ForeignKey(
                related_name="artifacts",
                to="workspaces.workspaceenvironment",
                on_delete=models.deletion.PROTECT,
                null=True,
                blank=True,
            ),
        ),
        migrations.AddIndex(
            model_name="artifact",
            index=models.Index(fields=["workspace_env"], name="artifact_wsenv_idx"),
        ),
    ]
