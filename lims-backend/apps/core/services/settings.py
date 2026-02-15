"""
Tenant-scoped settings helper.
"""

from apps.core.models import Tenant, TenantSettings


def get_tenant_settings(tenant):
    """
    Return TenantSettings for the given tenant, creating with safe defaults if missing.
    Default: enable_collection_centers=False; sample_workflow_enabled=True;
    default_branch/default_collection_center=None.
    """
    if tenant is None:
        return None
    settings, _ = TenantSettings.objects.get_or_create(
        tenant=tenant,
        defaults={
            "enable_branches": False,
            "enable_collection_centers": False,
            "sample_workflow_enabled": False,
            "default_branch_id": None,
            "default_collection_center_id": None,
        },
    )
    return settings


def require_sample_workflow_enabled(tenant):
    """
    Raise if sample workflow is disabled for this tenant.
    Use in sample collection/receiving endpoints to enforce tenant setting.
    Returns 404 (feature disabled) for consistency with branch/CC gating.

    Raises:
        apps.core.features.FeatureDisabled: When sample_workflow_enabled is False.
    """
    from apps.core.features import FeatureDisabled

    if tenant is None:
        return
    settings_obj = get_tenant_settings(tenant)
    if settings_obj is not None and not getattr(
        settings_obj, "sample_workflow_enabled", False
    ):
        raise FeatureDisabled(
            detail="This feature is not available."
        )
