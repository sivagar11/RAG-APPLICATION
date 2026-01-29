#!/usr/bin/env python3
"""Example usage of the RAG-MAG API.

This script demonstrates how to interact with the API programmatically.

Usage:
    python examples/api_usage.py
"""

import requests
import time
import os
from pathlib import Path

# API Configuration
API_URL = "http://localhost:8000"


def check_health():
    """Check API health."""
    print("\n" + "="*60)
    print("Checking API Health")
    print("="*60)
    
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"   Version: {data['version']}")
        print(f"   Documents: {data['documents_indexed']}")
        return True
    else:
        print(f"❌ API unhealthy: {response.status_code}")
        return False


def upload_document(pdf_path: str):
    """Upload a PDF document."""
    print("\n" + "="*60)
    print(f"Uploading Document: {pdf_path}")
    print("="*60)
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return None
    
    with open(pdf_path, "rb") as f:
        response = requests.post(
            f"{API_URL}/documents",
            files={"file": ("document.pdf", f, "application/pdf")}
        )
    
    if response.status_code == 202:
        data = response.json()
        print(f"✅ Upload accepted!")
        print(f"   Document ID: {data['document_id']}")
        print(f"   Filename: {data['filename']}")
        print(f"   Status: {data['status']}")
        return data['document_id']
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   {response.text}")
        return None


def list_documents():
    """List all documents."""
    print("\n" + "="*60)
    print("Listing All Documents")
    print("="*60)
    
    response = requests.get(f"{API_URL}/documents")
    
    if response.status_code == 200:
        data = response.json()
        print(f"📚 Total documents: {data['total_documents']}")
        
        for doc in data['documents']:
            print(f"\n   Document ID: {doc['document_id']}")
            print(f"   Filename: {doc['filename']}")
            print(f"   Pages: {doc['page_count']}")
        
        return data['documents']
    else:
        print(f"❌ Failed to list documents: {response.status_code}")
        return []


def get_document_details(doc_id: str):
    """Get detailed information about a document."""
    print("\n" + "="*60)
    print(f"Getting Document Details: {doc_id}")
    print("="*60)
    
    response = requests.get(f"{API_URL}/documents/{doc_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Document found!")
        print(f"   Filename: {data['filename']}")
        print(f"   Pages: {data['page_count']}")
        print(f"   Nodes: {len(data['node_ids'])}")
        
        # Show first page
        if data['pages']:
            page = data['pages'][0]
            print(f"\n   First page:")
            print(f"   - Page number: {page['page_number']}")
            print(f"   - Text preview: {page['text_preview'][:100]}...")
        
        return data
    elif response.status_code == 404:
        print(f"❌ Document not found: {doc_id}")
        return None
    else:
        print(f"❌ Failed: {response.status_code}")
        return None


def query_documents(query: str, similarity_top_k: int = 3):
    """Query the document collection."""
    print("\n" + "="*60)
    print(f"Querying: {query}")
    print("="*60)
    
    response = requests.post(
        f"{API_URL}/query",
        json={
            "query": query,
            "similarity_top_k": similarity_top_k,
            "include_images": True
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🧠 Answer:")
        print(f"   {data['answer']}")
        
        print(f"\n📚 Sources ({len(data['source_nodes'])} nodes):")
        for i, node in enumerate(data['source_nodes'], 1):
            print(f"\n   Source {i}:")
            print(f"   - File: {node['filename']}")
            print(f"   - Page: {node['page_number']}")
            if node['score']:
                print(f"   - Score: {node['score']:.3f}")
            print(f"   - Preview: {node['text_preview'][:100]}...")
        
        print(f"\n⏱️  Processing time: {data['processing_time']:.2f}s")
        
        return data
    elif response.status_code == 404:
        print(f"❌ No relevant documents found")
        return None
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(f"   {response.text}")
        return None


def delete_document(doc_id: str):
    """Delete a document."""
    print("\n" + "="*60)
    print(f"Deleting Document: {doc_id}")
    print("="*60)
    
    response = requests.delete(f"{API_URL}/documents/{doc_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Document deleted!")
        print(f"   Images deleted: {data['images_deleted']}")
        print(f"   Timestamp: {data['timestamp']}")
        return True
    elif response.status_code == 404:
        print(f"❌ Document not found: {doc_id}")
        return False
    else:
        print(f"❌ Deletion failed: {response.status_code}")
        return False


def download_image(doc_id: str, page_number: int, output_path: str):
    """Download a page image."""
    print("\n" + "="*60)
    print(f"Downloading Image: {doc_id} page {page_number}")
    print("="*60)
    
    response = requests.get(f"{API_URL}/images/{doc_id}/{page_number}")
    
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✅ Image saved to: {output_path}")
        return True
    else:
        print(f"❌ Failed to download image: {response.status_code}")
        return False


def main():
    """Run example workflow."""
    print("\n" + "="*60)
    print("RAG-MAG API Usage Example")
    print("="*60)
    
    # Check health
    if not check_health():
        print("\n❌ API is not running. Start it with 'make api'")
        return
    
    # List existing documents
    docs = list_documents()
    
    # If there are documents, query them
    if docs:
        # Get details of first document
        first_doc = docs[0]
        doc_details = get_document_details(first_doc['document_id'])
        
        # Query documents
        query_documents("How do I install this?")
        query_documents("What is the warranty period?")
        
        # Optionally download an image
        if doc_details and doc_details['pages']:
            output_dir = Path("examples/downloads")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            download_image(
                first_doc['document_id'],
                1,
                str(output_dir / "page_1.jpg")
            )
    else:
        print("\n⚠️  No documents found. Upload some PDFs first!")
        print("   Example: PUT your PDFs in 'data/' and run 'make parse'")
    
    # Example: Upload a new document (if available)
    data_dir = Path("data")
    if data_dir.exists():
        pdf_files = list(data_dir.glob("*.pdf"))
        if pdf_files:
            print("\n💡 Example: Uploading a document...")
            doc_id = upload_document(str(pdf_files[0]))
            
            if doc_id:
                # Wait a bit for processing
                print("\n⏳ Waiting for processing...")
                time.sleep(3)
                
                # Check status
                get_document_details(doc_id)
                
                # Example: Delete the document
                print("\n💡 Example: Deleting the document...")
                delete_document(doc_id)
    
    print("\n" + "="*60)
    print("✨ Example completed!")
    print("="*60)


if __name__ == "__main__":
    main()

