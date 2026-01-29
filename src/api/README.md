# RAG-MAG API

FastAPI backend for the RAG-MAG multimodal document Q&A system.

## Overview

This API provides REST endpoints for:
- **Document Management**: Upload, list, retrieve, update, and delete PDF documents
- **Query**: Query documents with multimodal (text + image) responses
- **Image Serving**: Retrieve page images from indexed documents

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Development mode (with auto-reload)
make api

# Or manually:
cd src && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Document Management

#### Upload Document
```http
POST /documents
Content-Type: multipart/form-data

file: <PDF file>
```

**Response:**
```json
{
  "document_id": "uuid-here",
  "filename": "manual.pdf",
  "page_count": 0,
  "status": "processing",
  "timestamp": "2026-01-29T10:30:00"
}
```

#### List All Documents
```http
GET /documents
```

**Response:**
```json
{
  "total_documents": 5,
  "documents": [
    {
      "document_id": "uuid-1",
      "filename": "manual1.pdf",
      "page_count": 42
    }
  ]
}
```

#### Get Document Details
```http
GET /documents/{doc_id}
```

**Response:**
```json
{
  "document_id": "uuid-1",
  "filename": "manual.pdf",
  "page_count": 42,
  "node_ids": ["node1", "node2", ...],
  "pages": [
    {
      "page_number": 1,
      "image_path": "/path/to/image.jpg",
      "text_preview": "Page text preview..."
    }
  ]
}
```

#### Delete Document
```http
DELETE /documents/{doc_id}
```

**Response:**
```json
{
  "document_id": "uuid-1",
  "status": "deleted",
  "images_deleted": 42,
  "timestamp": "2026-01-29T10:30:00"
}
```

#### Update Document
```http
PUT /documents/{doc_id}
Content-Type: multipart/form-data

file: <New PDF file>
```

**Response:**
```json
{
  "document_id": "uuid-1",
  "filename": "updated_manual.pdf",
  "page_count": 50,
  "status": "processing",
  "old_images_deleted": 42,
  "timestamp": "2026-01-29T10:30:00"
}
```

### Query

#### Query Documents
```http
POST /query
Content-Type: application/json

{
  "query": "How to install the device?",
  "similarity_top_k": 3,
  "include_images": true
}
```

**Response:**
```json
{
  "query": "How to install the device?",
  "answer": "To install the device, follow these steps...",
  "source_nodes": [
    {
      "page_number": 5,
      "filename": "manual.pdf",
      "image_path": "/path/to/page_5.jpg",
      "text_preview": "Installation instructions...",
      "score": 0.85
    }
  ],
  "processing_time": 2.34
}
```

### Images

#### Get Page Image
```http
GET /images/{doc_id}/{page_number}
```

**Response:** JPEG image file

#### Get Image by Filename
```http
GET /images/path/{image_filename}
```

**Response:** JPEG image file

## Usage Examples

### Python (requests)

```python
import requests

API_URL = "http://localhost:8000"

# Upload a document
with open("manual.pdf", "rb") as f:
    response = requests.post(
        f"{API_URL}/documents",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]

# Query documents
response = requests.post(
    f"{API_URL}/query",
    json={
        "query": "How do I reset the device?",
        "similarity_top_k": 3,
        "include_images": True
    }
)
print(response.json()["answer"])

# List all documents
response = requests.get(f"{API_URL}/documents")
print(response.json())

# Delete a document
response = requests.delete(f"{API_URL}/documents/{doc_id}")
print(response.json())
```

### cURL

```bash
# Upload document
curl -X POST "http://localhost:8000/documents" \
  -F "file=@manual.pdf"

# Query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How to install?", "similarity_top_k": 3}'

# List documents
curl "http://localhost:8000/documents"

# Get document details
curl "http://localhost:8000/documents/uuid-here"

# Delete document
curl -X DELETE "http://localhost:8000/documents/uuid-here"
```

## Architecture

### Components

