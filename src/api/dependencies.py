"""Shared dependencies for FastAPI routes."""

import os
import tempfile
from pathlib import Path
from typing import Generator
from fastapi import UploadFile, HTTPException

from config import IMAGE_DIR


def validate_pdf_file(file: UploadFile) -> None:
    """Validate that uploaded file is a PDF.
    
    Args:
        file: Uploaded file object
        
    Raises:
        HTTPException: If file is not a PDF
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Expected PDF, got: {file.filename}"
        )
    
    # Check file size (max 100MB)
    if file.size and file.size > 100 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 100MB"
        )


async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temporary location.
    
    Args:
        upload_file: Uploaded file object
        
    Returns:
        Path to saved temporary file
        
    Raises:
        HTTPException: If file cannot be saved
    """
    try:
        # Create temp file with PDF extension
        suffix = Path(upload_file.filename or "document.pdf").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            # Read and write in chunks to handle large files
            content = await upload_file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        return tmp_path
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )


def cleanup_temp_file(file_path: str) -> None:
    """Remove temporary file.
    
    Args:
        file_path: Path to temporary file
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Log but don't raise - cleanup failures shouldn't break the API
        print(f"Warning: Failed to cleanup temp file {file_path}: {e}")


def resolve_image_path(image_path: str) -> Path:
    """Resolve image path to actual file location.
    
    Args:
        image_path: Stored image path from metadata
        
    Returns:
        Resolved Path object to image file
        
    Raises:
        FileNotFoundError: If image cannot be found
    """
    img_path = Path(image_path).expanduser()
    
    # If path exists, return it
    if img_path.exists():
        return img_path
    
    # Try recovering by filename search in IMAGE_DIR
    filename = img_path.name
    possible_path = Path(IMAGE_DIR) / filename
    
    if possible_path.exists():
        return possible_path
    
    # Try searching in document subdirectories
    for doc_dir in Path(IMAGE_DIR).iterdir():
        if doc_dir.is_dir():
            possible_path = doc_dir / filename
            if possible_path.exists():
                return possible_path
    
    raise FileNotFoundError(f"Image not found: {filename}")

