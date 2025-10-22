from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
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
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)


app.include_router(health.router, prefix="")
app.include_router(patients.router, prefix="")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the LIMS API"}
