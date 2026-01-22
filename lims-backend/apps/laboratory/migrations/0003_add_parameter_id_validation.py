# Generated manually for parameter_id validation

from django.db import migrations, models


def validate_parameter_id_migration(value):
    """
    Validate parameter_id format: must match pattern p<number> (e.g., p1, p2, p53).
    Case-insensitive but stored as lowercase.
    """
    import re
    from django.core.exceptions import ValidationError
    
    if not value:
        raise ValidationError("parameter_id cannot be empty")
    
    # Normalize to lowercase for validation
    normalized = value.lower().strip()
    
    if not re.match(r'^p[0-9]+$', normalized):
        raise ValidationError(
            f"parameter_id must be in format 'p<number>' (e.g., p1, p2, p53). Got: {value}"
        )
    
    return normalized


def normalize_parameter_ids(apps, schema_editor):
    """Normalize existing parameter_ids to lowercase."""
    Parameter = apps.get_model("laboratory", "Parameter")
    for param in Parameter.objects.all():
        old_id = param.parameter_id
        new_id = old_id.lower().strip() if old_id else old_id
        if new_id != old_id:
            # Update the parameter
            param.parameter_id = new_id
            param.save(update_fields=['parameter_id'])


def reverse_normalize(apps, schema_editor):
    """Reverse migration - no action needed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("laboratory", "0002_parameter_parameterquicktext_parameterreferencerange_and_more"),
    ]

    operations = [
        # Rename 'code' field to 'parameter_id'
        migrations.RenameField(
            model_name='parameter',
            old_name='code',
            new_name='parameter_id',
        ),
        
        # Remove the old id field (BigAutoField) to make parameter_id the primary key
        migrations.RemoveField(
            model_name='parameter',
            name='id',
        ),
        
        # Alter the field to make it primary key with validator
        migrations.AlterField(
            model_name='parameter',
            name='parameter_id',
            field=models.CharField(
                max_length=100,
                primary_key=True,
                serialize=False,
                validators=[validate_parameter_id_migration],
                help_text='Parameter ID in format p<number> (e.g., p1, p2, p53)'
            ),
        ),
        
        # Update indexes and ordering
        migrations.AlterModelOptions(
            name='parameter',
            options={
                'ordering': ['parameter_id'],
                'verbose_name': 'Parameter',
                'verbose_name_plural': 'Parameters',
            },
        ),
        
        # Normalize existing parameter_ids to lowercase
        migrations.RunPython(normalize_parameter_ids, reverse_normalize),
    ]
