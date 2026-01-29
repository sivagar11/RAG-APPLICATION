"""Document management operations.

This module provides CRUD (Create, Read, Update, Delete) operations
for documents in the RAG system.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .parser import parse_pdf
from .index_manager import get_index, persist_index


async def add_document(pdf_path: str, doc_id: Optional[str] = None) -> Dict[str, str]:
    """Add a new document to the index.
    
    This function:
    1. Generates a unique document ID (or uses provided one)
    2. Parses the PDF into TextNodes with SOURCE relationships
    3. Inserts nodes into the vector index
    4. Persists changes to storage
    
    Args:
        pdf_path: Path to the PDF file to add
        doc_id: Optional document ID. If not provided, generates a UUID
        
    Returns:
        Dictionary with document information:
        {
            "document_id": "uuid-string",
            "filename": "manual.pdf",
            "page_count": 42,
            "status": "success"
        }
        
    Raises:
        FileNotFoundError: If PDF doesn't exist
        Exception: If parsing or indexing fails
    """
    # Generate document ID if not provided
    if doc_id is None:
        doc_id = str(uuid.uuid4())
    
    # Parse PDF into nodes with SOURCE relationships
    nodes = await parse_pdf(pdf_path, doc_id)
    
    if not nodes:
        raise Exception(f"No nodes extracted from PDF: {pdf_path}")
    
    # Get index and insert nodes
    index = get_index()
    index.insert_nodes(nodes)
    
    # Persist changes
    persist_index()
    
    return {
        "document_id": doc_id,
        "filename": os.path.basename(pdf_path),
        "page_count": len(nodes),
        "status": "success",
        "timestamp": datetime.now().isoformat()
    }


def delete_document(doc_id: str) -> Dict[str, str]:
    """Delete a document and its associated images.
    
    This function:
    1. Retrieves document information from the index
    2. Deletes associated image files
    3. Removes document from the vector index
    4. Persists changes
    
    Args:
        doc_id: Document ID to delete
        
    Returns:
        Dictionary with deletion information:
        {
            "document_id": "uuid-string",
            "status": "deleted",
            "images_deleted": 42
        }
        
    Raises:
        ValueError: If document doesn't exist
        Exception: If deletion fails
    """
    index = get_index()
    
    # Check if document exists
    doc_info = index.ref_doc_info.get(doc_id)
    if not doc_info:
        raise ValueError(f"Document not found: {doc_id}")
    
    # Delete associated images
    images_deleted = 0
    for node_id in doc_info.node_ids:
        try:
            node = index.docstore.get_node(node_id)
            image_path = node.metadata.get("image_path")
            
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                images_deleted += 1
        except Exception as e:
            # Log but don't fail if image deletion fails
            print(f"Warning: Failed to delete image for node {node_id}: {e}")
    
    # Delete document-specific image directory if it exists
    # Images are stored in IMAGE_DIR/doc_id/
    from config import IMAGE_DIR
    doc_image_dir = Path(IMAGE_DIR) / doc_id
    if doc_image_dir.exists():
        try:
            shutil.rmtree(doc_image_dir)
        except Exception as e:
            print(f"Warning: Failed to delete image directory {doc_image_dir}: {e}")
    
    # Delete from index
    index.delete_ref_doc(doc_id, delete_from_docstore=True)
    
    # Persist changes
    persist_index()
    
    return {
        "document_id": doc_id,
        "status": "deleted",
        "images_deleted": images_deleted,
        "timestamp": datetime.now().isoformat()
    }


async def update_document(doc_id: str, new_pdf_path: str) -> Dict[str, str]:
    """Update a document by replacing it with a new PDF.
    
    This function:
    1. Deletes the old document
    2. Adds the new document with the same ID
    
    Args:
        doc_id: Document ID to update
        new_pdf_path: Path to the new PDF file
        
    Returns:
        Dictionary with update information:
        {
            "document_id": "uuid-string",
            "filename": "new_manual.pdf",
            "page_count": 50,
            "status": "updated"
        }
        
    Raises:
        ValueError: If old document doesn't exist
        FileNotFoundError: If new PDF doesn't exist
        Exception: If update fails
    """
    # Delete old document
    delete_result = delete_document(doc_id)
    
    # Add new document with same ID
    add_result = await add_document(new_pdf_path, doc_id=doc_id)
    
    return {
        "document_id": doc_id,
        "filename": add_result["filename"],
        "page_count": add_result["page_count"],
        "status": "updated",
        "old_images_deleted": delete_result["images_deleted"],
        "timestamp": datetime.now().isoformat()
    }


def list_documents() -> Dict[str, Dict]:
    """List all documents in the index.
    
    Returns:
        Dictionary mapping document IDs to document information:
        {
            "doc-id-1": {
                "node_ids": ["node1", "node2", ...],
                "metadata": {"filename": "manual.pdf", ...},
                "page_count": 42
            },
            ...
        }
    """
    index = get_index()
    ref_doc_info = index.ref_doc_info
    
    documents = {}
    for doc_id, doc_info in ref_doc_info.items():
        # Get additional metadata from first node
        metadata = {}
        page_count = len(doc_info.node_ids)
        
        if doc_info.node_ids:
            try:
                first_node = index.docstore.get_node(doc_info.node_ids[0])
                metadata = {
                    "filename": first_node.metadata.get("filename", "unknown"),
                    "document_id": first_node.metadata.get("document_id", doc_id),
                }
            except Exception:
                pass
        
        documents[doc_id] = {
            "node_ids": doc_info.node_ids,
            "metadata": metadata,
            "page_count": page_count
        }
    
    return documents


def get_document_info(doc_id: str) -> Optional[Dict]:
    """Get detailed information about a specific document.
    
    Args:
        doc_id: Document ID to look up
        
    Returns:
        Dictionary with document details, or None if not found:
        {
            "document_id": "uuid-string",
            "filename": "manual.pdf",
            "page_count": 42,
            "node_ids": ["node1", "node2", ...],
            "pages": [
                {
                    "page_number": 1,
                    "image_path": "/path/to/image.jpg",
                    "text_preview": "First 100 chars..."
                },
                ...
            ]
        }
    """
    index = get_index()
    doc_info = index.ref_doc_info.get(doc_id)
    
    if not doc_info:
        return None
    
    # Gather detailed information
    filename = "unknown"
    pages = []
    
    for node_id in doc_info.node_ids:
        try:
            node = index.docstore.get_node(node_id)
            
            if not filename or filename == "unknown":
                filename = node.metadata.get("filename", "unknown")
            
            pages.append({
                "page_number": node.metadata.get("page_number", 0),
                "image_path": node.metadata.get("image_path", ""),
                "text_preview": node.get_content()[:100] + "..." if len(node.get_content()) > 100 else node.get_content()
            })
        except Exception as e:
            print(f"Warning: Failed to get node {node_id}: {e}")
    
    # Sort pages by page number
    pages.sort(key=lambda x: x["page_number"])
    
    return {
        "document_id": doc_id,
        "filename": filename,
        "page_count": len(pages),
        "node_ids": doc_info.node_ids,
        "pages": pages
    }


def get_document_count() -> int:
    """Get the total number of documents in the index.
    
    Returns:
        Number of documents
    """
    index = get_index()
    return len(index.ref_doc_info)

