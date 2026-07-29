# 300s - 5 min
PRESIGNED_URL_EXPIRY = 300

# How long are records in upload_pending state kept for
# Keep it for one hour - so that even if S3 trigger is called later, the record is not deleted
DYNAMODB_INITIAL_EXPIRY = 3600

# Max file size is 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed mime types
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_FORMATS = {"PNG", "WEBP", "JPEG"}

ORIGINAL_IMAGE_FOLDER_NAME = "uploads"
THUMBNAIL_IMAGE_FOLDER_NAME = "thumbnails"

THUMBNAIL_FORMAT = "WEBP"
