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

    @abstractmethod
    def change_status_conditional(
        self, image_id: str, new_status: ImgStatus, previous_status: ImgStatus
    ) -> bool:
        """
        Change the status of the image only if current status is equal to previous status
        This is to prevent race conditions
        Returns false if conditional update fails, throws exception if any other error occured
        """
        pass

    @abstractmethod
    def complete_initial_upload(self, image_id: str) -> bool:
        """
        Changes the image state from upload_pending to uploaded
        Also removes expiry_at TTL from the record
        """
        pass
