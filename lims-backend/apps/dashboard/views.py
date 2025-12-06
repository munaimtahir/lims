from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta
from apps.orders.models import Order
from apps.patients.models import Patient
from apps.samples.models import SampleCollection
from apps.results.models import TestResult
from apps.reports.models import Report
from apps.billing.models import Payment


class DashboardStatisticsView(APIView):
    """
    API endpoint for dashboard statistics.

    Provides various statistics for the dashboard including:
    - Today's orders, samples, results
    - Pending collections, results, verifications
    - Revenue statistics
    - Order status breakdown
    """

    def get(self, request):
        """
        Get dashboard statistics.

        Returns:
            Response: JSON object containing various statistics.
        """
        today = timezone.now().date()

        # Today's statistics
        today_orders = Order.objects.filter(created_at__date=today).count()
        today_samples = SampleCollection.objects.filter(
            collected_at__date=today
        ).count()
        today_results = TestResult.objects.filter(entered_at__date=today).count()
        today_reports = Report.objects.filter(generated_at__date=today).count()
        today_payments = Payment.objects.filter(payment_date__date=today)
        today_revenue = today_payments.aggregate(total=Sum("amount"))["total"] or 0

        # Pending work
        pending_collections = SampleCollection.objects.filter(status="pending").count()
        pending_results = TestResult.objects.filter(status="pending").count()
        pending_verifications = TestResult.objects.filter(status="pending").count()

        # Order status breakdown
        order_status_breakdown = (
            Order.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        # Recent orders (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_orders = Order.objects.filter(created_at__gte=week_ago).count()
        recent_revenue = (
            Payment.objects.filter(payment_date__gte=week_ago).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        # Total counts
        total_patients = Patient.objects.count()
        total_orders = Order.objects.count()
        total_samples = SampleCollection.objects.count()
        total_results = TestResult.objects.count()

        # Revenue statistics
        total_revenue = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
        unpaid_orders = (
            Order.objects.filter(is_paid=False).aggregate(total=Sum("net_amount"))[
                "total"
            ]
            or 0
        )

        # Role-specific statistics
        stats = {
            "today": {
                "orders": today_orders,
                "samples": today_samples,
                "results": today_results,
                "reports": today_reports,
                "revenue": float(today_revenue),
            },
            "pending": {
                "collections": pending_collections,
                "results": pending_results,
                "verifications": pending_verifications,
            },
            "totals": {
                "patients": total_patients,
                "orders": total_orders,
                "samples": total_samples,
                "results": total_results,
            },
            "revenue": {
                "today": float(today_revenue),
                "week": float(recent_revenue),
                "total": float(total_revenue),
                "unpaid": float(unpaid_orders),
            },
            "orders": {
                "status_breakdown": list(order_status_breakdown),
                "recent_week": recent_orders,
            },
        }

        # Add role-specific data
        if request.user.is_pathologist or request.user.is_admin:
            # Pathologist/Admin sees verification queue
            stats["pending"]["verification_queue"] = pending_verifications

        if request.user.is_phlebotomist:
            # Phlebotomist sees collection worklist
            stats["pending"]["collection_worklist"] = pending_collections

        if request.user.is_lab_technician:
            # Lab technician sees result entry worklist
            stats["pending"]["result_entry_worklist"] = pending_results

        if request.user.is_cashier or request.user.is_admin:
            # Cashier sees payment statistics
            stats["revenue"]["today"] = float(today_revenue)
            stats["revenue"]["unpaid"] = float(unpaid_orders)

        return Response(stats, status=status.HTTP_200_OK)
