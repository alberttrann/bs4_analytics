"""
api/services/data_service.py
Owner: Dat (B)
Task : Shared CSV→DataFrame cache; all route files import load_*() from here
"""

from __future__ import annotations

import pandas as pd

from shared.utils import load_code_examples as _load_code_examples_csv
from shared.utils import load_links as _load_links_csv
from shared.utils import load_sections as _load_sections_csv

_cache: dict[str, pd.DataFrame] = {}


def _cached(key: str, loader) -> pd.DataFrame:
    if key not in _cache:
        _cache[key] = loader()
    return _cache[key]


def load_sections() -> pd.DataFrame:
    """Return sections.csv as a cached DataFrame."""
    return _cached("sections", _load_sections_csv)


def load_links() -> pd.DataFrame:
    """Return links.csv as a cached DataFrame."""
    return _cached("links", _load_links_csv)


def load_code_examples() -> pd.DataFrame:
    """Return code_examples.csv as a cached DataFrame."""
    return _cached("code_examples", _load_code_examples_csv)


def invalidate_cache() -> None:
    """Clear all cached DataFrames (e.g. after pipeline re-run)."""
    _cache.clear()
