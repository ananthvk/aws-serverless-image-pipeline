from aws_lambda_powertools.utilities.data_classes import S3Event
from aws_lambda_powertools.utilities.typing import LambdaContext
from typing import Any
from ..implementations.dynamo_metadata import DynamoDBMetadata
from ..implementations.s3_storage import S3Storage
from ..services.image_service import ProcessService
import os

bucket_name = os.environ["IMAGE_BUCKET_NAME"]
metadata_table_name = os.environ["METADATA_TABLE_NAME"]
bucket = S3Storage(bucket_name)
metadata_table = DynamoDBMetadata(metadata_table_name)
processor = ProcessService(bucket, metadata_table)


def handler(event_dict: dict[str, Any], context: LambdaContext) -> None:
    event = S3Event(event_dict)
    for record in event.records:
        processor.process(record.s3.get_object.key)
