from typing import override

import boto3

from .. import config
from ..interfaces.storage import PresignedPost, Storage


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
