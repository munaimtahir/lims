"""Voice registration router."""

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from lims.database import get_db
from lims.models.voice_event import VoiceEvent
from lims.services.voice_mapping import VoiceMapping

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceTranscriptRequest(BaseModel):
    """Schema for voice transcript request."""

    transcript: str
    user: str = "anonymous"
    action_type: str = "registration"


class VoiceTranscriptResponse(BaseModel):
    """Schema for voice transcript response."""

    fields: dict[str, Any]
    confidences: dict[str, float]
    overall_confidence: float
    requires_confirmation: bool
    requires_manual: bool


@router.post("/map", response_model=VoiceTranscriptResponse)
async def map_voice_transcript(request: VoiceTranscriptRequest, db: Session = Depends(get_db)):
    """
    Map voice transcript to patient fields with confidence scoring.

    Confidence thresholds:
    - ≥0.9: Auto-accept (requires_confirmation=False)
    - 0.6-0.89: Requires confirmation (requires_confirmation=True)
    - <0.6: Requires manual entry (requires_manual=True)
    """
    # Map the transcript
    result = VoiceMapping.map_transcript(request.transcript)

    # Determine if confirmation or manual entry is needed
    overall_conf = result["overall_confidence"]
    requires_confirmation = 0.6 <= overall_conf < 0.9
    requires_manual = overall_conf < 0.6

    # Store audit record
    voice_event = VoiceEvent(
        user=request.user,
        transcript=request.transcript,
        mapping=json.dumps(result["fields"]),
        confidences=json.dumps(result["confidences"]),
        timestamp=datetime.utcnow(),
        action_type=request.action_type,
    )
    db.add(voice_event)
    db.commit()

    return {
        "fields": result["fields"],
        "confidences": result["confidences"],
        "overall_confidence": overall_conf,
        "requires_confirmation": requires_confirmation,
        "requires_manual": requires_manual,
    }


@router.get("/events")
async def list_voice_events(limit: int = 50, db: Session = Depends(get_db)):
    """List recent voice events for audit purposes."""
    events = db.query(VoiceEvent).order_by(VoiceEvent.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": event.id,
            "user": event.user,
            "transcript": event.transcript,
            "mapping": json.loads(event.mapping) if event.mapping else {},
            "confidences": json.loads(event.confidences) if event.confidences else {},
            "timestamp": event.timestamp.isoformat(),
            "action_type": event.action_type,
        }
        for event in events
    ]
