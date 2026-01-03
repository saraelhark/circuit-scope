"""Abstract storage service interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol


class StorageError(Exception):
    """Base exception for storage-related errors."""


class StorageFile(Protocol):
    """Protocol representing a file-like object suitable for uploads."""

    def read(self, size: int = -1) -> bytes:  # pragma: no cover - protocol definition
        ...

    def close(self) -> None:  # pragma: no cover - protocol definition
        ...

    def seek(self, offset: int, whence: int = 0) -> int:  # pragma: no cover - protocol definition
        ...


class StorageService(ABC):
    """Abstract storage service defining required methods."""

    @abstractmethod
    async def save(self, path: str, file_obj: StorageFile) -> str:
        """Persist the file object under the given path and return canonical location."""

    @abstractmethod
    async def upload(self, path: str, file_path: Path) -> str:
        """Upload a local file to the storage."""

    @abstractmethod
    async def download(self, path: str, destination: Path) -> None:
        """Download the file from storage to a local destination."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Remove the object at the given path if it exists."""

    @abstractmethod
    async def get_url(self, path: str) -> str | None:
        """Return a public URL for the stored object, if available."""

    @abstractmethod
    async def read(self, path: str) -> bytes:
        """Read the file contents from storage."""

    @abstractmethod
    def filesystem_path(self, path: str) -> Path:
        """Return the concrete filesystem path (for local backends)."""
