"""
pipeline/reporter.py
Owner: Hung (A)
Feature 8 — Final Report Generator

Produces two output artifacts:
  output/report/final_report.pdf     — full analytical report (reportlab)
  output/report/summary_tables.xlsx  — 5-sheet Excel workbook (openpyxl)
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from shared.constants import (
    ALL_CHART_PATHS,
    CHART_NAMES,
    FINAL_REPORT_PDF,
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


# Public entry point

def generate_all(
    pdf_path: Path = FINAL_REPORT_PDF,
    xlsx_path: Path = SUMMARY_TABLES_XLSX,
) -> tuple[Path, Path]:
    """Generate both report artifacts and return their paths."""
    ensure_dirs()
    sections = load_sections()
    links    = load_links()
    code     = load_code_examples()
    summary  = load_summary_stats()

    generate_pdf(sections, links, code, summary, pdf_path)
    generate_xlsx(sections, links, code, summary, xlsx_path)

    logger.info("Reports ready → %s | %s", pdf_path.name, xlsx_path.name)
    return pdf_path, xlsx_path


# PDF report

def generate_pdf(
    sections: pd.DataFrame,
    links: pd.DataFrame,
    code: pd.DataFrame,
    summary: dict,
    out: Path = FINAL_REPORT_PDF,
) -> Path:
    """
    Build the final analytical PDF report using reportlab.

    Report structure (8 required sections):
      1. Dataset Overview      — target URL, scraping date, row counts per CSV
      2. Scraping Method       — requests + BeautifulSoup4, parser choice, HTML structure
      3. Extracted Data Summary — column descriptions + sample rows per dataset
      4. Analysis Results      — all 10 analytics questions with values + tables
      5. Charts                — all 4 required charts embedded as images
      6. Key Findings          — bullet-point narrative of most interesting results
      7. Limitations           — network dependency, single-page source, parser quirks
      8. Conclusion            — summary paragraph
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Image, PageBreak, HRFlowable,
    )

    doc    = SimpleDocTemplate(str(out), pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    H1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, spaceAfter=12)
    H2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=14, spaceAfter=8)
    P  = styles["Normal"]
    P.spaceAfter = 6

    def add(text: str, style=P):
        story.append(Paragraph(text, style))

    def gap(height: float = 0.4):
        story.append(Spacer(1, height * cm))

    def rule():
        story.append(HRFlowable(width="100%", thickness=0.5,
                                 color=colors.grey, spaceAfter=6))

    # Cover 
    story.append(Spacer(1, 4 * cm))
    add("BeautifulSoup Documentation Analytics", H1)
    add("Final Project Report — AIO Program · FPT University", styles["Heading3"])
    gap(0.6)
    add(f"Generated: {utc_now_iso()[:10]}")
    add("Target: https://www.crummy.com/software/BeautifulSoup/bs4/doc/")
    story.append(PageBreak())

    # 1. Dataset Overview 
    add("1. Dataset Overview", H1); rule()
    add(f"Source URL: https://www.crummy.com/software/BeautifulSoup/bs4/doc/")
    add(f"Sections extracted : {len(sections)}")
    add(f"Links extracted    : {len(links)}")
    add(f"Code examples      : {len(code)}")
    gap()

    # 2. Scraping Method ─
    add("2. Scraping Method", H1); rule()
    add("The pipeline uses the Python <b>requests</b> library to download the "
        "documentation HTML with a 20-second timeout and raises an HTTPError on "
        "any non-200 response. The raw HTML is saved locally before parsing so "
        "the network is only hit once. Parsing uses <b>BeautifulSoup 4</b> with "
        "the built-in <i>html.parser</i> backend — no external C dependency "
        "required. Sections are identified by h1/h2/h3 heading tags; content is "
        "collected by iterating next siblings until the next equal-or-higher "
        "heading. Code examples are extracted via <code>&lt;div "
        "class=\"highlight\"&gt;</code> blocks, which is the Sphinx markup "
        "pattern used by the documentation generator.")
    gap()

    # 3. Extracted Data Summary 
    add("3. Extracted Data Summary", H1); rule()

    for label, df, cols in [
        ("Sections",      sections, ["section_id","section_title","section_level","word_count"]),
        ("Links",         links,    ["link_text","link_type","section_title"]),
        ("Code Examples", code,     ["example_id","section_title","line_count"]),
    ]:
        add(f"<b>{label}</b> ({len(df)} rows)", styles["Heading3"])
        sample   = df[cols].head(5)
        tdata    = [list(sample.columns)] + sample.values.tolist()
        tdata    = [[str(c)[:40] for c in row] for row in tdata]
        col_w    = [3.5 * cm] * len(cols)
        tbl      = Table(tdata, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4C72B0")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F0F4FF")]),
            ("GRID",       (0,0), (-1,-1), 0.3, colors.grey),
            ("PADDING",    (0,0), (-1,-1), 4),
        ]))
        story.append(tbl)
        gap()

    story.append(PageBreak())

    # 4. Analysis Results ─
    add("4. Analysis Results", H1); rule()

    q_answers = [
        ("Q1 — Total sections",              str(summary.get("total_sections", "N/A"))),
        ("Q2 — Highest word count section",  summary.get("highest_wordcount_section","N/A")
                                             + f" ({summary.get('highest_wordcount_value','N/A')} words)"),
        ("Q3 — Most code examples section",  summary.get("most_code_examples_section","N/A")
                                             + f" ({summary.get('most_code_examples_count','N/A')} examples)"),
        ("Q4 — Most links section",          summary.get("most_links_section","N/A")
                                             + f" ({summary.get('most_links_count','N/A')} links)"),
        ("Q5 — Top 10 keywords",             ", ".join(
                                                 k["keyword"] for k in summary.get("top_10_keywords",[])
                                             )),
        ("Q6 — Link type counts",            " | ".join(
                                                 f"{t}: {c}" for t,c in
                                                 summary.get("link_type_counts",{}).items()
                                             )),
        ("Q7 — find_all() code examples",    str(summary.get("find_all_example_count","N/A"))),
        ("Q8 — get_text() code examples",    str(summary.get("get_text_example_count","N/A"))),
        ("Q9 — Average words/section",       str(summary.get("avg_words_per_section","N/A"))),
        ("Q10 — Sections with no code",      str(summary.get("sections_with_no_code","N/A"))),
    ]
    tdata = [["Question", "Answer"]] + q_answers
    tbl   = Table(tdata, colWidths=[7*cm, 10.5*cm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4C72B0")),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F0F4FF")]),
        ("GRID",       (0,0), (-1,-1), 0.3, colors.grey),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("PADDING",    (0,0), (-1,-1), 5),
        ("WORDWRAP",   (0,0), (-1,-1), True),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # 5. Charts 
    add("5. Charts", H1); rule()
    for chart_path in ALL_CHART_PATHS:
        if chart_path.exists():
            add(f"<b>{CHART_NAMES.get(chart_path.name, chart_path.stem)}</b>",
                styles["Heading3"])
            story.append(Image(str(chart_path), width=14*cm, height=8*cm))
            gap(0.5)

    story.append(PageBreak())

    # 6. Key Findings 
    add("6. Key Findings", H1); rule()
    kw_list = ", ".join(k["keyword"] for k in summary.get("top_10_keywords", [])[:5])
    findings = [
        f"The documentation contains <b>{summary.get('total_sections','N/A')} sections</b> "
        f"across three heading levels, with the section "
        f"<i>\"{summary.get('highest_wordcount_section','N/A')}\"</i> "
        f"containing the most content at "
        f"{summary.get('highest_wordcount_value','N/A')} words.",

        f"<b>find_all()</b> is the most demonstrated method, appearing in "
        f"{summary.get('find_all_example_count','N/A')} code examples, "
        f"confirming its central role in the BeautifulSoup API.",

        f"The most frequent technical keywords are: <b>{kw_list}</b> — "
        f"reflecting the library's core concepts of tags, strings, and tree navigation.",

        f"<b>{summary.get('sections_with_no_code','N/A')} sections</b> contain no code "
        f"examples, primarily introductory and installation sections.",
    ]
    for f in findings:
        add(f"• {f}")
        gap(0.2)
    gap()

    # 7. Limitations 
    add("7. Limitations", H1); rule()
    limitations = [
        "The pipeline requires a live internet connection for the initial HTML download. "
        "Network timeouts or upstream changes to the documentation page structure "
        "could cause failures.",
        "Analysis is based on a single-page documentation source. Conclusions about "
        "API usage patterns may not generalise to other libraries or documentation styles.",
        "Section boundary detection relies on h1/h2/h3 headings. Content not under "
        "a heading is attributed to the 'Unknown' section.",
        "Keyword frequency analysis uses simple word counting with a stopword list. "
        "It does not account for stemming, lemmatisation, or contextual meaning.",
    ]
    for lim in limitations:
        add(f"• {lim}")
        gap(0.2)
    gap()

    # 8. Conclusion 
    add("8. Conclusion", H1); rule()
    add("This project successfully demonstrates an end-to-end data engineering "
        "pipeline applied to technical documentation. Starting from a raw HTML page, "
        "the system extracts structured datasets covering sections, hyperlinks, and "
        "code examples; answers ten analytical questions using Pandas and NumPy; "
        "and presents results through both static charts and an interactive "
        "Streamlit web application backed by a FastAPI REST API. The modular "
        "pipeline architecture — collector → parser → extractor → analyzer → "
        "visualizer → reporter — ensures each stage is independently testable "
        "and maintainable.")

    doc.build(story)
    logger.info("PDF report saved → %s", out.name)
    return out


