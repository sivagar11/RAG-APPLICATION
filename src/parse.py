"""Parse and index all PDFs in the data directory.

This is a CLI script for batch processing documents. It uses the ingestion
module to properly track documents with SOURCE relationships.

Usage:
    python src/parse.py
    OR
    make parse
"""

import os
import asyncio
import uuid
from llama_index.core import Settings

# Import configuration
from config import (
    DATA_DIR,
    IMAGE_DIR,
    PERSIST_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    VECTOR_DB_TYPE,
    QDRANT_COLLECTION,
    validate_config,
    print_config_summary,
)

# Import ingestion module
from ingestion.parser import parse_pdf
from ingestion.index_manager import create_new_index, persist_index

# Validate configuration
validate_config()

# Create directories
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(PERSIST_DIR, exist_ok=True)

# Print configuration summary
print_config_summary()


def get_data_files(data_dir=DATA_DIR):
    """Get all PDF files from the data directory."""
    files = []
    for f in os.listdir(data_dir):
        file_path = os.path.join(data_dir, f)
        if os.path.isfile(file_path) and f.lower().endswith('.pdf'):
            files.append(file_path)
    return files


async def main():
    """Parse all PDFs and create a new index."""
    print("\n📂 Scanning for PDF files...")
    files = get_data_files()
    
    if not files:
        print(f"⚠️  No PDF files found in {DATA_DIR}")
        return
    
    print(f"📄 Found {len(files)} PDF file(s):")
    for f in files:
        print(f"   - {os.path.basename(f)}")
    
    print("\n🔧 Creating new index...")
    
    # Configure RAG parameters
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP
    
    # Create new index (this also sets up LLM settings)
    index = create_new_index()
    
    # Parse each file with a unique document ID
    all_nodes = []
    doc_ids = []
    
    print("\n📝 Parsing documents...")
    for i, file_path in enumerate(files, 1):
        filename = os.path.basename(file_path)
        doc_id = str(uuid.uuid4())
        
        print(f"   [{i}/{len(files)}] Parsing {filename}...")
        
        try:
            # Parse PDF with SOURCE relationship set
            nodes = await parse_pdf(file_path, doc_id)
            all_nodes.extend(nodes)
            doc_ids.append(doc_id)
            
            print(f"       ✅ Extracted {len(nodes)} pages")
        except Exception as e:
            print(f"       ❌ Error: {e}")
            continue
    
    if not all_nodes:
        print("\n❌ No nodes extracted. Exiting.")
        return
    
    print(f"\n🔨 Building vector index with {len(all_nodes)} nodes...")
    
    # Insert nodes in small batches to avoid payload size and timeout limits
    batch_size = 2  # Upload 2 pages at a time for reliable uploads
    total_batches = (len(all_nodes) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(all_nodes))
        batch = all_nodes[start_idx:end_idx]
        
        print(f"   Uploading batch {batch_num + 1}/{total_batches} ({len(batch)} nodes)...")
        index.insert_nodes(batch)
    
    # Persist to storage
    persist_index()
    
    if VECTOR_DB_TYPE == "local":
        print(f"✅ Index saved to {PERSIST_DIR}")
    else:
        print(f"✅ Index saved to {VECTOR_DB_TYPE.upper()} (collection: {QDRANT_COLLECTION})")
    
    print(f"\n📊 Summary:")
    print(f"   Documents indexed: {len(doc_ids)}")
    print(f"   Total pages: {len(all_nodes)}")
    print(f"   Document IDs:")
    for doc_id, file_path in zip(doc_ids, files):
        print(f"      {doc_id} → {os.path.basename(file_path)}")
    
    print("\n✨ Done! You can now:")
    print("   - Run 'make run' or 'streamlit run src/app.py' to query documents")
    print("   - Use the ingestion API to add/delete/update documents")


if __name__ == "__main__":
    asyncio.run(main())
