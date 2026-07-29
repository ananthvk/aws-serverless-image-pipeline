from typing import override

import boto3
from botocore.exceptions import ClientError

from ..interfaces import metadata
from ..interfaces.metadata import ImgStatus
from .. import config

import time


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
                "expire_at": int(config.DYNAMODB_INITIAL_EXPIRY + time.time()),
            }
        )

    @override
    def change_status_conditional(
        self, image_id: str, new_status: ImgStatus, previous_status: ImgStatus
    ) -> bool:
        """
        Change the status of the image only if current status is equal to previous status
        This is to prevent race conditions
        """
        try:
            self.table.update_item(
                Key={"id": image_id},
                UpdateExpression="""SET #status = :new_status""",
                ConditionExpression="""#status = :previous_status""",
                # Have to do this because status is a reserved word in dynamodb
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":new_status": new_status,
                    ":previous_status": previous_status,
                },
            )
            return True
        except ClientError as e:
            err = e.response.get("Error", {}).get("Code", "")
            if err == "ConditionalCheckFailedException":
                return False

            # Raise if it's some other error
            raise e

    @override
    def complete_initial_upload(self, image_id: str) -> bool:
        try:
            self.table.update_item(
                Key={"id": image_id},
                UpdateExpression="SET #status = :new_status REMOVE expire_at",
                ConditionExpression="#status = :previous_status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":new_status": "uploaded",
                    ":previous_status": "upload_pending",
                },
            )
            return True
        except ClientError as e:
            if (
                e.response.get("Error", {}).get("Code", "")
                == "ConditionalCheckFailedException"
            ):
                return False
            raise e
