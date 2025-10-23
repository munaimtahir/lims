from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
async def read_health() -> dict[str, str]:
    """Return a simple health status payload."""
    return {"status": "ok"}
