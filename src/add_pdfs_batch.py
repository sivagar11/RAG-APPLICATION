"""Add PDFs to existing index without rebuilding.

This script adds new documents to an existing index. Use this when:
- You've already built an initial index with parse.py
- The API is running and has added/modified documents
- You want to batch-add more PDFs without losing existing data

For initial setup, use parse.py instead (which rebuilds the index).

Usage:
    python src/add_pdfs_batch.py
    OR
    make add-batch
"""

import os
import asyncio
import uuid
from llama_index.core import Settings

# Import configuration
from config import (
    DATA_DIR,
    validate_config,
)

# Import ingestion module
from ingestion import add_document, get_index, list_documents

# Validate configuration
validate_config()


def get_data_files(data_dir=DATA_DIR):
    """Get all PDF files from the data directory."""
    files = []
    for f in os.listdir(data_dir):
        file_path = os.path.join(data_dir, f)
        if os.path.isfile(file_path) and f.lower().endswith('.pdf'):
            files.append(file_path)
    return files


async def main():
    """Add PDFs from data directory to existing index."""
    
    print("📦 Connecting to Qdrant Cloud...")
    
    # Try to load existing index to verify connection
    try:
        existing_docs = list_documents()
        print(f"✅ Connected! Currently indexed: {len(existing_docs)} document(s)")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("   Please run 'python src/parse.py' first to create the initial index.")
        return
    
    print("\n📂 Scanning for PDF files...")
    files = get_data_files()
    
    if not files:
        print(f"⚠️  No PDF files found in {DATA_DIR}")
        return
    
    print(f"📄 Found {len(files)} PDF file(s):")
    for f in files:
        print(f"   - {os.path.basename(f)}")
    
    # Build set of existing filenames to avoid duplicates
    existing_filenames = set()
    for doc_info in existing_docs.values():
        filename = doc_info['metadata'].get('filename')
        if filename:
            existing_filenames.add(filename)
    
    # Filter to only new files
    new_files = []
    duplicate_files = []
    
    for file_path in files:
        filename = os.path.basename(file_path)
        if filename in existing_filenames:
            duplicate_files.append(filename)
        else:
            new_files.append(file_path)
    
    if duplicate_files:
        print(f"\n⚠️  Skipping {len(duplicate_files)} already-indexed file(s):")
        for filename in duplicate_files:
            print(f"   - {filename}")
    
    if not new_files:
        print("\n✅ All files are already indexed. Nothing to add.")
        return
    
    print(f"\n📝 Adding {len(new_files)} new document(s)...")
    
    added_count = 0
    failed_count = 0
    doc_ids = []
    
    for i, file_path in enumerate(new_files, 1):
        filename = os.path.basename(file_path)
        
        print(f"   [{i}/{len(new_files)}] Adding {filename}...")
        
        try:
            result = await add_document(file_path)
            doc_ids.append(result['document_id'])
            added_count += 1
            
            print(f"       ✅ Added with {result['page_count']} pages")
            print(f"          Document ID: {result['document_id']}")
        except Exception as e:
            print(f"       ❌ Error: {e}")
            failed_count += 1
            continue
    
    print(f"\n📊 Summary:")
    print(f"   Documents added: {added_count}")
    if failed_count:
        print(f"   Failed: {failed_count}")
    print(f"   Total indexed (after addition): {len(existing_docs) + added_count}")
    
    if doc_ids:
        print(f"\n   New Document IDs:")
        for doc_id, file_path in zip(doc_ids, new_files):
            print(f"      {doc_id} → {os.path.basename(file_path)}")
    
    print("\n✨ Done! New documents added to existing index.")


if __name__ == "__main__":
    asyncio.run(main())

