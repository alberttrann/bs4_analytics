"""
app/pages/0_home.py
Owner: Hung (A)
Advanced — Home page with live pipeline progress bar, dataset health
           indicators, quick-stat metric cards, and last-run timestamp.
"""

from __future__ import annotations

import os
import time

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_BASE  = API_BASE.replace("http://", "ws://").replace("https://", "wss://")

st.set_page_config(page_title="Home — BS4 Analytics", page_icon="🏠", layout="wide")
st.title("🏠 Home")

# Dataset health
st.subheader("Dataset status")
try:
    health = requests.get(f"{API_BASE}/health", timeout=3).json()
    cols   = st.columns(4)
    for i, (fname, present) in enumerate(health["data_files_present"].items()):
        icon = "✅" if present else "❌"
        cols[i % 4].metric(label=fname, value=icon)
    if not health["pipeline_ever_run"]:
        st.warning("Pipeline has not been run yet — click ▶ Run Pipeline below.")
except Exception as e:
    st.error(f"Cannot reach API: {e}")

st.divider()

# Pipeline trigger + live progress
st.subheader("Run pipeline")
st.caption("Downloads the BS4 documentation, extracts all data, runs analytics, "
           "and generates reports. Takes ~30 seconds.")

col_btn, col_status = st.columns([1, 3])
run_btn = col_btn.button("▶ Run Pipeline", type="primary",
                         disabled=st.session_state.get("pipeline_running", False))

if run_btn:
    try:
        resp = requests.post(f"{API_BASE}/pipeline/run", timeout=5)
        if resp.status_code == 202:
            st.session_state["pipeline_running"] = True
        elif resp.json().get("status") == "already_running":
            st.info("Pipeline is already running.")
        else:
            st.error(f"Failed to start pipeline: {resp.text}")
    except Exception as e:
        st.error(f"Cannot reach API: {e}")

if st.session_state.get("pipeline_running", False):
    import websocket as ws_lib

    bar     = st.progress(0, text="Connecting to pipeline...")
    log_box = st.empty()
    logs: list[str] = []
    TOTAL_STAGES = 6

    try:
        ws = ws_lib.create_connection(
            f"{WS_BASE}/ws/pipeline-progress",
            timeout=120,
        )
        while True:
            msg = ws.recv()
            if not msg:
                break
            logs.append(msg)
            log_box.code("\n".join(logs[-30:]), language=None)
            done_count = sum(1 for l in logs if "done" in l.lower())
            bar.progress(
                min(done_count / TOTAL_STAGES, 1.0),
                text=msg,
            )
        ws.close()
        bar.progress(1.0, text="Pipeline complete!")
        st.success("Pipeline finished! Refresh any page to see updated data.")
    except Exception as e:
        st.error(f"WebSocket error: {e}")
    finally:
        st.session_state["pipeline_running"] = False

st.divider()

# Quick-stat metric cards
st.subheader("Quick stats")
try:
    summary = requests.get(f"{API_BASE}/analytics/summary", timeout=10).json()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sections",           summary["total_sections"])
    c2.metric("find_all() examples",summary["find_all_example_count"])
    c3.metric("get_text() examples",summary["get_text_example_count"])
    c4.metric("Avg words/section",  f"{summary['avg_words_per_section']:.0f}")
    c5.metric("Sections (no code)", summary["sections_with_no_code"])
except Exception:
    st.info("Run the pipeline to populate stats.")

# Last pipeline run info
try:
    status = requests.get(f"{API_BASE}/pipeline/status", timeout=3).json()
    if status["last_run"]:
        st.caption(
            f"Last pipeline run: {status['last_run'][:19].replace('T',' ')} UTC  "
            f"({status['last_run_duration_seconds']:.1f}s)"
        )
except Exception:
    pass
