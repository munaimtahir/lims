"""Test catalog models."""

from django.db import models


class TestCatalog(models.Model):
    """Represents a single test available in the laboratory's catalog.

    This model stores all the essential information about a lab test that
    can be ordered.

    Attributes:
        code (CharField): A unique code for the test.
        name (CharField): The full name of the test.
        description (TextField): A detailed description of the test.
        category (CharField): The category the test belongs to (e.g., "Hematology").
        sample_type (CharField): The type of sample required (e.g., "Blood", "Urine").
        price (DecimalField): The price of the test.
        turnaround_time_hours (IntegerField): The expected turnaround time in hours.
        is_active (BooleanField): Whether the test is currently available.
        created_at (DateTimeField): The timestamp when the test was created.
        updated_at (DateTimeField): The timestamp when the test was last updated.
    """

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100)
    sample_type = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    turnaround_time_hours = models.IntegerField(help_text="Expected TAT in hours")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_catalog"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        """Returns a string representation of the test catalog item."""
        return f"{self.code} - {self.name}"


class Parameter(models.Model):
    """Represents a parameter or analyte that can be measured in a test.

    This model maps to the 'Parameters' sheet in the LIMS master data Excel file.

    Attributes:
        code (CharField): A unique code for the parameter.
        name (CharField): The full name of the parameter.
        short_name (CharField): A shorter name for the parameter.
        unit (CharField): The unit of measurement for the parameter.
        data_type (CharField): The data type of the result (e.g., "Numeric", "Text").
        editor_type (CharField): The type of editor to use for result entry.
        decimal_places (IntegerField): The number of decimal places for numeric results.
        allowed_values (TextField): A list of allowed values for the result.
        is_calculated (BooleanField): Whether the parameter is calculated from others.
        calculation_formula (TextField): The formula used for calculation.
        flag_direction (CharField): The direction for flagging abnormal results.
        has_quick_text (BooleanField): Whether the parameter has quick text templates.
        external_code_type (CharField): The type of external code (e.g., "LOINC").
        external_code_value (CharField): The value of the external code.
        active (BooleanField): Whether the parameter is currently in use.
        created_at (DateTimeField): The timestamp when the parameter was created.
        updated_at (DateTimeField): The timestamp when the parameter was last updated.
    """

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    data_type = models.CharField(max_length=50, default="Numeric")
    editor_type = models.CharField(max_length=50, default="Plain")
    decimal_places = models.IntegerField(default=2, null=True, blank=True)
    allowed_values = models.TextField(blank=True)
    is_calculated = models.BooleanField(default=False)
    calculation_formula = models.TextField(blank=True)
    flag_direction = models.CharField(max_length=20, default="Both")
    has_quick_text = models.BooleanField(default=False)
    external_code_type = models.CharField(max_length=50, blank=True)
    external_code_value = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parameters"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        """Returns a string representation of the parameter."""
        return f"{self.code} - {self.name}"


class Test(models.Model):
    """Represents a single test that can be ordered.

    This model maps to the 'Tests' sheet in the LIMS master data Excel file.

    Attributes:
        code (CharField): A unique code for the test.
        name (CharField): The full name of the test.
        short_name (CharField): A shorter name for the test.
        test_type (CharField): The type of test (e.g., "Single", "Profile").
        department (CharField): The department the test belongs to.
        specimen_type (CharField): The type of specimen required.
        container_type (CharField): The type of container for the specimen.
        result_scale (CharField): The scale of the result (e.g., "Quantitative").
        default_method (CharField): The default method used for the test.
        default_tat_minutes (IntegerField): The default turnaround time in minutes.
        default_print_group (CharField): The default print group for the report.
        default_report_template (CharField): The default report template.
        default_printer_code (CharField): The default printer code.
        billing_code (CharField): The billing code for the test.
        default_charge (DecimalField): The default charge for the test.
        external_code_type (CharField): The type of external code.
        external_code_value (CharField): The value of the external code.
        active (BooleanField): Whether the test is currently available.
        created_at (DateTimeField): The timestamp when the test was created.
        updated_at (DateTimeField): The timestamp when the test was last updated.
    """

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100, blank=True)
    test_type = models.CharField(max_length=50, default="Single")
    department = models.CharField(max_length=100, blank=True)
    specimen_type = models.CharField(max_length=100, blank=True)
    container_type = models.CharField(max_length=100, blank=True)
    result_scale = models.CharField(max_length=50, blank=True)
    default_method = models.CharField(max_length=100, blank=True)
    default_tat_minutes = models.IntegerField(default=0)
    default_print_group = models.CharField(max_length=100, blank=True)
    default_report_template = models.CharField(max_length=100, blank=True)
    default_printer_code = models.CharField(max_length=50, blank=True)
    billing_code = models.CharField(max_length=50, blank=True)
    default_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    external_code_type = models.CharField(max_length=50, blank=True)
    external_code_value = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tests"
        ordering = ["code"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        """Returns a string representation of the test."""
        return f"{self.code} - {self.name}"


class TestParameter(models.Model):
    """Represents the relationship between a test and a parameter.

    This model maps to the 'Test_Parameters' sheet in the LIMS master data Excel file,
    linking tests to their constituent parameters.

    Attributes:
        test (ForeignKey): The test in the relationship.
        parameter (ForeignKey): The parameter in the relationship.
        display_order (IntegerField): The order in which the parameter is displayed.
        section_header (CharField): A header for a section of parameters.
        is_mandatory (BooleanField): Whether the parameter is mandatory for the test.
        show_on_report (BooleanField): Whether the parameter is shown on the report.
        default_reference_profile_id (CharField): The default reference profile ID.
        delta_check_enabled (BooleanField): Whether delta check is enabled.
        panic_low_override (DecimalField): An override for the panic low value.
        panic_high_override (DecimalField): An override for the panic high value.
        comment_template_id (CharField): The ID of a comment template.
        created_at (DateTimeField): The timestamp when the relationship
            was created.
        updated_at (DateTimeField): The timestamp when the relationship
            was last updated.
    """

    test = models.ForeignKey(
        Test, on_delete=models.CASCADE, related_name="test_parameters"
    )
    parameter = models.ForeignKey(
        Parameter, on_delete=models.CASCADE, related_name="test_parameters"
    )
    display_order = models.IntegerField(default=0)
    section_header = models.CharField(max_length=255, blank=True)
    is_mandatory = models.BooleanField(default=True)
    show_on_report = models.BooleanField(default=True)
    default_reference_profile_id = models.CharField(max_length=50, blank=True)
    delta_check_enabled = models.BooleanField(default=False)
    panic_low_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    panic_high_override = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    comment_template_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_parameters"
        unique_together = [["test", "parameter"]]
        ordering = ["test", "display_order"]
        indexes = [
            models.Index(fields=["test", "display_order"]),
        ]

    def __str__(self):
        """Returns a string representation of the test-parameter relationship."""
        return f"{self.test.code} - {self.parameter.code}"


class ReferenceRange(models.Model):
    """Represents a reference range for a parameter.

    This model maps to the 'Reference_Ranges' sheet in the LIMS master data Excel file,
    defining normal and critical ranges for parameters based on various factors.

    Attributes:
        parameter (ForeignKey): The parameter the reference range belongs to.
        method_code (CharField): The code for the method used.
        sex (CharField): The sex the reference range applies to.
        age_min (IntegerField): The minimum age for the reference range.
        age_max (IntegerField): The maximum age for the reference range.
        age_unit (CharField): The unit for the age range (e.g., "Years").
        population_group (CharField): The population group for the range.
        unit (CharField): The unit of measurement for the range values.
        normal_low (DecimalField): The normal low value.
        normal_high (DecimalField): The normal high value.
        critical_low (DecimalField): The critical low value.
        critical_high (DecimalField): The critical high value.
        reference_text (TextField): A textual representation of the reference range.
        effective_from (DateField): The date the range becomes effective.
        effective_to (DateField): The date the range ceases to be effective.
        created_at (DateTimeField): The timestamp when the range was created.
        updated_at (DateTimeField): The timestamp when the range was last updated.
    """

    parameter = models.ForeignKey(
        Parameter, on_delete=models.CASCADE, related_name="reference_ranges"
    )
    method_code = models.CharField(max_length=50, blank=True)
    sex = models.CharField(max_length=20, default="All")
    age_min = models.IntegerField(default=0)
    age_max = models.IntegerField(default=999)
    age_unit = models.CharField(max_length=20, default="Years")
    population_group = models.CharField(max_length=50, default="Adult")
    unit = models.CharField(max_length=50, blank=True)
    normal_low = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    normal_high = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    critical_low = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    critical_high = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True
    )
    reference_text = models.TextField(blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reference_ranges"
        ordering = ["parameter", "age_min"]
        indexes = [
            models.Index(fields=["parameter", "sex", "age_min"]),
        ]

    def __str__(self):
        """Returns a string representation of the reference range."""
        return (
            f"{self.parameter.code} - {self.sex} "
            f"({self.age_min}-{self.age_max} {self.age_unit})"
        )


class ParameterQuickText(models.Model):
    """Represents quick text templates for parameter results.

    This model maps to the 'Parameter_Quick_Text' sheet in the LIMS
    master data Excel file, providing predefined text templates for
    result entry.

    Attributes:
        parameter (ForeignKey): The parameter the quick text belongs to.
        template_title (CharField): The title of the template.
        template_body (TextField): The body of the template.
        language (CharField): The language of the template.
        is_default (BooleanField): Whether this is the default template.
        active (BooleanField): Whether the template is currently active.
        created_at (DateTimeField): The timestamp when the template was created.
        updated_at (DateTimeField): The timestamp when the template was last updated.
    """

    parameter = models.ForeignKey(
        Parameter, on_delete=models.CASCADE, related_name="quick_texts"
    )
    template_title = models.CharField(max_length=255)
    template_body = models.TextField()
    language = models.CharField(max_length=10, default="EN")
    is_default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parameter_quick_texts"
        unique_together = [["parameter", "template_title", "language"]]
        ordering = ["parameter", "template_title"]
        indexes = [
            models.Index(fields=["parameter"]),
        ]

    def __str__(self):
        """Returns a string representation of the quick text template."""
        return f"{self.parameter.code} - {self.template_title}"
