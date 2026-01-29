"""Pydantic models for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# === Request Models ===

class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""
    query: str = Field(..., min_length=1, max_length=1000, description="Query text")
    similarity_top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")
    include_images: bool = Field(True, description="Whether to include images in response")


# === Response Models ===

class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    page_count: int = Field(..., description="Number of pages in document")
    status: str = Field(..., description="Processing status")
    timestamp: str = Field(..., description="Upload timestamp")


class DocumentInfo(BaseModel):
    """Model for document information."""
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    page_count: int = Field(..., description="Number of pages")


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    total_documents: int = Field(..., description="Total number of documents")
    documents: List[DocumentInfo] = Field(..., description="List of documents")


class PageInfo(BaseModel):
    """Model for page information."""
    page_number: int = Field(..., description="Page number")
    image_path: str = Field(..., description="Path to page image")
    text_preview: str = Field(..., description="Text preview of page")


class DocumentDetailResponse(BaseModel):
    """Response model for detailed document information."""
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    page_count: int = Field(..., description="Number of pages")
    node_ids: List[str] = Field(..., description="Associated node IDs")
    pages: List[PageInfo] = Field(..., description="Page information")


class DeleteDocumentResponse(BaseModel):
    """Response model for document deletion."""
    document_id: str = Field(..., description="Deleted document ID")
    status: str = Field(..., description="Deletion status")
    images_deleted: int = Field(..., description="Number of images deleted")
    timestamp: str = Field(..., description="Deletion timestamp")


class UpdateDocumentResponse(BaseModel):
    """Response model for document update."""
    document_id: str = Field(..., description="Updated document ID")
    filename: str = Field(..., description="New filename")
    page_count: int = Field(..., description="New page count")
    status: str = Field(..., description="Update status")
    old_images_deleted: int = Field(..., description="Number of old images deleted")
    timestamp: str = Field(..., description="Update timestamp")


class SourceNode(BaseModel):
    """Model for source node information."""
    page_number: Optional[int] = Field(None, description="Page number")
    filename: Optional[str] = Field(None, description="Source filename")
    image_path: Optional[str] = Field(None, description="Path to page image")
    text_preview: str = Field(..., description="Text content preview")
    score: Optional[float] = Field(None, description="Similarity score")


class QueryResponse(BaseModel):
    """Response model for query results."""
    query: str = Field(..., description="Original query text")
    answer: str = Field(..., description="Generated answer")
    source_nodes: List[SourceNode] = Field(..., description="Source nodes used")
    processing_time: float = Field(..., description="Processing time in seconds")


class ErrorResponse(BaseModel):
    """Model for error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    documents_indexed: int = Field(..., description="Number of documents in index")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

