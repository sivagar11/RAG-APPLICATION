Topic: "How to set ref_doc_id or document tracking on TextNode objects" Specific questions: - Can TextNodes have a `ref_doc_id` attribute? - Do we need to wrap TextNodes in Document objects? - What's the proper way to associate nodes with a document ID for tracking?



    TextNodes do not have a settable ref_doc_id attribute directly. The ref_doc_id is a derived property, not a constructor argument, and is set via node relationships—specifically, by assigning a source_node relationship to the node, which points to the parent document or node. Attempting to set ref_doc_id as a constructor kwarg will be ignored or discarded (cf291d60, f80128cb).

    You do not need to wrap TextNodes in Document objects for tracking, but you must set the source relationship. The standard way to associate a node with a document ID is to set the NodeRelationship.SOURCE relationship on the node, pointing to a RelatedNodeInfo with the document's node ID. This ensures the node's ref_doc_id property will return the correct document ID, enabling document-level tracking and deletion (cf291d60, ab4e04e8, d8c7158c, 52e110b0).


Here’s how to properly associate a TextNode with a document ID for tracking in LlamaIndex:

    Create your TextNode(s) as usual, without trying to set ref_doc_id directly.
    Set the source relationship on each node, using NodeRelationship.SOURCE and a RelatedNodeInfo that points to the document’s node ID.

Example:

python

from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo

# Suppose your document ID is "doc123"
doc_id = "doc123"
node = TextNode(text="example text", id_="node456")

# Set the SOURCE relationship to the document
node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc_id)

Now, node.ref_doc_id will return "doc123", and document-level operations (like deletion or tracking) will work as expected. You do not need to wrap the node in a Document object, but you must ensure the SOURCE relationship is set (cf291d60, ab4e04e8).

Topic: "VectorStoreIndex.insert_nodes() API and document tracking" Specific questions: - Does insert_nodes() support document tracking via ref_doc_id? - Can we later delete nodes added via insert_nodes() using delete_ref_doc()? - What's the relationship between nodes and documents in the index?

ex

    insert_nodes() only supports document tracking via ref_doc_id if each node’s NodeRelationship.SOURCE is set to the document’s node ID. If you create nodes without this relationship, they will not be associated with a document and cannot be tracked or deleted as a group (cf291d60, ab4e04e8).

    You can use delete_ref_doc() to delete nodes added via insert_nodes() only if those nodes have their SOURCE relationship set to the same document ID. Otherwise, delete_ref_doc() will not find or remove them as a group (cf291d60, 37500f41).

    The relationship is: a document is split into nodes, and each node should have a SOURCE relationship pointing to the document’s node ID. This enables document-level tracking, retrieval, and deletion. If nodes are inserted without this relationship, they are treated as independent and not grouped under any document (52e110b0, cf291d60).

Here’s a code example showing how to use VectorStoreIndex.insert_nodes() with document tracking, so you can later use delete_ref_doc() for group deletion:

python

from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.core import VectorStoreIndex

# Suppose your document ID is "doc123"
doc_id = "doc123"
# Create nodes and set the SOURCE relationship for document tracking
nodes = [
    TextNode(text="chunk 1", id_="node1"),
    TextNode(text="chunk 2", id_="node2"),
]
for node in nodes:
    node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=doc_id)

# Insert nodes into the index
index = VectorStoreIndex(nodes=[])  # or your existing index
index.insert_nodes(nodes)

# Later, delete all nodes associated with the document
index.delete_ref_doc(doc_id)

This ensures all nodes are tracked under doc123 and can be deleted as a group using delete_ref_doc() (cf291d60, ab4e04e8, 52e110b0).

Topic: "VectorStoreIndex with JSON persistence - docstore support" Specific questions: - Does the default JSON-based VectorStoreIndex support delete_ref_doc()? - Is there a list of which storage backends support docstore operations? - Any limitations on deletion with JSON storage?

maIndex

    Yes, the default JSON-based VectorStoreIndex (using the built-in SimpleVectorStore and SimpleDocumentStore) supports delete_ref_doc(), allowing you to delete a document and its associated nodes by ref_doc_id (c81ebef8, 60f9ba26).

    There is no single canonical list in the docs, but the Vector Store Options & Feature Support table shows which vector stores support "Store Documents" and "Delete" operations. For JSON-based (Simple) storage, both are supported.

    Limitations: With JSON storage, deletion is reliable as long as you use the default stores and persist changes. However, if you use a third-party vector store that stores text internally (e.g., Chroma, Qdrant, etc.) and do not set store_nodes_override=True, the docstore may not be used, and delete_ref_doc() may not work as expected (707474cc, c81ebef8).

Topic: "When to call persist() after insert/delete/update operations" Specific questions: - Does insert()/delete() auto-persist or do we need manual persist()? - Is persist() atomic? Thread-safe? - Best practices for persistence in an API context



    insert(), delete(), and similar operations do not auto-persist; you must call persist() manually to save changes to disk or your storage backend (d55bbcab, 8d5d83c1).

    persist() is not guaranteed to be atomic or thread-safe. For in-memory stores, concurrent writes may cause data corruption, and atomicity is not documented. For remote/vector DB backends, atomicity and thread safety depend on the backend’s implementation (8ea485e2, d55bbcab).

    Best practices: In an API context, call persist() after a batch of changes or at transaction boundaries, not after every single insert/delete for performance. Use async/concurrency patterns (not threads) for safety, and avoid concurrent writes to the same in-memory index. For production, consider a remote/vector DB backend with built-in durability and concurrency controls (d55bbcab, 8ea485e2).

Topic: "Reloading index after external modifications" Specific questions: - Can multiple processes share the same index safely? - How to reload index to see new changes? - Best practices for API + query app architecture



    Multiple processes cannot safely share the same in-memory index; concurrent writes or reads may cause data corruption or inconsistent state. For safe multi-process or multi-threaded access, use an external vector store or database backend (e.g., Qdrant, Chroma, Redis, Elasticsearch) that handles concurrency (c33d19fc, c3732080).

    To reload an index and see new changes, re-instantiate the StorageContext with the latest persisted data (e.g., from disk or remote backend), then call load_index_from_storage(storage_context). This ensures your process sees updates made by others (a267a25c, 48174c89).

    Best practices: For API/query apps, use a remote or persistent backend for storage, reload the index context on each request or at regular intervals, and avoid sharing in-memory objects between processes. For high concurrency, prefer async APIs and stateless app design (c33d19fc, a267a25c).


Topic: "TextNode metadata structure and persistence" Specific question: - Is metadata automatically persisted with nodes? - Can we add arbitrary keys to node.metadata? 



    Yes, metadata is automatically persisted with nodes when you save or persist the index; any key-value pairs in node.metadata are stored and reloaded with the node (c14a0f11, c2862369).

    You can add arbitrary keys to node.metadata as long as the values are serializable (e.g., str, int, float, or flat types for most vector stores). This allows you to store custom annotations or attributes for each node (c2862369, 4b8a0e82).


