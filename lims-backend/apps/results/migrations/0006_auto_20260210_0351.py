from django.db import migrations

def assign_verify_permission(apps, schema_editor):
    # We use apps.get_model to access the historical models
    # However, ContentType and Permission interactions often require the real database state 
    # for the underlying tables (django_content_type, auth_permission).
    # Since we are adding data, we use the model managers available on the historical models.
    
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Group = apps.get_model('auth', 'Group')
    
    # 1. Get or Create ContentType for TestResult
    # Note: 'testresult' must be lower case for model lookups in ContentType
    try:
        content_type = ContentType.objects.get(app_label='results', model='testresult')
    except ContentType.DoesNotExist:
        # Fallback: Create if missing. 
        # Note: ContentType.objects.create might fail if schema is not ready, 
        # but at this stage (after 0001 initial) table exists.
        content_type = ContentType.objects.create(app_label='results', model='testresult')

    # 2. Get or Create Permission
    codename = 'can_verify_results'
    name = 'Can verify and finalize laboratory results'
    
    # Permissions are usually created by post_migrate signal. 
    # Since we defined it in the model Meta in the previous migration (0005),
    # it might not exist yet when this RunPython executes during the same `migrate` run.
    # So we manually ensure it exists.
    
    try:
        permission = Permission.objects.get(codename=codename, content_type=content_type)
    except Permission.DoesNotExist:
        permission = Permission.objects.create(
            codename=codename,
            content_type=content_type,
            name=name
        )

    # 3. Assign to Groups
    target_groups = ['Administrator', 'Manager', 'Pathologist']
    
    for group_name in target_groups:
        # Ensure group exists
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            group = Group.objects.create(name=group_name)
            
        group.permissions.add(permission)
        print(f"Assigned '{codename}' to group '{group_name}'")

def reverse_assign(apps, schema_editor):
    # We strictly do not remove permissions on reverse to avoid accidental data loss 
    # of manual assignments.
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('results', '0005_alter_testresult_options_alter_testresult_status'),
    ]

    operations = [
        migrations.RunPython(assign_verify_permission, reverse_assign),
    ]
