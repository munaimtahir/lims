from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_systemsettings_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemsettings",
            name="report_header_image",
            field=models.ImageField(blank=True, help_text="Optional header image for reports and receipts", null=True, upload_to="settings/report_headers/"),
        ),
        migrations.AddField(
            model_name="systemsettings",
            name="report_footer_image",
            field=models.ImageField(blank=True, help_text="Optional footer image for reports and receipts", null=True, upload_to="settings/report_footers/"),
        ),
    ]
