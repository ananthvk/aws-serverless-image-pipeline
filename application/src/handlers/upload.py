import json
from datetime import datetime
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
import PIL


def handler(event: APIGatewayProxyEvent, context: LambdaContext):
    print("got event", event)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": "Hello world !",
                "ts": "%s" % datetime.now(),
                "version": PIL.__version__,
            }
        ),
    }
