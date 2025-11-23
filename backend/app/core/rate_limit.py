"""Rate limit configuration."""

from fastapi import Request
from slowapi import Limiter


def get_consumer_identifier(request: Request) -> str:
    """
    Identify the consumer for rate limiting purposes.
    Prioritizes the 'visitor_id' cookie (set by frontend).
    Falls back to the real IP address if the cookie is missing.
    """
    visitor_id = request.cookies.get("visitor_id")
    if visitor_id:
        return visitor_id


limiter = Limiter(key_func=get_consumer_identifier, default_limits=["50/minute"])
