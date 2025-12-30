"""Dashboard tests for analytics and performance metrics."""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import TestCatalog
from orders.models import Order
from patients.models import Patient
from results.models import Result, ResultStatus
from samples.models import Sample, SampleStatus
from users.models import User, UserRole


class DashboardAnalyticsTestCase(TestCase):
    """Test cases for dashboard analytics API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin", password="admin123", role=UserRole.ADMIN
        )

        # Create non-admin user
        self.regular_user = User.objects.create_user(
            username="user", password="user123", role=UserRole.RECEPTION
        )

        # Create test patient
        self.patient = Patient.objects.create(
            mrn="MRN-TEST-001",
            full_name="Test Patient",
            father_name="Father Name",
            dob="1990-01-01",
            sex="M",
            phone="03001234567",
            cnic="12345-1234567-1",
            address="Test Address",
        )

        # Create test catalog
        self.test_catalog = TestCatalog.objects.create(
            code="CBC",
            name="Complete Blood Count",
            category="Hematology",
            sample_type="Blood",
            price=1000.0,
            turnaround_time_hours=24,
        )

        self.url = reverse("dashboard-analytics")

    def test_dashboard_requires_authentication(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_accessible_by_non_admin(self):
        """Test that dashboard is accessible by non-admin authenticated users."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        # Dashboard is now accessible to all authenticated users
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_analytics_empty_state(self):
        """Test dashboard analytics with no data."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("quick_tiles", response.data)
        self.assertIn("orders_per_day", response.data)
        self.assertIn("sample_status", response.data)
        self.assertIn("result_status", response.data)
        self.assertIn("avg_tat_hours", response.data)

        # Check empty state
        self.assertEqual(response.data["quick_tiles"]["total_orders_today"], 0)
        self.assertEqual(response.data["quick_tiles"]["reports_published_today"], 0)
        self.assertEqual(response.data["sample_status"]["pending"], 0)
        self.assertEqual(response.data["avg_tat_hours"], 0)

    def test_dashboard_analytics_with_orders(self):
        """Test dashboard analytics with order data."""
        # Create orders
        Order.objects.create(patient=self.patient)
        Order.objects.create(patient=self.patient)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quick_tiles"]["total_orders_today"], 2)

    def test_dashboard_analytics_with_samples(self):
        """Test dashboard analytics with sample data."""
        order = Order.objects.create(patient=self.patient)
        order_item = order.items.create(test=self.test_catalog)

        # Create samples with different statuses
        Sample.objects.create(
            order_item=order_item, sample_type="Blood", status=SampleStatus.PENDING
        )
        Sample.objects.create(
            order_item=order_item, sample_type="Blood", status=SampleStatus.COLLECTED
        )
        Sample.objects.create(
            order_item=order_item, sample_type="Blood", status=SampleStatus.RECEIVED
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sample_status"]["pending"], 1)
        self.assertEqual(response.data["sample_status"]["collected"], 1)
        self.assertEqual(response.data["sample_status"]["received"], 1)

    def test_dashboard_analytics_with_results(self):
        """Test dashboard analytics with result data."""
        order = Order.objects.create(patient=self.patient)
        order_item = order.items.create(test=self.test_catalog)

        # Create results with different statuses
        Result.objects.create(
            order_item=order_item, value="10", status=ResultStatus.DRAFT
        )
        Result.objects.create(
            order_item=order_item, value="20", status=ResultStatus.ENTERED
        )
        Result.objects.create(
            order_item=order_item, value="30", status=ResultStatus.VERIFIED
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result_status"]["draft"], 1)
        self.assertEqual(response.data["result_status"]["entered"], 1)
        self.assertEqual(response.data["result_status"]["verified"], 1)

    def test_dashboard_analytics_with_published_results(self):
        """Test dashboard analytics with published results for TAT calculation."""
        order = Order.objects.create(patient=self.patient)
        order_item = order.items.create(test=self.test_catalog)

        # Create a published result with TAT
        now = timezone.now()
        Result.objects.create(
            order_item=order_item,
            value="15",
            status=ResultStatus.PUBLISHED,
            published_at=now,
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quick_tiles"]["reports_published_today"], 1)
        self.assertGreaterEqual(response.data["avg_tat_hours"], 0)

    def test_dashboard_analytics_date_range_filter(self):
        """Test dashboard analytics with date range filters."""
        # Create an order 5 days ago
        five_days_ago = timezone.now() - timedelta(days=5)
        order = Order.objects.create(patient=self.patient)
        order.created_at = five_days_ago
        order.save()

        self.client.force_authenticate(user=self.admin_user)

        # Get analytics for last 3 days (should not include the order)
        start_date = (timezone.now() - timedelta(days=3)).isoformat()
        end_date = timezone.now().isoformat()
        response = self.client.get(
            self.url, {"start_date": start_date, "end_date": end_date}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["orders_per_day"]), 4)  # 3 days + today

    def test_dashboard_analytics_invalid_date_format(self):
        """Test dashboard analytics with invalid date format."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {"start_date": "invalid-date"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_dashboard_analytics_invalid_date_range(self):
        """Test dashboard analytics with start_date after end_date."""
        self.client.force_authenticate(user=self.admin_user)
        start_date = timezone.now().isoformat()
        end_date = (timezone.now() - timedelta(days=1)).isoformat()
        response = self.client.get(
            self.url, {"start_date": start_date, "end_date": end_date}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_dashboard_orders_per_day_structure(self):
        """Test the structure of orders_per_day data."""
        # Create orders on different days
        Order.objects.create(patient=self.patient)
        Order.objects.create(patient=self.patient)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        orders_per_day = response.data["orders_per_day"]

        # Verify structure
        self.assertIsInstance(orders_per_day, list)
        if orders_per_day:
            self.assertIn("date", orders_per_day[0])
            self.assertIn("count", orders_per_day[0])

    def test_dashboard_tat_calculation_accuracy(self):
        """Test TAT calculation accuracy."""
        order = Order.objects.create(patient=self.patient)
        order_item = order.items.create(test=self.test_catalog)

        # Set order created time to 24 hours ago
        order.created_at = timezone.now() - timedelta(hours=24)
        order.save()

        # Create published result now
        Result.objects.create(
            order_item=order_item,
            value="10",
            status=ResultStatus.PUBLISHED,
            published_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TAT should be approximately 24 hours
        self.assertGreaterEqual(response.data["avg_tat_hours"], 23)
        self.assertLessEqual(response.data["avg_tat_hours"], 25)
