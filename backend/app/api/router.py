"""API router registration."""

from fastapi import APIRouter

from .routes import auth, comment_threads, health, projects, reviews

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(
    comment_threads.router,
    prefix="/projects/{project_id}/threads",
    tags=["comment-threads"],
)

__all__ = ["api_router"]
