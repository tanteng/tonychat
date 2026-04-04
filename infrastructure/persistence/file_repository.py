import os
import uuid
from datetime import datetime
from typing import List, Optional
from domain.entities.document import Document
from domain.repositories.document_repository import DocumentRepository


class FileDocumentRepository(DocumentRepository):
    """File-based implementation of DocumentRepository"""

    def __init__(self, upload_folder: str = "uploads"):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def _get_file_type(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        return ext.lstrip('.')

    def _read_file_content(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def save(self, document: Document) -> None:
        # Document is already saved to file system by caller
        pass

    def save_from_upload(self, filename: str) -> Document:
        """Save a newly uploaded file and create document"""
        file_path = os.path.join(self.upload_folder, filename)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        content = self._read_file_content(file_path)
        doc_id = self._generate_id()

        document = Document(
            id=doc_id,
            filename=filename,
            file_path=file_path,
            content=content,
            file_type=self._get_file_type(filename),
            uploaded_at=datetime.now()
        )

        return document

    def get_by_id(self, doc_id: str) -> Optional[Document]:
        # For now, we don't track by ID in file-based storage
        return None

    def get_by_filename(self, filename: str) -> Optional[Document]:
        file_path = os.path.join(self.upload_folder, filename)

        if not os.path.exists(file_path):
            return None

        content = self._read_file_content(file_path)

        return Document(
            id=filename,  # Use filename as ID for lookup
            filename=filename,
            file_path=file_path,
            content=content,
            file_type=self._get_file_type(filename),
            uploaded_at=datetime.fromtimestamp(os.path.getmtime(file_path))
        )

    def list_all(self) -> List[Document]:
        """List all documents in upload folder"""
        documents = []

        if not os.path.exists(self.upload_folder):
            return documents

        for filename in os.listdir(self.upload_folder):
            file_path = os.path.join(self.upload_folder, filename)

            if os.path.isfile(file_path):
                try:
                    content = self._read_file_content(file_path)
                    doc = Document(
                        id=filename,
                        filename=filename,
                        file_path=file_path,
                        content=content,
                        file_type=self._get_file_type(filename),
                        uploaded_at=datetime.fromtimestamp(os.path.getmtime(file_path))
                    )
                    documents.append(doc)
                except Exception:
                    continue

        return documents

    def delete(self, doc_id: str) -> None:
        file_path = os.path.join(self.upload_folder, doc_id)
        if os.path.exists(file_path):
            os.remove(file_path)

    def exists(self, filename: str) -> bool:
        file_path = os.path.join(self.upload_folder, filename)
        return os.path.exists(file_path)


# Global singleton instance
_document_repository: Optional[FileDocumentRepository] = None


def get_document_repository() -> FileDocumentRepository:
    global _document_repository
    if _document_repository is None:
        _document_repository = FileDocumentRepository()
    return _document_repository
