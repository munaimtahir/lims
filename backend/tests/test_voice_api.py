"""Tests for voice API endpoints."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_voice.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_map_voice_transcript_high_confidence():
    """Test voice mapping with high confidence."""
    # Clean up before test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    response = client.post(
        "/voice/map",
        json={
            "transcript": "Patient name is John Smith age 35 male contact 555-1234",
            "user": "test_user",
            "action_type": "registration"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "fields" in data
    assert "confidences" in data
    assert "overall_confidence" in data
    assert data["overall_confidence"] >= 0.85
    assert data["requires_confirmation"] is False
    assert data["requires_manual"] is False
    
    # Verify fields extracted
    assert "name" in data["fields"]
    assert "age" in data["fields"]
    assert data["fields"]["age"] == 35


def test_map_voice_transcript_medium_confidence():
    """Test voice mapping with medium confidence (requires confirmation)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    response = client.post(
        "/voice/map",
        json={
            "transcript": "John Doe 40 maybe male",
            "user": "test_user",
            "action_type": "registration"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Medium confidence should require confirmation
    if 0.6 <= data["overall_confidence"] < 0.9:
        assert data["requires_confirmation"] is True
        assert data["requires_manual"] is False


def test_map_voice_transcript_low_confidence():
    """Test voice mapping with low confidence (requires manual)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    response = client.post(
        "/voice/map",
        json={
            "transcript": "Um patient maybe",
            "user": "test_user",
            "action_type": "registration"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Low confidence should require manual entry
    if data["overall_confidence"] < 0.6:
        assert data["requires_manual"] is True


def test_list_voice_events():
    """Test listing voice events for audit."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a couple of voice events
    client.post(
        "/voice/map",
        json={
            "transcript": "Patient name is Alice Brown age 30 female",
            "user": "user1",
            "action_type": "registration"
        }
    )
    client.post(
        "/voice/map",
        json={
            "transcript": "Patient name is Bob Johnson age 45 male",
            "user": "user2",
            "action_type": "registration"
        }
    )
    
    # Get events list
    response = client.get("/voice/events")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 2
    assert "transcript" in data[0]
    assert "user" in data[0]
    assert "timestamp" in data[0]


def test_voice_audit_trail():
    """Test that voice events are properly audited."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    transcript = "Patient name is Test User age 50 male"
    
    response = client.post(
        "/voice/map",
        json={
            "transcript": transcript,
            "user": "audit_test_user",
            "action_type": "registration"
        }
    )
    
    assert response.status_code == 200
    
    # Verify audit record was created
    events = client.get("/voice/events").json()
    assert len(events) >= 1
    
    latest_event = events[0]
    assert latest_event["transcript"] == transcript
    assert latest_event["user"] == "audit_test_user"
    assert latest_event["action_type"] == "registration"
    assert "mapping" in latest_event
    assert "confidences" in latest_event
