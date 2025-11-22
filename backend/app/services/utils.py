"""General utility functions."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str) -> str:
    """Convert a string to a slug."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "sheet"


def unique_filename(base: str, extension: str, used: set[str]) -> str:
    """Generate a unique filename by appending a counter if necessary."""
    candidate = f"{base}{extension}"
    counter = 1
    while candidate in used:
        candidate = f"{base}-{counter}{extension}"
        counter += 1
    return candidate
