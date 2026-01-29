# Vector Database Configuration Guide

This guide explains the vector database configuration options and how to customize your setup.

**Current Setup**: Qdrant Cloud with base64 image storage (recommended for most use cases)

## 📋 **Table of Contents**

- [Overview](#overview)
- [Architecture Comparison](#architecture-comparison)
- [Migration Options](#migration-options)
- [Step-by-Step Setup](#step-by-step-setup)
- [Configuration Scenarios](#configuration-scenarios)
- [Performance Comparison](#performance-comparison)
- [Troubleshooting](#troubleshooting)

---

## 🎯 **Overview**

### **Why Migrate to External Vector DB?**

| Feature | Local Storage | Qdrant/External DB |
|---------|--------------|-------------------|
| **Multi-process** | ❌ Single process only | ✅ Multiple workers |
| **Scalability** | ❌ Limited by disk | ✅ Horizontally scalable |
| **Concurrent Access** | ❌ Not thread-safe | ✅ Thread-safe |
| **Performance** | ⚠️ Good for small scale | ✅ Optimized for scale |
| **Cloud Ready** | ❌ Requires shared disk | ✅ Native cloud support |
| **Image Storage** | ❌ Local filesystem | ✅ Can store in DB or S3 |

---

## 🏗️ **Architecture Comparison**

### **Current Architecture (Local)**

```
┌─────────────────┐
│  FastAPI/App    │
│   (Single)      │
└────────┬────────┘
         │
    ┌────▼─────────────────┐
    │ SimpleVectorStore    │
    │  + JSON Files        │
    │  storage/            │
    └──────────────────────┘
         │
    ┌────▼─────────────────┐
    │ Local Filesystem     │
    │  data_images/        │
    └──────────────────────┘
```

### **New Architecture (Qdrant + S3)**

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ FastAPI #1  │  │ FastAPI #2  │  │ FastAPI #N  │
│ (Worker 1)  │  │ (Worker 2)  │  │ (Worker N)  │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
            ┌───────────▼───────────┐
            │   Qdrant Vector DB    │
            │  (Shared, Persistent) │
            └───────────────────────┘
                        │
            ┌───────────▼───────────┐
            │    S3 / R2 / CDN      │
            │  (Image Storage)      │
            └───────────────────────┘
```

---

## 🔄 **Migration Options**

### **Option 1: Local Development with Qdrant (Docker)**

**Best for**: Testing, Development

```bash
# 1. Start Qdrant
docker-compose up -d qdrant

# 2. Update .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
IMAGE_STORAGE_TYPE=local
IMAGE_STORAGE_FORMAT=url

# 3. Re-parse documents
make parse
```

**Pros**: Easy setup, no cloud costs  
**Cons**: Still local, not production-ready

### **Option 2: Qdrant + Base64 Images (All-in-One)**

**Best for**: Small to medium datasets, simple deployment

```bash
# 1. Start Qdrant
docker-compose up -d qdrant

# 2. Update .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
IMAGE_STORAGE_TYPE=local
IMAGE_STORAGE_FORMAT=base64

# 3. Re-parse documents
make parse
```

**Pros**: Single storage system, atomic operations  
**Cons**: 33% storage overhead, payload size limits (~10MB)

### **Option 3: Qdrant Cloud + S3 (Production)**

**Best for**: Production deployments, scalability

```bash
# 1. Create Qdrant Cloud cluster (free tier available)
# Visit: https://cloud.qdrant.io

# 2. Create S3 bucket or Cloudflare R2

# 3. Update .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key
IMAGE_STORAGE_TYPE=s3
IMAGE_STORAGE_FORMAT=url
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=rag-mag-images

# 4. Re-parse documents
make parse
```

**Pros**: Fully scalable, production-ready, CDN integration  
**Cons**: Cloud costs, more complex setup

### **Option 4: Hybrid (Thumbnails + S3)**

**Best for**: Fast previews + high-quality originals

```bash
# Update .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
IMAGE_STORAGE_TYPE=s3
IMAGE_STORAGE_FORMAT=hybrid  # Stores thumbnails in Qdrant, full images in S3
```

**Pros**: Fast queries (thumbnails), full quality on demand  
**Cons**: Dual storage system

---

## 🚀 **Step-by-Step Setup**

### **Step 1: Install Dependencies**

```bash
# Install new dependencies
pip install -r requirements.txt

# Verify Qdrant client
python -c "import qdrant_client; print('✅ Qdrant client installed')"
```

### **Step 2: Start Qdrant (Local Development)**

```bash
# Using Docker Compose
docker-compose up -d qdrant

# Verify Qdrant is running
curl http://localhost:6333/health
# Expected: {"status":"ok"}
```

### **Step 3: Configure Environment**

```bash
# Copy example environment
cp env.example .env

# Edit .env with your settings
# Example for local Qdrant:
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
IMAGE_STORAGE_TYPE=local
IMAGE_STORAGE_FORMAT=url
```

### **Step 4: Migrate Existing Data**

#### **Option A: Fresh Start (Recommended)**

```bash
# Parse all documents fresh into Qdrant
make parse
```

#### **Option B: Export and Import (Preserve IDs)**

```python
# Script to migrate existing data
from src.ingestion import list_documents
from src.ingestion.document_manager import add_document
import asyncio

async def migrate():
    # Get list of PDF files
    import os
    from src.config import DATA_DIR
    
    pdfs = [f for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]
    
    for pdf in pdfs:
        pdf_path = os.path.join(DATA_DIR, pdf)
        print(f"Migrating {pdf}...")
        result = await add_document(pdf_path)
        print(f"  ✅ {result['document_id']}")

asyncio.run(migrate())
```

### **Step 5: Verify Migration**

```bash
# Check documents are indexed
python -c "from src.ingestion import list_documents; print(f'Documents: {len(list_documents())}')"

# Test query via API
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "similarity_top_k": 3}'
```

---

## ⚙️ **Configuration Scenarios**

### **Scenario 1: Local Development**

```bash
# .env
VECTOR_DB_TYPE=local
IMAGE_STORAGE_TYPE=local
```

**Use case**: Local testing, no external dependencies

### **Scenario 2: Qdrant Local + Local Images**

```bash
# .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
IMAGE_STORAGE_TYPE=local
IMAGE_STORAGE_FORMAT=url
```

**Use case**: Testing Qdrant, keeping images local

### **Scenario 3: Qdrant Local + Base64 Images**

```bash
# .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
IMAGE_STORAGE_TYPE=local
IMAGE_STORAGE_FORMAT=base64
```

**Use case**: All data in Qdrant, simple deployment

### **Scenario 4: Qdrant Cloud + S3 (Production)**

```bash
# .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=https://xyz-abc.qdrant.io
QDRANT_API_KEY=your-key
IMAGE_STORAGE_TYPE=s3
IMAGE_STORAGE_FORMAT=url
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET_NAME=rag-images
AWS_REGION=us-east-1
```

**Use case**: Production deployment, unlimited scale

### **Scenario 5: Cloudflare R2 (S3-Compatible)**

```bash
# .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=https://your-cluster.qdrant.io
IMAGE_STORAGE_TYPE=r2
IMAGE_STORAGE_FORMAT=url
AWS_ACCESS_KEY_ID=your-r2-access-key
AWS_SECRET_ACCESS_KEY=your-r2-secret-key
S3_BUCKET_NAME=rag-images
S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
```

**Use case**: Lower egress costs than S3, similar features

---

## 📊 **Performance Comparison**

### **Storage Sizes (1000 page manual)**

| Configuration | Text Vectors | Images | Total |
|--------------|-------------|--------|-------|
| **Local (JSON)** | ~50MB | ~200MB | ~250MB |
| **Qdrant + Local** | ~45MB (in Qdrant) | ~200MB (filesystem) | ~245MB |
| **Qdrant + Base64** | ~310MB (in Qdrant) | 0 | ~310MB |
| **Qdrant + S3** | ~45MB (in Qdrant) | ~200MB (S3) | ~245MB |
| **Qdrant + Hybrid** | ~50MB (in Qdrant) | ~200MB (S3) | ~250MB |

### **Query Performance**

| Configuration | First Query | Subsequent | Concurrent |
|--------------|------------|------------|------------|
| **Local** | 200ms | 150ms | ❌ Blocked |
| **Qdrant Local** | 180ms | 120ms | ✅ 100+ QPS |
| **Qdrant Cloud** | 250ms | 180ms | ✅ 1000+ QPS |

---

## 🐛 **Troubleshooting**

### **Qdrant Connection Issues**

```bash
# Test connection
curl http://localhost:6333/health

# Check Docker logs
docker logs rag-qdrant

# Restart Qdrant
docker-compose restart qdrant
```

### **S3 Upload Failures**

```bash
# Test S3 credentials
aws s3 ls s3://your-bucket --profile your-profile

# Check bucket permissions
# Ensure bucket policy allows PutObject, GetObject, DeleteObject
```

### **Image Not Found Errors**

```python
# Verify image storage manager
from src.ingestion.image_storage import get_image_storage_manager

manager = get_image_storage_manager()
print(f"Storage type: {manager.storage_type}")
print(f"Storage format: {manager.storage_format}")
```

### **Migration Stalled**

```bash
# Check Qdrant collection exists
curl http://localhost:6333/collections/rag_documents

# Reset collection (WARNING: Deletes all data)
curl -X DELETE http://localhost:6333/collections/rag_documents
```

---

## 🎯 **Recommended Configurations**

| Environment | Vector DB | Image Storage | Format |
|------------|-----------|---------------|--------|
| **Local Dev** | local | local | url |
| **Testing** | qdrant (docker) | local | url |
| **Staging** | qdrant (cloud) | S3/R2 | url |
| **Production** | qdrant (cloud) | S3/R2 + CDN | hybrid |

---

## 📚 **Additional Resources**

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [LlamaIndex Vector Stores](https://docs.llamaindex.ai/en/stable/module_guides/storing/vector_stores/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Cloudflare R2](https://developers.cloudflare.com/r2/)

---

## 🆘 **Support**

For issues or questions:
1. Check this migration guide
2. Review `VECTOR_DB_MIGRATION.md`
3. Check Qdrant logs: `docker logs rag-qdrant`
4. Verify configuration in `.env`

