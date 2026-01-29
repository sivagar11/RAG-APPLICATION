"""Ingestion module for document management.

This module provides the core functionality for adding, deleting, updating,
and listing documents in the RAG system.

Main exports:
    - add_document: Add a new PDF document to the index
    - delete_document: Remove a document and its images
    - update_document: Replace an existing document
    - list_documents: Get all indexed documents
    - get_index: Access the vector store index
"""

from .document_manager import (
    add_document,
    delete_document,
    update_document,
    list_documents,
    get_document_info,
)
from .index_manager import get_index, reload_index

__all__ = [
    "add_document",
    "delete_document",
    "update_document",
    "list_documents",
    "get_document_info",
    "get_index",
    "reload_index",
]

