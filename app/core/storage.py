"""
Thin wrapper around MinIO (S3-compatible) for document uploads.
"""
import uuid
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def ensure_bucket():
    try:
        if not _client.bucket_exists(settings.MINIO_BUCKET):
            _client.make_bucket(settings.MINIO_BUCKET)
    except S3Error:
        pass


def upload_file(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Uploads a file and returns its object URL (relative path within the bucket)."""
    ensure_bucket()
    object_name = f"{uuid.uuid4().hex}_{filename}"
    _client.put_object(
        settings.MINIO_BUCKET,
        object_name,
        BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )
    return f"/{settings.MINIO_BUCKET}/{object_name}"


def get_presigned_url(object_path: str, expires_seconds: int = 3600) -> str:
    object_name = object_path.split("/")[-1]
    return _client.presigned_get_object(settings.MINIO_BUCKET, object_name)
