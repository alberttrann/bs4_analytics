"""
pipeline/extractor.py
Features 3 & 4 - Section Extractor + Link Extractor
soup → sections.csv and links.csv
"""

from __future__ import annotations

import logging

import pandas as pd
from bs4 import BeautifulSoup, Tag

from pipeline.link_classifier import classify_link
from pipeline.parser import extract_section_tree
from shared.constants import LINK_COLS, LINKS_CSV, SECTION_COLS, SECTIONS_CSV
from shared.utils import ensure_dirs, save_csv

logger = logging.getLogger(__name__)


# Section extraction

def extract_sections(soup: BeautifulSoup) -> pd.DataFrame:
    """
    Build sections DataFrame from the parsed soup and write sections.csv.
    Delegates heading-tree logic to parser.extract_section_tree().
    """
    rows = extract_section_tree(soup)
    df   = pd.DataFrame(rows, columns=SECTION_COLS)
    ensure_dirs()
    save_csv(df, SECTIONS_CSV, expected_cols=SECTION_COLS)
    logger.info("sections.csv → %d rows", len(df))
    print(f"[extractor] sections.csv → {len(df)} rows")
    return df


# Link extraction

def extract_links(soup: BeautifulSoup, sections: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for tag in soup.find_all("a"):
        href      = tag.get("href", "") or ""
        link_text = tag.get_text(strip=True).replace("¶", "").strip()
        link_type = classify_link(href)

        # Skip pilcrow-only anchor links (¶ permalink markers Sphinx adds)
        if not link_text and href.startswith("#"):
            continue

        section_title = _find_parent_section(tag, sections)
        rows.append({
            "link_text":     link_text,
            "href":          href,
            "link_type":     link_type,
            "section_title": section_title,
        })

    df = pd.DataFrame(rows, columns=LINK_COLS)
    save_csv(df, LINKS_CSV, expected_cols=LINK_COLS)
    logger.info("links.csv → %d rows", len(df))
    print(f"[extractor] links.csv → {len(df)} rows")
    return df


def _find_parent_section(tag: Tag, sections: pd.DataFrame) -> str:
    """Find the nearest preceding heading in document order."""
    for heading in tag.find_all_previous(["h1", "h2", "h3"]):
        title = heading.get_text(strip=True).replace("¶", "").strip()
        match = sections[sections["section_title"] == title]
        if not match.empty:
            return title
    return "Unknown"


# Combined entry point

def extract_all(soup: BeautifulSoup) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run both extractors in dependency order. Returns (sections_df, links_df)."""
    sections = extract_sections(soup)
    links    = extract_links(soup, sections)
    return sections, links


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from pipeline.parser import parse_html
    soup = parse_html()
    sections, links = extract_all(soup)
    print(f"\nSections : {len(sections)}")
    print(f"Links    : {len(links)}")
    print("Link type breakdown:")
    print(links["link_type"].value_counts().to_string())