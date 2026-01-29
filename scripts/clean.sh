#!/bin/bash
# Utility script to clean various project artifacts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    echo "Usage: ./scripts/clean.sh [option]"
    echo ""
    echo "Options:"
    echo "  cache       Clean Python cache files and test artifacts"
    echo "  storage     Clean vector store (requires confirmation)"
    echo "  images      Clean extracted images (requires confirmation)"
    echo "  all         Clean everything (requires confirmation)"
    echo "  -h, --help  Show this help message"
    echo ""
}

clean_cache() {
    echo -e "${GREEN}Cleaning Python cache files...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    rm -rf htmlcov/
    rm -f .coverage
    echo -e "${GREEN}✅ Cache cleaned!${NC}"
}

clean_storage() {
    echo -e "${YELLOW}⚠️  WARNING: This will delete your vector index!${NC}"
    echo "You will need to run 'python3 parse.py' again to rebuild it."
    read -p "Are you sure? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf storage/*
        echo -e "${GREEN}✅ Storage cleared!${NC}"
    else
        echo -e "${RED}❌ Cancelled.${NC}"
    fi
}

clean_images() {
    echo -e "${YELLOW}⚠️  WARNING: This will delete extracted images!${NC}"
    echo "You will need to run 'python3 parse.py' again to rebuild them."
    read -p "Are you sure? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf data_images/*
        echo -e "${GREEN}✅ Images cleared!${NC}"
    else
        echo -e "${RED}❌ Cancelled.${NC}"
    fi
}

clean_all() {
    echo -e "${RED}⚠️  WARNING: This will delete ALL generated data!${NC}"
    echo "You will need to run 'python3 parse.py' again."
    read -p "Are you ABSOLUTELY sure? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        clean_cache
        rm -rf storage/*
        rm -rf data_images/*
        echo -e "${GREEN}✅ Everything cleaned!${NC}"
    else
        echo -e "${RED}❌ Cancelled.${NC}"
    fi
}

# Main script logic
case "$1" in
    cache)
        clean_cache
        ;;
    storage)
        clean_storage
        ;;
    images)
        clean_images
        ;;
    all)
        clean_all
        ;;
    -h|--help|"")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac

