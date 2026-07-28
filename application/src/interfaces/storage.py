from abc import ABC, abstractmethod

from pydantic import BaseModel


class PresignedPost(BaseModel):
    url: str
    fields: dict[str, str]


class Storage(ABC):
    @abstractmethod
    def generate_presigned_url(self, object_key: str, mime_type: str) -> PresignedPost:
        """
        Generates a presigned Post form
        """
