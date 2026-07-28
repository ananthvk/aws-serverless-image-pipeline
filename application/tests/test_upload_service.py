from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest

from src import config
from src.errors import ValidationError
from src.interfaces.metadata import ImgStatus, Metadata
from src.interfaces.storage import PresignedPost, Storage
from src.services.upload_service import (
    UploadRequest,
    UploadService,
)
from src.utils.object_key import create_object_key


@pytest.fixture
def mock_dependencies():
    """Provides mocked abstract interfaces for storage and metadata."""
    storage = MagicMock(spec=Storage)
    metadata = MagicMock(spec=Metadata)
    return storage, metadata


@pytest.fixture
def valid_request():
    """Provides a standard valid upload request."""
    return UploadRequest(
        filename="vacation_photo.png",
        mime_type="image/png",
    )


def test_initiate_upload_success(mock_dependencies, valid_request):
    """Verifies successful upload generation when inputs are valid."""
    mock_storage, mock_metadata = mock_dependencies

    # Configure mock behavior
    fake_post = PresignedPost.model_validate(
        {"url": "https://amazonaws.com", "fields": {"foo": "bar"}}
    )
    mock_storage.generate_presigned_url.return_value = fake_post

    service = UploadService(storage=mock_storage, metadata=mock_metadata)

    # Use patch to anchor the random ULID string for exact assertion testing
    fake_ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    object_key = f'{config.ORIGINAL_IMAGE_FOLDER_NAME}/{create_object_key(fake_ulid, "vacation_photo.jpg", ".png")}'
    assert (
        object_key
        == f"{config.ORIGINAL_IMAGE_FOLDER_NAME}/{fake_ulid}/vacation-photo.png"
    )

    with patch("ulid.ULID", return_value=fake_ulid):
        result = service.initiate_upload(valid_request)

    # Assertions
    assert result.image_id == fake_ulid
    assert result.object_key == object_key
    assert result.upload == fake_post

    # Verify Storage Interface interaction
    mock_storage.generate_presigned_url.assert_called_once_with(
        object_key, valid_request.mime_type
    )

    # Verify Metadata Interface interaction
    mock_metadata.initialize_record.assert_called_once_with(
        image_id=fake_ulid,
        object_key=object_key,
        filename=valid_request.filename,
        status=ImgStatus.UPLOAD_PENDING,
    )


def test_initiate_upload_invalid_mime_type(mock_dependencies, valid_request):
    """Verifies that an unsupported mime type throws a ValidationError."""
    mock_storage, mock_metadata = mock_dependencies
    service = UploadService(storage=mock_storage, metadata=mock_metadata)

    # Modify request with a bad media type
    valid_request.mime_type = "image/gif"

    with pytest.raises(ValidationError) as exc_info:
        service.initiate_upload(valid_request)

    assert exc_info.value.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert "Unsupported file type" in str(exc_info.value)

    # Ensure downstream infrastructure operations were never triggered
    mock_storage.generate_presigned_url.assert_not_called()
    mock_metadata.initialize_record.assert_not_called()
