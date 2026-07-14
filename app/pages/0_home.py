"""
app/pages/0_home.py
Home page - pipeline trigger with WebSocket live progress (polling fallback).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import time
import requests
import streamlit as st
from app.config import API_BASE, WS_BASE

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

# Pipeline trigger
st.subheader("Run pipeline")
st.caption(
    "Downloads the BS4 documentation, extracts all data, "
    "runs analytics, and generates reports. Takes ~30–60 seconds."
)

if "pipeline_triggered" not in st.session_state:
    st.session_state["pipeline_triggered"] = False
if "use_websocket" not in st.session_state:
    st.session_state["use_websocket"] = True   # try WS first

col_btn, col_mode = st.columns([1, 2])
with col_btn:
    run_btn = st.button("▶ Run Pipeline", type="primary",
                        disabled=st.session_state["pipeline_triggered"])
with col_mode:
    st.session_state["use_websocket"] = st.toggle(
        "Live streaming (WebSocket)",
        value=st.session_state["use_websocket"],
        help="Uncheck to use polling instead if WebSocket fails.",
    )

if run_btn:
    try:
        resp = requests.post(f"{API_BASE}/pipeline/run", timeout=5)
        body = resp.json()
        if body.get("status") == "already_running":
            st.info("Pipeline is already running.")
        else:
            st.session_state["pipeline_triggered"] = True
            st.rerun()
    except Exception as e:
        st.error(f"Cannot reach API: {e}")


# Progress display - WebSocket path
def _run_websocket_progress():
    """Stream pipeline stdout via WebSocket. Returns True if successful."""
    try:
        import websocket as ws_lib
    except ImportError:
        st.warning("`websocket-client` not installed - falling back to polling.\n"
                   "Run: `pip install websocket-client`")
        return False

    ws_url = f"{WS_BASE}/ws/pipeline-progress"
    bar      = st.progress(0, text="Connecting to pipeline…")
    log_box  = st.empty()
    logs: list[str] = []
    TOTAL = 7

    try:
        ws = ws_lib.create_connection(ws_url, timeout=120)
    except Exception as e:
        st.warning(f"WebSocket connection failed ({e}) - falling back to polling.")
        return False

    try:
        while True:
            try:
                msg = ws.recv()
            except Exception:
                break

            if not msg:
                break

            logs.append(msg)
            # Show rolling last 30 lines
            log_box.code("\n".join(logs[-30:]), language=None)

            # Advance progress bar
            done = sum(1 for l in logs if "Done" in l or "complete" in l.lower())
            pct  = min(done / TOTAL, 1.0)
            bar.progress(pct, text=msg[:80])

    finally:
        try:
            ws.close()
        except Exception:
            pass

    bar.progress(1.0, text="✅ Pipeline complete!")
    return True


# Progress display - polling path
def _run_polling_progress():
    """Poll GET /pipeline/status every second until done."""
    bar       = st.progress(0, text="Starting pipeline…")
    stage_box = st.empty()
    TOTAL     = 7

    while True:
        try:
            status = requests.get(f"{API_BASE}/pipeline/status", timeout=3).json()
        except Exception:
            time.sleep(1)
            continue

        done  = status.get("stages_done", 0)
        stage = status.get("current_stage", "")
        pct   = min(done / TOTAL, 1.0)

        bar.progress(pct, text=f"[{done}/{TOTAL}] {stage}")
        stage_box.info(f"Current stage: **{stage}**")

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
            break

        time.sleep(1)
        st.rerun()


# Run the progress mechanism
if st.session_state["pipeline_triggered"]:
    if st.session_state["use_websocket"]:
        success = _run_websocket_progress()
        if not success:
            # WebSocket failed - fall through to polling
            st.session_state["use_websocket"] = False
            _run_polling_progress()
    else:
        _run_polling_progress()

    st.session_state["pipeline_triggered"] = False

st.divider()

# Quick stats
st.subheader("Quick stats")
try:
    summary = requests.get(f"{API_BASE}/analytics/summary", timeout=15).json()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sections",            summary.get("total_sections", "–"))
    c2.metric("find_all() examples", summary.get("find_all_example_count", "–"))
    c3.metric("get_text() examples", summary.get("get_text_example_count", "–"))
    c4.metric("Avg words/section",   f"{summary.get('avg_words_per_section', 0):.0f}")
    c5.metric("Sections (no code)",  summary.get("sections_with_no_code", "–"))
except Exception:
    st.info("Run the pipeline to populate stats.")

# Last run info
try:
    status = requests.get(f"{API_BASE}/pipeline/status", timeout=3).json()
    if status.get("last_run"):
        st.caption(
            f"Last run: {status['last_run'][:19].replace('T', ' ')} UTC  "
            f"({status.get('last_run_duration_seconds', '?')}s)"
        )
except Exception:
    pass