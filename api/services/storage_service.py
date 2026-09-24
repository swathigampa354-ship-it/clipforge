# Storage abstraction layer
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class StorageObject:
    key: str
    data: bytes
    content_type: str = "application/octet-stream"
    size: int = 0
    metadata: dict | None = None


class StorageProvider(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream", metadata: dict | None = None) -> str:
        """Upload data and return the storage key"""
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download data by key"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete object by key"""
        pass

    @abstractmethod
    async def signed_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Generate a time-limited signed URL"""
        pass

    @abstractmethod
    async def list(self, prefix: str) -> list[dict]:
        """List objects by prefix"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if object exists"""
        pass


class LocalStorageProvider(StorageProvider):
    """Development storage using local filesystem"""

    def __init__(self, base_path: str):
        self.base_path = base_path
        import os
        os.makedirs(base_path, exist_ok=True)

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream", metadata: dict | None = None) -> str:
        import os
        path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return key

    async def download(self, key: str) -> bytes:
        import os
        path = os.path.join(self.base_path, key)
        with open(path, "rb") as f:
            return f.read()

    async def delete(self, key: str) -> None:
        import os
        path = os.path.join(self.base_path, key)
        if os.path.exists(path):
            os.remove(path)

    async def signed_url(self, key: str, expires_seconds: int = 3600) -> str:
        from urllib.parse import urlencode
        from api.app.config import settings
        return f"http://{settings.STORAGE_PATH}/{key}"

    async def list(self, prefix: str) -> list[dict]:
        import os
        results = []
        for root, dirs, files in os.walk(os.path.join(self.base_path, prefix)):
            for f in files:
                results.append({"key": os.path.relpath(os.path.join(root, f), self.base_path)})
        return results

    async def exists(self, key: str) -> bool:
        import os
        return os.path.exists(os.path.join(self.base_path, key))


class S3StorageProvider(StorageProvider):
    """Production storage using S3-compatible services"""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        import minio
        self.client = minio.Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
            bucket=bucket,
        )
        self.bucket = bucket

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream", metadata: dict | None = None) -> str:
        from io import BytesIO
        await self.client.put_object(
            self.bucket,
            key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
            metadata=metadata or {},
        )
        return key

    async def download(self, key: str) -> bytes:
        from io import BytesIO
        response = await self.client.get_object(self.bucket, key)
        return await response.read()

    async def delete(self, key: str) -> None:
        await self.client.remove_object(self.bucket, key)

    async def signed_url(self, key: str, expires_seconds: int = 3600) -> str:
        return await self.client.presigned_get_object(self.bucket, key, expires=expires_seconds)

    async def list(self, prefix: str) -> list[dict]:
        objects = await self.client.list_objects(self.bucket, prefix=prefix)
        return [{"key": obj.object_name, "size": obj.size} for obj in objects]

    async def exists(self, key: str) -> bool:
        try:
            await self.client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False


def get_storage_provider() -> StorageProvider:
    """Factory to create the appropriate storage provider"""
    from api.app.config import settings

    if settings.STORAGE_TYPE == "s3":
        return S3StorageProvider(
            endpoint=settings.STORAGE_PATH,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_SECRET_KEY,
        )
    return LocalStorageProvider(settings.STORAGE_PATH)
