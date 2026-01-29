#!/usr/bin/env python3
"""Test script for ingestion module.

This script tests the core document management operations:
- Adding documents
- Listing documents
- Getting document info
- Deleting documents
- Updating documents

Usage:
    python scripts/test_ingestion.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingestion import (
    add_document,
    delete_document,
    update_document,
    list_documents,
    get_document_info,
    get_index
)
from config import DATA_DIR, PERSIST_DIR


async def test_add_document():
    """Test adding a document."""
    print("\n" + "="*60)
    print("TEST 1: Add Document")
    print("="*60)
    
    # Find a PDF file to test with
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ No PDF files found in data directory!")
        return None
    
    test_file = os.path.join(DATA_DIR, pdf_files[0])
    print(f"📄 Adding document: {pdf_files[0]}")
    
    try:
        result = await add_document(test_file)
        print(f"✅ Success!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   Filename: {result['filename']}")
        print(f"   Pages: {result['page_count']}")
        print(f"   Timestamp: {result['timestamp']}")
        return result['document_id']
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_list_documents():
    """Test listing all documents."""
    print("\n" + "="*60)
    print("TEST 2: List Documents")
    print("="*60)
    
    try:
        docs = list_documents()
        print(f"📚 Found {len(docs)} document(s):")
        
        for doc_id, doc_info in docs.items():
            print(f"\n   Document ID: {doc_id}")
            print(f"   Filename: {doc_info['metadata'].get('filename', 'unknown')}")
            print(f"   Pages: {doc_info['page_count']}")
            print(f"   Nodes: {len(doc_info['node_ids'])}")
        
        print("\n✅ Success!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_document_info(doc_id):
    """Test getting detailed document info."""
    print("\n" + "="*60)
    print("TEST 3: Get Document Info")
    print("="*60)
    
    if not doc_id:
        print("⚠️  Skipping (no document ID)")
        return False
    
    print(f"🔍 Getting info for document: {doc_id}")
    
    try:
        info = get_document_info(doc_id)
        
        if not info:
            print(f"❌ Document not found!")
            return False
        
        print(f"✅ Success!")
        print(f"   Filename: {info['filename']}")
        print(f"   Pages: {info['page_count']}")
        print(f"   First page preview: {info['pages'][0]['text_preview'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_delete_document(doc_id):
    """Test deleting a document."""
    print("\n" + "="*60)
    print("TEST 4: Delete Document")
    print("="*60)
    
    if not doc_id:
        print("⚠️  Skipping (no document ID)")
        return False
    
    print(f"🗑️  Deleting document: {doc_id}")
    
    try:
        result = delete_document(doc_id)
        print(f"✅ Success!")
        print(f"   Images deleted: {result['images_deleted']}")
        print(f"   Timestamp: {result['timestamp']}")
        
        # Verify it's gone
        docs = list_documents()
        if doc_id in docs:
            print(f"❌ Document still exists after deletion!")
            return False
        
        print(f"   ✓ Verified document removed from index")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_update_document(doc_id):
    """Test updating a document."""
    print("\n" + "="*60)
    print("TEST 5: Update Document")
    print("="*60)
    
    # Find a PDF file to test with
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("⚠️  Skipping (no PDF files)")
        return False
    
    # Add a document first
    test_file = os.path.join(DATA_DIR, pdf_files[0])
    print(f"📄 First, adding document: {pdf_files[0]}")
    
    try:
        add_result = await add_document(test_file)
        doc_id = add_result['document_id']
        print(f"   ✓ Added with ID: {doc_id}")
        
        # Now update it with the same file (or another if available)
        update_file = os.path.join(DATA_DIR, pdf_files[-1])  # Last file
        print(f"📝 Updating with: {pdf_files[-1]}")
        
        result = await update_document(doc_id, update_file)
        print(f"✅ Success!")
        print(f"   Document ID: {result['document_id']}")
        print(f"   New filename: {result['filename']}")
        print(f"   New page count: {result['page_count']}")
        print(f"   Old images deleted: {result['old_images_deleted']}")
        
        # Clean up
        delete_document(doc_id)
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ref_doc_info():
    """Test that ref_doc_info is properly tracking documents."""
    print("\n" + "="*60)
    print("TEST 6: Verify ref_doc_info Tracking")
    print("="*60)
    
    try:
        index = get_index()
        ref_doc_info = index.ref_doc_info
        
        print(f"📊 Index tracking {len(ref_doc_info)} document(s)")
        
        for doc_id, doc_info in ref_doc_info.items():
            print(f"\n   Document: {doc_id}")
            print(f"   Nodes: {len(doc_info.node_ids)}")
            
            # Check first node has SOURCE relationship
            if doc_info.node_ids:
                first_node = index.docstore.get_node(doc_info.node_ids[0])
                print(f"   Has metadata: {bool(first_node.metadata)}")
                print(f"   Has SOURCE relationship: {first_node.ref_doc_id == doc_id}")
        
        print("\n✅ Success!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 INGESTION MODULE TEST SUITE")
    print("="*60)
    
    # Check if index exists
    if not os.path.exists(PERSIST_DIR):
        print("\n⚠️  No index found! Please run 'make parse' first.")
        print("   Or this test will create a fresh index.")
    
    # Run tests
    results = {}
    
    # Test 1: Add
    doc_id = await test_add_document()
    results['add'] = doc_id is not None
    
    # Test 2: List
    results['list'] = test_list_documents()
    
    # Test 3: Get info
    results['info'] = test_get_document_info(doc_id)
    
    # Test 4: ref_doc_info
    results['tracking'] = test_ref_doc_info()
    
    # Test 5: Update
    results['update'] = await test_update_document(doc_id)
    
    # Test 6: Delete (do this last)
    results['delete'] = test_delete_document(doc_id)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {test_name.upper()}: {status}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

