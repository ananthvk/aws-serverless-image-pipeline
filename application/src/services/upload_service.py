import mimetypes
from http import HTTPStatus

import ulid
from pydantic import BaseModel, Field

from .. import config
from ..errors import ValidationError
from ..interfaces.metadata import ImgStatus, Metadata
from ..interfaces.storage import PresignedPost, Storage
from ..utils.object_key import create_object_key


class UploadRequest(BaseModel):
    """Validates the incoming HTTP request payload body."""

    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str


class UploadInitiationResult(BaseModel):
    """Contains the presigned post form to which the image must be uploaded, and the image id"""

    model_config = {"frozen": True}

    image_id: str
    object_key: str
    upload: PresignedPost


class UploadService:
    def __init__(self, storage: Storage, metadata: Metadata):
        self.storage = storage
        self.metadata = metadata

    def initiate_upload(self, request: UploadRequest) -> UploadInitiationResult:
        # Validation to ensure that request parameters are correct
        if request.mime_type not in config.ALLOWED_MIME_TYPES:
            raise ValidationError(
                "Unsupported file type", status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE
            )

        # Create the presigned url, the object key is [ID].extension
        # For example ABC.png, so that it's easier for the browsers to directly download / link to the file
        extension = mimetypes.guess_extension(request.mime_type)
        if not extension:
            # Shouldn't happen since we check for existence in the set
            raise ValidationError("Invalid MIME type")
        image_id = f"{ulid.ULID()}"
        object_key = create_object_key(
            image_id, request.filename, extension, dir=config.ORIGINAL_IMAGE_FOLDER_NAME
        )
        presigned_url = self.storage.generate_presigned_url(
            object_key, request.mime_type
        )

        # Create a record in the metadata store
        # and set the file status to UPLOAD_PENDING
        self.metadata.initialize_record(
            image_id=image_id,
            object_key=object_key,
            filename=request.filename,
            status=ImgStatus.UPLOAD_PENDING,
        )

        return UploadInitiationResult(
            image_id=image_id, object_key=object_key, upload=presigned_url
        )
