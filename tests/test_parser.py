"""
tests/test_parser.py
Owner: Duong (D)
Unit tests for pipeline/parser.py - uses sample.html fixture (minimal BS4-style HTML).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from bs4 import BeautifulSoup
from shared.constants import SECTION_COLS

# Minimal HTML that mirrors the real BS4 doc structure
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>BS4 Test</title></head>
<body>
<h1>Quick Start</h1>
<p>Here is an example document used throughout this documentation.</p>
<div class="highlight"><pre>soup = BeautifulSoup(html, 'html.parser')</pre></div>
<a href="#installing-beautiful-soup">Install</a>
<a href="https://pypi.org/">PyPI</a>

<h2>Installing Beautiful Soup</h2>
<p>Install with pip: pip install beautifulsoup4</p>
<div class="highlight"><pre>pip install beautifulsoup4</pre></div>

<h3>Installing a Parser</h3>
<p>Use lxml for speed.</p>
<a href="http://lxml.de/">lxml</a>

<h1>Kinds of Objects</h1>
<p>BeautifulSoup transforms HTML into a tree of Python objects.</p>
</body>
</html>
"""


@pytest.fixture
def sample_soup():
    return BeautifulSoup(SAMPLE_HTML, "html.parser")


@pytest.fixture
def sample_html_file(tmp_path):
    f = tmp_path / "sample.html"
    f.write_text(SAMPLE_HTML, encoding="utf-8")
    return f


class TestParseHtml:

    def test_returns_beautifulsoup_object(self, sample_html_file):
        from pipeline.parser import parse_html
        soup = parse_html(sample_html_file)
        assert isinstance(soup, BeautifulSoup)

    def test_raises_file_not_found_for_missing_file(self, tmp_path):
        from pipeline.parser import parse_html
        with pytest.raises(FileNotFoundError):
            parse_html(tmp_path / "nonexistent.html")

    def test_finds_headings(self, sample_html_file):
        from pipeline.parser import parse_html
        soup = parse_html(sample_html_file)
        assert len(soup.find_all(["h1", "h2", "h3"])) == 4

    def test_finds_code_blocks(self, sample_html_file):
        from pipeline.parser import parse_html
        soup = parse_html(sample_html_file)
        assert len(soup.find_all("div", class_="highlight")) == 2


class TestExtractSectionTree:

    def test_returns_list_of_dicts(self, sample_soup):
        from pipeline.parser import extract_section_tree
        sections = extract_section_tree(sample_soup)
        assert isinstance(sections, list)
        assert len(sections) > 0
        assert isinstance(sections[0], dict)

    def test_all_required_columns_present(self, sample_soup):
        from pipeline.parser import extract_section_tree
        sections = extract_section_tree(sample_soup)
        for sec in sections:
            for col in SECTION_COLS:
                assert col in sec, f"Missing column '{col}' in {sec}"

    def test_section_levels_are_1_2_or_3(self, sample_soup):
        from pipeline.parser import extract_section_tree
        sections = extract_section_tree(sample_soup)
        for s in sections:
            assert s["section_level"] in (1, 2, 3), \
                f"Invalid level {s['section_level']} for '{s['section_title']}'"

    def test_section_ids_are_sequential_from_zero(self, sample_soup):
        from pipeline.parser import extract_section_tree
        sections = extract_section_tree(sample_soup)
        ids = [s["section_id"] for s in sections]
        assert ids == list(range(len(ids))), f"Non-sequential IDs: {ids}"

    def test_word_counts_are_non_negative(self, sample_soup):
        from pipeline.parser import extract_section_tree
        sections = extract_section_tree(sample_soup)
        for s in sections:
            assert s["word_count"] >= 0

    def test_quick_start_section_found(self, sample_soup):
        from pipeline.parser import extract_section_tree
        sections = extract_section_tree(sample_soup)
        titles = [s["section_title"] for s in sections]
        assert any("Quick Start" in t for t in titles), \
            f"'Quick Start' not found in {titles}"

    def test_finds_multiple_heading_levels(self, sample_soup):
        from pipeline.parser import extract_section_tree
        sections = extract_section_tree(sample_soup)
        levels_found = {s["section_level"] for s in sections}
        assert 1 in levels_found, "No H1 sections found"
        assert 2 in levels_found, "No H2 sections found"
