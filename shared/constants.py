"""
shared/constants.py
Every path, URL, column list, and enum used across the project.
No other file hardcodes these values - always import from here.
"""

from pathlib import Path

# Directory layout
BASE_DIR   = Path(__file__).resolve().parent.parent
DATA_DIR   = BASE_DIR / "data"
RAW_DIR    = DATA_DIR / "raw"
PROC_DIR   = DATA_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
REPORT_DIR = OUTPUT_DIR / "report"

ALL_DIRS = [RAW_DIR, PROC_DIR, CHARTS_DIR, REPORT_DIR]

# Source
TARGET_URL    = "https://www.crummy.com/software/BeautifulSoup/bs4/doc/"
RAW_HTML_PATH = RAW_DIR / "beautifulsoup_doc.html"

HTTP_TIMEOUT_SECONDS = 20

# Processed files
SECTIONS_CSV       = PROC_DIR / "sections.csv"
LINKS_CSV          = PROC_DIR / "links.csv"
CODE_EXAMPLES_CSV  = PROC_DIR / "code_examples.csv"
SUMMARY_STATS_JSON = PROC_DIR / "summary_stats.json"

# CSV column definitions  (match Pydantic models in schemas.py)
SECTION_COLS = [
    "section_id", "section_level", "section_title", "section_text",
    "word_count", "code_block_count", "link_count",
]

LINK_COLS = [
    "link_text", "href", "link_type", "section_title",
]

CODE_COLS = [
    "example_id", "section_title", "code_text", "line_count",
    "contains_find_all", "contains_find", "contains_select",
    "contains_get_text", "contains_requests",
]

# Link type enum
LINK_TYPE_INTERNAL_ANCHOR  = "internal_anchor"
LINK_TYPE_EXTERNAL         = "external_link"
LINK_TYPE_DOCUMENTATION    = "documentation_link"
LINK_TYPE_IMAGE            = "image_link"
LINK_TYPE_EMPTY_OR_INVALID = "empty_or_invalid"

LINK_TYPES = [
    LINK_TYPE_INTERNAL_ANCHOR,
    LINK_TYPE_EXTERNAL,
    LINK_TYPE_DOCUMENTATION,
    LINK_TYPE_IMAGE,
    LINK_TYPE_EMPTY_OR_INVALID,
]

# Chart output paths
CHART_WORD_COUNT       = CHARTS_DIR / "word_count_by_section.png"
CHART_CODE_BY_SECTION  = CHARTS_DIR / "code_examples_by_section.png"
CHART_LINK_DIST        = CHARTS_DIR / "link_type_distribution.png"
CHART_LINECOUNT_HIST   = CHARTS_DIR / "code_linecount_hist.png"

# Advanced charts
CHART_TFIDF_KEYWORDS   = CHARTS_DIR / "tfidf_keywords.png"
CHART_READABILITY      = CHARTS_DIR / "readability_by_section.png"
CHART_SIMILARITY       = CHARTS_DIR / "similarity_heatmap.png"
CHART_METHOD_USAGE     = CHARTS_DIR / "method_usage.png"

ALL_CHART_PATHS = [
    CHART_WORD_COUNT,
    CHART_CODE_BY_SECTION,
    CHART_LINK_DIST,
    CHART_LINECOUNT_HIST,
    CHART_TFIDF_KEYWORDS,
    CHART_READABILITY,
    CHART_SIMILARITY,
    CHART_METHOD_USAGE,
]

CHART_NAMES = {
    CHART_WORD_COUNT.name:      "Top Sections by Word Count",
    CHART_CODE_BY_SECTION.name: "Code Examples by Section",
    CHART_LINK_DIST.name:       "Link Type Distribution",
    CHART_LINECOUNT_HIST.name:  "Code Example Line Count Distribution",
    CHART_TFIDF_KEYWORDS.name:  "TF-IDF Keyword Ranking vs Raw Frequency",
    CHART_READABILITY.name:     "Readability Score by Section (Flesch Reading Ease)",
    CHART_SIMILARITY.name:      "Section Cosine Similarity Heatmap",
    CHART_METHOD_USAGE.name:    "BS4 Method Usage in Code Examples",
}

# Report output paths
FINAL_REPORT_PDF    = REPORT_DIR / "final_report.pdf"
SUMMARY_TABLES_XLSX = REPORT_DIR / "summary_tables.xlsx"

# Analytics - stopwords for keyword extraction (Q5)
def _load_stopwords() -> set[str]:
    """
    Load English stopwords from NLTK. On first call, attempts to download
    the corpus automatically (quiet=True suppresses console output).
    Falls back to a hardcoded set so the rest of the project never breaks.
    """
    try:
        from nltk.corpus import stopwords as _sw
        return set(_sw.words("english"))
    except LookupError:
        # Corpus not yet downloaded - try once automatically
        try:
            import nltk
            nltk.download("stopwords", quiet=True)
            from nltk.corpus import stopwords as _sw
            return set(_sw.words("english"))
        except Exception:
            pass
    except ImportError:
        pass

    # Hardcoded fallback - used when NLTK is unavailable
    return {
        "the", "a", "an", "and", "or", "is", "in", "to", "of", "for",
        "with", "that", "it", "this", "you", "can", "be", "are", "from",
        "by", "on", "as", "at", "if", "not", "but", "its", "will", "all",
        "one", "any", "has", "have", "was", "were", "into", "than", "then",
        "also", "each", "when", "there", "which", "your", "they", "them",
        "just", "more", "some", "only", "very", "what", "been", "use",
        "used", "using", "here", "these", "those", "new", "same",
    }


STOPWORDS: set[str] = _load_stopwords()
