"""Query endpoint for RAG system."""

import time
from typing import List
from fastapi import APIRouter, HTTPException
from llama_index.core import Settings
from llama_index.core.schema import MetadataMode
from llama_index.core.llms import ChatMessage, TextBlock, ImageBlock

from ingestion import get_index
from ..models import QueryRequest, QueryResponse, SourceNode
from ..dependencies import resolve_image_path

router = APIRouter(prefix="/query", tags=["query"])


def build_multimodal_prompt(query: str, nodes: List, include_images: bool = True) -> ChatMessage:
    """Build a multimodal prompt with text and images.
    
    Args:
        query: User query string
        nodes: Retrieved nodes from the index
        include_images: Whether to include images in the prompt
        
    Returns:
        ChatMessage with text and image blocks
    """
    # Collect context text
    context_str = "\n\n".join(
        [node.get_content(metadata_mode=MetadataMode.LLM) for node in nodes]
    )
    
    # Build prompt blocks
    blocks = [
        TextBlock(text=f"Below is the parsed content from the manual:\n---------------------\n{context_str}\n---------------------\n")
    ]
    
    # Add images if requested
    if include_images:
        blocks.append(TextBlock(text="Here are the corresponding images per page:\n"))
        
        for node in nodes:
            img_path_str = node.metadata.get("image_path")
            if img_path_str:
                try:
                    resolved_path = resolve_image_path(img_path_str)
                    blocks.append(ImageBlock(path=str(resolved_path)))
                except FileNotFoundError:
                    # Skip missing images
                    continue
    
    # Add query
    blocks.append(
        TextBlock(text=f"Given this content and without prior knowledge, answer the query:\n{query}")
    )
    
    return ChatMessage(role="user", blocks=blocks)


@router.post(
    "",
    response_model=QueryResponse,
    summary="Query the RAG system",
    description="Send a query and get an answer with source references."
)
async def query_documents(request: QueryRequest):
    """Query the document index and get an answer."""
    start_time = time.time()
    
    try:
        # Get index and retriever
        index = get_index()
        
        # Determine top_k
        similarity_top_k = request.similarity_top_k or 3
        retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        
        # Retrieve relevant nodes
        nodes = retriever.retrieve(request.query)
        
        if not nodes:
            raise HTTPException(
                status_code=404,
                detail="No relevant documents found for the query"
            )
        
        # Build multimodal prompt
        prompt = build_multimodal_prompt(
            request.query,
            nodes,
            include_images=request.include_images
        )
        
        # Get LLM response
        llm = Settings.llm
        llm_response = llm.chat([prompt])
        answer = str(llm_response.message.content)
        
        # Build source nodes for response
        source_nodes = []
        for node in nodes:
            source_nodes.append(
                SourceNode(
                    page_number=node.metadata.get("page_number"),
                    filename=node.metadata.get("filename"),
                    image_path=node.metadata.get("image_path"),
                    text_preview=node.get_content()[:200] + "..." if len(node.get_content()) > 200 else node.get_content(),
                    score=node.score if hasattr(node, 'score') else None
                )
            )
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            query=request.query,
            answer=answer,
            source_nodes=source_nodes,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )

