import os
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException

from app.database import API_ROOT


@lru_cache
def s3():
    endpoint = os.getenv("S3_ENDPOINT") or None
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        config=Config(s3={"addressing_style": "path"}) if endpoint else None,
        region_name=os.getenv("S3_REGION") or "us-east-1",
        aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID") or None,
        aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY") or None,
    )


class PhotoStorage:
    def __init__(self):
        mode = os.getenv("PHOTO_STORAGE")
        self.directory: Path | None = None
        self.bucket: str | None = None
        if mode == "local" and os.getenv("APP_ENV") in {"development", "test"}:
            self.directory = Path(os.getenv("PHOTO_DIR", str(API_ROOT / ".photos")))
        elif mode == "s3":
            self.bucket = os.getenv("S3_BUCKET")
        if self.directory is None and not self.bucket:
            raise HTTPException(503, "photo_storage_unavailable")

    def put(self, key: str, data: bytes):
        try:
            if self.directory is not None:
                self.directory.mkdir(parents=True, exist_ok=True)
                with (self.directory / key).open("xb") as target:
                    target.write(data)
            else:
                s3().put_object(
                    Bucket=self.bucket, Key=key, Body=data, ContentType="image/jpeg"
                )
        except (OSError, BotoCoreError, ClientError) as error:
            raise HTTPException(503, "photo_storage_unavailable") from error

    def get(self, key: str) -> bytes:
        try:
            if self.directory is not None:
                return (self.directory / key).read_bytes()
            body = s3().get_object(Bucket=self.bucket, Key=key)["Body"]
            try:
                return body.read()
            finally:
                body.close()
        except (OSError, BotoCoreError, ClientError) as error:
            raise HTTPException(503, "photo_storage_unavailable") from error

    def remove(self, key: str):
        if self.directory is not None:
            (self.directory / key).unlink(missing_ok=True)
        else:
            s3().delete_object(Bucket=self.bucket, Key=key)
