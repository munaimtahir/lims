"""Dashboard views for analytics and performance metrics."""

from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order
from results.models import Result, ResultStatus
from samples.models import Sample, SampleStatus


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_analytics(request):
    """Get dashboard analytics and performance metrics.

    Query parameters:
    - start_date: Filter from date (ISO format, default: 30 days ago)
    - end_date: Filter to date (ISO format, default: today)

    Returns:
    - quick_tiles: Total orders today, reports published today
    - orders_per_day: Daily order counts for the date range
    - sample_status: Count of pending, received, collected samples
    - avg_tat: Average turnaround time from order to publish (in hours)
    """
    # Parse date range from query params
    end_date = request.query_params.get("end_date")
    start_date = request.query_params.get("start_date")

    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            return Response(
                {"error": "Invalid end_date format. Use ISO format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        end_date = timezone.now()

    if start_date:
        try:
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            return Response(
                {"error": "Invalid start_date format. Use ISO format."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        start_date = end_date - timedelta(days=30)

    # Ensure start_date is before end_date
    if start_date > end_date:
        return Response(
            {"error": "start_date must be before end_date"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Quick tiles - today's data
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total_orders_today = Order.objects.filter(created_at__gte=today_start).count()
    reports_published_today = Result.objects.filter(
        status=ResultStatus.PUBLISHED, published_at__gte=today_start
    ).count()

    quick_tiles = {
        "total_orders_today": total_orders_today,
        "reports_published_today": reports_published_today,
    }

    # Orders per day for the date range
    orders_by_day = {}
    current_date = start_date.date()
    end_date_date = end_date.date()

    while current_date <= end_date_date:
        day_start = timezone.make_aware(
            datetime.combine(current_date, datetime.min.time())
        )
        day_end = day_start + timedelta(days=1)
        count = Order.objects.filter(
            created_at__gte=day_start, created_at__lt=day_end
        ).count()
        orders_by_day[current_date.isoformat()] = count
        current_date += timedelta(days=1)

    orders_per_day = [
        {"date": date, "count": count} for date, count in orders_by_day.items()
    ]

    # Sample status distribution
    sample_status = {
        "pending": Sample.objects.filter(status=SampleStatus.PENDING).count(),
        "collected": Sample.objects.filter(status=SampleStatus.COLLECTED).count(),
        "received": Sample.objects.filter(status=SampleStatus.RECEIVED).count(),
        "rejected": Sample.objects.filter(status=SampleStatus.REJECTED).count(),
    }

    # Result status distribution
    result_status = {
        "draft": Result.objects.filter(status=ResultStatus.DRAFT).count(),
        "entered": Result.objects.filter(status=ResultStatus.ENTERED).count(),
        "verified": Result.objects.filter(status=ResultStatus.VERIFIED).count(),
        "published": Result.objects.filter(status=ResultStatus.PUBLISHED).count(),
    }

    # Average TAT (Turnaround Time) - order creation to result publish
    published_results = Result.objects.filter(
        status=ResultStatus.PUBLISHED, published_at__isnull=False
    ).select_related("order_item__order")

    tat_hours = []
    for result in published_results:
        order_created = result.order_item.order.created_at
        result_published = result.published_at
        if order_created and result_published:
            tat = (result_published - order_created).total_seconds() / 3600
            tat_hours.append(tat)

    avg_tat = sum(tat_hours) / len(tat_hours) if tat_hours else 0

    return Response(
        {
            "quick_tiles": quick_tiles,
            "orders_per_day": orders_per_day,
            "sample_status": sample_status,
            "result_status": result_status,
            "avg_tat_hours": round(avg_tat, 2),
        },
        status=status.HTTP_200_OK,
    )
