"""Vector store configuration and management.

This module provides vector store initialization for different backends:
- Local: SimpleVectorStore (default)
- Qdrant: QdrantVectorStore
- Chroma: ChromaVectorStore (future)
"""

import os
from typing import Optional
from llama_index.core import StorageContext
from llama_index.core.vector_stores import SimpleVectorStore

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import (
    VECTOR_DB_TYPE,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    PERSIST_DIR,
)


def get_vector_store():
    """Get vector store based on configuration.
    
    Returns:
        VectorStore instance configured based on VECTOR_DB_TYPE
    """
    if VECTOR_DB_TYPE == "qdrant":
        return _get_qdrant_vector_store()
    elif VECTOR_DB_TYPE == "chroma":
        # Future implementation
        raise NotImplementedError("Chroma support coming soon")
    else:
        # Default to local SimpleVectorStore
        return None  # LlamaIndex uses SimpleVectorStore by default


def _get_qdrant_vector_store():
    """Initialize Qdrant vector store.
    
    Returns:
        QdrantVectorStore instance
    """
    try:
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        import qdrant_client
    except ImportError:
        raise ImportError(
            "Qdrant dependencies not installed. "
            "Run: pip install llama-index-vector-stores-qdrant qdrant-client"
        )
    
    # Initialize Qdrant client
    client = qdrant_client.QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=60,
    )
    
    # Create vector store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
    )
    
    return vector_store


def get_storage_context(vector_store=None) -> StorageContext:
    """Get storage context with configured vector store.
    
    Args:
        vector_store: Optional vector store instance. If None, uses default.
        
    Returns:
        StorageContext configured with the vector store
    """
    if VECTOR_DB_TYPE == "local":
        # Load from local persistence directory
        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=PERSIST_DIR
            )
        except FileNotFoundError:
            # Create new storage context if directory doesn't exist
            storage_context = StorageContext.from_defaults()
    else:
        # Use external vector store
        if vector_store is None:
            vector_store = get_vector_store()
        
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store
        )
    
    return storage_context


def check_vector_db_connection() -> bool:
    """Check if vector database is accessible.
    
    Returns:
        True if connection successful, False otherwise
    """
    if VECTOR_DB_TYPE == "local":
        return os.path.exists(PERSIST_DIR)
    
    elif VECTOR_DB_TYPE == "qdrant":
        try:
            import qdrant_client
            client = qdrant_client.QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=5,
            )
            # Try to get collections (this will fail if connection is bad)
            client.get_collections()
            return True
        except Exception as e:
            print(f"Qdrant connection failed: {e}")
            return False
    
    return False

