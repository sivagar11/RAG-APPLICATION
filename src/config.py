"""Configuration management for RAG-MAG system."""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

# === Script Directory ===
SCRIPT_DIR = Path(__file__).parent

# === API Keys ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLAMAPARSE_API_KEY = os.getenv("LLAMAPARSE_API_KEY")

# === LlamaParse Configuration ===
LLAMAPARSE_REGION = os.getenv("LLAMAPARSE_REGION", "na").lower()
LLAMAPARSE_MODEL = os.getenv("LLAMAPARSE_MODEL", "openai-gpt-4-1-mini")
LLAMAPARSE_PARSE_MODE = os.getenv("LLAMAPARSE_PARSE_MODE", "parse_page_with_agent")
LLAMAPARSE_HIGH_RES_OCR = os.getenv("LLAMAPARSE_HIGH_RES_OCR", "true").lower() == "true"
LLAMAPARSE_TABLE_EXTRACTION = os.getenv("LLAMAPARSE_TABLE_EXTRACTION", "true").lower() == "true"
LLAMAPARSE_OUTPUT_TABLES_HTML = os.getenv("LLAMAPARSE_OUTPUT_TABLES_HTML", "true").lower() == "true"

# LlamaParse base URL mapping
LLAMAPARSE_BASE_URL = {
    "eu": "https://api.cloud.eu.llamaindex.ai",
    "na": "https://api.cloud.llamaindex.ai",
}.get(LLAMAPARSE_REGION, "https://api.cloud.llamaindex.ai")

# === LLM Provider Selection ===
LLM_PROVIDER: Literal["openai", "gemini"] = os.getenv("LLM_PROVIDER", "gemini").lower()  # type: ignore

# === OpenAI Configuration ===
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

# === Gemini Configuration ===
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-3-small")

# === Directory Paths ===
DATA_DIR = os.getenv("DATA_DIR", str(SCRIPT_DIR / "data"))
IMAGE_DIR = os.getenv("IMAGE_DIR", str(SCRIPT_DIR / "data_images"))
PERSIST_DIR = os.getenv("PERSIST_DIR", str(SCRIPT_DIR / "storage"))

# Convert to absolute paths if relative
DATA_DIR = os.path.abspath(DATA_DIR) if not os.path.isabs(DATA_DIR) else DATA_DIR
IMAGE_DIR = os.path.abspath(IMAGE_DIR) if not os.path.isabs(IMAGE_DIR) else IMAGE_DIR
PERSIST_DIR = os.path.abspath(PERSIST_DIR) if not os.path.isabs(PERSIST_DIR) else PERSIST_DIR

# === RAG Configuration ===
SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "3"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "20"))

# === Vector Database Configuration ===
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "qdrant").lower()  # local, qdrant, chroma
QDRANT_URL = os.getenv("QDRANT_URL", "https://44f45e11-cf16-4ec7-8bb2-b4fb00dbdfe4.us-east4-0.gcp.cloud.qdrant.io:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.rm9IXxgo6vIetuUT7D8o-0lG69R_cCPpyya6S2jzpg8")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_documents")

# === Image Storage Configuration ===
IMAGE_STORAGE_TYPE = os.getenv("IMAGE_STORAGE_TYPE", "local").lower()  # local, s3, r2
IMAGE_STORAGE_FORMAT = os.getenv("IMAGE_STORAGE_FORMAT", "base64").lower()  # url, base64, hybrid

# S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "rag-mag-images")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")  # For S3-compatible services (R2, MinIO)


def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not LLAMAPARSE_API_KEY:
        errors.append("LLAMAPARSE_API_KEY is required")
    
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    elif LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        # Note: Gemini uses OpenAI embeddings, so OPENAI_API_KEY is also needed
        if not OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required for embeddings when LLM_PROVIDER=gemini")
    else:
        errors.append(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'openai' or 'gemini'")
    
    if errors:
        raise ValueError(f"Configuration errors:\n  - " + "\n  - ".join(errors))


def get_llm_config():
    """Get LLM and embedding model configuration based on provider."""
    if LLM_PROVIDER == "openai":
        return {
            "llm_model": OPENAI_LLM_MODEL,
            "embedding_model": OPENAI_EMBEDDING_MODEL,
            "llm_api_key": OPENAI_API_KEY,
            "embedding_api_key": OPENAI_API_KEY,
        }
    elif LLM_PROVIDER == "gemini":
        return {
            "llm_model": GEMINI_LLM_MODEL,
            "embedding_model": GEMINI_EMBEDDING_MODEL,
            "llm_api_key": GEMINI_API_KEY,
            "embedding_api_key": OPENAI_API_KEY,  # Using OpenAI for embeddings
        }
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")


def print_config_summary():
    """Print a summary of the current configuration."""
    print(f"🔧 Configuration Summary")
    print(f"   LlamaParse: {LLAMAPARSE_MODEL}")
    print(f"   Region: {LLAMAPARSE_REGION.upper()} ({LLAMAPARSE_BASE_URL})")
    print(f"   Parse Mode: {LLAMAPARSE_PARSE_MODE}")
    print(f"   High-Res OCR: {LLAMAPARSE_HIGH_RES_OCR}")
    print(f"   Table Extraction: {LLAMAPARSE_TABLE_EXTRACTION}")
    print(f"   LLM Provider: {LLM_PROVIDER.upper()}")
    
    if LLM_PROVIDER == "openai":
        print(f"   LLM: {OPENAI_LLM_MODEL}")
        print(f"   Embeddings: {OPENAI_EMBEDDING_MODEL}")
    elif LLM_PROVIDER == "gemini":
        print(f"   LLM: {GEMINI_LLM_MODEL}")
        print(f"   Embeddings: {GEMINI_EMBEDDING_MODEL} (OpenAI)")
    
    print(f"   RAG: top_k={SIMILARITY_TOP_K}, chunk={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")

