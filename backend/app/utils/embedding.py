from typing import List

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    model = None

    @classmethod
    def load(cls):
        import os
        model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh")
        if cls.model is None:
            cls.model = SentenceTransformer(model_name)

    @classmethod
    def encode(cls, texts: List[str]) -> List[List[float]]:
        cls.load()
        return cls.model.encode(texts, normalize_embeddings=True).tolist()

    @classmethod
    def similarity(cls, a: List[float], b: List[float]) -> float:
        import numpy as np
        return float(np.dot(a, b))
