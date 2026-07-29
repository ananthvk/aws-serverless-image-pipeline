import re
import unicodedata
from pathlib import PurePosixPath


def sanitize_name(filename: str) -> str:
    # Normalize path separator
    filename = filename.replace("\\", "/")
    p = PurePosixPath(filename)
    basename = p.stem
    # ext = p.suffix

    # Flatten unicode
    basename = unicodedata.normalize("NFKD", basename)
    basename = basename.encode("ascii", "ignore").decode("ascii")

    # Lowercase, replace spaces & underscore with hyphen
    basename = basename.lower().strip()
    basename = re.sub(r"[\s_]+", "-", basename)

    # Only allow alphanumeric, hyphen and periods
    basename = re.sub(r"[^a-z0-9\-\.]", "", basename)

    # Redundant hyphens
    basename = re.sub(r"-+", "-", basename)
    basename = basename.strip("-")

    # If the filename becomes empty, give a default name
    if not basename:
        basename = "file"

    # Note we are discarding the user specified extension, and will assign
    # the extension based on content type

    # Attach extension
    # final_filename = f"{basename}{ext.lower().strip()}"
    return basename


def create_object_key(id: str, filename: str, ext: str, dir: str = "uploads") -> str:
    filename = sanitize_name(filename)
    return f"{dir}/{id}/{filename}{ext}"


def get_image_id_from_object_key(object_key: str) -> tuple[str, str]:
    parts = object_key.split("/")
    # Make sure that object key contains 3 parts - dir, id, and filename + ext
    if len(parts) < 3:
        raise ValueError(f"Malformed object key structure: {object_key}")

    return parts[1], parts[2]
