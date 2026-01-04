from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# -------------------- GLOBALS (LAZY INIT) --------------------

_model = None
_index = None
_documents = []

EMBEDDING_DIM = 384
MODEL_NAME = "all-MiniLM-L6-v2"


# -------------------- LOADERS --------------------

def _load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _load_index():
    global _index
    if _index is None:
        _index = faiss.IndexFlatL2(EMBEDDING_DIM)
    return _index


# -------------------- CORE API --------------------

def embed_texts(texts, tag: str = "GENERAL"):
    """
    Embed text(s) with semantic tags and store in FAISS.

    Args:
        texts (str | list[str])
        tag (str): AUTH, SETTLEMENT, PERFORMANCE, etc.

    Returns:
        np.ndarray: embeddings
    """
    if isinstance(texts, str):
        texts = [texts]

    # Tag texts for intent-aware retrieval
    tagged_texts = [f"[{tag}] {t}" for t in texts]

    model = _load_model()
    index = _load_index()

    embeddings = model.encode(tagged_texts)
    embeddings = np.array(embeddings).astype("float32")

    index.add(embeddings)
    _documents.extend(tagged_texts)

    return embeddings


# -------------------- ACCESSORS --------------------

def get_faiss_index():
    return _load_index()


def get_documents():
    return _documents
