"""Document management endpoints."""

import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ingestion import (
    add_document,
    delete_document,
    update_document,
    list_documents,
    get_document_info,
)
from ..models import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DeleteDocumentResponse,
    UpdateDocumentResponse,
    DocumentInfo,
    PageInfo,
)
from ..dependencies import validate_pdf_file, save_upload_file, cleanup_temp_file

router = APIRouter(prefix="/documents", tags=["documents"])


async def process_document_upload(file_path: str, doc_id: Optional[str] = None):
    """Background task to process uploaded document.
    
    Args:
        file_path: Path to uploaded PDF file
        doc_id: Optional document ID for updates
    """
    try:
        # Add document to index
        result = await add_document(file_path, doc_id=doc_id)
        print(f"✅ Document processed: {result['document_id']}")
    except Exception as e:
        print(f"❌ Error processing document: {e}")
    finally:
        # Cleanup temp file
        cleanup_temp_file(file_path)


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=202,
    summary="Upload a new document",
    description="Upload a PDF document for indexing. Processing happens in background."
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF file to upload")
):
    """Upload and process a new PDF document."""
    # Validate file
    validate_pdf_file(file)
    
    # Save to temporary location
    try:
        temp_path = await save_upload_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Process in background
    background_tasks.add_task(process_document_upload, temp_path)
    
    # Return immediate response
    from datetime import datetime
    import uuid
    
    # Generate preliminary doc_id
    doc_id = str(uuid.uuid4())
    
    return DocumentUploadResponse(
        document_id=doc_id,
        filename=file.filename or "unknown.pdf",
        page_count=0,  # Will be updated after processing
        status="processing",
        timestamp=datetime.now().isoformat()
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all documents",
    description="Get a list of all indexed documents."
)
def list_all_documents():
    """List all documents in the index."""
    try:
        docs = list_documents()
        
        # Convert to response model
        document_list = [
            DocumentInfo(
                document_id=doc_id,
                filename=doc_info['metadata'].get('filename', 'unknown'),
                page_count=doc_info['page_count']
            )
            for doc_id, doc_info in docs.items()
        ]
        
        return DocumentListResponse(
            total_documents=len(document_list),
            documents=document_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get(
    "/{doc_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    description="Get detailed information about a specific document."
)
def get_document(doc_id: str):
    """Get detailed information about a document."""
    try:
        info = get_document_info(doc_id)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
        
        # Convert to response model
        pages = [
            PageInfo(
                page_number=page['page_number'],
                image_path=page['image_path'],
                text_preview=page['text_preview']
            )
            for page in info['pages']
        ]
        
        return DocumentDetailResponse(
            document_id=info['document_id'],
            filename=info['filename'],
            page_count=info['page_count'],
            node_ids=info['node_ids'],
            pages=pages
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document info: {str(e)}")


@router.delete(
    "/{doc_id}",
    response_model=DeleteDocumentResponse,
    summary="Delete a document",
    description="Delete a document and its associated images from the index."
)
def remove_document(doc_id: str):
    """Delete a document from the index."""
    try:
        result = delete_document(doc_id)
        
        return DeleteDocumentResponse(
            document_id=result['document_id'],
            status=result['status'],
            images_deleted=result['images_deleted'],
            timestamp=result['timestamp']
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.put(
    "/{doc_id}",
    response_model=UpdateDocumentResponse,
    status_code=202,
    summary="Update a document",
    description="Replace an existing document with a new PDF. Processing happens in background."
)
async def replace_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="New PDF file")
):
    """Update an existing document with a new PDF."""
    # Validate file
    validate_pdf_file(file)
    
    # Check if document exists
    try:
        info = get_document_info(doc_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    
    # Save to temporary location
    try:
        temp_path = await save_upload_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Process update in background
    async def process_update(file_path: str, document_id: str):
        try:
            result = await update_document(document_id, file_path)
            print(f"✅ Document updated: {result['document_id']}")
        except Exception as e:
            print(f"❌ Error updating document: {e}")
        finally:
            cleanup_temp_file(file_path)
    
    background_tasks.add_task(process_update, temp_path, doc_id)
    
    # Return immediate response
    from datetime import datetime
    
    return UpdateDocumentResponse(
        document_id=doc_id,
        filename=file.filename or "unknown.pdf",
        page_count=0,  # Will be updated after processing
        status="processing",
        old_images_deleted=0,  # Will be updated after processing
        timestamp=datetime.now().isoformat()
    )

