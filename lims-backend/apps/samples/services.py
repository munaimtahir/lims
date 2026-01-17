"""
Service layer for sample generation and management.

This module provides business logic for automatic sample creation and lifecycle management.
"""

import logging
from django.db import transaction
from django.utils import timezone
from .models import Sample, SampleStatus
from apps.orders.models import Order, OrderItem

logger = logging.getLogger(__name__)


def generate_samples_for_order(order: Order, created_by=None) -> list[Sample]:
    """
    Generate pending sample records for all items in a paid order.
    
    This function creates Sample instances for each OrderItem that requires sample collection.
    It is idempotent - if samples already exist for an order item, they will not be duplicated.
    
    Args:
        order: The Order instance to generate samples for
        created_by: Optional User who triggered the sample generation
        
    Returns:
        List of created Sample instances (empty if order not paid or samples already exist)
        
    Business Rules:
        - Only generates samples if order.is_paid == True
        - Creates one sample per OrderItem (test or panel)
        - Sample status starts as PENDING
        - Sample type determined by test/panel requirements
        - Idempotent: won't duplicate existing samples
    """
    created_samples = []
    
    # Only generate samples for paid orders
    if not order.is_paid:
        logger.debug(f"Order {order.order_id} is not paid. Skipping sample generation.")
        return created_samples
    
    with transaction.atomic():
        # Process each order item
        for order_item in order.items.all():
            # Check if samples already exist for this order item (idempotency)
            existing_samples = order_item.samples.all()
            if existing_samples.exists():
                logger.debug(
                    f"Samples already exist for OrderItem {order_item.id}. "
                    f"Skipping duplicate generation."
                )
                continue
            
            # Determine sample type based on test or panel
            sample_type = _determine_sample_type(order_item)
            
            # Create sample for this order item
            sample = Sample.objects.create(
                order_item=order_item,
                sample_type=sample_type,
                status=SampleStatus.PENDING,
                notes=f"Auto-generated on payment for order {order.order_id}"
            )
            
            created_samples.append(sample)
            logger.info(
                f"Created sample {sample.barcode} (type: {sample_type}) "
                f"for OrderItem {order_item.id} in Order {order.order_id}"
            )
    
    if created_samples:
        logger.info(
            f"Generated {len(created_samples)} samples for Order {order.order_id}"
        )
    
    return created_samples


def _determine_sample_type(order_item: OrderItem) -> str:
    """
    Determine the sample type required for an order item.
    
    Args:
        order_item: The OrderItem to determine sample type for
        
    Returns:
        Sample type string (e.g., "Blood", "Urine", "Serum")
        
    Notes:
        - Currently uses simple defaults based on test/panel
        - In future, could read from test.sample_type or parameter.sample_type
        - Falls back to "Blood" as most common lab sample type
    """
    if order_item.test:
        # Check if test has a sample_type field (future enhancement)
        test = order_item.test
        if hasattr(test, 'sample_type') and test.sample_type:
            return test.sample_type
        
        # Map test categories to sample types (simple heuristics)
        test_name_lower = test.test_name.lower()
        if 'urine' in test_name_lower:
            return "Urine"
        elif 'stool' in test_name_lower or 'fecal' in test_name_lower:
            return "Stool"
        elif 'swab' in test_name_lower or 'culture' in test_name_lower:
            return "Swab"
        elif 'csf' in test_name_lower or 'cerebrospinal' in test_name_lower:
            return "CSF"
        else:
            # Default to blood for most lab tests
            return "Blood"
    
    elif order_item.panel:
        # For panels, default to Blood (most panels are blood-based)
        return "Blood"
    
    # Fallback
    return "Blood"


def ensure_samples_for_paid_order(order: Order, created_by=None) -> list[Sample]:
    """
    Ensure samples exist for a paid order (wrapper for generate_samples_for_order).
    
    This is a convenience function with a more descriptive name for use in signals/endpoints.
    
    Args:
        order: The Order instance
        created_by: Optional User who triggered the action
        
    Returns:
        List of Sample instances (newly created or empty if already existed)
    """
    return generate_samples_for_order(order, created_by)
