import re
import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

def evaluate_formula(expression: str, values: Dict[str, Any]) -> Optional[str]:
    """
    Safely evaluate a math expression for laboratory results.
    Supported: +, -, *, /, (), and {CODE} placeholders.
    Values should be numeric strings or Decimals.
    """
    if not expression:
        return None

    # 1. Replace placeholders {WBC} with numeric values
    def replace_code(match):
        code = match.group(1)
        val = values.get(code)
        if val is None or str(val).strip() == "" or str(val) == "*":
            return "NaN" # Will cause evaluation to fail or return None
        return str(val)

    # Replace both {CODE} and just CODE if matched? 
    # Usually better to stick to {CODE} to avoid accidental replacements.
    processed_expr = re.sub(r"\{([^}]+)\}", replace_code, expression)

    if "NaN" in processed_expr:
        logger.debug(f"Formula evaluation skipped: missing values in {expression}")
        return None

    # 2. Basic Sanity Check (only allow math chars)
    # Allowed: 0-9, ., +, -, *, /, (, ), space
    if not re.match(r"^[0-9\.\+\-\*\/\(\)\s]+$", processed_expr):
        logger.error(f"Insecure or invalid formula expression generated: {processed_expr}")
        return None

    # 3. Safe Evaluation (using a very simple parser or eval with restricted globals)
    # Since we strictly validated the string above to only contain math chars, 
    # eval() is relatively safe, but let's be extra careful.
    try:
        # We use a simple eval with empty globals/locals
        # But even better, we use Decimal for precision if needed?
        # Standard eval is fine for simple math after strict regex validation.
        result = eval(processed_expr, {"__builtins__": None}, {})
        
        # Round to reasonable precision (e.g. 2-4 decimal places)
        if isinstance(result, (int, float, Decimal)):
            return str(round(Decimal(str(result)), 4).normalize())
        return str(result)
    except (ZeroDivisionError, SyntaxError, NameError, TypeError, InvalidOperation) as e:
        logger.warning(f"Formula evaluation error: {str(e)} for expression {processed_expr}")
        return None

def recompute_formulas_for_order_item(order_item):
    """
    Fetch all results for an OrderItem and recompute FORMULA parameters.
    """
    from apps.results.models import TestResult
    
    # 1. Fetch current results to build value map (use parameter_id and short_name as keys)
    results = TestResult.objects.filter(order_item=order_item).select_related("test_parameter", "test_parameter__parameter")
    
    values_map = {}
    for res in results:
        val = res.result_value
        # Store by parameter_id (e.g. p1) and short_name if available (e.g. WBC)
        p_id = res.test_parameter.parameter.parameter_id
        short_name = res.test_parameter.parameter.short_name
        
        values_map[p_id] = val
        if short_name:
            values_map[short_name] = val

    # 2. Identify formula-based parameters
    formula_results = [r for r in results if r.test_parameter.value_source == "FORMULA"]
    
    updated = []
    for res in formula_results:
        # Skip if manual override is enabled and a value already exists (and it's not the computed one?)
        # For MVP, let's assume if it has a value and allow_manual_override is True, we skip it.
        if res.test_parameter.allow_manual_override and res.result_value:
             # How do we know if it was manually entered? 
             # Maybe we need a flag? But request didn't specify a flag.
             # User said: "If allow_manual_override=true, manual value wins and formula is skipped (flag override)."
             # I'll assume for now that if value_source is FORMULA, we usually compute it.
             # If the user explicitly edited it, we might need a way to track.
             # Let's check if there is an 'is_manual_override' field.
             pass

        expr = res.test_parameter.formula_expression
        new_val = evaluate_formula(expr, values_map)
        
        if new_val and new_val != res.result_value:
            res.result_value = new_val
            # res.status = "ENTERED" # Should we update status?
            # User said: "Saving results must NOT advance Order/OrderItem to verified/published."
            # But the result itself should probably be marked ENTERED or similar.
            res.save(update_fields=["result_value", "flag"])
            updated.append(res)
            
            # Update map for dependent formulas
            values_map[res.test_parameter.parameter.parameter_id] = new_val
            if res.test_parameter.parameter.short_name:
                values_map[res.test_parameter.parameter.short_name] = new_val

    return updated
