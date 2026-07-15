"""
pipeline/collector.py
Owner: Dat (B)
Task : F1 — fetch TARGET_URL, save to data/raw/beautifulsoup_doc.html
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from shared.constants import (
    HTTP_TIMEOUT_SECONDS,
    HTTP_USER_AGENT,
    RAW_HTML_PATH,
    TARGET_URL,
)
from shared.utils import ensure_dirs

logger = logging.getLogger(__name__)


def collect(url: str = TARGET_URL, output_path: Path = RAW_HTML_PATH) -> Path:
    """
    Send an HTTP GET request to *url*, verify status 200, and save raw HTML.

    Parameters
    ----------
    url : str
        Documentation page to fetch.
    output_path : Path
        Destination file for the raw HTML response.

    Returns
    -------
    Path
        The path where the HTML was written.

    Raises
    ------
    requests.HTTPError
        When the server returns a non-2xx status code.
    requests.RequestException
        On network or timeout errors.
    """
    ensure_dirs()

    logger.info("Fetching %s", url)
    response = requests.get(
        url,
        timeout=HTTP_TIMEOUT_SECONDS,
        headers={"User-Agent": HTTP_USER_AGENT},
    )
    response.raise_for_status()

    output_path.write_text(response.text, encoding="utf-8")
    logger.info("Saved %d characters → %s", len(response.text), output_path)

    return output_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    path = collect()
    print(f"Saved raw HTML -> {path}")


if __name__ == "__main__":
    main()
