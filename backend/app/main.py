from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .routers import health

app = FastAPI(title="LIMS API", version="0.1.0")

# Read allowed origins from environment variable FRONTEND_ORIGINS (comma-separated)
allowed_origins = os.getenv("FRONTEND_ORIGINS", "")
allowed_origins_list = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the LIMS API"}
