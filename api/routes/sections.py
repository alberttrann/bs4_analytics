"""
api/routes/sections.py
Owner: Dat (B)
Task : GET /sections (paginated), GET /sections/{id}
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.services.data_service import load_sections
from shared.schemas import PaginatedSections, SectionModel

router = APIRouter()


def _raise_pipeline_not_ready(exc: FileNotFoundError) -> None:
    raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=PaginatedSections)
def list_sections(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginatedSections:
    try:
        df = load_sections()
    except FileNotFoundError as exc:
        _raise_pipeline_not_ready(exc)

    total = len(df)
    start = (page - 1) * size
    page_df = df.iloc[start : start + size]

    items = [SectionModel.model_validate(row) for row in page_df.to_dict(orient="records")]
    return PaginatedSections(total=total, page=page, size=size, items=items)


@router.get("/{section_id}", response_model=SectionModel)
def get_section(section_id: int) -> SectionModel:
    try:
        df = load_sections()
    except FileNotFoundError as exc:
        _raise_pipeline_not_ready(exc)

    match = df[df["section_id"] == section_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found")

    return SectionModel.model_validate(match.iloc[0].to_dict())
