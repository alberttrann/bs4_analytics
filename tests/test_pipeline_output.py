"""
tests/test_pipeline_output.py
All tests - run against real pipeline output data.
Tests skip gracefully when the pipeline has not been run yet.

Usage:
  pytest tests/ -v                   # after running pipeline
  pytest tests/ -v -k "not skip"    # run only non-data tests (API health etc.)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from shared.constants import (
    ALL_CHART_PATHS,
    CODE_COLS,
    LINK_COLS,
    LINK_TYPES,
    SECTION_COLS,
    CODE_EXAMPLES_CSV,
    LINKS_CSV,
    SECTIONS_CSV,
    SUMMARY_STATS_JSON,
)


# Skip decorator

def _pipeline_ready() -> bool:
    return (SECTIONS_CSV.exists()
            and LINKS_CSV.exists()
            and CODE_EXAMPLES_CSV.exists())


skip_if_no_data = pytest.mark.skipif(
    not _pipeline_ready(),
    reason="Pipeline output not found. Run `python -m pipeline.pipeline` first.",
)


# sections.csv

@skip_if_no_data
def test_sections_has_correct_columns():
    df = pd.read_csv(SECTIONS_CSV)
    assert set(SECTION_COLS) == set(df.columns), \
        f"Column mismatch. Expected {SECTION_COLS}, got {list(df.columns)}"


@skip_if_no_data
def test_sections_not_empty():
    df = pd.read_csv(SECTIONS_CSV)
    assert len(df) > 0, "sections.csv has no rows"


@skip_if_no_data
def test_sections_word_counts_non_negative():
    df = pd.read_csv(SECTIONS_CSV)
    assert (df["word_count"] >= 0).all(), "Found negative word counts"


@skip_if_no_data
def test_sections_levels_valid():
    df = pd.read_csv(SECTIONS_CSV)
    assert df["section_level"].isin([1, 2, 3]).all(), \
        f"Invalid section levels: {df['section_level'].unique()}"


@skip_if_no_data
def test_sections_ids_unique():
    df = pd.read_csv(SECTIONS_CSV)
    assert df["section_id"].is_unique, "section_id values are not unique"


@skip_if_no_data
def test_sections_titles_not_empty():
    df = pd.read_csv(SECTIONS_CSV)
    assert df["section_title"].str.strip().ne("").all(), \
        "Some section titles are empty"


# links.csv

@skip_if_no_data
def test_links_has_correct_columns():
    df = pd.read_csv(LINKS_CSV)
    assert set(LINK_COLS) == set(df.columns)


@skip_if_no_data
def test_links_not_empty():
    df = pd.read_csv(LINKS_CSV)
    assert len(df) > 0, "links.csv has no rows"


@skip_if_no_data
def test_links_all_five_types_present():
    df    = pd.read_csv(LINKS_CSV)
    found = set(df["link_type"].unique())
    for lt in LINK_TYPES:
        assert lt in found, \
            f"Link type '{lt}' not found in links.csv. Found: {found}"


@skip_if_no_data
def test_links_types_all_valid():
    df = pd.read_csv(LINKS_CSV)
    invalid = df[~df["link_type"].isin(LINK_TYPES)]
    assert len(invalid) == 0, \
        f"Invalid link types found: {invalid['link_type'].unique()}"


# code_examples.csv

@skip_if_no_data
def test_code_has_correct_columns():
    df = pd.read_csv(CODE_EXAMPLES_CSV)
    assert set(CODE_COLS) == set(df.columns)


@skip_if_no_data
def test_code_not_empty():
    df = pd.read_csv(CODE_EXAMPLES_CSV)
    assert len(df) > 0, "code_examples.csv has no rows"


@skip_if_no_data
def test_code_line_counts_positive():
    df = pd.read_csv(CODE_EXAMPLES_CSV)
    assert (df["line_count"] > 0).all(), "Found code examples with 0 lines"


@skip_if_no_data
def test_code_boolean_columns_are_bool():
    df    = pd.read_csv(CODE_EXAMPLES_CSV)
    b_cols = ["contains_find_all", "contains_find", "contains_select",
              "contains_get_text", "contains_requests"]
    for col in b_cols:
        unique = set(df[col].astype(str).str.lower().unique())
        assert unique <= {"true", "false", "1", "0"}, \
            f"Column '{col}' has unexpected values: {unique}"


@skip_if_no_data
def test_code_find_all_count_positive():
    df = pd.read_csv(CODE_EXAMPLES_CSV)
    df["contains_find_all"] = df["contains_find_all"].astype(bool)
    count = int(df["contains_find_all"].sum())
    assert count > 0, "No code examples use find_all() - unexpected for BS4 docs"


# Analytics

@skip_if_no_data
def test_analytics_all_required_keys():
    from pipeline.analyzer import run_all_analytics
    result = run_all_analytics()
    required = [
        "total_sections", "highest_wordcount_section", "highest_wordcount_value",
        "most_code_examples_section", "most_code_examples_count",
        "most_links_section", "most_links_count",
        "top_10_keywords", "link_type_counts",
        "find_all_example_count", "get_text_example_count",
        "avg_words_per_section", "sections_with_no_code",
    ]
    for key in required:
        assert key in result, f"Missing analytics key: '{key}'"


@skip_if_no_data
def test_analytics_top_keywords_count():
    from pipeline.analyzer import run_all_analytics
    result = run_all_analytics()
    kw = result["top_10_keywords"]
    assert len(kw) == 10, f"Expected 10 keywords, got {len(kw)}"


@skip_if_no_data
def test_analytics_total_sections_matches_csv():
    from pipeline.analyzer import run_all_analytics
    df     = pd.read_csv(SECTIONS_CSV)
    result = run_all_analytics()
    assert result["total_sections"] == len(df)


@skip_if_no_data
def test_analytics_summary_json_exists():
    assert SUMMARY_STATS_JSON.exists(), \
        "summary_stats.json not found - run the full pipeline"


# Charts

@skip_if_no_data
def test_all_four_charts_exist():
    for path in ALL_CHART_PATHS:
        assert path.exists(), f"Chart file missing: {path.name}"


@skip_if_no_data
def test_charts_are_non_empty():
    for path in ALL_CHART_PATHS:
        if path.exists():
            assert path.stat().st_size > 1000, \
                f"Chart file looks too small (possibly corrupt): {path.name}"


# API routes

def test_api_health():
    from fastapi.testclient import TestClient
    from api.main import app
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@skip_if_no_data
def test_api_sections_returns_data():
    from fastapi.testclient import TestClient
    from api.main import app
    data = TestClient(app).get("/sections/").json()
    assert data["total"] > 0
    assert len(data["items"]) > 0


@skip_if_no_data
def test_api_section_by_id():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    resp   = client.get("/sections/0")
    assert resp.status_code == 200
    assert "section_title" in resp.json()


@skip_if_no_data
def test_api_section_404():
    from fastapi.testclient import TestClient
    from api.main import app
    resp = TestClient(app).get("/sections/999999")
    assert resp.status_code == 404


@skip_if_no_data
def test_api_link_stats_has_all_five_types():
    from fastapi.testclient import TestClient
    from api.main import app
    data = TestClient(app).get("/links/stats").json()
    for lt in LINK_TYPES:
        assert lt in data, f"Link type '{lt}' missing from /links/stats"


@skip_if_no_data
def test_api_code_examples_returns_data():
    from fastapi.testclient import TestClient
    from api.main import app
    data = TestClient(app).get("/code-examples/").json()
    assert data["total"] > 0


@skip_if_no_data
def test_api_code_method_filter():
    from fastapi.testclient import TestClient
    from api.main import app
    client = TestClient(app)
    data   = client.get("/code-examples/?method=contains_find_all").json()
    for item in data["items"]:
        assert item["contains_find_all"] is True


@skip_if_no_data
def test_api_code_invalid_method_returns_400():
    from fastapi.testclient import TestClient
    from api.main import app
    resp = TestClient(app).get("/code-examples/?method=invalid_col")
    assert resp.status_code == 400


@skip_if_no_data
def test_api_analytics_summary_schema():
    from fastapi.testclient import TestClient
    from api.main import app
    from shared.schemas import AnalyticsSummary
    resp = TestClient(app).get("/analytics/summary")
    assert resp.status_code == 200
    obj  = AnalyticsSummary(**resp.json())   # raises ValidationError if schema wrong
    assert obj.total_sections > 0


@skip_if_no_data
def test_api_search_sections():
    from fastapi.testclient import TestClient
    from api.main import app
    data = TestClient(app).get("/search/?q=find_all&target=sections").json()
    assert "results" in data
    assert "sections" in data["results"]
    assert data["total_matches"] >= 0


@skip_if_no_data
def test_api_pipeline_status():
    from fastapi.testclient import TestClient
    from api.main import app
    data = TestClient(app).get("/pipeline/status").json()
    assert "running" in data
    assert "last_run" in data