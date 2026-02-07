# Generated manually to fix parameter_id PK transition with data preservation

import django.db.models.deletion
from django.db import migrations, models


def validate_parameter_id_migration(value):
    pass


def copy_parameter_ids(apps, schema_editor):
    Parameter = apps.get_model("laboratory", "Parameter")
    ParameterQuickText = apps.get_model("laboratory", "ParameterQuickText")
    ParameterReferenceRange = apps.get_model("laboratory", "ParameterReferenceRange")
    TestParameterLink = apps.get_model("laboratory", "TestParameterLink")

    param_map = {p.id: p.parameter_id for p in Parameter.objects.all()}

    def update_model(model):
        for obj in model.objects.all():
            fk_id = obj.parameter_id
            if fk_id in param_map:
                obj.parameter_temp = param_map[fk_id]
                obj.save()

    update_model(ParameterQuickText)
    update_model(ParameterReferenceRange)
    update_model(TestParameterLink)


class Migration(migrations.Migration):
    dependencies = [
        (
            "laboratory",
            "0002_parameter_parameterquicktext_parameterreferencerange_and_more",
        ),
    ]

    operations = [
        # 1. Rename 'code' to 'parameter_id' in Parameter
        migrations.RenameField(
            model_name="parameter",
            old_name="code",
            new_name="parameter_id",
        ),
        # 2. Fix ordering and indexes immediately after rename so ORM works
        migrations.AlterModelOptions(
            name="parameter",
            options={
                "ordering": ["parameter_id"],
                "verbose_name": "Parameter",
                "verbose_name_plural": "Parameters",
                "indexes": [
                    models.Index(
                        fields=["parameter_id"], name="parameters_param_id_idx"
                    ),
                    models.Index(fields=["active"], name="parameters_active_idx"),
                ],
            },
        ),
        # 3. Add temp fields to children
        migrations.AddField(
            model_name="parameterquicktext",
            name="parameter_temp",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="parameterreferencerange",
            name="parameter_temp",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="testparameterlink",
            name="parameter_temp",
            field=models.CharField(max_length=100, null=True),
        ),
        # 4. Copy Data
        migrations.RunPython(copy_parameter_ids, migrations.RunPython.noop),
        # 5. Remove constraints/indexes from children
        migrations.AlterUniqueTogether(
            name="parameterquicktext", unique_together=set()
        ),
        migrations.AlterUniqueTogether(name="testparameterlink", unique_together=set()),
        # 6. Remove old FKs
        migrations.RemoveField(model_name="parameterquicktext", name="parameter"),
        migrations.RemoveField(model_name="parameterreferencerange", name="parameter"),
        migrations.RemoveField(model_name="testparameterlink", name="parameter"),
        # 7. Fix Parameter PK
        migrations.RemoveField(model_name="parameter", name="id"),
        migrations.AlterField(
            model_name="parameter",
            name="parameter_id",
            field=models.CharField(
                max_length=100,
                primary_key=True,
                serialize=False,
                validators=[],
                help_text="Parameter ID in format p<number> (e.g., p1, p2, p53)",
            ),
        ),
        # 8. Rename temp -> parameter and Restore FKs
        migrations.RenameField(
            model_name="parameterquicktext",
            old_name="parameter_temp",
            new_name="parameter",
        ),
        migrations.RenameField(
            model_name="parameterreferencerange",
            old_name="parameter_temp",
            new_name="parameter",
        ),
        migrations.RenameField(
            model_name="testparameterlink",
            old_name="parameter_temp",
            new_name="parameter",
        ),
        migrations.AlterField(
            model_name="parameterquicktext",
            name="parameter",
            field=models.ForeignKey(
                to="laboratory.parameter",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="quick_texts",
            ),
        ),
        migrations.AlterField(
            model_name="parameterreferencerange",
            name="parameter",
            field=models.ForeignKey(
                to="laboratory.parameter",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="legacy_reference_ranges",
            ),
        ),
        migrations.AlterField(
            model_name="testparameterlink",
            name="parameter",
            field=models.ForeignKey(
                to="laboratory.parameter",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="test_links",
            ),
        ),
        # 9. Restore Constraints
        migrations.AlterUniqueTogether(
            name="parameterquicktext",
            unique_together={("parameter", "template_title", "language")},
        ),
        migrations.AlterUniqueTogether(
            name="testparameterlink",
            unique_together={("test", "parameter")},
        ),
    ]
