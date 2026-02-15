"""
Central feature-flag gating for tenant-scoped modules (branches, collection centers, sample workflow).

When a feature is disabled, we return 404 (security by obscurity; "invisible" requirement).
"""

import logging
from functools import wraps

from rest_framework.exceptions import NotFound

from .authz import user_tenant
from .services.settings import get_tenant_settings


logger = logging.getLogger(__name__)

# Map API-facing flag names to TenantSettings attribute names
FLAG_ATTR = {
    "enable_branches": "enable_branches",
    "enable_collection_centers": "enable_collection_centers",
    "enable_sample_workflow": "sample_workflow_enabled",
}


class FeatureDisabled(NotFound):
    """Raised when a feature is disabled for the tenant. Renders as 404."""

    default_detail = "This feature is not available."
    default_code = "feature_disabled"


def is_enabled(request, flag_name: str) -> bool:
    """
    Return True if the given feature flag is enabled for the current request's tenant.

    Uses request.user to resolve tenant and TenantSettings.
    """
    attr = FLAG_ATTR.get(flag_name, flag_name)
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", True):
        return False
    tenant = user_tenant(user)
    settings_obj = get_tenant_settings(tenant)
    if settings_obj is None:
        return False
    return bool(getattr(settings_obj, attr, False))


def require_enabled(flag_name: str):
    """
    If the feature is disabled for the request's tenant, raise FeatureDisabled (404).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not is_enabled(request, flag_name):
                logger.info("Feature %s disabled for tenant; returning 404", flag_name)
                raise FeatureDisabled(detail="This feature is not available.")
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class FeatureFlagPermission:
    """
    DRF permission class: allow only if all of the given feature flags are enabled.
    When disabled, raises FeatureDisabled (404) so the API appears "invisible".
    """

    def __init__(self, *flag_names: str):
        self.flag_names = flag_names

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", True):
            return False
        for flag_name in self.flag_names:
            if not is_enabled(request, flag_name):
                logger.info("Feature %s disabled for tenant; returning 404", flag_name)
                raise FeatureDisabled(detail="This feature is not available.")
        return True

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
