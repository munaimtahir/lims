"""
Tests for result filters.
"""
from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.laboratory.models import Parameter, Test, TestCategory, TestParameter
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.results.filters import TestResultFilter
from apps.results.models import TestResult


@pytest.mark.django_db
class TestTestResultFilter:
    """Test TestResultFilter."""

    @pytest.fixture
    def patient(self):
        """Create test patient."""
        return Patient.objects.create(
            patient_id="PAT-001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
            phone="1234567890",
        )

    @pytest.fixture
    def test_parameter(self):
        """Create test parameter."""
        category = TestCategory.objects.create(name="Hematology")
        test = Test.objects.create(
            category=category,
            test_code="CBC",
            test_name="Complete Blood Count",
            sample_type="Blood",
            price=Decimal("50.00"),
            turnaround_time=24,
        )
        parameter = Parameter.objects.create(
            parameter_id="p1",
            parameter_name="WBC",
            unit="10*3/uL",
        )
        return TestParameter.objects.create(
            test=test,
            parameter=parameter,
        )

    @pytest.fixture
    def order(self, patient):
        """Create test order."""
        return Order.objects.create(
            order_id="ORD-001",
            patient=patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )

    @pytest.fixture
    def order_item(self, order, test_parameter):
        """Create test order item."""
        return OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

    @pytest.fixture
    def technician(self):
        """Create technician user."""
        return User.objects.create_user(
            username="tech",
            email="tech@test.com",
            password="testpass",
            full_name="Tech User",
            role="Lab Technician",
        )

    def test_filter_by_value_min(self, order, test_parameter, technician):
        """Test filtering by minimum value."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item3 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        # Create results with different values on different order items
        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
        )
        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="10.0",
            entered_by=technician,
        )
        result3 = TestResult.objects.create(
            order_item=order_item3,
            test_parameter=test_parameter,
            result_value="3.0",
            entered_by=technician,
        )

        # Filter by value_min = 5.0
        filter_set = TestResultFilter(
            {"value_min": 5.0}, queryset=TestResult.objects.all()
        )
        results = list(filter_set.qs)
        result_ids = [r.id for r in results]

        # Should include result1 (5.0) and result2 (10.0), but not result3 (3.0)
        assert result1.id in result_ids
        assert result2.id in result_ids
        assert result3.id not in result_ids

    def test_filter_by_value_max(self, order, test_parameter, technician):
        """Test filtering by maximum value."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item3 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        # Create results with different values on different order items
        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
        )
        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="10.0",
            entered_by=technician,
        )
        result3 = TestResult.objects.create(
            order_item=order_item3,
            test_parameter=test_parameter,
            result_value="3.0",
            entered_by=technician,
        )

        # Filter by value_max = 5.0
        filter_set = TestResultFilter(
            {"value_max": 5.0}, queryset=TestResult.objects.all()
        )
        results = filter_set.qs

        # Should include result1 (5.0) and result3 (3.0), but not result2 (10.0)
        result_ids = [r.id for r in results]
        assert result1.id in result_ids
        assert result3.id in result_ids
        assert result2.id not in result_ids

    def test_filter_by_value_range(self, order, test_parameter, technician):
        """Test filtering by value range (min and max)."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item3 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        # Create results with different values on different order items
        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
        )
        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="10.0",
            entered_by=technician,
        )
        result3 = TestResult.objects.create(
            order_item=order_item3,
            test_parameter=test_parameter,
            result_value="3.0",
            entered_by=technician,
        )

        # Filter by value_min = 4.0 and value_max = 6.0
        filter_set = TestResultFilter(
            {"value_min": 4.0, "value_max": 6.0}, queryset=TestResult.objects.all()
        )
        results = filter_set.qs

        # Should only include result1 (5.0)
        result_ids = [r.id for r in results]
        assert result1.id in result_ids
        assert result2.id not in result_ids
        assert result3.id not in result_ids

    def test_filter_by_entered_from(self, order, test_parameter, technician):
        """Test filtering by entered_from date."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        now = timezone.now()
        yesterday = now - timezone.timedelta(days=1)

        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
            entered_at=yesterday,
        )
        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="10.0",
            entered_by=technician,
            entered_at=now,
        )

        # Filter by entered_from = now
        filter_set = TestResultFilter(
            {"entered_from": now.isoformat()}, queryset=TestResult.objects.all()
        )
        results = filter_set.qs

        # Should include result2 but not result1
        result_ids = [r.id for r in results]
        assert result2.id in result_ids
        assert result1.id not in result_ids

    def test_filter_by_entered_to(self, order, test_parameter, technician):
        """Test filtering by entered_to date."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        now = timezone.now()
        yesterday = now - timezone.timedelta(days=1)

        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
            entered_at=yesterday,
        )
        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="10.0",
            entered_by=technician,
            entered_at=now,
        )

        # Filter by entered_to = yesterday
        filter_set = TestResultFilter(
            {"entered_to": yesterday.isoformat()}, queryset=TestResult.objects.all()
        )
        results = filter_set.qs

        # Should include result1 but not result2
        result_ids = [r.id for r in results]
        assert result1.id in result_ids
        assert result2.id not in result_ids

    def test_filter_by_flag(self, order, test_parameter, technician):
        """Test filtering by flag."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
        )
        # Update flag directly in DB to bypass validation
        TestResult.objects.filter(id=result1.id).update(flag="L")
        result1.refresh_from_db()

        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="20.0",
            entered_by=technician,
        )
        # Update flag directly in DB to bypass validation
        TestResult.objects.filter(id=result2.id).update(flag="H")
        result2.refresh_from_db()

        # Filter by flag = high
        filter_set = TestResultFilter({"flag": "H"}, queryset=TestResult.objects.all())
        results = filter_set.qs

        # Should only include result2
        result_ids = [r.id for r in results]
        assert result2.id in result_ids
        assert result1.id not in result_ids

    def test_filter_by_status(self, order, test_parameter, technician):
        """Test filtering by status."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="5.0",
            status="DRAFT",
            entered_by=technician,
        )
        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="10.0",
            status="VERIFIED",
            entered_by=technician,
        )

        # Filter by status = DRAFT
        filter_set = TestResultFilter(
            {"status": "DRAFT"}, queryset=TestResult.objects.all()
        )
        results = filter_set.qs

        # Should only include result1
        result_ids = [r.id for r in results]
        assert result1.id in result_ids
        assert result2.id not in result_ids

    def test_filter_by_order_item(self, order_item, test_parameter, technician):
        """Test filtering by order_item."""
        other_order = Order.objects.create(
            order_id="ORD-002",
            patient=order_item.order.patient,
            status="completed",
            total_amount=Decimal("100.00"),
            net_amount=Decimal("100.00"),
        )
        other_order_item = OrderItem.objects.create(
            order=other_order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        result1 = TestResult.objects.create(
            order_item=order_item,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
        )
        result2 = TestResult.objects.create(
            order_item=other_order_item,
            test_parameter=test_parameter,
            result_value="10.0",
            entered_by=technician,
        )

        # Filter by order_item
        filter_set = TestResultFilter(
            {"order_item": order_item.id}, queryset=TestResult.objects.all()
        )
        results = filter_set.qs

        # Should only include result1
        result_ids = [r.id for r in results]
        assert result1.id in result_ids
        assert result2.id not in result_ids

    def test_filter_handles_non_numeric_values(self, order, test_parameter, technician):
        """Test that filter handles non-numeric result values gracefully."""
        # Create multiple order items for the same order to avoid unique constraint
        order_item1 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )
        order_item2 = OrderItem.objects.create(
            order=order,
            test=test_parameter.test,
            price=Decimal("50.00"),
        )

        result1 = TestResult.objects.create(
            order_item=order_item1,
            test_parameter=test_parameter,
            result_value="POSITIVE",
            entered_by=technician,
        )
        result2 = TestResult.objects.create(
            order_item=order_item2,
            test_parameter=test_parameter,
            result_value="5.0",
            entered_by=technician,
        )

        # Filter by value_min = 4.0
        filter_set = TestResultFilter(
            {"value_min": 4.0}, queryset=TestResult.objects.all()
        )
        results = filter_set.qs

        # Should include result2 but not result1 (non-numeric)
        result_ids = [r.id for r in results]
        assert result2.id in result_ids
        assert result1.id not in result_ids
