# Generated for Phase A: disable branch/CC by default

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0010_tenantsettings_sample_workflow_updated_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenantsettings",
            name="enable_branches",
            field=models.BooleanField(
                default=False,
                help_text="When True, branch and dispatch APIs and UI are enabled. When False, branches are hidden and orders do not require a branch.",
            ),
        ),
    ]
