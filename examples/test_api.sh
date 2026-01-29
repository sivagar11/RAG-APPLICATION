#!/bin/bash
# Test script for RAG-MAG API using cURL

set -e

API_URL="http://localhost:8000"
TEST_PDF="data/CK8518-18kg-manual.pdf"

echo "=========================================="
echo "RAG-MAG API Test Script"
echo "=========================================="

# Health check
echo ""
echo "1. Health Check"
echo "----------------------------------------"
curl -s "$API_URL/health" | python3 -m json.tool

# List documents
echo ""
echo "2. List Documents"
echo "----------------------------------------"
curl -s "$API_URL/documents" | python3 -m json.tool

# Upload document (if test PDF exists)
if [ -f "$TEST_PDF" ]; then
    echo ""
    echo "3. Upload Document"
    echo "----------------------------------------"
    UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/documents" \
        -F "file=@$TEST_PDF")
    
    echo "$UPLOAD_RESPONSE" | python3 -m json.tool
    
    # Extract document ID
    DOC_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['document_id'])")
    
    echo ""
    echo "Document ID: $DOC_ID"
    
    # Wait for processing
    echo ""
    echo "Waiting 5 seconds for processing..."
    sleep 5
    
    # Get document details
    echo ""
    echo "4. Get Document Details"
    echo "----------------------------------------"
    curl -s "$API_URL/documents/$DOC_ID" | python3 -m json.tool
    
    # Delete document
    echo ""
    echo "5. Delete Document"
    echo "----------------------------------------"
    curl -s -X DELETE "$API_URL/documents/$DOC_ID" | python3 -m json.tool
else
    echo ""
    echo "⚠️  Test PDF not found: $TEST_PDF"
    echo "   Skipping upload test."
fi

# Query example
echo ""
echo "6. Query Documents"
echo "----------------------------------------"
curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "How to install?",
        "similarity_top_k": 3,
        "include_images": true
    }' | python3 -m json.tool

echo ""
echo "=========================================="
echo "✅ API Tests Complete!"
echo "=========================================="

