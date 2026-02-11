import csv
import io
from datetime import datetime

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAdmin

from .analytics import AnalyticsService
from .models import ReportExportLog


class AnalyticsViewSet(viewsets.ViewSet):
    """Read-only operational & financial analytics for Admin/Manager roles."""

    permission_classes = [IsManagerOrAdmin]

    def _fetch_report(self, report_key, params):
        handlers = {
            "overview": AnalyticsService.get_overview,
            "patients": AnalyticsService.get_patients_report,
            "tests": AnalyticsService.get_tests_report,
            "referrals": AnalyticsService.get_referrals_report,
            "finance": AnalyticsService.get_finance_report,
        }
        if report_key not in handlers:
            return None
        return handlers[report_key](params)

    @action(detail=False, methods=["get"])
    def overview(self, request):
        return Response(AnalyticsService.get_overview(request.query_params))

    @action(detail=False, methods=["get"])
    def patients(self, request):
        return Response(AnalyticsService.get_patients_report(request.query_params))

    @action(detail=False, methods=["get"])
    def tests(self, request):
        return Response(AnalyticsService.get_tests_report(request.query_params))

    @action(detail=False, methods=["get"])
    def referrals(self, request):
        return Response(AnalyticsService.get_referrals_report(request.query_params))

    @action(detail=False, methods=["get"])
    def finance(self, request):
        return Response(AnalyticsService.get_finance_report(request.query_params))

    @action(detail=False, methods=["post"], url_path="export")
    def export_report(self, request):
        """
        Accepts payload: {report_key, format, filters}.
        Backward-compatible with legacy "params" key.
        """
        report_key = request.data.get("report_key")
        file_format = (request.data.get("format") or "csv").lower()
        filters = request.data.get("filters")
        if filters is None:
            filters = request.data.get("params", {})

        if file_format not in {"csv", "xlsx"}:
            return Response({"error": "Invalid format"}, status=400)

        data = self._fetch_report(report_key, filters)
        if data is None:
            return Response({"error": "Invalid report_key"}, status=400)

        rows = data.get("rows")
        if report_key == "overview":
            export_rows = [data.get("summary", {})]
        elif report_key == "referrals" and isinstance(rows, dict):
            export_rows = rows.get("revenue") or rows.get("volume") or []
        elif report_key == "finance":
            export_rows = rows if isinstance(rows, list) else []
        else:
            export_rows = rows if isinstance(rows, list) else []

        filename = f"{report_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}"
        ReportExportLog.objects.create(
            user=request.user,
            report_key=report_key,
            filters_json=filters or {},
            file_format=file_format,
            row_count=len(export_rows),
            file_path=filename,
        )

        if file_format == "csv":
            response = HttpResponse(
                content_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
            if export_rows:
                writer = csv.DictWriter(response, fieldnames=export_rows[0].keys())
                writer.writeheader()
                writer.writerows(export_rows)
            else:
                writer = csv.writer(response)
                writer.writerow(["No data found"])
            return response

        import pandas as pd

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

        if export_rows:
            df = pd.DataFrame(export_rows)
        else:
            df = pd.DataFrame([{"Message": "No data found"}])

        with io.BytesIO() as out:
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Report")
            response.write(out.getvalue())

        return response

    @action(detail=False, methods=["get"], url_path="export-logs")
    def export_logs(self, request):
        limit = request.query_params.get("limit", "100")
        try:
            limit_value = max(1, min(500, int(limit)))
        except ValueError:
            limit_value = 100

        logs_qs = ReportExportLog.objects.select_related("user").all()[:limit_value]
        rows = [
            {
                "id": log.id,
                "user": getattr(log.user, "username", None),
                "report_key": log.report_key,
                "filters_json": log.filters_json,
                "format": log.file_format,
                "generated_at": log.generated_at.isoformat(),
                "row_count": log.row_count,
                "file_path": log.file_path,
            }
            for log in logs_qs
        ]

        return Response(
            {
                "meta": {"limit": limit_value, "count": len(rows)},
                "summary": {"total_exports": len(rows)},
                "series": [],
                "rows": rows,
                "notes": [],
            }
        )
