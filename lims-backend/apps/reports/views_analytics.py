import csv
import io
import json
from datetime import datetime

from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAdmin, IsManager
from .analytics import AnalyticsService
from .models import ReportExportLog

# Helper permission
class IsManagerOrAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        is_auth = super().has_permission(request, view)
        if not is_auth:
            return False
        return request.user.is_admin or request.user.is_manager

class AnalyticsViewSet(viewsets.ViewSet):
    """
    API ViewSet for Operational & Financial Analytics.
    Read-only reports for Admins and Managers.
    """
    permission_classes = [IsManagerOrAdmin]

    @action(detail=False, methods=["get"])
    def overview(self, request):
        data = AnalyticsService.get_overview(request.query_params)
        return Response(data)

    @action(detail=False, methods=["get"])
    def patients(self, request):
        data = AnalyticsService.get_patients_report(request.query_params)
        return Response(data)

    @action(detail=False, methods=["get"])
    def tests(self, request):
        data = AnalyticsService.get_tests_report(request.query_params)
        return Response(data)

    @action(detail=False, methods=["get"])
    def referrals(self, request):
        data = AnalyticsService.get_referrals_report(request.query_params)
        return Response(data)

    @action(detail=False, methods=["get"])
    def finance(self, request):
        data = AnalyticsService.get_finance_report(request.query_params)
        return Response(data)

    @action(detail=False, methods=["post"], url_path="export")
    def export_report(self, request):
        """
        Export report to CSV/XLSX.
        Payload: {
            "report_key": "overview" | "patients" | "tests" | "referrals" | "finance",
            "format": "csv" | "xlsx",
            "params": { ...filters... }
        }
        """
        report_key = request.data.get("report_key")
        file_format = request.data.get("format", "csv")
        params = request.data.get("params", {})

        # Fetch data based on key
        if report_key == "overview":
            data = AnalyticsService.get_overview(params)
            rows = [data["summary"]]  # Overview is just summary for now
        elif report_key == "patients":
            data = AnalyticsService.get_patients_report(params)
            rows = data.get("rows", [])
        elif report_key == "tests":
            data = AnalyticsService.get_tests_report(params)
            rows = data.get("rows", [])
        elif report_key == "referrals":
            data = AnalyticsService.get_referrals_report(params)
            rows = data.get("rows", [])
        elif report_key == "finance":
            data = AnalyticsService.get_finance_report(params)
            rows = data.get("collections_by_method", []) # partial export
            # Finance might need more complex export structure (multiple sheets)
            # For v1 CSV, maybe just the collections list or summary?
            # Let's export summary + collections
            if not rows:
                rows = [data["summary"]]
        else:
            return Response({"error": "Invalid report_key"}, status=400)

        # Log export
        log = ReportExportLog.objects.create(
            user=request.user,
            report_key=report_key,
            filters_json=params,
            file_format=file_format,
            row_count=len(rows)
        )

        # Generate File
        filename = f"{report_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_format}"

        if file_format == "csv":
            response = HttpResponse(
                content_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
            if rows:
                writer = csv.DictWriter(response, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            else:
                writer = csv.writer(response)
                writer.writerow(["No data found"])
            
            return response

        elif file_format == "xlsx":
            import pandas as pd
            
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
            
            if rows:
                df = pd.DataFrame(rows)
            else:
                df = pd.DataFrame([{"Message": "No data found"}])

            with io.BytesIO() as b:
                with pd.ExcelWriter(b, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name="Report")
                response.write(b.getvalue())
                
            return response

        return Response({"error": "Invalid format"}, status=400)
