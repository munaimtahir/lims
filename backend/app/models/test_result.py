"""Test result model."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from datetime import datetime
from ..database import Base


class TestResult(Base):
    """Test result table model."""
    
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    test_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    units = Column(String, nullable=False)
    performed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    performed_by = Column(String, nullable=False)  # Technician name
    
    # QC flags stored as JSON
    qc_flags = Column(Text, nullable=True)  # JSON array of flags
    has_critical_flags = Column(Boolean, default=False, nullable=False)
    
    # Verification/release status
    verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    released = Column(Boolean, default=False, nullable=False)
    released_by = Column(String, nullable=True)
    released_at = Column(DateTime, nullable=True)
    
    # Comments/notes
    notes = Column(Text, nullable=True)
