"""
pipeline/link_classifier.py
Feature 4 - Link Type Classifier
"""

from __future__ import annotations

from shared.constants import (
    LINK_TYPE_DOCUMENTATION,
    LINK_TYPE_EMPTY_OR_INVALID,
    LINK_TYPE_EXTERNAL,
    LINK_TYPE_IMAGE,
    LINK_TYPE_INTERNAL_ANCHOR,
    TARGET_URL,
)

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp")
_INVALID_VALUES   = {"", "#", "javascript:void(0)", "javascript:", "#!"}


def classify_link(href: str | None, base_url: str = TARGET_URL) -> str:
    """
    Classify a single href into one of 5 canonical link types.

    Classification order (first match wins):
      1. empty_or_invalid   - None, empty string, bare "#", javascript: links
      2. image_link         - href ends with a known image file extension
      3. internal_anchor    - href starts with "#" (but not bare "#")
      4. documentation_link - href belongs to the BeautifulSoup docs domain
      5. external_link      - everything else

    Parameters
    ----------
    href : str | None
        Raw href attribute value from an <a> tag.
    base_url : str
        The canonical documentation base URL.

    Returns
    -------
    str
        One of the 5 LINK_TYPE_* constants from shared.constants.
    """
    # 1 - empty / invalid
    if not href:
        return LINK_TYPE_EMPTY_OR_INVALID
    href_stripped = href.strip()
    if href_stripped in _INVALID_VALUES or href_stripped.startswith("javascript:"):
        return LINK_TYPE_EMPTY_OR_INVALID

    href_lower = href_stripped.lower()

    # 2 - image
    if any(href_lower.endswith(ext) for ext in _IMAGE_EXTENSIONS):
        return LINK_TYPE_IMAGE

    # 3 - internal anchor (but not bare "#" - already caught above)
    if href_stripped.startswith("#"):
        return LINK_TYPE_INTERNAL_ANCHOR

    # 4 - documentation (same domain as the source docs)
    if href_stripped.startswith(base_url) or "crummy.com" in href_lower:
        return LINK_TYPE_DOCUMENTATION

    # 5 - external
    return LINK_TYPE_EXTERNAL