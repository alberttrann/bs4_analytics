"""
pipeline/code_extractor.py
Owner: Hung (A)
Feature 5 - Code Example Extractor

Finds every <div class="highlight"> block in the parsed soup, extracts
code text, counts non-empty lines, locates the parent section, and sets
boolean flags for five key BS4 / requests method signatures.
Writes data/processed/code_examples.csv.
"""

from __future__ import annotations

import logging

import pandas as pd
from bs4 import BeautifulSoup, Tag

from shared.constants import CODE_COLS, CODE_EXAMPLES_CSV
from shared.utils import ensure_dirs, save_csv

logger = logging.getLogger(__name__)

# Maps CSV column name → substring to search for in code text
_METHOD_FLAGS: dict[str, str] = {
    "contains_find_all": "find_all",
    "contains_find":     ".find(",
    "contains_select":   ".select(",
    "contains_get_text": "get_text",
    "contains_requests": "requests",
}


def extract_code_examples(soup: BeautifulSoup) -> pd.DataFrame:
    """
    Extract all Python code blocks from the parsed documentation.

    Parameters
    ----------
    soup : BeautifulSoup
        Parsed document returned by pipeline.parser.parse_html().

    Returns
    -------
    pd.DataFrame
        One row per code block, columns matching CODE_COLS.
        Also writes code_examples.csv to disk.
    """
    blocks = soup.find_all("div", class_="highlight")
    rows: list[dict] = []

    for i, block in enumerate(blocks):
        code_text = block.get_text()
        rows.append({
            "example_id":    i,
            "section_title": _find_parent_section(block),
            "code_text":     code_text,
            "line_count":    _count_lines(code_text),
            **_detect_methods(code_text),
        })

    df = pd.DataFrame(rows, columns=CODE_COLS)
    ensure_dirs()
    save_csv(df, CODE_EXAMPLES_CSV, expected_cols=CODE_COLS)
    logger.info("Extracted %d code examples → %s", len(df), CODE_EXAMPLES_CSV.name)
    return df


# Helpers

def _find_parent_section(tag) -> str:
    """Find the nearest preceding heading in document order."""
    for heading in tag.find_all_previous(["h1", "h2", "h3"]):
        title = heading.get_text(strip=True).replace("¶", "").strip()
        if title:
            return title
    return "Unknown"


def _count_lines(code_text: str) -> int:
    """Return number of non-empty lines in a code block."""
    return len([line for line in code_text.splitlines() if line.strip()])


def _detect_methods(code_text: str) -> dict[str, bool]:
    """Return boolean flags indicating which key methods appear in the code."""
    return {col: marker in code_text for col, marker in _METHOD_FLAGS.items()}


# CLI entry point

if __name__ == "__main__":
    import logging
    from pipeline.parser import parse_html

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    soup = parse_html()
    df = extract_code_examples(soup)
    print(f"\nExtracted {len(df)} code examples")
    print(f"find_all() usage : {df['contains_find_all'].sum()}")
    print(f"get_text() usage : {df['contains_get_text'].sum()}")
    print(df[["section_title", "line_count"]].head(10).to_string(index=False))
