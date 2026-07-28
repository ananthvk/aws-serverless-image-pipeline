import json
import os
import mimetypes
from pathlib import Path
from typing import Any

import requests
from requests import HTTPError
from pydantic import BaseModel

# Base url of the api gateway
API_BASE_URL = os.environ["API_BASE_URL"]


class UploadInfo(BaseModel):
    fields: dict[str, Any]
    url: str


class PresignedUploadResponse(BaseModel):
    image_id: str
    object_key: str
    upload: UploadInfo


def get_presigned_post(filepath: Path) -> PresignedUploadResponse:
    response = requests.post(
        f"{API_BASE_URL}/image/upload",
        json={
            "filename": filepath.name,
            "mime_type": mimetypes.guess_type(filepath)[0],
        },
    )
    response.raise_for_status()

    payload = response.json()
    return PresignedUploadResponse.model_validate(payload)


def upload_file(filepath: Path, upload_info: UploadInfo):
    with open(filepath, "rb") as f:
        response = requests.post(
            upload_info.url, data=upload_info.fields, files={"file": f}
        )
    response.raise_for_status()


def main():
    filepath = Path(input("Enter file path: "))
    try:
        presigned_post = get_presigned_post(filepath)
        print(f"Image Id: {presigned_post.image_id}")
        print(f"Uploading...")
        upload_file(filepath, presigned_post.upload)
        print(
            f"File uploaded, View at {presigned_post.upload.url}{presigned_post.object_key}"
        )
    except HTTPError as e:
        print(f"HTTP Error: {e.response.status_code}")
        print(f"Body: {e.response.text}")
    except Exception as e:
        print(f"Error uploading file: {e}")


if __name__ == "__main__":
    main()
