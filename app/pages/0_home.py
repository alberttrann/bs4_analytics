"""
app/pages/0_home.py
Owner: Hung (A)
Advanced - Home page with live pipeline progress bar, dataset health
           indicators, quick-stat metric cards, and last-run timestamp.
"""
from __future__ import annotations
import sys
from pathlib import Path
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os
import time

import requests
import streamlit as st

from app.config import API_BASE, WS_BASE
WS_BASE  = API_BASE.replace("http://", "ws://").replace("https://", "wss://")

st.set_page_config(page_title="Home - BS4 Analytics", page_icon="🏠", layout="wide")
st.title("🏠 Home")

# Dataset health
st.subheader("Dataset status")
try:
    health = requests.get(f"{API_BASE}/health", timeout=3).json()
    cols   = st.columns(4)
    for i, (fname, present) in enumerate(health["data_files_present"].items()):
        cols[i].metric(label=fname, value="✅" if present else "❌")
    if not health["pipeline_ever_run"]:
        st.warning("Pipeline has not been run yet - click ▶ Run Pipeline below.")
except Exception as e:
    st.error(f"Cannot reach API: {e}")

st.divider()

# Pipeline trigger + polling progress
st.subheader("Run pipeline")
st.caption("Downloads the BS4 documentation, extracts all data, runs analytics, and generates reports.")

STAGES = ["Collecting HTML", "Parsing HTML", "Extracting data",
          "Running analytics", "Generating charts", "Generating report"]

if st.button("▶ Run Pipeline", type="primary"):
    try:
        resp = requests.post(f"{API_BASE}/pipeline/run", timeout=5)
        if resp.json().get("status") == "already_running":
            st.info("Pipeline is already running.")
        else:
            st.session_state["pipeline_triggered"] = True
    except Exception as e:
        st.error(f"Cannot reach API: {e}")

if st.session_state.get("pipeline_triggered"):
    bar      = st.progress(0, text="Starting pipeline...")
    status_box = st.empty()

    while True:
        try:
            status = requests.get(f"{API_BASE}/pipeline/status", timeout=3).json()
        except Exception:
            time.sleep(1)
            continue

        done  = status.get("stages_done", 0)
        total = status.get("total_stages", 6)
        stage = status.get("current_stage", "")

        progress = min(done / total, 1.0)
        bar.progress(progress, text=f"[{done}/{total}] {stage}")
        status_box.info(f"Current stage: **{stage}**")

        if not status.get("running"):
            if "Error" in stage:
                st.error(f"Pipeline failed: {stage}")
            else:
                bar.progress(1.0, text="✅ Complete!")
                st.success(
                    f"Pipeline finished in "
                    f"{status.get('last_run_duration_seconds', '?')}s - "
                    "refresh any page to see updated data."
                )
            st.session_state["pipeline_triggered"] = False
            break

        time.sleep(1)
        st.rerun()

st.divider()

# Quick stats
st.subheader("Quick stats")
try:
    summary = requests.get(f"{API_BASE}/analytics/summary", timeout=15).json()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sections",            summary["total_sections"])
    c2.metric("find_all() examples", summary["find_all_example_count"])
    c3.metric("get_text() examples", summary["get_text_example_count"])
    c4.metric("Avg words/section",   f"{summary['avg_words_per_section']:.0f}")
    c5.metric("Sections (no code)",  summary["sections_with_no_code"])
except Exception:
    st.info("Run the pipeline to populate stats.")

# Last run info
try:
    status = requests.get(f"{API_BASE}/pipeline/status", timeout=3).json()
    if status.get("last_run"):
        st.caption(
            f"Last run: {status['last_run'][:19].replace('T',' ')} UTC  "
            f"({status.get('last_run_duration_seconds', '?')}s)"
        )
except Exception:
    pass
