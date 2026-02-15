"""
Smoke tests: when feature flags are OFF, gated endpoints return 404 and core workflow works.
When flags are ON, gated endpoints are accessible.
"""

from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core.models import Tenant, TenantSettings
from apps.laboratory.models import Test, TestCategory
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient


class FeatureFlagsSmokeTests(TestCase):
    """With enable_branches=False, enable_collection_centers=False, sample_workflow_enabled=False."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = Tenant.objects.create(code="LAB", name="Test Lab")
        self.settings, _ = TenantSettings.objects.get_or_create(
            tenant=self.tenant,
            defaults={
                "enable_branches": False,
                "enable_collection_centers": False,
                "sample_workflow_enabled": False,
            },
        )
        self.settings.enable_branches = False
        self.settings.enable_collection_centers = False
        self.settings.sample_workflow_enabled = False
        self.settings.save(update_fields=["enable_branches", "enable_collection_centers", "sample_workflow_enabled"])

        self.user = User.objects.create_user(
            username="smoke_user",
            email="smoke@test.com",
            password="pass123",
            full_name="Smoke User",
            role="Admin",
            tenant=self.tenant,
        )
        cat = TestCategory.objects.create(name="Cat", description="Cat")
        self.test = Test.objects.create(
            category=cat,
            test_code="T1",
            test_name="Test One",
            sample_type="Blood",
            price=Decimal("50"),
        )

    def test_branches_returns_404_when_disabled(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/v1/core/branches/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_collection_centers_returns_404_when_disabled(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/v1/core/collection-centers/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_dispatches_returns_404_when_branches_disabled(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/v1/orders/dispatches/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_samples_returns_404_when_sample_workflow_disabled(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/v1/samples/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_create_works_without_registration_center(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.post(
            "/api/v1/patients/",
            data={
                "full_name": "Smoke Patient",
                "phone": "0300-1234567",
                "gender": "Male",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", r.data)
        self.assertIn("mrn", r.data)

    def test_order_create_works_without_collection_branch(self):
        self.client.force_authenticate(user=self.user)
        patient = Patient.objects.create(
            tenant=self.tenant,
            full_name="Order Patient",
            phone="0300-9999999",
            gender="Male",
            created_by=self.user,
        )
        patient.generate_mrn()
        patient.save()
        r = self.client.post(
            "/api/v1/orders/",
            data={
                "patient": patient.id,
                "test_ids": [self.test.id],
                "panel_ids": [],
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertIn("order_id", r.data)
        order = Order.objects.get(id=r.data["id"])
        self.assertIsNone(order.collection_branch_id)

    def test_results_worklist_returns_200_when_sample_workflow_disabled(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/v1/results/worklist/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_settings_features_returns_flags(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/v1/core/settings/features/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("enable_branches", r.data)
        self.assertIn("enable_collection_centers", r.data)
        self.assertIn("enable_sample_workflow", r.data)
        self.assertFalse(r.data["enable_branches"])
        self.assertFalse(r.data["enable_sample_workflow"])
