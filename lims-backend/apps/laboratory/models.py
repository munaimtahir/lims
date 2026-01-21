"""
Laboratory test catalog models: Categories, Tests, Parameters, and Panels.

This module includes both the simplified models (Test, TestParameter) for basic use
and the comprehensive models (Parameter, ParameterReferenceRange, ParameterQuickText) for
advanced laboratory workflows with Excel import support.
"""

from django.db import models


class TestCategory(models.Model):
    """
    Represents a category for organizing laboratory tests.

    Examples: Hematology, Clinical Chemistry, Microbiology.

    Attributes:
        name (str): The unique name of the category.
        description (str, optional): A brief description of the category.
        is_active (bool): Whether the category is currently in use.
        created_at (datetime): The timestamp of when the category was created.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_categories"
        verbose_name = "Test Category"
        verbose_name_plural = "Test Categories"
        ordering = ["name"]

    def __str__(self):
        """
        Return the name of the test category.

        Returns:
            str: The name of the category.
        """
        return self.name


class Test(models.Model):
    """
    Represents an individual laboratory test.

    Attributes:
        test_id (int): Primary key, internal system identifier.
        test_code (str): A unique code for the test.
        legacy_test_code (str, optional): Original numeric or old code for backward compatibility.
        test_name (str): The full name of the test.
        category (TestCategory): The category this test belongs to.
        # ... other attributes ...
    """

    test_id = models.AutoField(primary_key=True)
    test_code = models.CharField(max_length=20, unique=True, db_index=True)
    legacy_test_code = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    test_name = models.CharField(max_length=200)
    
    category = models.ForeignKey(
        TestCategory, on_delete=models.PROTECT, related_name="tests"
    )
    loinc_code = models.CharField(max_length=20, blank=True, null=True)

    # Sample requirements
    sample_type = models.CharField(max_length=100)
    sample_volume = models.CharField(max_length=50, blank=True, null=True)

    # Pricing and timing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    turnaround_time = models.IntegerField(help_text="Turnaround time in hours")

    # Additional info
    instructions = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tests"
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        ordering = ["test_code"]
        indexes = [
            models.Index(fields=["test_code"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        """
        Return a string representation of the test.

        Returns:
            str: A string in the format "test_code - test_name".
        """
        return f"{self.test_code} - {self.test_name}"


class TestParameter(models.Model):
    """
    Junction table representing the mapping between a Test and a Parameter.

    Attributes:
        test (Test): The test in the relationship.
        parameter (Parameter): The global parameter in the relationship.
        display_order (int): The order in which the parameter is displayed for this test.
        reportable (bool): Whether the parameter is shown on the final report.
    """

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="test_parameters")
    parameter = models.ForeignKey("Parameter", on_delete=models.CASCADE, related_name="test_mappings")
    display_order = models.IntegerField(default=0)
    reportable = models.BooleanField(default=True)

    # Legacy field preserved for backward compatibility/migration
    parameter_name = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "test_parameters"
        verbose_name = "Test Parameter Mapping"
        verbose_name_plural = "Test Parameter Mappings"
        unique_together = [["test", "parameter"]]
        ordering = ["test", "display_order"]

    def __str__(self):
        """Return a string representation of the test-parameter relationship."""
        return f"{self.test.test_code} - {self.parameter.parameter_id}"

    @property
    def effective_parameter_name(self):
        """Returns parameter name from linked Parameter or legacy field."""
        return self.parameter.parameter_name if self.parameter else self.parameter_name

    @property
    def unit(self):
        """Returns unit from linked Parameter."""
        return self.parameter.unit if self.parameter else ""


class ReferenceRange(models.Model):
    """
    Represents a reference range for a test parameter with age and gender specificity.
    
    Supports versioning and age-specific ranges. Multiple ranges can exist for the same
    parameter with different age groups.
    
    Attributes:
        parameter (TestParameter): The parameter this range applies to.
        age_min (int, optional): Minimum age in years (null means no minimum).
        age_max (int, optional): Maximum age in years (null means no maximum).
        gender (str): Gender this range applies to (Male, Female, or Both).
        reference_min (Decimal): Minimum reference value.
        reference_max (Decimal): Maximum reference value.
        critical_low (Decimal, optional): Critical low value.
        critical_high (Decimal, optional): Critical high value.
        version (int): Version number for tracking changes.
        is_active (bool): Whether this range is currently active.
        effective_date (date): When this range became effective.
        notes (str, optional): Notes about this range.
        created_at (datetime): When this range was created.
        created_by (User, optional): User who created this range.
    """
    
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Both", "Both"),
    ]
    
    parameter = models.ForeignKey(
        TestParameter, on_delete=models.CASCADE, related_name="reference_ranges"
    )
    
    # Age range (in years)
    age_min = models.IntegerField(null=True, blank=True, help_text="Minimum age in years (null = no minimum)")
    age_max = models.IntegerField(null=True, blank=True, help_text="Maximum age in years (null = no maximum)")
    
    # Gender
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Both")
    
    # Reference values
    reference_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reference_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    # Critical values
    critical_low = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    critical_high = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    
    # Versioning
    version = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(auto_now_add=True)
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reference_ranges_created",
    )
    
    class Meta:
        db_table = "reference_ranges"
        verbose_name = "Reference Range"
        verbose_name_plural = "Reference Ranges"
        ordering = ["parameter", "age_min", "gender", "-version"]
        indexes = [
            models.Index(fields=["parameter", "is_active"]),
            models.Index(fields=["parameter", "gender", "age_min", "age_max"]),
        ]
        unique_together = [
            ("parameter", "age_min", "age_max", "gender", "version"),
        ]
    
    def __str__(self):
        """Return string representation."""
        age_str = ""
        if self.age_min is not None or self.age_max is not None:
            min_age = self.age_min if self.age_min is not None else "0"
            max_age = self.age_max if self.age_max is not None else "∞"
            age_str = f" (Age: {min_age}-{max_age})"
        return f"{self.parameter.parameter_name} - {self.gender}{age_str} v{self.version}"
    
    def clean(self):
        """Validate the reference range."""
        from django.core.exceptions import ValidationError
        
        if self.age_min is not None and self.age_max is not None:
            if self.age_min >= self.age_max:
                raise ValidationError("age_min must be less than age_max")
        
        if self.reference_min is not None and self.reference_max is not None:
            if self.reference_min >= self.reference_max:
                raise ValidationError("reference_min must be less than reference_max")


class TestPanel(models.Model):
    """
    Represents a test panel that groups multiple tests together.

    Attributes:
        panel_code (str): A unique code for the panel.
        panel_name (str): The full name of the panel.
        category (TestCategory): The category this panel belongs to.
        sample_type (str): The required sample type for the panel.
        sample_volume (str, optional): The required sample volume for the panel.
        price (Decimal): The price of the panel.
        turnaround_time (int): The expected turnaround time in hours.
        tests (ManyToManyField): The tests included in this panel.
        description (str, optional): A brief description of the panel.
        is_active (bool): Whether the panel is currently available.
        created_at (datetime): The timestamp of when the panel was created.
        updated_at (datetime): The timestamp of the last update.
    """

    panel_code = models.CharField(max_length=20, unique=True, db_index=True)
    panel_name = models.CharField(max_length=200)
    category = models.ForeignKey(
        TestCategory, on_delete=models.PROTECT, related_name="panels"
    )

    # Sample requirements
    sample_type = models.CharField(max_length=100)
    sample_volume = models.CharField(max_length=50, blank=True, null=True)

    # Pricing and timing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    turnaround_time = models.IntegerField(help_text="Turnaround time in hours")

    # Panel composition
    tests = models.ManyToManyField(Test, related_name="panels")

    # Additional info
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_panels"
        verbose_name = "Test Panel"
        verbose_name_plural = "Test Panels"
        ordering = ["panel_code"]
        indexes = [
            models.Index(fields=["panel_code"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        """
        Return a string representation of the test panel.

        Returns:
            str: A string in the format "panel_code - panel_name".
        """
        return f"{self.panel_code} - {self.panel_name}"


class Parameter(models.Model):
    """
    Represents a global parameter or analyte that can be measured in any test.

    Attributes:
        parameter_id (str): Primary key (e.g., 'p1', 'p2').
        parameter_name (str): The full name of the parameter.
        unit (str, optional): The unit of measurement for the parameter.
        data_type (str): The data type of the result (e.g., "Numeric", "Text").
        # ... other attributes ...
    """

    parameter_id = models.CharField(max_length=100, primary_key=True)
    parameter_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    
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
        verbose_name = "Parameter"
        verbose_name_plural = "Parameters"
        ordering = ["parameter_id"]
        indexes = [
            models.Index(fields=["parameter_id"]),
            models.Index(fields=["active"]),
        ]

    def __str__(self):
        """Return a string representation of the parameter."""
        return f"{self.parameter_id} - {self.parameter_name}"


class ParameterReferenceRange(models.Model):
    """
    Represents a reference range for a parameter (legacy Parameter model).

    This model defines normal and critical ranges for parameters based on
    various factors like sex, age, and method. Supports Excel import.

    Attributes:
        parameter (Parameter): The parameter the reference range belongs to.
        method_code (str): The code for the method used.
        sex (str): The sex the reference range applies to (M, F, All).
        age_min (int): The minimum age for the reference range.
        age_max (int): The maximum age for the reference range.
        age_unit (str): The unit for the age range (e.g., "Years", "Months", "Days").
        population_group (str): The population group for the range.
        unit (str): The unit of measurement for the range values.
        normal_low (Decimal): The normal low value.
        normal_high (Decimal): The normal high value.
        critical_low (Decimal): The critical low value.
        critical_high (Decimal): The critical high value.
        reference_text (str): A textual representation of the reference range.
        effective_from (date): The date the range becomes effective.
        effective_to (date): The date the range ceases to be effective.
    """

    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("All", "All"),
    ]

    AGE_UNIT_CHOICES = [
        ("Years", "Years"),
        ("Months", "Months"),
        ("Days", "Days"),
    ]

    parameter = models.ForeignKey(
        "Parameter", on_delete=models.CASCADE, related_name="legacy_reference_ranges"
    )
    method_code = models.CharField(max_length=50, blank=True)
    sex = models.CharField(max_length=20, choices=SEX_CHOICES, default="All")
    age_min = models.IntegerField(default=0)
    age_max = models.IntegerField(default=999)
    age_unit = models.CharField(max_length=20, choices=AGE_UNIT_CHOICES, default="Years")
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
        db_table = "parameter_reference_ranges"
        verbose_name = "Reference Range"
        verbose_name_plural = "Reference Ranges"
        ordering = ["parameter", "age_min"]
        indexes = [
            models.Index(fields=["parameter", "sex", "age_min"]),
        ]

    def __str__(self):
        """Return a string representation of the reference range."""
        return (
            f"{self.parameter.code} - {self.sex} "
            f"({self.age_min}-{self.age_max} {self.age_unit})"
        )


class ParameterQuickText(models.Model):
    """
    Represents quick text templates for parameter results.

    This model provides predefined text templates for result entry,
    supporting Excel import functionality.

    Attributes:
        parameter (Parameter): The parameter the quick text belongs to.
        template_title (str): The title of the template.
        template_body (str): The body of the template.
        language (str): The language of the template.
        is_default (bool): Whether this is the default template.
        active (bool): Whether the template is currently active.
    """

    parameter = models.ForeignKey(
        "Parameter", on_delete=models.CASCADE, related_name="quick_texts"
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
        verbose_name = "Parameter Quick Text"
        verbose_name_plural = "Parameter Quick Texts"
        unique_together = [["parameter", "template_title", "language"]]
        ordering = ["parameter", "template_title"]
        indexes = [
            models.Index(fields=["parameter"]),
        ]

    def __str__(self):
        """Return a string representation of the quick text template."""
        return f"{self.parameter.code} - {self.template_title}"


class TestParameterLink(models.Model):
    """
    Represents the relationship between a Test and a Parameter.

    This model links tests to their constituent parameters, supporting
    the Excel import structure where tests and parameters are separate entities.

    Attributes:
        test (Test): The test in the relationship.
        parameter (Parameter): The parameter in the relationship.
        display_order (int): The order in which the parameter is displayed.
        section_header (str): A header for a section of parameters.
        is_mandatory (bool): Whether the parameter is mandatory for the test.
        show_on_report (bool): Whether the parameter is shown on the report.
        default_reference_profile_id (str): The default reference profile ID.
        delta_check_enabled (bool): Whether delta check is enabled.
        panic_low_override (Decimal): An override for the panic low value.
        panic_high_override (Decimal): An override for the panic high value.
        comment_template_id (str): The ID of a comment template.
    """

    test = models.ForeignKey(
        Test, on_delete=models.CASCADE, related_name="parameter_links"
    )
    parameter = models.ForeignKey(
        "Parameter", on_delete=models.CASCADE, related_name="test_links"
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
        db_table = "test_parameter_links"
        verbose_name = "Test Parameter Link"
        verbose_name_plural = "Test Parameter Links"
        unique_together = [["test", "parameter"]]
        ordering = ["test", "display_order"]
        indexes = [
            models.Index(fields=["test", "display_order"]),
        ]

    def __str__(self):
        """Return a string representation of the test-parameter relationship."""
        return f"{self.test.test_code} - {self.parameter.code}"
