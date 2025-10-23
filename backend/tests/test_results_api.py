"""Tests for results API endpoints."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_results.db"
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


def test_create_result_normal():
    """Test creating a result with normal values."""
    # Clean up
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a patient first
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male", "contact": "555-0000"}
    )
    patient_id = patient_response.json()["id"]
    
    # Create result
    response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 15.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["test_name"] == "Hemoglobin"
    assert data["value"] == 15.0
    assert len(data["qc_flags"]) == 0  # Normal value, no flags
    assert data["has_critical_flags"] is False


def test_create_result_out_of_range():
    """Test creating a result with out-of-range value."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 12.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["qc_flags"]) > 0
    assert any(flag["flag_type"] == "out_of_range" for flag in data["qc_flags"])
    assert data["has_critical_flags"] is False  # Out of range but not critical


def test_create_result_critical():
    """Test creating a result with critical value."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 6.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["qc_flags"]) > 0
    assert any(flag["flag_type"] == "critical" for flag in data["qc_flags"])
    assert data["has_critical_flags"] is True


def test_create_result_with_delta_check():
    """Test delta check between consecutive results."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    # Create first result
    client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 15.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    
    # Create second result with large delta
    response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 12.0,
            "units": "g/dL",
            "performed_by": "tech_001",
            "check_previous": True
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["qc_flags"]) > 0
    # Should have delta flag (change of 3.0 exceeds max of 2.0)
    assert any(flag["flag_type"] == "delta" for flag in data["qc_flags"])


def test_create_result_decimal_error():
    """Test detection of decimal point error."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 150.0,  # Likely meant 15.0
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["qc_flags"]) > 0
    # Should detect decimal or unit error
    assert any(flag["flag_type"] in ["decimal_error", "unit_error"] for flag in data["qc_flags"])


def test_list_results():
    """Test listing results."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    # Create multiple results
    for value in [15.0, 14.5, 15.2]:
        client.post(
            "/results",
            json={
                "patient_id": patient_id,
                "test_name": "Hemoglobin",
                "value": value,
                "units": "g/dL",
                "performed_by": "tech_001"
            }
        )
    
    # List all results
    response = client.get("/results")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_list_results_filtered():
    """Test listing results with filters."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 15.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    
    # Filter by patient
    response = client.get(f"/results?patient_id={patient_id}")
    assert response.status_code == 200
    data = response.json()
    assert all(r["patient_id"] == patient_id for r in data)


def test_verify_result():
    """Test verifying a result."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    result_response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 15.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    result_id = result_response.json()["id"]
    
    # Verify the result
    response = client.post(f"/results/{result_id}/verify?verified_by=supervisor_001")
    assert response.status_code == 200
    assert "verified" in response.json()["message"].lower()


def test_release_result_normal():
    """Test releasing a verified result with no critical flags."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    result_response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 15.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    result_id = result_response.json()["id"]
    
    # Verify first
    client.post(f"/results/{result_id}/verify?verified_by=supervisor_001")
    
    # Then release
    response = client.post(f"/results/{result_id}/release?released_by=pathologist_001")
    assert response.status_code == 200
    assert "released" in response.json()["message"].lower()


def test_release_result_with_critical_flags():
    """Test that releasing a result with critical flags is blocked."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    result_response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 6.0,  # Critical value
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    result_id = result_response.json()["id"]
    
    # Verify first
    client.post(f"/results/{result_id}/verify?verified_by=supervisor_001")
    
    # Try to release - should fail
    response = client.post(f"/results/{result_id}/release?released_by=pathologist_001")
    assert response.status_code == 400
    assert "critical flags" in response.json()["detail"].lower()


def test_release_result_not_verified():
    """Test that releasing an unverified result is blocked."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    patient_response = client.post(
        "/patients",
        json={"name": "Test Patient", "age": 45, "gender": "Male"}
    )
    patient_id = patient_response.json()["id"]
    
    result_response = client.post(
        "/results",
        json={
            "patient_id": patient_id,
            "test_name": "Hemoglobin",
            "value": 15.0,
            "units": "g/dL",
            "performed_by": "tech_001"
        }
    )
    result_id = result_response.json()["id"]
    
    # Try to release without verifying - should fail
    response = client.post(f"/results/{result_id}/release?released_by=pathologist_001")
    assert response.status_code == 400
    assert "verified" in response.json()["detail"].lower()
