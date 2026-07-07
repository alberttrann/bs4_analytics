"""
shared/constants.py
===================
Central location for every path, URL, column list, and enum value used
across the project. Import from here — never hardcode strings in feature files.

Ownership: Hung 
"""

from pathlib import Path

# Directory layout

BASE_DIR   = Path(__file__).resolve().parent.parent   # repo root
DATA_DIR   = BASE_DIR / "data"
RAW_DIR    = DATA_DIR / "raw"
PROC_DIR   = DATA_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
REPORT_DIR = OUTPUT_DIR / "report"

# Convenience list for ensure_dirs()
ALL_DIRS = [RAW_DIR, PROC_DIR, CHARTS_DIR, REPORT_DIR]

# Raw input

TARGET_URL   = "https://www.crummy.com/software/BeautifulSoup/bs4/doc/"
RAW_HTML_PATH = RAW_DIR / "beautifulsoup_doc.html"

# Processed CSV paths

SECTIONS_CSV       = PROC_DIR / "sections.csv"
LINKS_CSV          = PROC_DIR / "links.csv"
CODE_EXAMPLES_CSV  = PROC_DIR / "code_examples.csv"
SUMMARY_STATS_JSON = PROC_DIR / "summary_stats.json"

# CSV column definitions
# Must match SectionModel / LinkModel / CodeExampleModel in schemas.py

SECTION_COLS = [
    "section_id",
    "section_level",
    "section_title",
    "section_text",
    "word_count",
    "code_block_count",
    "link_count",
]

LINK_COLS = [
    "link_text",
    "href",
    "link_type",
    "section_title",
]

CODE_COLS = [
    "example_id",
    "section_title",
    "code_text",
    "line_count",
    "contains_find_all",
    "contains_find",
    "contains_select",
    "contains_get_text",
    "contains_requests",
]

# Link type enum values (used by link_classifier.py and tests)

LINK_TYPE_INTERNAL_ANCHOR    = "internal_anchor"
LINK_TYPE_EXTERNAL           = "external_link"
LINK_TYPE_DOCUMENTATION      = "documentation_link"
LINK_TYPE_IMAGE              = "image_link"
LINK_TYPE_EMPTY_OR_INVALID   = "empty_or_invalid"

LINK_TYPES = [
    LINK_TYPE_INTERNAL_ANCHOR,
    LINK_TYPE_EXTERNAL,
    LINK_TYPE_DOCUMENTATION,
    LINK_TYPE_IMAGE,
    LINK_TYPE_EMPTY_OR_INVALID,
]

# Output file names (charts)

CHART_WORD_COUNT      = CHARTS_DIR / "word_count_by_section.png"
CHART_CODE_BY_SECTION = CHARTS_DIR / "code_examples_by_section.png"
CHART_LINK_DIST       = CHARTS_DIR / "link_type_distribution.png"
CHART_LINECOUNT_HIST  = CHARTS_DIR / "code_linecount_hist.png"

ALL_CHART_PATHS = [
    CHART_WORD_COUNT,
    CHART_CODE_BY_SECTION,
    CHART_LINK_DIST,
    CHART_LINECOUNT_HIST,
]

CHART_NAMES = {
    CHART_WORD_COUNT.name:      "Top Sections by Word Count",
    CHART_CODE_BY_SECTION.name: "Code Examples by Section",
    CHART_LINK_DIST.name:       "Link Type Distribution",
    CHART_LINECOUNT_HIST.name:  "Code Example Line Count Distribution",
}

# Report output paths

FINAL_REPORT_PDF    = REPORT_DIR / "final_report.pdf"
SUMMARY_TABLES_XLSX = REPORT_DIR / "summary_tables.xlsx"

# Analytics — stopwords for keyword extraction
# in sync with analyzer.py _compute_top_keywords()

STOPWORDS = {
    "the", "a", "an", "and", "or", "is", "in", "to", "of", "for",
    "with", "that", "it", "this", "you", "can", "be", "are", "from",
    "by", "on", "as", "at", "if", "not", "but", "its", "will", "all",
    "one", "any", "has", "have", "was", "were", "into", "than", "then",
    "also", "each", "when", "there", "which", "your", "they", "them",
}

# HTTP

HTTP_TIMEOUT_SECONDS = 20
HTTP_USER_AGENT = (
    "Mozilla/5.0 (compatible; BS4-Analytics/1.0; "
    "+https://github.com/your-team/bs4_analytics)"
)
