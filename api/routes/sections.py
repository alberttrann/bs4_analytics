"""
api/routes/sections.py
GET /sections (paginated), GET /sections/{id}
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import APIRouter, HTTPException, Query

from api.services.data_service import load_sections
from shared.schemas import PaginatedSections, SectionModel

router = APIRouter()


@router.get("/", response_model=PaginatedSections, summary="List all sections (paginated)")
def get_sections(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=200, description="Items per page"),
    level: int | None = Query(None, ge=1, le=3,
                               description="Filter by heading level (1, 2, or 3)"),
    search: str | None = Query(None,
                                description="Filter sections whose title contains this string"),
):
    df = load_sections()

    if level is not None:
        df = df[df["section_level"] == level]
    if search:
        df = df[df["section_title"].str.lower().str.contains(search.lower(), na=False)]

    total = len(df)
    start = (page - 1) * size
    chunk = df.iloc[start : start + size].fillna("")
    items = [SectionModel(**r) for r in chunk.to_dict(orient="records")]
    return PaginatedSections(total=total, page=page, size=size, items=items)


@router.get("/{section_id}", response_model=SectionModel, summary="Get one section by ID")
def get_section(section_id: int):
    df  = load_sections()
    row = df[df["section_id"] == section_id]
    if row.empty:
        raise HTTPException(status_code=404,
                            detail=f"Section {section_id} not found")
    return SectionModel(**row.iloc[0].fillna("").to_dict())