"""
pipeline/parser.py
Owner: Dat (B)
Task : F2 — load saved HTML, return BeautifulSoup object, extract section tree
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from shared.constants import RAW_HTML_PATH
from shared.utils import word_count

logger = logging.getLogger(__name__)

HEADING_TAGS: dict[str, int] = {"h1": 1, "h2": 2, "h3": 3}


def load_html(path: Path = RAW_HTML_PATH) -> BeautifulSoup:
    """
    Load raw HTML from disk and return a BeautifulSoup object.

    Raises
    ------
    FileNotFoundError
        When collector.py has not been run yet.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"[Collector not yet run] Missing file: {path}\n"
            "Run `python -m pipeline.collector` first."
        )

    html = path.read_text(encoding="utf-8")
    return BeautifulSoup(html, "html.parser")


def _heading_level(tag: Tag) -> int | None:
    return HEADING_TAGS.get(tag.name)


def _collect_section_elements(heading: Tag) -> list[Tag | NavigableString]:
    """
    Return sibling nodes belonging to *heading* until the next heading
    of the same or higher level (h1 > h2 > h3).
    """
    current_level = _heading_level(heading)
    if current_level is None:
        return []

    elements: list[Tag | NavigableString] = []
    for sibling in heading.next_siblings:
        if isinstance(sibling, Tag) and _heading_level(sibling) is not None:
            if _heading_level(sibling) <= current_level:
                break
        elements.append(sibling)

    return elements


def _section_metrics(elements: list[Tag | NavigableString]) -> tuple[str, int, int, int]:
    """Build combined text and count code blocks / links within *elements*."""
    text_parts: list[str] = []
    code_block_count = 0
    link_count = 0

    for element in elements:
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text:
                text_parts.append(text)
            continue

        if not isinstance(element, Tag):
            continue

        text = element.get_text(separator=" ", strip=True)
        if text:
            text_parts.append(text)

        code_block_count += len(element.find_all("div", class_="highlight"))
        link_count += len(element.find_all("a"))

    section_text = " ".join(text_parts)
    return section_text, word_count(section_text), code_block_count, link_count


def extract_section_tree(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """
    Walk every h1/h2/h3 heading in document order and build section records.

    Each section spans from its heading until the next heading of the same
    or higher level. Returned dicts match ``SECTION_COLS``.
    """
    sections: list[dict[str, Any]] = []

    for section_id, heading in enumerate(soup.find_all(list(HEADING_TAGS))):
        level = _heading_level(heading)
        if level is None:
            continue

        elements = _collect_section_elements(heading)
        section_text, wc, code_blocks, links = _section_metrics(elements)

        sections.append(
            {
                "section_id": section_id,
                "section_level": level,
                "section_title": heading.get_text(strip=True),
                "section_text": section_text,
                "word_count": wc,
                "code_block_count": code_blocks,
                "link_count": links,
            }
        )

    return sections


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    soup = load_html()
    sections = extract_section_tree(soup)
    logger.info("Found %d sections in %s", len(sections), RAW_HTML_PATH.name)
    print(f"Found {len(sections)} sections")


if __name__ == "__main__":
    main()
