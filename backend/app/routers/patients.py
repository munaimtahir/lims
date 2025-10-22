"""Patients router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..database import get_db, engine, Base
from ..models.patient import Patient

router = APIRouter(prefix="/patients", tags=["patients"])

# Create tables on import
Base.metadata.create_all(bind=engine)


class PatientCreate(BaseModel):
    """Schema for creating a patient."""
    name: str
    age: int
    gender: str
    contact: str | None = None


class PatientResponse(BaseModel):
    """Schema for patient response."""
    id: int
    name: str
    age: int
    gender: str
    contact: str | None = None

    class Config:
        from_attributes = True


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient."""
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient


@router.get("", response_model=List[PatientResponse])
async def list_patients(db: Session = Depends(get_db)):
    """List all patients."""
    patients = db.query(Patient).all()
    return patients
