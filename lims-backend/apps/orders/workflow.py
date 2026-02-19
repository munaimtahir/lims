from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.orders.models import Order, OrderItem
from apps.results.models import TestResult
from apps.samples.models import Sample, SampleStatus
from apps.audit.workflow_middleware import log_workflow_span
import logging

logger = logging.getLogger(__name__)

class OrderWorkflowService:
    """
    Centralized service for Order status transitions and workflow enforcement.
    This is the ONLY place where Order.status should be mutated.
    """

    @staticmethod
    @transaction.atomic
    def receive_sample(sample_id: str, user, location=None) -> Sample:
        """
        Mark a sample as RECEIVED.
        If all samples for the order are received, transition Order to IN_PROCESS.
        """
        sample = Sample.objects.select_for_update().get(id=sample_id)
        
        if sample.status == SampleStatus.RECEIVED:
            logger.info(f"Sample {sample_id} already received.")
            return sample

        old_status = sample.status
        sample.status = SampleStatus.RECEIVED
        sample.received_at = timezone.now()
        sample.received_by = user
        if location:
            sample.current_branch = location
        sample.save()
        
        # Log workflow span
        log_workflow_span("receive_sample", {
            "sample_id": sample_id,
            "old_status": old_status,
            "new_status": "RECEIVED",
            "user": user.username if user else None,
            "location": location
        })
        
        # Check parent order status
        # Note: Sample is linked to OrderItem, which is linked to Order
        if sample.order_item:
            order = sample.order_item.order
            OrderWorkflowService._recalculate_order_status(order, user)
            
        return sample

    @staticmethod
    @transaction.atomic
    def confirm_collection(order_id: int, user) -> Order:
        """
        Mark an order as COLLECTED (Phlebotomy complete).
        """
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status != "NEW":
             # If already further along, ignore or error. 
             # If strictly NEW, move to COLLECTED.
             pass
        
        # Update all samples to COLLECTED if they are PENDING
        for item in order.items.all():
            for sample in item.samples.all():
                if sample.status == SampleStatus.PENDING:
                    sample.status = SampleStatus.COLLECTED
                    sample.collected_at = timezone.now()
                    sample.collected_by = user
                    sample.save()
        
        OrderWorkflowService._transition_order(order, "COLLECTED", user)
        return order
        
    @staticmethod
    @transaction.atomic
    def enter_result(result_id: int, value: str, user) -> TestResult:
        """
        Enter a value for a result. Transitions status to ENTERED (or DRAFT).
        Ensures Order is at least IN_PROCESS.
        """
        result = TestResult.objects.select_for_update().get(pk=result_id)
        order = result.order_item.order
        
        # Ensure Order is not in a locked state
        if order.status in ["VERIFIED", "PUBLISHED", "CANCELLED"]:
            raise ValidationError(f"Cannot enter results for order in {order.status} state.")
            
        # Update result
        result.result_value = value
        result.entered_by = user
        result.entered_at = timezone.now()
        result.status = "ENTERED" # Or DRAFT? 
        result.validate_result() # Calcs flags
        result.save()
        
        # If Order was NEW or COLLECTED, it is now IN_PROCESS (implicit accessioning if skipped?)
        # Better to strictly require accessioning, but for MVP/User rules:
        # "Entering any result that completes required parameters sets Order.status = RESULTS_ENTERED"
        # Wait, Order.status doesn't have RESULTS_ENTERED. It has IN_PROCESS.
        # I will treat IN_PROCESS as "Processing/Results Entry".
        
        if order.status in ["NEW", "COLLECTED"]:
            OrderWorkflowService._transition_order(order, "IN_PROCESS", user)
            
        return result

    @staticmethod
    @transaction.atomic
    def verify_result(result_id: int, user) -> TestResult:
        """
        Verify a single result.
        Upgrades Order status if all required results are verified.
        """
        result = TestResult.objects.select_for_update().get(pk=result_id)
        
        if result.status in ["VERIFIED", "FINAL"]:
            return result
            
        result.status = "VERIFIED"
        result.verified_by = user
        result.verified_at = timezone.now()
        result.save()
        
        OrderWorkflowService._recalculate_order_status(result.order_item.order, user)
        return result

    @staticmethod
    @transaction.atomic
    def verify_order(order_id: int, user) -> Order:
        """
        Verify an order.
        Prerequisite: All required results must be entered.
        Action: Sets all eligible results to VERIFIED, sets Order to VERIFIED.
        """
        order = Order.objects.select_for_update().get(pk=order_id)
        
        # 1. Update all results to VERIFIED (if entered/ready)
        results = TestResult.objects.filter(order_item__order=order, status__in=["DRAFT", "ENTERED", "READY"])
        for res in results:
             res.status = "VERIFIED"
             res.verified_by = user
             res.verified_at = timezone.now()
             res.save()
        
        # 2. Recalculate will handle the Order status upgrade if valid
        OrderWorkflowService._recalculate_order_status(order, user)
        
        # Force verify if requirements met (recalculate should have done it, but let's be strict)
        order.refresh_from_db()
        if order.status != "VERIFIED":
             # Check if we CAN force it (maybe some optl results missing? logic depends on "Required" strictly)
             # If logic says "Verify Order", we usually imply "Verify all that is verifyable and close it".
             # But User Rule: "No order can be VERIFIED if required results are missing"
             pass
             
        return order

    @staticmethod
    @transaction.atomic
    def publish_order(order_id: int, user) -> Order:
        """
        Publish an order (Generate PDF).
        Prerequisite: Order must be VERIFIED.
        """
        order = Order.objects.select_for_update().get(pk=order_id)
        
        if order.status != "VERIFIED":
             # Auto-verify if possible? No, explicit step required.
             raise ValidationError("Order must be VERIFIED before publishing.")
             
        OrderWorkflowService._transition_order(order, "PUBLISHED", user)
        
        # Finalize results?
        TestResult.objects.filter(order_item__order=order).update(status="FINAL")
        
        return order

    @staticmethod
    @staticmethod
    def _recalculate_order_status(order: Order, user):
        """
        Derive Order status from its children (Samples, Results).
        """
        current_status = order.status
        if current_status in ["PUBLISHED", "CANCELLED"]:
            return

        # 1. Sample Status Check
        samples = Sample.objects.filter(order_item__order=order)
        samples_received = samples.filter(status=SampleStatus.RECEIVED).exists()
        samples_collected = samples.filter(status=SampleStatus.COLLECTED).exists()
        
        target_status = current_status
        
        # Promotion: NEW -> COLLECTED -> IN_PROCESS
        if current_status == "NEW":
            if samples_received:
               target_status = "IN_PROCESS"
            elif samples_collected:
               target_status = "COLLECTED"
        elif current_status == "COLLECTED":
            if samples_received:
               target_status = "IN_PROCESS"

        # 2. Result Status Check
        # If ANY result entered -> IN_PROCESS (if not already)
        results = TestResult.objects.filter(order_item__order=order)
        has_entered_results = results.filter(result_value__isnull=False).exclude(result_value="").exists()
        
        if has_entered_results and target_status in ["NEW", "COLLECTED"]:
            target_status = "IN_PROCESS"
            
        # 3. Verification Check
        # Promotion: IN_PROCESS -> VERIFIED
        # Condition: All REQUIRED parameters have VERIFIED or FINAL status
        # And at least one result exists (to avoid verifying empty orders)
        if target_status == "IN_PROCESS":
            required_params = results.filter(test_parameter__is_required_for_verification=True)
            if required_params.exists():
                pending_required = required_params.exclude(status__in=["VERIFIED", "FINAL"])
                if not pending_required.exists():
                    target_status = "VERIFIED"
            else:
                # If no required params, check if ALL existing results are verified
                if results.exists() and not results.exclude(status__in=["VERIFIED", "FINAL"]).exists():
                    target_status = "VERIFIED"
        
        # Regression: VERIFIED -> IN_PROCESS
        # If we are VERIFIED but suddenly have a strict requirement pending (e.g. result reverted)
        if current_status == "VERIFIED":
             required_params = results.filter(test_parameter__is_required_for_verification=True)
             if required_params.exists():
                 pending_required = required_params.exclude(status__in=["VERIFIED", "FINAL"])
                 if pending_required.exists():
                     target_status = "IN_PROCESS"
        
        if target_status != current_status:
            # Log workflow span for status recalculation
            log_workflow_span("recalculate_order_status", {
                "order_id": order.order_id,
                "old_status": current_status,
                "new_status": target_status,
                "samples_count": samples.count(),
                "samples_received": samples.filter(status=SampleStatus.RECEIVED).count(),
                "results_count": results.count(),
                "results_verified": results.filter(status__in=["VERIFIED", "FINAL"]).count(),
            })
            OrderWorkflowService._transition_order(order, target_status, user)

    @staticmethod
    def _transition_order(order: Order, new_status: str, user):
        if order.status == new_status:
            return
        
        # Use model's validation
        order.validate_status_transition(order.status, new_status)
        
        logger.info(f"Transitioning Order {order.order_id}: {order.status} -> {new_status} by {user}")
        
        # Log workflow span
        log_workflow_span("transition_order", {
            "order_id": order.order_id,
            "old_status": order.status,
            "new_status": new_status,
            "user": user.username if user else None,
        })
        
        order.status = new_status
        order.updated_at = timezone.now()
        # order.ordered_by = user # Keep original creator? Or last modifier? Model says ordered_by is creator.
        order.save(update_fields=["status", "updated_at"])
