import os
from typing import List, Optional
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader
)
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentLoader:
    """Document loader using LangChain loaders"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def load_file(self, file_path: str) -> List[Document]:
        """Load a single file and return documents"""
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif ext == '.docx' or ext == '.doc':
            loader = UnstructuredWordDocumentLoader(file_path)
        elif ext == '.txt' or ext == '.md':
            loader = TextLoader(file_path, encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        docs = loader.load()

        # Add source metadata to each document
        for doc in docs:
            doc.metadata["source"] = filename

        return self.split_documents(docs)

    def load_content(self, content: str, filename: str) -> List[Document]:
        """Load content directly and return split documents"""
        doc = Document(page_content=content, metadata={"source": filename})
        return self.split_documents([doc])

    def split_documents(self, docs: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        return self.text_splitter.split_documents(docs)


# Global singleton instance
_document_loader: Optional[DocumentLoader] = None


def get_document_loader() -> DocumentLoader:
    global _document_loader
    if _document_loader is None:
        _document_loader = DocumentLoader()
    return _document_loader
