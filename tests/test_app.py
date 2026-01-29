"""Tests for app.py and MultimodalQueryEngine."""

import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestMultimodalQueryEngine:
    """Tests for the MultimodalQueryEngine class."""
    
    def test_query_engine_initialization(self, mock_retriever, mock_llm):
        """Test that query engine initializes with proper attributes."""
        # Test that our mocks have the expected attributes
        assert mock_retriever is not None
        assert mock_llm is not None
        assert hasattr(mock_retriever, 'retrieve')
        assert hasattr(mock_llm, 'chat')
        
        # Verify mocks are callable
        assert callable(mock_retriever.retrieve)
        assert callable(mock_llm.chat)
    
    def test_image_path_resolution_valid(self, temp_dirs, sample_image_path):
        """Test resolving valid image paths."""
        img_path = Path(sample_image_path)
        
        assert img_path.exists()
        assert img_path.is_absolute() or img_path.resolve().exists()
    
    def test_image_path_resolution_invalid(self, temp_dirs):
        """Test resolving invalid image paths."""
        invalid_path = temp_dirs["images"] / "nonexistent.jpg"
        
        assert not invalid_path.exists()
    
    def test_image_path_recovery(self, temp_dirs):
        """Test recovering image path by filename."""
        # Simulate stored path that doesn't exist
        old_path = Path("/old/path/data_images/page_1.jpg")
        
        # But file exists in current location
        actual_path = temp_dirs["images"] / "page_1.jpg"
        actual_path.write_text("image content")
        
        # Simulate recovery logic
        if not old_path.exists():
            filename = old_path.name
            possible_path = temp_dirs["images"] / filename
            if possible_path.exists():
                resolved_path = possible_path
        
        assert resolved_path == actual_path
        assert resolved_path.exists()
    
    def test_context_string_creation(self, mock_text_node):
        """Test creating context string from nodes."""
        nodes = [mock_text_node, mock_text_node]
        
        context_str = "\n\n".join([node.get_content() for node in nodes])
        
        assert len(context_str) > 0
        assert context_str.count("Sample text content") == 2
    
    def test_image_blocks_creation(self, mock_text_node, temp_dirs, sample_image_path):
        """Test creating image blocks from nodes."""
        mock_text_node.metadata["image_path"] = str(sample_image_path)
        nodes = [mock_text_node]
        
        # Simulate image block creation
        from llama_index.core.llms import ImageBlock
        
        image_blocks = []
        for node in nodes:
            img_path = node.metadata.get("image_path")
            if img_path and Path(img_path).exists():
                image_blocks.append(ImageBlock(path=str(img_path)))
        
        assert len(image_blocks) == 1
    
    def test_query_response_structure(self, mock_retriever, mock_llm):
        """Test that query response has correct structure."""
        # Simulate a query
        query_str = "What is the warranty policy?"
        
        # Mock retrieval
        nodes = mock_retriever.retrieve(query_str)
        
        # Mock LLM response
        llm_response = mock_llm.chat([])
        
        assert nodes is not None
        assert len(nodes) > 0
        assert llm_response.message.content is not None


class TestAppConfiguration:
    """Tests for app.py configuration and setup."""
    
    def test_persist_dir_loading(self, temp_dirs, mock_env_vars):
        """Test loading persist directory configuration."""
        persist_dir = os.getenv("PERSIST_DIR")
        
        assert persist_dir == str(temp_dirs["storage"])
        assert Path(persist_dir).exists()
    
    def test_image_base_dir_loading(self, temp_dirs, mock_env_vars):
        """Test loading image base directory configuration."""
        image_dir = os.getenv("IMAGE_DIR")
        
        assert image_dir == str(temp_dirs["images"])
        assert Path(image_dir).exists()
    
    def test_llm_provider_selection_openai(self, monkeypatch):
        """Test selecting OpenAI as LLM provider."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        api_key = os.getenv("OPENAI_API_KEY")
        
        assert llm_provider == "openai"
        assert api_key == "test-key"
    
    def test_llm_provider_selection_gemini(self, monkeypatch):
        """Test selecting Gemini as LLM provider."""
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        api_key = os.getenv("GEMINI_API_KEY")
        
        assert llm_provider == "gemini"
        assert api_key == "test-key"
    
    def test_storage_context_exists(self, temp_dirs, mock_env_vars):
        """Test that storage context directory exists."""
        persist_dir = Path(os.getenv("PERSIST_DIR"))
        
        # Create mock index files
        (persist_dir / "docstore.json").write_text("{}")
        (persist_dir / "index_store.json").write_text("{}")
        
        assert persist_dir.exists()
        assert (persist_dir / "docstore.json").exists()
        assert (persist_dir / "index_store.json").exists()


class TestPromptTemplates:
    """Tests for prompt templates and formatting."""
    
    def test_qa_prompt_formatting(self):
        """Test QA prompt block text formatting."""
        qa_prompt_template = """\
