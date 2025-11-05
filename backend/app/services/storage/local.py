"""Local filesystem storage implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urljoin

from app.services.storage.base import StorageError, StorageFile, StorageService


class LocalStorage(StorageService):
    """Store files on the local filesystem."""

    def __init__(self, base_path: Path, public_base_url: str | None = None) -> None:
        self._base_path = base_path
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, path: str, file_obj: StorageFile) -> str:
        destination = self.filesystem_path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        def _write() -> None:
            try:
                file_obj.seek(0)
            except (AttributeError, OSError):
                pass

            with destination.open("wb") as output:
                while True:
                    chunk = file_obj.read(1024 * 1024)
                    if not chunk:
                        break
                    if isinstance(chunk, str):
                        chunk = chunk.encode()
                    output.write(chunk)

        try:
            await asyncio.to_thread(_write)
        except Exception as exc:
            raise StorageError("Failed to save file") from exc
        finally:
            try:
                file_obj.close()
            except Exception:
                pass

        return path

    async def delete(self, path: str) -> None:
        target = self.filesystem_path(path)
        if not target.exists():
            return

        def _delete() -> None:
            target.unlink()

        try:
            await asyncio.to_thread(_delete)
        except Exception as exc:
            raise StorageError("Failed to delete file") from exc

    async def get_url(self, path: str) -> str | None:
        if not self._public_base_url:
            return None
        return urljoin(f"{self._public_base_url}/", path)

    def filesystem_path(self, path: str) -> Path:
        safe_path = Path(path)
        if safe_path.is_absolute() or ".." in safe_path.parts:
            raise StorageError("Invalid storage path")
        return self._base_path / safe_path
