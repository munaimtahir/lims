from datetime import datetime, time, timedelta
import zoneinfo
from django.db.models import Count, Sum, F, Q, Case, When, Value, CharField, FloatField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from apps.orders.models import Order, OrderItem
from apps.billing.models import Payment
from apps.patients.models import Patient

KARACHI_TZ = zoneinfo.ZoneInfo("Asia/Karachi")

class AnalyticsService:
    @staticmethod
    def parse_date_range(params):
        """
        Parse start_date and end_date from params.
        Default: Today.
        Timezone: Asia/Karachi.
        Returns: (start_dt, end_dt) where start_dt is inclusive, end_dt is exclusive (next day).
        """
        today = datetime.now(KARACHI_TZ).date()
        start_str = params.get("start_date")
        end_str = params.get("end_date")

        if start_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            except ValueError:
                start_date = today
        else:
            start_date = today

        if end_str:
            try:
                end_date_inclusive = datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                end_date_inclusive = start_date
        else:
            end_date_inclusive = start_date

        # Create timezone-aware datetimes
        # Start at 00:00:00 of start_date
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=KARACHI_TZ)
        
        # End at 00:00:00 of end_date + 1 day (exclusive upper bound)
        end_dt = datetime.combine(end_date_inclusive + timedelta(days=1), time.min).replace(tzinfo=KARACHI_TZ)

        return start_dt, end_dt

    @staticmethod
    def get_overview(params):
        start_dt, end_dt = AnalyticsService.parse_date_range(params)
        
        # Base querysets
        orders_qs = Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt)
        # Exclude cancelled if requested? Default exclude cancelled?
        # User requirement: "include_cancelled (default false)"
        include_cancelled = params.get("include_cancelled") == "true"
        
        if not include_cancelled:
            orders_qs = orders_qs.exclude(status="CANCELLED")
            
        items_qs = OrderItem.objects.filter(order__in=orders_qs)
        
        # Payments are based on payment_date
        payments_qs = Payment.objects.filter(payment_date__gte=start_dt, payment_date__lt=end_dt)
        if not include_cancelled:
             # Typically payments for cancelled orders might be refunded or remain. 
             # For "Collections", usually we count actual money received regardless of order status,
             # unless refunded. But let's filter by valid orders if that's the logic.
             # User said: "Collections total and cash collected (payment date)".
             # We generally trust the Payment record itself.
             pass

        # 1. Patients seen (distinct order.patient_id)
        patients_seen = orders_qs.values("patient").distinct().count()

        # 2. Orders/Visits
        total_orders = orders_qs.count()

        # 3. Tests billed (count order_lines)
        total_tests = items_qs.count()

        # 4. Gross sales, discounts, net sales (booking date)
        sales_agg = orders_qs.aggregate(
            gross=Sum("total_amount"),
            discount=Sum("discount"),
            net=Sum("net_amount")
        )
        
        gross_sales = sales_agg["gross"] or 0
        total_discount = sales_agg["discount"] or 0
        net_sales = sales_agg["net"] or 0

        # 5. Collections total and cash collected (payment date)
        collections_agg = payments_qs.aggregate(
            total=Sum("amount"),
            cash=Sum("amount", filter=Q(payment_method="cash"))
        )
        total_collections = collections_agg["total"] or 0
        cash_collections = collections_agg["cash"] or 0

        # 6. Outstanding
        # a) Outstanding for SELECTED orders (payments any date)
        #    This means sum(order.due_amount) for the orders in date range.
        outstanding_selected_orders = orders_qs.aggregate(
            due=Sum("due_amount")
        )["due"] or 0

        # b) Outstanding within selected dates (payments in date range)
        # This is ambiguous. "Outstanding within selected dates" might mean 
        # (Net Sales in Range) - (Collections in Range).
        # Let's compute that derived metric.
        outstanding_period_activity = net_sales - total_collections

        return {
            "meta": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "include_cancelled": include_cancelled
            },
            "summary": {
                "patients_seen": patients_seen,
                "total_orders": total_orders,
                "total_tests": total_tests,
                "gross_sales": float(gross_sales),
                "total_discount": float(total_discount),
                "net_sales": float(net_sales),
                "total_collections": float(total_collections),
                "cash_collections": float(cash_collections),
                "outstanding_for_orders": float(outstanding_selected_orders),
                "outstanding_period_net": float(outstanding_period_activity),
            }
        }

    @staticmethod
    def get_patients_report(params):
        start_dt, end_dt = AnalyticsService.parse_date_range(params)
        include_cancelled = params.get("include_cancelled") == "true"
        
        orders_qs = Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt)
        if not include_cancelled:
            orders_qs = orders_qs.exclude(status="CANCELLED")
            
        # Distinct patients in this period
        patient_ids = orders_qs.values_list("patient_id", flat=True).distinct()
        patients_qs = Patient.objects.filter(id__in=patient_ids)

        total_patients = patients_qs.count()
        
        # New patients: First order is within range
        # This is a bit heavy, we check min(created_at) for each patient?
        # Optimization: Patient.created_at (if exists) -> assume registration date approximates first order.
        # Or checking Order table.
        # Let's stick to aggregation if efficient.
        
        # We can list the patients with basic stats
        rows = []
        for p in patients_qs[:100]: # Limit for performance if needed, or paginate in view
            # Get order count in period
            p_orders = orders_qs.filter(patient=p)
            cnt = p_orders.count()
            revenue = p_orders.aggregate(s=Sum("net_amount"))["s"] or 0
            rows.append({
                "patient_id": p.id,
                "name": str(p),
                "age": p.age if hasattr(p, 'age') else "N/A",
                "gender": p.gender if hasattr(p, 'gender') else "N/A",
                "orders_count": cnt,
                "revenue": float(revenue)
            })
            
        # Sort by revenue or count? Let's sort by revenue desc
        rows.sort(key=lambda x: x["revenue"], reverse=True)

        return {
            "meta": {"count": total_patients},
            "summary": {"total_patients": total_patients},
            "rows": rows
        }

    @staticmethod
    def get_tests_report(params):
        start_dt, end_dt = AnalyticsService.parse_date_range(params)
        include_cancelled = params.get("include_cancelled") == "true"
        
        items_qs = OrderItem.objects.filter(
            order__created_at__gte=start_dt, 
            order__created_at__lt=end_dt
        )
        if not include_cancelled:
            items_qs = items_qs.exclude(order__status="CANCELLED")

        total_tests = items_qs.count()
        
        # Group by Test
        # We need test name.
        test_stats = items_qs.values("test__test_name").annotate(
            count=Count("id"),
            revenue=Sum("price")
        ).order_by("-count")

        rows = []
        for item in test_stats:
            name = item["test__test_name"] or "Unknown/Panel"
            # Attempt to get panel name if test is None?
            if item["test__test_name"] is None:
                # This aggregation misses items that are only panels. 
                # We need to handle that.
                pass 
                
            rows.append({
                "test_name": name,
                "count": item["count"],
                "revenue": float(item["revenue"] or 0),
                "share_percent": round((item["count"] / total_tests * 100), 1) if total_tests > 0 else 0
            })
            
        # Refined query for Panels vs Tests if needed, but OrderItem has test FK and Panel FK.
        # If grouped by test__test_name, panel items (test=None) fall into None.
        
        return {
            "meta": {"period": f"{start_dt.date()} to {end_dt.date()}"},
            "summary": {"total_tests_billed": total_tests},
            "rows": rows
        }

    @staticmethod
    def get_referrals_report(params):
        start_dt, end_dt = AnalyticsService.parse_date_range(params)
        include_cancelled = params.get("include_cancelled") == "true"
        
        orders_qs = Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt)
        if not include_cancelled:
            orders_qs = orders_qs.exclude(status="CANCELLED")

        # Group by referred_by
        # Empty referred_by -> "Walk-in/Self"
        
        ref_stats = orders_qs.annotate(
            referrer=Case(
                When(referred_by__isnull=True, then=Value("Walk-in/Self")),
                When(referred_by="", then=Value("Walk-in/Self")),
                default=F("referred_by"),
                output_field=CharField(),
            )
        ).values("referrer").annotate(
            count=Count("id"),
            revenue=Sum("net_amount")
        ).order_by("-revenue")

        rows = [
            {
                "referrer": item["referrer"],
                "count": item["count"],
                "revenue": float(item["revenue"] or 0)
            }
            for item in ref_stats
        ]

        return {
             "summary": {"total_referrers": len(rows)},
             "rows": rows
        }

    @staticmethod
    def get_finance_report(params):
        start_dt, end_dt = AnalyticsService.parse_date_range(params)
        include_cancelled = params.get("include_cancelled") == "true"
        
        # SALES (Booking Date)
        orders_qs = Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt)
        if not include_cancelled:
            orders_qs = orders_qs.exclude(status="CANCELLED")
            
        sales = orders_qs.aggregate(
            gross=Sum("total_amount"),
            discount=Sum("discount"),
            net=Sum("net_amount")
        )

        # COLLECTIONS (Payment Date)
        payments_qs = Payment.objects.filter(payment_date__gte=start_dt, payment_date__lt=end_dt)
        
        # By Method
        by_method = payments_qs.values("payment_method").annotate(
            total=Sum("amount")
        ).order_by("-total")
        
        method_rows = [
            {
                "method": item["payment_method"], 
                "amount": float(item["total"] or 0)
            }
            for item in by_method
        ]
        
        total_collected = sum(r["amount"] for r in method_rows)

        return {
            "summary": {
                "gross_sales": float(sales["gross"] or 0),
                "discount": float(sales["discount"] or 0),
                "net_sales": float(sales["net"] or 0),
                "total_collected": float(total_collected)
            },
            "collections_by_method": method_rows
        }
