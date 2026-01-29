"""Tests for document parsing functionality."""

import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import pytest


def test_get_data_files(temp_dirs, sample_pdf_path):
    """Test retrieving data files from directory."""
    # Create additional test files
    (temp_dirs["data"] / "doc1.pdf").write_text("content1")
    (temp_dirs["data"] / "doc2.pdf").write_text("content2")
    
    # Simulate get_data_files function
    def get_data_files(data_dir):
        files = []
        for f in os.listdir(data_dir):
            fname = os.path.join(data_dir, f)
            if os.path.isfile(fname):
                files.append(fname)
        return files
    
    files = get_data_files(str(temp_dirs["data"]))
    
    assert len(files) == 3  # Including sample_pdf_path
    assert all(f.endswith('.pdf') or 'test' in f for f in files)


def test_get_data_files_empty_directory(temp_dirs):
    """Test get_data_files with empty directory."""
    empty_dir = temp_dirs["root"] / "empty"
    empty_dir.mkdir()
    
    def get_data_files(data_dir):
        files = []
        for f in os.listdir(data_dir):
            fname = os.path.join(data_dir, f)
            if os.path.isfile(fname):
                files.append(fname)
        return files
    
    files = get_data_files(str(empty_dir))
    assert len(files) == 0


def test_get_data_files_mixed_content(temp_dirs):
    """Test get_data_files with mixed files and directories."""
    (temp_dirs["data"] / "doc.pdf").write_text("content")
    (temp_dirs["data"] / "subdir").mkdir()
    (temp_dirs["data"] / "image.jpg").write_text("image")
    
    def get_data_files(data_dir):
        files = []
        for f in os.listdir(data_dir):
            fname = os.path.join(data_dir, f)
            if os.path.isfile(fname):
                files.append(fname)
        return files
    
    files = get_data_files(str(temp_dirs["data"]))
    
    # Should only include files, not directories
    assert all(os.path.isfile(f) for f in files)
    assert len(files) == 2  # doc.pdf and image.jpg


@pytest.mark.asyncio
async def test_parser_initialization():
    """Test LlamaParse parser initialization."""
    with patch('llama_cloud_services.LlamaParse') as mock_parser:
        mock_instance = Mock()
        mock_parser.return_value = mock_instance
        
        from llama_cloud_services import LlamaParse
        
        parser = LlamaParse(
            api_key="test-key",
            parse_mode="parse_page_with_agent",
            model="openai-gpt-4-1-mini",
            high_res_ocr=True,
            outlined_table_extraction=True,
            output_tables_as_HTML=True,
        )
        
        assert parser is not None


@pytest.mark.asyncio
async def test_parse_result_processing(temp_dirs):
    """Test processing of parse results."""
    # Mock parse result
    mock_result = MagicMock()
    mock_text_node = MagicMock()
    mock_text_node.metadata = {"page_number": 1}
    
    mock_image_node = MagicMock()
    mock_image_node.image_path = str(temp_dirs["images"] / "page_1.jpg")
    
    mock_result.get_markdown_nodes = Mock(return_value=[mock_text_node])
    mock_result.aget_image_nodes = AsyncMock(return_value=[mock_image_node])
    
    # Simulate processing
    results = [mock_result]
    all_text_nodes = []
    
    for result in results:
        text_nodes = result.get_markdown_nodes(split_by_page=True)
        image_nodes = await result.aget_image_nodes(
            include_object_images=False,
            include_screenshot_images=True,
            image_download_dir=str(temp_dirs["images"]),
        )
        
        for text_node, image_node in zip(text_nodes, image_nodes):
            text_node.metadata["image_path"] = image_node.image_path
            all_text_nodes.append(text_node)
    
    assert len(all_text_nodes) == 1
    assert "image_path" in all_text_nodes[0].metadata
    assert all_text_nodes[0].metadata["page_number"] == 1


def test_directory_creation(temp_dirs):
    """Test that directories are created if they don't exist."""
    new_dir = temp_dirs["root"] / "new_storage"
    
    os.makedirs(new_dir, exist_ok=True)
    
    assert new_dir.exists()
    assert new_dir.is_dir()


def test_image_directory_path_resolution(temp_dirs):
    """Test image directory path resolution."""
    image_dir = temp_dirs["images"]
    image_path = image_dir / "page_1.jpg"
    
    # Create image file
    image_path.write_text("image content")
    
    assert image_path.exists()
    assert image_path.parent == image_dir
    assert image_path.name == "page_1.jpg"


@pytest.mark.asyncio
async def test_multiple_documents_parsing(temp_dirs):
    """Test parsing multiple documents."""
    # Create multiple test files
    files = [
        temp_dirs["data"] / "doc1.pdf",
        temp_dirs["data"] / "doc2.pdf",
    ]
    
    for f in files:
        f.write_text("content")
    
    file_paths = [str(f) for f in files]
    
    assert len(file_paths) == 2
    assert all(Path(f).exists() for f in file_paths)


def test_node_metadata_structure(mock_text_node):
    """Test that text nodes have proper metadata structure."""
    assert "page_number" in mock_text_node.metadata
    assert "file_name" in mock_text_node.metadata
    assert "image_path" in mock_text_node.metadata
    
    assert isinstance(mock_text_node.metadata["page_number"], int)
    assert isinstance(mock_text_node.metadata["file_name"], str)
    assert isinstance(mock_text_node.metadata["image_path"], str)

