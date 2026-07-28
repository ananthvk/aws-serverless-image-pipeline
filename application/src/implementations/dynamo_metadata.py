from typing import override

import boto3

from ..interfaces import metadata
from ..interfaces.metadata import ImgStatus


class DynamoDBMetadata(metadata.Metadata):
    def __init__(self, table_name: str) -> None:
        super().__init__()
        self.table = boto3.resource("dynamodb").Table(table_name)

    @override
    def initialize_record(
        self,
        image_id: str,
        object_key: str,
        filename: str,
        status: metadata.ImgStatus = ImgStatus.UPLOAD_PENDING,
    ) -> None:
        self.table.put_item(
            Item={
                "id": image_id,
                "object_key": object_key,
                "filename": filename,
                "status": status,
            }
        )
