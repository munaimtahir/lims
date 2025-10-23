import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lims.database import Base, engine
from lims.routers import health, patients


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup: Create database tables with retry logic
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
            break
        except Exception:
            if attempt < max_retries - 1:
                print(
                    f"Database connection failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to database after {max_retries} attempts")
                raise

    yield
    # Shutdown: cleanup if needed


app = FastAPI(title="LIMS API", version="0.1.0", lifespan=lifespan)

# CORS configuration - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router, prefix="")
app.include_router(patients.router, prefix="")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the LIMS API"}
