"""API router registration."""

from fastapi import APIRouter, Depends

from app.api.deps import verify_frontend_token
from .routes import auth, comment_threads, health, projects, reviews, notifications

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])

# Protected routes (require frontend token)
protected_deps = [Depends(verify_frontend_token)]

api_router.include_router(auth.router, prefix="/auth", tags=["auth"], dependencies=protected_deps)
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"],
    dependencies=protected_deps,
)
api_router.include_router(
    projects.router, prefix="/projects", tags=["projects"], dependencies=protected_deps
)
api_router.include_router(
    reviews.router, prefix="/reviews", tags=["reviews"], dependencies=protected_deps
)
api_router.include_router(
    comment_threads.router,
    prefix="/projects/{project_id}/threads",
    tags=["comment-threads"],
    dependencies=protected_deps,
)

__all__ = ["api_router"]
