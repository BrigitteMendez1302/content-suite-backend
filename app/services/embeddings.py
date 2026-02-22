from typing import List
from app.core.config import settings

# Local embeddings (recommended for quick MVP + no extra API key)
from sentence_transformers import SentenceTransformer

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)
    return _model

def embed_texts(texts: List[str]) -> List[List[float]]:
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True).tolist()
    return vectors