from datetime import datetime, time, timedelta
import zoneinfo

from django.db.models import Case, CharField, Count, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce

from apps.billing.models import Payment
from apps.orders.models import Order, OrderItem

KARACHI_TZ = zoneinfo.ZoneInfo("Asia/Karachi")


class AnalyticsService:
    """Operational and finance analytics helpers for reports v1."""

    @staticmethod
    def _parse_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _as_params_dict(params):
        if hasattr(params, "dict"):
            return params.dict()
        return dict(params or {})

    @staticmethod
    def _parse_age_group(value):
        if not value:
            return (None, None)
        token = str(value).strip().lower()
        presets = {
            "child": (0, 12),
            "teen": (13, 17),
            "adult": (18, 59),
            "senior": (60, None),
        }
        if token in presets:
            return presets[token]

        if "-" in token:
            left, right = token.split("-", 1)
            try:
                return (int(left), int(right))
            except ValueError:
                return (None, None)

        if token.endswith("+"):
            try:
                return (int(token[:-1]), None)
            except ValueError:
                return (None, None)

        return (None, None)

    @staticmethod
    def parse_date_range(params):
        """
        Parse start_date/end_date (YYYY-MM-DD) in Asia/Karachi.
        Returns inclusive/exclusive bounds: start <= ts < end.
        """
        params = AnalyticsService._as_params_dict(params)
        notes = []
        today = datetime.now(KARACHI_TZ).date()

        start_str = params.get("start_date")
        end_str = params.get("end_date")

        start_date = today
        if start_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            except ValueError:
                notes.append("Invalid start_date; defaulted to today in Asia/Karachi.")

        end_date_inclusive = start_date
        if end_str:
            try:
                end_date_inclusive = datetime.strptime(end_str, "%Y-%m-%d").date()
            except ValueError:
                notes.append("Invalid end_date; defaulted to start_date.")

        if end_date_inclusive < start_date:
            end_date_inclusive = start_date
            notes.append("end_date before start_date; clamped to start_date.")

        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=KARACHI_TZ)
        end_dt = datetime.combine(end_date_inclusive + timedelta(days=1), time.min).replace(tzinfo=KARACHI_TZ)
        return start_dt, end_dt, notes

    @staticmethod
    def parse_filters(params):
        params = AnalyticsService._as_params_dict(params)
        notes = []

        include_cancelled = AnalyticsService._parse_bool(
            params.get("include_cancelled"), default=False
        )
        referrer_id = params.get("referrer_id") or None
        payment_method = params.get("payment_method") or None
        gender = params.get("gender") or None
        age_group = params.get("age_group") or None
        age_min, age_max = AnalyticsService._parse_age_group(age_group)

        if age_group and age_min is None and age_max is None:
            notes.append("Unsupported age_group value; ignored.")

        return {
            "include_cancelled": include_cancelled,
            "referrer_id": referrer_id,
            "payment_method": payment_method,
            "gender": gender,
            "age_group": age_group,
            "age_min": age_min,
            "age_max": age_max,
            "notes": notes,
        }

    @staticmethod
    def _apply_order_filters(orders_qs, filters):
        if not filters["include_cancelled"]:
            orders_qs = orders_qs.exclude(status="CANCELLED")
        if filters["referrer_id"]:
            orders_qs = orders_qs.filter(referred_by=filters["referrer_id"])
        if filters["gender"]:
            orders_qs = orders_qs.filter(patient__gender__iexact=filters["gender"])
        if filters["age_min"] is not None:
            orders_qs = orders_qs.filter(patient__age_years__gte=filters["age_min"])
        if filters["age_max"] is not None:
            orders_qs = orders_qs.filter(patient__age_years__lte=filters["age_max"])
        return orders_qs

    @staticmethod
    def _apply_payment_filters(payments_qs, filters):
        if not filters["include_cancelled"]:
            payments_qs = payments_qs.exclude(order__status="CANCELLED")
        if filters["payment_method"]:
            payments_qs = payments_qs.filter(payment_method=filters["payment_method"])
        if filters["referrer_id"]:
            payments_qs = payments_qs.filter(order__referred_by=filters["referrer_id"])
        if filters["gender"]:
            payments_qs = payments_qs.filter(order__patient__gender__iexact=filters["gender"])
        if filters["age_min"] is not None:
            payments_qs = payments_qs.filter(order__patient__age_years__gte=filters["age_min"])
        if filters["age_max"] is not None:
            payments_qs = payments_qs.filter(order__patient__age_years__lte=filters["age_max"])
        return payments_qs

    @staticmethod
    def _base_meta(start_dt, end_dt, filters):
        return {
            "timezone": "Asia/Karachi",
            "range": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "rule": "start <= ts < end",
            },
            "filters": {
                "include_cancelled": filters["include_cancelled"],
                "referrer_id": filters["referrer_id"],
                "payment_method": filters["payment_method"],
                "gender": filters["gender"],
                "age_group": filters["age_group"],
            },
        }

    @staticmethod
    def get_overview(params):
        start_dt, end_dt, date_notes = AnalyticsService.parse_date_range(params)
        filters = AnalyticsService.parse_filters(params)

        orders_qs = AnalyticsService._apply_order_filters(
            Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt), filters
        )
        items_qs = OrderItem.objects.filter(order__in=orders_qs)
        payments_qs = AnalyticsService._apply_payment_filters(
            Payment.objects.filter(payment_date__gte=start_dt, payment_date__lt=end_dt),
            filters,
        )

        sales_agg = orders_qs.aggregate(
            gross=Sum("total_amount"),
            discount=Sum("discount"),
            net=Sum("net_amount"),
            outstanding_for_orders=Sum("due_amount"),
        )
        collections_agg = payments_qs.aggregate(
            total=Sum("amount"),
            cash=Sum("amount", filter=Q(payment_method="cash")),
        )

        net_sales = float(sales_agg["net"] or 0)
        total_collections = float(collections_agg["total"] or 0)

        top_tests = (
            items_qs.annotate(
                metric_name=Coalesce(
                    "test__test_name", "panel__panel_name", Value("Unknown")
                )
            )
            .values("metric_name")
            .annotate(count=Count("id"), revenue=Sum("price"))
            .order_by("-count", "metric_name")[:10]
        )
        top_referrals = (
            orders_qs.annotate(
                metric_name=Case(
                    When(referred_by__isnull=True, then=Value("Walk-in/Self")),
                    When(referred_by="", then=Value("Walk-in/Self")),
                    default=F("referred_by"),
                    output_field=CharField(),
                )
            )
            .values("metric_name")
            .annotate(count=Count("id"), revenue=Sum("net_amount"))
            .order_by("-count", "metric_name")[:10]
        )

        return {
            "meta": AnalyticsService._base_meta(start_dt, end_dt, filters),
            "summary": {
                "patients_seen": orders_qs.values("patient_id").distinct().count(),
                "total_orders": orders_qs.count(),
                "total_tests": items_qs.count(),
                "gross_sales": float(sales_agg["gross"] or 0),
                "total_discount": float(sales_agg["discount"] or 0),
                "net_sales": net_sales,
                "total_collections": total_collections,
                "cash_collections": float(collections_agg["cash"] or 0),
                "outstanding_for_orders": float(sales_agg["outstanding_for_orders"] or 0),
                "outstanding_period_net": net_sales - total_collections,
            },
            "series": [],
            "rows": {
                "most_ordered_tests": [
                    {
                        "test_name": item["metric_name"],
                        "count": item["count"],
                        "revenue": float(item["revenue"] or 0),
                    }
                    for item in top_tests
                ],
                "most_referring_sources": [
                    {
                        "referrer": item["metric_name"],
                        "count": item["count"],
                        "revenue": float(item["revenue"] or 0),
                    }
                    for item in top_referrals
                ],
            },
            "notes": date_notes + filters["notes"],
        }

    @staticmethod
    def get_patients_report(params):
        start_dt, end_dt, date_notes = AnalyticsService.parse_date_range(params)
        filters = AnalyticsService.parse_filters(params)

        orders_qs = AnalyticsService._apply_order_filters(
            Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt), filters
        )

        patient_stats = (
            orders_qs.values(
                "patient_id",
                "patient__first_name",
                "patient__last_name",
                "patient__full_name",
                "patient__gender",
                "patient__age_years",
            )
            .annotate(orders_count=Count("id"), revenue=Sum("net_amount"))
            .order_by("-revenue", "patient_id")
        )

        rows = []
        for item in patient_stats:
            full_name = (item.get("patient__full_name") or "").strip()
            if not full_name:
                full_name = (
                    f"{item.get('patient__first_name', '')} {item.get('patient__last_name', '')}"
                ).strip()
            rows.append(
                {
                    "patient_id": item["patient_id"],
                    "name": full_name,
                    "age": item.get("patient__age_years"),
                    "gender": item.get("patient__gender") or "",
                    "orders_count": item["orders_count"],
                    "revenue": float(item["revenue"] or 0),
                }
            )

        return {
            "meta": AnalyticsService._base_meta(start_dt, end_dt, filters),
            "summary": {"total_patients": len(rows)},
            "series": [],
            "rows": rows,
            "notes": date_notes + filters["notes"],
        }

    @staticmethod
    def get_tests_report(params):
        start_dt, end_dt, date_notes = AnalyticsService.parse_date_range(params)
        filters = AnalyticsService.parse_filters(params)

        items_qs = OrderItem.objects.filter(
            order__created_at__gte=start_dt,
            order__created_at__lt=end_dt,
        )
        if not filters["include_cancelled"]:
            items_qs = items_qs.exclude(order__status="CANCELLED")
        if filters["referrer_id"]:
            items_qs = items_qs.filter(order__referred_by=filters["referrer_id"])
        if filters["gender"]:
            items_qs = items_qs.filter(order__patient__gender__iexact=filters["gender"])
        if filters["age_min"] is not None:
            items_qs = items_qs.filter(order__patient__age_years__gte=filters["age_min"])
        if filters["age_max"] is not None:
            items_qs = items_qs.filter(order__patient__age_years__lte=filters["age_max"])

        stats_qs = (
            items_qs.annotate(
                metric_name=Coalesce(
                    "test__test_name", "panel__panel_name", Value("Unknown")
                )
            )
            .values("metric_name")
            .annotate(count=Count("id"), revenue=Sum("price"))
            .order_by("-count", "metric_name")
        )

        total_tests = items_qs.count()
        rows = [
            {
                "test_name": item["metric_name"],
                "count": item["count"],
                "revenue": float(item["revenue"] or 0),
                "share_percent": round((item["count"] / total_tests * 100), 1)
                if total_tests
                else 0,
            }
            for item in stats_qs
        ]

        return {
            "meta": AnalyticsService._base_meta(start_dt, end_dt, filters),
            "summary": {"total_tests_billed": total_tests},
            "series": [],
            "rows": rows,
            "notes": date_notes + filters["notes"],
        }

    @staticmethod
    def get_referrals_report(params):
        start_dt, end_dt, date_notes = AnalyticsService.parse_date_range(params)
        filters = AnalyticsService.parse_filters(params)

        orders_qs = AnalyticsService._apply_order_filters(
            Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt), filters
        )

        ref_stats = (
            orders_qs.annotate(
                referrer=Case(
                    When(referred_by__isnull=True, then=Value("Walk-in/Self")),
                    When(referred_by="", then=Value("Walk-in/Self")),
                    default=F("referred_by"),
                    output_field=CharField(),
                )
            )
            .values("referrer")
            .annotate(count=Count("id"), revenue=Sum("net_amount"))
        )

        volume_rows = sorted(
            [
                {
                    "referrer": item["referrer"],
                    "count": item["count"],
                    "revenue": float(item["revenue"] or 0),
                }
                for item in ref_stats
            ],
            key=lambda x: (-x["count"], x["referrer"]),
        )
        revenue_rows = sorted(
            volume_rows,
            key=lambda x: (-x["revenue"], x["referrer"]),
        )

        return {
            "meta": AnalyticsService._base_meta(start_dt, end_dt, filters),
            "summary": {
                "total_referrers": len(volume_rows),
                "total_referred_orders": sum(row["count"] for row in volume_rows),
            },
            "series": [],
            "rows": {
                "volume": volume_rows,
                "revenue": revenue_rows,
            },
            "notes": date_notes + filters["notes"],
        }

    @staticmethod
    def get_finance_report(params):
        start_dt, end_dt, date_notes = AnalyticsService.parse_date_range(params)
        filters = AnalyticsService.parse_filters(params)

        orders_qs = AnalyticsService._apply_order_filters(
            Order.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt), filters
        )
        payments_qs = AnalyticsService._apply_payment_filters(
            Payment.objects.filter(payment_date__gte=start_dt, payment_date__lt=end_dt),
            filters,
        )

        sales = orders_qs.aggregate(
            gross=Sum("total_amount"),
            discount=Sum("discount"),
            net=Sum("net_amount"),
            outstanding_for_orders=Sum("due_amount"),
        )
        collections = payments_qs.aggregate(
            total=Sum("amount"),
            cash=Sum("amount", filter=Q(payment_method="cash")),
        )

        net_sales = float(sales["net"] or 0)
        total_collections = float(collections["total"] or 0)

        by_method = (
            payments_qs.values("payment_method")
            .annotate(total=Sum("amount"))
            .order_by("-total", "payment_method")
        )
        rows = [
            {
                "method": item["payment_method"],
                "amount": float(item["total"] or 0),
            }
            for item in by_method
        ]

        return {
            "meta": AnalyticsService._base_meta(start_dt, end_dt, filters),
            "summary": {
                "gross_sales": float(sales["gross"] or 0),
                "discount": float(sales["discount"] or 0),
                "net_sales": net_sales,
                "total_collected": total_collections,
                "cash_collections": float(collections["cash"] or 0),
                "outstanding_for_orders": float(sales["outstanding_for_orders"] or 0),
                "outstanding_period_net": net_sales - total_collections,
            },
            "series": [],
            "rows": rows,
            "notes": date_notes + filters["notes"],
        }
