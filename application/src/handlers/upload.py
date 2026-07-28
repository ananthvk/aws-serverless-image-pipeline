import json
import os
from http import HTTPStatus
from typing import Any

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError as PydanticValidationError

from ..errors import ValidationError
from ..implementations.dynamo_metadata import DynamoDBMetadata
from ..implementations.s3_storage import S3Storage
from ..services.upload_service import (
    UploadRequest,
    UploadService,
)

bucket_name = os.environ["IMAGE_BUCKET_NAME"]
metadata_table_name = os.environ["METADATA_TABLE_NAME"]
bucket = S3Storage(bucket_name)
metadata_table = DynamoDBMetadata(metadata_table_name)
upload_service = UploadService(storage=bucket, metadata=metadata_table)


def handler(event_dict: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    event = APIGatewayProxyEventV2(event_dict)

    # No need to check for these because this function is attached to only one route of APIGateway
    # raw_path = event.path
    # http_method = event.http_method

    try:
        body = event.body or "{}"
        request = UploadRequest.model_validate_json(body, extra="forbid")
        response = upload_service.initiate_upload(request)
        return {
            "statusCode": HTTPStatus.OK,
            "headers": {"Content-Type": "application/json"},
            "body": response.model_dump_json(),
        }

    except ValidationError as v:
        return {
            "statusCode": v.status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": v.message}),
        }
    except PydanticValidationError as err:
        error_msg = "; ".join(
            [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in err.errors()]
        )
        return {
            "statusCode": HTTPStatus.BAD_REQUEST,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": error_msg}),
        }
