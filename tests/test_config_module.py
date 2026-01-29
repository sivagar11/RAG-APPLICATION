"""Tests for the centralized config module."""

import os
from pathlib import Path
import pytest


def test_config_imports():
    """Test that config module can be imported and has all required attributes."""
    from src import config
    
    # Check API keys exist as attributes (even if None)
    assert hasattr(config, 'OPENAI_API_KEY')
    assert hasattr(config, 'GEMINI_API_KEY')
    assert hasattr(config, 'LLAMAPARSE_API_KEY')
    
    # Check LlamaParse config
    assert hasattr(config, 'LLAMAPARSE_MODEL')
    assert hasattr(config, 'LLAMAPARSE_REGION')
    assert hasattr(config, 'LLAMAPARSE_BASE_URL')
    assert hasattr(config, 'LLAMAPARSE_PARSE_MODE')
    assert hasattr(config, 'LLAMAPARSE_HIGH_RES_OCR')
    assert hasattr(config, 'LLAMAPARSE_TABLE_EXTRACTION')
    assert hasattr(config, 'LLAMAPARSE_OUTPUT_TABLES_HTML')
    
    # Check LLM config
    assert hasattr(config, 'LLM_PROVIDER')
    assert hasattr(config, 'OPENAI_LLM_MODEL')
    assert hasattr(config, 'OPENAI_EMBEDDING_MODEL')
    assert hasattr(config, 'GEMINI_LLM_MODEL')
    assert hasattr(config, 'GEMINI_EMBEDDING_MODEL')
    
    # Check directory paths
    assert hasattr(config, 'DATA_DIR')
    assert hasattr(config, 'IMAGE_DIR')
    assert hasattr(config, 'PERSIST_DIR')
    
    # Check RAG config
    assert hasattr(config, 'SIMILARITY_TOP_K')
    assert hasattr(config, 'CHUNK_SIZE')
    assert hasattr(config, 'CHUNK_OVERLAP')
    
    # Check functions
    assert hasattr(config, 'validate_config')
    assert hasattr(config, 'get_llm_config')
    assert hasattr(config, 'print_config_summary')


def test_llamaparse_region_url_mapping():
    """Test that LlamaParse region correctly maps to base URL."""
    from src import config
    
    # Check that region is either na or eu
    assert config.LLAMAPARSE_REGION in ["na", "eu"]
    
    # Check that base URL matches region
    if config.LLAMAPARSE_REGION == "eu":
        assert config.LLAMAPARSE_BASE_URL == "https://api.cloud.eu.llamaindex.ai"
    else:
        assert config.LLAMAPARSE_BASE_URL == "https://api.cloud.llamaindex.ai"


def test_llm_provider_valid():
    """Test that LLM provider is one of the supported values."""
    from src import config
    
    assert config.LLM_PROVIDER in ["openai", "gemini"]


def test_get_llm_config_returns_dict():
    """Test that get_llm_config returns a properly structured dictionary."""
    from src.config import get_llm_config
    
    llm_config = get_llm_config()
    
    # Check structure
    assert isinstance(llm_config, dict)
    assert "llm_model" in llm_config
    assert "embedding_model" in llm_config
    assert "llm_api_key" in llm_config
    assert "embedding_api_key" in llm_config
    
    # Check that values are strings (or None if not set)
    assert isinstance(llm_config["llm_model"], str)
    assert isinstance(llm_config["embedding_model"], str)


def test_get_llm_config_keys_not_empty():
    """Test that get_llm_config returns valid model names."""
    from src.config import get_llm_config, LLM_PROVIDER
    
    llm_config = get_llm_config()
    
    # Model names should not be empty
    assert len(llm_config["llm_model"]) > 0
    assert len(llm_config["embedding_model"]) > 0
    
    # Should have expected model patterns
    if LLM_PROVIDER == "openai":
        assert "gpt" in llm_config["llm_model"].lower()
        assert "embedding" in llm_config["embedding_model"].lower()
    elif LLM_PROVIDER == "gemini":
        assert "gemini" in llm_config["llm_model"].lower()
        assert "embedding" in llm_config["embedding_model"].lower()


def test_boolean_config_types():
    """Test that boolean configurations are actual booleans."""
    from src import config
    
    assert isinstance(config.LLAMAPARSE_HIGH_RES_OCR, bool)
    assert isinstance(config.LLAMAPARSE_TABLE_EXTRACTION, bool)
    assert isinstance(config.LLAMAPARSE_OUTPUT_TABLES_HTML, bool)


def test_integer_config_types():
    """Test that integer configurations are actual integers."""
    from src import config
    
    assert isinstance(config.SIMILARITY_TOP_K, int)
    assert isinstance(config.CHUNK_SIZE, int)
    assert isinstance(config.CHUNK_OVERLAP, int)
    
    # Check reasonable ranges
    assert config.SIMILARITY_TOP_K > 0
    assert config.CHUNK_SIZE > 0
    assert config.CHUNK_OVERLAP >= 0


def test_directory_paths_are_strings():
    """Test that directory paths are strings."""
    from src import config
    
    assert isinstance(config.DATA_DIR, str)
    assert isinstance(config.IMAGE_DIR, str)
    assert isinstance(config.PERSIST_DIR, str)
    
    # Check that paths are not empty
    assert len(config.DATA_DIR) > 0
    assert len(config.IMAGE_DIR) > 0
    assert len(config.PERSIST_DIR) > 0


def test_print_config_summary_no_error(capsys):
    """Test that print_config_summary runs without errors."""
    from src.config import print_config_summary
    
    # Should not raise any exceptions
    print_config_summary()
    
    captured = capsys.readouterr()
    # Check that something was printed
    assert len(captured.out) > 0
    assert "Configuration Summary" in captured.out


def test_llamaparse_config_values():
    """Test that LlamaParse configuration values are valid."""
    from src import config
    
    # Check model is a non-empty string
    assert isinstance(config.LLAMAPARSE_MODEL, str)
    assert len(config.LLAMAPARSE_MODEL) > 0
    
    # Check parse mode is a non-empty string
    assert isinstance(config.LLAMAPARSE_PARSE_MODE, str)
    assert len(config.LLAMAPARSE_PARSE_MODE) > 0
    
    # Check region is valid
    assert config.LLAMAPARSE_REGION in ["na", "eu"]


def test_llm_model_names_are_strings():
    """Test that LLM model names are valid strings."""
    from src import config
    
    assert isinstance(config.OPENAI_LLM_MODEL, str)
    assert len(config.OPENAI_LLM_MODEL) > 0
    
    assert isinstance(config.OPENAI_EMBEDDING_MODEL, str)
    assert len(config.OPENAI_EMBEDDING_MODEL) > 0
    
    assert isinstance(config.GEMINI_LLM_MODEL, str)
    assert len(config.GEMINI_LLM_MODEL) > 0
    
    assert isinstance(config.GEMINI_EMBEDDING_MODEL, str)
    assert len(config.GEMINI_EMBEDDING_MODEL) > 0
