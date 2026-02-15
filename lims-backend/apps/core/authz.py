"""Authorization helpers for tenant/branch-aware access control."""

from typing import Iterable, Optional

from django.db.models import QuerySet

from apps.core.models import Branch, get_default_tenant


def is_tenant_admin(user) -> bool:
    """Treat Admin role or superuser as tenant admin."""
    return getattr(user, "is_superuser", False) or getattr(user, "role", "") == "Admin"


def user_tenant(user):
    """Return user's tenant or the default tenant."""
    return getattr(user, "tenant", None) or get_default_tenant()


def user_active_branches(user) -> QuerySet:
    """Return queryset of branches the user can access (all for tenant admins)."""
    if is_tenant_admin(user):
        tenant = user_tenant(user)
        return Branch.objects.filter(tenant=tenant)
    return Branch.objects.filter(
        user_memberships__user=user, user_memberships__is_active=True, is_active=True
    )


def user_has_branch_access(user, branch: Optional[Branch]) -> bool:
    """Check if user may access the branch."""
    if branch is None:
        return True
    if is_tenant_admin(user):
        return True
    return (
        branch.is_active
        and branch.user_memberships.filter(user=user, is_active=True).exists()
    )


def filter_queryset_for_branches(qs: QuerySet, branch_field: str, user) -> QuerySet:
    """Filter queryset by user's allowed branches on given field."""
    if is_tenant_admin(user):
        return qs
    allowed = user_active_branches(user)
    # Include records with null branch (unassigned) so samples/orders without
    # branch config remain visible when lab has no branches configured
    from django.db.models import Q
    return qs.filter(
        Q(**{f"{branch_field}__in": allowed}) | Q(**{f"{branch_field}__isnull": True})
    )
