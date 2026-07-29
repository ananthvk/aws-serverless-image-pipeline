from aws_lambda_powertools.utilities.data_classes import S3Event, SQSEvent
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


def handler(event_dict: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    sqs_event = SQSEvent(event_dict)
    response = {"batchItemFailures": []}
    for sqs_record in sqs_event.records:
        id = sqs_record.message_id
        try:
            for s3rec in sqs_record.decoded_nested_s3_event.records:
                processor.process(s3rec.s3.get_object.key)
        except Exception as e:
            print(e)
            response["batchItemFailures"].append({"itemIdentifier": id})
    return response
