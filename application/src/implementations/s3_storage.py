from typing import override

import boto3

from .. import config
from ..interfaces.storage import PresignedPost, Storage
import io


class S3Storage(Storage):
    def __init__(self, bucket_name: str) -> None:
        super().__init__()
        self.client = boto3.client("s3")
        self.bucket_name = bucket_name

    @override
    def generate_presigned_url(self, object_key: str, mime_type: str) -> PresignedPost:
        """
        Generates a presigned URL
        """
        return PresignedPost.model_validate(
            self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Conditions=[
                    ["content-length-range", 1, config.MAX_FILE_SIZE],
                    {"Content-Type": mime_type},
                ],
                Fields={"Content-Type": mime_type},
                ExpiresIn=config.PRESIGNED_URL_EXPIRY,
            )
        )

    @override
    def get_object(self, object_key: str) -> io.BytesIO:
        response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
        # This is okay because objects are always < 10MB
        # But for larger objects, use streaming
        return io.BytesIO(response["Body"].read())

    @override
    def delete_object(self, object_key: str):
        self.client.delete_object(Bucket=self.bucket_name, Key=object_key)

    @override
    def save_object(self, object_key: str, body: io.BytesIO):
        self.client.put_object(Bucket=self.bucket_name, Key=object_key, Body=body)
