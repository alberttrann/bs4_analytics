"""
api/routes/links.py
GET /links (filtered), GET /links/stats
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query

from api.services.data_service import load_links
from shared.constants import LINK_TYPES
from shared.schemas import LinkModel, PaginatedLinks

router = APIRouter()


@router.get("/", response_model=PaginatedLinks, summary="List links with optional filters")
def get_links(
    link_type: str | None = Query(
        None,
        description=f"Filter by link type. One of: {', '.join(LINK_TYPES)}",
    ),
    section: str | None = Query(
        None,
        description="Filter by section_title (exact match)",
    ),
    search: str | None = Query(
        None,
        description="Filter by link_text or href containing this string",
    ),
):
    df = load_links()

    if link_type:
        if link_type not in LINK_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid link_type '{link_type}'. Valid: {LINK_TYPES}",
            )
        df = df[df["link_type"] == link_type]

    if section:
        df = df[df["section_title"] == section]

    if search:
        s = search.lower()
        mask = (
            df["link_text"].str.lower().str.contains(s, na=False) |
            df["href"].str.lower().str.contains(s, na=False)
        )
        df = df[mask]

    df = df.fillna("")
    items = [LinkModel(**r) for r in df.to_dict(orient="records")]
    return PaginatedLinks(total=len(items), items=items)


@router.get("/stats", summary="Link count by type")
def get_link_stats() -> dict[str, int]:
    counts = load_links()["link_type"].value_counts().to_dict()
    return {lt: int(counts.get(lt, 0)) for lt in LINK_TYPES}