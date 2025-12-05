from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Report
from .serializers import ReportSerializer
from .utils import generate_pdf_report
from apps.orders.models import Order


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling report generation and retrieval.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['order', 'is_final', 'generated_by']
    search_fields = ['order__order_id', 'order__patient__first_name', 'order__patient__last_name']
    ordering_fields = ['generated_at']
    
    @action(detail=False, methods=['get'])
    def list_reports(self, request):
        """
        List all reports with optional filtering.
        
        Query params:
            - order: Filter by order ID
            - is_final: Filter by final status (true/false)
            - search: Search by order ID or patient name
        
        Returns:
            Response: Paginated list of reports.
        """
        # This is handled by the default list action, but we can add custom logic here
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download the PDF report file.

        Args:
            request (Request): The request object.
            pk (int): The primary key of the report.

        Returns:
            FileResponse: The PDF file response.
        """
        report = self.get_object()
        if not report.report_file:
            return Response(
                {'error': 'Report file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return FileResponse(
            report.report_file.open('rb'),
            content_type='application/pdf',
            filename=report.report_file.name.split('/')[-1]
        )
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """
        Mark a report as delivered to the patient.

        Args:
            request (Request): The request object.
            pk (int): The primary key of the report.

        Returns:
            Response: Success message.
        """
        report = self.get_object()
        # Note: We might want to add a 'delivered_at' field to the Report model
        # For now, we'll just return success
        return Response({
            'status': 'Report marked as delivered',
            'report_id': report.id
        })
    
    @action(detail=True, methods=['post'])
    def upload_signature(self, request, pk=None):
        """
        Upload a digital signature for a report.

        Args:
            request (Request): The request object with 'signature' file and 'signature_type' ('pathologist' or 'technician').
            pk (int): The primary key of the report.

        Returns:
            Response: Updated report data.
        """
        report = self.get_object()
        signature_type = request.data.get('signature_type', 'pathologist')
        signature_file = request.FILES.get('signature')
        
        if not signature_file:
            return Response(
                {'error': 'Signature file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if signature_type == 'pathologist':
            if not (request.user.is_pathologist or request.user.is_admin):
                return Response(
                    {'error': 'Only pathologists can upload pathologist signatures'},
                    status=status.HTTP_403_FORBIDDEN
                )
            report.pathologist_signature = signature_file
            report.verified_by = request.user
            report.verified_at = timezone.now()
        elif signature_type == 'technician':
            if not (request.user.is_lab_technician or request.user.is_admin):
                return Response(
                    {'error': 'Only lab technicians can upload technician signatures'},
                    status=status.HTTP_403_FORBIDDEN
                )
            report.technician_signature = signature_file
        else:
            return Response(
                {'error': 'Invalid signature_type. Must be "pathologist" or "technician"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.save()
        return Response(self.get_serializer(report).data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new PDF report for a given order.

        Args:
            request (Request): The request object, containing the 'order_id'.

        Returns:
            Response: A response object with the created report data or an error message.
        """
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Try to get order by ID or order_id string
            try:
                order = Order.objects.get(id=order_id)
            except (Order.DoesNotExist, ValueError):
                try:
                    order = Order.objects.get(order_id=order_id)
                except Order.DoesNotExist:
                    return Response(
                        {'error': 'Order not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Check if report already exists
            existing_report = Report.objects.filter(order=order, is_final=True).first()
            if existing_report and not request.data.get('regenerate', False):
                return Response(
                    {
                        'message': 'Report already exists',
                        'report': ReportSerializer(existing_report).data
                    },
                    status=status.HTTP_200_OK
                )
            
            # Generate PDF
            pdf_content = generate_pdf_report(order.id)
            
            # Create or update report
            if existing_report:
                report = existing_report
            else:
                report = Report(order=order)
            
            if request.user.is_authenticated:
                report.generated_by = request.user
            
            filename = f"Report_{order.order_id}_{order.id}.pdf"
            report.report_file.save(filename, ContentFile(pdf_content))
            report.is_final = request.data.get('is_final', True)
            report.save()

            return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
