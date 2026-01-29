"""Image storage management for different backends.

Supports:
- Local filesystem storage
- S3/R2 cloud storage
- Base64 encoding for vector DB payloads
- Hybrid approach (thumbnails + S3)
"""

import os
import base64
from pathlib import Path
from typing import Optional, Dict, Tuple
from PIL import Image
from io import BytesIO

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import (
    IMAGE_STORAGE_TYPE,
    IMAGE_STORAGE_FORMAT,
    IMAGE_DIR,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    S3_BUCKET_NAME,
    S3_ENDPOINT_URL,
)


class ImageStorageManager:
    """Manages image storage across different backends."""
    
    def __init__(self):
        self.storage_type = IMAGE_STORAGE_TYPE
        self.storage_format = IMAGE_STORAGE_FORMAT
        
        if self.storage_type in ["s3", "r2"]:
            self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3/R2 client."""
        try:
            import boto3
        except ImportError:
            raise ImportError("boto3 not installed. Run: pip install boto3")
        
        # For Cloudflare R2 or other S3-compatible services
        if S3_ENDPOINT_URL:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=S3_ENDPOINT_URL,
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION,
            )
        else:
            # Standard AWS S3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION,
            )
        
        # Create bucket if it doesn't exist
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure S3 bucket exists."""
        try:
            self.s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
        except:
            try:
                self.s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
            except Exception as e:
                print(f"Warning: Could not create S3 bucket: {e}")
    
    def store_image(
        self, 
        image_path: str, 
        doc_id: str, 
        page_number: int
    ) -> Dict[str, str]:
        """Store image and return metadata.
        
        Args:
            image_path: Path to the image file
            doc_id: Document ID
            page_number: Page number
            
        Returns:
            Dictionary with storage metadata:
            {
                "url": "s3://..." or "file://..." or None,
                "base64": "..." or None,
                "thumbnail_b64": "..." or None,
                "storage_type": "s3" or "local" or "vector_db"
            }
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        metadata = {
            "url": None,
            "base64": None,
            "thumbnail_b64": None,
            "storage_type": self.storage_type,
        }
        
        if self.storage_type == "local":
            # Local filesystem storage (current implementation)
            metadata["url"] = image_path
            
            if self.storage_format == "base64":
                metadata["base64"] = self._encode_base64(image_path)
            elif self.storage_format == "hybrid":
                metadata["thumbnail_b64"] = self._create_thumbnail_b64(image_path)
        
        elif self.storage_type in ["s3", "r2"]:
            # Upload to S3/R2
            s3_key = f"{doc_id}/page_{page_number}.jpg"
            self._upload_to_s3(image_path, s3_key)
            
            if S3_ENDPOINT_URL:
                # For R2 or custom endpoints
                metadata["url"] = f"{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{s3_key}"
            else:
                # Standard S3 URL
                metadata["url"] = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
            
            if self.storage_format == "hybrid":
                # Store thumbnail for fast previews
                metadata["thumbnail_b64"] = self._create_thumbnail_b64(image_path)
        
        return metadata
    
    def _encode_base64(self, image_path: str, max_size: int = 800, quality: int = 60) -> str:
        """Encode image as base64 string with compression.
        
        Args:
            image_path: Path to image file
            max_size: Maximum width/height (images will be resized to fit)
            quality: JPEG quality (1-100, lower = smaller file)
            
        Returns:
            Base64 encoded string (data URI format)
        """
        # Open and compress image
        img = Image.open(image_path)
        
        # Resize if too large (maintain aspect ratio)
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to RGB (in case of RGBA or other formats)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as JPEG with compression
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        # Encode to base64 with data URI prefix
        image_b64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/jpeg;base64,{image_b64}"
    
    def _create_thumbnail_b64(
        self, 
        image_path: str, 
        size: Tuple[int, int] = (200, 200)
    ) -> str:
        """Create thumbnail and encode as base64.
        
        Args:
            image_path: Path to image file
            size: Thumbnail size (width, height)
            
        Returns:
            Base64 encoded thumbnail
        """
        img = Image.open(image_path)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to JPEG bytes
        buffer = BytesIO()
        img.convert('RGB').save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def _upload_to_s3(self, image_path: str, s3_key: str):
        """Upload image to S3/R2.
        
        Args:
            image_path: Path to local image file
            s3_key: S3 object key (path in bucket)
        """
        with open(image_path, 'rb') as f:
            self.s3_client.upload_fileobj(
                f,
                S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={'ContentType': 'image/jpeg'}
            )
    
    def get_image(self, image_metadata: Dict[str, str]) -> str:
        """Retrieve image path or data.
        
        Args:
            image_metadata: Metadata dict from store_image()
            
        Returns:
            Local path, URL, or base64 data
        """
        if image_metadata.get("url"):
            return image_metadata["url"]
        elif image_metadata.get("base64"):
            return image_metadata["base64"]
        elif image_metadata.get("thumbnail_b64"):
            return image_metadata["thumbnail_b64"]
        else:
            raise ValueError("No image data in metadata")
    
    def delete_images(self, doc_id: str) -> int:
        """Delete all images for a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Number of images deleted
        """
        deleted_count = 0
        
        if self.storage_type == "local":
            # Delete local directory
            doc_image_dir = Path(IMAGE_DIR) / doc_id
            if doc_image_dir.exists():
                import shutil
                shutil.rmtree(doc_image_dir)
                deleted_count = len(list(doc_image_dir.glob("*.jpg")))
        
        elif self.storage_type in ["s3", "r2"]:
            # Delete from S3
            try:
                # List all objects with prefix
                response = self.s3_client.list_objects_v2(
                    Bucket=S3_BUCKET_NAME,
                    Prefix=f"{doc_id}/"
                )
                
                if 'Contents' in response:
                    # Delete all objects
                    objects = [{'Key': obj['Key']} for obj in response['Contents']]
                    self.s3_client.delete_objects(
                        Bucket=S3_BUCKET_NAME,
                        Delete={'Objects': objects}
                    )
                    deleted_count = len(objects)
            except Exception as e:
                print(f"Warning: Failed to delete S3 images: {e}")
        
        return deleted_count


# Global instance
_image_storage_manager = None


def get_image_storage_manager() -> ImageStorageManager:
    """Get or create image storage manager singleton."""
    global _image_storage_manager
    if _image_storage_manager is None:
        _image_storage_manager = ImageStorageManager()
    return _image_storage_manager

