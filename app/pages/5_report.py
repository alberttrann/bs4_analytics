"""
app/pages/5_report.py
Download page - PDF report, Excel workbook, and individual chart PNGs.
"""
from __future__ import annotations
import sys
from pathlib import Path
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os

import streamlit as st

from shared.constants import ALL_CHART_PATHS, CHART_NAMES, FINAL_REPORT_PDF, SUMMARY_TABLES_XLSX

from app.config import API_BASE, WS_BASE

st.set_page_config(page_title="Report - BS4 Analytics", page_icon="📥")
st.title("📥 Download Reports")

# Final report - Markdown
st.subheader("Final analytical report")
MD_PATH = Path(__file__).resolve().parent.parent.parent / "output" / "report" / "final_report.md"
if MD_PATH.exists():
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()
    st.download_button(
        label="📄 Download final_report.md",
        data=md_content,
        file_name="final_report.md",
        mime="text/markdown",
    )
    with st.expander("Preview report"):
        st.markdown(md_content[:3000] + "\n\n*... (download for full report)*")
else:
    st.warning("Report not yet generated. Run the pipeline first.")

st.divider()

# Summary tables XLSX
st.subheader("Summary tables (Excel)")
if SUMMARY_TABLES_XLSX.exists():
    with open(SUMMARY_TABLES_XLSX, "rb") as f:
        st.download_button(
            label="📊 Download summary_tables.xlsx",
            data=f,
            file_name="summary_tables.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    st.caption("Contains 5 sheets: Sections · Links · Code Examples · "
               "Analytics Summary · Top Keywords")
else:
    st.warning("Excel workbook not yet generated. Run the pipeline first.")

st.divider()

# Individual chart downloads
st.subheader("Charts")
available = [p for p in ALL_CHART_PATHS if p.exists()]
if not available:
    st.warning("No charts found. Run the pipeline to generate them.")
else:
    for chart_path in available:
        col_img, col_btn = st.columns([3, 1])
        col_img.image(str(chart_path),
                      caption=CHART_NAMES.get(chart_path.name, chart_path.stem),
                      use_column_width=True)
        with open(chart_path, "rb") as f:
            col_btn.download_button(
                label=f"⬇ {chart_path.name}",
                data=f,
                file_name=chart_path.name,
                mime="image/png",
            )
        st.write("")
