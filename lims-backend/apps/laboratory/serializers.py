from rest_framework import serializers
from .models import TestCategory, Test, TestParameter, TestPanel


class TestCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the TestCategory model.
    """

    class Meta:
        model = TestCategory
        fields = "__all__"


class TestParameterSerializer(serializers.ModelSerializer):
    """
    Serializer for the TestParameter model.
    """

    class Meta:
        model = TestParameter
        fields = "__all__"


class TestSerializer(serializers.ModelSerializer):
    """
    Serializer for the Test model.

    Includes nested serialization for test parameters and the category name.
    """

    parameters = TestParameterSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Test
        fields = "__all__"


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
