"""
pipeline/parser.py
Feature 2 - HTML Parser
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

from shared.constants import RAW_HTML_PATH, SECTION_COLS
from shared.utils import word_count

logger = logging.getLogger(__name__)

_HEADING_TAGS = {"h1", "h2", "h3"}
_HEADING_LEVEL = {"h1": 1, "h2": 2, "h3": 3}


def parse_html(path: Path = RAW_HTML_PATH) -> BeautifulSoup:
    """Load saved HTML from disk and return a BeautifulSoup object."""
    if not path.exists():
        raise FileNotFoundError(
            f"HTML file not found: {path}\n"
            "Run `python -m pipeline.collector` first."
        )
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    logger.info("Parsed HTML - %d total tags", len(list(soup.find_all())))
    return soup


def extract_section_tree(soup: BeautifulSoup) -> list[dict]:
    """
    Walk all h1/h2/h3 headings in document order.
    For each heading, collect all sibling content until the next heading
    of equal or higher level. Return list of dicts matching SECTION_COLS.
    """
    headings = soup.find_all(["h1", "h2", "h3"])
    if not headings:
        logger.warning("No headings found in document")
        return []

    sections: list[dict] = []

    for idx, heading in enumerate(headings):
        level = _HEADING_LEVEL[heading.name]
        title = heading.get_text(strip=True).replace("¶", "").strip()

        # Collect siblings until next heading of same or higher level
        content_tags: list[Tag] = []
        for sibling in heading.next_siblings:
            if isinstance(sibling, NavigableString):
                continue
            if isinstance(sibling, Tag):
                if sibling.name in _HEADING_TAGS:
                    if _HEADING_LEVEL[sibling.name] <= level:
                        break
                content_tags.append(sibling)

        # Aggregate text
        section_text = " ".join(
            tag.get_text(separator=" ", strip=True)
            for tag in content_tags
        )
        section_text = re.sub(r"\s+", " ", section_text).strip()

        # Count code blocks and links within this section's content
        code_block_count = sum(
            1 for tag in content_tags
            if isinstance(tag, Tag) and tag.find("div", class_="highlight")
            or (isinstance(tag, Tag) and "highlight" in tag.get("class", []))
        )
        link_count = sum(
            len(tag.find_all("a")) if isinstance(tag, Tag) else 0
            for tag in content_tags
        )

        sections.append({
            "section_id":       idx,
            "section_level":    level,
            "section_title":    title,
            "section_text":     section_text,
            "word_count":       word_count(section_text),
            "code_block_count": code_block_count,
            "link_count":       link_count,
        })

    logger.info("Extracted %d sections", len(sections))
    return sections


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    soup     = parse_html()
    sections = extract_section_tree(soup)
    print(f"Found {len(sections)} sections")
    for s in sections[:5]:
        print(f"  [H{s['section_level']}] {s['section_title'][:60]}  "
              f"({s['word_count']} words, {s['code_block_count']} code blocks)")
