"""
tests/test_api_routes.py
Integration tests for all API routes using FastAPI TestClient.
Uses monkeypatched data_service so no CSV files are needed.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from shared.constants import LINK_TYPES


# Synthetic DataFrames injected via patch

SECTIONS_DF = pd.DataFrame([
    {"section_id": 0, "section_level": 1, "section_title": "Quick Start",
     "section_text": "Learn BeautifulSoup.", "word_count": 100,
     "code_block_count": 2, "link_count": 3},
    {"section_id": 1, "section_level": 2, "section_title": "Installing",
     "section_text": "pip install beautifulsoup4", "word_count": 50,
     "code_block_count": 1, "link_count": 1},
    {"section_id": 2, "section_level": 1, "section_title": "Searching the tree",
     "section_text": "Use find_all to search the document.", "word_count": 300,
     "code_block_count": 8, "link_count": 10},
])

LINKS_DF = pd.DataFrame([
    {"link_text": "PyPI",   "href": "https://pypi.org/",  "link_type": "external_link",    "section_title": "Quick Start"},
    {"link_text": "anchor", "href": "#installing",         "link_type": "internal_anchor",  "section_title": "Quick Start"},
    {"link_text": "docs",   "href": "https://crummy.com/","link_type": "documentation_link","section_title": "Searching the tree"},
    {"link_text": "logo",   "href": "_images/logo.png",   "link_type": "image_link",        "section_title": "Installing"},
    {"link_text": "",       "href": "",                    "link_type": "empty_or_invalid",  "section_title": "Installing"},
])

CODE_DF = pd.DataFrame([
    {"example_id": 0, "section_title": "Quick Start",
     "code_text": "soup.find_all('a')", "line_count": 1,
     "contains_find_all": True,  "contains_find": False,
     "contains_select": False,   "contains_get_text": False, "contains_requests": False},
    {"example_id": 1, "section_title": "Searching the tree",
     "code_text": "soup.get_text()", "line_count": 1,
     "contains_find_all": False, "contains_find": False,
     "contains_select": False,   "contains_get_text": True,  "contains_requests": False},
])


@pytest.fixture(scope="function")
def client():
    """
    Pre-populate data_service._cache directly with fixture DataFrames.
    """
    import api.services.data_service as ds
    from api.main import app

    # Directly inject fixture data into the shared cache
    ds._cache.clear()
    ds._cache["sections"] = SECTIONS_DF.copy()
    ds._cache["links"]    = LINKS_DF.copy()
    ds._cache["code"]     = CODE_DF.copy()

    with TestClient(app) as c:
        yield c

    # Always clean up so real data is not left in cache for next test
    ds._cache.clear()


# Health

class TestHealth:

    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_has_status_ok(self, client):
        assert client.get("/health").json()["status"] == "ok"

    def test_has_data_files_present_field(self, client):
        data = client.get("/health").json()
        assert "data_files_present" in data
        assert isinstance(data["data_files_present"], dict)


# Sections  

class TestSectionsRoute:

    def test_get_sections_200(self, client):
        assert client.get("/sections/").status_code == 200

    def test_returns_paginated_structure(self, client):
        data = client.get("/sections/").json()
        assert "total" in data and "items" in data and "page" in data

    def test_total_matches_fixture(self, client):
        assert client.get("/sections/").json()["total"] == len(SECTIONS_DF)

    def test_get_by_id_200(self, client):
        assert client.get("/sections/0").status_code == 200

    def test_get_by_id_has_section_title(self, client):
        data = client.get("/sections/0").json()
        assert data["section_title"] == "Quick Start"

    def test_get_by_id_404_for_missing(self, client):
        assert client.get("/sections/9999").status_code == 404

    def test_level_filter(self, client):
        data = client.get("/sections/?level=1").json()
        for item in data["items"]:
            assert item["section_level"] == 1

    def test_search_filter(self, client):
        data = client.get("/sections/?search=Quick").json()
        assert data["total"] >= 1
        assert any("Quick" in item["section_title"] for item in data["items"])


# Links 

class TestLinksRoute:

    def test_get_links_200(self, client):
        assert client.get("/links/").status_code == 200

    def test_returns_all_links(self, client):
        data = client.get("/links/").json()
        assert data["total"] == len(LINKS_DF)

    def test_filter_by_link_type(self, client):
        data = client.get("/links/?link_type=external_link").json()
        for item in data["items"]:
            assert item["link_type"] == "external_link"

    def test_invalid_link_type_returns_400(self, client):
        assert client.get("/links/?link_type=invalid_type").status_code == 400

    def test_stats_returns_all_five_types(self, client):
        data = client.get("/links/stats").json()
        for lt in LINK_TYPES:
            assert lt in data, f"Missing link type in stats: {lt}"

    def test_stats_values_are_integers(self, client):
        data = client.get("/links/stats").json()
        for val in data.values():
            assert isinstance(val, int)


# Code Examples 

class TestCodeRoute:

    def test_get_code_200(self, client):
        assert client.get("/code-examples/").status_code == 200

    def test_returns_correct_total(self, client):
        assert client.get("/code-examples/").json()["total"] == len(CODE_DF)

    def test_filter_by_find_all(self, client):
        data = client.get("/code-examples/?method=contains_find_all").json()
        for item in data["items"]:
            assert item["contains_find_all"] is True

    def test_filter_by_get_text(self, client):
        data = client.get("/code-examples/?method=contains_get_text").json()
        for item in data["items"]:
            assert item["contains_get_text"] is True

    def test_invalid_method_returns_400(self, client):
        assert client.get("/code-examples/?method=contains_magic").status_code == 400

    def test_get_by_id_200(self, client):
        assert client.get("/code-examples/0").status_code == 200

    def test_get_by_id_404(self, client):
        assert client.get("/code-examples/9999").status_code == 404


# Pipeline

class TestPipelineRoute:

    def test_status_200(self, client):
        assert client.get("/pipeline/status").status_code == 200

    def test_status_has_running_field(self, client):
        data = client.get("/pipeline/status").json()
        assert "running" in data
        assert isinstance(data["running"], bool)

    def test_run_returns_202(self, client):
        with patch("pipeline.pipeline.run_all"):
            resp = client.post("/pipeline/run")
        assert resp.status_code == 202

    def test_run_returns_status_started(self, client):
        with patch("pipeline.pipeline.run_all"):
            data = client.post("/pipeline/run").json()
        assert data.get("status") in ("started", "already_running")


# Search 

class TestSearchRoute:

    def test_search_sections_200(self, client):
        resp = client.get("/search/?q=find&target=sections")
        assert resp.status_code == 200

    def test_search_returns_results_key(self, client):
        data = client.get("/search/?q=find&target=sections").json()
        assert "results" in data
        assert "sections" in data["results"]

    def test_search_too_short_returns_422(self, client):
        # min_length=2 on the q param
        assert client.get("/search/?q=a").status_code == 422

    def test_invalid_target_returns_400(self, client):
        assert client.get("/search/?q=find&target=invalid").status_code == 400
