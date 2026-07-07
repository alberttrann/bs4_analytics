"""
shared/schemas.py
=================
Pydantic models used across pipeline/, api/, app/, and tests/.
This file is the single source of truth for all data shapes.

Ownership: Hung 
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# Pipeline output models

class SectionModel(BaseModel):
    """One documentation section, extracted by pipeline/extractor.py (Member C)."""

    section_id: int = Field(..., description="Zero-based row index")
    section_level: int = Field(..., ge=1, le=3, description="Heading level: 1=h1, 2=h2, 3=h3")
    section_title: str = Field(..., description="Heading text, stripped")
    section_text: str = Field(..., description="All plain text beneath this heading")
    word_count: int = Field(..., ge=0)
    code_block_count: int = Field(..., ge=0)
    link_count: int = Field(..., ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "section_id": 0,
                "section_level": 1,
                "section_title": "Quick Start",
                "section_text": "Here's an HTML document I'll be using...",
                "word_count": 120,
                "code_block_count": 3,
                "link_count": 5,
            }
        }


class LinkModel(BaseModel):
    """One hyperlink, extracted and classified by pipeline/extractor.py + link_classifier.py (Member C)."""

    link_text: str = Field(..., description="Visible anchor text")
    href: str = Field(..., description="Raw href attribute value")
    link_type: str = Field(
        ...,
        description=(
            "One of: internal_anchor | external_link | "
            "documentation_link | image_link | empty_or_invalid"
        ),
    )
    section_title: str = Field(..., description="Title of the section this link belongs to")

    class Config:
        json_schema_extra = {
            "example": {
                "link_text": "Beautiful Soup",
                "href": "http://www.crummy.com/software/BeautifulSoup/",
                "link_type": "external_link",
                "section_title": "Beautiful Soup Documentation",
            }
        }


class CodeExampleModel(BaseModel):
    """One code block, extracted by pipeline/code_extractor.py (Albert)."""

    example_id: int = Field(..., description="Zero-based row index")
    section_title: str = Field(..., description="Title of the section this code block belongs to")
    code_text: str = Field(..., description="Raw code string")
    line_count: int = Field(..., ge=1)
    contains_find_all: bool
    contains_find: bool
    contains_select: bool
    contains_get_text: bool
    contains_requests: bool

    class Config:
        json_schema_extra = {
            "example": {
                "example_id": 0,
                "section_title": "Quick Start",
                "code_text": "soup.find_all('a')",
                "line_count": 1,
                "contains_find_all": True,
                "contains_find": False,
                "contains_select": False,
                "contains_get_text": False,
                "contains_requests": False,
            }
        }


# Analytics output models

class KeywordEntry(BaseModel):
    """A single keyword with its frequency count."""
    keyword: str
    count: int


class AnalyticsSummary(BaseModel):
    """
    Aggregated analytics results produced by pipeline/analyzer.py (Member D).

    Core fields (Q1–Q8) are always present.
    Advanced fields (prefixed adv_) are populated by pipeline/advanced/ (Albert)
    and default to None so existing consumers never break.
    """

    # Q1
    total_sections: int = Field(..., description="Total number of extracted sections")
    # Q2
    highest_wordcount_section: str = Field(..., description="Section title with the most words")
    highest_wordcount_value: int = Field(..., ge=0)
    # Q3
    most_code_examples_section: str = Field(..., description="Section with the most code blocks")
    most_code_examples_count: int = Field(..., ge=0)
    # Q4
    most_links_section: str = Field(..., description="Section containing the most hyperlinks")
    most_links_count: int = Field(..., ge=0)
    # Q5
    top_10_keywords: list[KeywordEntry] = Field(..., description="Top 10 keywords by frequency")
    # Q6
    link_type_counts: dict[str, int] = Field(
        ...,
        description="Counts keyed by link_type string",
        example={
            "internal_anchor": 120,
            "external_link": 45,
            "documentation_link": 30,
            "image_link": 2,
            "empty_or_invalid": 1,
        },
    )
    # Q7
    find_all_example_count: int = Field(..., ge=0)
    # Q8
    get_text_example_count: int = Field(..., ge=0)

    # Team-proposed questions (Member D fills these)
    avg_words_per_section: float = Field(..., ge=0)
    sections_with_no_code: int = Field(..., ge=0)

    # Advanced fields — adds without breaking existing consumers
    adv_avg_readability_score: Optional[float] = Field(
        None, description="Mean Flesch Reading Ease across all sections"
    )
    adv_top_similar_pairs: Optional[list[tuple[str, str, float]]] = Field(
        None, description="Top cosine-similar section pairs: (title_a, title_b, score)"
    )
    adv_top_tfidf_keywords: Optional[list[KeywordEntry]] = Field(
        None, description="Top keywords by TF-IDF weight (more precise than raw frequency)"
    )


# API response wrappers

class PaginatedSections(BaseModel):
    total: int
    page: int
    size: int
    items: list[SectionModel]


class PaginatedLinks(BaseModel):
    total: int
    items: list[LinkModel]


class PaginatedCode(BaseModel):
    total: int
    items: list[CodeExampleModel]


class PipelineStatus(BaseModel):
    running: bool
    last_run: Optional[str] = Field(None, description="ISO-8601 timestamp of last completed run")
    last_run_duration_seconds: Optional[float] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    pipeline_ever_run: bool
    data_files_present: dict[str, bool]
