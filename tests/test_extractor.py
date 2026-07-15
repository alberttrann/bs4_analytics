"""
tests/test_extractor.py
Unit tests for pipeline/extractor.py - feeds a known HTML fixture.
Validates CSV column schemas and link type coverage.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pandas as pd
from bs4 import BeautifulSoup
from shared.constants import SECTION_COLS, LINK_COLS, LINK_TYPES

# HTML designed to produce all 5 link types and clear section structure
FIXTURE_HTML = """
<html><body>
<h1>Quick Start</h1>
<p>Learn Beautiful Soup with this guide.</p>
<a href="#installing-beautiful-soup">Install here</a>
<a href="https://pypi.org/">PyPI</a>
<a href="https://www.crummy.com/software/BeautifulSoup/bs4/doc/">Docs</a>
<a href="_images/logo.png">Logo</a>
<a href="">Empty link</a>
<div class="highlight"><pre>soup.find_all('a')</pre></div>

<h2>Installing Beautiful Soup</h2>
<p>Use pip to install.</p>
<a href="http://lxml.de/">lxml</a>
<div class="highlight"><pre>pip install beautifulsoup4</pre></div>

<h3>Installing a Parser</h3>
<p>Choose lxml for speed.</p>
</body></html>
"""


@pytest.fixture
def soup():
    return BeautifulSoup(FIXTURE_HTML, "html.parser")


@pytest.fixture
def sections_df(soup, tmp_path, monkeypatch):
    """Run extract_sections against fixture soup, redirecting CSV output."""
    from shared import constants as c
    monkeypatch.setattr(c, "SECTIONS_CSV", tmp_path / "sections.csv")
    monkeypatch.setattr(c, "LINKS_CSV",    tmp_path / "links.csv")
    from pipeline.extractor import extract_sections
    return extract_sections(soup)


@pytest.fixture
def links_df(soup, sections_df, tmp_path, monkeypatch):
    from shared import constants as c
    monkeypatch.setattr(c, "SECTIONS_CSV", tmp_path / "sections.csv")
    monkeypatch.setattr(c, "LINKS_CSV",    tmp_path / "links.csv")
    from pipeline.extractor import extract_links
    return extract_links(soup, sections_df)


class TestExtractSections:

    def test_returns_dataframe(self, sections_df):
        assert isinstance(sections_df, pd.DataFrame)

    def test_has_correct_columns(self, sections_df):
        assert set(SECTION_COLS) == set(sections_df.columns)

    def test_not_empty(self, sections_df):
        assert len(sections_df) > 0

    def test_section_levels_valid(self, sections_df):
        assert sections_df["section_level"].isin([1, 2, 3]).all()

    def test_word_counts_non_negative(self, sections_df):
        assert (sections_df["word_count"] >= 0).all()

    def test_section_titles_not_empty(self, sections_df):
        assert sections_df["section_title"].str.strip().ne("").all()

    def test_quick_start_present(self, sections_df):
        assert "Quick Start" in sections_df["section_title"].values


class TestExtractLinks:

    def test_returns_dataframe(self, links_df):
        assert isinstance(links_df, pd.DataFrame)

    def test_has_correct_columns(self, links_df):
        assert set(LINK_COLS) == set(links_df.columns)

    def test_not_empty(self, links_df):
        assert len(links_df) > 0

    def test_all_five_link_types_present(self, links_df):
        """The fixture HTML is designed to contain all 5 types."""
        found = set(links_df["link_type"].unique())
        for lt in LINK_TYPES:
            assert lt in found, \
                f"Link type '{lt}' missing. Found: {found}"

    def test_link_types_all_valid(self, links_df):
        assert links_df["link_type"].isin(LINK_TYPES).all()

    def test_no_pilcrow_in_link_text(self, links_df):
        """¶ symbols should be stripped from link text."""
        assert not links_df["link_text"].str.contains("¶").any()