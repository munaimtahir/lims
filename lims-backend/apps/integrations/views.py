"""
Views for analyzer integration.
"""

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Analyzer, AnalyzerResultImport
from .serializers import AnalyzerSerializer, AnalyzerResultImportSerializer
from .hl7_parser import parse_hl7_message
from apps.orders.models import OrderItem
from apps.results.models import TestResult
from apps.laboratory.models import TestParameter


class AnalyzerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing analyzers.
    """
    
    queryset = Analyzer.objects.all()
    serializer_class = AnalyzerSerializer


class AnalyzerResultImportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing analyzer result imports.
    """
    
    queryset = AnalyzerResultImport.objects.all()
    serializer_class = AnalyzerResultImportSerializer
    
    @action(detail=False, methods=["post"])
    def import_hl7(self, request):
        """
        Import results from HL7 message.
        
        Request body:
            - analyzer_id: ID of the analyzer
            - message: Raw HL7 message string
        
        Returns:
            Response: Import status and created records
        """
        analyzer_id = request.data.get("analyzer_id")
        message = request.data.get("message")
        
        if not analyzer_id or not message:
            return Response(
                {"error": "analyzer_id and message are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            analyzer = Analyzer.objects.get(id=analyzer_id, is_active=True)
        except Analyzer.DoesNotExist:
            return Response(
                {"error": "Analyzer not found or not active"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Parse HL7 message
        try:
            parsed_data = parse_hl7_message(message)
        except Exception as e:
            # Create import record with error
            import_record = AnalyzerResultImport.objects.create(
                analyzer=analyzer,
                raw_message=message,
                parsed_data={},
                status="FAILED",
                error_message=f"HL7 parsing error: {str(e)}",
            )
            return Response(
                {
                    "status": "failed",
                    "error": str(e),
                    "import_id": import_record.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Try to match to order
        order_info = parsed_data.get("order", {})
        order_item = None
        
        # Try to find order by placer order number or filler order number
        placer_order = order_info.get("placer_order_number")
        filler_order = order_info.get("filler_order_number")
        
        if placer_order:
            try:
                # Try to match by order_id
                from apps.orders.models import Order
                order = Order.objects.filter(order_id=placer_order).first()
                if order:
                    # Match by test code
                    test_code = order_info.get("test_code")
                    if test_code:
                        order_item = OrderItem.objects.filter(
                            order=order,
                            test__test_code=test_code,
                        ).first()
            except Exception as e:
                pass
        
        # Create import record
        import_record = AnalyzerResultImport.objects.create(
            analyzer=analyzer,
            raw_message=message,
            parsed_data=parsed_data,
            order_item=order_item,
            status="MATCHED" if order_item else "MANUAL_REVIEW",
            imported_by=request.user if request.user.is_authenticated else None,
        )
        
        # If matched, create test results
        if order_item:
            try:
                with transaction.atomic():
                    results = parsed_data.get("results", [])
                    for result_data in results:
                        # Find test parameter
                        param_name = result_data.get("parameter_name", "")
                        param = TestParameter.objects.filter(
                            test=order_item.test,
                            parameter_name__icontains=param_name,
                        ).first()
                        
                        if param:
                            # Create or update test result
                            test_result, created = TestResult.objects.get_or_create(
                                order_item=order_item,
                                test_parameter=param,
                                defaults={
                                    "result_value": result_data.get("value", ""),
                                    "flag": result_data.get("flag", "normal"),
                                    "entered_by": request.user if request.user.is_authenticated else None,
                                },
                            )
                            
                            if not created:
                                # Update existing result
                                test_result.result_value = result_data.get("value", "")
                                test_result.flag = result_data.get("flag", "normal")
                                test_result.save()
                            
                            import_record.test_result = test_result
                            import_record.status = "IMPORTED"
                            import_record.save()
                
                # Update analyzer last sync
                analyzer.last_sync_at = timezone.now()
                analyzer.save()
                
            except Exception as e:
                import_record.status = "FAILED"
                import_record.error_message = str(e)
                import_record.save()
                
                return Response(
                    {
                        "status": "failed",
                        "error": str(e),
                        "import_id": import_record.id,
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        
        serializer = self.get_serializer(import_record)
        return Response(
            {
                "status": "success" if import_record.status == "IMPORTED" else "pending_review",
                "import": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
    
    @action(detail=True, methods=["post"])
    def match_order(self, request, pk=None):
        """
        Manually match an import to an order item.
        
        Request body:
            - order_item_id: ID of the order item to match
        
        Returns:
            Response: Updated import record
        """
        import_record = self.get_object()
        order_item_id = request.data.get("order_item_id")
        
        if not order_item_id:
            return Response(
                {"error": "order_item_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            order_item = OrderItem.objects.get(id=order_item_id)
        except OrderItem.DoesNotExist:
            return Response(
                {"error": "Order item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        import_record.order_item = order_item
        import_record.status = "MATCHED"
        import_record.imported_by = request.user
        import_record.save()
        
        # Create test results
        try:
            parsed_data = import_record.parsed_data
            results = parsed_data.get("results", [])
            
            for result_data in results:
                param_name = result_data.get("parameter_name", "")
                param = TestParameter.objects.filter(
                    test=order_item.test,
                    parameter_name__icontains=param_name,
                ).first()
                
                if param:
                    test_result, created = TestResult.objects.get_or_create(
                        order_item=order_item,
                        test_parameter=param,
                        defaults={
                            "result_value": result_data.get("value", ""),
                            "flag": result_data.get("flag", "normal"),
                            "entered_by": request.user,
                        },
                    )
                    
                    if not created:
                        test_result.result_value = result_data.get("value", "")
                        test_result.flag = result_data.get("flag", "normal")
                        test_result.save()
                    
                    import_record.test_result = test_result
                    import_record.status = "IMPORTED"
                    import_record.save()
        
        except Exception as e:
            import_record.status = "FAILED"
            import_record.error_message = str(e)
            import_record.save()
        
        serializer = self.get_serializer(import_record)
        return Response(serializer.data, status=status.HTTP_200_OK)

