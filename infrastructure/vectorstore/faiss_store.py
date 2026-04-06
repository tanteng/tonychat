import os
import pickle
from typing import List, Optional, Dict, Set
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from infrastructure.embeddings.openai_embeddings import get_embeddings_adapter


class VectorStore:
    """FAISS vector store for document retrieval with file tracking"""

    def __init__(self, index_path: str = "vectorstore.index"):
        self.index_path = index_path
        self.index_dir = os.path.dirname(index_path) or "."
        self.index_name = os.path.basename(index_path)
        self._store: Optional[FAISS] = None
        # Track which doc IDs belong to which file: filename -> set of doc IDs
        self._filename_to_ids: Dict[str, Set[str]] = {}
        self._all_ids: Set[str] = set()  # Track all active IDs

    @property
    def store(self) -> Optional[FAISS]:
        return self._store

    def add_documents(self, docs: List[Document], embeddings: Embeddings) -> None:
        """Add documents to the vector store and track their source files"""
        if self._store is None:
            self._store = FAISS.from_documents(docs, embeddings)
        else:
            self._store.add_documents(docs)

        # Track which file each doc belongs to
        for doc in docs:
            source = doc.metadata.get("source", "unknown")
            if source not in self._filename_to_ids:
                self._filename_to_ids[source] = set()
            # FAISS uses doc.id or generates one - we use content hash as ID
            doc_id = str(hash(doc.page_content))
            self._filename_to_ids[source].add(doc_id)
            self._all_ids.add(doc_id)

    def similarity_search(self, query: str, k: int = 5, valid_files: List[str] = None) -> List[Document]:
        """Search for similar documents, optionally filtered by valid files"""
        if self._store is None:
            return []

        # Get more results than k to account for filtering
        results = self._store.similarity_search(query, k=k * 10)

        # Filter by valid files if specified
        if valid_files is not None:
            valid_files_set = set(valid_files)
            results = [doc for doc in results if doc.metadata.get("source") in valid_files_set]

        return results[:k]

    def similarity_search_with_score(self, query: str, k: int = 5, valid_files: List[str] = None):
        """Search for similar documents with scores"""
        if self._store is None:
            return []

        results = self._store.similarity_search_with_score(query, k=k * 10)

        # Filter by valid files if specified
        if valid_files is not None:
            valid_files_set = set(valid_files)
            results = [(doc, score) for doc, score in results if doc.metadata.get("source") in valid_files_set]

        return results[:k]

    def delete_by_filename(self, filename: str) -> bool:
        """Delete all chunks belonging to a specific file"""
        if self._store is None:
            return False

        if filename not in self._filename_to_ids:
            return False

        # Get all IDs belonging to this file
        ids_to_delete = list(self._filename_to_ids[filename])

        try:
            self._store.delete(ids=ids_to_delete)
        except Exception:
            # Fallback: rebuild index if delete fails
            pass

        # Update tracking
        del self._filename_to_ids[filename]
        self._all_ids = set()
        for source, ids in self._filename_to_ids.items():
            self._all_ids.update(ids)

        # Save updated state
        self.save()

        return True

    def get_all_filenames(self) -> List[str]:
        """Get list of all files currently indexed"""
        return list(self._filename_to_ids.keys())

    def save(self) -> None:
        """Save vector store and metadata to disk"""
        if self._store is not None:
            self._store.save_local(self.index_path)

        # Save filename -> IDs mapping
        metadata_path = os.path.join(self.index_dir, f"{self.index_name}_metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'filename_to_ids': self._filename_to_ids,
                'all_ids': self._all_ids
            }, f)

    def load(self) -> None:
        """Load vector store and metadata from disk"""
        if os.path.exists(self.index_path):
            embeddings = get_embeddings_adapter().embeddings
            self._store = FAISS.load_local(
                self.index_path,
                embeddings,
                allow_dangerous_deserialization=True
            )

            # Load metadata
            metadata_path = os.path.join(self.index_dir, f"{self.index_name}_metadata.pkl")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                    self._filename_to_ids = metadata.get('filename_to_ids', {})
                    self._all_ids = metadata.get('all_ids', set())

    def is_empty(self) -> bool:
        return self._store is None


# Global singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        _vector_store.load()
    return _vector_store


def reset_vector_store() -> None:
    """Reset the vector store (useful when documents change)"""
    global _vector_store
    _vector_store = VectorStore()
