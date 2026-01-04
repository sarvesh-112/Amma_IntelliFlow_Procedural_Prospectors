import numpy as np
from sentence_transformers import SentenceTransformer
from rag.embed import get_faiss_index, get_documents

# Use the SAME model name to ensure embedding compatibility
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def _load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def retrieve_context(query, k=2):
    """
    Retrieve top-k relevant document chunks for a query.
    Intent-aware via tagged embeddings.
    """
    index = get_faiss_index()
    documents = get_documents()

    if index.ntotal == 0:
        return "No indexed report context available."

    model = _load_model()

    # IMPORTANT: DO NOT index the query (no embed_texts here)
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")

    _, indices = index.search(query_embedding, k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(documents):
            results.append(documents[idx])

    # Combine retrieved context
    return "\n".join(results)
