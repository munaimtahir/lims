"""
Laboratory test catalog models: Categories, Tests, Parameters, and Panels.
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
        category (TestCategory): The category this test belongs to.
        test_code (str): A unique code for the test.
        test_name (str): The full name of the test.
        loinc_code (str, optional): The LOINC code for the test.
        sample_type (str): The required sample type (e.g., "EDTA Blood", "Serum").
        sample_volume (str, optional): The required sample volume (e.g., "3-5 mL").
        price (Decimal): The price of the test.
        turnaround_time (int): The expected turnaround time in hours.
        instructions (str, optional): Any special instructions for the test.
        is_active (bool): Whether the test is currently available.
        created_at (datetime): The timestamp of when the test was created.
        updated_at (datetime): The timestamp of the last update.
    """

    category = models.ForeignKey(
        TestCategory, on_delete=models.PROTECT, related_name="tests"
    )
    test_code = models.CharField(max_length=20, unique=True, db_index=True)
    test_name = models.CharField(max_length=200)
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
    Represents a measurable parameter within a laboratory test.

    Each parameter includes reference ranges and critical values.

    Attributes:
        test (Test): The test this parameter belongs to.
        parameter_name (str): The name of the parameter.
        loinc_code (str, optional): The LOINC code for the parameter.
        unit (str): The unit of measurement for the parameter.
        reference_min_male (Decimal, optional): The minimum reference value for males.
        reference_max_male (Decimal, optional): The maximum reference value for males.
        reference_min_female (Decimal, optional): The minimum reference value for females.
        reference_max_female (Decimal, optional): The maximum reference value for females.
        critical_low (Decimal, optional): The critical low value for the parameter.
        critical_high (Decimal, optional): The critical high value for the parameter.
        decimal_places (int): The number of decimal places to display for the result.
        display_order (int): The order in which to display the parameter.
    """

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="parameters")
    parameter_name = models.CharField(max_length=200)
    loinc_code = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=50)

    # Reference ranges (gender-specific)
    reference_min_male = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reference_max_male = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reference_min_female = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    reference_max_female = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Critical values
    critical_low = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    critical_high = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Display settings
    decimal_places = models.IntegerField(default=2)
    display_order = models.IntegerField(default=0)

    class Meta:
        db_table = "test_parameters"
        verbose_name = "Test Parameter"
        verbose_name_plural = "Test Parameters"
        ordering = ["test", "display_order", "parameter_name"]

    def __str__(self):
        """
        Return a string representation of the test parameter.

        Returns:
            str: A string in the format "test_code - parameter_name".
        """
        return f"{self.test.test_code} - {self.parameter_name}"


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
