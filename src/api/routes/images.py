"""Image serving endpoints."""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ingestion import get_document_info
from config import IMAGE_DIR
from ..dependencies import resolve_image_path

router = APIRouter(prefix="/images", tags=["images"])


@router.get(
    "/{doc_id}/{page_number}",
    response_class=FileResponse,
    summary="Get page image",
    description="Retrieve the image for a specific page of a document."
)
def get_page_image(doc_id: str, page_number: int):
    """Get the image for a specific page of a document."""
    try:
        # Get document info
        doc_info = get_document_info(doc_id)
        
        if not doc_info:
            raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
        
        # Find the page
        page = next((p for p in doc_info['pages'] if p['page_number'] == page_number), None)
        
        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_number} not found in document {doc_id}"
            )
        
        # Get image path
        image_path_str = page['image_path']
        
        if not image_path_str:
            raise HTTPException(
                status_code=404,
                detail=f"No image available for page {page_number}"
            )
        
        # Resolve image path
        try:
            image_path = resolve_image_path(image_path_str)
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found for page {page_number}"
            )
        
        # Return image file
        return FileResponse(
            path=str(image_path),
            media_type="image/jpeg",
            filename=f"{doc_id}_page_{page_number}.jpg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve image: {str(e)}"
        )


@router.get(
    "/path/{image_filename}",
    response_class=FileResponse,
    summary="Get image by filename",
    description="Retrieve an image by its filename (searches all document directories)."
)
def get_image_by_filename(image_filename: str):
    """Get an image by its filename."""
    try:
        # Search for image in IMAGE_DIR and subdirectories
        image_dir = Path(IMAGE_DIR)
        
        # Try direct path
        direct_path = image_dir / image_filename
        if direct_path.exists():
            return FileResponse(
                path=str(direct_path),
                media_type="image/jpeg",
                filename=image_filename
            )
        
        # Search in subdirectories
        for doc_dir in image_dir.iterdir():
            if doc_dir.is_dir():
                possible_path = doc_dir / image_filename
                if possible_path.exists():
                    return FileResponse(
                        path=str(possible_path),
                        media_type="image/jpeg",
                        filename=image_filename
                    )
        
        raise HTTPException(
            status_code=404,
            detail=f"Image not found: {image_filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve image: {str(e)}"
        )

