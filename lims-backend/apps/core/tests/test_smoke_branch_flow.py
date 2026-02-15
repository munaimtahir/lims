# API smoke test for Branch/Collection Center Phase-1 flow.
# Verifies: tenant settings OFF/ON, patient create (tenant set), order create (collection_branch),
# optional dispatch flow.

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User, UserBranchMembership
from apps.core.models import (
    Branch,
    BranchCapability,
    CollectionCenter,
    TenantSettings,
    get_default_tenant,
)
from apps.laboratory.models import Test, TestCategory
from apps.patients.models import Patient


class SmokeBranchFlowTests(TestCase):
    """Smoke test: patient -> order (with branch) -> sample collected; tenant settings OFF/ON."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = get_default_tenant()
        self.hq = Branch.objects.filter(tenant=self.tenant, code="00").first()
        if not self.hq:
            self.hq = Branch.objects.create(
                tenant=self.tenant,
                code="00",
                name="Head Office",
                capability_mode=BranchCapability.HQ_PROCESSING,
                is_hq=True,
                is_active=True,
            )
        CollectionCenter.objects.get_or_create(
            code="00", defaults={"name": "Head Office", "is_active": True}
        )
        self.tenant_settings, _ = TenantSettings.objects.get_or_create(
            tenant=self.tenant,
            defaults={
                "enable_collection_centers": False,
                "default_branch": self.hq,
                "default_collection_center": None,
            },
        )
        if not self.tenant_settings.default_branch_id:
            self.tenant_settings.default_branch = self.hq
            self.tenant_settings.save(update_fields=["default_branch", "updated_at"])
        self.user = User.objects.create_user(
            username="smoke_recep",
            email="smoke@lims.test",
            password="smoke123",
            full_name="Smoke Receptionist",
            role="Receptionist",
            tenant=self.tenant,
        )
        UserBranchMembership.objects.get_or_create(
            user=self.user, branch=self.hq, defaults={"role": "MEMBER", "is_active": True}
        )
        cat = TestCategory.objects.create(name="Smoke", description="Smoke")
        self.test = Test.objects.create(
            category=cat,
            test_code="SMK",
            test_name="Smoke Test",
            sample_type="Blood",
            price=100,
        )

    def test_patient_create_sets_tenant(self):
        """Create patient via API; assert tenant is set and patient appears in list."""
        self.client.force_authenticate(user=self.user)
        payload = {
            "first_name": "Smoke",
            "last_name": "Patient",
            "gender": "Male",
            "phone": "03001234567",
            "date_of_birth": "1990-01-01",
        }
        resp = self.client.post("/api/v1/patients/", payload, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        data = resp.json().get("data") or resp.json()
        patient_id = data.get("id")
        self.assertIsNotNone(patient_id)
        patient = Patient.objects.get(pk=patient_id)
        self.assertEqual(patient.tenant_id, self.tenant.id)
        list_resp = self.client.get("/api/v1/patients/")
        self.assertEqual(list_resp.status_code, 200)
        results = list_resp.json().get("results") or list_resp.json().get("data") or []
        ids = [p.get("id") for p in results if isinstance(p, dict)]
        self.assertIn(patient_id, ids)

    def test_order_create_has_collection_branch(self):
        """Create order without sending collection_branch; assert it is set from user."""
        self.client.force_authenticate(user=self.user)
        patient = Patient.objects.create(
            first_name="Ord",
            last_name="Patient",
            gender="Male",
            phone="03009876543",
            tenant=self.tenant,
        )
        payload = {
            "patient": patient.id,
            "test_ids": [self.test.id],
            "status": "NEW",
        }
        resp = self.client.post("/api/v1/orders/orders/", payload, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        from apps.orders.models import Order

        order = Order.objects.get(pk=resp.json().get("id"))
        self.assertIsNotNone(order.collection_branch_id)
        self.assertEqual(order.collection_branch_id, self.hq.id)

    def test_patient_create_ignores_invalid_center_when_flag_off(self):
        """Centers OFF: create patient with invalid registration_center (e.g. Branch id) -> ignored, OK."""
        self.client.force_authenticate(user=self.user)
        payload = {
            "first_name": "NoCenter",
            "last_name": "Patient",
            "gender": "Female",
            "phone": "03001112222",
            "date_of_birth": "1985-05-05",
            "registration_center": self.hq.id,  # Branch id sent as registration_center; backend ignores
        }
        resp = self.client.post("/api/v1/patients/", payload, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        data = resp.json().get("data") or resp.json()
        patient = Patient.objects.get(pk=data["id"])
        self.assertIsNone(patient.registration_center_id)

    def test_patient_create_requires_center_when_flag_on_no_default(self):
        """Centers ON, no default center: create patient without center -> 400."""
        self.tenant_settings.enable_collection_centers = True
        self.tenant_settings.default_collection_center = None
        self.tenant_settings.save(update_fields=["enable_collection_centers", "default_collection_center"])
        self.client.force_authenticate(user=self.user)
        payload = {
            "first_name": "NeedCenter",
            "last_name": "Patient",
            "gender": "Male",
            "phone": "03003334444",
            "date_of_birth": "1992-02-02",
        }
        resp = self.client.post("/api/v1/patients/", payload, format="json")
        self.assertEqual(resp.status_code, 400, resp.data)
        j = resp.json() or {}
        self.assertTrue(
            "registration_center" in j or "collection center" in str(j).lower(),
            msg=f"Expected registration_center error in {j}",
        )

    def test_order_create_defaults_collection_branch_from_user_or_default(self):
        """Order create without collection_branch uses user's branch or tenant default_branch."""
        self.client.force_authenticate(user=self.user)
        patient = Patient.objects.create(
            first_name="Def",
            last_name="Branch",
            gender="Male",
            phone="03005556666",
            tenant=self.tenant,
        )
        resp = self.client.post(
            "/api/v1/orders/orders/",
            {"patient": patient.id, "test_ids": [self.test.id], "status": "NEW"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.data)
        from apps.orders.models import Order

        order = Order.objects.get(pk=resp.json().get("id"))
        self.assertEqual(order.collection_branch_id, self.hq.id)

    def test_dispatch_flow_minimal(self):
        """Create dispatch from collected order -> send -> receive (main lab)."""
        from apps.orders.models import Dispatch, DispatchItem, Order
        from apps.samples.models import Sample, SampleStatus

        self.client.force_authenticate(user=self.user)
        patient = Patient.objects.create(
            first_name="Disp",
            last_name="Patient",
            gender="Male",
            phone="03007778888",
            tenant=self.tenant,
        )
        order_resp = self.client.post(
            "/api/v1/orders/orders/",
            {"patient": patient.id, "test_ids": [self.test.id], "status": "NEW"},
            format="json",
        )
        self.assertEqual(order_resp.status_code, 201)
        order_id = order_resp.json().get("id")
        order = Order.objects.get(pk=order_id)
        order.status = "COLLECTED"
        order.save()
        sample = Sample.objects.filter(order_item__order=order).first()
        if sample:
            sample.status = SampleStatus.COLLECTED
            sample.save(update_fields=["status"])
        create_resp = self.client.post(
            "/api/v1/orders/dispatches/",
            {"from_branch": self.hq.id, "to_branch": self.hq.id, "order_ids": [order_id]},
            format="json",
        )
        self.assertEqual(create_resp.status_code, 201, create_resp.data)
        dispatch_id = create_resp.json().get("id")
        send_resp = self.client.post(
            f"/api/v1/orders/dispatches/{dispatch_id}/send/",
            {},
            format="json",
        )
        self.assertEqual(send_resp.status_code, 200, send_resp.data)
        recv_resp = self.client.post(
            f"/api/v1/orders/dispatches/{dispatch_id}/receive/",
            {},
            format="json",
        )
        self.assertEqual(recv_resp.status_code, 200, recv_resp.data)
        dispatch = Dispatch.objects.get(pk=dispatch_id)
        self.assertEqual(dispatch.status, "RECEIVED")
