# app.py — Persistent Multimodal RAG Demo (Images-Only Source Display)

import os
from pathlib import Path
import streamlit as st
from llama_index.core import StorageContext, load_index_from_storage, Settings
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import MetadataMode
from llama_index.core.base.response.schema import Response
from llama_index.core.llms import ChatMessage, TextBlock, ImageBlock

# Import configuration and ingestion module
from config import (
    IMAGE_DIR,
    LLM_PROVIDER,
    SIMILARITY_TOP_K,
    validate_config,
    IMAGE_STORAGE_FORMAT,
)
from ingestion import get_index

# Validate configuration
validate_config()

# === CONFIGURATION ===
IMAGE_BASE_DIR = Path(IMAGE_DIR)

# === UI HEADER ===
st.title("🤖 RAG-MAG - Multimodal Document Assistant")
st.caption(f"Powered by Qdrant Cloud + {LLM_PROVIDER.upper()}")

# === Load Index from Qdrant ===
try:
    st.info(f"📦 Loading index from Qdrant Cloud...")
    index = get_index()
    st.success(f"✅ Connected! Using {LLM_PROVIDER.upper()} LLM")
except Exception as e:
    st.error(f"❌ Failed to load index: {e}")
    st.info("💡 Make sure you've run 'make parse' to index your documents")
    st.stop()

# === PROMPT BLOCKS ===
qa_prompt_block_text = """\
Below is the parsed content from the manual:
---------------------
{context_str}
---------------------
"""
image_prefix_block = TextBlock(text="Here are the corresponding images per page:\n")
image_suffix = """\
Given this content and without prior knowledge, answer the query:
{query_str}
"""


# === Custom Multimodal Query Engine ===
class MultimodalQueryEngine(CustomQueryEngine):
    retriever: BaseRetriever
    llm: object  # Can be OpenAI or Gemini

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _resolve_image_path(self, node) -> Path | str | None:
        """Resolve image from node metadata (supports base64 and file paths)."""
        # Check for base64 image first
        if "image_b64" in node.metadata:
            return node.metadata["image_b64"]  # Return base64 string
        
        # Fallback to file path
        img_path_str = node.metadata.get("image_path")
        if not img_path_str:
            return None
            
        img_path = Path(img_path_str).expanduser()
        if not img_path.exists():
            # Try recovering by filename search inside IMAGE_BASE_DIR
            filename = img_path.name
            possible_path = IMAGE_BASE_DIR / filename
            if possible_path.exists():
                return possible_path
            else:
                print(f"⚠️ Could not find image: {filename}")
                return None
        return img_path

    def custom_query(self, query_str: str):
        nodes = self.retriever.retrieve(query_str)

        # Collect valid image blocks
        image_blocks = []
        for n in nodes:
            resolved = self._resolve_image_path(n)
            if resolved:
                if isinstance(resolved, str) and resolved.startswith("data:image"):
                    # Base64 image
                    image_blocks.append(ImageBlock(url=resolved))
                else:
                    # File path
                    image_blocks.append(ImageBlock(path=str(resolved)))

        context_str = "\n\n".join(
            [r.get_content(metadata_mode=MetadataMode.LLM) for r in nodes]
        )

        formatted_msg = ChatMessage(
            role="user",
            blocks=[
                TextBlock(text=qa_prompt_block_text.format(context_str=context_str)),
                image_prefix_block,
                *image_blocks,
                TextBlock(text=image_suffix.format(query_str=query_str)),
            ],
        )

        llm_response = self.llm.chat([formatted_msg])
        return Response(
            response=str(llm_response.message.content),
            source_nodes=nodes,
        )


# === Initialize Query Engine ===
llm = Settings.llm
query_engine = MultimodalQueryEngine(
    retriever=index.as_retriever(similarity_top_k=SIMILARITY_TOP_K),
    llm=llm,
)

# === Streamlit Query Interface ===
st.subheader("💬 Ask your question")
query = st.text_input("Your question:", placeholder="e.g. How to connect antenna")

if st.button("Ask"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            try:
                response = query_engine.query(query)
                st.markdown("### 🧠 Answer")
                st.write(response.response)

                # === Source display — show IMAGES ONLY ===
                st.markdown("### 📸 Source Images")
                for i, node in enumerate(response.source_nodes):
                    resolved = query_engine._resolve_image_path(node.node)
                    page_num = node.node.metadata.get("page_num", "?")
                    
                    if resolved:
                        if isinstance(resolved, str) and resolved.startswith("data:image"):
                            # Base64 image from Qdrant
                            with st.expander(f"📄 Source {i+1} — Page {page_num}"):
                                st.markdown(f'<img src="{resolved}" style="width:100%"/>', unsafe_allow_html=True)
                        elif hasattr(resolved, 'exists') and resolved.exists():
                            # File path
                            with st.expander(f"📄 Source {i+1} — Page {page_num}"):
                                st.image(str(resolved), use_container_width=True)
                        else:
                            with st.expander(f"📄 Source {i+1}"):
                                st.warning(f"⚠️ Image not found")
                    else:
                        with st.expander(f"📄 Source {i+1}"):
                            st.warning(f"⚠️ Image not available")

            except Exception as e:
                st.error(f"❌ Error: {e}")

# === FOOTER ===
provider_display = "OpenAI" if LLM_PROVIDER == "openai" else "Google Gemini"
st.markdown(
    f"<br><center>Built with ❤️ using LlamaParse + {provider_display} + Streamlit</center>",
    unsafe_allow_html=True,
)
