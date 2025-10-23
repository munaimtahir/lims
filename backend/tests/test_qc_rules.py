"""Tests for QC rules service."""

from lims.services.qc_rules import QCRulesService


class TestQCRulesService:
    """Test QC rules functionality."""

    @classmethod
    def setup_class(cls):
        """Setup QC service with test data."""
        # Use the actual lims-content directory - go up from backend/tests to repo root
        import pathlib

        test_dir = pathlib.Path(__file__).parent
        repo_root = test_dir.parent.parent
        content_dir = repo_root / "lims-content"
        cls.qc = QCRulesService(content_dir=str(content_dir))

    def test_load_reference_ranges(self):
        """Test that reference ranges are loaded correctly."""
        assert "Hemoglobin" in self.qc.reference_ranges
        assert "Potassium" in self.qc.reference_ranges
        assert "Glucose Fasting" in self.qc.reference_ranges

        hb = self.qc.reference_ranges["Hemoglobin"]
        assert hb.low == 13.5
        assert hb.high == 17.5
        assert hb.units == "g/dL"

    def test_load_critical_values(self):
        """Test that critical values are loaded correctly."""
        assert "Hemoglobin" in self.qc.critical_values

        hb_critical = self.qc.critical_values["Hemoglobin"]
        assert hb_critical.low_critical == 7.0
        assert hb_critical.high_critical == 20.0

    def test_load_delta_rules(self):
        """Test that delta rules are loaded correctly."""
        assert "Hemoglobin" in self.qc.delta_rules

        hb_delta = self.qc.delta_rules["Hemoglobin"]
        assert hb_delta.max_delta == 2.0

    def test_reference_range_normal(self):
        """Test value within normal range."""
        flag = self.qc.check_reference_range("Hemoglobin", 15.0)
        assert flag is None  # No flag for normal value

    def test_reference_range_low(self):
        """Test value below reference range."""
        flag = self.qc.check_reference_range("Hemoglobin", 12.0)
        assert flag is not None
        assert flag.flag_type == "out_of_range"
        assert flag.severity == "warning"
        assert "outside reference range" in flag.reason.lower()

    def test_reference_range_high(self):
        """Test value above reference range."""
        flag = self.qc.check_reference_range("Hemoglobin", 18.5)
        assert flag is not None
        assert flag.flag_type == "out_of_range"
        assert flag.severity == "warning"

    def test_critical_value_low(self):
        """Test critically low value."""
        flag = self.qc.check_critical_value("Hemoglobin", 6.5)
        assert flag is not None
        assert flag.flag_type == "critical"
        assert flag.severity == "critical"
        assert flag.requires_resolution is True
        assert "CRITICAL" in flag.reason

    def test_critical_value_high(self):
        """Test critically high value."""
        flag = self.qc.check_critical_value("Potassium", 7.0)
        assert flag is not None
        assert flag.flag_type == "critical"
        assert flag.severity == "critical"
        assert flag.requires_resolution is True

    def test_critical_value_normal(self):
        """Test value not in critical range."""
        flag = self.qc.check_critical_value("Hemoglobin", 15.0)
        assert flag is None

    def test_delta_check_normal(self):
        """Test delta within acceptable range."""
        flag = self.qc.check_delta("Hemoglobin", 15.0, 14.5)
        assert flag is None  # Delta of 0.5 is within 2.0 max

    def test_delta_check_exceeds(self):
        """Test delta exceeding threshold."""
        flag = self.qc.check_delta("Hemoglobin", 15.0, 12.0)
        assert flag is not None
        assert flag.flag_type == "delta"
        assert flag.severity == "warning"
        assert "changed by 3.00" in flag.reason

    def test_decimal_error_high(self):
        """Test detection of decimal point error (value too high)."""
        # Hemoglobin of 150 g/dL should trigger decimal error (likely meant 15.0)
        flags = self.qc.check_clerical_errors("Hemoglobin", 150.0)
        assert len(flags) > 0
        assert any(flag.flag_type == "decimal_error" for flag in flags)
        assert any("decimal point error" in flag.reason.lower() for flag in flags)

    def test_decimal_error_low(self):
        """Test detection of decimal point error (value too low)."""
        # Hemoglobin of 1.5 g/dL should trigger decimal error (likely meant 15.0)
        flags = self.qc.check_clerical_errors("Hemoglobin", 1.5)
        assert len(flags) > 0
        assert any(flag.flag_type == "decimal_error" for flag in flags)

    def test_unit_error(self):
        """Test detection of unit conversion error."""
        # Hemoglobin of 1500 should trigger unit error
        flags = self.qc.check_clerical_errors("Hemoglobin", 1500.0)
        assert len(flags) > 0
        assert any(flag.flag_type == "unit_error" for flag in flags)
        assert any("unit error" in flag.reason.lower() for flag in flags)

    def test_validate_result_all_normal(self):
        """Test comprehensive validation with normal result."""
        flags = self.qc.validate_result("Hemoglobin", 15.0, previous_value=14.5)
        assert len(flags) == 0  # No flags for completely normal result

    def test_validate_result_out_of_range(self):
        """Test validation flags out of range value."""
        flags = self.qc.validate_result("Hemoglobin", 12.0)
        assert len(flags) > 0
        assert any(flag.flag_type == "out_of_range" for flag in flags)

    def test_validate_result_critical(self):
        """Test validation flags critical value."""
        flags = self.qc.validate_result("Hemoglobin", 6.0)
        assert len(flags) > 0
        assert any(flag.flag_type == "critical" for flag in flags)
        assert self.qc.has_unresolved_critical_flags(flags) is True

    def test_validate_result_with_delta(self):
        """Test validation includes delta check."""
        flags = self.qc.validate_result("Hemoglobin", 16.0, previous_value=13.0)
        assert len(flags) > 0
        assert any(flag.flag_type == "delta" for flag in flags)

    def test_validate_result_decimal_error(self):
        """Test validation detects decimal errors."""
        flags = self.qc.validate_result("Hemoglobin", 150.0)
        assert len(flags) > 0
        assert any(flag.flag_type in ["decimal_error", "unit_error"] for flag in flags)

    def test_seeded_clerical_errors_glucose(self):
        """Test detection of clerical errors in glucose values."""
        # Normal fasting glucose: 70-99 mg/dL

        # Test 1: Decimal error - 700 instead of 70
        flags = self.qc.validate_result("Glucose Fasting", 700.0)
        assert len(flags) > 0, "Should detect decimal/unit error for 700"

        # Test 2: Decimal error - 9 instead of 90
        flags = self.qc.validate_result("Glucose Fasting", 9.0)
        assert len(flags) > 0, "Should detect decimal error for 9"

        # Test 3: Normal value
        flags = self.qc.validate_result("Glucose Fasting", 85.0)
        assert len(flags) == 0, "Normal glucose should have no flags"

    def test_seeded_clerical_errors_potassium(self):
        """Test detection of clerical errors in potassium values."""
        # Normal potassium: 3.5-5.1 mmol/L

        # Test 1: Decimal error - 35 instead of 3.5
        flags = self.qc.validate_result("Potassium", 35.0)
        assert len(flags) > 0, "Should detect decimal error for 35"

        # Test 2: Decimal error - 0.45 instead of 4.5
        flags = self.qc.validate_result("Potassium", 0.45)
        assert len(flags) > 0, "Should detect decimal error for 0.45"

    def test_95_percent_detection_rate(self):
        """Test that ≥95% of seeded clerical errors are detected."""
        # Generate 100 test cases with known errors
        test_cases = []

        # Hemoglobin errors
        for i in range(20):
            test_cases.append(("Hemoglobin", 150.0 + i))  # Decimal errors
        for i in range(10):
            test_cases.append(("Hemoglobin", 1.0 + i * 0.1))  # Decimal errors (too low)

        # Glucose errors
        for i in range(20):
            test_cases.append(("Glucose Fasting", 500.0 + i * 10))  # Decimal/unit errors
        for i in range(10):
            test_cases.append(("Glucose Fasting", 5.0 + i * 0.5))  # Decimal errors (too low)

        # Potassium errors
        for i in range(20):
            test_cases.append(("Potassium", 30.0 + i))  # Decimal errors
        for i in range(20):
            test_cases.append(("Potassium", 0.3 + i * 0.01))  # Decimal errors (too low)

        # Run validation on all test cases
        detected = 0
        for test_name, value in test_cases:
            flags = self.qc.validate_result(test_name, value)
            if any(flag.flag_type in ["decimal_error", "unit_error", "critical"] for flag in flags):
                detected += 1

        detection_rate = (detected / len(test_cases)) * 100
        assert detection_rate >= 95.0, f"Detection rate {detection_rate:.1f}% is below 95%"

    def test_has_unresolved_critical_flags(self):
        """Test detection of unresolved critical flags."""
        flags = self.qc.validate_result("Hemoglobin", 6.0)
        assert self.qc.has_unresolved_critical_flags(flags) is True

        flags = self.qc.validate_result("Hemoglobin", 12.0)  # Out of range but not critical
        assert self.qc.has_unresolved_critical_flags(flags) is False
