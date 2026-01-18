"""Rate limit configuration."""

from fastapi import Request
from slowapi import Limiter


def get_consumer_identifier(request: Request) -> str:
    """Identify consumer for rate limiting. Uses IP, not client-controlled cookies.

    Security: Cookie-based identification (visitor_id) can be spoofed by clients
    to bypass rate limits. IP-based identification is more reliable.
    """
    # Try authenticated user ID (for better per-user limits)
    user_id = request.headers.get("x-user-id")
    if user_id:
        return f"user:{user_id}"

    # Use X-Forwarded-For for proxied requests (first IP is client)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"

    # Direct client IP
    client_host = getattr(request.client, "host", None)
    if client_host:
        return f"ip:{client_host}"

    return "anonymous"


limiter = Limiter(key_func=get_consumer_identifier, default_limits=["50/minute"])
