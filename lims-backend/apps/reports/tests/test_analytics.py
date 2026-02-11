from datetime import datetime, timedelta
import zoneinfo

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.models import Payment
from apps.laboratory.models import Test, TestCategory
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.reports.analytics import AnalyticsService
from apps.reports.models import ReportExportLog

KARACHI_TZ = zoneinfo.ZoneInfo("Asia/Karachi")


class AnalyticsServiceTests(TestCase):
    def test_parse_date_range_custom_inclusive_exclusive(self):
        start, end, notes = AnalyticsService.parse_date_range(
            {"start_date": "2026-02-01", "end_date": "2026-02-03"}
        )
        self.assertEqual(start, datetime(2026, 2, 1, 0, 0, tzinfo=KARACHI_TZ))
        self.assertEqual(end, datetime(2026, 2, 4, 0, 0, tzinfo=KARACHI_TZ))
        self.assertEqual(notes, [])

    def test_parse_date_range_clamps_end_before_start(self):
        start, end, notes = AnalyticsService.parse_date_range(
            {"start_date": "2026-02-10", "end_date": "2026-02-08"}
        )
        self.assertEqual(start, datetime(2026, 2, 10, 0, 0, tzinfo=KARACHI_TZ))
        self.assertEqual(end, datetime(2026, 2, 11, 0, 0, tzinfo=KARACHI_TZ))
        self.assertTrue(any("end_date before start_date" in note for note in notes))


class AnalyticsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create(
            username="admin",
            email="admin@example.com",
            full_name="Admin",
            role="Admin",
        )
        self.manager = User.objects.create(
            username="manager",
            email="manager@example.com",
            full_name="Manager",
            role="Manager",
        )
        self.receptionist = User.objects.create(
            username="receptionist",
            email="recep@example.com",
            full_name="Receptionist",
            role="Receptionist",
        )

        self.patient = Patient.objects.create(
            first_name="John",
            last_name="Doe",
            gender="Male",
            phone="03001234567",
            age_years=30,
        )
        self.category = TestCategory.objects.create(name="Hematology")
        self.test = Test.objects.create(
            test_name="CBC",
            test_code="CBC01",
            category=self.category,
            sample_type="Blood",
            price=1000,
            turnaround_time=24,
        )

        self.range_day = "2026-02-11"
        self.range_start = datetime(2026, 2, 11, 0, 0, tzinfo=KARACHI_TZ)

        # Active order in range
        self.order_active = Order.objects.create(
            patient=self.patient,
            total_amount=1000,
            discount=100,
            net_amount=900,
            ordered_by=self.admin,
            referred_by="Dr A",
            status="NEW",
        )
        Order.objects.filter(pk=self.order_active.pk).update(
            created_at=self.range_start + timedelta(hours=1)
        )
        self.order_active.refresh_from_db()

        OrderItem.objects.create(order=self.order_active, test=self.test, price=900)

        Payment.objects.create(
            order=self.order_active,
            amount=500,
            payment_method="cash",
            recorded_by=self.admin,
        )
        payment = Payment.objects.filter(order=self.order_active).first()
        Payment.objects.filter(pk=payment.pk).update(
            payment_date=self.range_start + timedelta(hours=2)
        )

        # Cancelled order in range
        self.order_cancelled = Order.objects.create(
            patient=self.patient,
            total_amount=600,
            discount=0,
            net_amount=600,
            ordered_by=self.admin,
            referred_by="Dr B",
            status="NEW",
        )
        Order.objects.filter(pk=self.order_cancelled.pk).update(
            created_at=self.range_start + timedelta(hours=3)
        )
        self.order_cancelled.refresh_from_db()
        OrderItem.objects.create(order=self.order_cancelled, test=self.test, price=600)

        Payment.objects.create(
            order=self.order_cancelled,
            amount=600,
            payment_method="card",
            recorded_by=self.admin,
        )
        cancelled_payment = Payment.objects.filter(order=self.order_cancelled).first()
        Payment.objects.filter(pk=cancelled_payment.pk).update(
            payment_date=self.range_start + timedelta(hours=4)
        )
        Order.objects.filter(pk=self.order_cancelled.pk).update(status="CANCELLED")

    def test_overview_permission(self):
        url = reverse("analytics-overview")

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)

        self.client.force_authenticate(user=self.receptionist)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)

        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.client.force_authenticate(user=self.manager)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_overview_default_excludes_cancelled(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(
            reverse("analytics-overview"),
            {"start_date": self.range_day, "end_date": self.range_day},
        )
        self.assertEqual(resp.status_code, 200)

        data = resp.data
        self.assertEqual(set(data.keys()), {"meta", "summary", "series", "rows", "notes"})
        summary = data["summary"]
        self.assertEqual(summary["total_orders"], 1)
        self.assertEqual(summary["total_tests"], 1)
        self.assertEqual(summary["gross_sales"], 1000.0)
        self.assertEqual(summary["total_discount"], 100.0)
        self.assertEqual(summary["net_sales"], 900.0)
        self.assertEqual(summary["total_collections"], 500.0)
        self.assertEqual(summary["cash_collections"], 500.0)
        self.assertEqual(summary["outstanding_for_orders"], 400.0)
        self.assertEqual(summary["outstanding_period_net"], 400.0)

    def test_overview_include_cancelled_toggle_changes_totals(self):
        self.client.force_authenticate(user=self.admin)
        base_resp = self.client.get(
            reverse("analytics-overview"),
            {"start_date": self.range_day, "end_date": self.range_day},
        )
        with_cancelled_resp = self.client.get(
            reverse("analytics-overview"),
            {
                "start_date": self.range_day,
                "end_date": self.range_day,
                "include_cancelled": "true",
            },
        )

        self.assertEqual(base_resp.status_code, 200)
        self.assertEqual(with_cancelled_resp.status_code, 200)

        self.assertEqual(base_resp.data["summary"]["total_orders"], 1)
        self.assertEqual(with_cancelled_resp.data["summary"]["total_orders"], 2)
        self.assertEqual(base_resp.data["summary"]["total_collections"], 500.0)
        self.assertEqual(with_cancelled_resp.data["summary"]["total_collections"], 1100.0)

    def test_finance_collection_by_payment_date(self):
        self.client.force_authenticate(user=self.admin)

        # Move active payment out of selected range; booking still in range
        payment = Payment.objects.filter(order=self.order_active).first()
        Payment.objects.filter(pk=payment.pk).update(
            payment_date=self.range_start + timedelta(days=2)
        )

        resp = self.client.get(
            reverse("analytics-finance"),
            {"start_date": self.range_day, "end_date": self.range_day},
        )
        self.assertEqual(resp.status_code, 200)
        summary = resp.data["summary"]

        # Sales follow booking date and stay 900; collections follow payment date and become 0.
        self.assertEqual(summary["net_sales"], 900.0)
        self.assertEqual(summary["total_collected"], 0.0)

    def test_export_creates_log_and_export_logs_endpoint(self):
        self.client.force_authenticate(user=self.admin)

        export_resp = self.client.post(
            reverse("analytics-export"),
            {
                "report_key": "overview",
                "format": "csv",
                "filters": {
                    "start_date": self.range_day,
                    "end_date": self.range_day,
                    "include_cancelled": True,
                },
            },
            format="json",
        )
        self.assertEqual(export_resp.status_code, 200)
        self.assertEqual(ReportExportLog.objects.count(), 1)

        log = ReportExportLog.objects.first()
        self.assertTrue(log.filters_json["include_cancelled"])

        logs_resp = self.client.get(reverse("analytics-export-logs"))
        self.assertEqual(logs_resp.status_code, 200)
        self.assertEqual(logs_resp.data["summary"]["total_exports"], 1)
        self.assertEqual(logs_resp.data["rows"][0]["report_key"], "overview")
