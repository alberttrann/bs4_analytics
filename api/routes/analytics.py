"""
api/routes/analytics.py
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter

from shared.constants import ALL_CHART_PATHS, CHART_NAMES, LINK_TYPES

router = APIRouter()


@router.get("/summary")
def get_summary():
    """Load from saved summary_stats.json - preserves adv_ fields written by advanced pipeline."""
    from shared.utils import load_summary_stats
    try:
        return load_summary_stats()
    except FileNotFoundError:
        # JSON doesn't exist yet - run analytics to generate it
        from api.services.data_service import load_sections, load_links, load_code_examples
        from pipeline.analyzer import run_all_analytics
        return run_all_analytics(
            sections=load_sections(),
            links=load_links(),
            code=load_code_examples(),
        )


@router.get("/charts")
def get_charts() -> dict[str, str]:
    return {
        CHART_NAMES[p.name]: f"/static/charts/{p.name}"
        for p in ALL_CHART_PATHS
        if p.exists()
    }


@router.get("/link-types")
def get_link_type_counts() -> dict[str, int]:
    from api.services.data_service import load_links
    counts = load_links()["link_type"].value_counts().to_dict()
    return {lt: int(counts.get(lt, 0)) for lt in LINK_TYPES}