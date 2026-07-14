"""
app/pages/3_code.py
Code example browser - method filter, st.code display, calls GET /code-examples.
"""
from __future__ import annotations
import sys
from pathlib import Path
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os

import requests
import streamlit as st

from app.config import API_BASE, WS_BASE

st.set_page_config(page_title="Code Examples - BS4 Analytics",
                   page_icon="💻", layout="wide")
st.title("💻 Code Examples")

# Method filter
METHODS = {
    "contains_find_all": "find_all()",
    "contains_find":     "find()",
    "contains_select":   "select()",
    "contains_get_text": "get_text()",
    "contains_requests": "requests",
}

st.subheader("Filter by method used")
cols = st.columns(len(METHODS))
selected_method: str | None = None
for i, (col_name, label) in enumerate(METHODS.items()):
    if cols[i].checkbox(label, key=f"chk_{col_name}"):
        selected_method = col_name

col_section, col_sort = st.columns([3, 1])
with col_section:
    section_filter = st.text_input("Filter by section title", placeholder="e.g. Quick Start")
with col_sort:
    sort_by = st.selectbox("Sort by", ["example_id", "line_count", "section_title"])

# Fetch
@st.cache_data(ttl=60, show_spinner=False)
def fetch_code(method, section):
    params = {}
    if method:  params["method"]  = method
    if section: params["section"] = section
    try:
        r = requests.get(f"{API_BASE}/code-examples", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

data = fetch_code(selected_method, section_filter)

if "error" in data:
    st.error(f"Cannot load code examples: {data['error']}")
    st.stop()

items = data.get("items", [])

# Sort
if sort_by == "line_count":
    items = sorted(items, key=lambda x: x["line_count"], reverse=True)
elif sort_by == "section_title":
    items = sorted(items, key=lambda x: x["section_title"])

st.caption(f"Showing {len(items)} code example(s)")

# Display
if not items:
    st.info("No code examples match the current filters.")
else:
    for ex in items:
        method_flags = [
            label for col_name, label in METHODS.items() if ex.get(col_name)
        ]
        header = (
            f"[#{ex['example_id']}] **{ex['section_title']}**"
            f"  -  {ex['line_count']} lines"
        )
        if method_flags:
            header += f"  · `{'` · `'.join(method_flags)}`"

        with st.expander(header):
            st.code(ex["code_text"], language="python")
            if method_flags:
                st.caption("Methods used: " + " · ".join(f"`{m}`" for m in method_flags))
