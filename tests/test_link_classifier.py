"""
tests/test_link_classifier.py
Parametrized unit tests for pipeline/link_classifier.py
One test case per classification branch + edge cases.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from shared.constants import (
    LINK_TYPE_DOCUMENTATION,
    LINK_TYPE_EMPTY_OR_INVALID,
    LINK_TYPE_EXTERNAL,
    LINK_TYPE_IMAGE,
    LINK_TYPE_INTERNAL_ANCHOR,
    LINK_TYPES,
)


@pytest.mark.parametrize("href, expected", [
    # --- empty_or_invalid ---
    (None,                        LINK_TYPE_EMPTY_OR_INVALID),
    ("",                          LINK_TYPE_EMPTY_OR_INVALID),
    ("   ",                       LINK_TYPE_EMPTY_OR_INVALID),
    ("#",                         LINK_TYPE_EMPTY_OR_INVALID),
    ("javascript:void(0)",        LINK_TYPE_EMPTY_OR_INVALID),
    ("javascript:",               LINK_TYPE_EMPTY_OR_INVALID),

    # --- image_link ---
    ("_images/logo.png",          LINK_TYPE_IMAGE),
    ("assets/banner.jpg",         LINK_TYPE_IMAGE),
    ("icons/icon.svg",            LINK_TYPE_IMAGE),
    ("http://example.com/a.gif",  LINK_TYPE_IMAGE),
    ("photo.jpeg",                LINK_TYPE_IMAGE),
    ("image.webp",                LINK_TYPE_IMAGE),

    # --- internal_anchor ---
    ("#quick-start",              LINK_TYPE_INTERNAL_ANCHOR),
    ("#installing-beautiful-soup",LINK_TYPE_INTERNAL_ANCHOR),
    ("#searching-the-tree",       LINK_TYPE_INTERNAL_ANCHOR),

    # --- documentation_link ---
    ("https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
                                  LINK_TYPE_DOCUMENTATION),
    ("http://www.crummy.com/software/BeautifulSoup/",
                                  LINK_TYPE_DOCUMENTATION),
    ("https://www.crummy.com/software/BeautifulSoup/bs4/doc/zh/",
                                  LINK_TYPE_DOCUMENTATION),

    # --- external_link ---
    ("https://pypi.org/project/beautifulsoup4/", LINK_TYPE_EXTERNAL),
    ("http://lxml.de/",                          LINK_TYPE_EXTERNAL),
    ("https://docs.python.org/3/",               LINK_TYPE_EXTERNAL),
    ("https://groups.google.com/forum/",         LINK_TYPE_EXTERNAL),
    ("http://kondou.com/BS4/",                   LINK_TYPE_EXTERNAL),
])
def test_classify_link_parametrized(href, expected):
    from pipeline.link_classifier import classify_link
    result = classify_link(href)
    assert result == expected, (
        f"classify_link({href!r}) returned {result!r}, expected {expected!r}"
    )


def test_return_value_always_in_link_types():
    """Every possible href should return one of the 5 known LINK_TYPES."""
    from pipeline.link_classifier import classify_link
    test_hrefs = [
        None, "", "#", "javascript:void(0)",
        "#section", "_images/img.png", "photo.jpeg",
        "https://www.crummy.com/bs4/", "http://www.crummy.com/",
        "https://example.com/", "http://google.com/",
        "mailto:user@example.com",
    ]
    for href in test_hrefs:
        result = classify_link(href)
        assert result in LINK_TYPES, \
            f"classify_link({href!r}) = {result!r} which is not in LINK_TYPES"


def test_all_five_types_reachable():
    """Confirm we can reach every LINK_TYPE with at least one input."""
    from pipeline.link_classifier import classify_link
    sample = {
        LINK_TYPE_EMPTY_OR_INVALID: "",
        LINK_TYPE_IMAGE:            "_images/logo.png",
        LINK_TYPE_INTERNAL_ANCHOR:  "#quick-start",
        LINK_TYPE_DOCUMENTATION:    "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
        LINK_TYPE_EXTERNAL:         "https://pypi.org/",
    }
    for expected_type, href in sample.items():
        assert classify_link(href) == expected_type