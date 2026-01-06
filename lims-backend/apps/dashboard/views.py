from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate, TruncDay
from datetime import timedelta, datetime
from decimal import Decimal
from apps.orders.models import Order, OrderItem
from apps.patients.models import Patient
from apps.samples.models import Sample, SampleStatus
from apps.results.models import TestResult
from apps.reports.models import Report
from apps.billing.models import Payment
from apps.laboratory.models import Test, TestPanel
from apps.core.export_utils import export_to_csv, export_to_excel


class DashboardStatisticsViewSet(ViewSet):
    """
    API endpoint for dashboard statistics.

    Provides various statistics for the dashboard including:
    - Today's orders, samples, results
    - Pending collections, results, verifications
    - Revenue statistics
    - Order status breakdown
    """

    def list(self, request):
        """
        Get dashboard statistics.

        Returns:
            Response: JSON object containing various statistics.
        """
        today = timezone.now().date()

        # Today's statistics
        today_orders = Order.objects.filter(created_at__date=today).count()
        today_samples = Sample.objects.filter(
            collected_at__date=today
        ).count()
        today_results = TestResult.objects.filter(entered_at__date=today).count()
        today_reports = Report.objects.filter(generated_at__date=today).count()
        today_payments = Payment.objects.filter(payment_date__date=today)
        today_revenue = today_payments.aggregate(total=Sum("amount"))["total"] or 0

        # Pending work
        pending_collections = Sample.objects.filter(status=SampleStatus.PENDING).count()
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
        total_samples = Sample.objects.count()
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
    
    @action(detail=False, methods=["get"])
    def revenue_report(self, request):
        """
        Get revenue report by date range.
        
        Query params:
            - date_from: Start date (YYYY-MM-DD)
            - date_to: End date (YYYY-MM-DD)
            - group_by: 'day', 'week', or 'month' (default: 'day')
        
        Returns:
            Response: Revenue statistics grouped by period.
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        group_by = request.query_params.get("group_by", "day")
        
        payments = Payment.objects.all()
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                payments = payments.filter(payment_date__gte=date_from_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                payments = payments.filter(payment_date__lte=date_to_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Group by period
        if group_by == "day":
            payments = payments.annotate(period=TruncDate("payment_date"))
        elif group_by == "week":
            payments = payments.annotate(period=TruncDay("payment_date"))
        else:  # month
            payments = payments.extra(
                select={"period": "DATE_TRUNC('month', payment_date)"}
            )
        
        revenue_data = (
            payments.values("period")
            .annotate(
                total_revenue=Sum("amount"),
                payment_count=Count("id"),
            )
            .order_by("period")
        )
        
        total_revenue = payments.aggregate(total=Sum("amount"))["total"] or 0
        total_payments = payments.count()
        
        return Response(
            {
                "success": True,
                "data": {
                    "period": group_by,
                    "revenue_by_period": list(revenue_data),
                    "summary": {
                        "total_revenue": float(total_revenue),
                        "total_payments": total_payments,
                        "average_payment": float(total_revenue / total_payments) if total_payments > 0 else 0,
                    },
                },
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["get"])
    def test_statistics(self, request):
        """
        Get test statistics (most/least ordered tests).
        
        Query params:
            - date_from: Start date (YYYY-MM-DD)
            - date_to: End date (YYYY-MM-DD)
            - limit: Number of top tests to return (default: 10)
        
        Returns:
            Response: Test ordering statistics.
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        limit = int(request.query_params.get("limit", 10))
        
        order_items = OrderItem.objects.all()
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                order_items = order_items.filter(order__created_at__gte=date_from_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                order_items = order_items.filter(order__created_at__lte=date_to_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Test statistics
        test_stats = (
            order_items.filter(test__isnull=False)
            .values("test__test_code", "test__test_name")
            .annotate(
                order_count=Count("id"),
                total_revenue=Sum("price"),
            )
            .order_by("-order_count")[:limit]
        )
        
        # Panel statistics
        panel_stats = (
            order_items.filter(panel__isnull=False)
            .values("panel__panel_code", "panel__panel_name")
            .annotate(
                order_count=Count("id"),
                total_revenue=Sum("price"),
            )
            .order_by("-order_count")[:limit]
        )
        
        return Response(
            {
                "success": True,
                "data": {
                    "most_ordered_tests": list(test_stats),
                    "most_ordered_panels": list(panel_stats),
                },
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["get"])
    def turnaround_time(self, request):
        """
        Get turnaround time analysis.
        
        Query params:
            - date_from: Start date (YYYY-MM-DD)
            - date_to: End date (YYYY-MM-DD)
        
        Returns:
            Response: Turnaround time statistics.
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        
        orders = Order.objects.filter(status__in=["VERIFIED", "PUBLISHED"])
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                orders = orders.filter(created_at__gte=date_from_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                orders = orders.filter(created_at__lte=date_to_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        # Calculate TAT for each order (from creation to verification/publishing)
        tat_data = []
        for order in orders.select_related("patient"):
            # Get first result verification time or report generation time
            first_result = TestResult.objects.filter(
                order_item__order=order,
                verified_at__isnull=False
            ).order_by("verified_at").first()
            
            if first_result and first_result.verified_at:
                tat_hours = (first_result.verified_at - order.created_at).total_seconds() / 3600
                tat_data.append({
                    "order_id": order.order_id,
                    "created_at": order.created_at.isoformat(),
                    "completed_at": first_result.verified_at.isoformat(),
                    "tat_hours": round(tat_hours, 2),
                })
        
        if tat_data:
            avg_tat = sum(item["tat_hours"] for item in tat_data) / len(tat_data)
            min_tat = min(item["tat_hours"] for item in tat_data)
            max_tat = max(item["tat_hours"] for item in tat_data)
        else:
            avg_tat = min_tat = max_tat = 0
        
        return Response(
            {
                "success": True,
                "data": {
                    "average_tat_hours": round(avg_tat, 2),
                    "min_tat_hours": round(min_tat, 2),
                    "max_tat_hours": round(max_tat, 2),
                    "total_orders": len(tat_data),
                    "tat_distribution": tat_data[:50],  # Limit to 50 for response size
                },
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["get"])
    def workload_distribution(self, request):
        """
        Get workload distribution by user role.
        
        Query params:
            - date_from: Start date (YYYY-MM-DD)
            - date_to: End date (YYYY-MM-DD)
        
        Returns:
            Response: Workload statistics by role.
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        
        workload = {}
        
        # Orders created by receptionists
        orders_qs = Order.objects.all()
        if date_from:
            orders_qs = orders_qs.filter(created_at__gte=date_from)
        if date_to:
            orders_qs = orders_qs.filter(created_at__lte=date_to)
        
        workload["receptionists"] = (
            orders_qs.filter(ordered_by__role="Receptionist")
            .values("ordered_by__full_name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        # Samples collected by phlebotomists
        samples_qs = Sample.objects.filter(collected_by__isnull=False)
        if date_from:
            samples_qs = samples_qs.filter(collected_at__gte=date_from)
        if date_to:
            samples_qs = samples_qs.filter(collected_at__lte=date_to)
        
        workload["phlebotomists"] = (
            samples_qs.values("collected_by__full_name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        # Results entered by lab technicians
        results_qs = TestResult.objects.filter(entered_by__isnull=False)
        if date_from:
            results_qs = results_qs.filter(entered_at__gte=date_from)
        if date_to:
            results_qs = results_qs.filter(entered_at__lte=date_to)
        
        workload["lab_technicians"] = (
            results_qs.values("entered_by__full_name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        # Results verified by pathologists
        verified_qs = TestResult.objects.filter(verified_by__isnull=False)
        if date_from:
            verified_qs = verified_qs.filter(verified_at__gte=date_from)
        if date_to:
            verified_qs = verified_qs.filter(verified_at__lte=date_to)
        
        workload["pathologists"] = (
            verified_qs.values("verified_by__full_name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        
        return Response(
            {
                "success": True,
                "data": {
                    "receptionists": list(workload["receptionists"]),
                    "phlebotomists": list(workload["phlebotomists"]),
                    "lab_technicians": list(workload["lab_technicians"]),
                    "pathologists": list(workload["pathologists"]),
                },
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["get"])
    def payment_methods(self, request):
        """
        Get payment method breakdown.
        
        Query params:
            - date_from: Start date (YYYY-MM-DD)
            - date_to: End date (YYYY-MM-DD)
        
        Returns:
            Response: Payment method statistics.
        """
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        
        payments = Payment.objects.all()
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                payments = payments.filter(payment_date__gte=date_from_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_from format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                payments = payments.filter(payment_date__lte=date_to_obj)
            except ValueError:
                return Response(
                    {"error": "Invalid date_to format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        payment_methods = (
            payments.values("payment_method")
            .annotate(
                count=Count("id"),
                total_amount=Sum("amount"),
            )
            .order_by("-total_amount")
        )
        
        total_amount = payments.aggregate(total=Sum("amount"))["total"] or 0
        
        return Response(
            {
                "success": True,
                "data": {
                    "payment_methods": list(payment_methods),
                    "total_amount": float(total_amount),
                },
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=["get"])
    def export_analytics(self, request):
        """
        Export analytics data to PDF or Excel.
        
        Query params:
            - report_type: 'revenue', 'tests', 'tat', 'workload', 'payments'
            - format: 'csv' or 'excel' (default: 'excel')
            - date_from: Start date (YYYY-MM-DD)
            - date_to: End date (YYYY-MM-DD)
        
        Returns:
            Response: CSV or Excel file download
        """
        report_type = request.query_params.get("report_type", "revenue")
        format_type = request.query_params.get("format", "excel").lower()
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        
        filename = f"analytics_{report_type}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        if report_type == "revenue":
            # Get revenue data
            payments = Payment.objects.all()
            if date_from:
                payments = payments.filter(payment_date__gte=date_from)
            if date_to:
                payments = payments.filter(payment_date__lte=date_to)
            
            data = []
            headers = ["Date", "Payment ID", "Order ID", "Amount", "Method", "Patient"]
            for payment in payments.select_related("order", "order__patient")[:1000]:
                data.append([
                    payment.payment_date.strftime("%Y-%m-%d"),
                    payment.id,
                    payment.order.order_id,
                    str(payment.amount),
                    payment.get_payment_method_display(),
                    payment.order.patient.get_full_name(),
                ])
            
            if format_type == "excel":
                return export_to_excel(data, f"{filename}.xlsx", headers, "Revenue Report")
            else:
                return export_to_csv(data, f"{filename}.csv", headers)
        
        elif report_type == "tests":
            # Get test statistics
            order_items = OrderItem.objects.filter(test__isnull=False)
            if date_from:
                order_items = order_items.filter(order__created_at__gte=date_from)
            if date_to:
                order_items = order_items.filter(order__created_at__lte=date_to)
            
            test_stats = (
                order_items.values("test__test_code", "test__test_name")
                .annotate(count=Count("id"), revenue=Sum("price"))
                .order_by("-count")[:100]
            )
            
            data = []
            headers = ["Test Code", "Test Name", "Order Count", "Total Revenue"]
            for stat in test_stats:
                data.append([
                    stat["test__test_code"],
                    stat["test__test_name"],
                    stat["count"],
                    str(stat["revenue"] or 0),
                ])
            
            if format_type == "excel":
                return export_to_excel(data, f"{filename}.xlsx", headers, "Test Statistics")
            else:
                return export_to_csv(data, f"{filename}.csv", headers)
        
        else:
            return Response(
                {"error": f"Unsupported report type: {report_type}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
