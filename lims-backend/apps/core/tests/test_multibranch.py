from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import (
    Branch,
    BranchCapability,
    OrderIdSequence,
    Tenant,
    get_default_tenant,
)
from apps.core.numbering import generate_branch_order_id
from rest_framework.exceptions import ValidationError


class MultiBranchTests(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(code="TST", name="Test Lab")
        self.branch_hq = Branch.objects.create(
            tenant=self.tenant,
            code="00",
            name="HQ",
            capability_mode=BranchCapability.HQ_PROCESSING,
            is_hq=True,
        )
        self.branch_three = Branch.objects.create(
            tenant=self.tenant,
            code="03",
            name="Branch 03",
            capability_mode=BranchCapability.COLLECT_ONLY,
        )

    def test_branch_code_preserves_leading_zero(self):
        self.assertEqual(self.branch_three.code, "03")

    def test_branch_code_unique_per_tenant(self):
        with self.assertRaises(Exception):
            Branch.objects.create(
                tenant=self.tenant,
                code="03",
                name="Duplicate",
                capability_mode=BranchCapability.COLLECT_ONLY,
            )

    def test_order_id_generation_separate_per_branch(self):
        dt = timezone.now()
        id_hq = generate_branch_order_id(self.tenant, self.branch_hq, dt)
        id_b3 = generate_branch_order_id(self.tenant, self.branch_three, dt)
        self.assertNotEqual(id_hq, id_b3)
        self.assertTrue(id_b3.startswith("03-"))

    def test_order_sequence_increments(self):
        dt = timezone.now().date()
        first = OrderIdSequence.next_sequence(self.tenant, self.branch_three, dt)
        second = OrderIdSequence.next_sequence(self.tenant, self.branch_three, dt)
        self.assertEqual(first + 1, second)

    def test_collect_only_blocks_results(self):
        from apps.results.views import TestResultViewSet
        from apps.orders.models import Order, OrderItem
        from apps.patients.models import Patient
        from apps.laboratory.models import Test, TestCategory

        patient = Patient.objects.create(
            full_name="Test Patient",
            phone="03001234567",
            gender="Male",
            tenant=self.tenant,
        )
        order = Order.objects.create(
            patient=patient,
            tenant=self.tenant,
            collection_branch=self.branch_three,
            processing_branch=self.branch_three,
        )
        category = TestCategory.objects.create(name="Hematology", description="Hem")
        test = Test.objects.create(
            test_name="CBC",
            test_code="CBC001",
            price=100,
            sample_type="Blood",
            turnaround_time=1,
            category=category,
        )
        order_item = OrderItem.objects.create(order=order, test=test, price=100)

        viewset = TestResultViewSet()
        admin_user = User(role="Admin")
        with self.assertRaises(ValidationError):
            viewset._assert_branch_permissions(order_item, admin_user)
