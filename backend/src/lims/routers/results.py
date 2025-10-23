"""Results router for test result entry and QC validation."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lims.database import get_db
from lims.models.test_result import TestResult
from lims.services.qc_rules import QCRulesService

router = APIRouter(prefix="/results", tags=["results"])

# Initialize QC rules service
qc_service = QCRulesService()


class ResultCreate(BaseModel):
    """Schema for creating a test result."""

    patient_id: int
    test_name: str
    value: float
    units: str
    performed_by: str
    notes: str | None = None
    check_previous: bool = True  # Whether to run delta checks


class QCFlagResponse(BaseModel):
    """Schema for QC flag response."""

    flag_type: str
    severity: str
    test_name: str
    value: float
    expected_range: str
    reason: str
    requires_resolution: bool


class ResultResponse(BaseModel):
    """Schema for result response."""

    model_config = {"from_attributes": True}

    id: int
    patient_id: int
    test_name: str
    value: float
    units: str
    performed_at: datetime
    performed_by: str
    qc_flags: list[QCFlagResponse]
    has_critical_flags: bool
    verified: bool
    released: bool
    notes: str | None = None


@router.post("", response_model=ResultResponse, status_code=201)
async def create_result(result: ResultCreate, db: Session = Depends(get_db)):
    """
    Create a new test result with automatic QC validation.

    Returns the result with any QC flags that were detected.
    Critical flags prevent the result from being released until resolved.
    """
    # Get previous result for delta check if requested
    previous_value = None
    if result.check_previous:
        previous_result = (
            db.query(TestResult)
            .filter(
                TestResult.patient_id == result.patient_id, TestResult.test_name == result.test_name
            )
            .order_by(TestResult.performed_at.desc())
            .first()
        )
        if previous_result:
            previous_value = previous_result.value

    # Run QC validation
    flags = qc_service.validate_result(
        test_name=result.test_name, value=result.value, previous_value=previous_value
    )

    # Convert flags to dict for JSON storage
    flags_dict = [
        {
            "flag_type": flag.flag_type,
            "severity": flag.severity,
            "test_name": flag.test_name,
            "value": flag.value,
            "expected_range": flag.expected_range,
            "reason": flag.reason,
            "requires_resolution": flag.requires_resolution,
        }
        for flag in flags
    ]

    # Check for critical flags
    has_critical = qc_service.has_unresolved_critical_flags(flags)

    # Create result record
    db_result = TestResult(
        patient_id=result.patient_id,
        test_name=result.test_name,
        value=result.value,
        units=result.units,
        performed_by=result.performed_by,
        notes=result.notes,
        qc_flags=json.dumps(flags_dict),
        has_critical_flags=has_critical,
        performed_at=datetime.utcnow(),
    )

    db.add(db_result)
    db.commit()
    db.refresh(db_result)

    # Return response with parsed flags
    return {
        "id": db_result.id,
        "patient_id": db_result.patient_id,
        "test_name": db_result.test_name,
        "value": db_result.value,
        "units": db_result.units,
        "performed_at": db_result.performed_at,
        "performed_by": db_result.performed_by,
        "qc_flags": flags_dict,
        "has_critical_flags": db_result.has_critical_flags,
        "verified": db_result.verified,
        "released": db_result.released,
        "notes": db_result.notes,
    }


@router.get("", response_model=list[ResultResponse])
async def list_results(
    patient_id: int | None = None,
    test_name: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List test results with optional filtering."""
    query = db.query(TestResult)

    if patient_id:
        query = query.filter(TestResult.patient_id == patient_id)

    if test_name:
        query = query.filter(TestResult.test_name == test_name)

    results = query.order_by(TestResult.performed_at.desc()).limit(limit).all()

    # Parse QC flags for each result
    response = []
    for result in results:
        flags = json.loads(result.qc_flags) if result.qc_flags else []
        response.append(
            {
                "id": result.id,
                "patient_id": result.patient_id,
                "test_name": result.test_name,
                "value": result.value,
                "units": result.units,
                "performed_at": result.performed_at,
                "performed_by": result.performed_by,
                "qc_flags": flags,
                "has_critical_flags": result.has_critical_flags,
                "verified": result.verified,
                "released": result.released,
                "notes": result.notes,
            }
        )

    return response


@router.post("/{result_id}/verify")
async def verify_result(result_id: int, verified_by: str, db: Session = Depends(get_db)):
    """Mark result as verified by a technician."""
    result = db.query(TestResult).filter(TestResult.id == result_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    result.verified = True
    result.verified_by = verified_by
    result.verified_at = datetime.utcnow()

    db.commit()

    return {"message": "Result verified", "id": result_id}


@router.post("/{result_id}/release")
async def release_result(result_id: int, released_by: str, db: Session = Depends(get_db)):
    """
    Release result for reporting.
    Cannot release if there are unresolved critical flags.
    """
    result = db.query(TestResult).filter(TestResult.id == result_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    if result.has_critical_flags:
        raise HTTPException(
            status_code=400, detail="Cannot release result with unresolved critical flags"
        )

    if not result.verified:
        raise HTTPException(status_code=400, detail="Result must be verified before release")

    result.released = True
    result.released_by = released_by
    result.released_at = datetime.utcnow()

    db.commit()

    return {"message": "Result released", "id": result_id}
