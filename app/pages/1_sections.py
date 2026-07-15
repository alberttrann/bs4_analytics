"""
app/pages/1_sections.py
Section explorer - fuzzy search (Levenshtein via rapidfuzz), level filter,
                   expandable text, calls GET /sections.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import os
import requests
import streamlit as st
from app.config import API_BASE

st.set_page_config(page_title="Sections - BS4 Analytics",
                   page_icon="📄", layout="wide")
st.title("📄 Documentation Sections")

# Controls
col_search, col_level, col_size, col_threshold = st.columns([3, 1, 1, 1])

with col_search:
    search = st.text_input(
        "🔍 Search sections",
        placeholder="e.g. api docs, find all, tree navigation...",
        help="Supports fuzzy matching - partial or slightly misspelled queries still work.",
    )

with col_level:
    level_opt = st.selectbox("Heading level", ["All", "H1", "H2", "H3"])

with col_size:
    page_size = st.selectbox("Show per page", [20, 50, 100], index=0)

with col_threshold:
    fuzzy_threshold = st.slider(
        "Fuzzy sensitivity",
        min_value=30, max_value=95, value=55, step=5,
        help="Lower = more lenient matching. 55 is recommended.",
    )

level_map = {"All": None, "H1": 1, "H2": 2, "H3": 3}
level_val = level_map[level_opt]

# Fetch all sections 
@st.cache_data(ttl=120, show_spinner=False)
def fetch_all_sections(level_v):
    params = {"size": 200}
    if level_v:
        params["level"] = level_v
    try:
        r = requests.get(f"{API_BASE}/sections", params=params, timeout=10)
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception as e:
        return []

all_sections = fetch_all_sections(level_val)

if not all_sections:
    st.error("Cannot load sections. Make sure the API is running and the pipeline has been executed.")
    st.stop()

# Fuzzy search logic
def fuzzy_filter(sections: list, query: str, threshold: int) -> list:
    """
    Filter sections using rapidfuzz Levenshtein-based partial ratio.
    Each section is scored against the query on both title and a snippet of text.
    Returns list of (score, section) sorted by score descending.
    """
    if not query or not query.strip():
        return [(100, s) for s in sections]

    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        # Fallback to plain substring search if rapidfuzz not installed
        q = query.lower()
        matched = [s for s in sections
                   if q in s["section_title"].lower()
                   or q in s["section_text"].lower()]
        return [(100, s) for s in matched]

    q = query.strip()
    results = []
    for sec in sections:
        title_score = fuzz.partial_ratio(q.lower(), sec["section_title"].lower())
        # Also check against first 300 chars of section text
        text_snippet = sec["section_text"][:300].lower()
        text_score   = fuzz.partial_ratio(q.lower(), text_snippet)
        # Token sort catches word-order differences: "api docs" vs "docs api"
        token_score  = fuzz.token_sort_ratio(q.lower(), sec["section_title"].lower())
        best_score   = max(title_score, text_score, token_score)
        if best_score >= threshold:
            results.append((best_score, sec))

    results.sort(key=lambda x: -x[0])
    return results

scored = fuzzy_filter(all_sections, search, fuzzy_threshold)

# Paginate
total_matched = len(scored)
page_items    = scored[:page_size]

# Results header
if search:
    st.caption(
        f"Found **{total_matched}** section(s) matching *\"{search}\"* "
        f"(fuzzy threshold: {fuzzy_threshold}) - showing top {len(page_items)}"
    )
else:
    st.caption(f"Showing {len(page_items)} of {total_matched} section(s)")

if total_matched == 0:
    st.warning(
        f"No sections matched *\"{search}\"* at threshold {fuzzy_threshold}. "
        "Try lowering the **Fuzzy sensitivity** slider or broadening your query."
    )
    st.stop()

# Display sections
for score, sec in page_items:
    level_icon = {1: "🔵", 2: "🟢", 3: "🟡"}.get(sec["section_level"], "⚪")
    score_badge = f"  `{score}%`" if search else ""
    label = (
        f"{level_icon} **[H{sec['section_level']}]** {sec['section_title']}"
        f"{score_badge}"
        f"  -  {sec['word_count']:,} words"
        f" · {sec['code_block_count']} code blocks"
        f" · {sec['link_count']} links"
    )
    with st.expander(label):
        text = sec["section_text"]
        if len(text) > 800:
            toggle_key = f"expand_{sec['section_id']}"
            if st.session_state.get(toggle_key):
                st.write(text)
                if st.button("Show less", key=f"less_{sec['section_id']}"):
                    st.session_state[toggle_key] = False
                    st.rerun()
            else:
                st.write(text[:800] + "…")
                if st.button("Show more", key=f"more_{sec['section_id']}"):
                    st.session_state[toggle_key] = True
                    st.rerun()
        else:
            st.write(text if text.strip() else "_No text content_")

        st.markdown(
            f"**Section ID:** `{sec['section_id']}`  "
            f"**Level:** H{sec['section_level']}"
        )