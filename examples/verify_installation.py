#!/usr/bin/env python3
"""Verify RAG-MAG API installation and setup.

This script checks that all components are properly configured and working.

Usage:
    python examples/verify_installation.py
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def check_environment():
    """Check environment variables."""
    print("\n" + "="*60)
    print("1. Checking Environment Variables")
    print("="*60)
    
    required_vars = [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY", 
        "LLAMAPARSE_API_KEY",
    ]
    
    optional_vars = [
        "LLM_PROVIDER",
        "DATA_DIR",
        "IMAGE_DIR",
        "PERSIST_DIR",
    ]
    
    issues = []
    
    # Check required
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"❌ {var}: Not set")
            issues.append(f"{var} not configured")
        else:
            # Show partial key for security
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked}")
    
    # Check optional
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Using default")
    
    return issues


def check_dependencies():
    """Check required Python packages."""
    print("\n" + "="*60)
    print("2. Checking Python Dependencies")
    print("="*60)
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "streamlit",
        "llama_index",
        "llama_cloud_services",
        "openai",
        "google.generativeai",
        "pydantic",
        "PIL",
    ]
    
    issues = []
    
    for package in required_packages:
        try:
            if package == "llama_index":
                import llama_index
            elif package == "llama_cloud_services":
                import llama_cloud_services
            elif package == "google.generativeai":
                import google.generativeai
            elif package == "PIL":
                import PIL
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}: Not installed")
            issues.append(f"{package} not installed")
    
    return issues


def check_directories():
    """Check required directories."""
    print("\n" + "="*60)
    print("3. Checking Directories")
    print("="*60)
    
    from config import DATA_DIR, IMAGE_DIR, PERSIST_DIR
    
    dirs = {
        "DATA_DIR": DATA_DIR,
        "IMAGE_DIR": IMAGE_DIR,
        "PERSIST_DIR": PERSIST_DIR,
    }
    
    issues = []
    
    for name, path in dirs.items():
        if os.path.exists(path):
            # Count files
            if name == "DATA_DIR":
                pdf_count = len([f for f in os.listdir(path) if f.endswith('.pdf')])
                print(f"✅ {name}: {path} ({pdf_count} PDFs)")
            elif name == "IMAGE_DIR":
                doc_dirs = len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
                print(f"✅ {name}: {path} ({doc_dirs} document dirs)")
            elif name == "PERSIST_DIR":
                files = len(os.listdir(path)) if os.path.isdir(path) else 0
                print(f"✅ {name}: {path} ({files} files)")
        else:
            print(f"⚠️  {name}: {path} (will be created)")
    
    return issues


def check_config():
    """Check configuration module."""
    print("\n" + "="*60)
    print("4. Checking Configuration")
    print("="*60)
    
    try:
        from config import (
            LLM_PROVIDER,
            OPENAI_LLM_MODEL,
            GEMINI_LLM_MODEL,
            SIMILARITY_TOP_K,
            CHUNK_SIZE,
            CHUNK_OVERLAP,
            validate_config,
        )
        
        print(f"✅ LLM Provider: {LLM_PROVIDER}")
        
        if LLM_PROVIDER == "openai":
            print(f"✅ LLM Model: {OPENAI_LLM_MODEL}")
        else:
            print(f"✅ LLM Model: {GEMINI_LLM_MODEL}")
        
        print(f"✅ RAG Config: top_k={SIMILARITY_TOP_K}, chunk={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
        
        # Try validation
        try:
            validate_config()
            print(f"✅ Configuration valid")
            return []
        except ValueError as e:
            print(f"❌ Configuration invalid: {e}")
            return [str(e)]
            
    except Exception as e:
        print(f"❌ Config error: {e}")
        return [str(e)]


def check_ingestion_module():
    """Check ingestion module."""
    print("\n" + "="*60)
    print("5. Checking Ingestion Module")
    print("="*60)
    
    try:
        from ingestion import (
            add_document,
            delete_document,
            update_document,
            list_documents,
            get_document_info,
            get_index,
        )
        
        print(f"✅ Ingestion module imported")
        
        # Try to get index (will fail if not created yet)
        try:
            index = get_index()
            from ingestion.document_manager import get_document_count
            doc_count = get_document_count()
            print(f"✅ Index loaded: {doc_count} documents")
            return []
        except FileNotFoundError:
            print(f"⚠️  Index not found (run 'make parse' to create)")
            return ["Index not created"]
        except Exception as e:
            print(f"❌ Index error: {e}")
            return [str(e)]
            
    except Exception as e:
        print(f"❌ Ingestion module error: {e}")
        return [str(e)]


def check_api_module():
    """Check API module."""
    print("\n" + "="*60)
    print("6. Checking API Module")
    print("="*60)
    
    try:
        from api import app
        from api.models import QueryRequest, DocumentUploadResponse
        from api.routes import documents, query, images
        
        print(f"✅ API module imported")
        print(f"✅ FastAPI app created")
        print(f"✅ Pydantic models available")
        print(f"✅ All routes imported")
        
        # Check routes
        routes = [route.path for route in app.routes]
        expected = ["/documents", "/query", "/images", "/health"]
        
        for path in expected:
            matching = [r for r in routes if path in r]
            if matching:
                print(f"✅ Route: {path}")
            else:
                print(f"❌ Route missing: {path}")
        
        return []
        
    except Exception as e:
        print(f"❌ API module error: {e}")
        return [str(e)]


def check_streamlit_app():
    """Check Streamlit app."""
    print("\n" + "="*60)
    print("7. Checking Streamlit App")
    print("="*60)
    
    try:
        # Just check if file exists and can be read
        app_path = Path(__file__).parent.parent / "src" / "app.py"
        
        if app_path.exists():
            print(f"✅ Streamlit app exists: {app_path}")
            
            # Check if it imports correctly
            with open(app_path) as f:
                content = f.read()
                if "st.title" in content and "MultimodalQueryEngine" in content:
                    print(f"✅ Streamlit app structure valid")
                    return []
                else:
                    print(f"⚠️  Streamlit app may have issues")
                    return ["Streamlit app structure unclear"]
        else:
            print(f"❌ Streamlit app not found")
            return ["app.py missing"]
            
    except Exception as e:
        print(f"❌ Streamlit check error: {e}")
        return [str(e)]


def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("RAG-MAG Installation Verification")
    print("="*60)
    
    all_issues = []
    
    # Run checks
    all_issues.extend(check_environment())
    all_issues.extend(check_dependencies())
    all_issues.extend(check_directories())
    all_issues.extend(check_config())
    all_issues.extend(check_ingestion_module())
    all_issues.extend(check_api_module())
    all_issues.extend(check_streamlit_app())
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if not all_issues:
        print("\n✅ All checks passed!")
        print("\n🚀 Next steps:")
        print("   1. If index not created: make parse")
        print("   2. Start API: make api")
        print("   3. Or start Streamlit: make run")
        print("   4. Test API: python examples/api_usage.py")
        return 0
    else:
        print(f"\n⚠️  Found {len(all_issues)} issue(s):")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 How to fix:")
        
        if any("not configured" in issue for issue in all_issues):
            print("   - Copy env.example to .env and add your API keys")
        
        if any("not installed" in issue for issue in all_issues):
            print("   - Run: pip install -r requirements.txt")
        
        if any("Index not created" in issue for issue in all_issues):
            print("   - Run: make parse (to create initial index)")
        
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

