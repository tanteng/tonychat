from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.document import Document


class DocumentRepository(ABC):
    """Repository interface for Document entity"""

    @abstractmethod
    def save(self, document: Document) -> None:
        pass

    @abstractmethod
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        pass

    @abstractmethod
    def get_by_filename(self, filename: str) -> Optional[Document]:
        pass

    @abstractmethod
    def list_all(self) -> List[Document]:
        pass

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        pass

    @abstractmethod
    def exists(self, filename: str) -> bool:
        pass
