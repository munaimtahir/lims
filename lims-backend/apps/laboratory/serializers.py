from rest_framework import serializers
from django.db import models
from .models import TestCategory, Test, Parameter, TestParameter, TestPanel, ReferenceRange


class TestCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the TestCategory model.
    """

    class Meta:
        model = TestCategory
        fields = "__all__"


class ParameterSerializer(serializers.ModelSerializer):
    """
    Serializer for the global Parameter model with parameter_id validation.
    """

    class Meta:
        model = Parameter
        fields = "__all__"
    
    def validate_parameter_id(self, value):
        """
        Validate parameter_id format and normalize to lowercase.
        """
        from .models import validate_parameter_id
        
        if not value:
            raise serializers.ValidationError("parameter_id cannot be empty")
        
        try:
            normalized = validate_parameter_id(value)
            return normalized
        except Exception as e:
            raise serializers.ValidationError(str(e))


class TestParameterSerializer(serializers.ModelSerializer):
    """
    Serializer for the TestParameter junction model.
    """
    parameter_name = serializers.CharField(source="parameter.parameter_name", read_only=True)
    unit = serializers.CharField(source="parameter.unit", read_only=True)

    class Meta:
        model = TestParameter
        fields = ["parameter", "parameter_name", "unit", "display_order", "reportable"]


class TestSerializer(serializers.ModelSerializer):
    """
    Serializer for the Test model.

    Includes nested serialization for test parameters and the category name.
    """

    parameters = TestParameterSerializer(source="test_parameters", many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Test
        fields = [
            "test_id",
            "test_code",
            "legacy_test_code",
            "test_name",
            "category",
            "category_name",
            "sample_type",
            "sample_volume",
            "price",
            "turnaround_time",
            "is_active",
            "parameters",
        ]


class TestPanelSerializer(serializers.ModelSerializer):
    """
    Serializer for the TestPanel model.

    Includes nested serialization for the tests within the panel and the category name.
    Provides a write-only field `test_ids` for associating tests with the panel.
    """

    tests = TestSerializer(many=True, read_only=True)
    test_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Test.objects.all(), source="tests"
    )
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = TestPanel
        fields = "__all__"


class ReferenceRangeSerializer(serializers.ModelSerializer):
    """
    Serializer for the ReferenceRange model.
    
    Includes parameter details for easier display.
    """
    
    parameter_name = serializers.CharField(source="parameter.parameter.parameter_name", read_only=True)
    test_name = serializers.CharField(source="parameter.test.test_name", read_only=True)
    test_code = serializers.CharField(source="parameter.test.test_code", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    
    class Meta:
        model = ReferenceRange
        fields = [
            "id",
            "parameter",
            "parameter_name",
            "test_name",
            "test_code",
            "age_min",
            "age_max",
            "gender",
            "reference_min",
            "reference_max",
            "critical_low",
            "critical_high",
            "version",
            "is_active",
            "effective_date",
            "notes",
            "created_at",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["created_at", "version"]
    
    def validate(self, data):
        """Validate reference range data."""
        age_min = data.get("age_min")
        age_max = data.get("age_max")
        ref_min = data.get("reference_min")
        ref_max = data.get("reference_max")
        
        if age_min is not None and age_max is not None:
            if age_min >= age_max:
                raise serializers.ValidationError({
                    "age_max": "Maximum age must be greater than minimum age."
                })
        
        if ref_min is not None and ref_max is not None:
            if ref_min >= ref_max:
                raise serializers.ValidationError({
                    "reference_max": "Maximum reference value must be greater than minimum value."
                })
        
        return data
    
    def create(self, validated_data):
        """Create a new reference range with versioning."""
        # Get the latest version for this parameter/age/gender combination
        parameter = validated_data["parameter"]
        age_min = validated_data.get("age_min")
        age_max = validated_data.get("age_max")
        gender = validated_data.get("gender", "Both")
        
        # Deactivate old ranges for the same parameter/age/gender
        old_ranges = ReferenceRange.objects.filter(
            parameter=parameter,
            age_min=age_min,
            age_max=age_max,
            gender=gender,
            is_active=True
        )
        old_ranges.update(is_active=False)
        
        # Get next version number
        max_version = ReferenceRange.objects.filter(
            parameter=parameter,
            age_min=age_min,
            age_max=age_max,
            gender=gender
        ).aggregate(max_version=models.Max("version"))["max_version"] or 0
        
        validated_data["version"] = max_version + 1
        
        # Set created_by if available
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        
        return super().create(validated_data)
