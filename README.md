# RAG-MAG

Multimodal RAG system that processes PDF manuals and answers questions using both text and images.

## Quick Start

```bash
# 1. Setup
cp env.example .env  # Add your API keys
pip install -r requirements.txt

# 2. Parse documents (initial batch load)
make parse  # or: python src/parse.py

# 3. Choose your interface:

# Option A: Streamlit UI (interactive web app)
make run    # or: streamlit run src/app.py

# Option B: FastAPI REST API (for programmatic access)
make api    # or: cd src && uvicorn api.main:app --reload
```

## Table of Contents

- [Configuration](#configuration)
- [Document Ingestion Workflow](#document-ingestion-workflow)
- [Ingestion Architecture](#ingestion-architecture)
- [FastAPI Backend](#fastapi-backend)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Tech Stack](#tech-stack)
- [Next Steps](#next-steps)

---

## Configuration

All configuration is centralized in `.env` file:

```bash
cp env.example .env  # Then edit with your values
```

### Required Settings

```bash
# API Keys
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
LLAMAPARSE_API_KEY=your_key_here

# LLM Provider
LLM_PROVIDER=gemini  # or openai
```

### Optional Settings (with defaults)

**LlamaParse Configuration:**
- `LLAMAPARSE_MODEL=openai-gpt-4-1-mini` - Parser model
- `LLAMAPARSE_REGION=na` - Region (na or eu)
- `LLAMAPARSE_PARSE_MODE=parse_page_with_agent` - Parsing mode
- `LLAMAPARSE_HIGH_RES_OCR=true` - High-res OCR
- `LLAMAPARSE_TABLE_EXTRACTION=true` - Extract tables
- `LLAMAPARSE_OUTPUT_TABLES_HTML=true` - Tables as HTML

**OpenAI Models** (when `LLM_PROVIDER=openai`):
- `OPENAI_LLM_MODEL=gpt-4o-mini` - LLM model
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-large` - Embedding model

**Gemini Models** (when `LLM_PROVIDER=gemini`):
- `GEMINI_LLM_MODEL=gemini-2.5-flash` - LLM model
- `GEMINI_EMBEDDING_MODEL=text-embedding-3-small` - Embedding model (via OpenAI)

**Paths:**
- `DATA_DIR=./data` - PDFs to process
- `IMAGE_DIR=./data_images` - Extracted images
- `PERSIST_DIR=./storage` - Vector index

**RAG Settings:**
- `SIMILARITY_TOP_K=3` - Number of chunks to retrieve per query
- `CHUNK_SIZE=1024` - Text chunk size for indexing
- `CHUNK_OVERLAP=20` - Overlap between chunks

---

## Document Ingestion Workflow

### Phase 1: Initial Batch Load (One Time)

```bash
# Put all your PDFs in data/
cp /path/to/manuals/*.pdf data/

# Run initial batch parser (creates fresh index)
make parse
```

**What this does:**
- ✅ Processes ALL PDFs in `data/`
- ✅ Creates vector index in `storage/`
- ✅ Extracts images to `data_images/{doc_id}/`
- ✅ Assigns UUID to each document
- ✅ Sets proper SOURCE relationships for tracking
- ⚠️ **OVERWRITES** any existing index

**Output:**
```
📄 Found 25 PDF file(s)
📝 Parsing documents...
   [1/25] Parsing manual1.pdf...
       ✅ Extracted 42 pages
   ...
📊 Summary:
   Documents indexed: 25
   Total pages: 1,247
   Document IDs:
      a3f5e891-abc1-... → manual1.pdf
      b7c2d441-def2-... → manual2.pdf
```

### Phase 2: Deploy API (Future)

Once you build the FastAPI backend, it will:
- ✅ Load existing index from `storage/`
- ✅ Add/delete/update documents via API
- ✅ Persist changes immediately
- ✅ Preserve batch-loaded documents

### Phase 3: Add More PDFs (Optional)

If you need to batch-add more PDFs after API is live:

```bash
# Put new PDFs in data/
cp /path/to/more_manuals/*.pdf data/

# Add to existing index (SAFE - preserves API documents)
make add-batch
```

**What this does:**
- ✅ Loads EXISTING index
- ✅ Checks for duplicates (by filename)
- ✅ Only adds NEW files
- ✅ **PRESERVES** API-added documents

### Decision Matrix: Which Script to Use?

| Scenario | Command | Safe for API docs? |
|----------|---------|-------------------|
| First time setup | `make parse` | N/A (no API yet) |
| API is live, add more PDFs | `make add-batch` | ✅ YES |
| Start completely fresh | `make parse` | ❌ NO (destroys API docs) |
| Testing/development | `make parse` | N/A |

**⚠️ Warning:** Never run `make parse` after API goes live unless you want to rebuild from scratch!

---

## Ingestion Architecture

### Overview

The system includes a dedicated document management module (`src/ingestion/`) that provides CRUD operations with proper LlamaIndex document tracking.

### Key Features

✅ **Document Tracking**: Proper SOURCE relationships enable document-level operations  
✅ **CRUD Operations**: Add, delete, update, and list documents programmatically  
✅ **Image Management**: Document-specific directories prevent conflicts  
✅ **UUID System**: Each document gets a unique identifier for tracking  
✅ **API-Ready**: Functions ready to wrap in FastAPI endpoints  

### Core Components

#### 1. **parser.py** - LlamaParse Wrapper
- Wraps LlamaParse with SOURCE relationship configuration
- Creates document-specific image directories: `data_images/{doc_id}/`
- Attaches metadata: document_id, filename, page_number, image_path

#### 2. **index_manager.py** - Index Lifecycle
- Singleton pattern for efficient index access
- Configures LLM and embedding models
- Handles persistence and reloading
- Thread-safe write operations

#### 3. **document_manager.py** - CRUD Operations
- `add_document(pdf_path, doc_id=None)` - Add PDF to index
- `delete_document(doc_id)` - Remove document and images
- `update_document(doc_id, new_pdf_path)` - Replace document
- `list_documents()` - Get all indexed documents
- `get_document_info(doc_id)` - Detailed document information

### Usage Examples

**CLI (Batch Processing):**
```bash
make parse        # Initial load - builds fresh index
make add-batch    # Add more - preserves existing
```

**Python (Programmatic):**
```python
from ingestion import add_document, delete_document, list_documents

# Add a document
result = await add_document("manual.pdf")
doc_id = result['document_id']

# List all documents
docs = list_documents()
for doc_id, info in docs.items():
    print(f"{doc_id}: {info['metadata']['filename']}")

# Delete document (removes from index + images)
delete_document(doc_id)
```

**Testing:**
```bash
python scripts/test_ingestion.py  # Comprehensive test suite
```

### Technical Implementation

**SOURCE Relationships (Critical):**
```python
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

# Enable document tracking and deletion
node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc_id)
```

Without this, `delete_ref_doc()` won't work and documents can't be tracked.

**Image Organization:**
```
data_images/
├── {doc-uuid-1}/
│   ├── page_1.jpg
│   ├── page_2.jpg
│   └── ...
├── {doc-uuid-2}/
│   └── ...
```

This prevents filename conflicts and enables clean deletion.

### Limitations & Solutions

| Limitation | Impact | Solution |
|------------|--------|----------|
| Single process only | Index not shared across processes | Use external vector DB (Chroma/Qdrant) |
| Manual persistence | Changes must be explicitly saved | CRUD functions handle automatically |
| Local file storage | Not scalable for cloud | Migrate to S3/CDN for images |
| No transactions | Operations not atomic | Add try/except with rollback logic |

### API Integration (Ready)

The ingestion module is designed for FastAPI:

```python
from fastapi import FastAPI, UploadFile, BackgroundTasks
from ingestion import add_document, delete_document

app = FastAPI()

@app.post("/documents")
async def upload(file: UploadFile, bg: BackgroundTasks):
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    bg.add_task(add_document, temp_path)
    return {"status": "processing"}

@app.delete("/documents/{doc_id}")
def delete(doc_id: str):
    return delete_document(doc_id)
```

---

## FastAPI Backend

### Overview

The FastAPI backend provides REST API endpoints for programmatic access to the RAG system.

**Features:**
- ✅ Document upload, list, retrieve, update, delete (CRUD)
- ✅ Multimodal query endpoint (text + images)
- ✅ Image serving for page screenshots
- ✅ Background task processing for uploads
- ✅ Auto-generated API documentation (Swagger UI)
- ✅ Async/await support for efficiency

### Quick Start

```bash
# Start API server
make api

# Access documentation
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - Health: http://localhost:8000/health
```

### API Endpoints

#### Document Management

**Upload Document**
```bash
curl -X POST "http://localhost:8000/documents" \
  -F "file=@manual.pdf"
```

**List Documents**
```bash
curl "http://localhost:8000/documents"
```

**Get Document Details**
```bash
curl "http://localhost:8000/documents/{doc_id}"
```

**Delete Document**
```bash
curl -X DELETE "http://localhost:8000/documents/{doc_id}"
```

**Update Document**
```bash
curl -X PUT "http://localhost:8000/documents/{doc_id}" \
  -F "file=@new_manual.pdf"
```

#### Query

**Query Documents**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to install?",
    "similarity_top_k": 3,
    "include_images": true
  }'
```

#### Images

**Get Page Image**
```bash
curl "http://localhost:8000/images/{doc_id}/{page_number}" \
  --output page.jpg
```

### Python Client Example

```python
import requests

API_URL = "http://localhost:8000"

# Upload document
with open("manual.pdf", "rb") as f:
    response = requests.post(
        f"{API_URL}/documents",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]

# Query
response = requests.post(
    f"{API_URL}/query",
    json={
        "query": "How to install?",
        "similarity_top_k": 3
    }
)
print(response.json()["answer"])

# List documents
response = requests.get(f"{API_URL}/documents")
print(response.json())

# Delete document
requests.delete(f"{API_URL}/documents/{doc_id}")
```

### Testing the API

```bash
# Run example Python script
python examples/api_usage.py

# Or use the shell script
./examples/test_api.sh
```

### Production Deployment

```bash
# Multi-worker mode
make api-prod

# Or manually with 4 workers
cd src && uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

For detailed API documentation, see [`src/api/README.md`](src/api/README.md).

---

## Project Structure

```
Mag-/
├── src/                     # Application code
│   ├── config.py           # Centralized configuration
│   ├── app.py              # Streamlit web app (query interface)
│   ├── parse.py            # CLI batch document parser
│   ├── add_pdfs_batch.py   # Add PDFs to existing index
│   ├── api/                # FastAPI backend (NEW!)
│   │   ├── __init__.py     # API module exports
│   │   ├── main.py         # FastAPI app and configuration
│   │   ├── models.py       # Pydantic request/response models
│   │   ├── dependencies.py # Shared dependencies
│   │   ├── routes/         # API route modules
│   │   │   ├── documents.py # Document CRUD endpoints
│   │   │   ├── query.py    # Query endpoint
│   │   │   └── images.py   # Image serving endpoints
│   │   └── README.md       # API documentation
│   └── ingestion/          # Document management module
│       ├── __init__.py     # Module exports
│       ├── parser.py       # LlamaParse wrapper
│       ├── index_manager.py # Index lifecycle
│       ├── document_manager.py # CRUD operations
│       └── README.md       # Module documentation
├── examples/               # Usage examples (NEW!)
│   ├── api_usage.py        # Python API client example
│   └── test_api.sh         # Shell script for testing API
├── scripts/
│   ├── test_ingestion.py   # Ingestion test suite
│   ├── install-hooks.sh    # Git hook installer
│   └── clean.sh            # Cleanup utility
├── tests/                  # Test suite (43+ tests)
│   ├── test_config.py
│   ├── test_parse.py
│   ├── test_app.py
│   └── ...
├── data/                   # Input PDFs (your documents)
├── storage/                # Vector index (generated)
├── data_images/            # Page images (generated, by doc_id)
├── docs.md                 # LlamaIndex documentation reference
├── Makefile                # Common commands
├── requirements.txt        # Python dependencies
└── pytest.ini              # Test configuration
```

---

## Development

### Common Commands

```bash
make help               # Show all commands
make run                # Run Streamlit app
make api                # Run FastAPI server (development mode)
make api-prod           # Run FastAPI server (production mode with workers)
make parse              # Parse all PDFs (fresh index)
make add-batch          # Add PDFs to existing index
make test               # Run full test suite
make test-quick         # Fast tests (no coverage)
make clean              # Clean Python cache
make clean-storage      # Clear vector index
make format             # Format code (black + isort)
make lint               # Lint code (flake8 + mypy)
```

### Git Hook

Pre-commit hook runs tests automatically:

```bash
git commit -m "changes"  # Runs tests first
git commit --no-verify   # Skip tests (not recommended)

# Reinstall hook
./scripts/install-hooks.sh
```

---

## Testing

### Full Test Suite

```bash
make test               # Run all tests with coverage
make test-verbose       # Verbose output
make test-cov           # Coverage report (HTML + terminal)
make test-quick         # Fast (no coverage)
```

### Ingestion Module Tests

```bash
python scripts/test_ingestion.py
```

Tests all CRUD operations:
- ✅ Adding documents
- ✅ Listing documents
- ✅ Getting document info
- ✅ SOURCE relationship tracking
- ✅ Updating documents
- ✅ Deleting documents (index + images)

### Manual Testing (Python REPL)

```python
import asyncio
from src.ingestion import add_document, list_documents, delete_document

# Add a document
result = asyncio.run(add_document("data/manual.pdf"))
print(result)  # See document ID, page count

# List all
docs = list_documents()
print(f"Total documents: {len(docs)}")

# Delete
delete_document(result['document_id'])
```

### Validation Checklist

After running `make parse`, verify:

```bash
# 1. Check ref_doc_info is populated (SOURCE relationships work)
python3 -c "from src.ingestion import get_index; \
    print(f'Documents tracked: {len(get_index().ref_doc_info)}')"

# 2. Images exist in doc-specific directories
ls data_images/  # Should show UUID directories

# 3. Streamlit queries work
make run  # Test querying documents

# 4. Deletion works
python scripts/test_ingestion.py  # Run full test suite
```

**Success Criteria:**
- ✅ `ref_doc_info` shows tracked documents
- ✅ Images in `data_images/{doc_id}/` directories
- ✅ Streamlit finds and displays documents
- ✅ Test suite passes all tests
- ✅ Deletion removes index entries + images

---

## Tech Stack

- **LlamaIndex** - RAG framework with document tracking
- **LlamaParse** - PDF parsing with multimodal extraction
- **OpenAI/Gemini** - LLM and embeddings
- **Streamlit** - Web UI for query interface
- **FastAPI** - REST API for document management ✅
- **Uvicorn** - ASGI server for FastAPI
- **Pydantic** - Data validation and serialization
- **pytest** - Testing framework (43+ tests)

---

## Next Steps

### Phase 1: Validation ✅ (Completed)
- [x] Ingestion module implemented
- [x] Document tracking with SOURCE relationships
- [x] CLI batch processing
- [x] Test suite
- [x] Validate with your PDFs

### Phase 2: API Development ✅ (Completed)
- [x] Create `src/api/` directory
- [x] Build FastAPI application
- [x] Implement endpoints:
  - [x] `POST /documents` - Upload PDF
  - [x] `DELETE /documents/{id}` - Delete document
  - [x] `PUT /documents/{id}` - Update document
  - [x] `GET /documents` - List all documents
  - [x] `POST /query` - Query the RAG system
- [x] Add background job processing
- [x] Implement image serving
- [x] Auto-generated API documentation
- [x] Example scripts and usage guides

### Phase 3: Dockerization
- [ ] Write Dockerfile
- [ ] Docker Compose setup
- [ ] Volume management
- [ ] Environment configuration

### Phase 4: Production Hardening
- [ ] External vector DB (Chroma/Qdrant)
- [ ] S3/CDN for image storage
- [ ] PostgreSQL for metadata
- [ ] Message queue (RQ/Celery)
- [ ] Authentication & authorization
- [ ] Monitoring & logging

---

## Additional Documentation

- [`src/ingestion/README.md`](src/ingestion/README.md) - Detailed module API documentation
- [`docs.md`](docs.md) - LlamaIndex documentation reference and answers

---

## License

All rights reserved.
