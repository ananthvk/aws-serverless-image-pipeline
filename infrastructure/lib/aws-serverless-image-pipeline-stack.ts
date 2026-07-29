import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3n from "aws-cdk-lib/aws-s3-notifications";
import * as cdk from "aws-cdk-lib/core";
import * as apigateway from "aws-cdk-lib/aws-apigatewayv2";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { Construct } from "constructs";
import { HttpLambdaIntegration } from "aws-cdk-lib/aws-apigatewayv2-integrations";
import { join } from "path";
import * as python from "@aws-cdk/aws-lambda-python-alpha";

export class AwsServerlessImagePipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const imgBucket = new s3.Bucket(this, "ImgBucket", {
      publicReadAccess: true,
      blockPublicAccess: new s3.BlockPublicAccess({
        blockPublicAcls: true,
        blockPublicPolicy: false,
        ignorePublicAcls: true,
        restrictPublicBuckets: false,
      }),
      // Don't this in production app since the bucket can get deleted on stack change
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const tableName = "ImgMetadata";

    const metadataTable = new dynamodb.Table(this, `${tableName}Table`, {
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      // Add a TTL attribute so that records that have status = upload_pending are automatically cleared after a while
      timeToLiveAttribute: "expire_at",
    });

    // This lambda handles creation of presigned S3 links for the client to upload the image, generation of id, and creating an entry
    // in the dynamodb table
    const uploadFn = new python.PythonFunction(this, "UploadFunction", {
      entry: join(__dirname, "../../application/"),
      runtime: lambda.Runtime.PYTHON_3_14,
      index: "src/handlers/upload.py",
      handler: "handler",
      bundling: {
        assetExcludes: [".venv", ".ruff_cache", ".pytest_cache", "vendored"],
      },
      environment: {
        IMAGE_BUCKET_NAME: imgBucket.bucketName,
        METADATA_TABLE_NAME: metadataTable.tableName,
      },
    });
    // Give the lambda write access so that presigned urls created by it work
    // Lambda doesn't need to call S3
    // Presigned url contains the lambda's temporary IAM credentials, so when the client uses it, S3 checks the permissions
    imgBucket.grants.put(uploadFn);
    metadataTable.grants.readWriteData(uploadFn);

    // Process lambda - this lambda gets triggered by S3 event
    // in uploads/ directory
    const processFn = new python.PythonFunction(this, "ProcessFunction", {
      entry: join(__dirname, "../../application/"),
      runtime: lambda.Runtime.PYTHON_3_14,
      index: "src/handlers/process_image.py",
      handler: "handler",
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      bundling: {
        assetExcludes: [".venv", ".ruff_cache", ".pytest_cache", "vendored"],
      },
      environment: {
        IMAGE_BUCKET_NAME: imgBucket.bucketName,
        METADATA_TABLE_NAME: metadataTable.tableName,
      },
    });
    imgBucket.grants.readWrite(processFn);
    metadataTable.grants.readWriteData(processFn);

    // Add an event notification so that processFn is triggered whenever a new file is uploaded
    imgBucket.addEventNotification(
      s3.EventType.OBJECT_CREATED,
      new s3n.LambdaDestination(processFn),
      {
        prefix: "uploads/",
      },
    );

    // Create the API Gateway (HTTP API)
    const api = new apigateway.HttpApi(this, "ImgHttpAPI");
    api.addRoutes({
      path: "/image/upload",
      methods: [apigateway.HttpMethod.POST],
      integration: new HttpLambdaIntegration("UploadIntegration", uploadFn),
    });

    new cdk.CfnOutput(this, "apigwUrl", {
      value: api.url || "NONE",
    });

    new cdk.CfnOutput(this, "bucketUrl", {
      value: `https://${imgBucket.bucketDomainName}`,
    });
  }
}
