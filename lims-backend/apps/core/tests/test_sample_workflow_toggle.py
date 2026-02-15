"""
Tests for tenant-level sample workflow toggle (sample_workflow_enabled).
- When ON: sample endpoints allowed; result entry requires sample collected/received.
- When OFF: sample endpoints return 403; result worklist shows paid orders immediately.
- Multi-tenant isolation.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User, UserBranchMembership
from apps.core.models import (
    Branch,
    BranchCapability,
    Tenant,
    TenantSettings,
)
from apps.laboratory.models import Test, TestCategory
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient


class SampleWorkflowToggleTests(TestCase):
    """Tenant A: toggle ON. Tenant B: toggle OFF. Verify backend eligibility and isolation."""

    def setUp(self):
        self.client = APIClient()
        self.tenant_a = Tenant.objects.create(code="TWA", name="Lab A")
        self.tenant_b = Tenant.objects.create(code="TWB", name="Lab B")
        for tenant, code, name in [
            (self.tenant_a, "00", "HQ A"),
            (self.tenant_b, "00", "HQ B"),
        ]:
            Branch.objects.get_or_create(
                tenant=tenant,
                code=code,
                defaults={
                    "name": name,
                    "capability_mode": BranchCapability.HQ_PROCESSING,
                    "is_hq": True,
                    "is_active": True,
                },
            )

        # Tenant A: sample workflow ON (default)
        self.settings_a, _ = TenantSettings.objects.get_or_create(
            tenant=self.tenant_a,
            defaults={"enable_collection_centers": False, "sample_workflow_enabled": True},
        )
        self.settings_a.sample_workflow_enabled = True
        self.settings_a.save(update_fields=["sample_workflow_enabled", "updated_at"])

        # Tenant B: sample workflow OFF
        self.settings_b, _ = TenantSettings.objects.get_or_create(
            tenant=self.tenant_b,
            defaults={"enable_collection_centers": False, "sample_workflow_enabled": False},
        )
        self.settings_b.sample_workflow_enabled = False
        self.settings_b.save(update_fields=["sample_workflow_enabled", "updated_at"])

        self.user_a = User.objects.create_user(
            username="user_a",
            email="a@test.com",
            password="pass123",
            full_name="User A",
            role="Lab Technician",
            tenant=self.tenant_a,
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            email="b@test.com",
            password="pass123",
            full_name="User B",
            role="Lab Technician",
            tenant=self.tenant_b,
        )
        hq_a = Branch.objects.get(tenant=self.tenant_a, code="00")
        hq_b = Branch.objects.get(tenant=self.tenant_b, code="00")
        UserBranchMembership.objects.get_or_create(
            user=self.user_a, branch=hq_a, defaults={"role": "MEMBER", "is_active": True}
        )
        UserBranchMembership.objects.get_or_create(
            user=self.user_b, branch=hq_b, defaults={"role": "MEMBER", "is_active": True}
        )

        cat = TestCategory.objects.create(name="Cat", description="Cat")
        self.test = Test.objects.create(
            category=cat,
            test_code="T1",
            test_name="Test One",
            sample_type="Blood",
            price=Decimal("50"),
        )

    def test_tenant_b_sample_list_returns_403_when_workflow_disabled(self):
        """When sample_workflow_enabled=False, sample list returns 403."""
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get("/api/v1/samples/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("disabled", (resp.json() or {}).get("detail", "").lower())

    def test_tenant_a_sample_list_allowed_when_workflow_enabled(self):
        """When sample_workflow_enabled=True, sample list returns 200."""
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/v1/samples/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_tenant_b_result_worklist_includes_paid_order_when_workflow_disabled(self):
        """When sample_workflow_enabled=False, result worklist includes paid order without sample."""
        patient_b = Patient.objects.create(
            first_name="P",
            last_name="B",
            gender="Male",
            phone="03001111111",
            tenant=self.tenant_b,
        )
        order_b = Order.objects.create(
            patient=patient_b,
            tenant=self.tenant_b,
            collection_branch=Branch.objects.get(tenant=self.tenant_b, code="00"),
            processing_branch=Branch.objects.get(tenant=self.tenant_b, code="00"),
            status="NEW",
            is_paid=True,
            net_amount=Decimal("50"),
            paid_amount=Decimal("50"),
        )
        OrderItem.objects.create(order=order_b, test=self.test, price=Decimal("50"))

        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get("/api/v1/results/worklist/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        if not isinstance(results, list):
            results = []
        order_ids_in_worklist = [
            (item.get("order") or {}).get("order_id")
            for item in results
            if isinstance(item.get("order"), dict)
        ]
        self.assertIn(
            order_b.order_id,
            order_ids_in_worklist,
            msg="Paid order should appear in worklist when sample workflow disabled",
        )

    def test_tenant_settings_api_returns_sample_workflow_enabled(self):
        """GET tenant settings returns sample_workflow_enabled."""
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/v1/core/settings/tenant/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("sample_workflow_enabled", resp.json())
        self.assertTrue(resp.json()["sample_workflow_enabled"])

        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get("/api/v1/core/settings/tenant/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.json()["sample_workflow_enabled"])

    def test_multi_tenant_isolation_toggle_does_not_affect_other(self):
        """Toggling tenant B does not allow tenant A to see different behavior."""
        self.client.force_authenticate(user=self.user_a)
        r = self.client.get("/api/v1/samples/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user_b)
        r = self.client.get("/api/v1/samples/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_order_new_to_in_process_allowed_when_workflow_disabled(self):
        """When sample_workflow_enabled=False, order can transition NEW -> IN_PROCESS."""
        from apps.orders.services import transition_visit_state

        patient_b = Patient.objects.create(
            first_name="P",
            last_name="B",
            gender="Male",
            phone="03001111111",
            tenant=self.tenant_b,
        )
        order_b = Order.objects.create(
            patient=patient_b,
            tenant=self.tenant_b,
            collection_branch=Branch.objects.get(tenant=self.tenant_b, code="00"),
            processing_branch=Branch.objects.get(tenant=self.tenant_b, code="00"),
            status="NEW",
            is_paid=True,
        )
        transition_visit_state(order_b, "IN_PROCESS", self.user_b, source="test")
        order_b.refresh_from_db()
        self.assertEqual(order_b.status, "IN_PROCESS")
