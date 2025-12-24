from __future__ import annotations

from typing import Optional, BinaryIO
from datetime import timedelta
import io

from miniopy_async import Minio
from fastapi import UploadFile, HTTPException, status

from . import settings


class MinioManager:
    """Manages MinIO connections and file operations."""

    def __init__(self) -> None:
        self.client: Optional[Minio] = None
        self.bucket_name: str = settings.MINIO_BUCKET_NAME

    async def init_minio(self) -> None:
        """Initialize MinIO client and ensure bucket exists."""
        self.client = Minio(
            endpoint=f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )

        # Создаем bucket если его нет
        bucket_exists = await self.client.bucket_exists(self.bucket_name)
        if not bucket_exists:
            await self.client.make_bucket(self.bucket_name)

    async def close(self) -> None:
        """Close MinIO client connection."""
        if self.client:
            # miniopy-async не требует явного закрытия
            self.client = None

    async def upload_file(
        self,
        file: UploadFile,
        object_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """Upload file to MinIO."""
        if not self.client:
            raise RuntimeError("MinIO client is not initialized.")

        try:
            # Читаем содержимое файла
            content = await file.read()
            file_size = len(content)
            
            # Определяем content_type
            if content_type is None:
                content_type = file.content_type or "application/octet-stream"

            # Загружаем файл
            await self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(content),
                length=file_size,
                content_type=content_type
            )

            # Возвращаем URL для доступа к файлу
            file_url = f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}/{self.bucket_name}/{object_name}"
            return file_url

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
        finally:
            await file.seek(0)  # Сбрасываем позицию файла

    async def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload bytes data to MinIO."""
        if not self.client:
            raise RuntimeError("MinIO client is not initialized.")

        try:
            file_size = len(data)

            await self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=file_size,
                content_type=content_type
            )

            file_url = f"http://{settings.MINIO_HOST}:{settings.MINIO_PORT}/{self.bucket_name}/{object_name}"
            return file_url

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload bytes: {str(e)}"
            )

    async def get_file(self, object_name: str) -> bytes:
        """Download file from MinIO."""
        if not self.client:
            raise RuntimeError("MinIO client is not initialized.")

        try:
            response = await self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return await response.read()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {str(e)}"
            )

    async def delete_file(self, object_name: str) -> bool:
        """Delete file from MinIO."""
        if not self.client:
            raise RuntimeError("MinIO client is not initialized.")

        try:
            await self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )

    async def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate a presigned URL for temporary access to a file."""
        if not self.client:
            raise RuntimeError("MinIO client is not initialized.")

        try:
            url = await self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )

    async def file_exists(self, object_name: str) -> bool:
        """Check if file exists in MinIO."""
        if not self.client:
            raise RuntimeError("MinIO client is not initialized.")

        try:
            await self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except Exception:
            return False


async def get_minio() -> MinioManager:
    """Dependency for getting MinIO manager instance."""
    return minio_manager


minio_manager = MinioManager()