"""
pipeline/pipeline.py
Orchestrator - runs all pipeline stages in dependency order.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

logger = logging.getLogger(__name__)


def _stage_collect(skip_fetch: bool = False):
    from pipeline.collector import fetch_and_save
    from shared.constants import RAW_HTML_PATH
    if skip_fetch and RAW_HTML_PATH.exists():
        logger.info("Skipping fetch - reusing %s", RAW_HTML_PATH.name)
        return
    fetch_and_save()


def _stage_parse():
    from pipeline.parser import parse_html
    soup = parse_html()
    logger.info("Parsed HTML - %d tags", len(list(soup.find_all())))


def _stage_extract():
    from pipeline.parser import parse_html
    from pipeline.extractor import extract_all
    from pipeline.code_extractor import extract_code_examples
    soup = parse_html()
    extract_all(soup)
    extract_code_examples(soup)


def _stage_analyze():
    from pipeline.analyzer import run_all_analytics
    run_all_analytics()


def _stage_visualize():
    from pipeline.visualizer import plot_all
    plot_all()


def _stage_report():
    from pipeline.reporter import generate_all
    generate_all()


def _stage_advanced():
    """Run TF-IDF, readability, similarity - saves adv_ fields into summary_stats.json."""
    try:
        import json
        from pipeline.advanced.nlp_analyzer import compute_tfidf_keywords, compute_readability
        from pipeline.advanced.similarity import top_similar_pairs
        from shared.utils import load_sections, load_summary_stats
        from shared.constants import SUMMARY_STATS_JSON

        sections = load_sections()
        summary  = load_summary_stats()

        tfidf  = compute_tfidf_keywords(sections, top_n=20)
        scores = compute_readability(sections)
        pairs  = top_similar_pairs(sections, top_n=10)

        summary["adv_top_tfidf_keywords"]    = tfidf
        summary["adv_avg_readability_score"] = round(float(scores.mean()), 2)
        summary["adv_top_similar_pairs"]     = [
            [a, b, round(s, 4)] for a, b, s in pairs
        ]

        SUMMARY_STATS_JSON.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print("[advanced] adv_ fields saved to summary_stats.json")
    except Exception as e:
        print(f"[advanced] Non-critical error (skipping): {e}")


# ---------------------------------------------------------------------------
# CLI run_all  (used by: python -m pipeline.pipeline)
# ---------------------------------------------------------------------------

def run_all(skip_fetch: bool = False) -> None:
    stages = [
        ("Collecting HTML",    lambda: _stage_collect(skip_fetch)),
        ("Parsing HTML",       _stage_parse),
        ("Extracting data",    _stage_extract),
        ("Running analytics",  _stage_analyze),
        ("Generating charts",  _stage_visualize),
        ("Generating report",  _stage_report),
        ("Advanced analytics", _stage_advanced),
    ]

    total         = len(stages)
    overall_start = time.perf_counter()
    print(f"[pipeline] Starting - {total} stages", flush=True)

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