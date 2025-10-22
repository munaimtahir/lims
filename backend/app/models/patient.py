"""Patient model."""
from sqlalchemy import Column, Integer, String
from ..database import Base


class Patient(Base):
    """Patient table model."""
    
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    contact = Column(String, nullable=True)
