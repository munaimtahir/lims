from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_order_priority_alter_order_status_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="referred_by",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
