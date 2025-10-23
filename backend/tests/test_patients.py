"""Tests for patients endpoint."""
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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


def test_create_patient():
    """Test creating a new patient."""
    # Clean up before test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    response = client.post(
        "/patients",
        json={
            "name": "John Doe",
            "age": 35,
            "gender": "Male",
            "contact": "555-1234"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["age"] == 35
    assert data["gender"] == "Male"
    assert data["contact"] == "555-1234"
    assert "id" in data


def test_list_patients():
    """Test listing all patients."""
    # Clean up before test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a couple of patients
    client.post(
        "/patients",
        json={"name": "Jane Smith", "age": 28, "gender": "Female", "contact": "555-5678"}
    )
    client.post(
        "/patients",
        json={"name": "Bob Johnson", "age": 42, "gender": "Male"}
    )
    
    # Get the list
    response = client.get("/patients")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Jane Smith"
    assert data[1]["name"] == "Bob Johnson"


def test_create_patient_without_contact():
    """Test creating a patient without optional contact field."""
    # Clean up before test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    response = client.post(
        "/patients",
        json={
            "name": "Alice Brown",
            "age": 30,
            "gender": "Female"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice Brown"
    assert data["contact"] is None
