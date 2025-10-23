"""QC Rules service for validating laboratory results."""
import csv
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ReferenceRange:
    """Reference range for a test."""
    test_name: str
    low: float
    high: float
    units: str


@dataclass
class CriticalValue:
    """Critical value thresholds for a test."""
    test_name: str
    low_critical: float
    high_critical: float
    units: str


@dataclass
class DeltaRule:
    """Delta check rule for a test."""
    test_name: str
    max_delta: float
    units: str


@dataclass
class QCFlag:
    """QC flag result."""
    flag_type: str  # 'out_of_range', 'critical', 'delta', 'decimal_error', 'unit_error'
    severity: str  # 'warning', 'critical'
    test_name: str
    value: float
    expected_range: str
    reason: str
    requires_resolution: bool  # True for critical flags


class QCRulesService:
    """Service for quality control rules and validation."""
    
    def __init__(self, content_dir: str = None):
        """Initialize QC Rules Service by loading clinical policy files."""
        if content_dir is None:
            # Default to lims-content directory
            content_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                '../lims-content'
            )
        
        self.content_dir = content_dir
        self.reference_ranges: Dict[str, ReferenceRange] = {}
        self.critical_values: Dict[str, CriticalValue] = {}
        self.delta_rules: Dict[str, DeltaRule] = {}
        
        self._load_reference_ranges()
        self._load_critical_values()
        self._load_delta_rules()
    
    def _load_reference_ranges(self):
        """Load reference ranges from CSV."""
        filepath = os.path.join(self.content_dir, 'reference_ranges.csv')
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ref_range = ReferenceRange(
                        test_name=row['test_name'],
                        low=float(row['low']),
                        high=float(row['high']),
                        units=row['units']
                    )
                    self.reference_ranges[ref_range.test_name] = ref_range
        except FileNotFoundError:
            print(f"Warning: reference_ranges.csv not found at {filepath}")
    
    def _load_critical_values(self):
        """Load critical values from CSV."""
        filepath = os.path.join(self.content_dir, 'critical_values.csv')
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    critical = CriticalValue(
                        test_name=row['test_name'],
                        low_critical=float(row['low_critical']),
                        high_critical=float(row['high_critical']),
                        units=row['units']
                    )
                    self.critical_values[critical.test_name] = critical
        except FileNotFoundError:
            print(f"Warning: critical_values.csv not found at {filepath}")
    
    def _load_delta_rules(self):
        """Load delta check rules from CSV."""
        filepath = os.path.join(self.content_dir, 'delta_rules.csv')
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    delta = DeltaRule(
                        test_name=row['test_name'],
                        max_delta=float(row['max_delta']),
                        units=row['units']
                    )
                    self.delta_rules[delta.test_name] = delta
        except FileNotFoundError:
            print(f"Warning: delta_rules.csv not found at {filepath}")
    
    def check_reference_range(self, test_name: str, value: float) -> Optional[QCFlag]:
        """Check if value is within reference range."""
        if test_name not in self.reference_ranges:
            return None
        
        ref = self.reference_ranges[test_name]
        
        if value < ref.low or value > ref.high:
            expected = f"{ref.low}-{ref.high} {ref.units}"
            return QCFlag(
                flag_type='out_of_range',
                severity='warning',
                test_name=test_name,
                value=value,
                expected_range=expected,
                reason=f"{test_name} value {value} {ref.units} is outside reference range ({expected})",
                requires_resolution=False
            )
        
        return None
    
    def check_critical_value(self, test_name: str, value: float) -> Optional[QCFlag]:
        """Check if value is in critical range - requires immediate attention."""
        if test_name not in self.critical_values:
            return None
        
        critical = self.critical_values[test_name]
        
        if value <= critical.low_critical or value >= critical.high_critical:
            return QCFlag(
                flag_type='critical',
                severity='critical',
                test_name=test_name,
                value=value,
                expected_range=f"Critical below {critical.low_critical} or above {critical.high_critical} {critical.units}",
                reason=f"CRITICAL: {test_name} value {value} {critical.units} requires immediate attention",
                requires_resolution=True
            )
        
        return None
    
    def check_delta(self, test_name: str, current_value: float, previous_value: float) -> Optional[QCFlag]:
        """Check if delta between consecutive results exceeds threshold."""
        if test_name not in self.delta_rules:
            return None
        
        delta_rule = self.delta_rules[test_name]
        actual_delta = abs(current_value - previous_value)
        
        if actual_delta > delta_rule.max_delta:
            return QCFlag(
                flag_type='delta',
                severity='warning',
                test_name=test_name,
                value=current_value,
                expected_range=f"Max delta: {delta_rule.max_delta} {delta_rule.units}",
                reason=f"{test_name} changed by {actual_delta:.2f} {delta_rule.units} (previous: {previous_value}, current: {current_value}). Max expected: {delta_rule.max_delta}",
                requires_resolution=False
            )
        
        return None
    
    def check_clerical_errors(self, test_name: str, value: float) -> List[QCFlag]:
        """Check for common clerical errors (unit confusion, decimal point errors)."""
        flags = []
        
        if test_name not in self.reference_ranges:
            return flags
        
        ref = self.reference_ranges[test_name]
        
        # Check for decimal point errors (e.g., 135 instead of 13.5 for Hemoglobin)
        if value > ref.high * 5:
            # Likely decimal point error - value too high by factor of 5+
            corrected = value / 10
            flags.append(QCFlag(
                flag_type='decimal_error',
                severity='warning',
                test_name=test_name,
                value=value,
                expected_range=f"{ref.low}-{ref.high} {ref.units}",
                reason=f"Possible decimal point error: {value} {ref.units} is extremely high. Did you mean {corrected}?",
                requires_resolution=False
            ))
        elif value < ref.low / 5 and value > 0:
            # Likely decimal point error - value too low by factor of 5+
            corrected = value * 10
            flags.append(QCFlag(
                flag_type='decimal_error',
                severity='warning',
                test_name=test_name,
                value=value,
                expected_range=f"{ref.low}-{ref.high} {ref.units}",
                reason=f"Possible decimal point error: {value} {ref.units} is extremely low. Did you mean {corrected}?",
                requires_resolution=False
            ))
        
        # Check for unit conversion errors (e.g., mg/dL vs g/dL)
        if value > ref.high * 50:
            # Possible wrong units
            flags.append(QCFlag(
                flag_type='unit_error',
                severity='warning',
                test_name=test_name,
                value=value,
                expected_range=f"{ref.low}-{ref.high} {ref.units}",
                reason=f"Possible unit error: {value} is much higher than expected for {ref.units}. Check unit conversion.",
                requires_resolution=False
            ))
        
        return flags
    
    def validate_result(
        self,
        test_name: str,
        value: float,
        previous_value: Optional[float] = None
    ) -> List[QCFlag]:
        """
        Comprehensive validation of a test result.
        Returns list of all applicable QC flags.
        """
        flags = []
        
        # Check critical values first (highest priority)
        critical_flag = self.check_critical_value(test_name, value)
        if critical_flag:
            flags.append(critical_flag)
        
        # Check reference range
        range_flag = self.check_reference_range(test_name, value)
        if range_flag:
            flags.append(range_flag)
        
        # Check delta (if previous value provided)
        if previous_value is not None:
            delta_flag = self.check_delta(test_name, value, previous_value)
            if delta_flag:
                flags.append(delta_flag)
        
        # Check for clerical errors
        clerical_flags = self.check_clerical_errors(test_name, value)
        flags.extend(clerical_flags)
        
        return flags
    
    def has_unresolved_critical_flags(self, flags: List[QCFlag]) -> bool:
        """Check if there are any critical flags that require resolution."""
        return any(flag.requires_resolution for flag in flags)
