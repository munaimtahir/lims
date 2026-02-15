"""Tests for authorization helpers."""

import pytest

from apps.accounts.models import User
from apps.core.authz import filter_queryset_for_branches
from apps.samples.models import Sample


@pytest.mark.django_db
def test_filter_queryset_for_branches_includes_null_branch():
    """
    Regression: Non-admin users must see records with null branch
    when lab has no branches configured (samples with collected_at_branch=null).
    """
    user = User.objects.create_user(
        username="receptionist",
        email="r@test.com",
        password="pass",
        full_name="Receptionist",
        role="Receptionist",
    )
    # User has no branch memberships; user_active_branches returns empty queryset
    from apps.core.authz import user_active_branches

    allowed = user_active_branches(user)
    assert allowed.count() == 0

    # Mock queryset with samples that have null collected_at_branch
    qs = Sample.objects.all()
    filtered = filter_queryset_for_branches(qs, "collected_at_branch", user)

    # Filter should include records where branch is null (Q(branch_field__isnull=True))
    assert "collected_at_branch__isnull" in str(filtered.query) or "isnull" in str(
        filtered.query
    )
