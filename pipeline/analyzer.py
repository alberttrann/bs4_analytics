"""
pipeline/analyzer.py
Feature 6 - Documentation Analytics
10 questions using Pandas/NumPy → summary_stats.json
"""

from __future__ import annotations

import json
import logging
import re
from collections import Counter

import numpy as np
import pandas as pd

from shared.constants import STOPWORDS, SUMMARY_STATS_JSON
from shared.utils import load_code_examples, load_links, load_sections

logger = logging.getLogger(__name__)


# Main entry point

def run_all_analytics(
    sections: pd.DataFrame | None = None,
    links:    pd.DataFrame | None = None,
    code:     pd.DataFrame | None = None,
) -> dict:
    """
    Execute all 10 analytics questions.
    Loads DataFrames from disk if not provided.
    Saves results to summary_stats.json and returns the dict.
    """
    sections = sections if sections is not None else load_sections()
    links    = links    if links    is not None else load_links()
    code     = code     if code     is not None else load_code_examples()

    # Ensure boolean columns are parsed correctly
    bool_cols = ["contains_find_all", "contains_find", "contains_select",
                 "contains_get_text", "contains_requests"]
    for col in bool_cols:
        if col in code.columns:
            code[col] = code[col].astype(bool)

    result = {
        # Q1 - How many sections are in the documentation?
        "total_sections": int(len(sections)),

        # Q2 - Which section has the highest word count?
        "highest_wordcount_section": str(
            sections.loc[sections["word_count"].idxmax(), "section_title"]
        ),
        "highest_wordcount_value": int(sections["word_count"].max()),

        # Q3 - Which section contains the most code examples?
        "most_code_examples_section": str(
            code.groupby("section_title").size().idxmax()
        ),
        "most_code_examples_count": int(
            code.groupby("section_title").size().max()
        ),

        # Q4 - Which section contains the most links?
        "most_links_section": str(
            links.groupby("section_title").size().idxmax()
        ),
        "most_links_count": int(
            links.groupby("section_title").size().max()
        ),

        # Q5 - Top 10 most frequent technical keywords
        "top_10_keywords": _top_keywords(sections, n=10),

        # Q6 - Internal vs external link counts
        "link_type_counts": {
            str(k): int(v)
            for k, v in links["link_type"].value_counts().items()
        },

        # Q7 - How many code examples use find_all()?
        "find_all_example_count": int(code["contains_find_all"].sum()),

        # Q8 - How many code examples use get_text()?
        "get_text_example_count": int(code["contains_get_text"].sum()),

        # Q9 (team-proposed) - Average words per section
        "avg_words_per_section": round(float(sections["word_count"].mean()), 2),

        # Q10 (team-proposed) - Sections with zero code blocks
        "sections_with_no_code": int((sections["code_block_count"] == 0).sum()),
    }

    # Save JSON
    SUMMARY_STATS_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Analytics complete → %s", SUMMARY_STATS_JSON.name)

    # Print summary to stdout
    print(f"[analyzer] Q1  Total sections          : {result['total_sections']}")
    print(f"[analyzer] Q2  Highest word count       : {result['highest_wordcount_section'][:50]} ({result['highest_wordcount_value']} words)")
    print(f"[analyzer] Q3  Most code examples       : {result['most_code_examples_section'][:50]} ({result['most_code_examples_count']})")
    print(f"[analyzer] Q4  Most links               : {result['most_links_section'][:50]} ({result['most_links_count']})")
    print(f"[analyzer] Q5  Top keywords             : {', '.join(k['keyword'] for k in result['top_10_keywords'][:5])}...")
    print(f"[analyzer] Q6  Link types               : {result['link_type_counts']}")
    print(f"[analyzer] Q7  find_all() examples      : {result['find_all_example_count']}")
    print(f"[analyzer] Q8  get_text() examples      : {result['get_text_example_count']}")
    print(f"[analyzer] Q9  Avg words/section        : {result['avg_words_per_section']}")
    print(f"[analyzer] Q10 Sections with no code    : {result['sections_with_no_code']}")

    return result


# Helpers

def _top_keywords(sections: pd.DataFrame, n: int = 10) -> list[dict]:
    """
    Extract top-n keywords by raw frequency across all section text.
    Filters: minimum 4 chars, not in STOPWORDS, not purely numeric.
    Returns list of {"keyword": str, "count": int}.
    """
    all_text = " ".join(sections["section_text"].fillna("")).lower()
    words    = re.findall(r"\b[a-z][a-z0-9_]{2,}\b", all_text)
    filtered = [
        w for w in words
        if w not in STOPWORDS and not w.isdigit() and len(w) >= 4
    ]
    counts = Counter(filtered)
    return [
        {"keyword": kw, "count": cnt}
        for kw, cnt in counts.most_common(n)
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_all_analytics()