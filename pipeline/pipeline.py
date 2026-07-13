"""
pipeline/pipeline.py
Owner: Hung (A)
Orchestrator — runs all pipeline stages in dependency order.
Prints one progress line per stage to stdout (consumed by api/websocket.py).

Usage:
  python -m pipeline.pipeline               # full run
  python -m pipeline.pipeline --skip-fetch  # reuse cached HTML
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

logger = logging.getLogger(__name__)


def run_all(skip_fetch: bool = False) -> None:
    """
    Execute every pipeline stage in sequence.
    Each stage prints a timestamped progress line — flush=True ensures
    the WebSocket endpoint can stream lines in real time.
    """
    # Import here (not at module level) to avoid circular imports and so
    # that each stage module is only loaded when the pipeline actually runs.
    from pipeline import (
        analyzer,
        code_extractor,
        collector,
        extractor,
        parser,
        reporter,
        visualizer,
    )

    # ── Stage definitions ──────────────────────────────────────────────────
    def stage_collect():
        if skip_fetch:
            from shared.constants import RAW_HTML_PATH
            if not RAW_HTML_PATH.exists():
                raise FileNotFoundError(
                    f"--skip-fetch requested but {RAW_HTML_PATH} does not exist. "
                    "Run without --skip-fetch first."
                )
            logger.info("Skipping fetch — reusing %s", RAW_HTML_PATH.name)
            return
        collector.fetch_and_save()

    def stage_parse():
        # Just validate the HTML parses cleanly; soup is re-created per extraction stage.
        soup = parser.parse_html()
        logger.info("Parsed HTML — found %d tags", len(list(soup.find_all())))

    def stage_extract():
        soup = parser.parse_html()
        extractor.extract_all(soup)
        code_extractor.extract_code_examples(soup)

    def stage_analyze():
        analyzer.run_all_analytics()

    def stage_visualize():
        visualizer.plot_all()

    def stage_report():
        reporter.generate_all()

    stages = [
        ("Collecting HTML",   stage_collect),
        ("Parsing HTML",      stage_parse),
        ("Extracting data",   stage_extract),
        ("Running analytics", stage_analyze),
        ("Generating charts", stage_visualize),
        ("Generating report", stage_report),
    ]

    total         = len(stages)
    overall_start = time.perf_counter()
    print(f"[pipeline] Starting — {total} stages", flush=True)

    for i, (label, fn) in enumerate(stages, start=1):
        print(f"[pipeline] [{i}/{total}] {label}...", flush=True)
        t = time.perf_counter()
        try:
            fn()
        except Exception as exc:
            print(f"[pipeline] ERROR in '{label}': {exc}", flush=True)
            logger.exception("Pipeline stage '%s' failed", label)
            sys.exit(1)
        elapsed = time.perf_counter() - t
        print(f"[pipeline] [{i}/{total}] Done ({elapsed:.1f}s)", flush=True)

    total_elapsed = time.perf_counter() - overall_start
    print(f"[pipeline] All stages complete in {total_elapsed:.1f}s", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description="BS4 Analytics pipeline")
    p.add_argument("--skip-fetch", action="store_true",
                   help="Reuse cached HTML instead of downloading")
    p.add_argument("--log-level", default="INFO",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = p.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_all(skip_fetch=args.skip_fetch)


if __name__ == "__main__":
    main()
