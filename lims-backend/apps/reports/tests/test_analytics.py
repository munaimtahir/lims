from datetime import datetime, timedelta
import zoneinfo
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.reports.analytics import AnalyticsService
from apps.orders.models import Order, OrderItem
from apps.billing.models import Payment
from apps.patients.models import Patient
from apps.laboratory.models import Test

KARACHI_TZ = zoneinfo.ZoneInfo("Asia/Karachi")

class AnalyticsServiceTests(TestCase):
    def test_parse_date_range_defaults(self):
        """Test default date range is today."""
        start, end = AnalyticsService.parse_date_range({})
        now = datetime.now(KARACHI_TZ)
        expected_start = datetime.combine(now.date(), datetime.min.time()).replace(tzinfo=KARACHI_TZ)
        expected_end = datetime.combine(now.date() + timedelta(days=1), datetime.min.time()).replace(tzinfo=KARACHI_TZ)
        
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

    def test_parse_date_range_custom(self):
        """Test custom date range parsing."""
        params = {"start_date": "2023-01-01", "end_date": "2023-01-05"}
        start, end = AnalyticsService.parse_date_range(params)
        
        expected_start = datetime(2023, 1, 1, 0, 0, 0, tzinfo=KARACHI_TZ)
        # End date is exclusive next day
        expected_end = datetime(2023, 1, 6, 0, 0, 0, tzinfo=KARACHI_TZ)
        
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)


class AnalyticsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(
            username="admin", 
            email="admin@example.com", 
            role="Admin", 
            is_admin=True
        )
        self.manager = User.objects.create(
            username="manager", 
            email="manager@example.com", 
            role="Manager", 
            is_manager=True
        )
        self.receptionist = User.objects.create(
            username="receptionist", 
            email="recep@example.com", 
            role="Receptionist", 
            is_receptionist=True
        )
        
        # Setup Data
        self.patient = Patient.objects.create(first_name="John", last_name="Doe", gender="M", mobile="03001234567")
        self.test = Test.objects.create(test_name="CBC", test_code="CBC01", price=1000)
        
        # Create an Order
        self.order = Order.objects.create(
            patient=self.patient,
            total_amount=1000,
            net_amount=1000,
            ordered_by=self.admin
        )
        OrderItem.objects.create(order=self.order, test=self.test, price=1000)
        
        # Create a Payment
        Payment.objects.create(order=self.order, amount=500, payment_method="cash", recorded_by=self.admin)

    def test_overview_permission(self):
        """Only Admin/Manager can access analytics."""
        url = reverse("analytics-overview")
        
        # Unauthenticated
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)
        
        # Receptionist (Forbidden)
        self.client.force_authenticate(user=self.receptionist)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)
        
        # Admin (Allowed)
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
        # Manager (Allowed)
        self.client.force_authenticate(user=self.manager)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_overview_data(self):
        """Test overview data correctness."""
        self.client.force_authenticate(user=self.admin)
        
        # Default ranges (Today)
        # Ensure created_at is today, or pass wide range
        today_str = datetime.now().strftime("%Y-%m-%d")
        url = reverse("analytics-overview") + f"?start_date={today_str}&end_date={today_str}"
        
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.data["summary"]
        
        self.assertEqual(data["total_orders"], 1)
        self.assertEqual(data["gross_sales"], 1000)
        self.assertEqual(data["net_sales"], 1000)
        self.assertEqual(data["total_collections"], 500)
        self.assertEqual(data["outstanding_for_orders"], 500) # 1000 - 500