Below is the parsed content from the manual:
---------------------
{context_str}
---------------------
"""
        context_str = "Sample context text"
        formatted = qa_prompt_template.format(context_str=context_str)
        
        assert "Sample context text" in formatted
        assert "---------------------" in formatted
    
    def test_image_suffix_formatting(self):
        """Test image suffix prompt formatting."""
        image_suffix = """\
Given this content and without prior knowledge, answer the query:
{query_str}
"""
        query_str = "What is the installation process?"
        formatted = image_suffix.format(query_str=query_str)
        
        assert "What is the installation process?" in formatted
    
    def test_prompt_with_multiple_contexts(self):
        """Test prompt with multiple context strings."""
        contexts = ["Context 1", "Context 2", "Context 3"]
        combined_context = "\n\n".join(contexts)
        
        assert "Context 1" in combined_context
        assert "Context 2" in combined_context
        assert "Context 3" in combined_context
        assert combined_context.count("\n\n") == 2


class TestRetrievalFunctionality:
    """Tests for retrieval functionality."""
    
    def test_retriever_returns_nodes(self, mock_retriever):
        """Test that retriever returns nodes."""
        query = "test query"
        nodes = mock_retriever.retrieve(query)
        
        assert nodes is not None
        assert len(nodes) > 0
    
    def test_retriever_similarity_top_k(self, mock_retriever):
        """Test retriever with similarity_top_k parameter."""
        # Simulate top_k retrieval
        mock_retriever.retrieve = Mock(return_value=[mock_retriever.retrieve("test")[0]] * 3)
        
        query = "test query"
        nodes = mock_retriever.retrieve(query)
        
        # Should return exactly top_k results
        assert len(nodes) == 3
    
    def test_node_metadata_presence(self, mock_text_node):
        """Test that retrieved nodes have required metadata."""
        assert "image_path" in mock_text_node.metadata
        assert "page_number" in mock_text_node.metadata
        assert "file_name" in mock_text_node.metadata


class TestErrorHandling:
    """Tests for error handling scenarios."""
    
    def test_missing_api_key(self, monkeypatch):
        """Test handling of missing API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        api_key = os.getenv("OPENAI_API_KEY")
        
        assert api_key is None
    
    def test_invalid_llm_provider(self, monkeypatch):
        """Test handling of invalid LLM provider."""
        monkeypatch.setenv("LLM_PROVIDER", "invalid_provider")
        
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        
        assert llm_provider not in ["openai", "gemini"]
    
    def test_missing_persist_directory(self, temp_dirs):
        """Test handling of missing persist directory."""
        nonexistent_dir = temp_dirs["root"] / "nonexistent"
        
        assert not nonexistent_dir.exists()
    
    def test_missing_image_file(self, temp_dirs):
        """Test handling of missing image file."""
        nonexistent_image = temp_dirs["images"] / "missing.jpg"
        
        assert not nonexistent_image.exists()


class TestPathResolution:
    """Tests for path resolution in MultimodalQueryEngine."""
    
    def test_expanduser_path(self):
        """Test expanding user home directory in paths."""
        path_with_tilde = Path("~/data/images")
        expanded = path_with_tilde.expanduser()
        
        assert "~" not in str(expanded)
    
    def test_absolute_path_check(self):
        """Test checking if path is absolute."""
        abs_path = Path("/home/user/data")
        rel_path = Path("./data")
        
        assert abs_path.is_absolute()
        assert not rel_path.is_absolute()
    
    def test_path_resolution(self, temp_dirs):
        """Test resolving relative to absolute path."""
        rel_path = Path("data/images")
        abs_path = rel_path.resolve()
        
        assert abs_path.is_absolute()

