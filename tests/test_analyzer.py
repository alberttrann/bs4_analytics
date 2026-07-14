"""
tests/test_analyzer.py
Unit tests for pipeline/analyzer.py - feeds small synthetic DataFrames.
All 10 required analytics questions tested for correct output type and value.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pandas as pd
from shared.constants import LINK_TYPES


@pytest.fixture
def small_sections():
    return pd.DataFrame([
        {"section_id": 0, "section_level": 1, "section_title": "Quick Start",
         "section_text": "Learn BeautifulSoup quickly with find_all and get_text.",
         "word_count": 120, "code_block_count": 3, "link_count": 5},
        {"section_id": 1, "section_level": 2, "section_title": "Installing",
         "section_text": "Install with pip. Use lxml for speed.",
         "word_count": 80,  "code_block_count": 1, "link_count": 2},
        {"section_id": 2, "section_level": 1, "section_title": "Searching the tree",
         "section_text": "Use find_all to search. find returns one result.",
         "word_count": 500, "code_block_count": 10, "link_count": 15},
        {"section_id": 3, "section_level": 2, "section_title": "Output",
         "section_text": "Pretty print output.",
         "word_count": 30,  "code_block_count": 0, "link_count": 1},
        {"section_id": 4, "section_level": 3, "section_title": "Encodings",
         "section_text": "Handle encoding with care.",
         "word_count": 60,  "code_block_count": 0, "link_count": 3},
    ])


@pytest.fixture
def small_links():
    return pd.DataFrame([
        {"link_text": "PyPI",    "href": "https://pypi.org/",   "link_type": "external_link",     "section_title": "Quick Start"},
        {"link_text": "anchor",  "href": "#installing",          "link_type": "internal_anchor",   "section_title": "Quick Start"},
        {"link_text": "docs",    "href": "https://crummy.com/",  "link_type": "documentation_link","section_title": "Searching the tree"},
        {"link_text": "find",    "href": "#find-all",            "link_type": "internal_anchor",   "section_title": "Searching the tree"},
        {"link_text": "navigate","href": "#navigating",          "link_type": "internal_anchor",   "section_title": "Searching the tree"},
        {"link_text": "logo",    "href": "_images/logo.png",     "link_type": "image_link",        "section_title": "Installing"},
        {"link_text": "",        "href": "",                     "link_type": "empty_or_invalid",  "section_title": "Output"},
        {"link_text": "lxml",    "href": "http://lxml.de/",      "link_type": "external_link",     "section_title": "Installing"},
    ])


@pytest.fixture
def small_code():
    return pd.DataFrame([
        {"example_id": 0, "section_title": "Quick Start",
         "code_text": "soup.find_all('a')", "line_count": 1,
         "contains_find_all": True,  "contains_find": False,
         "contains_select": False,   "contains_get_text": False, "contains_requests": False},
        {"example_id": 1, "section_title": "Quick Start",
         "code_text": "soup.get_text()", "line_count": 1,
         "contains_find_all": False, "contains_find": False,
         "contains_select": False,   "contains_get_text": True,  "contains_requests": False},
        {"example_id": 2, "section_title": "Searching the tree",
         "code_text": "import requests\nrequests.get(url)", "line_count": 2,
         "contains_find_all": False, "contains_find": False,
         "contains_select": False,   "contains_get_text": False, "contains_requests": True},
        {"example_id": 3, "section_title": "Searching the tree",
         "code_text": "soup.find('b')", "line_count": 1,
         "contains_find_all": False, "contains_find": True,
         "contains_select": False,   "contains_get_text": False, "contains_requests": False},
        {"example_id": 4, "section_title": "Output",
         "code_text": "soup.select('p')", "line_count": 1,
         "contains_find_all": False, "contains_find": False,
         "contains_select": True,    "contains_get_text": False, "contains_requests": False},
    ])


@pytest.fixture
def result(small_sections, small_links, small_code, tmp_path, monkeypatch):
    json_path = tmp_path / "summary.json"
    monkeypatch.setattr("pipeline.analyzer.SUMMARY_STATS_JSON", json_path)
    from pipeline.analyzer import run_all_analytics
    return run_all_analytics(small_sections, small_links, small_code)


REQUIRED_KEYS = [
    "total_sections", "highest_wordcount_section", "highest_wordcount_value",
    "most_code_examples_section", "most_code_examples_count",
    "most_links_section", "most_links_count", "top_10_keywords",
    "link_type_counts", "find_all_example_count", "get_text_example_count",
    "avg_words_per_section", "sections_with_no_code",
]


class TestRunAllAnalytics:

    def test_all_required_keys_present(self, result):
        for key in REQUIRED_KEYS:
            assert key in result, f"Missing key: '{key}'"

    def test_q1_total_sections_correct(self, result, small_sections):
        assert result["total_sections"] == len(small_sections)

    def test_q2_highest_wordcount_is_searching(self, result):
        assert result["highest_wordcount_section"] == "Searching the tree"
        assert result["highest_wordcount_value"] == 500

    def test_q3_most_code_examples(self, result):
        # 2 examples in "Searching the tree" and 2 in "Quick Start"
        assert result["most_code_examples_count"] >= 2

    def test_q4_most_links(self, result):
        # "Searching the tree" has 3 links in the fixture
        assert result["most_links_section"] == "Searching the tree"
        assert result["most_links_count"] == 3

    def test_q5_top_keywords_is_list_of_dicts(self, result):
        kw = result["top_10_keywords"]
        assert isinstance(kw, list)
        assert len(kw) > 0
        for item in kw:
            assert "keyword" in item
            assert "count" in item
            assert isinstance(item["count"], int)

    def test_q6_link_type_counts_has_all_five(self, result):
        counts = result["link_type_counts"]
        for lt in LINK_TYPES:
            assert lt in counts, f"Missing link type: {lt}"

    def test_q7_find_all_count_correct(self, result):
        assert result["find_all_example_count"] == 1

    def test_q8_get_text_count_correct(self, result):
        assert result["get_text_example_count"] == 1

    def test_q9_avg_words_is_float(self, result):
        assert isinstance(result["avg_words_per_section"], float)
        assert result["avg_words_per_section"] == pytest.approx(158.0, abs=1)

    def test_q10_sections_with_no_code(self, result):
        # "Output" and "Encodings" have 0 code_block_count
        assert result["sections_with_no_code"] == 2

    def test_summary_json_written(self, result, tmp_path):
        import json
        json_file = tmp_path / "summary.json"
        assert json_file.exists(), f"summary.json not found at {json_file}"
        loaded = json.loads(json_file.read_text())
        assert loaded["total_sections"] == result["total_sections"]
