"""
app/components/stat_cards.py
Owner: Hung (A)
Advanced — reusable metric card row for any page that needs a summary header.
"""

from __future__ import annotations
import streamlit as st


def render_summary_cards(summary: dict) -> None:
    """
    Render a row of st.metric cards from an AnalyticsSummary dict.
    Call after fetching GET /analytics/summary.
    """
    cols = st.columns(5)
    cols[0].metric("Sections",             summary.get("total_sections", "–"))
    cols[1].metric("find_all() examples",  summary.get("find_all_example_count", "–"))
    cols[2].metric("get_text() examples",  summary.get("get_text_example_count", "–"))
    cols[3].metric("Avg words / section",
                   f"{summary.get('avg_words_per_section', 0):.0f}")
    cols[4].metric("No-code sections",     summary.get("sections_with_no_code", "–"))


def render_pipeline_status_card(status: dict) -> None:
    """
    Render a compact status indicator from GET /pipeline/status.
    """
    if status.get("running"):
        st.info(" Pipeline is currently running...")
    elif status.get("last_run"):
        ts  = status["last_run"][:19].replace("T", " ")
        dur = status.get("last_run_duration_seconds")
        msg = f" Last run: {ts} UTC"
        if dur:
            msg += f" ({dur:.1f}s)"
        st.success(msg)
    else:
        st.warning(" Pipeline has never been run. Click ▶ Run Pipeline.")
