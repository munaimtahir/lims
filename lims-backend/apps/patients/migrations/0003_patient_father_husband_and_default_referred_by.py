from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0002_patient_age_days_patient_age_months_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="father_husband_name",
            field=models.CharField(
                blank=True, help_text="Father/Husband name", max_length=255, null=True
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="default_referred_by",
            field=models.CharField(
                blank=True,
                help_text="Default referred by for future orders",
                max_length=255,
                null=True,
            ),
        ),
    ]
