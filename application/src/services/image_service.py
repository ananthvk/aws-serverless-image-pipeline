from .. import config
from ..interfaces.metadata import ImgStatus, Metadata
from ..interfaces.storage import Storage
from ..utils.object_key import get_image_id_from_object_key, create_object_key

from PIL import Image, UnidentifiedImageError
import io


class ProcessService:
    def __init__(self, storage: Storage, metadata: Metadata):
        self.storage = storage
        self.metadata = metadata

    def process(self, object_key: str) -> None:
        # First implement only the "happy path", i.e. no checks for failed lambdas, errors, deletion of files etc
        image_id, filename = get_image_id_from_object_key(object_key)
        if not self.metadata.complete_initial_upload(image_id):
            return
        if not self.metadata.change_status_conditional(
            image_id, ImgStatus.PROCESSING, ImgStatus.UPLOADED
        ):
            return

        img_bytes = self.storage.get_object(object_key)

        # Use PIL to resize the image
        try:
            img = Image.open(img_bytes)
        except UnidentifiedImageError as e:
            # TODO: What if this call / S3 delete throws an error ?
            self.metadata.change_status_conditional(
                image_id, ImgStatus.FAILED, ImgStatus.PROCESSING
            )
            self.storage.delete_object(object_key)
            return

        if img.format not in config.ALLOWED_FORMATS:
            print(f"Unsupported image format: {img.format}")
            self.metadata.change_status_conditional(
                image_id, ImgStatus.FAILED, ImgStatus.PROCESSING
            )
            self.storage.delete_object(object_key)
            return

        # original_format = img.format
        img_resized = img.resize((300, 300))
        output_io = io.BytesIO()
        img_resized.save(output_io, format=config.THUMBNAIL_FORMAT)
        output_io.seek(0)

        resized_key = create_object_key(
            image_id,
            filename,
            f".{config.THUMBNAIL_FORMAT.lower()}",
            dir=config.THUMBNAIL_IMAGE_FOLDER_NAME,
        )

        self.storage.save_object(resized_key, output_io)
        print(f"Finished processing {object_key} -> {resized_key}")
        self.metadata.change_status_conditional(
            image_id, ImgStatus.COMPLETED, ImgStatus.PROCESSING
        )
