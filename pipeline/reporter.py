"""
pipeline/reporter.py
Feature 8 - Report Generator
Produces:
  output/report/final_report.md   - Markdown report with embedded chart refs
  output/report/summary_tables.xlsx - 5-sheet Excel workbook
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from shared.constants import (
    ALL_CHART_PATHS,
    CHART_NAMES,
    REPORT_DIR,
    SUMMARY_TABLES_XLSX,
)
from shared.utils import (
    ensure_dirs,
    load_code_examples,
    load_links,
    load_sections,
    load_summary_stats,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

FINAL_REPORT_MD = REPORT_DIR / "final_report.md"


def generate_all(
    md_path: Path = FINAL_REPORT_MD,
    xlsx_path: Path = SUMMARY_TABLES_XLSX,
) -> tuple[Path, Path]:
    """Generate Markdown report and Excel workbook."""
    ensure_dirs()
    sections = load_sections()
    links    = load_links()
    code     = load_code_examples()
    summary  = load_summary_stats()

    generate_md(sections, links, code, summary, md_path)
    generate_xlsx(sections, links, code, summary, xlsx_path)

    logger.info("Reports ready → %s | %s", md_path.name, xlsx_path.name)
    return md_path, xlsx_path


def generate_md(
    sections: pd.DataFrame,
    links: pd.DataFrame,
    code: pd.DataFrame,
    summary: dict,
    out: Path = FINAL_REPORT_MD,
) -> Path:
    """Build the analytical report as a Markdown file."""

    lines = []

    def h(level: int, text: str):
        lines.append(f"\n{'#' * level} {text}\n")

    def p(text: str):
        lines.append(f"{text}\n")

    def rule():
        lines.append("\n---\n")

    def table(headers: list, rows: list):
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in rows:
            lines.append("| " + " | ".join(str(c) for c in row) + " |")
        lines.append("")

    #  Cover 
    h(1, "BeautifulSoup Documentation Analytics - Final Report")
    p(f"**Generated:** {utc_now_iso()[:10]}")
    p(f"**Source:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/")
    rule()

    #  1. Dataset Overview 
    h(2, "1. Dataset Overview")
    table(
        ["Dataset", "Rows", "Description"],
        [
            ["sections.csv",      len(sections), "Documentation sections by heading"],
            ["links.csv",         len(links),    "All hyperlinks, classified by type"],
            ["code_examples.csv", len(code),     "Python code blocks with method flags"],
        ]
    )

    #  2. Scraping Method 
    h(2, "2. Scraping Method")
    p(
        "The pipeline uses Python **requests** to download the documentation HTML "
        "with a 20-second timeout, raising an error on any non-200 response. "
        "The raw HTML is saved locally so the network is only hit once. "
        "Parsing uses **BeautifulSoup 4** with the `html.parser` backend. "
        "Sections are identified by h1/h2/h3 headings; content is collected by "
        "iterating next siblings until the next equal-or-higher heading. "
        "Code examples are found via `<div class=\"highlight\">` blocks (Sphinx markup). "
        "Links are extracted from all `<a>` tags and classified into 5 types."
    )

    #  3. Extracted Data Summary 
    h(2, "3. Extracted Data Summary")

    h(3, "Sections (first 5 rows)")
    table(
        ["ID", "Level", "Title", "Words", "Code blocks", "Links"],
        [
            [r.section_id, f"H{r.section_level}", r.section_title[:40],
             r.word_count, r.code_block_count, r.link_count]
            for r in sections.head(5).itertuples()
        ]
    )

    h(3, "Links - type breakdown")
    link_counts = links["link_type"].value_counts()
    table(
        ["Link type", "Count", "%"],
        [
            [lt, int(link_counts.get(lt, 0)),
             f"{link_counts.get(lt, 0) / len(links) * 100:.1f}%"]
            for lt in ["internal_anchor", "external_link",
                       "documentation_link", "image_link", "empty_or_invalid"]
        ]
    )

    h(3, "Code examples - method usage")
    bool_cols = ["contains_find_all", "contains_find", "contains_select",
                 "contains_get_text", "contains_requests"]
    labels    = ["find_all()", "find()", "select()", "get_text()", "requests"]
    table(
        ["Method", "Examples using it", "% of total"],
        [
            [label, int(code[col].astype(bool).sum()),
             f"{code[col].astype(bool).sum() / len(code) * 100:.1f}%"]
            for col, label in zip(bool_cols, labels)
        ]
    )

    #  4. Analysis Results 
    h(2, "4. Analysis Results")
    qa_rows = [
        ["Q1", "Total sections", str(summary.get("total_sections", "–"))],
        ["Q2", "Highest word count section",
         f"{summary.get('highest_wordcount_section','–')} "
         f"({summary.get('highest_wordcount_value','–')} words)"],
        ["Q3", "Most code examples section",
         f"{summary.get('most_code_examples_section','–')} "
         f"({summary.get('most_code_examples_count','–')} examples)"],
        ["Q4", "Most links section",
         f"{summary.get('most_links_section','–')} "
         f"({summary.get('most_links_count','–')} links)"],
        ["Q5", "Top 10 keywords",
         ", ".join(k["keyword"] for k in summary.get("top_10_keywords", []))],
        ["Q6", "Link type counts",
         " | ".join(f"{t}: {c}" for t, c in
                    summary.get("link_type_counts", {}).items())],
        ["Q7", "find_all() code examples", str(summary.get("find_all_example_count","–"))],
        ["Q8", "get_text() code examples", str(summary.get("get_text_example_count","–"))],
        ["Q9", "Average words per section", str(summary.get("avg_words_per_section","–"))],
        ["Q10","Sections with no code blocks", str(summary.get("sections_with_no_code","–"))],
    ]
    if summary.get("adv_avg_readability_score"):
        qa_rows.append(["ADV", "Mean Flesch readability score",
                        str(summary["adv_avg_readability_score"])])
    table(["#", "Question", "Answer"], qa_rows)

    #  5. Charts 
    h(2, "5. Charts")
    API_BASE = "http://localhost:8001"
    for chart_path in ALL_CHART_PATHS:
        if chart_path.exists():
            name = CHART_NAMES.get(chart_path.name, chart_path.stem)
            url  = f"{API_BASE}/static/charts/{chart_path.name}"
            h(3, name)
            lines.append(f"![{name}]({url})\n")
        else:
            p(f"*{chart_path.name} - not yet generated*")

    #  6. Key Findings 
    h(2, "6. Key Findings")
    kw_top5 = ", ".join(
        f"**{k['keyword']}**"
        for k in summary.get("top_10_keywords", [])[:5]
    )
    findings = [
        f"The documentation has **{summary.get('total_sections','?')} sections** "
        f"across three heading levels.",

        f"The longest section is **\"{summary.get('highest_wordcount_section','?')}\"** "
        f"with {summary.get('highest_wordcount_value','?')} words.",

        f"`find_all()` is the most-demonstrated method, appearing in "
        f"**{summary.get('find_all_example_count','?')} code examples**.",

        f"The top 5 keywords are {kw_top5} - reflecting the library's core concepts.",

        f"**{summary.get('sections_with_no_code','?')} sections** contain no code examples "
        f"(primarily introductory/installation sections).",
    ]
    if summary.get("adv_top_similar_pairs"):
        pair = summary["adv_top_similar_pairs"][0]
        findings.append(
            f"Most similar section pair: **\"{pair[0]}\"** and **\"{pair[1]}\"** "
            f"(cosine similarity: {pair[2]:.3f})."
        )
    for f in findings:
        p(f"- {f}")

    #  7. Limitations 
    h(2, "7. Limitations")
    for lim in [
        "Requires a live internet connection for initial HTML download.",
        "Analysis is based on a single-page documentation source.",
        "Section boundary detection relies on h1/h2/h3 heading structure. "
        "Content before the first heading is attributed to 'Unknown'.",
        "Keyword frequency uses simple counting without stemming or lemmatisation.",
    ]:
        p(f"- {lim}")

    #  8. Conclusion 
    h(2, "8. Conclusion")
    p(
        "This project demonstrates an end-to-end data engineering pipeline applied "
        "to technical documentation. Starting from a raw HTML page, the system "
        "extracts structured datasets, answers ten analytical questions, and presents "
        "results through an interactive Streamlit web application backed by a FastAPI "
        "REST API. The modular architecture - collector → parser → extractor → "
        "analyzer → visualizer → reporter - ensures each stage is independently "
        "testable and maintainable."
    )

    out.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Markdown report saved → %s", out.name)
    print(f"[reporter] Saved {out.name}")
    return out


def generate_xlsx(
    sections: pd.DataFrame,
    links: pd.DataFrame,
    code: pd.DataFrame,
    summary: dict,
    out: Path = SUMMARY_TABLES_XLSX,
) -> Path:
    """Build summary_tables.xlsx with 5 sheets."""
    with pd.ExcelWriter(str(out), engine="openpyxl") as writer:
        sections.to_excel(writer, sheet_name="Sections",      index=False)
        links.to_excel(   writer, sheet_name="Links",         index=False)
        code.to_excel(    writer, sheet_name="Code Examples", index=False)

        summary_rows = [
            ("Total sections",             summary.get("total_sections")),
            ("Highest word count section", summary.get("highest_wordcount_section")),
            ("Highest word count value",   summary.get("highest_wordcount_value")),
            ("Most code examples section", summary.get("most_code_examples_section")),
            ("Most code examples count",   summary.get("most_code_examples_count")),
            ("Most links section",         summary.get("most_links_section")),
            ("Most links count",           summary.get("most_links_count")),
            ("find_all() example count",   summary.get("find_all_example_count")),
            ("get_text() example count",   summary.get("get_text_example_count")),
            ("Average words per section",  summary.get("avg_words_per_section")),
            ("Sections with no code",      summary.get("sections_with_no_code")),
            ("Mean readability score",     summary.get("adv_avg_readability_score")),
        ]
        for lt, cnt in summary.get("link_type_counts", {}).items():
            summary_rows.append((f"Links - {lt}", cnt))

        pd.DataFrame(summary_rows, columns=["Metric", "Value"]).to_excel(
            writer, sheet_name="Analytics Summary", index=False
        )

        kw = summary.get("top_10_keywords", [])
        pd.DataFrame(kw).to_excel(
            writer, sheet_name="Top Keywords", index=False
        )

    logger.info("Excel workbook saved → %s", out.name)
    print(f"[reporter] Saved {out.name}")
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    md, xlsx = generate_all()
    print(f"MD   → {md}")
    print(f"XLSX → {xlsx}")