"""
api/routes/code.py
Owner: Hung (A)
GET /code-examples (filtered), GET /code-examples/{id}
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.services.data_service import load_code_examples
from shared.schemas import CodeExampleModel, PaginatedCode

router = APIRouter()

_VALID_METHOD_FILTERS = [
    "contains_find_all", "contains_find", "contains_select",
    "contains_get_text", "contains_requests",
]


@router.get("/", response_model=PaginatedCode, summary="List code examples")
def get_code_examples(
    method: str | None = Query(
        None,
        description="Filter to examples that use this method. "
                    "One of: contains_find_all, contains_find, contains_select, "
                    "contains_get_text, contains_requests",
    ),
    section: str | None = Query(None, description="Filter by section_title (exact)"),
):
    df = load_code_examples()

    if method:
        if method not in _VALID_METHOD_FILTERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown method filter '{method}'. "
                       f"Valid options: {_VALID_METHOD_FILTERS}",
            )
        df = df[df[method] == True]  

    if section:
        df = df[df["section_title"] == section]

    items = [CodeExampleModel(**r) for r in df.to_dict(orient="records")]
    return PaginatedCode(total=len(items), items=items)


@router.get("/{example_id}", response_model=CodeExampleModel,
            summary="Get one code example by ID")
def get_code_example(example_id: int):
    df  = load_code_examples()
    row = df[df["example_id"] == example_id]
    if row.empty:
        raise HTTPException(status_code=404,
                            detail=f"Code example {example_id} not found")
    return CodeExampleModel(**row.iloc[0].to_dict())
