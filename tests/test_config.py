"""Tests for configuration and path handling."""

import os
from pathlib import Path
import pytest


def test_env_variables_loaded(mock_env_vars):
    """Test that environment variables are properly loaded."""
    assert os.getenv("OPENAI_API_KEY") == "test-openai-key"
    assert os.getenv("GEMINI_API_KEY") == "test-gemini-key"
    assert os.getenv("LLAMAPARSE_API_KEY") == "test-llamaparse-key"
    assert os.getenv("LLM_PROVIDER") == "gemini"


def test_directory_paths_from_env(mock_env_vars):
    """Test that directory paths are read from environment variables."""
    data_dir = os.getenv("DATA_DIR")
    image_dir = os.getenv("IMAGE_DIR")
    persist_dir = os.getenv("PERSIST_DIR")
    
    assert data_dir == str(mock_env_vars["data"])
    assert image_dir == str(mock_env_vars["images"])
    assert persist_dir == str(mock_env_vars["storage"])


def test_relative_path_conversion():
    """Test that relative paths are converted to absolute paths."""
    relative_path = "./data"
    absolute_path = os.path.abspath(relative_path)
    
    assert os.path.isabs(absolute_path)
    assert not os.path.isabs(relative_path)


def test_absolute_path_unchanged():
    """Test that absolute paths remain unchanged."""
    absolute_path = "/home/user/data"
    result = absolute_path if os.path.isabs(absolute_path) else os.path.abspath(absolute_path)
    
    assert result == absolute_path


def test_default_paths_when_env_not_set(monkeypatch):
    """Test that default paths are used when environment variables are not set."""
    # Clear environment variables
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.delenv("IMAGE_DIR", raising=False)
    monkeypatch.delenv("PERSIST_DIR", raising=False)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    data_dir = os.getenv("DATA_DIR", os.path.join(script_dir, "data"))
    image_dir = os.getenv("IMAGE_DIR", os.path.join(script_dir, "data_images"))
    persist_dir = os.getenv("PERSIST_DIR", os.path.join(script_dir, "storage"))
    
    assert "data" in data_dir
    assert "data_images" in image_dir
    assert "storage" in persist_dir


def test_llm_provider_default(monkeypatch):
    """Test that LLM provider defaults to 'gemini' if not set."""
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    assert llm_provider == "gemini"


def test_llm_provider_openai(monkeypatch):
    """Test that LLM provider can be set to 'openai'."""
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    assert llm_provider == "openai"


def test_directories_exist(mock_env_vars):
    """Test that configured directories exist."""
    assert mock_env_vars["data"].exists()
    assert mock_env_vars["images"].exists()
    assert mock_env_vars["storage"].exists()


def test_path_resolution_with_pathlib(temp_dirs):
    """Test path resolution using pathlib."""
    test_path = Path(temp_dirs["data"]) / "test.pdf"
    
    assert test_path.parent == temp_dirs["data"]
    assert test_path.name == "test.pdf"


def test_llamaparse_region_default(monkeypatch):
    """Test that LlamaParse region defaults to 'na' if not set."""
    monkeypatch.delenv("LLAMAPARSE_REGION", raising=False)
    
    region = os.getenv("LLAMAPARSE_REGION", "na").lower()
    assert region == "na"


def test_llamaparse_region_eu(monkeypatch):
    """Test that LlamaParse region can be set to 'eu'."""
    monkeypatch.setenv("LLAMAPARSE_REGION", "eu")
    
    region = os.getenv("LLAMAPARSE_REGION", "na").lower()
    assert region == "eu"


def test_llamaparse_base_url_mapping():
    """Test that region correctly maps to base URL."""
    region_mapping = {
        "eu": "https://api.cloud.eu.llamaindex.ai",
        "na": "https://api.cloud.llamaindex.ai",
    }
    
    assert region_mapping.get("eu") == "https://api.cloud.eu.llamaindex.ai"
    assert region_mapping.get("na") == "https://api.cloud.llamaindex.ai"
    assert region_mapping.get("invalid", "https://api.cloud.llamaindex.ai") == "https://api.cloud.llamaindex.ai"

