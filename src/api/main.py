"""FastAPI application for RAG-MAG system."""

import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import (
    validate_config,
    print_config_summary,
    PERSIST_DIR,
    LLM_PROVIDER
)
from ingestion import get_index, get_document_count
from .models import HealthResponse, ErrorResponse
from .routes import documents, query, images


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print("\n" + "="*60)
    print("🚀 Starting RAG-MAG API Server")
    print("="*60)
    
    try:
        # Validate configuration
        validate_config()
        print_config_summary()
        
        # Check if index exists
        if not os.path.exists(PERSIST_DIR):
            print("\n⚠️  WARNING: No index found!")
            print("   Please run 'make parse' to create the initial index.")
        else:
            # Load index to verify it works
            try:
                index = get_index()
                doc_count = get_document_count()
                print(f"\n✅ Loaded index with {doc_count} document(s)")
            except Exception as e:
                print(f"\n❌ Error loading index: {e}")
        
        print("\n" + "="*60)
        print("✨ API server ready!")
        print("   Docs: http://localhost:8000/docs")
        print("   Health: http://localhost:8000/health")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    print("\n👋 Shutting down RAG-MAG API server...")


# Create FastAPI app
app = FastAPI(
    title="RAG-MAG API",
    description="Multimodal RAG system for document Q&A with text and images",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=None
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )


# Include routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(images.router)


# Root endpoint
@app.get("/", summary="Root endpoint")
def root():
    """Root endpoint - redirects to docs."""
    return {
        "message": "RAG-MAG API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health", response_model=HealthResponse, summary="Health check")
def health_check():
    """Check API health and status."""
    try:
        # Try to get document count
        doc_count = 0
        if os.path.exists(PERSIST_DIR):
            try:
                doc_count = get_document_count()
            except Exception:
                pass
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            documents_indexed=doc_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


# Main entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