```
src/api/
├── __init__.py          # Module exports
├── main.py              # FastAPI app and configuration
├── models.py            # Pydantic request/response models
├── dependencies.py      # Shared dependencies and utilities
└── routes/
    ├── __init__.py
    ├── documents.py     # Document CRUD endpoints
    ├── query.py         # Query endpoint
    └── images.py        # Image serving endpoints
```

### Request Flow

```
Client Request
    ↓
FastAPI Router
    ↓
Validation (Pydantic)
    ↓
Business Logic (ingestion module)
    ↓
Vector Index / LLM
    ↓
Response (Pydantic)
    ↓
Client
```

### Background Processing

Document uploads and updates are processed in the background:

1. File is uploaded and saved to temp location
2. Immediate 202 response returned with document ID
3. Background task processes PDF (parsing, indexing)
4. Client can check document status via GET /documents/{doc_id}

## Configuration

The API uses the same configuration as the rest of the system (from `.env`):

```bash
# API Keys
OPENAI_API_KEY=your_key
GEMINI_API_KEY=your_key
LLAMAPARSE_API_KEY=your_key

# LLM Provider
LLM_PROVIDER=gemini

# Paths
DATA_DIR=./data
IMAGE_DIR=./data_images
PERSIST_DIR=./storage

# RAG Settings
SIMILARITY_TOP_K=3
CHUNK_SIZE=1024
CHUNK_OVERLAP=20
```

## Error Handling

All errors return consistent JSON responses:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2026-01-29T10:30:00"
}
```

### HTTP Status Codes

- `200`: Success
- `202`: Accepted (processing in background)
- `400`: Bad request (validation error)
- `404`: Resource not found
- `413`: Payload too large
- `500`: Internal server error
- `503`: Service unavailable

## Production Deployment

### Using uvicorn (multi-worker)

```bash
make api-prod

# Or manually:
cd src && uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker (Future)

```bash
docker build -t rag-mag-api .
docker run -p 8000:8000 --env-file .env rag-mag-api
```

## Security Considerations

### Current State (Development)
- ⚠️ CORS enabled for all origins
- ⚠️ No authentication/authorization
- ⚠️ No rate limiting
- ⚠️ File size limited to 100MB

### Production Recommendations
- ✅ Configure CORS for specific origins
- ✅ Add API key authentication
- ✅ Implement rate limiting (e.g., using slowapi)
- ✅ Add user authentication/authorization
- ✅ Set up HTTPS with SSL certificates
- ✅ Add request validation and sanitization
- ✅ Implement file upload virus scanning
- ✅ Add logging and monitoring

## Limitations

1. **Single Process**: Index is not shared across multiple processes
   - Solution: Use external vector DB (Chroma, Qdrant)

2. **File Storage**: Local filesystem only
   - Solution: Migrate to S3/cloud storage

3. **No Async Processing Queue**: Background tasks run in-process
   - Solution: Use Celery/RQ with Redis

4. **No Caching**: Every query hits the index
   - Solution: Add Redis for query caching

5. **No Persistence Layer**: Metadata not in database
   - Solution: Add PostgreSQL for document metadata

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_api.py -v
```

### Adding New Endpoints

1. Create route in `src/api/routes/`
2. Define request/response models in `models.py`
3. Add shared logic to `dependencies.py` if needed
4. Include router in `main.py`
5. Update this README

### API Documentation

The API auto-generates documentation from:
- Docstrings
- Pydantic model descriptions
- Type hints
- OpenAPI metadata

Access at `/docs` or `/redoc`.

## Troubleshooting

### "No index found" error
```bash
# Create initial index
make parse
```

### Port already in use
```bash
# Use different port
uvicorn api.main:app --port 8001
```

### Background tasks not running
- Check logs for errors
- Ensure sufficient memory for parsing
- Verify temp file permissions

## Next Steps

- [ ] Add API key authentication
- [ ] Implement rate limiting
- [ ] Add request caching
- [ ] External vector database integration
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring and logging (Prometheus, Grafana)
- [ ] API versioning (/v1/, /v2/)

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

