"""
shared/utils.py
===============
Common utility functions imported by all pipeline stages, API routes,
and Streamlit pages. 

Ownership: Hung 
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from shared.constants import (
    ALL_DIRS,
    CODE_COLS,
    CODE_EXAMPLES_CSV,
    LINK_COLS,
    LINKS_CSV,
    SECTION_COLS,
    SECTIONS_CSV,
    SUMMARY_STATS_JSON,
)

logger = logging.getLogger(__name__)


# Directory management

def ensure_dirs() -> None:
    """
    Create all required data and output directories if they don't exist.
    Safe to call multiple times (idempotent).
    Call this at the start of any pipeline stage that writes files.
    """
    for directory in ALL_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
    logger.debug("All required directories verified/created.")


# CSV loaders

def load_csv(path: Path, expected_cols: list[str] | None = None) -> pd.DataFrame:
    """
    Load a processed CSV from disk with schema validation.

    Parameters
    ----------
    path : Path
        Absolute path to the CSV file.
    expected_cols : list[str] | None
        If provided, raises ValueError when the CSV is missing any expected column.

    Raises
    ------
    FileNotFoundError
        When the file doesn't exist — includes a human-friendly message
        telling the developer to run the pipeline first.
    ValueError
        When the CSV is missing expected columns.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"[Pipeline not yet run] Missing file: {path}\n"
            "Run `python -m pipeline.pipeline` to generate all data files."
        )

    df = pd.read_csv(path)

    if expected_cols:
        missing = set(expected_cols) - set(df.columns)
        if missing:
            raise ValueError(
                f"CSV at {path} is missing expected columns: {missing}\n"
                "The pipeline may be using an outdated schema. "
                "Re-run the full pipeline to regenerate."
            )

    logger.debug("Loaded %d rows from %s", len(df), path.name)
    return df


def load_sections() -> pd.DataFrame:
    """Load sections.csv with column validation."""
    return load_csv(SECTIONS_CSV, expected_cols=SECTION_COLS)


def load_links() -> pd.DataFrame:
    """Load links.csv with column validation."""
    return load_csv(LINKS_CSV, expected_cols=LINK_COLS)


def load_code_examples() -> pd.DataFrame:
    """Load code_examples.csv with column validation."""
    return load_csv(CODE_EXAMPLES_CSV, expected_cols=CODE_COLS)


def load_summary_stats() -> dict[str, Any]:
    """
    Load summary_stats.json produced by analyzer.py.

    Returns
    -------
    dict
        The full analytics result dictionary.

    Raises
    ------
    FileNotFoundError
        If the pipeline has not been run yet.
    """
    if not SUMMARY_STATS_JSON.exists():
        raise FileNotFoundError(
            f"[Pipeline not yet run] Missing file: {SUMMARY_STATS_JSON}\n"
            "Run `python -m pipeline.pipeline` to generate analytics."
        )
    with open(SUMMARY_STATS_JSON, encoding="utf-8") as f:
        return json.load(f)


# CSV writers

def save_csv(df: pd.DataFrame, path: Path, expected_cols: list[str] | None = None) -> None:
    """
    Validate columns then write a DataFrame to CSV (UTF-8, no index).

    Parameters
    ----------
    df : pd.DataFrame
    path : Path
        Destination path. Parent directory must already exist.
    expected_cols : list[str] | None
        When provided, raises ValueError if df is missing any expected column.
    """
    if expected_cols:
        missing = set(expected_cols) - set(df.columns)
        if missing:
            raise ValueError(
                f"DataFrame is missing columns before save: {missing}\n"
                f"Expected: {expected_cols}\n"
                f"Got:      {list(df.columns)}"
            )

    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("Saved %d rows → %s", len(df), path.name)


# Pipeline state helpers

def pipeline_has_run() -> bool:
    """Return True if all three processed CSVs exist on disk."""
    return SECTIONS_CSV.exists() and LINKS_CSV.exists() and CODE_EXAMPLES_CSV.exists()


def data_files_status() -> dict[str, bool]:
    """
    Return a dict mapping each expected output file name to whether it exists.
    Used by GET /health and the Streamlit home page dashboard.
    """
    files = {
        "sections.csv":       SECTIONS_CSV,
        "links.csv":          LINKS_CSV,
        "code_examples.csv":  CODE_EXAMPLES_CSV,
        "summary_stats.json": SUMMARY_STATS_JSON,
    }
    return {name: path.exists() for name, path in files.items()}


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


# Text helpers

def word_count(text: str) -> int:
    """Return the number of whitespace-delimited tokens in a string."""
    return len(text.split()) if text and text.strip() else 0


def truncate(text: str, max_chars: int = 200, suffix: str = "…") -> str:
    """Truncate a string to max_chars, appending suffix if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + suffix
