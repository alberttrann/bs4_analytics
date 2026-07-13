"""
pipeline/advanced/nlp_analyzer.py
Owner: Hung (A)
Advanced — TF-IDF keyword ranking, Flesch-Kincaid readability per section,
           spaCy NER to extract class/function names.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def compute_tfidf_keywords(sections: pd.DataFrame, top_n: int = 20) -> list[dict]:
    """
    Rank keywords across the full corpus using TF-IDF weighting.
    More precise than raw frequency (Q5) because it downweights terms that
    appear in every section (e.g. "soup", "tag").

    Returns list of {"keyword": str, "count": float} sorted descending.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = sections["section_text"].fillna("").tolist()
    vec   = TfidfVectorizer(stop_words="english", max_features=500)
    X     = vec.fit_transform(texts)
    scores = X.toarray().sum(axis=0)
    terms  = vec.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x: -x[1])[:top_n]
    return [{"keyword": k, "count": round(float(v), 4)} for k, v in ranked]


def compute_readability(sections: pd.DataFrame) -> pd.Series:
    """
    Compute Flesch Reading Ease score per section.
    Scale: 0 (very hard) to 100 (very easy).
    Returns a Series aligned with sections.index.
    """
    import textstat
    return sections["section_text"].fillna("").apply(textstat.flesch_reading_ease)


def extract_entities(sections: pd.DataFrame) -> pd.DataFrame:
    """
    Run spaCy NER over each section to extract Python class/function names.
    Requires: python -m spacy download en_core_web_sm

    Returns DataFrame with columns: section_title, entity_text, entity_label.
    """
    import spacy
    nlp  = spacy.load("en_core_web_sm")
    rows = []
    for _, row in sections.iterrows():
        doc = nlp(row["section_text"][:50_000])   # spaCy token limit guard
        for ent in doc.ents:
            rows.append({
                "section_title": row["section_title"],
                "entity_text":   ent.text,
                "entity_label":  ent.label_,
            })
    return pd.DataFrame(rows)
