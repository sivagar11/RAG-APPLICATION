"""Shared test fixtures and configuration for pytest."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock
import pytest


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_dir = tmpdir / "data"
        image_dir = tmpdir / "data_images"
        persist_dir = tmpdir / "storage"
        
        data_dir.mkdir()
        image_dir.mkdir()
        persist_dir.mkdir()
        
        yield {
            "root": tmpdir,
            "data": data_dir,
            "images": image_dir,
            "storage": persist_dir,
        }


@pytest.fixture
def mock_env_vars(temp_dirs, monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("DATA_DIR", str(temp_dirs["data"]))
    monkeypatch.setenv("IMAGE_DIR", str(temp_dirs["images"]))
    monkeypatch.setenv("PERSIST_DIR", str(temp_dirs["storage"]))
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("LLAMAPARSE_API_KEY", "test-llamaparse-key")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    return temp_dirs


@pytest.fixture
def sample_pdf_path(temp_dirs):
    """Create a dummy PDF file for testing."""
    pdf_path = temp_dirs["data"] / "test_document.pdf"
    pdf_path.write_text("dummy PDF content")
    return pdf_path


@pytest.fixture
def sample_image_path(temp_dirs):
    """Create a dummy image file for testing."""
    img_path = temp_dirs["images"] / "page_1.jpg"
    img_path.write_text("dummy image content")
    return img_path


@pytest.fixture
def mock_text_node():
    """Create a mock text node with metadata."""
    node = MagicMock()
    node.metadata = {
        "page_number": 1,
        "file_name": "test_document.pdf",
        "image_path": "/path/to/image.jpg",
    }
    node.get_content = Mock(return_value="Sample text content")
    node.node = node  # For nested access in some contexts
    return node


@pytest.fixture
def mock_retriever(mock_text_node):
    """Create a mock retriever that returns sample nodes."""
    retriever = MagicMock()
    retriever.retrieve = Mock(return_value=[mock_text_node])
    return retriever


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    response = MagicMock()
    response.message.content = "This is a test response from the LLM."
    llm.chat = Mock(return_value=response)
    return llm


@pytest.fixture
def mock_embedding_model():
    """Create a mock embedding model."""
    embed_model = MagicMock()
    embed_model.get_text_embedding = Mock(return_value=[0.1] * 1536)
    return embed_model