# Excel workbook

def generate_xlsx(
    sections: pd.DataFrame,
    links: pd.DataFrame,
    code: pd.DataFrame,
    summary: dict,
    out: Path = SUMMARY_TABLES_XLSX,
) -> Path:
    """
    Build summary_tables.xlsx with 5 sheets using openpyxl.

    Sheets:
      1. Sections          — full sections DataFrame
      2. Links             — full links DataFrame
      3. Code Examples     — full code_examples DataFrame
      4. Analytics Summary — question / answer pairs
      5. Top Keywords      — keyword / count pairs
    """
    with pd.ExcelWriter(str(out), engine="openpyxl") as writer:

        sections.to_excel(writer, sheet_name="Sections",      index=False)
        links.to_excel(   writer, sheet_name="Links",         index=False)
        code.to_excel(    writer, sheet_name="Code Examples", index=False)

        # Analytics summary sheet
        summary_rows = [
            ("Total sections",              summary.get("total_sections")),
            ("Highest word count section",  summary.get("highest_wordcount_section")),
            ("Highest word count value",    summary.get("highest_wordcount_value")),
            ("Most code examples section",  summary.get("most_code_examples_section")),
            ("Most code examples count",    summary.get("most_code_examples_count")),
            ("Most links section",          summary.get("most_links_section")),
            ("Most links count",            summary.get("most_links_count")),
            ("find_all() example count",    summary.get("find_all_example_count")),
            ("get_text() example count",    summary.get("get_text_example_count")),
            ("Average words per section",   summary.get("avg_words_per_section")),
            ("Sections with no code",       summary.get("sections_with_no_code")),
        ]
        for link_type, count in summary.get("link_type_counts", {}).items():
            summary_rows.append((f"Links — {link_type}", count))

        pd.DataFrame(summary_rows, columns=["Question", "Answer"]).to_excel(
            writer, sheet_name="Analytics Summary", index=False
        )

        # Top keywords sheet
        keywords = summary.get("top_10_keywords", [])
        pd.DataFrame(keywords).to_excel(
            writer, sheet_name="Top Keywords", index=False
        )

    logger.info("Excel workbook saved → %s", out.name)
    return out


# CLI

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    pdf, xlsx = generate_all()
    print(f"PDF  → {pdf}")
    print(f"XLSX → {xlsx}")
