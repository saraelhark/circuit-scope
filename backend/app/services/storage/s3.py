"""S3 storage implementation."""

from __future__ import annotations

import asyncio
from pathlib import Path
import logging

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = None

from app.services.storage.base import StorageError, StorageFile, StorageService

logger = logging.getLogger(__name__)


class S3Storage(StorageService):
    """Store files on S3."""

    def __init__(
        self,
        bucket_name: str,
        region_name: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
        public_base_url: str | None = None,
    ) -> None:
        if boto3 is None:
            raise ImportError("boto3 is required for S3 storage")

        self._bucket_name = bucket_name
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None

        self._client = boto3.client(
            "s3",
            region_name=region_name,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
        )

    async def save(self, path: str, file_obj: StorageFile) -> str:
        def _upload() -> None:
            try:
                file_obj.seek(0)
            except (AttributeError, OSError):
                pass

            try:
                self._client.upload_fileobj(file_obj, self._bucket_name, path)
            except ClientError as exc:
                raise StorageError(f"Failed to upload to S3: {exc}") from exc

        await asyncio.to_thread(_upload)
        return path

    async def upload(self, path: str, file_path: Path) -> str:
        def _upload() -> None:
            try:
                self._client.upload_file(str(file_path), self._bucket_name, path)
            except ClientError as exc:
                raise StorageError(f"Failed to upload file to S3: {exc}") from exc

        await asyncio.to_thread(_upload)
        return path

    async def download(self, path: str, destination: Path) -> None:
        def _download() -> None:
            try:
                self._client.download_file(self._bucket_name, path, str(destination))
            except ClientError as exc:
                raise StorageError(f"Failed to download from S3: {exc}") from exc

        await asyncio.to_thread(_download)

    async def delete(self, path: str) -> None:
        def _delete() -> None:
            try:
                self._client.delete_object(Bucket=self._bucket_name, Key=path)
            except ClientError as exc:
                raise StorageError(f"Failed to delete from S3: {exc}") from exc

        await asyncio.to_thread(_delete)

    async def read(self, path: str) -> bytes:
        def _read() -> bytes:
            try:
                response = self._client.get_object(Bucket=self._bucket_name, Key=path)
                return response["Body"].read()
            except ClientError as exc:
                raise StorageError(f"Failed to read from S3: {exc}") from exc

        return await asyncio.to_thread(_read)

    async def get_url(self, path: str) -> str | None:
        if self._public_base_url:
            from urllib.parse import urljoin

            return urljoin(f"{self._public_base_url}/", path)

        # Generate presigned URL
        def _generate_url() -> str:
            try:
                return self._client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self._bucket_name, "Key": path},
                    ExpiresIn=3600,
                )
            except ClientError:
                return None

        return await asyncio.to_thread(_generate_url)

    def filesystem_path(self, path: str) -> Path:
        raise NotImplementedError("S3 storage does not support direct filesystem paths")
