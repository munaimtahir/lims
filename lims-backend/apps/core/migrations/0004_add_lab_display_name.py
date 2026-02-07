# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_systemsettings_report_images"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="lab_display_name",
            field=models.CharField(
                blank=True,
                help_text="Display name for UI header and login (defaults to lab_name if not set)",
                max_length=255,
                null=True,
            ),
        ),
    ]
