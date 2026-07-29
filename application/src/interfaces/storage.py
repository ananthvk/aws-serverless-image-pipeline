from abc import ABC, abstractmethod
import io

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

    @abstractmethod
    def get_object(self, object_key: str) -> io.BytesIO:
        pass
    
    @abstractmethod
    def save_object(self, object_key: str, body: io.BytesIO):
        pass

    @abstractmethod
    def delete_object(self, object_key: str):
        pass
