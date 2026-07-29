import argparse
import asyncio
import mimetypes
import os
from pathlib import Path
from typing import Any, List

import httpx
from pydantic import BaseModel

API_BASE_URL = os.environ["API_BASE_URL"]

VALID_EXTENSIONS = {".png", ".webp", ".jpg", ".jpeg"}


class UploadInfo(BaseModel):
    fields: dict[str, Any]
    url: str


class PresignedUploadResponse(BaseModel):
    image_id: str
    object_key: str
    upload: UploadInfo


async def get_presigned_post_async(
    client: httpx.AsyncClient, filepath: Path
) -> PresignedUploadResponse:
    response = await client.post(
        f"{API_BASE_URL}/image/upload",
        json={
            "filename": filepath.name,
            "mime_type": mimetypes.guess_type(filepath)[0],
        },
    )
    response.raise_for_status()
    return PresignedUploadResponse.model_validate(response.json())


async def upload_file_async(
    client: httpx.AsyncClient, filepath: Path, upload_info: UploadInfo
):
    data = upload_info.fields.copy()

    with open(filepath, "rb") as f:
        files = {"file": f}
        response = await client.post(upload_info.url, data=data, files=files)

    response.raise_for_status()


async def process_single_file(client: httpx.AsyncClient, filepath: Path):
    try:
        presigned_post = await get_presigned_post_async(client, filepath)

        await upload_file_async(client, filepath, presigned_post.upload)

        obj_key = Path(presigned_post.object_key)
        print(
            f"Y Successfully uploaded: {filepath.name} (ID: {presigned_post.image_id})"
        )
        print(f"   > URL: {presigned_post.upload.url}{presigned_post.object_key}")
        print(
            f"   > Thumbnail: {presigned_post.upload.url}thumbnails/{presigned_post.image_id}/{obj_key.stem}.webp"
        )

    except httpx.HTTPStatusError as e:
        print(
            f"❌ HTTP Error for {filepath.name}: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        print(f"❌ Error processing {filepath.name}: {e}")


def get_image_files(directory: Path) -> List[Path]:
    if not directory.is_dir():
        raise ValueError(f"'{directory}' is not a valid directory.")

    valid_files = []
    for path in directory.iterdir():
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
            valid_files.append(path)

    return valid_files


async def upload_directory_parallel(directory_path: str):
    dir_to_process = Path(directory_path)

    try:
        files_to_upload = get_image_files(dir_to_process)
    except ValueError as e:
        print(e)
        return

    if not files_to_upload:
        print(
            f"No matching files found in {dir_to_process} ({', '.join(VALID_EXTENSIONS)})"
        )
        return

    print(
        f"\nFound {len(files_to_upload)} file(s) to upload in '{dir_to_process.absolute()}':"
    )
    for f in files_to_upload:
        print(f" - {f.name}")

    confirm = input("\nProceed with upload? (y/n): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Upload cancelled")
        return

    print(f"\nStarting parallel upload of {len(files_to_upload)} files...")

    async with httpx.AsyncClient() as client:
        tasks = [process_single_file(client, f) for f in files_to_upload]
        await asyncio.gather(*tasks)


def main():
    parser = argparse.ArgumentParser(
        description="Upload images from a directory in parallel."
    )
    parser.add_argument(
        "dir", type=str, help="The path to the directory containing images."
    )
    args = parser.parse_args()

    asyncio.run(upload_directory_parallel(args.dir))


if __name__ == "__main__":
    main()
