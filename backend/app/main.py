from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import time
from .routers import health, patients
from .database import engine, Base

app = FastAPI(title="LIMS API", version="0.1.0")

# CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup with retry logic."""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database connection failed (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")
                raise


app.include_router(health.router, prefix="")
app.include_router(patients.router, prefix="")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the LIMS API"}
