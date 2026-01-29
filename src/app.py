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

# Import configuration
from config import (
    PERSIST_DIR,
    IMAGE_DIR,
    LLM_PROVIDER,
    SIMILARITY_TOP_K,
    validate_config,
    get_llm_config,
)

# Validate configuration
validate_config()

# === CONFIGURATION ===
IMAGE_BASE_DIR = Path(IMAGE_DIR)

# === UI HEADER ===
st.title("🤖 Engineering Manual Assistant (Persistent RAG)")
# st.caption("Ask questions about the VPOS Touch Installation Guide")

# === Load Saved Index ===
if os.path.exists(PERSIST_DIR):
    st.info(f"📦 Found existing vector index — loading with {LLM_PROVIDER.upper()}...")
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)
    
    # Set up LLM + embedding model based on provider
    llm_config = get_llm_config()
    
    if LLM_PROVIDER == "openai":
        from llama_index.embeddings.openai import OpenAIEmbedding
        from llama_index.llms.openai import OpenAI
        
        Settings.embed_model = OpenAIEmbedding(
            model=llm_config["embedding_model"], 
            api_key=llm_config["embedding_api_key"]
        )
        Settings.llm = OpenAI(
            model=llm_config["llm_model"], 
            api_key=llm_config["llm_api_key"]
        )
    elif LLM_PROVIDER == "gemini":
        from llama_index.llms.google_genai import GoogleGenAI
        from llama_index.embeddings.openai import OpenAIEmbedding
        
        # Using Gemini for LLM, OpenAI for embeddings (hybrid approach)
        Settings.embed_model = OpenAIEmbedding(
            model=llm_config["embedding_model"], 
            api_key=llm_config["embedding_api_key"]
        )
        Settings.llm = GoogleGenAI(
            model=llm_config["llm_model"], 
            api_key=llm_config["llm_api_key"]
        )
    else:
        st.error(f"❌ Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'openai' or 'gemini'")
        st.stop()
else:
    st.error("❌ No saved index found! Run parse.py first.")
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

    def _resolve_image_path(self, img_path_str: str) -> Path | None:
        """Resolve stored metadata image path to actual existing file."""
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
            img_path_str = n.metadata.get("image_path")
            if img_path_str:
                resolved_path = self._resolve_image_path(img_path_str)
                if resolved_path:
                    image_blocks.append(ImageBlock(path=str(resolved_path)))

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
                    img_path_str = node.node.metadata.get("image_path")
                    if not img_path_str:
                        continue

                    resolved_path = query_engine._resolve_image_path(img_path_str)
                    if resolved_path and resolved_path.exists():
                        with st.expander(f"Source {i+1} — {resolved_path.name}"):
                            st.image(
                                str(resolved_path),
                                caption=f"Extracted diagram ({resolved_path.name})",
                                use_container_width=True,
                            )
                    else:
                        with st.expander(f"Source {i+1}"):
                            st.warning(f"⚠️ Image not found: {img_path_str}")

            except Exception as e:
                st.error(f"❌ Error: {e}")

# === FOOTER ===
provider_display = "OpenAI" if LLM_PROVIDER == "openai" else "Google Gemini"
st.markdown(
    f"<br><center>Built with ❤️ using LlamaParse + {provider_display} + Streamlit</center>",
    unsafe_allow_html=True,
)
