"""
api/routes/search.py
Advanced - GET /search?q=&target=sections|links|code|all
Full-text search across all three processed datasets.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException

from api.services.data_service import load_code_examples, load_links, load_sections

router = APIRouter()

_VALID_TARGETS = {"sections", "links", "code", "all"}


@router.get("/", summary="Full-text search across datasets")
def search(
    q: str = Query(..., min_length=2,
                   description="Search query (minimum 2 characters)"),
    target: str = Query("all",
                        description="Which dataset to search: sections | links | code | all"),
):
    """
    Search for *q* across section text, link text/href, and/or code blocks.
    Returns matching rows grouped under their dataset name.
    """
    if target not in _VALID_TARGETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target '{target}'. Must be one of: {sorted(_VALID_TARGETS)}",
        )

    q_lower  = q.lower()
    results: dict[str, list] = {}

    if target in ("sections", "all"):
        df   = load_sections()
        mask = (df["section_title"].str.lower().str.contains(q_lower, na=False) |
                df["section_text"].str.lower().str.contains(q_lower, na=False))
        results["sections"] = df[mask].to_dict(orient="records")

    if target in ("links", "all"):
        df   = load_links()
        mask = (df["link_text"].str.lower().str.contains(q_lower, na=False) |
                df["href"].str.lower().str.contains(q_lower, na=False))
        results["links"] = df[mask].to_dict(orient="records")

    if target in ("code", "all"):
        df   = load_code_examples()
        mask = df["code_text"].str.lower().str.contains(q_lower, na=False)
        results["code"] = df[mask].to_dict(orient="records")

    total = sum(len(v) for v in results.values())
    return {"query": q, "target": target, "total_matches": total, "results": results}
