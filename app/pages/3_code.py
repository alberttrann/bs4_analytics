"""
app/pages/3_code.py
Code example browser - method filter, fuzzy section title search (rapidfuzz),
                       syntax-highlighted display, calls GET /code-examples.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import requests
import streamlit as st
from app.config import API_BASE

st.set_page_config(page_title="Code Examples - BS4 Analytics",
                   page_icon="💻", layout="wide")
st.title("💻 Code Examples")

# Method filter checkboxes
METHODS = {
    "contains_find_all": "find_all()",
    "contains_find":     "find()",
    "contains_select":   "select()",
    "contains_get_text": "get_text()",
    "contains_requests": "requests",
}

st.subheader("Filter by method used")
method_cols = st.columns(len(METHODS))
selected_method: str | None = None
for i, (col_name, label) in enumerate(METHODS.items()):
    if method_cols[i].checkbox(label, key=f"chk_{col_name}"):
        selected_method = col_name
        break  # single-select: first checked wins

# Section title fuzzy search + sort
col_section, col_threshold, col_sort = st.columns([3, 1, 1])

with col_section:
    section_query = st.text_input(
        "🔍 Filter by section title",
        placeholder="e.g. searching tree, find all, navigating...",
        help="Supports fuzzy matching - partial or slightly misspelled queries still work.",
    )

with col_threshold:
    fuzzy_threshold = st.slider(
        "Fuzzy sensitivity",
        min_value=30, max_value=95, value=60, step=5,
        help="Lower = more lenient. 60 is recommended for section titles.",
    )

with col_sort:
    sort_by = st.selectbox("Sort by", ["example_id", "line_count", "section_title"])


# Fuzzy filter function 
def fuzzy_filter_by_section(items: list, query: str, threshold: int) -> list:
    """
    Filter code examples whose section_title fuzzy-matches the query.
    Returns list of (score, item) sorted by score descending.
    Falls back to plain substring search if rapidfuzz is not installed.
    """
    if not query or not query.strip():
        return [(100, item) for item in items]

    try:
        from rapidfuzz import fuzz
    except ImportError:
        q = query.lower()
        matched = [item for item in items if q in item["section_title"].lower()]
        return [(100, item) for item in matched]

    q = query.strip()
    results = []
    for item in items:
        title = item["section_title"]
        # partial_ratio: "find all" matches "find_all() arguments"
        partial  = fuzz.partial_ratio(q.lower(), title.lower())
        # token_sort: "tree searching" matches "Searching the tree"
        token    = fuzz.token_sort_ratio(q.lower(), title.lower())
        best     = max(partial, token)
        if best >= threshold:
            results.append((best, item))

    results.sort(key=lambda x: -x[0])
    return results

# Fetch - always fetch without section param to do fuzzy-filter client-side
def fetch_code(method: str | None) -> dict:
    params = {}
    if method:
        params["method"] = method
    try:
        r = requests.get(f"{API_BASE}/code-examples",
                         params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


data = fetch_code(selected_method)

if "error" in data:
    st.error(f"Cannot load code examples: {data['error']}\n\n"
             "Make sure the API is running and the pipeline has been executed.")
    st.stop()

all_items = data.get("items", [])

# Apply fuzzy section filter client-side
if section_query:
    scored = fuzzy_filter_by_section(all_items, section_query, fuzzy_threshold)
    items  = [item for _, item in scored]
    scores = {item["example_id"]: score for score, item in scored}
else:
    items  = all_items
    scores = {}

# Sort
if sort_by == "line_count":
    items = sorted(items, key=lambda x: x["line_count"], reverse=True)
elif sort_by == "section_title":
    items = sorted(items, key=lambda x: x["section_title"])
# example_id: already in natural order from API

# Results header
if section_query:
    st.caption(
        f"Found **{len(items)}** example(s) in sections matching "
        f"*\"{section_query}\"* (fuzzy threshold: {fuzzy_threshold})"
    )
else:
    st.caption(f"Showing **{len(items)}** code example(s)")

if not items:
    st.warning(
        f"No code examples found in sections matching *\"{section_query}\"* "
        f"at threshold {fuzzy_threshold}. "
        "Try lowering the **Fuzzy sensitivity** slider or broadening your query."
    )
    st.stop()

# Display
for ex in items:
    method_flags = [
        label for col_name, label in METHODS.items()
        if ex.get(col_name) is True or ex.get(col_name) == "True"
    ]

    score_badge = f"  `{scores[ex['example_id']]}%`" if ex["example_id"] in scores else ""
    header = (
        f"[#{ex['example_id']}] **{ex['section_title']}**"
        f"{score_badge}"
        f"  -  {ex['line_count']} lines"
    )
    if method_flags:
        header += f"  · `{'` · `'.join(method_flags)}`"

    with st.expander(header):
        st.code(ex["code_text"], language="python")
        if method_flags:
            st.caption("Methods used: " + " · ".join(f"`{m}`" for m in method_flags))
        st.caption(f"Section: *{ex['section_title']}*  ·  Example ID: `{ex['example_id']}`")