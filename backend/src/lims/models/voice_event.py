"""Voice event model for audit trail."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from lims.database import Base


class VoiceEvent(Base):
    """Voice event audit table."""

    __tablename__ = "voice_events"

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, nullable=False)  # User who performed the action
    transcript = Column(Text, nullable=False)  # Voice transcript
    mapping = Column(Text, nullable=True)  # JSON mapping of extracted fields
    confidences = Column(Text, nullable=True)  # JSON confidence scores
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    action_type = Column(String, nullable=False)  # 'registration', 'result_entry', etc.
