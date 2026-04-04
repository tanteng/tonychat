from typing import List, Optional
from domain.entities.document import Document
from domain.repositories.document_repository import DocumentRepository
from infrastructure.document_loading.document_loader import DocumentLoader, get_document_loader
from infrastructure.vectorstore.faiss_store import VectorStore, get_vector_store
from infrastructure.embeddings.openai_embeddings import EmbeddingsAdapter, get_embeddings_adapter
from infrastructure.persistence.file_repository import FileDocumentRepository, get_document_repository


class DocumentService:
    """Service for document processing and indexing"""

    def __init__(
        self,
        repository: Optional[FileDocumentRepository] = None,
        loader: Optional[DocumentLoader] = None,
        vector_store: Optional[VectorStore] = None,
        embeddings: Optional[EmbeddingsAdapter] = None
    ):
        self.repository = repository or get_document_repository()
        self.loader = loader or get_document_loader()
        self.vector_store = vector_store or get_vector_store()
        self.embeddings = embeddings or get_embeddings_adapter()

    def load_and_index_document(self, filename: str) -> Document:
        """Load a document from filesystem and index it in vector store"""
        # Get document from repository
        document = self.repository.save_from_upload(filename)

        # Load and split the document
        docs = self.loader.load_file(document.file_path)

        # Update chunk count
        document.chunk_count = len(docs)

        # Add to vector store
        if docs:
            self.vector_store.add_documents(docs, self.embeddings.embeddings)
            self.vector_store.save()

        return document

    def get_all_documents(self) -> List[Document]:
        """Get all documents"""
        return self.repository.list_all()

    def delete_document(self, filename: str) -> None:
        """Delete a document from both file system and vector store"""
        # Delete from file system
        self.repository.delete(filename)
        # Delete from vector store
        self.vector_store.delete_by_filename(filename)

    def is_vector_store_empty(self) -> bool:
        """Check if vector store has any documents"""
        return self.vector_store.is_empty()

    def reset_index(self) -> None:
        """Reset the vector store index"""
        from infrastructure.vectorstore.faiss_store import reset_vector_store
        reset_vector_store()


# Global singleton instance
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
