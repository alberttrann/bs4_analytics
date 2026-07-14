"""
pipeline/collector.py
Feature 1 - Web Page Collector
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from shared.constants import HTTP_TIMEOUT_SECONDS, RAW_HTML_PATH, TARGET_URL
from shared.utils import ensure_dirs

logger = logging.getLogger(__name__)


def fetch_and_save(
    url: str = TARGET_URL,
    dest: Path = RAW_HTML_PATH,
    timeout: int = HTTP_TIMEOUT_SECONDS,
) -> Path:
    """
    Send HTTP GET to *url*, assert 200, write HTML to *dest*.
    Returns dest path.
    """
    ensure_dirs()
    dest.parent.mkdir(parents=True, exist_ok=True) 
    logger.info("Fetching %s", url)
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "BS4-Analytics/1.0 (academic project)"},
    )
    response.raise_for_status()
    dest.write_text(response.text, encoding="utf-8")
    logger.info("Saved %d chars → %s", len(response.text), dest.name)
    print(f"[collector] Saved {len(response.text):,} chars → {dest.name}")
    return dest


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path = fetch_and_save()
    print(f"Done: {path}")
