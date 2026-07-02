from __future__ import annotations

from functools import cached_property

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.logger import get_logger


class TransformerService:
    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    @cached_property
    def feature_extractor(self):  # type: ignore[no-untyped-def]
        try:
            from transformers import pipeline

            return pipeline("feature-extraction", model="sentence-transformers/all-MiniLM-L6-v2")
        except Exception as exc:
            self.logger.warning("Transformer feature extraction unavailable. Using TF-IDF fallback: %s", exc)
            return None

    def semantic_similarity(self, resume_text: str, job_description: str) -> float:
        if self.feature_extractor is None:
            return self._tfidf_similarity(resume_text, job_description)

        try:
            embeddings = self.feature_extractor([resume_text[:4000], job_description[:4000]], truncation=True)
            vectors = [self._pool_embedding(item) for item in embeddings]
            score = cosine_similarity([vectors[0]], [vectors[1]])[0][0]
            return float(max(0.0, min(1.0, score)))
        except Exception as exc:
            self.logger.warning("Transformer similarity failed. Using TF-IDF fallback: %s", exc)
            return self._tfidf_similarity(resume_text, job_description)

    def _pool_embedding(self, embedding: list[list[float]] | list[list[list[float]]]) -> np.ndarray:
        array = np.array(embedding, dtype=float)
        if array.ndim == 3:
            array = array[0]
        return array.mean(axis=0)

    def _tfidf_similarity(self, resume_text: str, job_description: str) -> float:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        matrix = vectorizer.fit_transform([resume_text, job_description])
        score = cosine_similarity(matrix[0], matrix[1])[0][0]
        return float(max(0.0, min(1.0, score)))
