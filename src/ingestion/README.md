# Ingestion Module

This module provides document management functionality for the RAG-MAG system. It handles adding, deleting, updating, and listing documents with proper LlamaIndex document tracking.

## Architecture

The ingestion module is built with three core components:

### 1. `parser.py` - PDF Parsing
- Wraps LlamaParse for PDF processing
- Sets SOURCE relationships on TextNodes for document tracking
- Creates document-specific image directories
- Attaches metadata (document_id, filename, page_number, image_path)

### 2. `index_manager.py` - Index Lifecycle
- Manages VectorStoreIndex singleton
- Handles index loading/reloading
- Configures LLM and embedding models
- Provides thread-safe access via async locks

### 3. `document_manager.py` - CRUD Operations
- `add_document()` - Add new PDF to index
- `delete_document()` - Remove document and images
- `update_document()` - Replace existing document
- `list_documents()` - List all indexed documents
- `get_document_info()` - Get detailed document information

## Key Concepts

### Document Tracking with SOURCE Relationships

LlamaIndex requires proper SOURCE relationships for document tracking:

```python
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

# Set SOURCE relationship on each node
node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc_id)
```

This enables:
- Grouping nodes by document
- Deletion by document ID: `index.delete_ref_doc(doc_id)`
- Tracking via `index.ref_doc_info`

### Document ID Management

Each document gets a UUID:
```python
import uuid
doc_id = str(uuid.uuid4())
```

This ID is used for:
- Node SOURCE relationships
- Image directory naming: `data_images/{doc_id}/page_1.jpg`
- Metadata tracking
- API operations

### Image Organization

Images are stored in document-specific directories:
```
data_images/
├── {doc-id-1}/
│   ├── page_1.jpg
│   ├── page_2.jpg
│   └── ...
├── {doc-id-2}/
│   ├── page_1.jpg
│   └── ...
```

This prevents:
- Filename conflicts between documents
- Orphaned images after deletion
- Need for complex image tracking

## Usage

### Basic Operations

```python
from ingestion import add_document, delete_document, list_documents

# Add a document
result = await add_document("path/to/manual.pdf")
doc_id = result['document_id']

# List all documents
docs = list_documents()
for doc_id, info in docs.items():
    print(f"{doc_id}: {info['metadata']['filename']}")

# Delete a document
delete_document(doc_id)
```

### Advanced Operations

```python
from ingestion import update_document, get_document_info, get_index

# Update a document (replace with new PDF)
result = await update_document(doc_id, "path/to/new_manual.pdf")

# Get detailed document info
info = get_document_info(doc_id)
print(f"Filename: {info['filename']}")
print(f"Pages: {info['page_count']}")
for page in info['pages']:
    print(f"  Page {page['page_number']}: {page['text_preview']}")

# Direct index access (for custom operations)
index = get_index()
ref_doc_info = index.ref_doc_info
```

### CLI Usage

The refactored `parse.py` uses this module:

```bash
# Parse all PDFs in data directory
python src/parse.py
# OR
make parse
```

This will:
1. Scan for PDF files
2. Generate unique document IDs
3. Parse with SOURCE relationships
4. Create the vector index
5. Display document IDs for tracking

### Testing

Run the test suite:

```bash
python scripts/test_ingestion.py
```

This tests:
- Adding documents
- Listing documents
- Getting document info
- SOURCE relationship tracking
- Updating documents
- Deleting documents

## API Integration (Future)

This module is designed to be used by a FastAPI backend:

```python
from fastapi import FastAPI, UploadFile
from ingestion import add_document, delete_document

app = FastAPI()

@app.post("/documents")
async def upload_document(file: UploadFile):
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())
    
    # Add to index
    result = await add_document(temp_path)
    return result

@app.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    result = delete_document(doc_id)
    return result
```

## Technical Details

### Thread Safety

- Uses `asyncio.Lock()` for write operations
- Safe within single process
- **NOT safe across multiple processes** (use external vector DB for that)

### Persistence

Changes are NOT auto-persisted. You must call:
```python
from ingestion import persist_index

# After modifications
persist_index()
```

The module handles this automatically in CRUD operations.

### Index Reloading

If the index is modified externally:
```python
from ingestion import reload_index

# Force reload from disk
index = reload_index()
```

### Error Handling

All operations raise exceptions on failure:
```python
try:
    result = await add_document("invalid.pdf")
except FileNotFoundError:
    print("PDF not found")
except Exception as e:
    print(f"Parsing failed: {e}")
```

## Configuration

The module uses settings from `config.py`:

- `LLAMAPARSE_*` - Parser configuration
- `IMAGE_DIR` - Where images are stored
- `PERSIST_DIR` - Vector index storage
- `LLM_PROVIDER` - OpenAI or Gemini
- `CHUNK_SIZE`, `CHUNK_OVERLAP` - RAG parameters

## Limitations

1. **Single Process**: Index singleton only works within one process
2. **Manual Locking**: API must use locks for concurrent operations
3. **No Transaction Support**: Operations are not atomic
4. **Image Storage**: Uses local filesystem (not scalable for production)

For production, consider:
- External vector database (Chroma, Qdrant)
- S3/CDN for image storage
- Message queue for async processing
- PostgreSQL for metadata tracking

## Development

### Running Tests

```bash
# Test ingestion module
python scripts/test_ingestion.py

# Test everything
make test
```

### Adding New Operations

To add new document operations:

1. Add function to `document_manager.py`
2. Export in `__init__.py`
3. Add test in `scripts/test_ingestion.py`
4. Update this README

### Debugging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check index state:
```python
from ingestion import get_index

index = get_index()
print(f"Documents: {len(index.ref_doc_info)}")
print(f"Nodes: {len(index.docstore.docs)}")
```

## References

- [LlamaIndex Document Management](https://docs.llamaindex.ai/en/stable/understanding/indexing/indexing/)
- [TextNode Documentation](https://docs.llamaindex.ai/en/stable/api_reference/schema/)
- [VectorStoreIndex API](https://docs.llamaindex.ai/en/stable/api_reference/indices/vector_store/)

