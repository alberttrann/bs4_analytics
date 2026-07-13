"""
pipeline/advanced/similarity.py
Owner: Hung (A)
Advanced — cosine similarity matrix between documentation sections.
Used to populate the heatmap in app/pages/4_analytics.py.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_similarity_matrix(sections: pd.DataFrame) -> np.ndarray:
    """
    Build an (n x n) cosine similarity matrix over section texts.

    Returns
    -------
    np.ndarray  shape (n_sections, n_sections)
        Entry [i, j] is cosine similarity between section i and section j.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    texts  = sections["section_text"].fillna("").tolist()
    vec    = TfidfVectorizer(stop_words="english")
    X      = vec.fit_transform(texts)
    matrix = cosine_similarity(X)
    logger.info("Computed %dx%d similarity matrix", *matrix.shape)
    return matrix


def top_similar_pairs(
    sections: pd.DataFrame,
    matrix: np.ndarray | None = None,
    top_n: int = 10,
) -> list[tuple[str, str, float]]:
    """
    Return the top-N most similar section pairs (self-similarity excluded).

    Returns
    -------
    list[tuple[str, str, float]]
        Each tuple: (title_a, title_b, similarity_score), sorted descending.
    """
    if matrix is None:
        matrix = compute_similarity_matrix(sections)

    titles = sections["section_title"].tolist()
    pairs  = []
    n      = len(titles)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append((titles[i], titles[j], float(matrix[i, j])))

    return sorted(pairs, key=lambda x: -x[2])[:top_n]
