"""
api/services/data_service.py
Shared CSV→DataFrame cache. All route files import load_*() from here.
Never reads CSVs directly - delegates to shared.utils loaders.
"""

from __future__ import annotations

import logging

import pandas as pd

from shared.utils import (
    load_code_examples as _load_code,
    load_links as _load_links,
    load_sections as _load_sections,
    load_summary_stats as _load_summary,
)

logger = logging.getLogger(__name__)

_cache: dict = {}


def _get(key: str, loader):
    if key not in _cache:
        logger.debug("Cache miss '%s' - loading from disk", key)
        _cache[key] = loader()
    return _cache[key]


def load_sections() -> pd.DataFrame:
    return _get("sections", _load_sections)


def load_links() -> pd.DataFrame:
    return _get("links", _load_links)


def load_code_examples() -> pd.DataFrame:
    return _get("code", _load_code)


def load_summary() -> dict:
    return _get("summary", _load_summary)


def invalidate_cache() -> None:
    """Clear all cached DataFrames. Called after a pipeline re-run."""
    _cache.clear()
    logger.info("Data cache invalidated")
