"""Utility functions for settings app."""

from .models import WorkflowSettings


def get_workflow_settings():
    """Get current workflow settings."""
    return WorkflowSettings.load()


def should_skip_sample_collection():
    """Check if sample collection step should be skipped."""
    settings = get_workflow_settings()
    return not settings.enable_sample_collection


def should_skip_sample_receive():
    """Check if sample receive step should be skipped."""
    settings = get_workflow_settings()
    return not settings.enable_sample_receive


def should_skip_verification():
    """Check if verification step should be skipped."""
    settings = get_workflow_settings()
    return not settings.enable_verification
