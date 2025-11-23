"""Dependency functions for API routes."""

from typing import Annotated

from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_frontend_token(
    x_frontend_token: Annotated[str | None, Header()] = None,
) -> None:
    """
    Verify that the request is coming from the authorized frontend.
    """

    if x_frontend_token != settings.frontend_secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid frontend token",
        )
