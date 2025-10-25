"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["health"], summary="Health check")
async def health() -> dict[str, str]:
    """Return application health status."""

    return {"status": "ok"}
