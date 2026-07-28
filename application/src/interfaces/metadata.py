from abc import ABC, abstractmethod
from enum import StrEnum, auto


class ImgStatus(StrEnum):
    FAILED = auto()
    UPLOAD_PENDING = auto()
    UPLOADED = auto()
    PROCESSING = auto()
    COMPLETED = auto()


class Metadata(ABC):
    @abstractmethod
    def initialize_record(
        self,
        image_id: str,
        object_key: str,
        filename: str,
        status: ImgStatus = ImgStatus.UPLOAD_PENDING,
    ) -> None:
        """Creates the initial metadata record"""
