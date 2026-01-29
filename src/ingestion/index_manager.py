"""Index lifecycle management.

This module manages the VectorStoreIndex lifecycle - loading, reloading,
and providing thread-safe access to the index.
"""

import os
import asyncio
from typing import Optional
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings

# Import configuration
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import PERSIST_DIR, LLM_PROVIDER, VECTOR_DB_TYPE, get_llm_config
from .vector_store import get_vector_store, get_storage_context


# Global index instance (singleton pattern)
_index: Optional[VectorStoreIndex] = None
_index_lock = asyncio.Lock()


def _setup_llm_settings():
    """Configure LLM and embedding models based on provider."""
    llm_config = get_llm_config()
    
    if LLM_PROVIDER == "openai":
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
        
        Settings.embed_model = OpenAIEmbedding(
            model=llm_config["embedding_model"],
            api_key=llm_config["embedding_api_key"]
        )
        Settings.llm = OpenAI(
            model=llm_config["llm_model"],
            api_key=llm_config["llm_api_key"]
        )
    elif LLM_PROVIDER == "gemini":
        from llama_index.llms.google_genai import GoogleGenAI
        from llama_index.embeddings.openai import OpenAIEmbedding
        
        Settings.embed_model = OpenAIEmbedding(
            model=llm_config["embedding_model"],
            api_key=llm_config["embedding_api_key"]
        )
        Settings.llm = GoogleGenAI(
            model=llm_config["llm_model"],
            api_key=llm_config["llm_api_key"]
        )


def get_index(force_reload: bool = False) -> VectorStoreIndex:
    """Get or load the vector store index.
    
    This function implements a singleton pattern for the index. The index
    is loaded once and reused across multiple calls for efficiency.
    
    Args:
        force_reload: If True, reload the index from storage even if cached
        
    Returns:
        VectorStoreIndex instance
        
    Raises:
        FileNotFoundError: If storage directory doesn't exist (local mode)
        ValueError: If index cannot be loaded
    """
    global _index
    
    if force_reload or _index is None:
        # Setup LLM settings
        _setup_llm_settings()
        
        if VECTOR_DB_TYPE == "local":
            # Local storage mode (original implementation)
            if not os.path.exists(PERSIST_DIR):
                raise FileNotFoundError(
                    f"Storage directory not found: {PERSIST_DIR}. "
                    "Run parse.py first to create the initial index."
                )
            
            storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
            _index = load_index_from_storage(storage_context)
        else:
            # External vector DB mode (Qdrant, etc.)
            vector_store = get_vector_store()
            storage_context = get_storage_context(vector_store)
            
            try:
                # Try to load existing index
                _index = VectorStoreIndex.from_vector_store(
                    vector_store,
                    storage_context=storage_context
                )
            except Exception as e:
                print(f"Creating new index in {VECTOR_DB_TYPE}: {e}")
                # Create new index if loading fails
                _index = VectorStoreIndex(
                    [],
                    storage_context=storage_context
                )
    
    return _index


def reload_index() -> VectorStoreIndex:
    """Force reload the index from storage.
    
    Use this when you know the index has been modified externally
    and you need to see the latest changes.
    
    Returns:
        Reloaded VectorStoreIndex instance
    """
    return get_index(force_reload=True)


async def get_index_lock():
    """Get the async lock for thread-safe index operations.
    
    Use this as a context manager to ensure only one operation
    modifies the index at a time:
    
    Example:
        async with (await get_index_lock()):
            index.insert_nodes(nodes)
            index.storage_context.persist()
    
    Returns:
        asyncio.Lock instance
    """
    return _index_lock


def create_new_index() -> VectorStoreIndex:
    """Create a new empty index.
    
    This is useful for testing or starting fresh.
    
    Returns:
        New empty VectorStoreIndex
    """
    global _index
    
    # Setup LLM settings
    _setup_llm_settings()
    
    if VECTOR_DB_TYPE == "local":
        # Create new empty index with local storage
        _index = VectorStoreIndex([])
    else:
        # Create new index with external vector DB (Qdrant, etc.)
        vector_store = get_vector_store()
        storage_context = get_storage_context(vector_store)
        _index = VectorStoreIndex(
            [],
            storage_context=storage_context
        )
    
    return _index


def persist_index():
    """Persist the current index to storage.
    
    This must be called after any modifications (insert, delete, update)
    to save changes. For external vector DBs, this is handled automatically.
    For local storage, this saves to disk.
    
    Raises:
        RuntimeError: If no index is loaded
    """
    global _index
    
    if _index is None:
        raise RuntimeError("No index loaded. Call get_index() first.")
    
    if VECTOR_DB_TYPE == "local":
        # Only persist to disk for local storage
        os.makedirs(PERSIST_DIR, exist_ok=True)
        _index.storage_context.persist(persist_dir=PERSIST_DIR)
    else:
        # External vector DBs auto-persist, but we can force a sync
        # Qdrant/Chroma handle persistence automatically
        pass

