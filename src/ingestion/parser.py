"""PDF parsing with LlamaParse.

This module wraps LlamaParse to parse PDFs and create TextNodes with proper
SOURCE relationships for document tracking.
"""

import os
from pathlib import Path
from typing import List
from llama_cloud_services import LlamaParse
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo

# Import configuration
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import (
    LLAMAPARSE_API_KEY,
    LLAMAPARSE_BASE_URL,
    LLAMAPARSE_MODEL,
    LLAMAPARSE_PARSE_MODE,
    LLAMAPARSE_HIGH_RES_OCR,
    LLAMAPARSE_TABLE_EXTRACTION,
    LLAMAPARSE_OUTPUT_TABLES_HTML,
    IMAGE_DIR,
    IMAGE_STORAGE_FORMAT,
)
from .image_storage import get_image_storage_manager


# Initialize parser with configuration (singleton)
_parser = None


def get_parser() -> LlamaParse:
    """Get or create the LlamaParse parser instance."""
    global _parser
    if _parser is None:
        _parser = LlamaParse(
            api_key=LLAMAPARSE_API_KEY,
            base_url=LLAMAPARSE_BASE_URL,
            parse_mode=LLAMAPARSE_PARSE_MODE,
            model=LLAMAPARSE_MODEL,
            high_res_ocr=LLAMAPARSE_HIGH_RES_OCR,
            outlined_table_extraction=LLAMAPARSE_TABLE_EXTRACTION,
            output_tables_as_HTML=LLAMAPARSE_OUTPUT_TABLES_HTML,
        )
    return _parser


async def parse_pdf(pdf_path: str, doc_id: str) -> List[TextNode]:
    """Parse a PDF file and return TextNodes with SOURCE relationships.
    
    This function:
    1. Parses the PDF using LlamaParse
    2. Extracts text nodes (markdown) per page
    3. Downloads page screenshots to a document-specific directory
    4. Sets the SOURCE relationship on each node to enable document tracking
    5. Adds metadata (document_id, filename, image_path) to each node
    
    Args:
        pdf_path: Path to the PDF file to parse
        doc_id: Unique document identifier (UUID)
        
    Returns:
        List of TextNode objects with proper SOURCE relationships set
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If parsing fails
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    parser = get_parser()
    
    # Parse the PDF
    results = await parser.aparse([pdf_path])
    if not results:
        raise Exception(f"Failed to parse PDF: {pdf_path}")
    
    result = results[0]
    
    # Create document-specific image directory
    doc_image_dir = Path(IMAGE_DIR) / doc_id
    doc_image_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract text and images
    text_nodes = result.get_markdown_nodes(split_by_page=True)
    image_nodes = await result.aget_image_nodes(
        include_object_images=False,
        include_screenshot_images=True,
        image_download_dir=str(doc_image_dir),
    )
    
    # Set relationships and metadata on each node
    processed_nodes = []
    filename = os.path.basename(pdf_path)
    
    for i, (text_node, image_node) in enumerate(zip(text_nodes, image_nodes)):
        # CRITICAL: Set SOURCE relationship for document tracking
        # This allows delete_ref_doc() to work properly
        text_node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
            node_id=doc_id
        )
        
        # Add metadata for querying and tracking
        text_node.metadata["document_id"] = doc_id
        text_node.metadata["filename"] = filename
        text_node.metadata["page_number"] = i + 1
        text_node.metadata["image_path"] = image_node.image_path
        
        # If base64 format, encode and store in metadata using ImageStorageManager
        if IMAGE_STORAGE_FORMAT == "base64":
            try:
                storage_manager = get_image_storage_manager()
                # This will compress, resize, and add data URI prefix
                text_node.metadata["image_b64"] = storage_manager._encode_base64(image_node.image_path)
            except Exception as e:
                print(f"Warning: Failed to encode image to base64: {e}")
        
        # CRITICAL: Exclude base64 image from embedding (it's too large!)
        text_node.excluded_embed_metadata_keys = ["image_b64", "image_path"]
        text_node.excluded_llm_metadata_keys = []  # LLM can see everything in prompts
        
        processed_nodes.append(text_node)
    
    return processed_nodes


async def parse_multiple_pdfs(pdf_paths: List[str], doc_ids: List[str]) -> List[TextNode]:
    """Parse multiple PDFs in batch.
    
    This is useful for initial bulk ingestion.
    
    Args:
        pdf_paths: List of PDF file paths
        doc_ids: List of document IDs (must match length of pdf_paths)
        
    Returns:
        Combined list of all TextNodes from all documents
        
    Raises:
        ValueError: If lengths of pdf_paths and doc_ids don't match
    """
    if len(pdf_paths) != len(doc_ids):
        raise ValueError("Number of PDF paths must match number of document IDs")
    
    all_nodes = []
    for pdf_path, doc_id in zip(pdf_paths, doc_ids):
        nodes = await parse_pdf(pdf_path, doc_id)
        all_nodes.extend(nodes)
    
    return all_nodes

